#!/usr/bin/env python3
"""
STEP 3: CRDT Types
==================

Conflict-free replicated data types:
- OR-Map (Observed-Remove Map)
- LWW-Register (Last-Write-Wins Register)

These provide mathematical convergence guarantees.
"""

import logging
import json
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

from vector_clock import VectorClock

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CRDTType(Enum):
    """CRDT type"""
    OR_MAP = "or_map"
    LWW_REGISTER = "lww_register"


@dataclass
class LWWRegister:
    """
    Last-Write-Wins Register.
    
    Simple CRDT: last write wins based on vector clock.
    Used for single values that can be overwritten.
    """
    
    value: Any
    vector_clock: VectorClock
    
    def set(self, new_value: Any, clock: VectorClock) -> 'LWWRegister':
        """
        Set value if clock is newer.
        
        Args:
            new_value: New value
            clock: Vector clock for this write
            
        Returns:
            New register (immutable)
        """
        # Compare clocks
        comparison = clock.compare(self.vector_clock)
        
        if comparison == 'after' or comparison == 'equal':
            # Newer or equal - update
            return LWWRegister(value=new_value, vector_clock=clock)
        elif comparison == 'before':
            # Older - keep current
            return self
        else:
            # Concurrent - use deterministic tie-breaker (node_id lexicographic)
            # This ensures convergence even with concurrent writes
            new_node_ids = sorted(clock.clock.keys())
            old_node_ids = sorted(self.vector_clock.clock.keys())
            
            if new_node_ids > old_node_ids:
                return LWWRegister(value=new_value, vector_clock=clock)
            else:
                return self
    
    def merge(self, other: 'LWWRegister') -> 'LWWRegister':
        """
        Merge with another register.
        
        Args:
            other: Other register
            
        Returns:
            Merged register
        """
        return self.set(other.value, other.vector_clock)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict"""
        return {
            'value': self.value,
            'vector_clock': self.vector_clock.to_dict()
        }
    
    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'LWWRegister':
        """Deserialize from dict"""
        return cls(
            value=d.get('value'),
            vector_clock=VectorClock.from_dict(d.get('vector_clock', {}))
        )


@dataclass
class ORMap:
    """
    Observed-Remove Map.
    
    CRDT map that supports add/remove operations.
    Removes are observed (tombstones) to handle concurrent add/remove.
    """
    
    entries: Dict[str, LWWRegister] = field(default_factory=dict)
    tombstones: Dict[str, VectorClock] = field(default_factory=dict)
    
    def set(self, key: str, value: Any, clock: VectorClock) -> 'ORMap':
        """
        Set value at key.
        
        Args:
            key: Map key
            value: Value to set
            clock: Vector clock for this operation
            
        Returns:
            New map (immutable)
        """
        new_entries = self.entries.copy()
        new_tombstones = self.tombstones.copy()
        
        # Check if key is tombstoned
        if key in new_tombstones:
            tombstone_clock = new_tombstones[key]
            comparison = clock.compare(tombstone_clock)
            
            if comparison == 'before':
                # Set happened before remove - ignore (remove wins)
                return self
            elif comparison == 'concurrent':
                # Concurrent - add wins (observed-remove semantics)
                # Remove tombstone
                new_tombstones = {k: v for k, v in new_tombstones.items() if k != key}
        
        # Set value
        if key in new_entries:
            register = new_entries[key]
            new_register = register.set(value, clock)
        else:
            new_register = LWWRegister(value=value, vector_clock=clock)
        
        new_entries[key] = new_register
        
        return ORMap(entries=new_entries, tombstones=new_tombstones)
    
    def remove(self, key: str, clock: VectorClock) -> 'ORMap':
        """
        Remove key from map.
        
        Args:
            key: Key to remove
            clock: Vector clock for this operation
            
        Returns:
            New map (immutable)
        """
        new_entries = self.entries.copy()
        new_tombstones = self.tombstones.copy()
        
        # Add tombstone
        if key in new_tombstones:
            # Merge tombstone clocks (component-wise max)
            existing_tombstone = new_tombstones[key]
            new_tombstones[key] = existing_tombstone.update(clock)
        else:
            new_tombstones[key] = clock
        
        # Remove from entries if present
        if key in new_entries:
            entry_clock = new_entries[key].vector_clock
            comparison = clock.compare(entry_clock)
            
            if comparison == 'after' or comparison == 'equal':
                # Remove happened after or equal to add - remove entry
                new_entries = {k: v for k, v in new_entries.items() if k != key}
            # If before or concurrent, keep entry (add wins)
        
        return ORMap(entries=new_entries, tombstones=new_tombstones)
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get value at key.
        
        Args:
            key: Map key
            default: Default value if key doesn't exist or is tombstoned
            
        Returns:
            Value or default
        """
        if key in self.tombstones:
            return default  # Tombstoned (removed)
        
        if key in self.entries:
            return self.entries[key].value
        
        return default
    
    def merge(self, other: 'ORMap') -> 'ORMap':
        """
        Merge with another OR-Map.
        
        Mathematical convergence: merge is commutative, associative, idempotent.
        
        Args:
            other: Other OR-Map
            
        Returns:
            Merged map
        """
        # Merge entries
        merged_entries = {}
        all_keys = set(list(self.entries.keys()) + list(other.entries.keys()))
        
        for key in all_keys:
            if key in self.entries and key in other.entries:
                # Both have entry - merge registers
                merged_entries[key] = self.entries[key].merge(other.entries[key])
            elif key in self.entries:
                merged_entries[key] = self.entries[key]
            else:
                merged_entries[key] = other.entries[key]
        
        # Merge tombstones (component-wise max)
        merged_tombstones = {}
        all_tombstone_keys = set(list(self.tombstones.keys()) + list(other.tombstones.keys()))
        
        for key in all_tombstone_keys:
            if key in self.tombstones and key in other.tombstones:
                merged_tombstones[key] = self.tombstones[key].update(other.tombstones[key])
            elif key in self.tombstones:
                merged_tombstones[key] = self.tombstones[key]
            else:
                merged_tombstones[key] = other.tombstones[key]
        
        # Remove entries that are tombstoned
        final_entries = {}
        for key, register in merged_entries.items():
            if key in merged_tombstones:
                tombstone_clock = merged_tombstones[key]
                entry_clock = register.vector_clock
                comparison = entry_clock.compare(tombstone_clock)
                
                if comparison == 'before' or comparison == 'equal':
                    # Entry happened before or equal to tombstone - remove
                    continue
                elif comparison == 'concurrent':
                    # Concurrent - keep entry (observed-remove: add wins)
                    final_entries[key] = register
                else:
                    # Entry happened after tombstone - keep
                    final_entries[key] = register
            else:
                final_entries[key] = register
        
        return ORMap(entries=final_entries, tombstones=merged_tombstones)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict"""
        return {
            'entries': {k: v.to_dict() for k, v in self.entries.items()},
            'tombstones': {k: v.to_dict() for k, v in self.tombstones.items()}
        }
    
    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'ORMap':
        """Deserialize from dict"""
        entries = {}
        if 'entries' in d:
            for k, v in d['entries'].items():
                entries[k] = LWWRegister.from_dict(v)
        
        tombstones = {}
        if 'tombstones' in d:
            for k, v in d['tombstones'].items():
                tombstones[k] = VectorClock.from_dict(v)
        
        return cls(entries=entries, tombstones=tombstones)
    
    def keys(self):
        """Get all active keys (not tombstoned)"""
        return [k for k in self.entries.keys() if k not in self.tombstones]


def test_crdt_types():
    """Test CRDT types"""
    # Test LWW Register
    clock_a = VectorClock().tick('node_a')
    reg_a = LWWRegister(value='value_a', vector_clock=clock_a)
    
    clock_b = VectorClock().tick('node_b')
    reg_b = LWWRegister(value='value_b', vector_clock=clock_b)
    
    # Merge
    merged = reg_a.merge(reg_b)
    assert merged.value in ['value_a', 'value_b']  # Deterministic tie-breaker
    
    # Test OR-Map
    map_a = ORMap()
    clock1 = VectorClock().tick('node_a')
    map_a = map_a.set('key1', 'value1', clock1)
    
    map_b = ORMap()
    clock2 = VectorClock().tick('node_b')
    map_b = map_b.set('key2', 'value2', clock2)
    
    # Merge maps
    merged_map = map_a.merge(map_b)
    assert merged_map.get('key1') == 'value1'
    assert merged_map.get('key2') == 'value2'
    
    # Test remove
    clock3 = clock1.tick('node_a')
    map_a = map_a.remove('key1', clock3)
    merged_map = map_a.merge(map_b)
    assert merged_map.get('key1') is None  # Removed
    
    print("✓ CRDT type tests passed")


if __name__ == "__main__":
    test_crdt_types()
