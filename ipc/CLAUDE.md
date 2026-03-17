# IPC — Claude Code Context

## What this directory is

The shared memory transport layer between the Fund OS and agent processes. The ABI defines *what* is communicated. IPC defines *how*.

## Files

- `shared_memory.h/c` — POSIX `shm_open`/`mmap` primitives: create, attach, detach
- `ring_buffer.h/c` — lock-free ring buffer on top of shared memory for state snapshot delivery
- `tests/` — GoogleTest tests for both modules

## Language: C, not C++

This layer is written in C deliberately — maximum portability, direct Python `ctypes` compatibility, no hidden allocations or RAII that could complicate shared memory layout. Do not introduce C++ here without explicit discussion.

## Key invariants

1. **No dynamic allocation in shared regions.** All struct sizes fixed and known at compile time.
2. **Fund OS is the sole writer of FundState.** Agents have read-only mapped regions for state, write-only for intent.
3. **Ring buffer is lock-free.** Use atomic operations for head/tail indices. No mutexes on the hot path.
4. **Shared memory names are config-driven.** Never hardcode shmem names — they come from config so multiple sim environments can run simultaneously.
5. **Always call `shm_unlink` on Fund OS shutdown.** Leaked shmem segments are hard to debug and persist across reboots.

## Running tests

```bash
cmake --build build
ctest --test-dir build -R ipc -V
```

## When modifying ring_buffer or shared_memory

- Run the full `ipc/tests/` suite before committing
- If changing ring buffer layout, check `fund/` and `agents/` for hardcoded size assumptions
