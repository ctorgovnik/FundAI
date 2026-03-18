# Agents — Claude Code Context

## What this directory is

Python agent processes. Each agent is an independent process that attaches to the Fund OS via the pybind11 wrapper, observes `FundState` snapshots, and emits `AgentAction` intent. Agents never touch execution, risk, or accounting directly.

## Current files

- `base.py` — `AgentProcess` base class (in progress, see issue #12)

## Planned structure

```
agents/
├── base.py                    # AgentProcess base class
├── pm/
│   └── discretionary.py       # DiscretionaryPM — LLM research + RL decision engine
├── tools/
│   ├── base.py                # Tool base class and registry
│   ├── web_search.py          # WebSearchTool
│   ├── news.py                # NewsFetchTool
│   ├── sec_filings.py         # SECFilingTool
│   ├── price_history.py       # PriceHistoryTool
│   └── router.py              # ToolRouter — routes tool calls based on runtime mode
├── factory.py                 # AgentFactory — spawn, restart, hot-swap agents
└── tests/
```

## Agent lifecycle

```
AgentProcess (base.py)
    on_start()       → called once at attach, loads config
    on_state(state)  → called every tick, must return AgentAction
    on_stop()        → called on shutdown, detaches from shmem

DiscretionaryPM (pm/discretionary.py — not yet built)
    ResearchLoop     → LLM + tools → ViewObject  (slow timescale, not every tick)
    DecisionEngine   → FundState + ViewObject → AgentAction  (every tick, RL-trained)
```

## Agent specialization config

Each agent is described by a JSON config (`AgentConfigV1`, issue #26). Example:

```json
{
  "agent_id": "tech-equity-pm",
  "version": 1,
  "tradeable_instruments": ["AAPL", "MSFT", "NVDA", "GOOGL"],
  "observable_instruments": ["BTC-USD", "polymarket:will-fed-cut-rates-q1"],
  "risk_limits": {
    "max_position_pct": 0.20,
    "max_drawdown_pct": 0.10
  },
  "research_focus": "technology sector equities",
  "research_trigger": "on_open",
  "capital_allocation": {
    "starting_cash": 1000000,
    "max_pct_of_fund": 0.30
  }
}
```

- `tradeable_instruments` — agent can submit intent for these
- `observable_instruments` — agent observes these in FundState but cannot trade them (e.g. crypto signals, prediction market probabilities)
- `research_focus` is a hint to the LLM, not a hard constraint — agent can explore beyond it
- Configs live in `configs/` — add examples to `configs/examples/` for each new specialization

## ViewObject — most important schema in this directory

The structured output of the research loop fed into the decision engine. The contract between unstructured LLM research and structured RL decision-making. **Treat schema changes like ABI changes — they affect training and require a version bump.**

```python
@dataclass
class ViewObject:
    symbol: str
    direction: Literal["long", "short", "flat"]
    conviction: float          # 0.0 to 1.0
    catalyst: str              # thesis in one sentence
    regime: str                # "risk-on" | "risk-off" | "neutral"
    confidence_decay_bars: int # bars until view expires and defaults to flat
    generated_at: datetime
```

## Tool layer (issue #13)

Tools are read-only external information sources. Rules:
- Return concise structured string output (~2000 chars max per call)
- Must never submit intent, write files, or access Fund OS internals
- Every call is logged and auditable (especially important for backtesting audit trail)
- Rate-limited per research cycle

### Tool routing — live vs backtest

All tool calls go through `ToolRouter` which applies mode-specific routing:

| Tool | Live / Paper mode | Simulation (backtest) mode |
|---|---|---|
| `WebSearchTool` | Real internet | **Blocked** — returns clear message |
| `NewsFetchTool` | Live news API | Historical archive, `as_of=sim_clock` |
| `SECFilingTool` | Live EDGAR API | Historical archive, `as_of=sim_clock` |
| `PriceHistoryTool` | Live market data | Sim engine data, `as_of=sim_clock` |

Agent code is **identical in both modes** — only the router changes behavior. Mode is injected at agent startup from Fund OS config. The agent cannot change its own mode.

## Multi-asset awareness

Agents can observe multiple asset classes in a single `on_state()` call. The `instrument_id` + `asset_class` fields distinguish them:

- **Equities** — OHLCV, bid/ask, position, PnL (tradeable if in `tradeable_instruments`)
- **Crypto** — same numeric fields as equities, 24/7 (tradeable if configured)
- **Prediction markets** — `yes_price`, `no_price` probabilities (observable only for now — not tradeable)

The agent decides how to use cross-asset signals — we do not prescribe signal logic.

## Agent factory (issue #28)

`factory.py` manages agent process lifecycle:
- `spawn(config_path)` — forks a new agent process from config, registers with Fund OS
- `stop(agent_id)` — graceful SIGTERM
- `restart(agent_id)` — stop + spawn with same config
- `hot_swap(agent_id, new_config)` — spawn new, wait for healthy attach, stop old
- Crashed agents are auto-restarted (configurable max restarts)
- Startup validation: new agent must emit at least one intent before factory marks it healthy

## Hard rules

1. **No raw ctypes or mmap in agent code.** Use `import fund_py` (pybind11 wrapper) only.
2. **`on_state()` must never raise.** Catch all exceptions internally. An unhandled exception halts the agent and triggers Fund OS no-op fallback.
3. **FundState is read-only from the agent side.** Never attempt to write to the state object.
4. **Research loop runs on a slow timescale.** Not every tick. Trigger on market open, major news, or a configurable interval (e.g. every 30 bars).
5. **ViewObject expires.** After `confidence_decay_bars`, default to flat. Never hold a stale view.
6. **Tools must route through `ToolRouter`.** Never call external APIs directly from agent code — always use the registered tool classes so backtest routing works correctly.
7. **Shmem names use `agent_id`.** Each agent derives its shared memory segment name from its `agent_id` config field. Never hardcode shmem names.

## Python conventions

- Python 3.11+, type hints everywhere
- `dataclass` for all value objects
- `logging` module only — no bare `print()`
- Config from JSON files in `configs/` — nothing hardcoded
- Tests in `agents/tests/`

## Key dependencies

- `anthropic` — Anthropic Python SDK for LLM research loop
- `fund_py` — pybind11 wrapper built from CMake (issue #8, not yet available)
- `numpy`, `pandas`, `requests` — standard
- `psutil` — process management in factory.py
