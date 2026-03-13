#!/bin/bash
# Super Kill - Find and destroy all OMNI/NEXUS processes

echo "🔥 SUPER KILL - DESTROYING ALL OMNI/NEXUS PROCESSES..."

# Kill ALL Python processes with omni in the name
echo "🧹 Killing Python processes..."
for pid in $(ps aux | grep python | grep omni | awk '{print $2}'); do
    echo "  Killing PID $pid"
    kill -9 $pid 2>/dev/null
done

# Kill ALL shell scripts with launch in the name
echo "🧹 Killing launcher scripts..."
for pid in $(ps aux | grep bash | grep launch | awk '{print $2}'); do
    echo "  Killing PID $pid"
    kill -9 $pid 2>/dev/null
done

# Kill processes using our ports
echo "🧹 Killing processes on ports 8888 and 8889..."
lsof -ti:8888 | xargs kill -9 2>/dev/null
lsof -ti:8889 | xargs kill -9 2>/dev/null

# Kill any remaining NEXUS processes
echo "🧹 Killing NEXUS processes..."
pkill -f "nexus_container" 2>/dev/null
pkill -f "mitel_subsystem" 2>/dev/null

# Wait a moment
sleep 2

# Check if any remain
echo ""
echo "🔍 Checking for remaining processes..."
remaining=$(ps aux | grep -E "(omni|nexus|launch_omni)" | grep -v grep | wc -l)

if [ $remaining -eq 0 ]; then
    echo "✅ ALL OMNI/NEXUS PROCESSES DESTROYED!"
else
    echo "⚠️  Found $remaining remaining processes:"
    ps aux | grep -E "(omni|nexus|launch_omni)" | grep -v grep
    echo ""
    echo "🔥 Force killing remaining..."
    pkill -9 -f "omni" 2>/dev/null
    pkill -9 -f "nexus" 2>/dev/null
    pkill -9 -f "launch" 2>/dev/null
fi

echo ""
echo "🌐 CPU should be back to normal now"
echo "🎯 Your Ryzen 9 can breathe again!"
