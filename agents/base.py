"""
AgentProcess base class and core data types for the FundAI agent layer.

All agent processes subclass AgentProcess and implement on_state().
The base class guarantees:
  - Config is loaded from JSON before on_start() is called.
  - on_state() exceptions are caught and converted to no-op (hold) intent.
  - Shmem names are derived from agent_id — never hardcoded.
"""

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# ABI mirror types — Python equivalents of abi/fund_state.h and agent_action.h
# These will be replaced by pybind11 bindings (fund_py) once issue #8 lands.
# ---------------------------------------------------------------------------

@dataclass
class FundStateV1:
    """Python mirror of abi/fund_state.h FundStateV1.

    instrument_id  — identifies the instrument this snapshot describes
    mid/bid/ask    — current market prices
    volatility     — realised vol estimate
    volume         — traded volume this bar
    position       — current signed position (shares / contracts)
    avg_entry_price — cost basis of open position
    unrealized_pnl — mark-to-market PnL on open position
    realized_pnl   — closed PnL this session
    cash           — available cash allocated to this agent
    """
    instrument_id: int
    mid_price: float
    bid_price: float
    ask_price: float
    volatility: float
    volume: float
    position: int
    avg_entry_price: float
    unrealized_pnl: float
    realized_pnl: float
    cash: float


@dataclass
class AgentActionV1:
    """Python mirror of abi/agent_action.h AgentActionV1.

    instrument_id   — must match the FundStateV1.instrument_id that triggered intent
    target_position — desired signed position; Fund OS risk layer enforces limits
    """
    instrument_id: int
    target_position: float


# ---------------------------------------------------------------------------
# Agent configuration — loaded from configs/*.json
# ---------------------------------------------------------------------------

@dataclass
class AgentConfigV1:
    """Structured representation of an agent JSON config file (version 1).

    See configs/examples/ for concrete examples.
    """
    agent_id: str
    version: int
    tradeable_instruments: list[str]
    observable_instruments: list[str]
    risk_limits: dict
    research_focus: str
    research_trigger: str
    capital_allocation: dict


# ---------------------------------------------------------------------------
# AgentProcess base class
# ---------------------------------------------------------------------------

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
        self._config: Optional[AgentConfigV1] = None
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
        self._config = self._load_config(self._config_path)
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
        """Call on_stop() and log shutdown."""
        if self._config:
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

    def on_stop(self) -> None:
        """Called on graceful shutdown. Override for cleanup logic."""

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _load_config(config_path: str) -> AgentConfigV1:
        path = Path(config_path)
        with path.open() as f:
            data = json.load(f)
        return AgentConfigV1(
            agent_id=data["agent_id"],
            version=data["version"],
            tradeable_instruments=data.get("tradeable_instruments", []),
            observable_instruments=data.get("observable_instruments", []),
            risk_limits=data.get("risk_limits", {}),
            research_focus=data.get("research_focus", ""),
            research_trigger=data.get("research_trigger", "on_open"),
            capital_allocation=data.get("capital_allocation", {}),
        )
