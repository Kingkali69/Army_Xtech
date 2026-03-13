#!/usr/bin/env python3
"""
GHOSTNET MESH — Global P2P Network Fabric
Every node is a router, repeater, and edge compute unit
No central server. Pure mesh. Mathematical resilience.
"""

import socket
import json
import time
import random
import hashlib
import threading
from typing import Dict, List, Set, Optional
from dataclasses import dataclass, field
from enum import Enum
from collections import deque

MESH_PORT = 7777
GOSSIP_INTERVAL = 5
MAX_PEERS = 50
HEARTBEAT_TIMEOUT = 30

class NodeRole(Enum):
    ROUTER = "router"
    REPEATER = "repeater"
    EDGE = "edge"
    HUB = "hub"
    SENSOR = "sensor"

class OSType(Enum):
    LINUX = "linux"
    WINDOWS = "windows"
    ANDROID = "android"
    MACOS = "macos"
    BSD = "bsd"
    UNKNOWN = "unknown"

@dataclass
class MeshPeer:
    node_id: str
    ip: str
    port: int
    os_type: OSType
    role: NodeRole
    swarm_id: str
    last_seen: float
    latency: float = 0.0
    reputation: float = 1.0
    is_leader: bool = False

@dataclass
class GossipMessage:
    msg_id: str
    msg_type: str
    origin: str
    payload: dict
    ttl: int = 10
    timestamp: float = field(default_factory=time.time)
    signature: str = ""

