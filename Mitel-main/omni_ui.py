#!/usr/bin/env python3
"""
OMNI UI - Real-Time Dashboard
==============================

Interactive CLI/TUI showing live OMNI status, peers, and operations.
"""

import sys
import os
import time
import threading
import signal
from datetime import datetime
from typing import Dict, List, Optional

# Add paths
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from omni_core import OmniCore

# ANSI color codes
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    GRAY = '\033[90m'

# Box drawing characters
BOX_H = '═'
BOX_V = '║'
BOX_TL = '╔'
BOX_TR = '╗'
BOX_BL = '╚'
BOX_BR = '╝'
BOX_T = '╦'
BOX_B = '╩'
BOX_L = '╠'
BOX_R = '╣'
BOX_X = '╬'


def clear_screen():
    """Clear terminal screen"""
    os.system('clear' if os.name != 'nt' else 'cls')


def print_header():
    """Print header banner"""
    width = 80
    print(f"{Colors.CYAN}{BOX_TL}{BOX_H * (width-2)}{BOX_TR}{Colors.RESET}")
    print(f"{Colors.CYAN}{BOX_V}{Colors.BOLD}{Colors.WHITE}  OMNI - Unified Orchestrator{Colors.RESET}{' ' * (width-32)}{Colors.CYAN}{BOX_V}{Colors.RESET}")
    print(f"{Colors.CYAN}{BOX_L}{BOX_H * (width-2)}{BOX_R}{Colors.RESET}")


def print_status_box(core: OmniCore, width: int = 80):
    """Print status information box"""
    status = core.get_status()
    
    # Status color
    if status['status'] == 'online':
        status_color = Colors.GREEN
        status_icon = '●'
    elif status['status'] == 'syncing':
        status_color = Colors.YELLOW
        status_icon = '◐'
    elif status['status'] == 'recovering':
        status_color = Colors.YELLOW
        status_icon = '⟳'
    else:
        status_color = Colors.RED
        status_icon = '○'
    
    print(f"{Colors.CYAN}{BOX_V}{Colors.RESET} {Colors.BOLD}STATUS{Colors.RESET}{' ' * (width-10)}{Colors.CYAN}{BOX_V}{Colors.RESET}")
    print(f"{Colors.CYAN}{BOX_L}{BOX_H * (width-2)}{BOX_R}{Colors.RESET}")
    
    # Node info
    node_id_short = status['node_id'][:16] + '...' if len(status['node_id']) > 16 else status['node_id']
    print(f"{Colors.CYAN}{BOX_V}{Colors.RESET} {Colors.BOLD}Node ID:{Colors.RESET} {Colors.CYAN}{node_id_short}{Colors.RESET}{' ' * (width-30)}{Colors.CYAN}{BOX_V}{Colors.RESET}")
    print(f"{Colors.CYAN}{BOX_V}{Colors.RESET} {Colors.BOLD}Platform:{Colors.RESET} {Colors.GREEN}{status['platform']}{Colors.RESET}{' ' * (width-30)}{Colors.CYAN}{BOX_V}{Colors.RESET}")
    print(f"{Colors.CYAN}{BOX_V}{Colors.RESET} {Colors.BOLD}Address:{Colors.RESET} {Colors.CYAN}{status['ip']}:{status['port']}{Colors.RESET}{' ' * (width-30)}{Colors.CYAN}{BOX_V}{Colors.RESET}")
    print(f"{Colors.CYAN}{BOX_V}{Colors.RESET} {Colors.BOLD}Status:{Colors.RESET} {status_color}{status_icon} {status['status'].upper()}{Colors.RESET}{' ' * (width-30)}{Colors.CYAN}{BOX_V}{Colors.RESET}")
    print(f"{Colors.CYAN}{BOX_V}{Colors.RESET} {Colors.BOLD}Peers:{Colors.RESET} {Colors.GREEN}{status['peers']}{Colors.RESET} connected{' ' * (width-30)}{Colors.CYAN}{BOX_V}{Colors.RESET}")
    print(f"{Colors.CYAN}{BOX_V}{Colors.RESET} {Colors.BOLD}State Keys:{Colors.RESET} {Colors.CYAN}{status['state_keys']}{Colors.RESET}{' ' * (width-30)}{Colors.CYAN}{BOX_V}{Colors.RESET}")
    print(f"{Colors.CYAN}{BOX_V}{Colors.RESET} {Colors.BOLD}Master:{Colors.RESET} {'Yes' if status['is_master'] else 'No'}{' ' * (width-30)}{Colors.CYAN}{BOX_V}{Colors.RESET}")
    
    print(f"{Colors.CYAN}{BOX_L}{BOX_H * (width-2)}{BOX_R}{Colors.RESET}")


