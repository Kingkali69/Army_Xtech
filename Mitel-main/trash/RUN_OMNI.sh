#!/bin/bash
# Quick launcher - just run the UI

cd "$(dirname "$0")"
python3 omni_ui.py "$@"
