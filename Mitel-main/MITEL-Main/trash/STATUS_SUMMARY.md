# OMNI FOUNDATION REBUILD - STATUS SUMMARY

## WHAT WE'RE DOING

Rebuilding the OMNI organism foundation from the ground up. The existing system has components but lacks resilience:
- State files corrupt easily (JSON → 2 days to recover)
- Multiple sync mechanisms compete (race conditions)
- File transfers fail silently (no retries/verification)
- Weak error recovery (failures cascade)

We're implementing a **proper distributed system foundation** with:
- SQLite authoritative state store (crash-safe, transactional)
- CRDT-based sync (mathematical convergence, conflict-free)
- Reliable file transfer (chunked, verified, retry)
- Self-healing mechanisms (automatic recovery from corruption/failures)

---

## WHERE WE'RE AT

**✅ STEP 0 COMPLETE** - Freeze & Prune
- Disabled all competing sync mechanisms (moved to `.DISABLED/`)
- Created temporary stub entry point
- Organized `rustic/` folder (reference/archive)
- Created `rusty/` folder (clean rebuild workspace)

**⏳ NEXT: STEP 1** - Authoritative State Store
- Create SQLite DB with WAL mode
- Transactional state mutations (append-only log)
- State snapshots + recovery from corruption
- Replace fragile JSON state files

---

## WHAT WE'RE HOPING TO ACHIEVE

### Foundation (Steps 1-8)

**STEP 1: Authoritative State Store**
- SQLite + WAL mode (crash-safe writes)
- Transaction log (append-only, replayable)
- State snapshots (recovery from corruption)
- No more 2-day recovery problem

**STEP 2: State Model**
- Ops-based state (no direct mutation)
- Deterministic, serializable, replayable
- `apply(op)` → state change

**STEP 3: CRDT Merge**
- Vector clocks (not wall-clock timestamps)
- OR-Map, LWW-Register
- Mathematical convergence guarantee

**STEP 4: Single Sync Engine**
- One daemon (no competing mechanisms)
- Exchange ops only (not full state)
- Retry with exponential backoff

**STEP 5: Files as Payloads**
- Chunked transfer (large files)
- Hash verification (integrity)
- Resume support (don't restart)

**STEP 6: Self-Healing**
- Survive kill/power loss/corruption
- Automatic recovery from all failure modes
- No human intervention required

**STEP 7: Adapters**
- OS adapters observe events → emit ops
- Apply merged state back to OS
- Adapters are dumb muscles (not brains)

**STEP 8: Demo Lock**
- Two nodes, offline, kill one, heal, converge
- If demo breaks, everything stops

---

## THE GOAL

**Resilient OMNI Organism:**
- If Windows crashes → Android takes over seamlessly
- If state corrupts → auto-heal from snapshot + log
- If network fails → queue ops, retry with backoff
- If file transfer fails → chunked retry with verification
- **No more 2-day recovery. No more losing work. No more fragile state.**

**Current state:** Components exist but architecture is fragile.

**Target state:** Proper distributed system foundation with mathematical guarantees.

---

## FOLDERS

**`rustic/`** - Organized reference/archive (preserved as-is)
- All historical components
- Experimental code in `experimental/`
- Separate projects in `projects/`
- Documentation in `docs/`

**`rusty/`** - Clean foundation rebuild workspace
- Essential components copied
- Foundation rebuild in `substrate/`
- Steps 1-8 will live here

---

**Status:** STEP 0 complete. Ready for STEP 1 (SQLite state store).
