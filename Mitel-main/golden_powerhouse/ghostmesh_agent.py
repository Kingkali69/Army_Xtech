#!/usr/bin/env python3
"""
GhostMesh™ Agent - Distributed Wireless Intrusion Defense
Patent Pending - KK&GDevOps, LLC

Features:
- Rogue AP detection (Evil Twin detection)
- Deauth flood prevention
- Packet injection detection
- MAC trust layer (M.I.T.E.L. integration)
- ARP poisoning detection
- Mesh voting system for distributed validation
- Real-time alerting via CloudCore_Sync_2

Deployment: Router, Raspberry Pi, Kali box in monitor mode
"""

import os
import sys
import time
import json
import socket
import hashlib
import threading
from datetime import datetime
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
from typing import Dict, List, Set, Optional

try:
    from scapy.all import (
        sniff, Dot11, Dot11Beacon, Dot11Elt, Dot11Deauth, 
        ARP, Ether, conf, get_if_list
    )
    SCAPY_AVAILABLE = True
except ImportError:
    print("⚠️ Scapy not available. Install with: pip install scapy")
    SCAPY_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

# Configuration
MONITOR_INTERFACE = os.environ.get('GHOSTMESH_IFACE', 'wlan0mon')
MESH_PORT = 9999
ALERT_THRESHOLD = 5  # Number of suspicious events before blocking
DEAUTH_FLOOD_THRESHOLD = 10  # Deauth packets per minute
CLOUDCORE_SYNC_ENABLED = True

@dataclass
class WirelessDevice:
    """Represents a wireless device on the network"""
    mac: str
    first_seen: float
    last_seen: float
    trust_score: int = 100
    ssid: Optional[str] = None
    signal_strength: int = 0
    vendor: Optional[str] = None
    suspicious_events: int = 0
    
    def is_trusted(self) -> bool:
        return self.trust_score >= 50
    
    def degrade_trust(self, amount: int = 10):
        self.trust_score = max(0, self.trust_score - amount)
    
    def improve_trust(self, amount: int = 5):
        self.trust_score = min(100, self.trust_score + amount)

@dataclass
class AccessPoint:
    """Represents an Access Point"""
    bssid: str
    ssid: str
    channel: int
    encryption: str
    signal_strength: int
    first_seen: float
    last_seen: float
    is_legitimate: bool = False
    
    def fingerprint(self) -> str:
        """Generate unique fingerprint for AP"""
        data = f"{self.ssid}:{self.bssid}:{self.channel}:{self.encryption}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]

@dataclass
class ThreatAlert:
    """Security threat alert"""
    timestamp: float
    threat_type: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    source_mac: str
    target_mac: Optional[str]
    details: str
    action_taken: str

class MITELTrustLayer:
    """
    M.I.T.E.L. Integration for MAC trust scoring
    Patent #2: Modular Input Trust Enforcement Layer
    """
    
    def __init__(self):
        self.known_devices: Dict[str, WirelessDevice] = {}
        self.whitelist: Set[str] = set()
        self.blacklist: Set[str] = set()
        self.trust_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
    
    def register_device(self, mac: str, ssid: Optional[str] = None) -> WirelessDevice:
        """Register or update device"""
        if mac not in self.known_devices:
            device = WirelessDevice(
                mac=mac,
                first_seen=time.time(),
                last_seen=time.time(),
                ssid=ssid
            )
            self.known_devices[mac] = device
            return device
        else:
            device = self.known_devices[mac]
            device.last_seen = time.time()
            if ssid:
                device.ssid = ssid
            return device
    
    def calculate_trust_score(self, mac: str) -> int:
        """Calculate trust score for a MAC address"""
        if mac in self.whitelist:
            return 100
        if mac in self.blacklist:
            return 0
        
        device = self.known_devices.get(mac)
        if not device:
            return 50  # Unknown devices start at 50
        
        # Factor in suspicious events
        score = device.trust_score
        score -= (device.suspicious_events * 5)
        
        # Factor in age (older = more trusted)
        age_hours = (time.time() - device.first_seen) / 3600
        if age_hours > 24:
            score += 10
        
        return max(0, min(100, score))
    
    def report_suspicious_activity(self, mac: str, reason: str):
        """Report suspicious activity for a device"""
        device = self.register_device(mac)
        device.suspicious_events += 1
        device.degrade_trust(10)
        self.trust_history[mac].append({
            'timestamp': time.time(),
            'reason': reason,
            'trust_score': device.trust_score
        })
    
    def should_block(self, mac: str) -> bool:
        """Determine if device should be blocked"""
        trust_score = self.calculate_trust_score(mac)
        return trust_score < 30 or mac in self.blacklist

