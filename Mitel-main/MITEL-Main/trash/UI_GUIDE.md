# OMNI UI Guide

## 🖥️ Real-Time Dashboard

OMNI now has a **visual dashboard** that shows everything in real-time!

## Quick Start

```bash
# Launch with UI (default)
./START.sh

# Or directly
python3 omni_ui.py

# Simple mode (no interactive keys)
python3 omni_ui.py --simple
```

## What You'll See

The dashboard shows:

### Status Box
- **Node ID** - Your unique node identifier
- **Platform** - Linux/Windows/macOS/Android
- **Address** - IP:Port where you're listening
- **Status** - Online/Syncing/Recovering/Offline
- **Peers** - Number of connected peers
- **State Keys** - Number of keys in state tree
- **Master** - Whether you're the master node

### Peers Box
- List of all discovered peers
- Shows: Node ID, IP:Port, Platform
- Last seen time
- Health score

### Activity Box
- Real-time activity log
- Discovery events
- Sync events
- Status changes

## Interactive Commands

While the dashboard is running:

- **`r`** - Refresh/redraw dashboard
- **`s`** - Show status info
- **`p`** - Show peer count
- **`q`** - Quit

## Visual Indicators

- **● Green** - Online/Active
- **◐ Yellow** - Syncing/Processing
- **⟳ Yellow** - Recovering
- **○ Red** - Offline/Error
- **✓ Green** - Success
- **ℹ Blue** - Information

## Screenshot

```
╔══════════════════════════════════════════════════════════════════════════════╗
║  OMNI - Unified Orchestrator                                                ║
╠══════════════════════════════════════════════════════════════════════════════╣

║  STATUS                                                                      ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  Node ID: omni_44b1497b6d5...                                               ║
║  Platform: linux                                                             ║
║  Address: 192.168.1.161:7777                                                ║
║  Status: ● ONLINE                                                            ║
║  Peers: 2 connected                                                         ║
║  State Keys: 15                                                              ║
║  Master: No                                                                  ║
╠══════════════════════════════════════════════════════════════════════════════╣

║  PEERS (2)                                                                   ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  ● omni_abc123... @ 192.168.1.100:7777 (linux) - 5s ago                    ║
║  ● omni_def456... @ 192.168.1.101:7777 (windows) - 12s ago                  ║
╠══════════════════════════════════════════════════════════════════════════════╣

║  ACTIVITY                                                                    ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  ✓ OMNI core initialized                                                    ║
║  ✓ Discovery started on port 45678                                          ║
║  ✓ Mesh listener started on port 7777                                      ║
║  ✓ Sync engine started                                                      ║
║  ● 2 peer(s) discovered                                                     ║
╠══════════════════════════════════════════════════════════════════════════════╣

║  Commands: [r]efresh  [s]tatus  [p]eers  [q]uit                            ║
╚══════════════════════════════════════════════════════════════════════════════╝
Last update: 22:18:45
```

## That's It!

Just run `./START.sh` and you'll see the dashboard immediately showing:
- ✅ System is running
- ✅ What's happening
- ✅ Who's connected
- ✅ Real-time updates

**No more guessing - you can SEE it's working!**
