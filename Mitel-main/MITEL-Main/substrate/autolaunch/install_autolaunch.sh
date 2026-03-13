#!/bin/bash
# Install Auto-Launch Service
# Survives power outages - auto-restarts after power returns

set -e

WORKSPACE_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
CURRENT_USER=$(whoami)
PYTHON_PATH=$(which python3)

echo "=========================================="
echo "  OMNI Auto-Launch Installation"
echo "=========================================="
echo ""
echo "Workspace: $WORKSPACE_DIR"
echo "User: $CURRENT_USER"
echo "Python: $PYTHON_PATH"
echo ""

# Create systemd service file
SERVICE_FILE="/tmp/omni-console.service"

cat > "$SERVICE_FILE" << EOF
[Unit]
Description=OMNI Infrastructure Operations Console
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=$CURRENT_USER
WorkingDirectory=$WORKSPACE_DIR
ExecStart=$PYTHON_PATH $WORKSPACE_DIR/omni_web_console.py --port 8888
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Auto-restart on failure
StartLimitInterval=0
StartLimitBurst=0

# Survive power outages
RemainAfterExit=no

[Install]
WantedBy=multi-user.target
EOF

echo "✅ Service file created: $SERVICE_FILE"
echo ""

# Install service
echo "Installing systemd service..."
sudo cp "$SERVICE_FILE" /etc/systemd/system/omni-console.service
sudo systemctl daemon-reload
sudo systemctl enable omni-console.service

echo ""
echo "✅ Service installed and enabled"
echo ""
echo "To start:"
echo "  sudo systemctl start omni-console.service"
echo ""
echo "To check status:"
echo "  sudo systemctl status omni-console.service"
echo ""
echo "Service will:"
echo "  ✓ Auto-start on boot"
echo "  ✓ Auto-restart on failure"
echo "  ✓ Survive power outages"
echo "  ✓ Restart after 10 seconds if crashes"
echo ""
