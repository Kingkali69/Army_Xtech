#!/usr/bin/env python3
"""
Systemd Service Generator
==========================

Creates systemd service file for auto-launch on boot.
Survives power outages - auto-restarts after power returns.
"""

import os
import sys
import stat

def create_systemd_service(workspace_path: str, user: str = None):
    """
    Create systemd service file for auto-launch.
    
    Args:
        workspace_path: Path to OMNI workspace
        user: Username to run as (default: current user)
    """
    if user is None:
        import getpass
        user = getpass.getuser()
    
    workspace_path = os.path.abspath(workspace_path)
    python_path = sys.executable
    
    service_content = f"""[Unit]
Description=OMNI Infrastructure Operations Console
After=network.target
Wants=network-online.target

[Service]
Type=simple
User={user}
WorkingDirectory={workspace_path}
ExecStart={python_path} {workspace_path}/omni_web_console.py --port 8888
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
"""
    
    service_file = f"/tmp/omni-console.service"
    
    with open(service_file, 'w') as f:
        f.write(service_content)
    
    print(f"✅ Systemd service file created: {service_file}")
    print()
    print("To install:")
    print(f"  sudo cp {service_file} /etc/systemd/system/")
    print("  sudo systemctl daemon-reload")
    print("  sudo systemctl enable omni-console.service")
    print("  sudo systemctl start omni-console.service")
    print()
    print("Service will:")
    print("  ✓ Auto-start on boot")
    print("  ✓ Auto-restart on failure")
    print("  ✓ Survive power outages")
    print("  ✓ Restart after 10 seconds if crashes")
    
    return service_file

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Create systemd service for OMNI")
    parser.add_argument('--workspace', type=str, default=os.getcwd(), help='Workspace path')
    parser.add_argument('--user', type=str, default=None, help='User to run as')
    args = parser.parse_args()
    
    create_systemd_service(args.workspace, args.user)
