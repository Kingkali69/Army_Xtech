#!/bin/bash
# OFFLINE TEST - Can you launch without internet?

echo "🔥 OFFLINE LAUNCH TEST"
echo "===================="

cd "/home/kali/Desktop/MITEL/Mitel-main"

echo "📂 Current directory: $(pwd)"
echo "🔍 Checking internet connection..."
ping -c 1 google.com 2>/dev/null && echo "🌐 Internet: CONNECTED" || echo "🌐 Internet: OFFLINE (GOOD!)"

echo ""
echo "🔍 Checking required files:"
for file in "omni_web_console.py" "START_SLOW_DEMO.sh" "SUPER_KILL.sh"; do
    if [ -f "$file" ]; then
        echo "✅ $file exists"
    else
        echo "❌ $file MISSING!"
    fi
done

echo ""
echo "🧹 Killing any existing processes..."
./SUPER_KILL.sh

echo ""
echo "🚀 Testing offline launch..."
echo "📝 This will start the console and create logs"
echo "📝 If it fails, check console.log for errors"

# Start the launcher with full logging
./START_SLOW_DEMO.sh

echo ""
echo "📋 TEST COMPLETE!"
echo "🌐 If successful, open: http://localhost:8888"
echo "📝 If failed, check: console.log"
echo "🔍 To check logs: cat console.log"
