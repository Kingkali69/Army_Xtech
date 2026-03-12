#!/bin/bash
# NEXUS Engine Launcher - Kills everything, starts clean, opens browser

cd "/home/kali/Desktop/MITEL/Mitel-main"

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                    🚀 NEXUS ENGINE LAUNCHER                   ║"
echo "║                                                              ║"
echo "║  🔥 KILLING ALL PROCESSES FIRST                              ║"
echo "║  🧠 Starting NEXUS Container                                 ║"
echo "║  🔌 USB Event Monitoring (Linux Fix)                         ║"
echo "║  🛡️  M.I.T.E.L. Zero-Trust Security                            ║"
echo "║  🌐 Auto-Opening Browser                                     ║"
echo "║  📱 Terminal Stays Open                                      ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# KILL ALL EXISTING PROCESSES
echo "🧹 Killing all existing NEXUS processes..."
pkill -f "omni_web_console.py" 2>/dev/null
pkill -f "omni_ai_chat.py" 2>/dev/null
pkill -f "nexus_container" 2>/dev/null
pkill -f "mitel_subsystem" 2>/dev/null
pkill -f "launch_nexus_engine" 2>/dev/null
pkill -f "SIMPLE_LAUNCH" 2>/dev/null

# Wait for processes to die
sleep 3

# Kill any remaining Python processes using our ports
echo "🧹 Checking for remaining processes..."
lsof -ti:8888 | xargs kill -9 2>/dev/null
lsof -ti:8889 | xargs kill -9 2>/dev/null

echo "✅ All processes killed"
echo ""

# Get local IP
LOCAL_IP=$(hostname -I | awk '{print $1}')
if [ -z "$LOCAL_IP" ]; then
    LOCAL_IP="127.0.0.1"
fi

echo "🌐 Local IP: $LOCAL_IP"
echo ""

# Start NEXUS Container (background)
echo "🧠 Starting NEXUS Container..."
python3 -c "
from substrate.ai_layer.nexus_container_layer import start_nexus_container
if start_nexus_container():
    print('✅ NEXUS Container started successfully')
else:
    print('❌ NEXUS Container failed to start')
    exit(1)
" &
NEXUS_PID=$!

# Wait for container to initialize
sleep 3

# Start M.I.T.E.L. with USB monitoring (background)
echo "🛡️  Starting M.I.T.E.L. with USB monitoring..."
python3 -c "
from substrate.mitel_subsystem import MITELSubsystem
config = {'zero_trust': True, 'quarantine_unknown': True}
mitel = MITELSubsystem(config)

if mitel.start():
    print('✅ M.I.T.E.L. started with USB event monitoring')
    print('🔌 USB devices will be detected automatically')
else:
    print('❌ M.I.T.E.L. failed to start')
    
# Keep M.I.T.E.L. running
import time
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    mitel.stop()
    print('✅ M.I.T.E.L. stopped')
" &
MITEL_PID=$!

# Wait for M.I.T.E.L. to initialize
sleep 2

# Start Infrastructure Operations Console (background)
echo "🚀 Starting Infrastructure Operations Console..."
python3 omni_web_console.py --port 8888 &
CONSOLE_PID=$!

# Start AI Chat (background)
echo "🤖 Starting NEXUS AI Chat..."
python3 omni_ai_chat.py --port 8889 &
CHAT_PID=$!

# Wait for servers to start
echo ""
echo "⏳ Waiting for services to start..."
sleep 5

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                     ✅ NEXUS ENGINE ACTIVE                      ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "🌐 Services Available:"
echo "   Infrastructure Operations Console: http://$LOCAL_IP:8888"
echo "   NEXUS AI Chat:                    http://$LOCAL_IP:8889"
echo ""
echo "🔧 Active Services:"
echo "   🧠 NEXUS Container:     PID $NEXUS_PID"
echo "   🛡️  M.I.T.E.L.:           PID $MITEL_PID"
echo "   🖥️  Console:             PID $CONSOLE_PID"
echo "   💬 AI Chat:              PID $CHAT_PID"
echo ""
echo "🔌 USB Monitoring: ACTIVE (Linux udev events)"
echo "🛡️  Zero-Trust Security: ACTIVE"
echo "🧠 Hive Intelligence: ACTIVE"
echo "🔧 Tool Registry: READY"
echo ""

# Open browser automatically
echo "🌐 Opening browser..."
python3 -c "
import webbrowser
import time
time.sleep(1)
webbrowser.open('http://$LOCAL_IP:8888')
print('✅ Operations Console opened')
" 2>/dev/null &

echo ""
echo "🎯 NEXUS ENGINE IS RUNNING!"
echo ""
echo "💡 Instructions:"
echo "   1. Console opens automatically in browser"
echo "   2. Plug/unplug USB devices to test event detection"
echo "   3. Use UNQUARANTINE buttons in device list"
echo "   4. This terminal stays open for debugging"
echo "   5. Press Ctrl+C to stop everything"
echo ""
echo "🛑 To stop: Press Ctrl+C or close this terminal"
echo ""

# Keep terminal open and show processes
echo "⏰ NEXUS Engine monitoring... (Press Ctrl+C to stop)"
trap 'echo ""; echo "🛑 Stopping NEXUS Engine..."; pkill -f "omni_web_console.py"; pkill -f "omni_ai_chat.py"; pkill -f "nexus_container"; echo "✅ All services stopped"; exit 0' INT

# Monitor processes and show status
while true; do
    clear
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                    🚀 NEXUS ENGINE STATUS                    ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""
    echo "🌐 Console: http://$LOCAL_IP:8888"
    echo "💬 AI Chat: http://$LOCAL_IP:8889"
    echo ""
    echo "🔧 Process Status:"
    
    # Check each process
    if kill -0 $CONSOLE_PID 2>/dev/null; then
        echo "   🖥️  Console:             ✅ RUNNING (PID $CONSOLE_PID)"
    else
        echo "   🖥️  Console:             ❌ STOPPED"
    fi
    
    if kill -0 $CHAT_PID 2>/dev/null; then
        echo "   💬 AI Chat:              ✅ RUNNING (PID $CHAT_PID)"
    else
        echo "   💬 AI Chat:              ❌ STOPPED"
    fi
    
    if kill -0 $NEXUS_PID 2>/dev/null; then
        echo "   🧠 NEXUS Container:     ✅ RUNNING (PID $NEXUS_PID)"
    else
        echo "   🧠 NEXUS Container:     ❌ STOPPED"
    fi
    
    if kill -0 $MITEL_PID 2>/dev/null; then
        echo "   🛡️  M.I.T.E.L.:           ✅ RUNNING (PID $MITEL_PID)"
    else
        echo "   🛡️  M.I.T.E.L.:           ❌ STOPPED"
    fi
    
    echo ""
    echo "🔌 USB devices will be detected automatically"
    echo "🛑 Press Ctrl+C to stop everything"
    echo ""
    sleep 5
done
