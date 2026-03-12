# Launch Authority Model

**Formal definition of authority, ownership, and control boundaries in OMNI.**

---

## Purpose

This document defines:
- **Who** is allowed to launch what
- **Under what conditions** launch occurs
- **After which failures** recovery triggers
- **With which state guarantees** operations proceed
- **AI participation limits** and boundaries
- **Human override rules** and audit trails

**This is not marketing. This is a technical contract.**

---

## Core Principle: Substrate Ownership

### The Substrate Owns Launch Authority

The substrate layer is the **authoritative owner** of:
- Node lifecycle (start, stop, restart)
- State recovery (corruption, power loss)
- Cross-platform coordination (Linux ↔ Windows ↔ Android)
- Failure domain boundaries

**The OS is an adapter, not an owner.**

### What This Means

1. **Launch decisions** originate in the substrate
2. **OS services** (systemd, Windows Service, Android Service) are **executors**, not **deciders**
3. **State consistency** is guaranteed by the substrate, not the OS
4. **Recovery triggers** are substrate-defined, OS-agnostic

---

## Launch Ownership Hierarchy

```
┌─────────────────────────────────────┐
│   SUBSTRATE (Authoritative Owner)   │
│   - Launch decisions                │
│   - State guarantees                │
│   - Failure domain boundaries       │
│   - Recovery triggers               │
└──────────────┬──────────────────────┘
               │
       ┌───────┴────────┐
       │                │
┌──────▼──────┐  ┌─────▼──────┐
│ OS Adapter  │  │ AI Layer    │
│ (Executor)  │  │ (Participant)│
│             │  │             │
│ - systemd   │  │ - NEXUS     │
│ - Windows   │  │ - Commands   │
│ - Android   │  │ - Monitoring │
└─────────────┘  └─────────────┘
```

### 1. Substrate Layer (Authoritative)

**Owns:**
- Launch authority decisions
- State consistency guarantees
- Failure domain definitions
- Recovery trigger conditions

**Cannot be overridden by:**
- OS-level services
- User-level processes
- Network conditions
- Cloud services (none exist)

**Can be overridden by:**
- Explicit human intervention (see Override Rules)

### 2. OS Adapter Layer (Executor)

**Role:**
- Execute substrate launch decisions
- Provide OS-specific services (systemd, Windows Service)
- Report OS-level failures to substrate
- Apply state changes to OS filesystem

**Cannot:**
- Make launch decisions independently
- Override substrate state guarantees
- Bypass substrate recovery triggers

**Can:**
- Request substrate intervention on OS-level failures
- Report platform-specific constraints

### 3. AI Layer (Participant)

**Role:**
- Assist in launch decision-making (recommendations)
- Execute commands through substrate executor
- Monitor system health and predict failures
- Provide recovery coaching

**Cannot:**
- Override substrate authority
- Bypass human override rules
- Execute commands outside defined boundaries
- Make launch decisions without substrate approval

**Can:**
- Recommend launch actions
- Execute approved commands
- Monitor and report
- Learn from outcomes

---

## Failure Domains

### Domain 1: Node-Level Failure

**Scope:** Single node (Linux, Windows, or Android)

**Triggers:**
- Power loss
- Process crash
- State corruption
- Network disconnection

**Authority:**
- **Substrate** decides recovery strategy
- **OS Adapter** executes recovery (systemd restart, Windows Service restart)
- **AI** monitors and reports

**Guarantees:**
- State recovery from SQLite + WAL
- Automatic restart within 2.5 hours (systemd)
- Standalone mode if network unavailable

### Domain 2: Network Partition

**Scope:** Multiple nodes, network isolation

**Triggers:**
- LAN disconnection
- Android leaving network
- Network infrastructure failure

**Authority:**
- **Substrate** detects partition
- **Substrate** enters standalone mode
- **Substrate** queues operations for later sync
- **AI** monitors partition status

**Guarantees:**
- Nodes continue operating independently
- State divergence tracked via vector clocks
- Automatic reconciliation on reconnection
- No data loss (CRDT merge)

### Domain 3: State Corruption

**Scope:** SQLite database corruption

**Triggers:**
- Database file corruption
- WAL corruption
- Transaction log corruption

