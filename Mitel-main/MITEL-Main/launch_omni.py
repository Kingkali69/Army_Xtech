#!/usr/bin/env python3
"""
OMNI Launcher - Unified Entry Point
===================================

Auto-configures, launches, and orchestrates the entire OMNI organism.

Usage:
    python launch_omni.py
    python launch_omni.py --status
    python launch_omni.py --config /path/to/config.json
"""

import sys
import os
import time
import signal
import argparse

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from omni_core import OmniCore

# Global reference for signal handling
omni_instance = None


def signal_handler(sig, frame):
    """Handle shutdown signals"""
    global omni_instance
    if omni_instance:
        print("\n[OMNI] Received shutdown signal, stopping...")
        omni_instance.stop()
    sys.exit(0)


def main():
    """Main entry point"""
    global omni_instance
    
    parser = argparse.ArgumentParser(
        description='OMNI Launcher - Unified Orchestrator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python launch_omni.py                    # Start OMNI
  python launch_omni.py --status           # Show status and exit
  python launch_omni.py --config custom.json # Use custom config
        """
    )
    parser.add_argument(
        '--config',
        help='Path to configuration file (auto-detected if not provided)'
    )
    parser.add_argument(
        '--status',
        action='store_true',
        help='Show status and exit'
    )
    parser.add_argument(
        '--daemon',
        action='store_true',
        help='Run as daemon (background)'
    )
    
    args = parser.parse_args()
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create OMNI instance
    omni_instance = OmniCore(config_path=args.config)
    
    if args.status:
        # Status mode - start, show status, exit
        print("[OMNI] Starting in status mode...")
        omni_instance.start()
        time.sleep(3)  # Give it time to initialize
        
        status = omni_instance.get_status()
        peers = omni_instance.get_peers()
        
        print("\n" + "="*70)
        print("OMNI STATUS")
        print("="*70)
        print(f"Node ID:      {status['node_id']}")
        print(f"Status:        {status['status']}")
        print(f"Platform:     {status['platform']}")
        print(f"IP:Port:       {status['ip']}:{status['port']}")
        print(f"Peers:         {status['peers']}")
        print(f"State Keys:    {status['state_keys']}")
        print(f"Master:        {status['is_master']}")
        if peers:
            print("\nPeers:")
            for peer in peers:
                print(f"  - {peer['node_id'][:12]} @ {peer['ip']}:{peer['port']} ({peer['platform']})")
        print("="*70 + "\n")
        
        omni_instance.stop()
        return
    
    # Normal mode - start and run
    if args.daemon:
        # Daemon mode - run in background
        print("="*70)
        print("OMNI - Unified Orchestrator (Daemon Mode)")
        print("="*70 + "\n")
        omni_instance.start()
        print("[OMNI] Running as daemon...")
        while True:
            time.sleep(60)
            # Periodic status check
            status = omni_instance.get_status()
            if status['status'] == 'offline':
                print("[OMNI] Warning: Node went offline, attempting recovery...")
                omni_instance.initialize()
    else:
        # UI mode - launch dashboard
        print("="*70)
        print("OMNI - Unified Orchestrator")
        print("="*70)
        print("Launching dashboard...")
        print("="*70 + "\n")
        
        omni_instance.start()
        time.sleep(1)
        
        # Launch UI
        try:
            from omni_ui import interactive_dashboard, simple_dashboard
            import sys
            
            # Try interactive mode, fallback to simple
            try:
                import select
                interactive_dashboard(omni_instance)
            except (ImportError, AttributeError):
                # Windows or no select support
                simple_dashboard(omni_instance)
        except ImportError:
            # Fallback to simple text output
            print("[OMNI] Running... (Press Ctrl+C to stop)")
            print(f"[OMNI] Node ID: {omni_instance.node_id}")
            print(f"[OMNI] Listening on {omni_instance.config['local_ip']}:{omni_instance.mesh_port}")
            print("[OMNI] Use --status to check status")
            print("[OMNI] Use 'python3 omni_ui.py' for dashboard\n")
            
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n[OMNI] Shutting down...")
                
        except KeyboardInterrupt:
            print("\n[OMNI] Shutting down...")
        except Exception as e:
            print(f"\n[OMNI] Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if omni_instance:
                omni_instance.stop()
            print("[OMNI] ✅ Stopped")


if __name__ == "__main__":
    main()
