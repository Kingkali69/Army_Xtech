#!/bin/bash
# QUICK START - Just the web console, no AI loading

cd "/home/kali/Desktop/MITEL/Mitel-main"

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                 🚀 QUICK START LAUNCHER                     ║"
echo "║                                                              ║"
echo "║  ⚡ Web Console Only (No AI Loading)                        ║"
echo "║  🌐 Fast Start (5 seconds)                                  ║"
echo "║  💻 Ready for Testing                                       ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# Kill any existing processes
echo "🧹 Cleaning up..."
pkill -f "simple_console.py" 2>/dev/null
pkill -f "python3.*8888" 2>/dev/null
sleep 1

# Get local IP
LOCAL_IP=$(hostname -I | awk '{print $1}')

# Start Simple Console ONLY
echo "🚀 Starting Web Console..."
python3 simple_console.py --port 8888 &
CONSOLE_PID=$!

# Wait for console to start
sleep 3

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                     ✅ QUICK START ACTIVE                    ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "🌐 Web Console: http://$LOCAL_IP:8888"
echo ""
echo "🔧 Status:"
echo "   🖥️  Web Console: ✅ RUNNING (PID $CONSOLE_PID)"
echo ""
echo "💡 Next Steps:"
echo "   1. Open browser to: http://$LOCAL_IP:8888"
echo "   2. Verify console loads"
echo "   3. Test basic functionality"
echo ""
echo "🛑 To stop: pkill -f simple_console.py"
echo ""

# Keep terminal open
echo "📋 Console running. Press Ctrl+C to stop..."
tail -f /dev/null &