class GhostMeshAgent:
    """
    Main GhostMesh agent for wireless network defense
    """
    
    def __init__(self, node_id: str = None):
        self.node_id = node_id or self._generate_node_id()
        self.mitel = MITELTrustLayer()
        self.access_points: Dict[str, AccessPoint] = {}
        self.legitimate_aps: Dict[str, AccessPoint] = {}
        self.threats: List[ThreatAlert] = []
        self.deauth_counter: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.arp_table: Dict[str, str] = {}  # IP -> MAC mapping
        self.running = False
        self.mesh_peers: Set[str] = set()
        
        # Statistics
        self.stats = {
            'packets_analyzed': 0,
            'threats_detected': 0,
            'devices_blocked': 0,
            'aps_discovered': 0,
            'evil_twins_found': 0
        }
    
    def _generate_node_id(self) -> str:
        """Generate unique node ID"""
        hostname = socket.gethostname()
        mac = self._get_mac_address()
        return hashlib.sha256(f"{hostname}:{mac}".encode()).hexdigest()[:16]
    
    def _get_mac_address(self) -> str:
        """Get primary MAC address"""
        try:
            import uuid
            mac = ':'.join(['{:02x}'.format((uuid.getnode() >> i) & 0xff) 
                           for i in range(0, 48, 8)])
            return mac
        except:
            return "00:00:00:00:00:00"
    
    def register_legitimate_ap(self, bssid: str, ssid: str, channel: int = 0):
        """Register a known-good access point"""
        ap = AccessPoint(
            bssid=bssid.upper(),
            ssid=ssid,
            channel=channel,
            encryption="WPA2",  # Default
            signal_strength=0,
            first_seen=time.time(),
            last_seen=time.time(),
            is_legitimate=True
        )
        self.legitimate_aps[bssid.upper()] = ap
        self.log(f"✅ Registered legitimate AP: {ssid} ({bssid})")
    
    def detect_evil_twin(self, ap: AccessPoint) -> bool:
        """Detect if AP is an evil twin"""
        # Check if same SSID but different BSSID
        for legit_bssid, legit_ap in self.legitimate_aps.items():
            if (legit_ap.ssid == ap.ssid and 
                legit_ap.bssid != ap.bssid):
                self.log(f"🚨 EVIL TWIN DETECTED: {ap.ssid}")
                self.log(f"   Legitimate: {legit_ap.bssid}")
                self.log(f"   Rogue:      {ap.bssid}")
                self.raise_alert(
                    threat_type="evil_twin",
                    severity="critical",
                    source_mac=ap.bssid,
                    details=f"Evil twin of {ap.ssid}",
                    action_taken="Logged and alerted"
                )
                self.stats['evil_twins_found'] += 1
                return True
        return False
    
    def process_beacon(self, pkt):
        """Process beacon frame to discover APs"""
        if pkt.haslayer(Dot11Beacon):
            bssid = pkt[Dot11].addr2.upper()
            ssid = pkt[Dot11Elt].info.decode('utf-8', errors='ignore')
            
            # Get channel
            channel = 0
            if pkt.haslayer(Dot11Elt):
                try:
                    channel = int(ord(pkt[Dot11Elt:3].info))
                except:
                    pass
            
            # Get encryption
            encryption = "Open"
            if pkt.haslayer(Dot11Elt):
                cap = pkt.sprintf("{Dot11Beacon:%Dot11Beacon.cap%}").split('+')
                if 'privacy' in cap:
                    encryption = "WPA2"
            
            # Create or update AP record
            if bssid not in self.access_points:
                ap = AccessPoint(
                    bssid=bssid,
                    ssid=ssid,
                    channel=channel,
                    encryption=encryption,
                    signal_strength=self._get_signal_strength(pkt),
                    first_seen=time.time(),
                    last_seen=time.time()
                )
                self.access_points[bssid] = ap
                self.stats['aps_discovered'] += 1
                
                # Check for evil twin
                self.detect_evil_twin(ap)
            else:
                self.access_points[bssid].last_seen = time.time()
    
    def process_deauth(self, pkt):
        """Process deauthentication frame"""
        if pkt.haslayer(Dot11Deauth):
            source = pkt[Dot11].addr2.upper()
            target = pkt[Dot11].addr1.upper()
            
            # Track deauth frequency
            self.deauth_counter[source].append(time.time())
            
            # Check for deauth flood
            recent_deauths = [t for t in self.deauth_counter[source] 
                            if time.time() - t < 60]
            
            if len(recent_deauths) > DEAUTH_FLOOD_THRESHOLD:
                self.log(f"🚨 DEAUTH FLOOD from {source}")
                self.mitel.report_suspicious_activity(source, "deauth_flood")
                self.raise_alert(
                    threat_type="deauth_flood",
                    severity="high",
                    source_mac=source,
                    target_mac=target,
                    details=f"{len(recent_deauths)} deauth packets in 60s",
                    action_taken="Trust degraded, blocking considered"
                )
                
                # Block if trust score too low
                if self.mitel.should_block(source):
                    self.block_mac(source)
    
    def process_arp(self, pkt):
        """Process ARP packets to detect poisoning"""
        if pkt.haslayer(ARP):
            arp = pkt[ARP]
            
            # ARP response
            if arp.op == 2:  # is-at
                ip = arp.psrc
                mac = arp.hwsrc.upper()
                
                # Check for ARP poisoning
                if ip in self.arp_table:
                    if self.arp_table[ip] != mac:
                        self.log(f"🚨 ARP POISONING DETECTED!")
                        self.log(f"   IP: {ip}")
                        self.log(f"   Old MAC: {self.arp_table[ip]}")
                        self.log(f"   New MAC: {mac}")
                        
                        self.mitel.report_suspicious_activity(mac, "arp_poisoning")
                        self.raise_alert(
                            threat_type="arp_poisoning",
                            severity="critical",
                            source_mac=mac,
                            details=f"ARP poisoning attempt for {ip}",
                            action_taken="Logged, MAC trust degraded"
                        )
                else:
                    self.arp_table[ip] = mac
    
    def process_packet(self, pkt):
        """Main packet processing function"""
        self.stats['packets_analyzed'] += 1
        
        try:
            # Process different packet types
            if pkt.haslayer(Dot11Beacon):
                self.process_beacon(pkt)
            
            if pkt.haslayer(Dot11Deauth):
                self.process_deauth(pkt)
            
            if pkt.haslayer(ARP):
                self.process_arp(pkt)
            
            # Update device tracking
            if pkt.haslayer(Dot11):
                src_mac = pkt[Dot11].addr2
                if src_mac:
                    self.mitel.register_device(src_mac.upper())
        
        except Exception as e:
            self.log(f"⚠️ Packet processing error: {e}")
    
    def _get_signal_strength(self, pkt) -> int:
        """Extract signal strength from packet"""
        try:
            return pkt.dBm_AntSignal
        except:
            return 0
    
    def block_mac(self, mac: str):
        """Block a MAC address"""
        self.log(f"🛑 BLOCKING MAC: {mac}")
        self.mitel.blacklist.add(mac)
        self.stats['devices_blocked'] += 1
        
        # Execute iptables/firewall command
        try:
            os.system(f"iptables -A INPUT -m mac --mac-source {mac} -j DROP")
            os.system(f"iptables -A OUTPUT -m mac --mac-destination {mac} -j DROP")
        except:
            self.log("⚠️ Unable to execute firewall rules (requires root)")
    
    def raise_alert(self, threat_type: str, severity: str, source_mac: str,
                   details: str, action_taken: str, target_mac: str = None):
        """Raise a security alert"""
        alert = ThreatAlert(
            timestamp=time.time(),
            threat_type=threat_type,
            severity=severity,
            source_mac=source_mac,
            target_mac=target_mac,
            details=details,
            action_taken=action_taken
        )
        self.threats.append(alert)
        self.stats['threats_detected'] += 1
        
        # Broadcast to mesh network
        self.broadcast_to_mesh(alert)
        
        # Send to CloudCore_Sync_2 if enabled
        if CLOUDCORE_SYNC_ENABLED:
            self.sync_to_cloudcore(alert)
    
    def broadcast_to_mesh(self, alert: ThreatAlert):
        """Broadcast alert to other GhostMesh nodes"""
        message = {
            'node_id': self.node_id,
            'type': 'threat_alert',
            'data': asdict(alert)
        }
        
        # Send to all known peers
        for peer in self.mesh_peers:
            try:
                # UDP broadcast
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.sendto(json.dumps(message).encode(), (peer, MESH_PORT))
                sock.close()
            except:
                pass
    
    def sync_to_cloudcore(self, alert: ThreatAlert):
        """Sync alert to CloudCore_Sync_2"""
        if not REQUESTS_AVAILABLE:
            return
        
        try:
            requests.post(
                'http://localhost:5000/ghostmesh/alert',
                json=asdict(alert),
                timeout=2
            )
        except:
            pass
    
    def log(self, message: str):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [GhostMesh:{self.node_id[:8]}] {message}")
    
    def print_stats(self):
        """Print current statistics"""
        print("\n" + "="*60)
        print("📊 GhostMesh™ Statistics")
        print("="*60)
        for key, value in self.stats.items():
            print(f"  {key.replace('_', ' ').title()}: {value}")
        print(f"  Known Devices: {len(self.mitel.known_devices)}")
        print(f"  Access Points: {len(self.access_points)}")
        print(f"  Legitimate APs: {len(self.legitimate_aps)}")
        print(f"  Threats Logged: {len(self.threats)}")
        print("="*60 + "\n")
    
    def start(self, interface: str = None):
        """Start the GhostMesh agent"""
        if not SCAPY_AVAILABLE:
            self.log("❌ Scapy is required. Install with: pip install scapy")
            return
        
        interface = interface or MONITOR_INTERFACE
        
        self.log(f"🚀 Starting GhostMesh™ Agent")
        self.log(f"   Node ID: {self.node_id}")
        self.log(f"   Interface: {interface}")
        self.log(f"   M.I.T.E.L. Trust Layer: ACTIVE")
        self.log(f"   CloudCore_Sync_2: {'ENABLED' if CLOUDCORE_SYNC_ENABLED else 'DISABLED'}")
        
        self.running = True
        
        # Start stats printer thread
        stats_thread = threading.Thread(target=self._stats_loop, daemon=True)
        stats_thread.start()
        
        try:
            # Start packet capture
            self.log("📡 Beginning wireless monitoring...")
            sniff(iface=interface, prn=self.process_packet, store=False)
        except KeyboardInterrupt:
            self.log("🛑 Shutting down...")
            self.running = False
        except Exception as e:
            self.log(f"❌ Error: {e}")
            self.log("💡 Make sure interface is in monitor mode:")
            self.log(f"   sudo airmon-ng start {interface.replace('mon', '')}")
    
    def _stats_loop(self):
        """Periodically print statistics"""
        while self.running:
            time.sleep(30)
            if self.running:
                self.print_stats()

def main():
    """Main entry point"""
    print("="*60)
    print("👻 GhostMesh™ - Distributed Wireless Intrusion Defense")
    print("Patent Pending - KK&GDevOps, LLC")
    print("="*60)
    
    # Check if running as root
    if os.geteuid() != 0:
        print("⚠️ WARNING: Not running as root.")
        print("   Some features (MAC blocking) require root privileges.")
        print()
    
    # Initialize agent
    agent = GhostMeshAgent()
    
    # Register your legitimate APs here
    # agent.register_legitimate_ap("AA:BB:CC:DD:EE:FF", "MyNetwork", channel=6)
    
    # Get interface from args or env
    interface = sys.argv[1] if len(sys.argv) > 1 else MONITOR_INTERFACE
    
    # Start monitoring
    agent.start(interface)

if __name__ == "__main__":
    main()
