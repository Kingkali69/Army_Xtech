#!/bin/bash
# Stop NEXUS Engine Services

echo "🛑 Stopping NEXUS Engine Services..."

# Stop all services
echo "🧹 Cleaning up processes..."
pkill -f "omni_web_console.py" 2>/dev/null
pkill -f "omni_ai_chat.py" 2>/dev/null
pkill -f "nexus_container" 2>/dev/null
pkill -f "mitel_subsystem" 2>/dev/null

# Wait for processes to stop
sleep 3

# Verify processes are stopped
if pgrep -f "omni_web_console.py" > /dev/null; then
    echo "⚠️  Some console processes still running, force killing..."
    pkill -9 -f "omni_web_console.py" 2>/dev/null
fi

if pgrep -f "omni_ai_chat.py" > /dev/null; then
    echo "⚠️  Some AI chat processes still running, force killing..."
    pkill -9 -f "omni_ai_chat.py" 2>/dev/null
fi

echo "✅ NEXUS Engine stopped successfully"
echo ""
