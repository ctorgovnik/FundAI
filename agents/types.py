"""
ABI mirror types for the FundAI agent layer.

Python equivalents of abi/fund_state.h (FundStateV1) and
abi/agent_action.h (AgentActionV1). These will be replaced by pybind11
bindings (fund_py) once issue #8 lands.

Treat schema changes like ABI changes — they affect all consumers and
require a new version (V2), never in-place modification.
"""

from dataclasses import dataclass


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
