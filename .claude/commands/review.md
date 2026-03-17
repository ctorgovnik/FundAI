Review the current staged changes (or branch diff if on a feature branch) against the FundAI coding standards.

Check for:
1. **ABI invariants** — no non-POD members in ABI structs, no in-place modification of versioned structs, `static_assert` present
2. **IPC rules** — no dynamic allocation in shared regions, no mutex on hot path, `shm_unlink` called on shutdown
3. **Agent rules** — `on_state()` is exception-safe, no raw ctypes, ViewObject schema respected, no bare `print()`
4. **C++ conventions** — thread-safety documented in headers, no hardcoded config, C-compatible headers in `abi/` and `ipc/`
5. **Python conventions** — type hints present, `dataclass` for value objects, config from JSON not hardcoded
6. **General** — no build artifacts committed, no hardcoded shmem names, mode differences config-driven not ifdef-driven

List violations with file and line number. Suggest a fix for each.
