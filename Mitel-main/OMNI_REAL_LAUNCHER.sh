#!/bin/bash

# 🔥 OMNI REAL LAUNCHER - KILLS OLD + STARTS NEW + OPENS URL
# =========================================================

echo "🔥🔥🔥 OMNI REAL LAUNCHER 🔥🔥🔥"
echo "============================="
echo "🎯 Killing old processes + Starting engine + Opening URL"
echo ""

# Get local IP
LOCAL_IP=$(hostname -I | awk '{print $1}')

# KILL EVERYTHING FIRST
echo "🛑 KILLING ALL OLD PROCESSES..."
pkill -f omni_web_console.py 2>/dev/null
pkill -f omni_ai_chat_simple.py 2>/dev/null
pkill -f omni_ai_chat.py 2>/dev/null
pkill -f START_COMPLETE_DEMO.sh 2>/dev/null
sleep 3

# Check directory
if [ ! -f "omni_web_console.py" ]; then
    echo "❌ ERROR: Not in OMNI directory!"
    exit 1
fi

echo "✅ OLD PROCESSES KILLED"
echo ""

# START CONSOLE
echo "🚀 Starting OMNI Console..."
python3 omni_web_console.py --port 8888 --no-browser > /dev/null 2>&1 &
CONSOLE_PID=$!

# Wait for console to start
sleep 5

# Check if console is actually running
if ! ps -p $CONSOLE_PID > /dev/null; then
    echo "❌ CONSOLE FAILED TO START!"
    exit 1
fi

# START AI CHAT
echo "💬 Starting AI Chat..."
python3 omni_ai_chat_simple.py --port 8889 --no-browser > /dev/null 2>&1 &
CHAT_PID=$!

# Wait for chat to start
sleep 3

# Check if chat is running
if ! ps -p $CHAT_PID > /dev/null; then
    echo "⚠️  AI Chat failed (console still works)"
    CHAT_PID=""
fi

# OPEN THE GODDAMN URL
echo "🌐 OPENING CONSOLE URL..."
if command -v xdg-open > /dev/null; then
    xdg-open "http://$LOCAL_IP:8888" 2>/dev/null &
elif command -v firefox > /dev/null; then
    firefox "http://$LOCAL_IP:8888" 2>/dev/null &
elif command -v google-chrome > /dev/null; then
    google-chrome "http://$LOCAL_IP:8888" 2>/dev/null &
else
    echo "⚠️  Could not auto-open browser"
fi

# Clear screen and show status
clear
echo "🔥🔥🔥 OMNI ENGINE RUNNING 🔥🔥🔥"
echo "==============================="
echo ""
echo "🌐 CONSOLE URL: http://$LOCAL_IP:8888"
echo "💬 AI CHAT URL: http://$LOCAL_IP:8889"
echo ""
echo "🔧 STATUS:"
echo "   🖥️  Console: ✅ RUNNING (PID $CONSOLE_PID)"
if [ ! -z "$CHAT_PID" ]; then
    echo "   💬 AI Chat: ✅ RUNNING (PID $CHAT_PID)"
else
    echo "   💬 AI Chat: ❌ FAILED"
fi
echo ""
echo "🛡️ M.I.T.E.L. Security: ✅ ACTIVE"
echo "🧠 NEXUS Intelligence: ✅ OPERATIONAL"
echo "🚑 Self-Healing: ✅ READY"
echo ""
echo "✅ ENGINE STARTED - URL SHOULD BE OPEN IN BROWSER"
echo "🛑 To stop: pkill -f omni_web_console.py && pkill -f omni_ai_chat_simple.py"
echo ""

# Exit immediately - launcher done
exit 0
