#!/bin/bash
# Simple NEXUS Launcher - No monitoring, no browser spam

cd "/home/kali/Desktop/MITEL/Mitel-main"

echo "🚀 Starting NEXUS Engine..."

# Kill any existing processes
pkill -f "omni_web_console.py" 2>/dev/null
pkill -f "omni_ai_chat.py" 2>/dev/null

# Start NEXUS Container
python3 -c "
from substrate.ai_layer.nexus_container_layer import start_nexus_container
start_nexus_container()
print('✅ NEXUS Container started')
" &

# Start Console (no browser)
python3 omni_web_console.py --port 8888 --no-browser &

# Start AI Chat (no browser)  
python3 omni_ai_chat.py --port 8889 --no-browser &

# Start M.I.T.E.L.
python3 -c "
from substrate.mitel_subsystem import MITELSubsystem
config = {'zero_trust': True, 'quarantine_unknown': True}
mitel = MITELSubsystem(config)
mitel.start()
print('✅ M.I.T.E.L. started')
" &

# Get IP
LOCAL_IP=$(hostname -I | awk '{print $1}')

echo ""
echo "✅ NEXUS ENGINE RUNNING!"
echo ""
echo "🌐 Open these URLs in your browser:"
echo "   Console: http://$LOCAL_IP:8888"
echo "   AI Chat: http://$LOCAL_IP:8889"
echo ""
echo "🔌 USB devices will be detected automatically"
echo ""
echo "🛑 To stop: pkill -f omni_web_console.py && pkill -f omni_ai_chat.py"
echo ""

# Just exit - no monitoring
exit 0
