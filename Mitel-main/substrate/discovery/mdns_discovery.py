#!/usr/bin/env python3
"""
mDNS/Avahi Discovery Engine
============================

Cross-subnet, zero-config service discovery using mDNS/Avahi.
Works across different subnets (university, hospital, enterprise networks).

Features:
- mDNS service advertisement (_omni._tcp.local)
- Cross-subnet peer discovery
- Zero hard-coded IPs
- Automatic service registration
- Compatible with Linux (Avahi), macOS (Bonjour), Windows (Bonjour SDK)
"""

import sys
import os
import socket
import json
import time
import threading
import logging
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field

try:
    from zeroconf import ServiceBrowser, ServiceInfo, Zeroconf, ServiceStateChange
    MDNS_AVAILABLE = True
except ImportError:
    MDNS_AVAILABLE = False
    logging.warning("[MDNS_DISCOVERY] zeroconf not installed. Install with: pip install zeroconf")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


MDNS_SERVICE_TYPE = "_omni._tcp.local."
MDNS_DISCOVERY_INTERVAL = 10  # Seconds between service checks


@dataclass
class MDNSPeer:
    """Discovered peer via mDNS"""
    node_id: str
    hostname: str
    ip: str
    port: int
    platform: str
    is_master: bool = False
    last_seen: float = field(default_factory=time.time)
    capabilities: List[str] = field(default_factory=list)
    properties: Dict[str, str] = field(default_factory=dict)


