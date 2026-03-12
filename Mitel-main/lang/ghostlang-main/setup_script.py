#!/usr/bin/env python3
"""
ghost_service_wrapper.py - Connects GhostFallbackDaemon to existing GhostHUD

Usage:
  python ghost_service_wrapper.py --node-id <node_id> --mode <master|peer> [--master-ip <ip>]
"""

import os
import sys
import subprocess
import time
import threading
import json
import argparse
from pathlib import Path

# Import your existing modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from ghost_fallback_daemon import GhostFallbackDaemon, ConnectivityStatus, TransportMode

def main():
    parser = argparse.ArgumentParser(description="GhostHUD Fallback Service")
    parser.add_argument("--node-id", required=True, help="Node ID")
    parser.add_argument("--mode", choices=["master", "peer"], required=True, help="Node mode")
    parser.add_argument("--master-ip", help="Master IP address (required for peer mode)")
    parser.add_argument("--auth-key", default="ghostops", help="Auth key for mesh")
    parser.add_argument("--data-dir", default="./ghost_data", help="Data directory")
    args = parser.parse_args()
    
    # Validate args
    if args.mode == "peer" and not args.master_ip:
        print("Error: --master-ip is required for peer mode")
        sys.exit(1)
    
    # Setup data directory
    data_dir = os.path.abspath(args.data_dir)
    os.makedirs(data_dir, exist_ok=True)
    
    # Initialize fallback daemon
    master_ip = None if args.mode == "master" else args.master_ip
    fallback = GhostFallbackDaemon(
        node_id=args.node_id,
        data_dir=data_dir,
        auth_key=args.auth_key,
        master_ip=master_ip
    )
    
    # Start fallback daemon
    fallback.start()
    
    # Keep running and monitor
    try:
        while True:
            status = fallback.get_status()
            print(f"Status: {status['connectivity']} | Mode: {status['transport_mode']}")
            print(f"Peers: {status['peer_count']} | Queue: {status['command_queue_size']}")
            time.sleep(30)
    except KeyboardInterrupt:
        print("Stopping service...")
        fallback.stop()
        print("Service stopped.")

if __name__ == "__main__":
    main()
