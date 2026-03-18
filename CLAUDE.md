# FundAI — Claude Code Context

## What this project is

FundAI models a hedge fund as a deterministic operating system (Fund OS) that exposes a controlled, versioned interface to independent AI decision agents (agentic portfolio managers). The fund owns all interaction with the external world. Agents observe state and emit intent — they never touch execution directly.

The core hypothesis: a discretionary AI portfolio manager, backed by LLM-driven research and RL-trained position sizing, can generate alpha across equities, crypto, and prediction markets.

## Repo structure

```
FundAI/
├── abi/              # ABI structs — the contract between Fund OS and agents (C headers)
├── ipc/              # Shared memory transport — ring buffer, shmem primitives (C)
├── fund/             # Fund OS — market data, execution, risk, accounting (C++) [not yet active]
├── agents/           # Python agent processes — base class, discretionary PM, tools
├── backtesting/      # Hermetic backtest environment, data vault, audit trail [not yet active]
├── configs/          # JSON configs — agent specializations, sim params, risk limits
├── scripts/          # Bootstrap, env validation, lock file update scripts
├── docs/             # Design documents and architecture decision records
├── CMakeLists.txt    # Root CMake — C++20, GoogleTest, subdirs: abi, ipc (fund commented out)
└── .mcp.json         # GitHub MCP config for Claude Code
```

## Build

```bash
cmake -B build -DCMAKE_BUILD_TYPE=Debug
cmake --build build
ctest --test-dir build
```

- C++20, CMake 3.16+
- GoogleTest via FetchContent (v1.14.0)
- `CMAKE_EXPORT_COMPILE_COMMANDS=ON` always on
- `fund/` is commented out in root CMakeLists.txt — uncomment when creating it

## Architecture — critical invariants

These are laws. Do not violate them without explicit discussion.

1. **Agents never touch execution.** All market action flows through `submit_intent()` → Fund OS risk layer → execution. No agent ever calls a broker API directly.
2. **The ABI is a versioned contract.** `FundStateV1` and `AgentActionV1` are POD-only, fixed layout. Adding fields requires a new version (`V2`), never modifying existing structs in place.
3. **Fund OS owns shared memory.** Only the Fund OS writes `FundState`. Agents read state and write intent only.
4. **Simulation = Paper = Production.** Mode differences are config-driven, not `#ifdef`-driven. Same code path everywhere.
5. **Fail safe.** On agent failure, invalid intent, or missing intent: default to no-op (hold position). Never fail open.
6. **Backtesting is hermetic.** In simulation mode, all agent tool calls are routed through the Fund OS data vault with strict `as_of` enforcement. No live network access from agent tools during backtesting. The same agent code runs in live and backtest — only the routing changes.
7. **Agents do not know each other's positions.** Agents can query fund-level aggregate exposure (anonymized) but never individual agent books.
8. **The data vault enforces point-in-time semantics.** When sim clock = T, no data call returns information timestamped after T. This is enforced at the service level, not by trusting the agent.

## ABI — current structs

```cpp
// abi/fund_state.h
struct FundStateV1 {
    int32_t instrument_id;
    double mid_price;
    double bid_price;
    double ask_price;
    double volatility;
    double volume;
    int64_t position;
    double avg_entry_price;
    double unrealized_pnl;
    double realized_pnl;
    double cash;
};
// abi/agent_action.h — see file for current definition
```

`FundStateV1` will need to be extended (as `FundStateV2`) when multi-asset support lands — crypto and prediction market instruments require an `asset_class` discriminator field.

## IPC layer (`ipc/`)

- `shared_memory.h/c` — POSIX shmem create/attach/detach
- `ring_buffer.h/c` — ring buffer on top of shmem for state snapshots
- Written in C for portability and Python ctypes compatibility
- Tests in `ipc/tests/`

## Agent layer (`agents/`)

