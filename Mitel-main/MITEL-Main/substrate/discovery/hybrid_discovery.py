#!/usr/bin/env python3
"""
Hybrid Discovery Engine
========================

Combines UDP broadcast (fast, same subnet) with mDNS (robust, cross-subnet)
for maximum compatibility and zero-config operation.

Features:
- UDP broadcast for same-subnet discovery (fast, <1s)
- mDNS for cross-subnet discovery (robust, works everywhere)
- Automatic fallback if mDNS unavailable
- Zero hard-coded IPs
- Works on university/hospital/enterprise networks
"""

import sys
import os
import logging
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
import time

# Import both discovery engines
from .auto_discovery import AutoDiscovery, DiscoveredPeer
try:
    from .mdns_discovery import MDNSDiscovery, MDNSPeer, MDNS_AVAILABLE
except ImportError:
    MDNS_AVAILABLE = False
    MDNSDiscovery = None
    MDNSPeer = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class HybridPeer:
    """Unified peer representation from both discovery methods"""
    node_id: str
    ip: str
    port: int
    platform: str
    is_master: bool = False
    last_seen: float = field(default_factory=time.time)
    capabilities: List[str] = field(default_factory=list)
    discovery_method: str = "unknown"  # "udp" or "mdns"


class HybridDiscovery:
    """
    Hybrid discovery engine using both UDP broadcast and mDNS.
    
    Strategy:
    1. Always use UDP broadcast (fast, works on same subnet)
    2. If mDNS available, also use it (cross-subnet capability)
    3. Merge results from both methods
    4. Prefer UDP for same-subnet (lower latency)
    5. Use mDNS for cross-subnet scenarios
    """
    
    def __init__(self, node_id: str, local_ip: str, fabric_port: int,
                 is_master: bool = False, platform: str = "linux"):
        """
        Initialize hybrid discovery engine.
        
        Args:
            node_id: Node identifier
            local_ip: Local IP address
            fabric_port: Fabric port for connections
            is_master: Whether this node is master
            platform: Platform type
        """
        self.node_id = node_id
        self.local_ip = local_ip
        self.fabric_port = fabric_port
        self.is_master = is_master
        self.platform = platform
        
        # Discovery engines
        self.udp_discovery: Optional[AutoDiscovery] = None
        self.mdns_discovery: Optional[MDNSDiscovery] = None
        
        # Unified peer list
        self.discovered_peers: Dict[str, HybridPeer] = {}
        self.master_peer: Optional[HybridPeer] = None
        
        # Discovery state
        self.running = False
        
        # Callbacks
        self.on_master_discovered: Optional[Callable] = None
        self.on_peer_discovered: Optional[Callable] = None
        self.on_peer_lost: Optional[Callable] = None
        
        logger.info(f"[HYBRID_DISCOVERY] Initialized for node {node_id[:12]}... (master={is_master})")
        logger.info(f"[HYBRID_DISCOVERY] UDP broadcast: enabled")
        logger.info(f"[HYBRID_DISCOVERY] mDNS/Avahi: {'enabled' if MDNS_AVAILABLE else 'disabled (install zeroconf)'}")
    
    def start(self):
        """Start hybrid discovery (UDP + mDNS)"""
        if self.running:
            return
        
        self.running = True
        
        # Start UDP broadcast discovery
        self.udp_discovery = AutoDiscovery(
            node_id=self.node_id,
            local_ip=self.local_ip,
            fabric_port=self.fabric_port,
            is_master=self.is_master,
            platform=self.platform
        )
        
        # Set up UDP callbacks
        self.udp_discovery.on_peer_discovered = self._on_udp_peer_discovered
        self.udp_discovery.on_master_discovered = self._on_udp_master_discovered
        
        self.udp_discovery.start()
        logger.info("[HYBRID_DISCOVERY] UDP broadcast discovery started")
        
        # Start mDNS discovery if available
        if MDNS_AVAILABLE and MDNSDiscovery:
            try:
                self.mdns_discovery = MDNSDiscovery(
                    node_id=self.node_id,
                    local_ip=self.local_ip,
                    fabric_port=self.fabric_port,
                    is_master=self.is_master,
                    platform=self.platform
                )
                
                # Set up mDNS callbacks
                self.mdns_discovery.on_peer_discovered = self._on_mdns_peer_discovered
                self.mdns_discovery.on_master_discovered = self._on_mdns_master_discovered
                self.mdns_discovery.on_peer_lost = self._on_mdns_peer_lost
                
                self.mdns_discovery.start()
                logger.info("[HYBRID_DISCOVERY] mDNS discovery started (cross-subnet enabled)")
                
            except Exception as e:
                logger.warning(f"[HYBRID_DISCOVERY] Failed to start mDNS: {e}")
                logger.info("[HYBRID_DISCOVERY] Continuing with UDP broadcast only")
        else:
            logger.info("[HYBRID_DISCOVERY] mDNS unavailable - using UDP broadcast only")
            logger.info("[HYBRID_DISCOVERY] For cross-subnet support, install: pip install zeroconf")
        
        logger.info("[HYBRID_DISCOVERY] Started - discovering peers via UDP and mDNS")
    
    def stop(self):
        """Stop hybrid discovery"""
        self.running = False
        
        if self.udp_discovery:
            self.udp_discovery.stop()
            logger.info("[HYBRID_DISCOVERY] UDP discovery stopped")
        
        if self.mdns_discovery:
            self.mdns_discovery.stop()
            logger.info("[HYBRID_DISCOVERY] mDNS discovery stopped")
        
        logger.info("[HYBRID_DISCOVERY] Stopped")
    
    def _on_udp_peer_discovered(self, peer: DiscoveredPeer):
        """Handle peer discovered via UDP broadcast"""
        hybrid_peer = HybridPeer(
            node_id=peer.node_id,
            ip=peer.ip,
            port=peer.port,
            platform=peer.platform,
            is_master=peer.is_master,
            capabilities=peer.capabilities,
            discovery_method="udp"
        )
        
        # Store or update peer
        existing = self.discovered_peers.get(peer.node_id)
        if not existing or existing.discovery_method != "udp":
            self.discovered_peers[peer.node_id] = hybrid_peer
            logger.info(f"[HYBRID_DISCOVERY] Peer discovered via UDP: {peer.node_id[:12]}... at {peer.ip}:{peer.port}")
            
            # Notify callback
            if self.on_peer_discovered:
                self.on_peer_discovered(hybrid_peer)
    
    def _on_udp_master_discovered(self, peer: DiscoveredPeer):
        """Handle master discovered via UDP broadcast"""
        hybrid_peer = HybridPeer(
            node_id=peer.node_id,
            ip=peer.ip,
            port=peer.port,
            platform=peer.platform,
            is_master=True,
            capabilities=peer.capabilities,
            discovery_method="udp"
        )
        
        self.discovered_peers[peer.node_id] = hybrid_peer
        
        if not self.master_peer:
            self.master_peer = hybrid_peer
            logger.info(f"[HYBRID_DISCOVERY] Master discovered via UDP: {peer.node_id[:12]}... at {peer.ip}:{peer.port}")
            
            # Notify callback
            if self.on_master_discovered:
                self.on_master_discovered(hybrid_peer)
    
    def _on_mdns_peer_discovered(self, peer):
        """Handle peer discovered via mDNS"""
        hybrid_peer = HybridPeer(
            node_id=peer.node_id,
            ip=peer.ip,
            port=peer.port,
            platform=peer.platform,
            is_master=peer.is_master,
            capabilities=peer.capabilities,
            discovery_method="mdns"
        )
        
        # Only store if not already discovered via UDP (UDP is faster for same subnet)
        if peer.node_id not in self.discovered_peers:
            self.discovered_peers[peer.node_id] = hybrid_peer
            logger.info(f"[HYBRID_DISCOVERY] Peer discovered via mDNS: {peer.node_id[:12]}... at {peer.ip}:{peer.port}")
            
            # Notify callback
            if self.on_peer_discovered:
                self.on_peer_discovered(hybrid_peer)
        else:
            # Update last_seen
            self.discovered_peers[peer.node_id].last_seen = time.time()
    
    def _on_mdns_master_discovered(self, peer):
        """Handle master discovered via mDNS"""
        hybrid_peer = HybridPeer(
            node_id=peer.node_id,
            ip=peer.ip,
            port=peer.port,
            platform=peer.platform,
            is_master=True,
            capabilities=peer.capabilities,
            discovery_method="mdns"
        )
        
        # Store peer
        if peer.node_id not in self.discovered_peers:
            self.discovered_peers[peer.node_id] = hybrid_peer
        
        # Set as master if we don't have one
        if not self.master_peer:
            self.master_peer = hybrid_peer
            logger.info(f"[HYBRID_DISCOVERY] Master discovered via mDNS: {peer.node_id[:12]}... at {peer.ip}:{peer.port}")
            
            # Notify callback
            if self.on_master_discovered:
                self.on_master_discovered(hybrid_peer)
    
    def _on_mdns_peer_lost(self, peer):
        """Handle peer lost via mDNS"""
        if peer.node_id in self.discovered_peers:
            lost_peer = self.discovered_peers[peer.node_id]
            
            # Only remove if it was discovered via mDNS (UDP might still see it)
            if lost_peer.discovery_method == "mdns":
                del self.discovered_peers[peer.node_id]
                logger.info(f"[HYBRID_DISCOVERY] Peer lost via mDNS: {peer.node_id[:12]}...")
                
                # Clear master if it was the master
                if self.master_peer and self.master_peer.node_id == peer.node_id:
                    self.master_peer = None
                
                # Notify callback
                if self.on_peer_lost:
                    self.on_peer_lost(lost_peer)
    
    def get_peers(self) -> List[HybridPeer]:
        """Get list of all discovered peers"""
        return list(self.discovered_peers.values())
    
    def get_master(self) -> Optional[HybridPeer]:
        """Get discovered master peer"""
        return self.master_peer
    
    def get_peer(self, node_id: str) -> Optional[HybridPeer]:
        """Get specific peer by node ID"""
        return self.discovered_peers.get(node_id)
    
    def is_cross_subnet_capable(self) -> bool:
        """Check if cross-subnet discovery is available"""
        return MDNS_AVAILABLE and self.mdns_discovery is not None
    
    def get_discovery_stats(self) -> Dict[str, int]:
        """Get discovery statistics"""
        stats = {
            'total_peers': len(self.discovered_peers),
            'udp_peers': sum(1 for p in self.discovered_peers.values() if p.discovery_method == 'udp'),
            'mdns_peers': sum(1 for p in self.discovered_peers.values() if p.discovery_method == 'mdns'),
            'master_found': 1 if self.master_peer else 0,
            'cross_subnet_enabled': 1 if self.is_cross_subnet_capable() else 0
        }
        return stats


