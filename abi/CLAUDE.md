# ABI — Claude Code Context

## What this directory is

The versioned interface contract between the Fund OS and all agents. These structs define what information exists to an agent and what actions an agent can take. **If it's not in the ABI, it doesn't exist to the agent.**

Treat this with the same care as an exchange protocol or syscall interface.

## Current files

- `fund_state.h` — `FundStateV1`: what the Fund OS exposes to agents each tick
- `agent_action.h` — `AgentActionV1`: what an agent can submit as intent

## Hard rules — do not break these

1. **POD only.** No constructors, destructors, virtual functions, `std::string`, or pointers. Structs must be trivially copyable and trivially destructible.
2. **Never modify an existing versioned struct.** `FundStateV1` is frozen. Adding a field means creating `FundStateV2`. Old versions are kept.
3. **Explicit layout.** Order fields to avoid implicit padding. Verify with `static_assert(sizeof(FundStateV1) == expected_size)`.
4. **C-compatible headers.** Must compile as both C and C++. Use `#ifdef __cplusplus` guards if needed.
5. **No implementation in headers.** Pure data definitions only.

## Required assertions on every ABI struct

```cpp
static_assert(std::is_trivially_copyable_v<FundStateV1>);
static_assert(std::is_standard_layout_v<FundStateV1>);
```

## Adding a new ABI version

1. Create `fund_state_v2.h` — do not rename or touch `fund_state.h`
2. Add `uint32_t abi_version = 2;` as the first field
3. Update the pybind11 wrapper to expose the new version
4. Add size and layout `static_assert`s
5. Update the ABI section in root `CLAUDE.md`
