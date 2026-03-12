#!/bin/bash
# Complete OMNI Launcher for Linux
# Starts Infrastructure Operations Console + Engine + AI Chat
# Requires root/sudo privileges for M.I.T.E.L. device enforcement

# Check for root privileges
if [ "$EUID" -ne 0 ]; then
    echo "======================================================================"
    echo "  ROOT PRIVILEGES REQUIRED"
    echo "======================================================================"
    echo ""
    echo "M.I.T.E.L. device quarantine enforcement requires root privileges."
    echo "Please run this script with sudo:"
    echo "  sudo ./launch_omni_linux.sh"
    echo ""
    exit 1
fi

cd "$(dirname "$0")"

echo "======================================================================"
echo "  OMNI COMPLETE LAUNCHER - Linux [ROOT MODE]"
echo "======================================================================"
echo ""
echo "Starting OMNI Infrastructure Operations Console..."
echo "Starting OMNI Engine..."
echo "Starting NEXUS AI Chat..."
echo ""

# Kill any existing instances
echo "Stopping any running OMNI processes..."
pkill -f "python.*omni_core.py" 2>/dev/null
pkill -f "python.*omni_web_console.py" 2>/dev/null
sleep 2

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3: sudo apt install python3 python3-pip"
    exit 1
fi

# Install Python dependencies if requirements.txt exists
if [ -f "requirements.txt" ]; then
    echo "Installing Python dependencies..."
    python3 -m pip install -r requirements.txt --quiet
fi

# Add firewall rules (silent, may need root but won't fail)
ufw allow 8888/tcp 2>/dev/null
ufw allow 8889/tcp 2>/dev/null

# Start OMNI Engine
echo "Starting OMNI Engine..."
python3 omni_core.py > /dev/null 2>&1 &
OMNI_CORE_PID=$!

# Wait for core to fully initialize and connect to mesh
echo "Waiting for OMNI Core to initialize and connect to mesh..."
sleep 8

# Verify core is running before continuing
if ! ps -p $OMNI_CORE_PID > /dev/null; then
    echo "ERROR: OMNI Core failed to start"
    exit 1
fi

# Start Web Console on port 8888
echo "Starting OMNI Web Console..."
sleep 2
python3 omni_web_console.py --port 8888 > /dev/null 2>&1 &
OMNI_CONSOLE_PID=$!

# NEXUS AI Chat runs on Linux mesh node (192.168.1.161:8889)
# No local AI chat needed - unified console has iframe to Linux NEXUS

# Wait for servers to start
echo ""
echo "Waiting for servers to start..."
sleep 13

# Open browser - try xdg-open first, then common browsers
echo ""
echo "Opening unified console..."
echo ""

if command -v xdg-open &> /dev/null; then
    xdg-open http://127.0.0.1:8888 &
elif command -v firefox &> /dev/null; then
    firefox http://127.0.0.1:8888 &
elif command -v google-chrome &> /dev/null; then
    google-chrome http://127.0.0.1:8888 &
elif command -v chromium-browser &> /dev/null; then
    chromium-browser http://127.0.0.1:8888 &
fi

echo ""
echo "======================================================================"
echo "  OMNI LAUNCHED"
echo "======================================================================"
echo ""
echo "OMNI Unified Console:"
echo "  http://127.0.0.1:8888"
echo "  (or http://localhost:8888)"
echo ""
echo "Tabs available:"
echo "  - OMNI Infrastructure (mesh topology, fabric health)"
echo "  - M.I.T.E.L. Security (device quarantine, zero-trust)"
echo "  - NEXUS AI (Linux-hosted at 192.168.1.161:8889)"
echo ""
echo "Processes running in background."
echo "  OMNI Core PID: $OMNI_CORE_PID"
echo "  Web Console PID: $OMNI_CONSOLE_PID"
echo ""
echo "To stop everything:"
echo "  sudo pkill -f 'python.*omni'"
echo ""
echo "======================================================================"
echo ""
echo "Everything is running!"
echo "Browser should open automatically..."
echo "If not, open the URLs above manually."
echo ""
echo "Press Ctrl+C to stop (processes will keep running in background)"
echo ""

# Keep script running to show it's active
wait