def test_hybrid_discovery():
    """Test hybrid discovery"""
    import platform
    
    # Create discovery instance
    node_id = f"test-hybrid-{int(time.time())}"
    discovery = HybridDiscovery(
        node_id=node_id,
        local_ip="",  # Auto-detect
        fabric_port=7777,
        is_master=False,
        platform=platform.system().lower()
    )
    
    # Set up callbacks
    def on_peer_discovered(peer: HybridPeer):
        print(f"✅ Peer discovered ({peer.discovery_method}): {peer.node_id[:12]}... at {peer.ip}:{peer.port}")
    
    def on_master_discovered(peer: HybridPeer):
        print(f"👑 Master discovered ({peer.discovery_method}): {peer.node_id[:12]}... at {peer.ip}:{peer.port}")
    
    def on_peer_lost(peer: HybridPeer):
        print(f"❌ Peer lost: {peer.node_id[:12]}...")
    
    discovery.on_peer_discovered = on_peer_discovered
    discovery.on_master_discovered = on_master_discovered
    discovery.on_peer_lost = on_peer_lost
    
    # Start discovery
    print(f"Starting hybrid discovery for node {node_id[:12]}...")
    print(f"Cross-subnet capable: {discovery.is_cross_subnet_capable()}")
    discovery.start()
    
    try:
        # Run for 60 seconds
        for i in range(60):
            time.sleep(1)
            if i % 10 == 0:
                stats = discovery.get_discovery_stats()
                print(f"\n[{i}s] Discovery stats: {stats}")
                peers = discovery.get_peers()
                for peer in peers:
                    print(f"  - {peer.node_id[:12]}... ({peer.ip}:{peer.port}) via {peer.discovery_method} master={peer.is_master}")
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        discovery.stop()


if __name__ == "__main__":
    test_hybrid_discovery()
