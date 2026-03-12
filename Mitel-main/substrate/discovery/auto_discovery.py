#!/usr/bin/env python3
"""
Auto-Discovery Engine
=====================

Auto-discovery for nodes leaving and returning:
- Android leaves → Standalone mode
- Android returns → Auto-discovers master, reconnects
- Continuous discovery loop
- Master announcement (UDP broadcast)
- Peer discovery (UDP broadcast response)
"""

import sys
import os
import socket
import json
import time
import threading
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


DISCOVERY_PORT = 7891  # UDP broadcast port for discovery
DISCOVERY_INTERVAL = 5  # Seconds between discovery attempts
MASTER_TIMEOUT = 30  # Seconds before considering master offline
STANDALONE_THRESHOLD = 60  # Seconds before entering standalone mode


@dataclass
class DiscoveredPeer:
    """Discovered peer information"""
    node_id: str
    ip: str
    port: int
    platform: str
    is_master: bool = False
    last_seen: float = field(default_factory=time.time)
    capabilities: List[str] = field(default_factory=list)


class AutoDiscovery:
    """
    Auto-discovery engine.
    
    Features:
    - Continuous UDP broadcast discovery
    - Master announcement (if master)
    - Peer discovery (if peer)
    - Standalone mode detection
    - Auto-reconnection
    """
    
    def __init__(self, node_id: str, local_ip: str, fabric_port: int, 
                 is_master: bool = False, platform: str = "linux"):
        """
        Initialize auto-discovery engine.
        
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
        
        # Calculate subnet broadcast address for offline-first operation
        self.broadcast_addr = self._calculate_broadcast_address(local_ip)
        
        # Discovered peers
        self.discovered_peers: Dict[str, DiscoveredPeer] = {}
        self.master_peer: Optional[DiscoveredPeer] = None
        
        # Discovery state
        self.running = False
        self.standalone_mode = False
        self.discovery_thread: Optional[threading.Thread] = None
        self.listener_thread: Optional[threading.Thread] = None
        
        # Callbacks
        self.on_master_discovered: Optional[callable] = None
        self.on_peer_discovered: Optional[callable] = None
        self.on_standalone_entered: Optional[callable] = None
        self.on_standalone_exited: Optional[callable] = None
        
        logger.info(f"[AUTO_DISCOVERY] Initialized for node {node_id[:12]}... (master={is_master})")
        logger.info(f"[AUTO_DISCOVERY] Using broadcast address: {self.broadcast_addr}")
    
    def _calculate_broadcast_address(self, ip: str) -> str:
        """
        Calculate subnet broadcast address for offline-first operation.
        Uses subnet-specific broadcast instead of global 255.255.255.255
        to work without internet gateway.
        
        For 192.168.1.x/24 networks, returns 192.168.1.255
        Falls back to 255.255.255.255 if calculation fails
        """
        try:
            # Assume /24 subnet (255.255.255.0) for most local networks
            # This works for 192.168.x.x and 10.x.x.x networks
            parts = ip.split('.')
            if len(parts) == 4:
                # Replace last octet with 255 for /24 broadcast
                broadcast = f"{parts[0]}.{parts[1]}.{parts[2]}.255"
                return broadcast
        except Exception as e:
            logger.warning(f"[AUTO_DISCOVERY] Failed to calculate broadcast address: {e}")
        
        # Fallback to global broadcast
        return '255.255.255.255'
    
    def start(self):
        """Start auto-discovery"""
        if self.running:
            return
        
        self.running = True
        
        # Start UDP listener (responds to discovery requests)
        self.listener_thread = threading.Thread(
            target=self._udp_listener_loop,
            daemon=True,
            name="auto-discovery-listener"
        )
        self.listener_thread.start()
        
        # Start discovery loop (broadcasts if peer, announces if master)
        self.discovery_thread = threading.Thread(
            target=self._discovery_loop,
            daemon=True,
            name="auto-discovery-loop"
        )
        self.discovery_thread.start()
        
        logger.info("[AUTO_DISCOVERY] Started")
    
    def stop(self):
        """Stop auto-discovery"""
        self.running = False
        if self.discovery_thread and self.discovery_thread.is_alive():
            self.discovery_thread.join(timeout=2)
        if self.listener_thread and self.listener_thread.is_alive():
            self.listener_thread.join(timeout=2)
        logger.info("[AUTO_DISCOVERY] Stopped")
    
    def _udp_listener_loop(self):
        """UDP listener - responds to discovery requests"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(('0.0.0.0', DISCOVERY_PORT))
            sock.settimeout(1.0)
            
            logger.info(f"[AUTO_DISCOVERY] UDP listener started on port {DISCOVERY_PORT}")
            
            while self.running:
                try:
                    data, addr = sock.recvfrom(1024)
                    request = json.loads(data.decode('utf-8'))
                    
                    if request.get('type') == 'discovery_request':
                        # Respond with our info
                        response = {
                            'type': 'discovery_response',
                            'node_id': self.node_id,
                            'ip': self.local_ip,
                            'port': self.fabric_port,
                            'platform': self.platform,
                            'is_master': self.is_master,
                            'capabilities': ['sync', 'file_transfer', 'discovery']
                        }
                        
                        sock.sendto(json.dumps(response).encode(), addr)
                        logger.debug(f"[AUTO_DISCOVERY] Responded to discovery from {addr[0]}")
                    
                    elif request.get('type') == 'master_announce':
                        # Master is announcing itself
                        master_id = request.get('node_id')
                        master_ip = request.get('ip')
                        master_port = request.get('port')
                        
                        if master_id != self.node_id:
                            peer = DiscoveredPeer(
                                node_id=master_id,
                                ip=master_ip,
                                port=master_port,
                                platform=request.get('platform', 'unknown'),
                                is_master=True,
                                last_seen=time.time()
                            )
                            
                            self.discovered_peers[master_id] = peer
                            self.master_peer = peer
                            
                            # Exit standalone mode if we were in it
                            if self.standalone_mode:
                                self.standalone_mode = False
                                logger.info(f"[AUTO_DISCOVERY] Master discovered: {master_id[:12]}... at {master_ip}:{master_port}")
                                logger.info("[AUTO_DISCOVERY] Exiting standalone mode")
                                if self.on_standalone_exited:
                                    self.on_standalone_exited(peer)
                            
                            if self.on_master_discovered:
                                self.on_master_discovered(peer)
                            
                            logger.info(f"[AUTO_DISCOVERY] Master discovered: {master_id[:12]}... at {master_ip}:{master_port}")
                    
                    elif request.get('type') == 'discovery_response':
                        # Peer responded to our discovery
                        peer_id = request.get('node_id')
                        if peer_id != self.node_id:
                            peer = DiscoveredPeer(
                                node_id=peer_id,
                                ip=request.get('ip'),
                                port=request.get('port'),
                                platform=request.get('platform', 'unknown'),
                                is_master=request.get('is_master', False),
                                last_seen=time.time(),
                                capabilities=request.get('capabilities', [])
                            )
                            
                            self.discovered_peers[peer_id] = peer
                            
                            if peer.is_master:
                                self.master_peer = peer
                                if self.standalone_mode:
                                    self.standalone_mode = False
                                    logger.info("[AUTO_DISCOVERY] Exiting standalone mode")
                                    if self.on_standalone_exited:
                                        self.on_standalone_exited(peer)
                            
                            if self.on_peer_discovered:
                                self.on_peer_discovered(peer)
                            
                            logger.debug(f"[AUTO_DISCOVERY] Peer discovered: {peer_id[:12]}... at {peer.ip}:{peer.port}")
                
                except socket.timeout:
                    continue
                except Exception as e:
                    logger.debug(f"[AUTO_DISCOVERY] Listener error: {e}")
        
        except Exception as e:
            logger.error(f"[AUTO_DISCOVERY] Failed to start UDP listener: {e}")
        finally:
            try:
                sock.close()
            except:
                pass
    
    def _discovery_loop(self):
        """Discovery loop - broadcasts or announces"""
        while self.running:
            try:
                if self.is_master:
                    # Master: Announce ourselves via UDP broadcast
                    self._broadcast_master_announcement()
                else:
                    # Peer: Broadcast discovery request
                    self._broadcast_discovery_request()
                    
                    # Check if master is still available
                    self._check_master_availability()
                
                time.sleep(DISCOVERY_INTERVAL)
            
            except Exception as e:
                logger.error(f"[AUTO_DISCOVERY] Discovery loop error: {e}")
                time.sleep(DISCOVERY_INTERVAL)
    
    def _broadcast_master_announcement(self):
        """Broadcast master announcement"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            
            announcement = {
                'type': 'master_announce',
                'node_id': self.node_id,
                'ip': self.local_ip,
                'port': self.fabric_port,
                'platform': self.platform,
                'capabilities': ['sync', 'file_transfer', 'discovery']
            }
            
            sock.sendto(
                json.dumps(announcement).encode(),
                (self.broadcast_addr, DISCOVERY_PORT)
            )
            sock.close()
            
            logger.debug(f"[AUTO_DISCOVERY] Broadcast master announcement to {self.broadcast_addr}")
        
        except Exception as e:
            logger.debug(f"[AUTO_DISCOVERY] Broadcast error: {e}")
    
    def _broadcast_discovery_request(self):
        """Broadcast discovery request"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.settimeout(0.5)  # Short timeout for responses
            
            request = {
                'type': 'discovery_request',
                'node_id': self.node_id,
                'ip': self.local_ip,
                'port': self.fabric_port,
                'platform': self.platform
            }
            
            sock.sendto(
                json.dumps(request).encode(),
                (self.broadcast_addr, DISCOVERY_PORT)
            )
            
            # Listen for responses briefly
            start_time = time.time()
            while time.time() - start_time < 0.5:
                try:
                    data, addr = sock.recvfrom(1024)
                    response = json.loads(data.decode('utf-8'))
                    
                    if response.get('type') == 'discovery_response':
                        peer_id = response.get('node_id')
                        if peer_id != self.node_id:
                            peer = DiscoveredPeer(
                                node_id=peer_id,
                                ip=response.get('ip'),
                                port=response.get('port'),
                                platform=response.get('platform', 'unknown'),
                                is_master=response.get('is_master', False),
                                last_seen=time.time(),
                                capabilities=response.get('capabilities', [])
                            )
                            
                            self.discovered_peers[peer_id] = peer
                            
                            if peer.is_master:
                                self.master_peer = peer
                                if self.standalone_mode:
                                    self.standalone_mode = False
                                    logger.info("[AUTO_DISCOVERY] Master discovered, exiting standalone mode")
                                    if self.on_standalone_exited:
                                        self.on_standalone_exited(peer)
                            
                            if self.on_peer_discovered:
                                self.on_peer_discovered(peer)
                
                except socket.timeout:
                    break
                except:
                    continue
            
            sock.close()
        
        except Exception as e:
            logger.debug(f"[AUTO_DISCOVERY] Discovery request error: {e}")
    
    def _check_master_availability(self):
        """Check if master is still available, enter standalone if not"""
        if self.is_master:
            return  # Master doesn't need to check
        
        if not self.master_peer:
            # No master known - enter standalone if threshold exceeded
            if not self.standalone_mode:
                # Check if we've been without master for threshold
                # For now, enter standalone immediately if no master
                self.standalone_mode = True
                logger.info("[AUTO_DISCOVERY] No master available - entering standalone mode")
                if self.on_standalone_entered:
                    self.on_standalone_entered()
            return
        
        # Check if master is stale
        time_since_seen = time.time() - self.master_peer.last_seen
        
        if time_since_seen > MASTER_TIMEOUT:
            # Master hasn't been seen - consider it offline
            if not self.standalone_mode:
                self.standalone_mode = True
                logger.warning(f"[AUTO_DISCOVERY] Master {self.master_peer.node_id[:12]}... not seen for {time_since_seen:.0f}s - entering standalone mode")
                if self.on_standalone_entered:
                    self.on_standalone_entered()
            
            # Clear stale master
            if self.master_peer.node_id in self.discovered_peers:
                del self.discovered_peers[self.master_peer.node_id]
            self.master_peer = None
        else:
            # Master is still available - update last_seen if we just discovered it
            self.master_peer.last_seen = time.time()
    
    def get_discovered_peers(self) -> List[DiscoveredPeer]:
        """Get list of discovered peers"""
        # Remove stale peers
        current_time = time.time()
        stale_peers = [
            peer_id for peer_id, peer in self.discovered_peers.items()
            if current_time - peer.last_seen > MASTER_TIMEOUT * 2
        ]
        for peer_id in stale_peers:
            del self.discovered_peers[peer_id]
        
        return list(self.discovered_peers.values())
    
    def get_master(self) -> Optional[DiscoveredPeer]:
        """Get current master peer"""
        return self.master_peer
    
    def is_standalone(self) -> bool:
        """Check if in standalone mode"""
        return self.standalone_mode


# Export
__all__ = ['AutoDiscovery', 'DiscoveredPeer', 'DISCOVERY_PORT']
