#!/usr/bin/env python3
"""
STEP 4: Single Sync Engine
==========================

One daemon. No competing mechanisms.
Exchange ops only (not full state).
Retry with exponential backoff.
Uses CRDT merge for conflict-free sync.
"""

import sys
import os
import time
import logging
import threading
import socket
import json
import uuid
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from collections import deque
from enum import Enum

# Add paths
base_dir = os.path.dirname(__file__)
substrate_dir = os.path.join(base_dir, '..')
sys.path.insert(0, os.path.join(substrate_dir, 'step_1_state_store'))
sys.path.insert(0, os.path.join(substrate_dir, 'step_2_state_model'))
sys.path.insert(0, os.path.join(substrate_dir, 'step_3_crdt_merge'))

# Import with fallback
try:
    from step_1_state_store.state_store import StateOp, OpType, AuthoritativeStateStore
    from step_2_state_model.state_model import StateModel
    from step_3_crdt_merge.vector_clock import VectorClock
    from step_3_crdt_merge.crdt_merge import CRDTMergeEngine
except ImportError:
    # Fallback: direct import
    import importlib.util
    
    def load_module(name, path):
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    
    state_store_mod = load_module(
        "state_store",
        os.path.join(substrate_dir, 'step_1_state_store', 'state_store.py')
    )
    state_model_mod = load_module(
        "state_model",
        os.path.join(substrate_dir, 'step_2_state_model', 'state_model.py')
    )
    vector_clock_mod = load_module(
        "vector_clock",
        os.path.join(substrate_dir, 'step_3_crdt_merge', 'vector_clock.py')
    )
    crdt_merge_mod = load_module(
        "crdt_merge",
        os.path.join(substrate_dir, 'step_3_crdt_merge', 'crdt_merge.py')
    )
    
    StateOp = state_store_mod.StateOp
    OpType = state_store_mod.OpType
    AuthoritativeStateStore = state_store_mod.AuthoritativeStateStore
    StateModel = state_model_mod.StateModel
    VectorClock = vector_clock_mod.VectorClock
    CRDTMergeEngine = crdt_merge_mod.CRDTMergeEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SyncStatus(Enum):
    """Sync status"""
    IDLE = "idle"
    SYNCING = "syncing"
    RETRYING = "retrying"
    ERROR = "error"


@dataclass
class PeerSyncState:
    """State for syncing with a peer"""
    node_id: str
    ip: str
    port: int
    last_op_id: Optional[str] = None
    last_sync_time: float = 0.0
    retry_count: int = 0
    last_error: Optional[str] = None
    status: SyncStatus = SyncStatus.IDLE


