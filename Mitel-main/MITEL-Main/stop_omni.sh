#!/bin/bash
# Stop all OMNI processes

echo "Stopping OMNI..."
pkill -f "omni_web_console.py" 2>/dev/null
pkill -f "omni_ai_chat.py" 2>/dev/null
pkill -f "omni_core.py" 2>/dev/null
sleep 1
echo "✅ OMNI stopped"
