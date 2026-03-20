"""Tests for AgentProcess base class (issue #12).

Covers:
  - Config loading from JSON
  - Lifecycle: start → tick → stop
  - on_state() exception safety — exceptions produce a no-op hold intent
  - Double-start guard
  - agent_id / shmem_name before start raises
  - shmem_name format uses agent_id
"""

import json
import logging
import pytest
from pathlib import Path

from agents.base import AgentProcess
from agents.config import AgentConfigV1
from agents.types import AgentActionV1, FundStateV1


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def config_file(tmp_path: Path) -> Path:
    cfg = {
        "agent_id": "test-agent",
        "version": 1,
        "tradeable_instruments": ["AAPL", "MSFT"],
        "observable_instruments": ["BTC-USD"],
        "risk_limits": {"max_position_pct": 0.10},
        "research_focus": "test",
        "research_trigger": "on_open",
        "capital_allocation": {"starting_cash": 100000, "max_pct_of_fund": 0.20},
    }
    path = tmp_path / "agent.json"
    path.write_text(json.dumps(cfg))
    return path


def make_state(instrument_id: int = 1, position: int = 0) -> FundStateV1:
    return FundStateV1(
        instrument_id=instrument_id,
        mid_price=100.0,
        bid_price=99.9,
        ask_price=100.1,
        volatility=0.2,
        volume=1_000_000.0,
        position=position,
        avg_entry_price=0.0,
        unrealized_pnl=0.0,
        realized_pnl=0.0,
        cash=100_000.0,
    )


# ---------------------------------------------------------------------------
# Concrete subclasses for testing
# ---------------------------------------------------------------------------

class PassthroughAgent(AgentProcess):
    """Returns a fixed target_position every tick."""

    def __init__(self, config_path: str, target: float = 10.0) -> None:
        super().__init__(config_path)
        self.target = target
        self.start_called = False
        self.stop_called = False

    def on_start(self) -> None:
        self.start_called = True

    def on_state(self, state: FundStateV1) -> AgentActionV1:
        return AgentActionV1(
            instrument_id=state.instrument_id,
            target_position=self.target,
        )

    def on_stop(self) -> None:
        self.stop_called = True


class RaisingAgent(AgentProcess):
    """on_state() always raises to test the no-op fallback."""

    def on_state(self, state: FundStateV1) -> AgentActionV1:
        raise RuntimeError("deliberate error in on_state")


class DefaultHooksAgent(AgentProcess):
    """Uses default (no-op) on_start and on_stop implementations."""

    def on_state(self, state: FundStateV1) -> AgentActionV1:
        return AgentActionV1(
            instrument_id=state.instrument_id,
            target_position=0.0,
        )


# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------

class TestConfigLoading:
    def test_config_fields_loaded(self, config_file: Path) -> None:
        agent = PassthroughAgent(str(config_file))
        agent.start()
        cfg = agent.config
        assert cfg.agent_id == "test-agent"
        assert cfg.version == 1
        assert cfg.tradeable_instruments == ["AAPL", "MSFT"]
        assert cfg.observable_instruments == ["BTC-USD"]
        assert cfg.risk_limits == {"max_position_pct": 0.10}
        assert cfg.research_focus == "test"
        assert cfg.research_trigger == "on_open"
        assert cfg.capital_allocation == {
            "starting_cash": 100000,
            "max_pct_of_fund": 0.20,
        }

    def test_missing_config_file_raises(self, tmp_path: Path) -> None:
        agent = PassthroughAgent(str(tmp_path / "nonexistent.json"))
        with pytest.raises(FileNotFoundError):
            agent.start()

    def test_malformed_json_raises(self, tmp_path: Path) -> None:
        bad = tmp_path / "bad.json"
        bad.write_text("{not valid json")
        agent = PassthroughAgent(str(bad))
        with pytest.raises(json.JSONDecodeError):
            agent.start()

    def test_missing_required_field_raises(self, tmp_path: Path) -> None:
        cfg = tmp_path / "cfg.json"
        cfg.write_text(json.dumps({"version": 1}))  # missing agent_id
        agent = PassthroughAgent(str(cfg))
        with pytest.raises(KeyError):
            agent.start()

    def test_optional_fields_default(self, tmp_path: Path) -> None:
        minimal = {"agent_id": "min-agent", "version": 1}
        path = tmp_path / "min.json"
        path.write_text(json.dumps(minimal))
        agent = PassthroughAgent(str(path))
        agent.start()
        assert agent.config.tradeable_instruments == []
        assert agent.config.observable_instruments == []
        assert agent.config.risk_limits == {}
        assert agent.config.research_focus == ""
        assert agent.config.research_trigger == "on_open"
        assert agent.config.capital_allocation == {}


# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------

class TestLifecycle:
    def test_on_start_called(self, config_file: Path) -> None:
        agent = PassthroughAgent(str(config_file))
        assert not agent.start_called
        agent.start()
        assert agent.start_called

    def test_on_stop_called(self, config_file: Path) -> None:
        agent = PassthroughAgent(str(config_file))
        agent.start()
        assert not agent.stop_called
        agent.stop()
        assert agent.stop_called

    def test_double_start_raises(self, config_file: Path) -> None:
        agent = PassthroughAgent(str(config_file))
        agent.start()
        with pytest.raises(RuntimeError, match="start\\(\\) called twice"):
            agent.start()

    def test_default_hooks_no_raise(self, config_file: Path) -> None:
        agent = DefaultHooksAgent(str(config_file))
        agent.start()   # on_start default — should not raise
        agent.stop()    # on_stop default — should not raise

    def test_config_before_start_raises(self, config_file: Path) -> None:
        agent = PassthroughAgent(str(config_file))
        with pytest.raises(RuntimeError, match="not started"):
            _ = agent.config

    def test_agent_id_before_start_raises(self, config_file: Path) -> None:
        agent = PassthroughAgent(str(config_file))
        with pytest.raises(RuntimeError, match="not started"):
            _ = agent.agent_id


# ---------------------------------------------------------------------------
# tick() / on_state() behaviour
# ---------------------------------------------------------------------------

class TestTick:
    def test_returns_intent(self, config_file: Path) -> None:
        agent = PassthroughAgent(str(config_file), target=50.0)
        agent.start()
        state = make_state(instrument_id=42, position=0)
        action = agent.tick(state)
        assert isinstance(action, AgentActionV1)
        assert action.instrument_id == 42
        assert action.target_position == 50.0

    def test_exception_in_on_state_returns_hold(self, config_file: Path) -> None:
        agent = RaisingAgent(str(config_file))
        agent.start()
        state = make_state(instrument_id=7, position=25)
        action = agent.tick(state)
        # No-op: hold current position
        assert action.instrument_id == 7
        assert action.target_position == 25.0

    def test_exception_is_logged_not_raised(
        self, config_file: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        agent = RaisingAgent(str(config_file))
        agent.start()
        state = make_state()
        with caplog.at_level(logging.ERROR):
            agent.tick(state)
        assert any("on_state" in record.message for record in caplog.records)

    def test_hold_preserves_signed_position(self, config_file: Path) -> None:
        """Negative position (short) is preserved by the no-op hold."""
        agent = RaisingAgent(str(config_file))
        agent.start()
        state = make_state(position=-100)
        action = agent.tick(state)
        assert action.target_position == -100.0


# ---------------------------------------------------------------------------
# shmem_name
# ---------------------------------------------------------------------------

class TestShmemName:
    def test_shmem_name_uses_agent_id(self, config_file: Path) -> None:
        agent = PassthroughAgent(str(config_file))
        agent.start()
        assert agent.shmem_name == "/test-agent"

    def test_shmem_name_starts_with_slash(self, config_file: Path) -> None:
        agent = PassthroughAgent(str(config_file))
        agent.start()
        assert agent.shmem_name.startswith("/")

    def test_shmem_name_before_start_raises(self, config_file: Path) -> None:
        agent = PassthroughAgent(str(config_file))
        with pytest.raises(RuntimeError, match="not started"):
            _ = agent.shmem_name
