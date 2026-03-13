#!/bin/bash
# NEXUS Container Engine Launcher
# Launches NEXUS Container + M.I.T.E.L. + Console + Terminal

cd "$(dirname "$0")"

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                    🚀 NEXUS CONTAINER ENGINE                   ║"
echo "║                                                              ║"
echo "║  🧠 Shared Consciousness Runtime                              ║"
echo "║  🔌 USB Event Monitoring (Linux Fix)                         ║"
echo "║  🛡️  M.I.T.E.L. Zero-Trust Security                            ║"
echo "║  🔧 Tool Registry & Sandbox Execution                          ║"
echo "║  📱 Cross-Platform Hive Intelligence                           ║"
echo "║                                                              ║"
echo "║  Built for ghosts by a ghost                                   ║"
echo "║  When trust matters the most, you ghost                       ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Kill any existing instances
echo "🧹 Cleaning up existing instances..."
pkill -f "omni_web_console.py" 2>/dev/null
pkill -f "omni_ai_chat.py" 2>/dev/null
pkill -f "nexus_container" 2>/dev/null
sleep 2

echo "🔥 Starting NEXUS Container Services..."
echo ""

# Start NEXUS Container (background)
python3 -c "
from substrate.ai_layer.nexus_container_layer import start_nexus_container
if start_nexus_container():
    print('✅ NEXUS Container started successfully')
else:
    print('❌ NEXUS Container failed to start')
    exit(1)
" &
NEXUS_PID=$!
echo "🧠 NEXUS Container PID: $NEXUS_PID"

# Wait for container to initialize
sleep 3

# Start M.I.T.E.L. with USB monitoring (background)
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
echo "🛡️  M.I.T.E.L. PID: $MITEL_PID"

# Wait for M.I.T.E.L. to initialize
sleep 2

# Start Infrastructure Operations Console (background)
echo "🚀 Starting Infrastructure Operations Console..."
python3 omni_web_console.py --port 8888 --no-browser &
CONSOLE_PID=$!
echo "🖥️  Console PID: $CONSOLE_PID"

# Start AI Chat (background)
echo "🤖 Starting NEXUS AI Chat..."
python3 omni_ai_chat.py --port 8889 --no-browser &
CHAT_PID=$!
echo "💬 AI Chat PID: $CHAT_PID"

# Wait for servers to start
echo ""
echo "⏳ Waiting for services to start..."
sleep 5

# Get local IP
LOCAL_IP=$(hostname -I | awk '{print $1}')
if [ -z "$LOCAL_IP" ]; then
    LOCAL_IP="127.0.0.1"
fi

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
echo "🌐 CONSOLE READY - Open manually:"
echo "   Infrastructure Operations Console: http://$LOCAL_IP:8888"
echo "   NEXUS AI Chat:                    http://$LOCAL_IP:8889"
echo ""
echo "💡 Instructions:"
echo "   1. Open the URLs above in your browser"
echo "   2. Plug/unplug USB devices to test event detection"
echo "   3. Use AI Chat for voice commands (when integrated)"
echo "   4. This terminal shows real-time engine output"
echo ""
echo "🛑 To stop everything:"
echo "   ./stop_nexus_engine.sh"
echo "   Or press Ctrl+C in this terminal"
echo ""

# Keep script running so processes stay alive
echo "⏰ NEXUS Engine running... (Press Ctrl+C to stop)"
trap 'echo ""; echo "🛑 Stopping NEXUS Engine..."; pkill -f "omni_web_console.py"; pkill -f "omni_ai_chat.py"; pkill -f "nexus_container"; echo "✅ All services stopped"; exit 0' INT

# Just wait for user to stop
while true; do
    sleep 10
done
