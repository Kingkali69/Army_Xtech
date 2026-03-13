# OMNI Quick Start

## 🚀 Launch

```bash
./START.sh
```

That's it! OMNI will:
- Auto-configure (platform, network, node ID)
- Start discovery (find peers on LAN)
- Start sync engine (exchange state with peers)
- Enable recovery (auto-heal from corruption)
- Work offline (no internet required)

## 📊 Check Status

```bash
python3 launch_omni.py --status
```

## 🔧 Requirements Met

✅ **Auto-configure** - Done  
✅ **Launch** - Done  
✅ **Sync & update** - Done  
✅ **Failover** - Done  
✅ **Recovery** - Done  
✅ **Discovery** - Done  
✅ **Offline first** - Done  
✅ **Airgapped** - Done  
✅ **Zero cloud dependency** - Done  

## 📁 Files

- `omni_core.py` - Main orchestrator
- `launch_omni.py` - Launcher script
- `START.sh` - Quick start script
- `~/.omni/config.json` - Auto-generated config
- `~/.omni/state.db` - State database

## 🌐 Network

- **Discovery**: UDP port 45678 (broadcast)
- **Sync**: TCP port 7777 (mesh)
- **Firewall**: Allow these ports for full functionality

## 🔍 Multiple Nodes

Run `./START.sh` on multiple machines:
- They'll discover each other automatically
- State syncs automatically
- Works on isolated LAN (no internet needed)

## 📖 Full Docs

See `OMNI_INTEGRATION.md` for complete documentation.
