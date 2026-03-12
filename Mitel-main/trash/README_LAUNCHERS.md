# OMNI Launchers - Cross-Platform Setup

Easy launchers for all platforms. Just download the repo and run the launcher for your platform.

---

## 🐧 Linux

### Launch:
```bash
./launch_omni_complete.sh
```

Or double-click `LAUNCH_OMNI.sh` on your desktop.

### Stop:
```bash
./stop_omni.sh
```

---

## 🪟 Windows

### Launch (Choose one):

**Option 1: Batch File (Easiest)**
- Double-click `launch_omni_windows.bat`
- Works on all Windows versions

**Option 2: PowerShell (Recommended)**
- Right-click `launch_omni_windows.ps1`
- Select "Run with PowerShell"
- Or double-click if PowerShell is associated with .ps1 files

### Stop:
- Double-click `stop_omni_windows.bat`
- Or run `stop_omni_windows.ps1` in PowerShell

---

## 📱 Android (Termux)

### Prerequisites:
1. Install [Termux](https://termux.com/) from F-Droid
2. Install Python 3 in Termux:
   ```bash
   pkg update
   pkg install python python-pip
   ```

### Launch:
```bash
bash launch_omni_android.sh
```

### Stop:
```bash
bash stop_omni_android.sh
```

### Access from Browser:
- Open browser on Android
- Navigate to: `http://127.0.0.1:8888` (Operations Console)
- Navigate to: `http://127.0.0.1:8889` (AI Chat)
- Or use your Android device's IP address from another device on the same network

---

## 🚀 What Gets Started

All launchers start:
1. **OMNI Infrastructure Operations Console** (port 8888)
   - System monitoring and observation
   - Real-time telemetry
   - Event timeline

2. **NEXUS AI Chat** (port 8889)
   - First-class citizen AI
   - Command execution capability
   - Intelligent assistance

3. **OMNI Engine** (integrated)
   - State management
   - File transfers
   - Auto-discovery
   - Self-healing

---

## 📋 Quick Start

1. **Download the repo** to your platform
2. **Run the launcher** for your platform:
   - Linux: `./launch_omni_complete.sh`
   - Windows: `launch_omni_windows.bat` (double-click)
   - Android: `bash launch_omni_android.sh`
3. **Browsers open automatically** (Linux/Windows)
4. **Access the interfaces:**
   - Operations Console: `http://localhost:8888`
   - AI Chat: `http://localhost:8889`

---

## 🔧 Troubleshooting

### Windows:
- If PowerShell script won't run: Right-click → Properties → Unblock → OK
- If Python not found: Install Python 3 and add to PATH
- If ports in use: Close other instances first

### Android:
- If Python not found: Run `pkg install python` in Termux
- If network access denied: Allow Termux network permissions
- If browser won't open: Manually navigate to `http://127.0.0.1:8888`

### Linux:
- If permission denied: `chmod +x launch_omni_complete.sh`
- If Python not found: Install Python 3: `sudo apt install python3`

---

## 📝 Notes

- All launchers are **user-friendly** - just double-click or run
- Servers run in **background** (Windows/Android) or **foreground** (Linux)
- To stop: Use the stop scripts or close the terminal window
- **No configuration needed** - everything auto-configures on first run

---

**Ready to launch!** 🚀
