# 🏛️ Architecture Genesis Matrix & Standards Reference

> **Mandatory Reference for `system-architect` (Phase 0: Spec-Before-Code).**  
> Synthesizes battle-tested industry standards (The Twelve-Factor App, C4 Model, Clean Architecture, MADR, and Fail-Fast Process Resilience) for zero-hallucination, LLM-native project generation.

---

## 🧭 1. The 5 Core Layer Boundaries (Clean Architecture Invariant)

Every project authored or bootstrapped in AnD os must strictly separate its layers into concentric zones of dependency. Dependencies point strictly **inward**:

```
Presentation / UI / CLI (Outermost)
        │
        ▼
   Adapters / I/O / Gateways (HTTP, SQLite, Disk, Process)
        │
        ▼
   Domain / Use Cases (Pure Algorithms, Invariants, 0 I/O)
        │
        ▼
   Entities / Core Contracts (Data Structures, Schemas, Config)
```

1. **`core/` & `config/` (Inward):**
   - 12-Factor environment configuration loaded once at startup.
   - Fail-fast validation: if an environment variable or critical path is missing, process exits with status `1` and explicit code.
   - Zero hardcoded secrets, zero machine host paths.
2. **`domain/` (Pure Business Logic):**
   - Pure functions and mathematical transformations.
   - **Strict Invariant:** Zero side-effects. Zero `open()`, zero `requests.get()`, zero `sqlite3.connect()`, zero `console.log()`.
   - 100% unit-testable in under 5 milliseconds without mocks.
3. **`adapters/` (I/O Gateways & Infrastructure):**
   - Handles network calls, SQLite queries, filesystem persistence, and subshell processes.
   - Implements mandatory timeouts ($\le 5$s) and exponential backoff with jitter on network calls.
4. **`entrypoints/` (Transport & Presentation):**
   - CLI parsers (`argparse`), HTTP router handlers (`FastAPI`, `Express`), or GUI views (`HTML/Canvas`, `SwiftUI`).
   - Translates raw input to clean domain DTOs, executes domain functions, and formats the output.

---

## 🤖 2. LLM-Native Deterministic Anchors

To prevent agent hallucinations and context bloat during future development, every project must maintain 3 deterministic anchors:

### Anchor 1: Project `AGENTS.md` (Context Budget: $\le 300$ tokens)
A dedicated, ultra-dense map for LLM coders at the root of the project:
```markdown
# AGENTS.md — [Project Name] Agent Directive

- **Domain:** [Domain Title / Island]
- **Port:** [Port or N/A]
- **Core Mission:** [1-sentence functional objective]
- **Safe Zone (Allowed to mutate):** `src/domain/`, `src/adapters/`, `tests/`
- **Protected Zone (Do not edit directly):** `docs/schema.json`, `config/`
- **Verification Commands:**
  - `make smoke` -> Sub-200ms sanity check
  - `make verify` -> Full unit test suite + lint
```

### Anchor 2: Strict Machine-Readable Contract (`docs/schema.json`)
- Every data exchange between producer (backend) and consumer (frontend/UI) must conform to an explicit JSON schema.
- Agents are forbidden from guessing field names.

### Anchor 3: Deterministic Error Catalog (`docs/error_catalog.json`)
```json
{
  "ERR_CONFIG_INVALID": { "code": 1001, "retryable": false, "description": "Invalid environment configuration" },
  "ERR_CONTRACT_MISMATCH": { "code": 1002, "retryable": false, "description": "Input payload failed schema validation" },
  "ERR_UPSTREAM_TIMEOUT": { "code": 2001, "retryable": true, "description": "Network gateway timeout exceeded 5s" }
}
```

---

## 🛡️ 3. Process Resilience & Production Hygiene

Adopted from `goldbergyoni/nodebestpractices` and `system-design-primer`:

1. **Graceful Shutdown Protocol (SIGTERM / SIGINT):**
   - Any long-running server or daemon must intercept `SIGTERM` and `SIGINT`.
   - Flush pending write buffers, close open database connections, and release ports cleanly within 3 seconds.
2. **Liveness & Readiness Probes:**
   - Web services expose `/healthz` (Process is alive) and `/readyz` (Data/DB is loaded and ready to serve).
3. **Idempotent Side-Effects & Outbox Pattern:**
   - Any script writing to disk or database must be strictly idempotent. Running it twice produces the identical valid state without duplicating records.
   - Operations take an `idempotency_key = hash(entity_id + mutation_payload)` checked against a dedup ledger before execution.
4. **Schema Evolution & Migrations Engine:**
   - Persistent stores (SQLite/PostgreSQL) maintain a `_schema_migrations` ledger.
   - Migrations are forward (`up()`) and rollback (`down()`) capable, executed atomically at startup in < 5ms.
5. **Backpressure & Bulkheads:**
   - Bounded queues for background operations (e.g., GPU rendering, async sync).
   - Reject load early (fail-fast with `ERR_QUEUE_FULL`) to prevent Memory/VRAM Out-Of-Memory crashes.
6. **Structured JSON Telemetry:**
   - All diagnostic logs written in JSON format: `{"timestamp": "...", "level": "INFO", "trace_id": "...", "component": "...", "duration_ms": 12}`.

