# Agents — Claude Code Context

## What this directory is

Python agent processes. Each agent is an independent process that attaches to the Fund OS via the pybind11 wrapper, observes `FundState` snapshots, and emits `AgentAction` intent. Agents never touch execution, risk, or accounting directly.

## Current files

- `base.py` — `AgentProcess` base class (in progress, see issue #12)

## Agent lifecycle

```
AgentProcess (base.py)
    on_start()       → called once at attach
    on_state(state)  → called every tick, must return AgentAction
    on_stop()        → called on shutdown

DiscretionaryPM (pm/discretionary.py — not yet built)
    ResearchLoop     → LLM + tools → ViewObject  (slow timescale)
    DecisionEngine   → FundState + ViewObject → AgentAction  (every tick, RL-trained)
```

## ViewObject — most important schema in this directory

The `ViewObject` is the structured output of the research loop fed into the decision engine. It is the contract between unstructured LLM research and structured RL decision-making. Treat schema changes like ABI changes — they affect training.

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
- Every call is logged and auditable
- Rate-limited per research cycle

Planned: `WebSearchTool`, `NewsFetchTool`, `SECFilingTool`, `PriceHistoryTool`

## Hard rules

1. **No raw ctypes or mmap in agent code.** Use `import fund_py` (pybind11 wrapper) only.
2. **`on_state()` must never raise.** Catch all exceptions internally. An unhandled exception halts the agent and triggers Fund OS no-op fallback.
3. **FundState is read-only from the agent side.** Never attempt to write to the state object.
4. **Research loop runs on a slow timescale.** Not every tick. Trigger on market open, major news, or a configurable interval (e.g. every 30 bars).
5. **ViewObject expires.** After `confidence_decay_bars`, default to flat. Never hold a stale view.

## Python conventions

- Python 3.11+, type hints everywhere
- `dataclass` for all value objects
- `logging` module only — no bare `print()`
- Config from JSON files, nothing hardcoded
- Tests in `agents/tests/`

## Key dependencies

- `anthropic` — Anthropic Python SDK for LLM research loop
- `fund_py` — pybind11 wrapper built from CMake (issue #8, not yet available)
- `numpy`, `pandas`, `requests` — standard