**Authority:**
- **Substrate** detects corruption
- **Substrate** triggers recovery from:
  1. Last known good snapshot
  2. Append-only log replay
  3. Peer state sync (if available)
- **OS Adapter** provides filesystem access
- **AI** reports corruption and recovery status

**Guarantees:**
- Recovery from snapshot + log (no data loss)
- Peer state sync as fallback
- Audit trail of recovery actions

### Domain 4: AI Command Execution Failure

**Scope:** NEXUS command execution errors

**Triggers:**
- Command execution failure
- Permission denied
- Timeout
- Invalid command

**Authority:**
- **Substrate** validates command before execution
- **Substrate** enforces execution boundaries
- **AI** receives execution results
- **AI** learns from failures

**Guarantees:**
- Commands execute through substrate (not direct OS calls)
- Execution boundaries enforced (SafeSubprocess)
- Audit trail of all AI commands
- Human override available

---

## Recovery Triggers

### Automatic Recovery (No Human Intervention)

**Triggered by:**
1. Process crash → Auto-restart (systemd/Windows Service)
2. Power loss → Auto-start on boot (systemd)
3. State corruption → Auto-recovery from snapshot + log
4. Network partition → Auto-standalone mode
5. File transfer failure → Auto-retry with exponential backoff

**Authority:** Substrate (automatic)

**Guarantees:**
- Recovery within defined timeframes
- State consistency maintained
- No data loss
- Audit trail created

### Human Intervention Required

**Triggered by:**
1. Multiple consecutive recovery failures
2. State corruption beyond recovery capability
3. Explicit human override request
4. Security violation detected

**Authority:** Human operator

**Process:**
1. Substrate reports failure to Operations Console
2. Human reviews failure in Event Timeline
3. Human executes override command
4. Substrate validates override
5. Recovery proceeds with human authority

**Guarantees:**
- All human interventions logged
- Override commands auditable
- State consistency maintained post-override

---

## AI Participation Limits

### What AI Can Do

1. **Recommend Actions**
   - Suggest file transfer routes
   - Recommend recovery strategies
   - Predict potential failures

2. **Execute Approved Commands**
   - Commands validated by substrate
   - Execution through SafeSubprocess
   - Results reported back to AI

3. **Monitor and Report**
   - System health monitoring
   - Anomaly detection
   - Performance metrics

4. **Learn from Outcomes**
   - Transfer results → routing optimization
   - Command failures → boundary learning
   - Recovery outcomes → strategy improvement

### What AI Cannot Do

1. **Override Substrate Authority**
   - Cannot bypass launch decisions
   - Cannot override recovery triggers
   - Cannot bypass state guarantees

2. **Execute Unvalidated Commands**
   - All commands go through substrate executor
   - SafeSubprocess enforces boundaries
   - No direct OS system calls

3. **Make Launch Decisions Independently**
   - AI recommends, substrate decides
   - AI monitors, substrate executes
   - AI learns, substrate enforces

4. **Bypass Human Override**
   - Human override always takes precedence
   - AI cannot prevent human intervention
   - AI reports all actions for audit

### AI Authority Boundary

```
AI Request → Substrate Validation → Execution → Results → AI Learning
     │              │                    │           │
     │              │                    │           │
     └──────────────┴────────────────────┴───────────┘
                    │
                    │
            [Human Override Available]
```

**Key Point:** AI is **privileged**, not **sovereign**.

---

## Human Override Rules

### When Override is Available

1. **Any time** - Human can always override
2. **Recovery failures** - After multiple automatic recovery attempts
3. **State corruption** - When automatic recovery insufficient
4. **Security concerns** - When suspicious activity detected
5. **Explicit request** - Human-initiated override

### Override Process

1. **Human initiates override** via Operations Console or command line
2. **Substrate validates override** (checks authority, logs action)
3. **Override executes** with human authority
4. **Results logged** in Event Timeline
5. **State updated** with override results

### Override Guarantees

- **Audit trail** - All overrides logged with timestamp, user, action
- **State consistency** - Override maintains state guarantees
- **Recovery** - System returns to automatic operation after override
- **No escalation** - Override cannot grant permanent elevated privileges

---

## Audit Trail Guarantees

### What is Audited