class MDNSDiscovery:
    """
    mDNS/Avahi-based service discovery for cross-subnet operation.
    
    Features:
    - Advertises OMNI service via mDNS (_omni._tcp.local)
    - Discovers peers across different subnets
    - Zero hard-coded IPs required
    - Works on university/hospital/enterprise networks
    """
    
    def __init__(self, node_id: str, local_ip: str, fabric_port: int,
                 is_master: bool = False, platform: str = "linux"):
        """
        Initialize mDNS discovery engine.
        
        Args:
            node_id: Node identifier
            local_ip: Local IP address (auto-detected if not provided)
            fabric_port: Fabric port for connections
            is_master: Whether this node is master
            platform: Platform type
        """
        if not MDNS_AVAILABLE:
            raise ImportError("zeroconf library required. Install with: pip install zeroconf")
        
        self.node_id = node_id
        self.local_ip = local_ip or self._get_local_ip()
        self.fabric_port = fabric_port
        self.is_master = is_master
        self.platform = platform
        
        # mDNS state
        self.zeroconf: Optional[Zeroconf] = None
        self.service_info: Optional[ServiceInfo] = None
        self.browser: Optional[ServiceBrowser] = None
        
        # Discovered peers
        self.discovered_peers: Dict[str, MDNSPeer] = {}
        self.master_peer: Optional[MDNSPeer] = None
        
        # Discovery state
        self.running = False
        self.monitor_thread: Optional[threading.Thread] = None
        
        # Callbacks
        self.on_master_discovered: Optional[Callable] = None
        self.on_peer_discovered: Optional[Callable] = None
        self.on_peer_lost: Optional[Callable] = None
        
        logger.info(f"[MDNS_DISCOVERY] Initialized for node {node_id[:12]}... (master={is_master})")
        logger.info(f"[MDNS_DISCOVERY] Local IP: {self.local_ip}, Port: {fabric_port}")
    
    def _get_local_ip(self) -> str:
        """Auto-detect local IP address"""
        try:
            # Create UDP socket to determine local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except Exception as e:
            logger.warning(f"[MDNS_DISCOVERY] Failed to auto-detect IP: {e}")
            return "127.0.0.1"
    
    def start(self):
        """Start mDNS service discovery"""
        if self.running:
            return
        
        if not MDNS_AVAILABLE:
            logger.error("[MDNS_DISCOVERY] Cannot start - zeroconf not available")
            return
        
        self.running = True
        
        try:
            # Initialize Zeroconf
            self.zeroconf = Zeroconf()
            
            # Register our service
            self._register_service()
            
            # Start browsing for peers
            self.browser = ServiceBrowser(
                self.zeroconf,
                MDNS_SERVICE_TYPE,
                handlers=[self._on_service_state_change]
            )
            
            # Start monitoring thread
            self.monitor_thread = threading.Thread(
                target=self._monitor_loop,
                daemon=True,
                name="mdns-monitor"
            )
            self.monitor_thread.start()
            
            logger.info("[MDNS_DISCOVERY] Started - advertising and browsing for peers")
            
        except Exception as e:
            logger.error(f"[MDNS_DISCOVERY] Failed to start: {e}")
            self.running = False
    
    def stop(self):
        """Stop mDNS service discovery"""
        self.running = False
        
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=2)
        
        if self.service_info and self.zeroconf:
            try:
                self.zeroconf.unregister_service(self.service_info)
                logger.info("[MDNS_DISCOVERY] Unregistered service")
            except Exception as e:
                logger.warning(f"[MDNS_DISCOVERY] Failed to unregister service: {e}")
        
        if self.zeroconf:
            try:
                self.zeroconf.close()
                logger.info("[MDNS_DISCOVERY] Closed Zeroconf")
            except Exception as e:
                logger.warning(f"[MDNS_DISCOVERY] Failed to close Zeroconf: {e}")
        
        logger.info("[MDNS_DISCOVERY] Stopped")
    
    def _register_service(self):
        """Register OMNI service via mDNS"""
        try:
            # Service name: omni-<node_id_short>._omni._tcp.local.
            service_name = f"omni-{self.node_id[:8]}.{MDNS_SERVICE_TYPE}"
            
            # Service properties (metadata)
            properties = {
                'node_id': self.node_id,
                'platform': self.platform,
                'is_master': str(self.is_master),
                'version': '1.0',
                'capabilities': 'sync,file_transfer,discovery'
            }
            
            # Create ServiceInfo
            self.service_info = ServiceInfo(
                MDNS_SERVICE_TYPE,
                service_name,
                addresses=[socket.inet_aton(self.local_ip)],
                port=self.fabric_port,
                properties=properties,
                server=f"{socket.gethostname()}.local."
            )
            
            # Register service
            self.zeroconf.register_service(self.service_info)
            
            logger.info(f"[MDNS_DISCOVERY] Registered service: {service_name}")
            logger.info(f"[MDNS_DISCOVERY] Service properties: {properties}")
            
        except Exception as e:
            logger.error(f"[MDNS_DISCOVERY] Failed to register service: {e}")
    
    def _on_service_state_change(self, zeroconf: Zeroconf, service_type: str,
                                  name: str, state_change: ServiceStateChange):
        """Handle service state changes (added/removed/updated)"""
        try:
            if state_change is ServiceStateChange.Added:
                self._on_service_added(zeroconf, service_type, name)
            elif state_change is ServiceStateChange.Removed:
                self._on_service_removed(zeroconf, service_type, name)
            elif state_change is ServiceStateChange.Updated:
                self._on_service_updated(zeroconf, service_type, name)
        except Exception as e:
            logger.error(f"[MDNS_DISCOVERY] Error handling service state change: {e}")
    
    def _on_service_added(self, zeroconf: Zeroconf, service_type: str, name: str):
        """Handle new service discovered"""
        try:
            info = zeroconf.get_service_info(service_type, name)
            if not info:
                return
            
            # Extract peer information
            properties = {k.decode('utf-8'): v.decode('utf-8') if isinstance(v, bytes) else v
                         for k, v in info.properties.items()}
            
            peer_node_id = properties.get('node_id', '')
            
            # Ignore our own service
            if peer_node_id == self.node_id:
                return
            
            # Extract IP address
            if info.addresses:
                peer_ip = socket.inet_ntoa(info.addresses[0])
            else:
                logger.warning(f"[MDNS_DISCOVERY] No address for service {name}")
                return
            
            # Create peer object
            peer = MDNSPeer(
                node_id=peer_node_id,
                hostname=info.server.rstrip('.'),
                ip=peer_ip,
                port=info.port,
                platform=properties.get('platform', 'unknown'),
                is_master=properties.get('is_master', 'false').lower() == 'true',
                capabilities=properties.get('capabilities', '').split(','),
                properties=properties
            )
            
            # Store peer
            self.discovered_peers[peer_node_id] = peer
            
            logger.info(f"[MDNS_DISCOVERY] Discovered peer: {peer_node_id[:12]}... at {peer_ip}:{peer.port} (master={peer.is_master})")
            
            # Check if this is a master
            if peer.is_master and not self.master_peer:
                self.master_peer = peer
                if self.on_master_discovered:
                    self.on_master_discovered(peer)
            
            # Notify peer discovered
            if self.on_peer_discovered:
                self.on_peer_discovered(peer)
                
        except Exception as e:
            logger.error(f"[MDNS_DISCOVERY] Error processing added service {name}: {e}")
    
    def _on_service_removed(self, zeroconf: Zeroconf, service_type: str, name: str):
        """Handle service removed"""
        try:
            # Find peer by service name
            for node_id, peer in list(self.discovered_peers.items()):
                if f"omni-{node_id[:8]}" in name:
                    logger.info(f"[MDNS_DISCOVERY] Peer lost: {node_id[:12]}... ({peer.ip})")
                    del self.discovered_peers[node_id]
                    
                    # Clear master if it was the master
                    if self.master_peer and self.master_peer.node_id == node_id:
                        self.master_peer = None
                    
                    # Notify peer lost
                    if self.on_peer_lost:
                        self.on_peer_lost(peer)
                    break
                    
        except Exception as e:
            logger.error(f"[MDNS_DISCOVERY] Error processing removed service {name}: {e}")
    
    def _on_service_updated(self, zeroconf: Zeroconf, service_type: str, name: str):
        """Handle service updated"""
        # Treat as add (will update existing peer)
        self._on_service_added(zeroconf, service_type, name)
    
    def _monitor_loop(self):
        """Monitor discovered peers and update last_seen"""
        while self.running:
            try:
                current_time = time.time()
                
                # Update last_seen for all peers (they're still in zeroconf cache)
                for peer in self.discovered_peers.values():
                    peer.last_seen = current_time
                
                time.sleep(MDNS_DISCOVERY_INTERVAL)
                
            except Exception as e:
                logger.error(f"[MDNS_DISCOVERY] Error in monitor loop: {e}")
                time.sleep(1)
    
    def get_peers(self) -> List[MDNSPeer]:
        """Get list of discovered peers"""
        return list(self.discovered_peers.values())
    
    def get_master(self) -> Optional[MDNSPeer]:
        """Get discovered master peer"""
        return self.master_peer
    
    def is_peer_alive(self, node_id: str, timeout: float = 30.0) -> bool:
        """Check if peer is still alive"""
        peer = self.discovered_peers.get(node_id)
        if not peer:
            return False
        return (time.time() - peer.last_seen) < timeout


