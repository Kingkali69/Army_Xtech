#!/bin/bash
# OMNI Framework - Unified Launcher
# Just run: ./START.sh
# Auto-opens browser on all platforms

cd "$(dirname "$0")"

echo "OMNI Infrastructure Operations Console"
echo "======================================="
echo ""
echo "Starting web console..."
echo ""

# Launch web console (auto-opens browser)
python3 omni_web_console.py "$@"

