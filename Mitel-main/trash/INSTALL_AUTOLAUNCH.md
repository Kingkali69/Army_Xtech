# Install Auto-Launch (Power Outage Survival)

## Quick Install

```bash
cd /home/kali/Desktop/rusty
./substrate/autolaunch/install_autolaunch.sh
```

## What It Does

**Auto-Launch Service:**
- ✅ Auto-starts on boot
- ✅ Auto-restarts on failure (10 second delay)
- ✅ Survives power outages
- ✅ No human intervention needed

**After Power Outage:**
1. Power returns
2. System boots
3. Service auto-starts (systemd)
4. OMNI auto-discovers peers
5. System is back online

**This is how you test failover in airgapped environment!**

## Manual Install

```bash
# Generate service file
python3 substrate/autolaunch/systemd_service.py

# Install
sudo cp /tmp/omni-console.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable omni-console.service
sudo systemctl start omni-console.service
```

## Verify

```bash
# Check status
sudo systemctl status omni-console.service

# Check logs
sudo journalctl -u omni-console.service -f
```

## Test Power Outage

1. System running
2. **Unplug power** (simulates outage)
3. System stops
4. **Plug power back in**
5. System boots
6. **Service auto-starts** (verify with: `sudo systemctl status omni-console.service`)
7. System is back online

**Ready for failover testing!** 🔌⚡
