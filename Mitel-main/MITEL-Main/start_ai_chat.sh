#!/bin/bash
# Start AI Chat Server
# Keeps running even if browser refreshes

cd "$(dirname "$0")"

echo "======================================================================"
echo "  Starting OMNI AI Chat Server"
echo "======================================================================"
echo ""

# Kill any existing instances
pkill -f "omni_ai_chat.py" 2>/dev/null
sleep 1

# Start server
python3 omni_ai_chat.py --port 8889
