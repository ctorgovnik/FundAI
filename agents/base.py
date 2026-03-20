"""
AgentProcess base class for the FundAI agent layer.

All agent processes subclass AgentProcess and implement on_state().
The base class guarantees:
  - Config is loaded from JSON before on_start() is called.
  - on_state() exceptions are caught and converted to no-op (hold) intent.
  - Shmem names are derived from agent_id — never hardcoded.
"""

import logging
from abc import ABC, abstractmethod

from agents.config import AgentConfigV1
from agents.types import AgentActionV1, FundStateV1


class AgentProcess(ABC):
    """Base class for all FundAI agent processes.

    Lifecycle:
        start()         — load config, call on_start()
        tick(state)     — call on_state(), catch all exceptions → no-op fallback
        stop()          — call on_stop()

    Subclasses must implement on_state(). on_start() and on_stop() are
    optional hooks with empty default implementations.

    Thread safety: not thread-safe. Each agent runs in its own process.
    """

    def __init__(self, config_path: str) -> None:
        self._config_path = config_path
        self._config: AgentConfigV1 | None = None
        # Logger name updated to include agent_id once config is loaded.
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    # ------------------------------------------------------------------
    # Public lifecycle interface — called by Fund OS process manager
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Load config from JSON and call on_start().

        Must be called once before tick(). Calling start() twice is a
        programming error and will raise RuntimeError.
        """
        if self._config is not None:
            raise RuntimeError(
                f"start() called twice on agent {self._config.agent_id!r}"
            )
        self._config = AgentConfigV1.from_file(self._config_path)
        self._logger = logging.getLogger(
            f"{__name__}.{self._config.agent_id}"
        )
        self._logger.info("Agent starting: %s", self._config.agent_id)
        self.on_start()

    def tick(self, state: FundStateV1) -> AgentActionV1:
        """Deliver a FundState snapshot and return agent intent.

        Wraps on_state() with a catch-all guard: if on_state() raises for
        any reason, logs the exception and returns a no-op (hold current
        position) intent. The agent is never allowed to crash the Fund OS.
        """
        try:
            return self.on_state(state)
        except Exception:
            self._logger.exception(
                "on_state() raised on instrument %d — returning no-op hold intent",
                state.instrument_id,
            )
            # No-op: target == current position (hold).
            return AgentActionV1(
                instrument_id=state.instrument_id,
                target_position=float(state.position),
            )

    def stop(self) -> None:
        """Call on_stop() and log shutdown.

        No-op (with a warning) if start() was never called, so that teardown
        code is always safe to call regardless of startup success.
        """
        if self._config is None:
            self._logger.warning("stop() called on agent that was never started")
            return
        self._logger.info("Agent stopping: %s", self._config.agent_id)
        self.on_stop()

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def config(self) -> AgentConfigV1:
        """The loaded config. Raises RuntimeError if start() not yet called."""
        if self._config is None:
            raise RuntimeError("Agent not started — call start() first")
        return self._config

    @property
    def agent_id(self) -> str:
        """The agent's unique identifier, used to derive shmem names."""
        return self.config.agent_id

    @property
    def shmem_name(self) -> str:
        """POSIX shared memory segment name derived from agent_id.

        Format: /<agent_id>  (leading slash required by shm_open).
        Multiple agents can run simultaneously without collision because
        each agent_id must be unique within the fund.
        """
        return f"/{self.agent_id}"

    # ------------------------------------------------------------------
    # Overridable hooks
    # ------------------------------------------------------------------

    def on_start(self) -> None:
        """Called once after config is loaded. Override for setup logic."""

    @abstractmethod
    def on_state(self, state: FundStateV1) -> AgentActionV1:
        """Called every tick with the latest FundState snapshot.

        Must return an AgentActionV1 expressing the agent's intent.
        Must not raise — the base class tick() catches all exceptions and
        falls back to a hold intent. However, suppressing exceptions hides
        bugs; prefer logging and returning a safe intent explicitly.
        """
        ...

    def on_stop(self) -> None:
        """Called on graceful shutdown. Override for cleanup logic."""
