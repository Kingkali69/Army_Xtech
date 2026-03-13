#!/bin/bash
# Complete OMNI Launcher
# Starts Infrastructure Operations Console + Engine + AI Chat
# Just double-click to launch everything

cd "$(dirname "$0")"

echo "======================================================================"
echo "  🚀 OMNI COMPLETE LAUNCHER"
echo "======================================================================"
echo ""
echo "Starting OMNI Infrastructure Operations Console..."
echo "Starting OMNI Engine..."
echo "Starting NEXUS AI Chat..."
echo ""

# Kill any existing instances
pkill -f "omni_web_console.py" 2>/dev/null
pkill -f "omni_ai_chat.py" 2>/dev/null
pkill -f "omni_core.py" 2>/dev/null
sleep 1

# Start OMNI Core Engine (background) - integrated into console
# The console starts the engine automatically, so we don't need separate process
echo "Note: OMNI Engine starts automatically with Operations Console"
ENGINE_PID="integrated"

# Wait a moment for engine to initialize
sleep 2

# Start Infrastructure Operations Console (port 8888)
echo "Starting Infrastructure Operations Console..."
python3 omni_web_console.py --port 8888 --no-browser &
CONSOLE_PID=$!
echo "  Console PID: $CONSOLE_PID"

# Start AI Chat (port 8889)
echo "Starting NEXUS AI Chat..."
python3 omni_ai_chat.py --port 8889 --no-browser &
AI_PID=$!
echo "  AI Chat PID: $AI_PID"

# Wait for servers to start
echo ""
echo "Waiting for servers to start..."
sleep 5

# Get local IP
LOCAL_IP=$(hostname -I | awk '{print $1}')
if [ -z "$LOCAL_IP" ]; then
    LOCAL_IP="127.0.0.1"
fi

# Open browsers
echo ""
echo "Opening browsers..."
echo ""

# Open Operations Console
python3 -c "
import webbrowser
import time
time.sleep(1)
webbrowser.open('http://$LOCAL_IP:8888')
print('✅ Operations Console opened')
" 2>/dev/null &

# Open AI Chat
python3 -c "
import webbrowser
import time
time.sleep(2)
webbrowser.open('http://$LOCAL_IP:8889')
print('✅ AI Chat opened')
" 2>/dev/null &

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
echo "To stop everything:"
echo "  ./stop_omni.sh"
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
echo "Browsers should open automatically..."
echo "If not, open the URLs above manually."
echo ""
echo "Press Ctrl+C to stop everything"
echo ""

# Keep script running so processes stay alive
wait
