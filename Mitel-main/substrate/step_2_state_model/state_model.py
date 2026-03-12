

#!/usr/bin/env python3
"""
STEP 2: State Model (NO FILES YET)
===================================

Define single in-memory state tree.
State changes expressed only as ops.

Ops are:
- Deterministic
- Serializable
- Replayable

No direct mutation of state.
All state = apply(op)
"""

import json
import hashlib
import logging
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum

import sys
import os
# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'step_1_state_store'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'step_3_crdt_merge'))

try:
    from step_1_state_store.state_store import (
        AuthoritativeStateStore, StateOp, OpType, get_state_store
    )
except ImportError:
    # Fallback: try direct import
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "state_store",
        os.path.join(os.path.dirname(__file__), '..', 'step_1_state_store', 'state_store.py')
    )
    state_store_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(state_store_mod)
    AuthoritativeStateStore = state_store_mod.AuthoritativeStateStore
    StateOp = state_store_mod.StateOp
    OpType = state_store_mod.OpType
    get_state_store = state_store_mod.get_state_store

# CRDT imports (STEP 3)
CRDT_AVAILABLE = False
CRDTMergeEngine = None
VectorClock = None

try:
    # Try relative import first
    from step_3_crdt_merge.crdt_merge import CRDTMergeEngine
    from step_3_crdt_merge.vector_clock import VectorClock
    CRDT_AVAILABLE = True
