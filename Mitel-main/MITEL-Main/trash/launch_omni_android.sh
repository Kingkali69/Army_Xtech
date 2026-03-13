#!/bin/bash
# Complete OMNI Launcher for Android (Termux)
# Starts Infrastructure Operations Console + Engine + AI Chat
# Run from Termux: bash launch_omni_android.sh

cd "$(dirname "$0")"

echo "======================================================================"
echo "  🚀 OMNI COMPLETE LAUNCHER - Android"
echo "======================================================================"
echo ""
echo "Starting OMNI Infrastructure Operations Console..."
echo "Starting OMNI Engine..."
echo "Starting NEXUS AI Chat..."
echo ""

# Check if running on Android
if [ ! -d "/data/data/com.termux" ] && [ -z "$ANDROID_ROOT" ]; then
    echo "⚠️  Warning: This doesn't appear to be Android/Termux"
    echo "   Continuing anyway..."
    echo ""
fi

# Kill any existing instances
pkill -f "omni_web_console.py" 2>/dev/null
pkill -f "omni_ai_chat.py" 2>/dev/null
pkill -f "omni_core.py" 2>/dev/null
sleep 1

# Start Infrastructure Operations Console (port 8888)
echo "Starting Infrastructure Operations Console..."
nohup python3 omni_web_console.py --port 8888 --no-browser > /tmp/omni_console.log 2>&1 &
CONSOLE_PID=$!
echo "  Console PID: $CONSOLE_PID"

# Start AI Chat (port 8889)
echo "Starting NEXUS AI Chat..."
nohup python3 omni_ai_chat.py --port 8889 --no-browser > /tmp/omni_ai.log 2>&1 &
AI_PID=$!
echo "  AI Chat PID: $AI_PID"

# Wait for servers to start
echo ""
echo "Waiting for servers to start..."
sleep 5

# Get local IP (Android-specific)
LOCAL_IP=$(ip route get 1.1.1.1 2>/dev/null | awk '{print $7; exit}')
if [ -z "$LOCAL_IP" ]; then
    # Try alternative method
    LOCAL_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -1)
fi
if [ -z "$LOCAL_IP" ]; then
    LOCAL_IP="127.0.0.1"
fi

echo ""
echo "======================================================================"
echo "  ✅ OMNI LAUNCHED"
echo "======================================================================"
echo ""
echo "Infrastructure Operations Console:"
echo "  http://$LOCAL_IP:8888"
echo ""
echo "NEXUS AI Chat:"
echo "  http://$LOCAL_IP:8889"
echo ""
echo "Processes running:"
echo "  Operations Console (includes Engine): PID $CONSOLE_PID"
echo "  AI Chat: PID $AI_PID"
echo ""
echo "To access from another device on the same network:"
echo "  Use the IP addresses above"
echo ""
echo "To stop everything:"
echo "  ./stop_omni_android.sh"
echo ""
echo "Or manually:"
echo "  pkill -f omni_web_console.py"
echo "  pkill -f omni_ai_chat.py"
echo ""
echo "======================================================================"
echo ""
echo "✅ Everything is running!"
echo "   Operations Console: http://$LOCAL_IP:8888"
echo "   AI Chat: http://$LOCAL_IP:8889"
echo ""
echo "Note: On Android, you may need to:"
echo "  1. Open these URLs in a browser manually"
echo "  2. Allow Termux to access network if prompted"
echo ""
echo "Press Ctrl+C to stop everything"
echo ""

# Keep script running so processes stay alive
wait
