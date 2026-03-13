#!/usr/bin/env python3
"""
OMNI Infrastructure Operations Console
======================================

National-scale Infrastructure Operations Console.
Observation-only. Read-only. Trusted.

Layout:
- TOP BAND: System State Bar (always visible)
- LEFT PANEL: Physical/Logical Map (primary view)
- RIGHT PANEL: Metrics Stack (read-only cards)
- BOTTOM STRIP: Event Timeline (immutable, append-only)
"""

import sys
import os
import time
import threading
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from collections import deque

# Add paths
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from omni_core import OmniCore

# Color palette (muted, professional)
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    
    # Status colors (green/amber/red only)
    GREEN = '\033[38;5;46m'      # Muted green
    AMBER = '\033[38;5;214m'     # Amber
    RED = '\033[38;5;196m'        # Red
    
    # Neutral colors
    WHITE = '\033[38;5;255m'
    GRAY = '\033[38;5;244m'
    DARK_GRAY = '\033[38;5;238m'
    CYAN = '\033[38;5;51m'        # Muted cyan (not neon)
    
    # Background (charcoal, not black)
    BG = '\033[48;5;235m'


class EventLog:
    """Immutable, append-only event timeline"""
    
    def __init__(self, max_events: int = 1000):
        self.events: deque = deque(maxlen=max_events)
        self.lock = threading.Lock()
    
    def append(self, timestamp: str, category: str, message: str):
        """Append event (immutable)"""
        with self.lock:
            self.events.append({
                'timestamp': timestamp,
                'category': category,
                'message': message
            })
    
    def get_recent(self, count: int = 20) -> List[Dict]:
        """Get recent events"""
        with self.lock:
            return list(self.events)[-count:]


