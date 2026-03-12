# OMNI Infrastructure Operations Console

## Design Principles

### First Principle (Non-Negotiable)

**The UI must NEVER be the control plane.**

It is a **window**, not a lever.

The console is **observation-only**. **Read-only**. **Trusted**.

---

## Mental Model

**NORAD × NOC × Flight Deck × War Room**

Not a hacker dashboard.  
Not a game HUD.  
Not a DevOps panel.

Those look cool — and they kill systems.

---

## Layout Specification

### 1. TOP BAND — System State Bar (Always Visible)

**Single line. No animation.**

```
GLOBAL STATUS: OPERATIONAL | EPOCH 1842 | MESH NODES: 317 | QUORUM: STABLE
LATENCY: 9ms avg | FAILOVERS (24h): 2 | THREATS: 31 | DEGRADED ZONES: 1
```

**Purpose:**
- Executives understand it in 3 seconds
- Operators trust it
- Nothing clickable

**Color rules:**
- Green / Amber / Red only
- No gradients
- No neon

---

### 2. LEFT PANEL — Physical/Logical Map (Primary View)

**This is the main screen.**

- Geographic map OR abstract topology
- Nodes as **simple glyphs**
- Links as **thin lines**
- Thickness = bandwidth
- Color = health
- Pulse = data flow (slow, subtle)

**No explosions. No lightning. No fireworks.**

If a node dies:
- it **fades**
- routes re-draw calmly
- no drama

This is how real infrastructure looks when it works.

---

### 3. RIGHT PANEL — Metrics Stack (Read-Only)

**Vertical cards. Each card is one truth.**

Example cards:
- Mesh Health
- Control Plane Status
- Failover Engine
- Security Subsystems
- Data Integrity

**Each card:**
- 3–5 metrics max
- numbers + sparklines
- no buttons

This is where engineers live.

---

### 4. BOTTOM STRIP — Event Timeline (The Most Important Part)

**Chronological, immutable, append-only.**

```
14:32:11  [SYSTEM]  Console initialized
14:32:12  [MESH]    Mesh connectivity: 2 peer(s)
14:32:13  [SYSTEM]  Observation mode active
14:32:14  [MESH]    Node discovered: omni_abc123...
```

**This is what auditors, DARPA, DoD, SpaceX care about.**

**If it's not here, it didn't happen.**

---

## What It Must NEVER Look Like

❌ No push buttons on main screen  
❌ No "Attack / Defend / Execute"  
❌ No auto-actions triggered from UI  
❌ No animations tied to decisions  
❌ No "god mode" visuals  

If it looks like a video game, it will never pass:
- military review
- aerospace review
- national infrastructure review

---

## Color & Style Rules (Hard Rules)

- **Dark neutral background** (charcoal, not black)
- **Muted cyan / amber / red accents**
- **No purple**
- **No pink**
- **No neon green**
- **Typography:** mono + humanist sans
- **Motion budget:** near zero

**Boring = trusted.**

---

## One Sentence Truth

If a senator, general, or infrastructure chief walks in the room, they should say:

> **"That looks calm. That looks under control."**

Not:

> **"What the hell am I looking at?"**

---

## Implementation

### File: `omni_console.py`

- **Observation-only** - No control functions
- **Read-only** - No write operations
- **Event timeline** - Immutable, append-only log
- **Professional styling** - Muted colors, no neon
- **Trusted appearance** - Calm, controlled, boring

### Usage

```bash
# Launch console
./START.sh

# Or directly
python3 omni_console.py
```

---

## Separation of Concerns

### OPERATOR VIEW (Default)
- Observation-only
- Read-only
- Always safe
- This console

### SIMULATION / TRAINING VIEW (Separate)
- AR/VR
- Lightning
- Serpentine belts
- AI narration
- Threat visualization

**Physically and logically separated.**
Different ports. Different processes. Different permissions.

---

## Status

✅ **Console implemented**  
✅ **Observation-only**  
✅ **Professional styling**  
✅ **Event timeline**  
✅ **Metrics stack**  
✅ **System state bar**  

**Ready for infrastructure operations.**