1. **Launch Events**
   - Node startup
   - Node shutdown
   - Recovery triggers
   - Override actions

2. **State Changes**
   - All state operations
   - CRDT merges
   - Recovery actions
   - Corruption events

3. **AI Actions**
   - Command execution requests
   - Command execution results
   - Recommendations made
   - Learning outcomes

4. **Network Events**
   - Peer discovery
   - Network partitions
   - Reconnection events
   - Sync operations

5. **Human Interventions**
   - Override commands
   - Manual recovery actions
   - Configuration changes

### Audit Trail Properties

- **Immutable** - Events cannot be deleted or modified
- **Chronological** - Events in timestamp order
- **Complete** - All authority decisions logged
- **Queryable** - Events searchable by type, time, node

### Audit Trail Storage

- **Primary:** SQLite database (`~/.omni/audit.db`)
- **Backup:** Append-only log file (`~/.omni/audit.log`)
- **Replication:** Synced to peers (if available)

---

## State Guarantees

### Launch State Guarantees

1. **Consistent State**
   - All nodes see consistent state after sync
   - CRDT merge ensures convergence
   - No split-brain scenarios

2. **Recovery Guarantees**
   - State recoverable from snapshot + log
   - No data loss on recovery
   - Recovery time bounded (2.5 hours max for auto-restart)

3. **Failure Isolation**
   - Node failures don't cascade
   - Network partitions handled gracefully
   - State corruption isolated to affected node

### What We Guarantee

✅ **State consistency** after sync  
✅ **Recovery** from corruption/power loss  
✅ **No data loss** on recovery  
✅ **Automatic operation** after recovery  
✅ **Audit trail** of all authority decisions  

### What We Don't Guarantee (Yet)

❌ **Five nines** uptime (not proven)  
❌ **Zero-downtime** failover (not proven)  
❌ **Formal proofs** of correctness (not done)  
❌ **Chaos engineering** results (not done)  

**We are architecturally capable of these guarantees. We have not yet proven them.**

---

## Launch Authority Contract Summary

### The Contract

1. **Substrate owns launch authority** - OS adapters execute, not decide
2. **AI participates, does not override** - AI is privileged, not sovereign
3. **Human override always available** - All overrides audited
4. **State guarantees enforced** - Consistency, recovery, isolation
5. **Audit trail maintained** - Immutable, chronological, complete

### The Guarantees

- **State consistency** after sync
- **Recovery** from failures
- **No data loss** on recovery
- **Automatic operation** after recovery
- **Audit trail** of all decisions

### The Boundaries

- **Substrate** decides, **OS** executes, **AI** participates
- **Human** can always override
- **State** is authoritative, **OS** is adapter
- **AI** is privileged, not sovereign

---

## Next Steps (To Earn "Five Nines")

To move from "architecturally capable" to "proven":

1. **Mean Time to Recovery (MTTR) Metrics**
   - Measure actual recovery times
   - Document recovery scenarios
   - Prove 2.5-hour auto-restart guarantee

2. **Fault Domain Documentation**
   - Map all failure modes
   - Document recovery strategies
   - Prove isolation guarantees

3. **Formal Failover Proofs**
   - Mathematical proofs of CRDT convergence
   - Formal verification of state guarantees
   - Proof of no split-brain scenarios

4. **Chaos Engineering Results**
   - Fault injection tests
   - Network partition tests
   - State corruption tests
   - Recovery time measurements

5. **Production Deployment Metrics**
   - Uptime measurements
   - Failure rate tracking
   - Recovery success rates
   - Performance under load

**Until these are done, we claim "architectural capability," not "five nines."**

---

## Conclusion

This document defines the **technical contract** for launch authority in OMNI.

**What we have:**
- Clear authority boundaries
- Defined failure domains
- Recovery triggers
- AI participation limits
- Human override rules
- Audit trail guarantees

**What we need:**
- Proof of guarantees (MTTR, chaos tests)
- Formal verification (mathematical proofs)
- Production metrics (uptime, failure rates)

**We are architecturally sound. We are not yet proven.**

This document is a **living contract** - it will be updated as we prove our guarantees.

---

**Last Updated:** January 27, 2025  
**Status:** Technical Contract (Not Marketing)  
**Next Review:** After first production deployment