class GhostNetMesh:
    def __init__(self, node_id: str = None):
        self.node_id = node_id or self._generate_node_id()
        self.ip = self._get_local_ip()
        self.port = MESH_PORT
        self.os_type = self._detect_os()
        self.role = NodeRole.ROUTER
        self.swarm_id = "swarm_default"
        
        self.peers: Dict[str, MeshPeer] = {}
        self.seen_messages: Set[str] = set()
        self.message_queue: deque = deque(maxlen=10000)
        self.pending_sync: List[dict] = []
        
        self.is_leader = False
        self.leader_id: Optional[str] = None
        
        self.stats = {
            "messages_sent": 0,
            "messages_received": 0,
            "messages_relayed": 0,
            "peers_discovered": 0,
            "syncs_completed": 0,
        }
        
        self.running = False
        self.listeners: List[callable] = []
    
    def _generate_node_id(self) -> str:
        seed = f"{socket.gethostname()}{time.time()}{random.random()}"
        return f"ghost_{hashlib.sha256(seed.encode()).hexdigest()[:16]}"
    
    def _get_local_ip(self) -> str:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"
    
    def _detect_os(self) -> OSType:
        import platform
        system = platform.system().lower()
        if "linux" in system:
            if "android" in platform.platform().lower():
                return OSType.ANDROID
            return OSType.LINUX
        elif "windows" in system:
            return OSType.WINDOWS
        elif "darwin" in system:
            return OSType.MACOS
        elif "bsd" in system:
            return OSType.BSD
        return OSType.UNKNOWN
    
    def start(self):
        self.running = True
        threading.Thread(target=self._listen_loop, daemon=True).start()
        threading.Thread(target=self._gossip_loop, daemon=True).start()
        threading.Thread(target=self._heartbeat_loop, daemon=True).start()
        threading.Thread(target=self._leader_election_loop, daemon=True).start()
        print(f"[GHOSTNET] Node {self.node_id[:12]} online at {self.ip}:{self.port}")
    
    def stop(self):
        self.running = False
    
    def _listen_loop(self):
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            srv.bind(("0.0.0.0", self.port))
            srv.listen(100)
            srv.settimeout(1)
            
            while self.running:
                try:
                    conn, addr = srv.accept()
                    threading.Thread(target=self._handle_connection, args=(conn, addr), daemon=True).start()
                except socket.timeout:
                    continue
        except Exception as e:
            print(f"[GHOSTNET] Listen error: {e}")
        finally:
            srv.close()
    
    def _handle_connection(self, conn: socket.socket, addr):
        try:
            data = conn.recv(65535).decode()
            if data:
                msg = json.loads(data)
                self._process_message(msg, addr[0])
                self.stats["messages_received"] += 1
        except:
            pass
        finally:
            conn.close()
    
    def _process_message(self, msg: dict, sender_ip: str):
        msg_id = msg.get("msg_id", "")
        
        if msg_id in self.seen_messages:
            return
        self.seen_messages.add(msg_id)
        
        if len(self.seen_messages) > 50000:
            self.seen_messages = set(list(self.seen_messages)[-25000:])
        
        msg_type = msg.get("msg_type", "")
        
        if msg_type == "announce":
            self._handle_announce(msg, sender_ip)
        elif msg_type == "gossip":
            self._handle_gossip(msg)
        elif msg_type == "sync":
            self._handle_sync(msg)
        elif msg_type == "heartbeat":
            self._handle_heartbeat(msg, sender_ip)
        elif msg_type == "leader_vote":
            self._handle_leader_vote(msg)
        elif msg_type == "quarantine":
            self._handle_quarantine(msg)
        elif msg_type == "update":
            self._handle_update(msg)
        
        for listener in self.listeners:
            try:
                listener(msg_type, msg)
            except:
                pass
        
        if msg.get("ttl", 0) > 0:
            self._relay_message(msg)
    
    def _handle_announce(self, msg: dict, sender_ip: str):
        payload = msg.get("payload", {})
        node_id = payload.get("node_id")
        
        if node_id and node_id != self.node_id:
            peer = MeshPeer(
                node_id=node_id,
                ip=sender_ip,
                port=payload.get("port", MESH_PORT),
                os_type=OSType(payload.get("os_type", "unknown")),
                role=NodeRole(payload.get("role", "router")),
                swarm_id=payload.get("swarm_id", "default"),
                last_seen=time.time()
            )
            
            if node_id not in self.peers:
                self.stats["peers_discovered"] += 1
            
            self.peers[node_id] = peer
    
    def _handle_gossip(self, msg: dict):
        payload = msg.get("payload", {})
        gossip_type = payload.get("type")
        
        if gossip_type == "threat":
            self._process_threat_intel(payload)
        elif gossip_type == "config":
            self._process_config_update(payload)
        elif gossip_type == "flag":
            self._process_flag_broadcast(payload)
    
    def _handle_sync(self, msg: dict):
        self.stats["syncs_completed"] += 1
    
    def _handle_heartbeat(self, msg: dict, sender_ip: str):
        node_id = msg.get("origin")
        if node_id in self.peers:
            self.peers[node_id].last_seen = time.time()
    
    def _handle_leader_vote(self, msg: dict):
        payload = msg.get("payload", {})
        candidate = payload.get("candidate")
        votes = payload.get("votes", 0)
        
        if votes > len(self.peers) // 2:
            self.leader_id = candidate
            if candidate == self.node_id:
                self.is_leader = True
    
    def _handle_quarantine(self, msg: dict):
        payload = msg.get("payload", {})
        target_node = payload.get("target")
        
        if target_node in self.peers:
            del self.peers[target_node]
    
    def _handle_update(self, msg: dict):
        pass
    
    def _process_threat_intel(self, payload: dict):
        pass
    
    def _process_config_update(self, payload: dict):
        pass
    
    def _process_flag_broadcast(self, payload: dict):
        pass
    
    def _relay_message(self, msg: dict):
        msg["ttl"] = msg.get("ttl", 10) - 1
        if msg["ttl"] <= 0:
            return
        
        for peer in random.sample(list(self.peers.values()), min(5, len(self.peers))):
            self._send_to_peer(peer, msg)
        
        self.stats["messages_relayed"] += 1
    
    def _send_to_peer(self, peer: MeshPeer, msg: dict) -> bool:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(5)
            s.connect((peer.ip, peer.port))
            s.sendall(json.dumps(msg).encode())
            s.close()
            self.stats["messages_sent"] += 1
            return True
        except:
            return False
    
    def _gossip_loop(self):
        while self.running:
            self._send_announce()
            time.sleep(GOSSIP_INTERVAL)
    
    def _send_announce(self):
        msg = {
            "msg_id": f"ann_{self.node_id}_{int(time.time())}",
            "msg_type": "announce",
            "origin": self.node_id,
            "payload": {
                "node_id": self.node_id,
                "ip": self.ip,
                "port": self.port,
                "os_type": self.os_type.value,
                "role": self.role.value,
                "swarm_id": self.swarm_id
            },
            "ttl": 3,
            "timestamp": time.time()
        }
        
        for peer in list(self.peers.values()):
            self._send_to_peer(peer, msg)
    
    def _heartbeat_loop(self):
        while self.running:
            now = time.time()
            dead_peers = [
                pid for pid, peer in self.peers.items()
                if now - peer.last_seen > HEARTBEAT_TIMEOUT
            ]
            
            for pid in dead_peers:
                del self.peers[pid]
            
            time.sleep(10)
    
    def _leader_election_loop(self):
        while self.running:
            if not self.leader_id or self.leader_id not in self.peers:
                self._initiate_election()
            time.sleep(30)
    
    def _initiate_election(self):
        candidates = [self.node_id] + list(self.peers.keys())
        candidates.sort()
        
        if candidates:
            self.leader_id = candidates[0]
            self.is_leader = (self.leader_id == self.node_id)
    
    def broadcast(self, msg_type: str, payload: dict, ttl: int = 5):
        msg = {
            "msg_id": f"{msg_type}_{self.node_id}_{int(time.time()*1000)}",
            "msg_type": msg_type,
            "origin": self.node_id,
            "payload": payload,
            "ttl": ttl,
            "timestamp": time.time()
        }
        
        for peer in self.peers.values():
            self._send_to_peer(peer, msg)
    
    def broadcast_threat(self, threat_data: dict):
        self.broadcast("gossip", {"type": "threat", **threat_data})
    
    def broadcast_update(self, update_data: dict):
        self.broadcast("update", update_data)
    
    def quarantine_node(self, target_node: str, reason: str):
        if self.is_leader:
            self.broadcast("quarantine", {"target": target_node, "reason": reason})
    
    def join_peer(self, ip: str, port: int = MESH_PORT):
        msg = {
            "msg_id": f"join_{self.node_id}_{int(time.time())}",
            "msg_type": "announce",
            "origin": self.node_id,
            "payload": {
                "node_id": self.node_id,
                "ip": self.ip,
                "port": self.port,
                "os_type": self.os_type.value,
                "role": self.role.value,
                "swarm_id": self.swarm_id
            },
            "ttl": 1,
            "timestamp": time.time()
        }
        
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(5)
            s.connect((ip, port))
            s.sendall(json.dumps(msg).encode())
            s.close()
            return True
        except:
            return False
    
    def get_status(self) -> dict:
        return {
            "node_id": self.node_id,
            "ip": self.ip,
            "port": self.port,
            "os_type": self.os_type.value,
            "role": self.role.value,
            "swarm_id": self.swarm_id,
            "is_leader": self.is_leader,
            "leader_id": self.leader_id,
            "peers": len(self.peers),
            "stats": self.stats
        }

mesh = GhostNetMesh()

def get_mesh() -> GhostNetMesh:
    return mesh

if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║                    GHOSTNET MESH                                     ║
║          Global P2P Network Fabric — Level 9                         ║
║                                                                      ║
║   "Every node is a router. Every device is Ghost Nation."            ║
╚══════════════════════════════════════════════════════════════════════╝
""")
    
    m = get_mesh()
    m.start()
    
    print(f"\n[STATUS]")
    status = m.get_status()
    for k, v in status.items():
        print(f"  {k}: {v}")
    
    print(f"\n[MESH ACTIVE] Listening for peers...")

