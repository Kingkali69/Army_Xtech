#!/bin/bash
# Graceful shutdown with control file

echo "🛑 Graceful shutdown with control file..."

# Create control file to signal intentional shutdown
sudo touch /var/run/nexus.manual_stop 2>/dev/null || touch /tmp/nexus.manual_stop

echo "✅ Control file created - auto-launch will not restart"

# Kill all processes
pkill -f "omni_web_console.py" 2>/dev/null
pkill -f "omni_ai_chat.py" 2>/dev/null
pkill -f "launch_omni_complete" 2>/dev/null

# Stop systemd service
systemctl stop omni-autolaunch.service 2>/dev/null

echo "🎯 NEXUS stopped gracefully - auto-launch disabled"
echo ""
echo "🔄 To re-enable auto-launch:"
echo "   sudo rm /var/run/nexus.manual_stop"