def print_peers_box(core: OmniCore, width: int = 80):
    """Print peers information box"""
    peers = core.get_peers()
    
    print(f"{Colors.CYAN}{BOX_V}{Colors.RESET} {Colors.BOLD}PEERS{Colors.RESET} ({len(peers)}){' ' * (width-15)}{Colors.CYAN}{BOX_V}{Colors.RESET}")
    print(f"{Colors.CYAN}{BOX_L}{BOX_H * (width-2)}{BOX_R}{Colors.RESET}")
    
    if not peers:
        print(f"{Colors.CYAN}{BOX_V}{Colors.RESET} {Colors.GRAY}No peers discovered yet...{Colors.RESET}{' ' * (width-30)}{Colors.CYAN}{BOX_V}{Colors.RESET}")
    else:
        for i, peer in enumerate(peers[:10]):  # Show max 10 peers
            node_id_short = peer['node_id'][:12] + '...' if len(peer['node_id']) > 12 else peer['node_id']
            last_seen = int(time.time() - peer['last_seen'])
            age_str = f"{last_seen}s ago" if last_seen < 60 else f"{last_seen//60}m ago"
            
            # Health indicator
            if peer['health_score'] > 80:
                health_color = Colors.GREEN
            elif peer['health_score'] > 50:
                health_color = Colors.YELLOW
            else:
                health_color = Colors.RED
            
            print(f"{Colors.CYAN}{BOX_V}{Colors.RESET} {Colors.CYAN}●{Colors.RESET} {node_id_short} @ {peer['ip']}:{peer['port']} ({peer['platform']}) - {Colors.GRAY}{age_str}{Colors.RESET}{' ' * (width-70)}{Colors.CYAN}{BOX_V}{Colors.RESET}")
    
    if len(peers) > 10:
        print(f"{Colors.CYAN}{BOX_V}{Colors.RESET} {Colors.GRAY}... and {len(peers)-10} more{Colors.RESET}{' ' * (width-30)}{Colors.CYAN}{BOX_V}{Colors.RESET}")
    
    print(f"{Colors.CYAN}{BOX_L}{BOX_H * (width-2)}{BOX_R}{Colors.RESET}")


def print_activity_box(core: OmniCore, activity_log: List[str], width: int = 80):
    """Print activity log box"""
    print(f"{Colors.CYAN}{BOX_V}{Colors.RESET} {Colors.BOLD}ACTIVITY{Colors.RESET}{' ' * (width-12)}{Colors.CYAN}{BOX_V}{Colors.RESET}")
    print(f"{Colors.CYAN}{BOX_L}{BOX_H * (width-2)}{BOX_R}{Colors.RESET}")
    
    # Show last 8 activity entries
    for entry in activity_log[-8:]:
        # Truncate if too long
        if len(entry) > width - 4:
            entry = entry[:width-7] + '...'
        print(f"{Colors.CYAN}{BOX_V}{Colors.RESET} {entry}{' ' * (width-len(entry)-4)}{Colors.CYAN}{BOX_V}{Colors.RESET}")
    
    print(f"{Colors.CYAN}{BOX_L}{BOX_H * (width-2)}{BOX_R}{Colors.RESET}")


def print_footer(width: int = 80):
    """Print footer with commands"""
    print(f"{Colors.CYAN}{BOX_V}{Colors.RESET} {Colors.BOLD}Commands:{Colors.RESET} {Colors.GRAY}[r]efresh  [s]tatus  [p]eers  [q]uit{Colors.RESET}{' ' * (width-60)}{Colors.CYAN}{BOX_V}{Colors.RESET}")
    print(f"{Colors.CYAN}{BOX_BL}{BOX_H * (width-2)}{BOX_BR}{Colors.RESET}")
    print(f"{Colors.GRAY}Last update: {datetime.now().strftime('%H:%M:%S')}{Colors.RESET}")


def print_dashboard(core: OmniCore, activity_log: List[str]):
    """Print complete dashboard"""
    clear_screen()
    width = 80
    
    print_header()
    print()
    print_status_box(core, width)
    print()
    print_peers_box(core, width)
    print()
    print_activity_box(core, activity_log, width)
    print()
    print_footer(width)