except ImportError:
    try:
        # Try direct import with resolved path
        crdt_path = os.path.join(os.path.dirname(__file__), '..', 'step_3_crdt_merge')
        crdt_path = os.path.abspath(crdt_path)
        if crdt_path not in sys.path:
            sys.path.insert(0, crdt_path)
        from crdt_merge import CRDTMergeEngine
        from vector_clock import VectorClock
        CRDT_AVAILABLE = True
    except ImportError as e:
        CRDT_AVAILABLE = False
        CRDTMergeEngine = None
        VectorClock = None
        logger.debug(f"[STATE_MODEL] CRDT not available: {e}")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StateModel:
    """
    In-memory state tree built from ops.
    
    State changes expressed only as ops.
    No direct mutation - all changes go through apply(op).
    """
    
    def __init__(self, state_store: AuthoritativeStateStore = None, node_id: str = None):
        """
        Initialize state model
        
        Args:
            state_store: State store instance (default: singleton)
            node_id: Node ID for CRDT merge engine
        """
        self.store = state_store or get_state_store()
        
        # In-memory state tree (nested dict)
        self.state: Dict[str, Any] = {}
        
        # Track last op ID we've applied
        self.last_applied_op_id: Optional[str] = None
        
        # CRDT merge engine (STEP 3)
        self.node_id = node_id or "unknown"
        if CRDT_AVAILABLE:
            self.crdt_engine = CRDTMergeEngine(self.node_id)
            logger.info(f"[STATE_MODEL] CRDT merge engine enabled")
        else:
            self.crdt_engine = None
            logger.warning(f"[STATE_MODEL] CRDT merge engine not available")
        
        # Load state from log (replay all ops)
        self._replay_log()
        
        logger.info(f"[STATE_MODEL] Initialized - {len(self.state)} keys in state tree")
    
    def _replay_log(self):
        """
        Replay all ops from log to build state tree.
        
        If snapshot exists, load it first, then replay ops after snapshot.
        If no snapshot, replay entire log.
        """
        # TODO: Load snapshot if exists (STEP 1 has snapshot table, but restoration logic here)
        # For now, replay entire log
        
        logger.info("[STATE_MODEL] Replaying log to build state tree...")
        
        last_op_id = None
        ops_applied = 0
        
        while True:
            # Get next batch of ops
            ops = self.store.get_log_tail(last_op_id=last_op_id, limit=100)
            
            if not ops:
                break
            
            # Apply each op
            for op in ops:
                self._apply_op_internal(op)
                last_op_id = op.op_id
                ops_applied += 1
            
            # If we got fewer than limit, we're done
            if len(ops) < 100:
                break
        
        self.last_applied_op_id = last_op_id
        
        logger.info(f"[STATE_MODEL] Replay complete - applied {ops_applied} ops")
    
    def _apply_op_internal(self, op: StateOp):
        """
        Apply op to in-memory state (internal, no logging to store).
        
        This is called during replay and when applying new ops.
        Uses CRDT merge if available.
        """
        if op.op_type == OpType.SET:
            # Set value at key path
            if self.crdt_engine and op.vector_clock:
                # Use CRDT
                clock = VectorClock.from_dict(op.vector_clock) if isinstance(op.vector_clock, dict) else op.vector_clock
                if isinstance(clock, dict):
                    clock = VectorClock.from_dict(clock)
                self.crdt_engine.apply_op(op.key, op.value, 'set', clock)
                # Update state tree from CRDT
                crdt_state = self.crdt_engine.get_all()
                for k, v in crdt_state.items():
                    if k == op.key or k.startswith(op.key + '.'):
                        self._set_value(k, v)
            else:
                # Fallback to simple set
                self._set_value(op.key, op.value)
        
        elif op.op_type == OpType.DELETE:
            # Delete key
            if self.crdt_engine and op.vector_clock:
                # Use CRDT
                clock = VectorClock.from_dict(op.vector_clock) if isinstance(op.vector_clock, dict) else op.vector_clock
                if isinstance(clock, dict):
                    clock = VectorClock.from_dict(clock)
                self.crdt_engine.apply_op(op.key, None, 'delete', clock)
                # Update state tree from CRDT
                self._delete_key(op.key)
            else:
                # Fallback to simple delete
                self._delete_key(op.key)
        
        elif op.op_type == OpType.MERGE:
            # Merge value into key (CRDT merge)
            self._merge_value(op.key, op.value, op)
        
        elif op.op_type == OpType.SNAPSHOT:
            # Snapshot marker - ignore (snapshot is stored separately)
            pass
    
    def _set_value(self, key: str, value: Any):
        """
        Set value at key path (dot-notation supported).
        
        Example: "node.meta.hostname" → state["node"]["meta"]["hostname"] = value
        """
        parts = key.split('.')
        current = self.state
        
        # Navigate to parent dict
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            elif not isinstance(current[part], dict):
                # Overwrite non-dict with dict
                current[part] = {}
            current = current[part]
        
        # Set final value
        current[parts[-1]] = value
    
    def _delete_key(self, key: str):
        """
        Delete key from state tree.
        
        Example: "node.meta.hostname" → del state["node"]["meta"]["hostname"]
        """
        parts = key.split('.')
        current = self.state
        
        # Navigate to parent dict
        for part in parts[:-1]:
            if part not in current or not isinstance(current[part], dict):
                return  # Key doesn't exist
            current = current[part]
        
        # Delete final key
        if parts[-1] in current:
            del current[parts[-1]]
    
    def _merge_value(self, key: str, value: Any, op: StateOp = None):
        """
        Merge value into key using CRDT merge (STEP 3).
        
        Uses OR-Map for conflict-free merging.
        """
        if self.crdt_engine and op and op.vector_clock:
            # Use CRDT merge
            clock = VectorClock.from_dict(op.vector_clock) if isinstance(op.vector_clock, dict) else op.vector_clock
            if isinstance(clock, dict):
                clock = VectorClock.from_dict(clock)
            
            self.crdt_engine.apply_op(key, value, 'merge', clock)
            
            # Update state tree from CRDT
            crdt_state = self.crdt_engine.get_all()
            for k, v in crdt_state.items():
                self._set_value(k, v)
        else:
            # Fallback to simple set
            self._set_value(key, value)
    
    def apply_op(self, op: StateOp) -> bool:
        """
        Apply op to state (external API).
        
        This:
        1. Applies op to in-memory state (with CRDT merge if available)
        2. Logs op to store (transactional)
        
        Args:
            op: State operation to apply
            
        Returns:
            True if applied, False if failed
        """
        # Ensure vector clock is set
        if self.crdt_engine and not op.vector_clock:
            # Generate vector clock for this op
            clock = self.crdt_engine.tick()
            op.vector_clock = clock.to_dict()
        
        # Apply op to in-memory state first
        self._apply_op_internal(op)
        
        # Apply to CRDT engine if available
        if self.crdt_engine and op.vector_clock:
            clock = VectorClock.from_dict(op.vector_clock) if isinstance(op.vector_clock, dict) else op.vector_clock
            if isinstance(clock, dict):
                clock = VectorClock.from_dict(clock)
            
            if op.op_type == OpType.SET:
                self.crdt_engine.apply_op(op.key, op.value, 'set', clock)
            elif op.op_type == OpType.DELETE:
                self.crdt_engine.apply_op(op.key, None, 'delete', clock)
            elif op.op_type == OpType.MERGE:
                self.crdt_engine.apply_op(op.key, op.value, 'merge', clock)
        
        # Log op to store (transactional)
        if self.store.apply_op(op):
            self.last_applied_op_id = op.op_id
            logger.debug(f"[STATE_MODEL] Applied op: {op.op_id} ({op.op_type.value})")
            return True
        else:
            # Op failed to log - rollback in-memory state
            logger.error(f"[STATE_MODEL] Failed to log op: {op.op_id} - state may be inconsistent")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get value from state tree.
        
        Args:
            key: Key path (dot-notation supported)
            default: Default value if key doesn't exist
            
        Returns:
            Value at key, or default
        """
        parts = key.split('.')
        current = self.state
        
        # Navigate to value
        for part in parts:
            if not isinstance(current, dict) or part not in current:
                return default
            current = current[part]
        
        return current
    
    def get_state_snapshot(self) -> Dict[str, Any]:
        """
        Get complete state snapshot (for persistence).
        
        Returns:
            Complete state tree as dict
        """
        return json.loads(json.dumps(self.state))  # Deep copy
    
    def restore_from_snapshot(self, snapshot: Dict[str, Any], last_op_id: str = None):
        """
        Restore state from snapshot.
        
        Then replay ops after snapshot point if last_op_id provided.
        
        Args:
            snapshot: State snapshot dict
            last_op_id: Last op ID in snapshot (replay ops after this)
        """
        logger.info("[STATE_MODEL] Restoring from snapshot...")
        
        # Restore state
        self.state = json.loads(json.dumps(snapshot))  # Deep copy
        
        # Replay ops after snapshot
        if last_op_id:
            logger.info(f"[STATE_MODEL] Replaying ops after snapshot (last_op_id: {last_op_id})...")
            
            ops_applied = 0
            current_last_op_id = last_op_id
            
            while True:
                ops = self.store.get_log_tail(last_op_id=current_last_op_id, limit=100)
                
                if not ops:
                    break
                
                for op in ops:
                    self._apply_op_internal(op)
                    current_last_op_id = op.op_id
                    ops_applied += 1
                
                if len(ops) < 100:
                    break
            
            self.last_applied_op_id = current_last_op_id
            logger.info(f"[STATE_MODEL] Restored snapshot + {ops_applied} ops")
        else:
            self.last_applied_op_id = last_op_id
    
    def compute_state_hash(self) -> str:
        """
        Compute hash of current state (for integrity verification).
        
        Returns:
            SHA256 hash of state JSON
        """
        state_json = json.dumps(self.state, sort_keys=True)
        return hashlib.sha256(state_json.encode()).hexdigest()


# Singleton instance
_model_instance: Optional[StateModel] = None


def get_state_model(state_store: AuthoritativeStateStore = None, node_id: str = None) -> StateModel:
    """Get singleton state model instance"""
    global _model_instance
    if _model_instance is None:
        _model_instance = StateModel(state_store=state_store, node_id=node_id)
    return _model_instance


if __name__ == "__main__":
    # Test state model
    import uuid
    from step_1_state_store.state_store import StateOp, OpType
    
    test_db = f"/tmp/test_state_model_{uuid.uuid4().hex[:8]}.db"
    store = get_state_store(db_path=test_db)
    model = StateModel(state_store=store)
    
    # Test apply op
    test_op1 = StateOp(
        op_id=str(uuid.uuid4()),
        op_type=OpType.SET,
        key="test.key1",
        value="value1",
        node_id="test_node"
    )
    
    if model.apply_op(test_op1):
        print("[TEST] ✅ Apply op succeeded")
    else:
        print("[TEST] ❌ Apply op failed")
        exit(1)
    
    # Test get
    value = model.get("test.key1")
    if value == "value1":
        print(f"[TEST] ✅ Get value succeeded: {value}")
    else:
        print(f"[TEST] ❌ Get value failed: expected 'value1', got {value}")
        exit(1)
    
    # Test nested keys
    test_op2 = StateOp(
        op_id=str(uuid.uuid4()),
        op_type=OpType.SET,
        key="node.meta.hostname",
        value="linux_kali",
        node_id="test_node"
    )
    
    model.apply_op(test_op2)
    
    hostname = model.get("node.meta.hostname")
    if hostname == "linux_kali":
        print(f"[TEST] ✅ Nested key succeeded: {hostname}")
    else:
        print(f"[TEST] ❌ Nested key failed")
        exit(1)
    
    # Test state hash
    state_hash = model.compute_state_hash()
    print(f"[TEST] ✅ State hash: {state_hash[:16]}...")
    
    # Test snapshot
    snapshot = model.get_state_snapshot()
    print(f"[TEST] ✅ State snapshot: {len(snapshot)} top-level keys")
    
    store.close()
    
    # Cleanup
    import os
    if os.path.exists(test_db):
        os.remove(test_db)
    
    print("[TEST] ✅ All tests passed")
