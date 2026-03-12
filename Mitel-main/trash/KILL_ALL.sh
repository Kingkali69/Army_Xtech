#!/bin/bash
# Kill all NEXUS processes to free up CPU

echo "🔥 KILLING ALL NEXUS PROCESSES..."

# Kill all Python processes related to NEXUS
pkill -f "omni_web_console.py" 2>/dev/null
pkill -f "omni_ai_chat.py" 2>/dev/null
pkill -f "nexus_container" 2>/dev/null
pkill -f "mitel_subsystem" 2>/dev/null
pkill -f "launch_nexus_engine" 2>/dev/null
pkill -f "START_NEXUS_ENGINE" 2>/dev/null
pkill -f "SIMPLE_LAUNCH" 2>/dev/null

# Kill any processes using our ports
lsof -ti:8888 | xargs kill -9 2>/dev/null
lsof -ti:8889 | xargs kill -9 2>/dev/null

# Kill UI sync processes
pkill -f "unified_state_engine" 2>/dev/null
pkill -f "unified_ui_engine" 2>/dev/null

# Kill Trinity AI processes
pkill -f "trinity_evolution" 2>/dev/null
pkill -f "universal_ai_agent" 2>/dev/null

echo "✅ ALL PROCESSES KILLED!"
echo ""
echo "🌐 CPU should be back to normal now"
echo "🎯 You can now restart with the desktop launcher"