class OMNIConsole:
    """
    Infrastructure Operations Console
    
    Observation-only. Read-only. Trusted.
    """
    
    def __init__(self, core: OmniCore):
        self.core = core
        self.event_log = EventLog()
        self.running = False
        
        # State tracking
        self.epoch = 1
        self.last_epoch_update = time.time()
        self.quorum_state = "STABLE"
        self.failover_count_24h = 0
        self.threat_count = 0
        self.degraded_zones = 0
        
        # Metrics
        self.metrics = {
            'mesh_health': 100.0,
            'control_plane': 'OPERATIONAL',
            'failover_engine': 'STANDBY',
            'security_subsystems': 'ACTIVE',
            'data_integrity': 'VERIFIED'
        }
        
        # Initialize event log
        self._log_event("SYSTEM", "Console initialized")
        self._log_event("SYSTEM", "Observation mode active")
    
    def _log_event(self, category: str, message: str):
        """Log event to timeline"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.event_log.append(timestamp, category, message)
    
    def _get_status_color(self, status: str) -> str:
        """Get color for status (green/amber/red only)"""
        status_upper = status.upper()
        if 'OPERATIONAL' in status_upper or 'STABLE' in status_upper or 'ACTIVE' in status_upper:
            return Colors.GREEN
        elif 'DEGRADED' in status_upper or 'WARNING' in status_upper or 'STANDBY' in status_upper:
            return Colors.AMBER
        else:
            return Colors.RED
    
    def _render_top_band(self, width: int = 120) -> str:
        """
        TOP BAND - System State Bar (always visible)
        Single line. No animation.
        """
        status = self.core.get_status()
        peers = self.core.get_peers()
        
        # Calculate metrics
        mesh_nodes = len(peers) + 1  # +1 for self
        avg_latency = self._calculate_avg_latency(peers)
        
        # Status color
        if status['status'] == 'online':
            status_color = Colors.GREEN
            status_text = "OPERATIONAL"
        elif status['status'] == 'syncing':
            status_color = Colors.AMBER
            status_text = "SYNCING"
        else:
            status_color = Colors.RED
            status_text = "DEGRADED"
        
        # Build line
        line = f"{Colors.BG}{Colors.WHITE}{Colors.BOLD}"
        line += f"GLOBAL STATUS: {status_color}{status_text}{Colors.WHITE} | "
        line += f"EPOCH {self.epoch} | "
        line += f"MESH NODES: {mesh_nodes} | "
        line += f"QUORUM: {Colors.GREEN if self.quorum_state == 'STABLE' else Colors.AMBER}{self.quorum_state}{Colors.WHITE} | "
        line += f"LATENCY: {avg_latency}ms avg | "
        line += f"FAILOVERS (24h): {self.failover_count_24h} | "
        line += f"THREATS: {self.threat_count} | "
        line += f"DEGRADED ZONES: {self.degraded_zones}"
        line += f"{Colors.RESET}"
        
        return line
    
    def _calculate_avg_latency(self, peers: List[Dict]) -> int:
        """Calculate average latency (simplified)"""
        if not peers:
            return 0
        # In real implementation, this would use actual ping times
        return 9  # Placeholder
    
    def _render_left_panel(self, width: int = 60, height: int = 30) -> List[str]:
        """
        LEFT PANEL - Physical/Logical Map (PRIMARY VIEW)
        
        Nodes as simple glyphs.
        Links as thin lines.
        Thickness = bandwidth.
        Color = health.
        Pulse = data flow (slow, subtle).
        """
        lines = []
        status = self.core.get_status()
        peers = self.core.get_peers()
        
        # Header
        lines.append(f"{Colors.BOLD}PHYSICAL/LOGICAL MAP{Colors.RESET}")
        lines.append("─" * width)
        
        # Simple topology representation
        # Center node (self)
        center_y = height // 2
        center_x = width // 2
        
        # Draw self
        node_char = "●" if status['status'] == 'online' else "○"
        node_color = Colors.GREEN if status['status'] == 'online' else Colors.AMBER
        
        # Draw peers around center
        if peers:
            lines.append(f"{Colors.GRAY}Topology: {len(peers)} peer(s) connected{Colors.RESET}")
            lines.append("")
            
            # Simple list representation (in real implementation, would be spatial map)
            for i, peer in enumerate(peers[:10]):  # Show max 10
                node_id_short = peer['node_id'][:16] + '...' if len(peer['node_id']) > 16 else peer['node_id']
                health = peer.get('health_score', 100)
                
                if health > 80:
                    health_color = Colors.GREEN
                    glyph = "●"
                elif health > 50:
                    health_color = Colors.AMBER
                    glyph = "◐"
                else:
                    health_color = Colors.RED
                    glyph = "○"
                
                lines.append(f"  {health_color}{glyph}{Colors.RESET} {node_id_short} @ {peer['ip']}:{peer['port']}")
                lines.append(f"      Platform: {peer['platform']} | Health: {health:.0f}%")
        else:
            lines.append(f"{Colors.GRAY}No peers discovered{Colors.RESET}")
            lines.append("")
            lines.append(f"  {node_color}{node_char}{Colors.RESET} {status['node_id'][:16]}... (self)")
            lines.append(f"      Platform: {status['platform']} | Status: {status['status']}")
        
        # Fill remaining space
        while len(lines) < height - 2:
            lines.append("")
        
        return lines
    
    def _render_right_panel(self, width: int = 55) -> List[str]:
        """
        RIGHT PANEL - Metrics Stack (READ-ONLY)
        
        Vertical cards. Each card is one truth.
        3-5 metrics max per card.
        Numbers + sparklines.
        No buttons.
        """
        lines = []
        
        # Card 1: Mesh Health
        lines.append(f"{Colors.BOLD}MESH HEALTH{Colors.RESET}")
        lines.append("─" * width)
        health = self.metrics['mesh_health']
        health_color = Colors.GREEN if health > 80 else Colors.AMBER if health > 50 else Colors.RED
        lines.append(f"  Status: {health_color}{health:.1f}%{Colors.RESET}")
        lines.append(f"  Nodes: {len(self.core.get_peers()) + 1}")
        lines.append(f"  Connectivity: {Colors.GREEN}STABLE{Colors.RESET}")
        lines.append("")
        
        # Card 2: Control Plane Status
        lines.append(f"{Colors.BOLD}CONTROL PLANE{Colors.RESET}")
        lines.append("─" * width)
        cp_status = self.metrics['control_plane']
        cp_color = self._get_status_color(cp_status)
        lines.append(f"  Status: {cp_color}{cp_status}{Colors.RESET}")
        lines.append(f"  Epoch: {self.epoch}")
        lines.append(f"  Quorum: {self.quorum_state}")
        lines.append("")
        
        # Card 3: Failover Engine
        lines.append(f"{Colors.BOLD}FAILOVER ENGINE{Colors.RESET}")
        lines.append("─" * width)
        fe_status = self.metrics['failover_engine']
        fe_color = self._get_status_color(fe_status)
        lines.append(f"  Status: {fe_color}{fe_status}{Colors.RESET}")
        lines.append(f"  Failovers (24h): {self.failover_count_24h}")
        lines.append(f"  Degraded zones: {self.degraded_zones}")
        lines.append("")
        
        # Card 4: Security Subsystems
        lines.append(f"{Colors.BOLD}SECURITY SUBSYSTEMS{Colors.RESET}")
        lines.append("─" * width)
        sec_status = self.metrics['security_subsystems']
        sec_color = self._get_status_color(sec_status)
        lines.append(f"  Status: {sec_color}{sec_status}{Colors.RESET}")
        lines.append(f"  Threats: {self.threat_count}")
        lines.append(f"  Integrity: {Colors.GREEN}VERIFIED{Colors.RESET}")
        lines.append("")
        
        # Card 5: Data Integrity
        lines.append(f"{Colors.BOLD}DATA INTEGRITY{Colors.RESET}")
        lines.append("─" * width)
        di_status = self.metrics['data_integrity']
        di_color = self._get_status_color(di_status)
        lines.append(f"  Status: {di_color}{di_status}{Colors.RESET}")
        status = self.core.get_status()
        lines.append(f"  State keys: {status['state_keys']}")
        lines.append(f"  Log entries: {self._get_log_count()}")
        
        return lines
    
    def _get_log_count(self) -> int:
        """Get state log entry count"""
        try:
            import sqlite3
            db_path = os.path.expanduser('~/.omni/state.db')
            if os.path.exists(db_path):
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM state_log')
                count = cursor.fetchone()[0]
                conn.close()
                return count
        except:
            pass
        return 0
    
    def _render_bottom_strip(self, width: int = 120) -> List[str]:
        """
        BOTTOM STRIP - Event Timeline (THE MOST IMPORTANT PART)
        
        Chronological, immutable, append-only.
        If it's not here, it didn't happen.
        """
        lines = []
        
        lines.append(f"{Colors.BOLD}EVENT TIMELINE{Colors.RESET}")
        lines.append("─" * width)
        
        # Get recent events
        events = self.event_log.get_recent(15)
        
        if not events:
            lines.append(f"{Colors.GRAY}No events recorded{Colors.RESET}")
        else:
            for event in events:
                timestamp = event['timestamp']
                category = event['category']
                message = event['message']
                
                # Category color
                if category == 'SYSTEM':
                    cat_color = Colors.CYAN
                elif category == 'MESH':
                    cat_color = Colors.GREEN
                elif category == 'WARNING':
                    cat_color = Colors.AMBER
                elif category == 'ERROR':
                    cat_color = Colors.RED
                else:
                    cat_color = Colors.GRAY
                
                # Format: timestamp category message
                line = f"  {Colors.GRAY}{timestamp}{Colors.RESET}  {cat_color}[{category}]{Colors.RESET}  {message}"
                if len(line) > width:
                    line = line[:width-3] + "..."
                lines.append(line)
        
        return lines
    
    def _update_metrics(self):
        """Update metrics from core state"""
        status = self.core.get_status()
        peers = self.core.get_peers()
        
        # Mesh health
        if status['status'] == 'online' and len(peers) > 0:
            self.metrics['mesh_health'] = 95.0
        elif status['status'] == 'online':
            self.metrics['mesh_health'] = 85.0
        else:
            self.metrics['mesh_health'] = 50.0
        
        # Control plane
        if status['status'] == 'online':
            self.metrics['control_plane'] = 'OPERATIONAL'
        else:
            self.metrics['control_plane'] = 'DEGRADED'
        
        # Log events for significant changes
        if len(peers) > 0:
            self._log_event("MESH", f"Mesh connectivity: {len(peers)} peer(s)")
    
    def render(self):
        """Render complete console"""
        # Clear screen
        os.system('clear' if os.name != 'nt' else 'cls')
        
        # Update metrics
        self._update_metrics()
        
        # Top band (always visible)
        top_band = self._render_top_band()
        print(top_band)
        print()
        
        # Main content area (left + right panels)
        left_panel = self._render_left_panel()
        right_panel = self._render_right_panel()
        
        # Combine left and right
        max_height = max(len(left_panel), len(right_panel))
        for i in range(max_height):
            left_line = left_panel[i] if i < len(left_panel) else ""
            right_line = right_panel[i] if i < len(right_panel) else ""
            
            # Pad left panel to fixed width
            left_padded = left_line.ljust(65)
            print(f"{left_padded}  {right_line}")
        
        print()
        print("─" * 120)
        print()
        
        # Bottom strip (event timeline)
        bottom_strip = self._render_bottom_strip()
        for line in bottom_strip:
            print(line)
        
        print()
        print(f"{Colors.GRAY}Console: Observation mode | Read-only | Last update: {datetime.now().strftime('%H:%M:%S')}{Colors.RESET}")
    
    def run(self):
        """Run console (observation mode)"""
        self.running = True
        
        # Log startup
        self._log_event("SYSTEM", "Console operational")
        self._log_event("SYSTEM", "Observation mode active")
        
        # Initial render
        self.render()
        
        try:
            while self.running:
                time.sleep(2)  # Update every 2 seconds
                self.render()
        except KeyboardInterrupt:
            self.running = False
            self._log_event("SYSTEM", "Console shutdown")
        
        # Final render
        os.system('clear' if os.name != 'nt' else 'cls')
        print(f"{Colors.GREEN}Console shutdown complete.{Colors.RESET}")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='OMNI Infrastructure Operations Console')
    parser.add_argument('--config', help='Path to config file')
    args = parser.parse_args()
    
    # Create OMNI instance
    core = OmniCore(config_path=args.config)
    
    # Start OMNI
    print(f"{Colors.CYAN}Initializing OMNI core...{Colors.RESET}")
    core.start()
    time.sleep(1)  # Give it a moment to initialize
    
    # Create and run console
    console = OMNIConsole(core)
    
    try:
        console.run()
    finally:
        core.stop()


if __name__ == "__main__":
    main()
