#!/bin/bash

# NEXUS OMNIPRESENT INSTALLER
# ==========================
# Install NEXUS daemon and UI for omnipresent control

echo "🔥 NEXUS OMNIPRESENT INSTALLER"
echo "==============================="
echo "🚀 Installing JARVIS omnipresent system..."
echo ""

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo "❌ Don't run as root. Run as regular user."
   exit 1
fi

# Get installation directory
INSTALL_DIR="/home/kali/Desktop/MITEL/Mitel-main/nexus_omnipresent"
SYSTEMD_DIR="$HOME/.config/systemd/user"

echo "📁 Installation directory: $INSTALL_DIR"
echo "🔧 Systemd directory: $SYSTEMD_DIR"
echo ""

# Create directories
mkdir -p "$SYSTEMD_DIR"
mkdir -p "$HOME/.local/bin"

# Make scripts executable
echo "🔧 Making scripts executable..."
chmod +x "$INSTALL_DIR/nexus_daemon.py"
chmod +x "$INSTALL_DIR/nexus_ui.py"

# Create systemd service for daemon
echo "🔧 Creating systemd service..."
cat > "$SYSTEMD_DIR/nexus-daemon.service" << EOF
[Unit]
Description=NEXUS Omnipresent Daemon
After=graphical-session.target

[Service]
Type=simple
Restart=always
RestartSec=5
ExecStart=/usr/bin/python3 $INSTALL_DIR/nexus_daemon.py
WorkingDirectory=$INSTALL_DIR
StandardOutput=file:$HOME/.local/share/nexus/daemon.log
StandardError=file:$HOME/.local/share/nexus/daemon.error.log

[Install]
WantedBy=default.target
EOF

# Create log directory
mkdir -p "$HOME/.local/share/nexus"

# Create desktop launcher for UI
echo "🔧 Creating desktop launcher..."
cat > "$HOME/Desktop/NEXUS_CONTROL.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=NEXUS CONTROL
Comment=Launch NEXUS Omnipresent Control
Exec=/usr/bin/python3 $INSTALL_DIR/nexus_ui.py
Icon=applications-system
Terminal=false
Categories=System;Security;
StartupNotify=true
EOF

chmod +x "$HOME/Desktop/NEXUS_CONTROL.desktop"

# Create command-line launcher
echo "🔧 Creating command-line launcher..."
cat > "$HOME/.local/bin/nexus" << 'EOF'
#!/bin/bash
# NEXUS command-line interface

case "$1" in
    start)
        python3 /home/kali/Desktop/MITEL/Mitel-main/nexus_omnipresent/nexus_ui.py &
        ;;
    stop)
        pkill -f nexus_ui.py
        ;;
    daemon)
        python3 /home/kali/Desktop/MITEL/Mitel-main/nexus_omnipresent/nexus_daemon.py
        ;;
    status)
        if pgrep -f nexus_daemon.py > /dev/null; then
            echo "✅ NEXUS daemon running"
        else
            echo "❌ NEXUS daemon not running"
        fi
        ;;
    *)
        echo "Usage: nexus {start|stop|daemon|status}"
        echo "  start   - Launch NEXUS UI"
        echo "  stop    - Stop NEXUS UI"
        echo "  daemon  - Run NEXUS daemon"
        echo "  status  - Check daemon status"
        ;;
esac
EOF

chmod +x "$HOME/.local/bin/nexus"

# Reload systemd and enable service
echo "🔧 Enabling systemd service..."
systemctl --user daemon-reload
systemctl --user enable nexus-daemon.service

# Start the daemon
echo "🚀 Starting NEXUS daemon..."
systemctl --user start nexus-daemon.service

# Wait for daemon to start
sleep 3

# Check if daemon is running
if systemctl --user is-active --quiet nexus-daemon.service; then
    echo "✅ NEXUS daemon started successfully"
else
    echo "❌ NEXUS daemon failed to start"
    echo "📋 Check logs with: journalctl --user -u nexus-daemon"
fi

echo ""
echo "🔥🔥🔥 INSTALLATION COMPLETE! 🔥🔥🔥"
echo "=================================="
echo ""
echo "🎯 How to use NEXUS:"
echo ""
echo "1. Desktop UI:"
echo "   Double-click 'NEXUS CONTROL' on desktop"
echo ""
echo "2. Command line:"
echo "   nexus start    - Launch UI"
echo "   nexus status   - Check daemon"
echo "   nexus daemon   - Run daemon manually"
echo ""
echo "3. Voice commands (when UI is running):"
echo "   Say 'NEXUS' to activate"
echo "   Then 'Start OMNI' to launch engine"
echo ""
echo "🌐 Available commands in UI:"
echo "   • START OMNI    - Launch full OMNI system"
echo "   • STOP OMNI     - Stop all OMNI services"
echo "   • RESTART OMNI  - Restart OMNI system"
echo "   • STATUS        - Check system status"
echo "   • FIX BROKEN    - Auto-repair services"
echo "   • KILL PORT     - Kill process on port"
echo "   • CLEAR PYTHON  - Clear all Python processes"
echo ""
echo "📋 Daemon logs: $HOME/.local/share/nexus/daemon.log"
echo "📋 Systemd logs: journalctl --user -u nexus-daemon"
echo ""
echo "🚀 NEXUS is now OMNIPRESENT!"
echo "🔥 JARVIS is ready to execute your commands!"
