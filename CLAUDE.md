# FundAI — Claude Code Context

## What this project is

FundAI models a hedge fund as a deterministic operating system (Fund OS) that exposes a controlled, versioned interface to independent AI decision agents (agentic portfolio managers). The fund owns all interaction with the external world. Agents observe state and emit intent — they never touch execution directly.

The core hypothesis: a discretionary AI portfolio manager, backed by LLM-driven research and RL-trained position sizing, can generate alpha on equities.

## Repo structure

```
FundAI/
├── abi/              # ABI structs — the contract between Fund OS and agents (C headers)
├── ipc/              # Shared memory transport — ring buffer, shmem primitives (C)
├── fund/             # Fund OS — market data, execution, risk, accounting (C++) [not yet active]
├── agents/           # Python agent processes — base class, discretionary PM, tools
├── docs/             # Design documents
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

## Open Phase 1 issues

| # | Title | Track |
|---|-------|-------|
| #3 | Define ABI v1 structs | Fund OS |
| #4 | ABI adapter layer | Fund OS |
| #5 | Simulate communication via ABI | Fund OS |
| #6 | Ring buffer and shared memory modules | Fund OS |
| #7 | Process skeleton + build system | Fund OS |
| #8 | pybind11 Python wrapper | Fund OS |
| #9 | Simulation engine + deterministic clock | Fund OS |
| #10 | Realistic fill simulation + market impact | Fund OS |
| #11 | Risk validation layer | Fund OS |
| #12 | Agent process skeleton | PM Agent |
| #13 | Tool layer (web search, news, SEC) | PM Agent |
| #14 | Research loop + ViewObject schema | PM Agent |
| #15 | Evaluation framework | PM Agent |
| #16 | Reward function design | PM Agent |

## C/C++ conventions (`abi/`, `ipc/`, `fund/`)

- C++20 for `fund/`, C for `ipc/` (C-compatible for Python interop)
- ABI structs are POD only — no constructors, virtual functions, std::string, or pointers
- No dynamic allocation in shared memory regions
- All public headers must compile as both C and C++
- Use `static_assert(std::is_trivially_copyable_v<FundStateV1>)` on all ABI structs
- Document thread-safety in headers

## Python conventions (`agents/`)

- Python 3.11+
- Type hints on all function signatures
- `dataclass` for value objects (ViewObject, etc.)
- No raw ctypes or mmap in agent code — pybind11 wrapper only
- `on_state()` must never raise — catch all exceptions internally
- `logging` module only, no bare `print()`

## Notes for Claude Code

- When modifying ABI structs, check all consumers: `ipc/`, `fund/`, `agents/`, pybind11 wrapper
- When adding a field to `FundStateV1`, create `FundStateV2` — never modify V1
- Run IPC tests with: `ctest --test-dir build -R ipc`
- To activate `fund/`: add `add_subdirectory(fund)` to root CMakeLists.txt
- Do not commit build artifacts (`build/`, `*.o`, `*.a`, `CMakeFiles/`, `cmake_install.cmake`, `Makefile` generated by CMake)
