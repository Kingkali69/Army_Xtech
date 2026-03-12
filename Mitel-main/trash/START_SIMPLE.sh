#!/bin/bash
# Simple NEXUS Launcher - UI Only (No Engine)

cd "/home/kali/Desktop/MITEL/Mitel-main"

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                🚀 NEXUS SIMPLE LAUNCHER                       ║"
echo "║                                                              ║"
echo "║  ⚡ CPU Optimized - UI Only                                  ║"
echo "║  🧠 No Engine Running                                        ║"
echo "║  🌐 Web Console Only                                         ║"
echo "║  💻 Normal CPU Usage                                         ║"
echo "║  🔌 No USB Monitoring                                        ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Kill any existing processes
echo "🧹 Killing any existing processes..."
pkill -f "omni_web_console.py" 2>/dev/null
pkill -f "simple_console.py" 2>/dev/null
pkill -f "omni_ai_chat.py" 2>/dev/null

# Wait for processes to die
sleep 2

# Kill any processes using our ports
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

# Start Simple Console (background)
echo "🚀 Starting Simple Console (CPU Optimized)..."
python3 simple_console.py --port 8888 &
CONSOLE_PID=$!

# Wait for console to start
sleep 2

# Start AI Chat (optional - lightweight)
echo "🤖 Starting AI Chat..."
python3 omni_ai_chat.py --port 8889 &
CHAT_PID=$!

# Wait for AI chat to start
sleep 2

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                     ✅ SIMPLE CONSOLE ACTIVE                   ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "🌐 Services Available:"
echo "   Simple Console: http://$LOCAL_IP:8888"
echo "   AI Chat:        http://$LOCAL_IP:8889"
echo ""
echo "🔧 Active Services:"
echo "   🖥️  Simple Console: ✅ RUNNING (PID $CONSOLE_PID)"
echo "   💬 AI Chat:        ✅ RUNNING (PID $CHAT_PID)"
echo ""
echo "⚡ CPU OPTIMIZATIONS:"
echo "   🧠 Engine: DISABLED"
echo "   💻 CPU Usage: NORMAL"
echo "   🔌 USB Monitoring: DISABLED"
echo "   🔄 Updates: DISABLED"
echo ""
echo "🎯 This is a lightweight console for testing UI only"
echo "💻 CPU usage should stay normal on Ryzen 9"
echo ""
echo "🌐 Browser should open automatically..."
echo "🛑 Press Ctrl+C to stop everything"
echo ""

# Keep terminal open and show status
echo "⏰ Simple Console monitoring... (Press Ctrl+C to stop)"
trap 'echo ""; echo "🛑 Stopping Simple Console..."; pkill -f "simple_console.py"; pkill -f "omni_ai_chat.py"; echo "✅ All services stopped"; exit 0' INT

# Monitor processes
while true; do
    clear
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                🚀 NEXUS SIMPLE CONSOLE                       ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""
    echo "🌐 Console: http://$LOCAL_IP:8888"
    echo "💬 AI Chat: http://$LOCAL_IP:8889"
    echo ""
    echo "⚡ STATUS:"
    echo "   🧠 Engine: DISABLED"
    echo "   💻 CPU Usage: NORMAL"
    echo "   🔌 USB Monitoring: DISABLED"
    echo ""
    echo "🔧 Process Status:"
    
    # Check each process
    if kill -0 $CONSOLE_PID 2>/dev/null; then
        echo "   🖥️  Simple Console: ✅ RUNNING (PID $CONSOLE_PID)"
    else
        echo "   🖥️  Simple Console: ❌ STOPPED"
    fi
    
    if kill -0 $CHAT_PID 2>/dev/null; then
        echo "   💬 AI Chat:        ✅ RUNNING (PID $CHAT_PID)"
    else
        echo "   💬 AI Chat:        ❌ STOPPED"
    fi
    
    echo ""
    echo "💻 CPU should be normal - no engine running"
    echo "🛑 Press Ctrl+C to stop everything"
    echo ""
    sleep 10
done