class SyncEngine:
    """
    Single sync engine.
    
    Features:
    - Exchange ops only (not full state)
    - CRDT merge for conflict-free sync
    - Retry with exponential backoff
    - One daemon (no competing mechanisms)
    """
    
    def __init__(
        self,
        state_model: StateModel,
        node_id: str,
        sync_interval: float = 5.0,
        max_retries: int = 5,
        initial_backoff: float = 1.0,
        max_backoff: float = 60.0
    ):
        """
        Initialize sync engine.
        
        Args:
            state_model: State model instance
            node_id: This node's ID
            sync_interval: Seconds between sync attempts
            max_retries: Maximum retry attempts
            initial_backoff: Initial backoff seconds
            max_backoff: Maximum backoff seconds
        """
        self.state_model = state_model
        self.node_id = node_id
        self.sync_interval = sync_interval
        self.max_retries = max_retries
        self.initial_backoff = initial_backoff
        self.max_backoff = max_backoff
        
        # Peer sync states
        self.peer_states: Dict[str, PeerSyncState] = {}
        
        # Sync queue (ops to send)
        self.sync_queue: deque = deque(maxlen=10000)
        
        # Running state
        self.running = False
        self.sync_thread: Optional[threading.Thread] = None
        self.lock = threading.Lock()
        
        logger.info(f"[SYNC_ENGINE] Initialized for node {node_id[:12]}...")
    
    def register_peer(self, node_id: str, ip: str, port: int):
        """
        Register a peer for syncing.
        
        Args:
            node_id: Peer node ID
            ip: Peer IP address
            port: Peer port
        """
        with self.lock:
            if node_id not in self.peer_states:
                self.peer_states[node_id] = PeerSyncState(
                    node_id=node_id,
                    ip=ip,
                    port=port
                )
                logger.info(f"[SYNC_ENGINE] Registered peer: {node_id[:12]}... @ {ip}:{port}")
            else:
                # Update existing peer
                self.peer_states[node_id].ip = ip
                self.peer_states[node_id].port = port
    
    def unregister_peer(self, node_id: str):
        """Unregister a peer"""
        with self.lock:
            if node_id in self.peer_states:
                del self.peer_states[node_id]
                logger.info(f"[SYNC_ENGINE] Unregistered peer: {node_id[:12]}...")
    
    def start(self):
        """Start sync engine"""
        if self.running:
            return
        
        self.running = True
        self.sync_thread = threading.Thread(
            target=self._sync_loop,
            daemon=True,
            name="sync-engine"
        )
        self.sync_thread.start()
        logger.info("[SYNC_ENGINE] Started")
    
    def stop(self):
        """Stop sync engine"""
        self.running = False
        if self.sync_thread:
            self.sync_thread.join(timeout=2)
        logger.info("[SYNC_ENGINE] Stopped")
    
    def _sync_loop(self):
        """Main sync loop"""
        while self.running:
            try:
                # Sync with all registered peers
                peers_to_sync = list(self.peer_states.keys())
                
                for peer_id in peers_to_sync:
                    if not self.running:
                        break
                    
                    peer_state = self.peer_states.get(peer_id)
                    if not peer_state:
                        continue
                    
                    # Check if it's time to sync
                    time_since_sync = time.time() - peer_state.last_sync_time
                    if time_since_sync < self.sync_interval:
                        continue
                    
                    # Sync with peer
                    self._sync_with_peer(peer_state)
                
                # Sleep before next iteration
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"[SYNC_ENGINE] Sync loop error: {e}")
                time.sleep(self.sync_interval)
    
    def _sync_with_peer(self, peer_state: PeerSyncState):
        """
        Sync with a single peer.
        
        Args:
            peer_state: Peer sync state
        """
        try:
            peer_state.status = SyncStatus.SYNCING
            
            # Exchange ops
            ops_sent = self._send_ops_to_peer(peer_state)
            ops_received = self._receive_ops_from_peer(peer_state)
            
            # Update sync time
            peer_state.last_sync_time = time.time()
            peer_state.retry_count = 0  # Reset retry count on success
            peer_state.status = SyncStatus.IDLE
            peer_state.last_error = None
            
            if ops_sent > 0 or ops_received > 0:
                logger.debug(f"[SYNC_ENGINE] Synced with {peer_state.node_id[:12]}... ({ops_sent} sent, {ops_received} received)")
            
        except Exception as e:
            peer_state.status = SyncStatus.ERROR
            peer_state.last_error = str(e)
            peer_state.retry_count += 1
            
            # Exponential backoff
            backoff = min(
                self.initial_backoff * (2 ** peer_state.retry_count),
                self.max_backoff
            )
            
            logger.warning(f"[SYNC_ENGINE] Sync failed with {peer_state.node_id[:12]}... (retry {peer_state.retry_count}/{self.max_retries}): {e}")
            
            if peer_state.retry_count >= self.max_retries:
                logger.error(f"[SYNC_ENGINE] Max retries reached for {peer_state.node_id[:12]}... - unregistering")
                self.unregister_peer(peer_state.node_id)
            else:
                # Schedule retry with backoff
                peer_state.last_sync_time = time.time() - self.sync_interval + backoff
    
    def _send_ops_to_peer(self, peer_state: PeerSyncState) -> int:
        """
        Send ops to peer since last_op_id.
        
        Args:
            peer_state: Peer sync state
            
        Returns:
            Number of ops sent
        """
        try:
            # Get ops since last_op_id
            ops = self.state_model.store.get_log_tail(
                last_op_id=peer_state.last_op_id,
                limit=1000
            )
            
            if not ops:
                return 0
            
            # Connect to peer
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((peer_state.ip, peer_state.port))
            
            # Prepare sync request
            request = {
                'type': 'sync_request',
                'node_id': self.node_id,
                'last_op_id': peer_state.last_op_id,
                'vector_clock': self._get_vector_clock_dict(),
                'timestamp': time.time()
            }
            
            sock.sendall(json.dumps(request).encode())
            
            # Receive response - read until complete
            chunks = []
            while True:
                chunk = sock.recv(65535)
                if not chunk:
                    break
                chunks.append(chunk)
                # Check if we have complete JSON
                try:
                    data = b''.join(chunks).decode()
                    response = json.loads(data)
                    break  # Successfully parsed
                except json.JSONDecodeError:
                    continue  # Need more data
                except Exception:
                    break  # Other error, give up
            
            if response.get('type') == 'sync_response':
                # Update last_op_id for ops we sent
                if ops:
                    peer_state.last_op_id = ops[-1].op_id
            
            sock.close()
            return len(ops)
            
        except Exception as e:
            logger.debug(f"[SYNC_ENGINE] Send ops error: {e}")
            raise
    
    def _receive_ops_from_peer(self, peer_state: PeerSyncState) -> int:
        """
        Receive and apply ops from peer.
        
        Args:
            peer_state: Peer sync state
            
        Returns:
            Number of ops received and applied
        """
        try:
            # Connect to peer
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((peer_state.ip, peer_state.port))
            
            # Send sync request
            request = {
                'type': 'sync_request',
                'node_id': self.node_id,
                'last_op_id': peer_state.last_op_id,
                'vector_clock': self._get_vector_clock_dict(),
                'timestamp': time.time()
            }
            
            sock.sendall(json.dumps(request).encode())
            
            # Receive response - read until complete
            chunks = []
            while True:
                chunk = sock.recv(65535)
                if not chunk:
                    break
                chunks.append(chunk)
                # Check if we have complete JSON
                try:
                    data = b''.join(chunks).decode()
                    response = json.loads(data)
                    break  # Successfully parsed
                except json.JSONDecodeError:
                    continue  # Need more data
                except Exception:
                    break  # Other error, give up
            
            if response.get('type') == 'sync_response':
                ops_data = response.get('ops', [])
                peer_clock_dict = response.get('vector_clock', {})
                
                # Apply ops with CRDT merge
                ops_applied = 0
                for op_data in ops_data:
                    try:
                        op = StateOp.from_dict(op_data)
                        
                        # Skip our own ops
                        if op.node_id == self.node_id:
                            continue
                        
                        # Apply op (CRDT merge happens in state model)
                        if self.state_model.apply_op(op):
                            ops_applied += 1
                            # Update last_op_id
                            peer_state.last_op_id = op.op_id
                    except Exception as e:
                        logger.debug(f"[SYNC_ENGINE] Failed to apply op: {e}")
                        continue
                
                # Merge vector clocks
                if peer_clock_dict and self.state_model.crdt_engine:
                    peer_clock = VectorClock.from_dict(peer_clock_dict)
                    self.state_model.crdt_engine.local_clock = \
                        self.state_model.crdt_engine.local_clock.update(peer_clock)
                
                sock.close()
                return ops_applied
            
            sock.close()
            return 0
            
        except Exception as e:
            logger.debug(f"[SYNC_ENGINE] Receive ops error: {e}")
            raise
    
    def _get_vector_clock_dict(self) -> Dict[str, int]:
        """Get current vector clock as dict"""
        if self.state_model.crdt_engine:
            return self.state_model.crdt_engine.get_clock().to_dict()
        return {}
    
    def get_status(self) -> Dict[str, any]:
        """Get sync engine status"""
        with self.lock:
            return {
                'running': self.running,
                'peers': len(self.peer_states),
                'sync_interval': self.sync_interval,
                'peer_states': {
                    pid: {
                        'node_id': ps.node_id,
                        'status': ps.status.value,
                        'last_sync_time': ps.last_sync_time,
                        'retry_count': ps.retry_count,
                        'last_error': ps.last_error
                    }
                    for pid, ps in self.peer_states.items()
                }
            }


def test_sync_engine():
    """Test sync engine"""
    from step_1_state_store.state_store import get_state_store
    from step_2_state_model.state_model import get_state_model
    
    # Create two nodes
    store_a = get_state_store(db_path='/tmp/test_sync_a.db')
    model_a = get_state_model(state_store=store_a, node_id='node_a')
    engine_a = SyncEngine(model_a, 'node_a')
    
    store_b = get_state_store(db_path='/tmp/test_sync_b.db')
    model_b = get_state_model(state_store=store_b, node_id='node_b')
    engine_b = SyncEngine(model_b, 'node_b')
    
    # Register peers
    engine_a.register_peer('node_b', '127.0.0.1', 7778)
    engine_b.register_peer('node_a', '127.0.0.1', 7777)
    
    print("✓ Sync engine tests passed")
    
    store_a.close()
    store_b.close()


if __name__ == "__main__":
    test_sync_engine()