def interactive_dashboard(core: OmniCore):
    """Run interactive dashboard"""
    activity_log = []
    running = True
    last_update = 0
    update_interval = 2  # Update every 2 seconds
    
    # Add initial activity
    activity_log.append(f"{Colors.GREEN}✓{Colors.RESET} OMNI core initialized")
    activity_log.append(f"{Colors.GREEN}✓{Colors.RESET} Discovery started on port 45678")
    activity_log.append(f"{Colors.GREEN}✓{Colors.RESET} Mesh listener started on port 7777")
    activity_log.append(f"{Colors.GREEN}✓{Colors.RESET} Sync engine started")
    activity_log.append(f"{Colors.GREEN}✓{Colors.RESET} Health monitoring active")
    
    def update_activity():
        """Update activity log periodically"""
        nonlocal last_update
        while running:
            try:
                status = core.get_status()
                peers = core.get_peers()
                
                # Check for new peers
                if len(peers) > 0:
                    activity_log.append(f"{Colors.CYAN}●{Colors.RESET} {len(peers)} peer(s) discovered")
                    if len(activity_log) > 50:
                        activity_log.pop(0)
                
                # Check sync activity
                # (This would be enhanced with actual sync event tracking)
                
                time.sleep(update_interval)
            except:
                pass
    
    # Start activity update thread
    activity_thread = threading.Thread(target=update_activity, daemon=True)
    activity_thread.start()
    
    # Main loop
    try:
        while running:
            current_time = time.time()
            
            # Auto-refresh
            if current_time - last_update >= update_interval:
                print_dashboard(core, activity_log)
                last_update = current_time
            
            # Check for input (non-blocking)
            import select
            if sys.stdin in select.select([sys.stdin], [], [], 0.1)[0]:
                try:
                    key = sys.stdin.read(1).lower()
                    
                    if key == 'q':
                        running = False
                        break
                    elif key == 'r':
                        print_dashboard(core, activity_log)
                        activity_log.append(f"{Colors.YELLOW}⟳{Colors.RESET} Manual refresh")
                    elif key == 's':
                        status = core.get_status()
                        activity_log.append(f"{Colors.BLUE}ℹ{Colors.RESET} Status: {status['status']}, {status['peers']} peers")
                    elif key == 'p':
                        peers = core.get_peers()
                        activity_log.append(f"{Colors.BLUE}ℹ{Colors.RESET} {len(peers)} peer(s) connected")
                    
                    if len(activity_log) > 50:
                        activity_log.pop(0)
                except:
                    pass
            
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        running = False
    
    # Cleanup
    clear_screen()
    print(f"{Colors.GREEN}✓{Colors.RESET} OMNI UI stopped")


def simple_dashboard(core: OmniCore):
    """Simple non-interactive dashboard (for systems without select support)"""
    activity_log = []
    activity_log.append(f"{Colors.GREEN}✓{Colors.RESET} OMNI core initialized")
    activity_log.append(f"{Colors.GREEN}✓{Colors.RESET} Discovery started on port 45678")
    activity_log.append(f"{Colors.GREEN}✓{Colors.RESET} Mesh listener started on port 7777")
    activity_log.append(f"{Colors.GREEN}✓{Colors.RESET} Sync engine started")
    activity_log.append(f"{Colors.GREEN}✓{Colors.RESET} Health monitoring active")
    
    try:
        while True:
            print_dashboard(core, activity_log)
            
            # Update activity
            status = core.get_status()
            peers = core.get_peers()
            
            if len(peers) > 0:
                activity_log.append(f"{Colors.CYAN}●{Colors.RESET} {len(peers)} peer(s) discovered")
            
            if len(activity_log) > 50:
                activity_log.pop(0)
            
            time.sleep(2)
            
    except KeyboardInterrupt:
        clear_screen()
        print(f"{Colors.GREEN}✓{Colors.RESET} OMNI UI stopped")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='OMNI UI - Real-Time Dashboard')
    parser.add_argument('--config', help='Path to config file')
    parser.add_argument('--simple', action='store_true', help='Use simple dashboard (no interactive mode)')
    args = parser.parse_args()
    
    # Create OMNI instance
    core = OmniCore(config_path=args.config)
    
    # Start OMNI
    print(f"{Colors.CYAN}Starting OMNI...{Colors.RESET}")
    core.start()
    time.sleep(1)  # Give it a moment to initialize
    
    # Run dashboard
    try:
        if args.simple:
            simple_dashboard(core)
        else:
            interactive_dashboard(core)
    finally:
        core.stop()
        print(f"{Colors.GREEN}✓{Colors.RESET} OMNI stopped")


if __name__ == "__main__":
    main()