def test_mdns_discovery():
    """Test mDNS discovery"""
    if not MDNS_AVAILABLE:
        print("ERROR: zeroconf not installed. Install with: pip install zeroconf")
        return
    
    import platform
    
    # Create discovery instance
    node_id = f"test-node-{int(time.time())}"
    discovery = MDNSDiscovery(
        node_id=node_id,
        local_ip="",  # Auto-detect
        fabric_port=7777,
        is_master=False,
        platform=platform.system().lower()
    )
    
    # Set up callbacks
    def on_peer_discovered(peer: MDNSPeer):
        print(f"✅ Peer discovered: {peer.node_id[:12]}... at {peer.ip}:{peer.port}")
    
    def on_master_discovered(peer: MDNSPeer):
        print(f"👑 Master discovered: {peer.node_id[:12]}... at {peer.ip}:{peer.port}")
    
    def on_peer_lost(peer: MDNSPeer):
        print(f"❌ Peer lost: {peer.node_id[:12]}...")
    
    discovery.on_peer_discovered = on_peer_discovered
    discovery.on_master_discovered = on_master_discovered
    discovery.on_peer_lost = on_peer_lost
    
    # Start discovery
    print(f"Starting mDNS discovery for node {node_id[:12]}...")
    discovery.start()
    
    try:
        # Run for 60 seconds
        for i in range(60):
            time.sleep(1)
            if i % 10 == 0:
                peers = discovery.get_peers()
                print(f"\n[{i}s] Discovered {len(peers)} peers:")
                for peer in peers:
                    print(f"  - {peer.node_id[:12]}... ({peer.ip}:{peer.port}) master={peer.is_master}")
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        discovery.stop()


if __name__ == "__main__":
    test_mdns_discovery()