- `base.py` — `AgentProcess` base class (in progress)
- All agents subclass `AgentProcess` and implement `on_state(state)` → returns intent
- Agents attach to Fund OS via pybind11 wrapper (issue #8, not yet built)
- `ViewObject` is the structured output of the LLM research loop, fed into the RL decision engine
- Agent specializations are defined by JSON config (`configs/`) and spawned by the agent factory (issue #28)

## Multi-asset data model

Data flows to agents on two paths depending on type:

| Data type | Path | Examples |
|---|---|---|
| Tick prices, positions, vol | Shared memory (`FundState`) | Equity OHLCV, crypto spot, PM probabilities |
| News, filings, text, contract metadata | MCP tool calls via Fund OS data server | News articles, 10-K filings, PM question text |

In **live mode**, tool calls hit real external APIs. In **backtest/sim mode**, tool calls are routed through the historical data vault with `as_of=sim_clock`. `WebSearchTool` is blocked in backtest mode. Agent code is identical in both modes — only routing changes.

## Multi-agent model

- Multiple agents run simultaneously, each with its own specialization config
- The **agent registry** (issue #27) tracks all attached agents, their configs, and health
- The **agent factory** (issue #28) spawns, restarts, and hot-swaps agents
- The **crossing engine** (issue #30) nets opposing intents internally before sending to market
- Fund OS tracks **aggregate positions** (issue #29) across all agents per instrument
- **Fund-level PnL** (issue #31) is tracked separately from per-agent PnL
- Agents cannot see each other's positions — only anonymized fund-level aggregates

## Milestone structure

| Milestone | Issues | What it covers |
|---|---|---|
| #3 Phase 1 — Fund OS Core | #3–#11 | Process skeleton, shmem, sim engine, fills, risk |
| #4 Phase 1 — PM Agent | #12–#16 | Agent skeleton, tools, research loop, eval, reward |
| #5 Phase 2 — Multi-Asset + Multi-Agent | #23–#32 | Data sources, factory, crossing, fund accounting |
| #6 Phase 2 — Backtesting + RL | #33–#39 | Data vault, hermetic env, RL harness |
| #7 Phase 2 — Infrastructure | #40–#41 | Environment isolation and reproducibility |

See github.com/ctorgovnik/FundAI/milestones for live progress.

## C/C++ conventions (`abi/`, `ipc/`, `fund/`)

- C++20 for `fund/`, C for `ipc/` (C-compatible for Python interop)
- ABI structs are POD only — no constructors, virtual functions, std::string, or pointers
- No dynamic allocation in shared memory regions
- All public headers must compile as both C and C++
- Use `static_assert(std::is_trivially_copyable_v<FundStateV1>)` on all ABI structs
- Document thread-safety in headers

## Python conventions (`agents/`, `backtesting/`)

- Python 3.11+
- Type hints on all function signatures
- `dataclass` for value objects (ViewObject, AgentConfigV1, etc.)
- No raw ctypes or mmap in agent code — pybind11 wrapper only
- `on_state()` must never raise — catch all exceptions internally
- `logging` module only, no bare `print()`
- Config from JSON files in `configs/` — nothing hardcoded

## Notes for Claude Code

- When modifying ABI structs, check all consumers: `ipc/`, `fund/`, `agents/`, pybind11 wrapper
- When adding a field to `FundStateV1`, create `FundStateV2` — never modify V1
- When adding a new tool to the tool layer, also add its backtest routing to `ToolRouter` in `backtesting/`
- When creating a new agent specialization, add an example config to `configs/examples/`
- Run IPC tests with: `ctest --test-dir build -R ipc`
- To activate `fund/`: add `add_subdirectory(fund)` to root CMakeLists.txt
- Do not commit build artifacts (`build/`, `*.o`, `*.a`, `CMakeFiles/`, `cmake_install.cmake`, `Makefile` generated by CMake)
- Shmem names must be derived from `agent_id` config field — never hardcoded — so multiple agents can run simultaneously without collision
