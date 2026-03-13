#!/usr/bin/env python3
"""
STEP 3: CRDT Merge Engine
=========================

Mathematical convergence guarantee.
Merges ops from multiple nodes deterministically.

This is the core of conflict-free replication.
"""

import sys
import os
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

# Add paths
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'step_1_state_store'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'step_2_state_model'))

from vector_clock import VectorClock
from crdt_types import ORMap, LWWRegister, CRDTType

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CRDTMergeEngine:
    """
    CRDT merge engine.
    
    Provides mathematical convergence guarantee:
    - Commutative: merge(A, B) == merge(B, A)
    - Associative: merge(merge(A, B), C) == merge(A, merge(B, C))
    - Idempotent: merge(A, A) == A
    
    This ensures all nodes converge to the same state.
    """
    
    def __init__(self, node_id: str):
        """
        Initialize merge engine.
        
        Args:
            node_id: This node's ID
        """
        self.node_id = node_id
        self.local_clock = VectorClock()
        
        # CRDT state (OR-Map of keys to values)
        self.state: Dict[str, ORMap] = {}
        
        logger.info(f"[CRDT_MERGE] Initialized for node {node_id[:12]}...")
    
    def get_clock(self) -> VectorClock:
        """Get current local vector clock"""
        return self.local_clock
    
    def tick(self) -> VectorClock:
        """
        Increment local clock.
        
        Returns:
            New clock after tick
        """
        self.local_clock = self.local_clock.tick(self.node_id)
        return self.local_clock
    
    def apply_op(self, key: str, value: Any, op_type: str, clock: VectorClock) -> bool:
        """
        Apply operation to CRDT state.
        
        Args:
            key: State key (dot-notation, e.g., "nodes.node_a")
            value: Value to set/merge
            op_type: Operation type ("set", "delete", "merge")
            clock: Vector clock for this operation
            
        Returns:
            True if applied, False if rejected
        """
        # Update local clock with received clock
        self.local_clock = self.local_clock.update(clock)
        
        # Parse key path
        parts = key.split('.')
        if len(parts) == 0:
            return False
        
        # Get or create OR-Map for this key path
        map_key = parts[0]  # Top-level key
        if map_key not in self.state:
            self.state[map_key] = ORMap()
        
        or_map = self.state[map_key]
        
        if op_type == "set":
            # Set value (creates LWW-Register)
            if len(parts) == 1:
                # Top-level key
                or_map = or_map.set(key, value, clock)
            else:
                # Nested key - set in nested structure
                # For now, treat as single key-value
                or_map = or_map.set(key, value, clock)
        
        elif op_type == "delete":
            # Remove key
            or_map = or_map.remove(key, clock)
        
        elif op_type == "merge":
            # Merge value (for nested structures)
            # This would merge nested OR-Maps
            # For now, treat as set
            or_map = or_map.set(key, value, clock)
        
        else:
            logger.warning(f"[CRDT_MERGE] Unknown op type: {op_type}")
            return False
        
        self.state[map_key] = or_map
        logger.debug(f"[CRDT_MERGE] Applied op: {op_type} {key} @ {clock}")
        return True
    
    def merge_state(self, other_state: Dict[str, ORMap], other_clock: VectorClock) -> Dict[str, ORMap]:
        """
        Merge state from another node.
        
        Mathematical convergence: commutative, associative, idempotent.
        
        Args:
            other_state: State from other node
            other_clock: Vector clock from other node
            
        Returns:
            Merged state
        """
        # Update local clock
        self.local_clock = self.local_clock.update(other_clock)
        
        # Merge all OR-Maps
        merged_state = {}
        all_keys = set(list(self.state.keys()) + list(other_state.keys()))
        
        for key in all_keys:
            if key in self.state and key in other_state:
                # Both have this key - merge OR-Maps
                merged_state[key] = self.state[key].merge(other_state[key])
            elif key in self.state:
                merged_state[key] = self.state[key]
            else:
                merged_state[key] = other_state[key]
        
        self.state = merged_state
        logger.debug(f"[CRDT_MERGE] Merged state from {len(other_state)} keys")
        return merged_state
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get value from CRDT state.
        
        Args:
            key: State key
            default: Default value if not found
            
        Returns:
            Value or default
        """
        parts = key.split('.')
        if len(parts) == 0:
            return default
        
        map_key = parts[0]
        if map_key not in self.state:
            return default
        
        or_map = self.state[map_key]
        return or_map.get(key, default)
    
    def get_all(self) -> Dict[str, Any]:
        """
        Get all state as flat dict.
        
        Returns:
            Dictionary of all key-value pairs
        """
        result = {}
        for map_key, or_map in self.state.items():
            for key in or_map.keys():
                result[key] = or_map.get(key)
        return result
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize state to dict"""
        return {
            'node_id': self.node_id,
            'clock': self.local_clock.to_dict(),
            'state': {k: v.to_dict() for k, v in self.state.items()}
        }
    
    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'CRDTMergeEngine':
        """Deserialize from dict"""
        engine = cls(node_id=d.get('node_id', 'unknown'))
        engine.local_clock = VectorClock.from_dict(d.get('clock', {}))
        engine.state = {
            k: ORMap.from_dict(v) for k, v in d.get('state', {}).items()
        }
        return engine


def test_merge_engine():
    """Test merge engine"""
    # Node A
    engine_a = CRDTMergeEngine('node_a')
    clock_a = engine_a.tick()
    engine_a.apply_op('test.key1', 'value1', 'set', clock_a)
    
    # Node B
    engine_b = CRDTMergeEngine('node_b')
    clock_b = engine_b.tick()
    engine_b.apply_op('test.key2', 'value2', 'set', clock_b)
    
    # Merge
    engine_a.merge_state(engine_b.state, engine_b.get_clock())
    
    assert engine_a.get('test.key1') == 'value1'
    assert engine_a.get('test.key2') == 'value2'
    
    print("✓ Merge engine tests passed")


if __name__ == "__main__":
    test_merge_engine()
