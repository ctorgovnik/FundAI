# Architecture Overview

## High-level Plan
The Fund and its agentic PMs will initially be deployed on the same machine and communicate via shared memory. The Fund will be written in C++ and deployed as a single, multi-threaded process. It may be subject to sharding and horizontal scaling in the future.

Each PM will be an independent process. Agent source code will initially be written in Python. Core distribution and deployment mechanisms will be decided closer to an MVP, but the architecture is designed to support language-agnostic agents.

---

## Process Topology & Lifecycle
The Fund process is started first and is responsible for initializing all core services, including shared memory regions, configuration state, and internal subsystems (market ingestion, execution, risk, accounting).

Agent processes are launched independently and attach to the Fund via the ABI. Agents may be started, stopped, or restarted without requiring a Fund restart.

The Fund does not depend on the presence of any individual agent in order to operate safely.

---

## Configuration / Service Management
In production environments, configuration for all processes (the Fund and all agents) will be stored in a SQL database. Configuration includes:

- service identifiers  
- enabled instruments  
- agent-to-symbol mappings  
- risk and execution parameters  

Upon startup, each process fetches its configuration before signaling readiness.

In simulation or local development environments, configuration may be provided via static JSON files.

---

## Data Flow
Market data flows unidirectionally into the Fund. Agents never ingest raw market feeds directly.

At a high level:

```
Market Data → Fund OS → FundState (ABI)
                           ↓
                        Agent
                           ↓
                        Intent
                           ↓
                   Execution / Risk
```

Agents observe FundState snapshots and emit trading intent. The Fund validates, nets, and executes intent before producing the next state snapshot.

---

## Shared Memory & ABI Model
The Fund and agents communicate via shared memory using a stable, versioned ABI.

- ABI structs are POD-only  
- Memory layout is explicit and fixed  
- No dynamic allocation occurs in shared regions  

The Fund is the sole writer of state snapshots. Agents are readers of state and writers of intent.

ABI compatibility is treated as a long-lived contract.

---

## Threading & Concurrency (Fund)
The Fund is internally multi-threaded, with distinct threads for:

- market data ingestion  
- state updates  
- agent intent handling  

All state transitions are serialized through explicit ordering to preserve determinism. Concurrency is used for throughput, not for speculative behavior.

---

## Failure & Isolation Model
Agents are treated as untrusted processes.

- Agent crashes do not affect the Fund process  
- If an agent fails to emit intent, the Fund defaults to a no-op or risk-reducing action  
- Shared memory corruption or invalid intent is rejected by validation layers  

The Fund remains safe and deterministic regardless of agent behavior.

---

## Runtime Modes
The same architecture is used across all environments:

- **Simulation**: historical replay, deterministic clock, file-based configuration  
- **Paper Trading**: live market data, simulated execution  
- **Production**: live data, live execution, database-backed configuration  

Differences between modes are configuration-driven, not architectural.

---

## Deferred Concerns
The following are intentionally deferred from the initial architecture:

- multi-machine deployment  
- network-based agent communication  
- dynamic sharding of instruments  
- high-frequency execution optimizations  

These concerns are expected to be layered on without modifying the Fund–Agent interface.
