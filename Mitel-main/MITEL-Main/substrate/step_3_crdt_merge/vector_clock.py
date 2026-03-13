#!/usr/bin/env python3
"""
STEP 3: Vector Clocks
=====================

Logical time, not wall-clock time.
Enables causal ordering and conflict detection.

Vector clock = map of node_id → logical timestamp
"""

import logging
from typing import Dict, Optional
from dataclasses import dataclass, field

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class VectorClock:
    """
    Vector clock for logical time ordering.
    
    Each node maintains a vector clock: {node_id: logical_timestamp}
    Enables causal ordering without wall-clock synchronization.
    """
    
    clock: Dict[str, int] = field(default_factory=dict)
    
    def tick(self, node_id: str) -> 'VectorClock':
        """
        Increment logical time for this node.
        
        Args:
            node_id: Node ID to increment
            
        Returns:
            New vector clock (immutable)
        """
        new_clock = self.clock.copy()
        new_clock[node_id] = new_clock.get(node_id, 0) + 1
        return VectorClock(clock=new_clock)
    
    def update(self, other: 'VectorClock') -> 'VectorClock':
        """
        Update this clock with another clock (component-wise max).
        
        Used when receiving ops from another node.
        
        Args:
            other: Other vector clock
            
        Returns:
            New vector clock (merged)
        """
        new_clock = self.clock.copy()
        for node_id, timestamp in other.clock.items():
            new_clock[node_id] = max(new_clock.get(node_id, 0), timestamp)
        return VectorClock(clock=new_clock)
    
    def happens_before(self, other: 'VectorClock') -> bool:
        """
        Check if this clock happens before other (causal ordering).
        
        Returns True if this < other (causally precedes).
        
        Args:
            other: Other vector clock
            
        Returns:
            True if this happens before other
        """
        if not self.clock:
            return True
        
        # Check if all components are <= and at least one is <
        all_leq = all(
            self.clock.get(node_id, 0) <= other.clock.get(node_id, 0)
            for node_id in set(list(self.clock.keys()) + list(other.clock.keys()))
        )
        
        at_least_one_lt = any(
            self.clock.get(node_id, 0) < other.clock.get(node_id, 0)
            for node_id in set(list(self.clock.keys()) + list(other.clock.keys()))
        )
        
        return all_leq and at_least_one_lt
    
    def happens_after(self, other: 'VectorClock') -> bool:
        """
        Check if this clock happens after other.
        
        Args:
            other: Other vector clock
            
        Returns:
            True if this happens after other
        """
        return other.happens_before(self)
    
    def concurrent(self, other: 'VectorClock') -> bool:
        """
        Check if clocks are concurrent (conflict).
        
        Neither happens before the other.
        
        Args:
            other: Other vector clock
            
        Returns:
            True if concurrent (conflict)
        """
        return not self.happens_before(other) and not other.happens_before(self)
    
    def compare(self, other: 'VectorClock') -> str:
        """
        Compare two vector clocks.
        
        Returns:
            'before', 'after', 'concurrent', or 'equal'
        """
        if self.clock == other.clock:
            return 'equal'
        elif self.happens_before(other):
            return 'before'
        elif other.happens_before(self):
            return 'after'
        else:
            return 'concurrent'
    
    def to_dict(self) -> Dict[str, int]:
        """Serialize to dict"""
        return self.clock.copy()
    
    @classmethod
    def from_dict(cls, d: Dict[str, int]) -> 'VectorClock':
        """Deserialize from dict"""
        if d is None:
            return cls()
        return cls(clock=d.copy() if isinstance(d, dict) else {})
    
    def __repr__(self):
        return f"VectorClock({self.clock})"


def test_vector_clock():
    """Test vector clock operations"""
    # Node A
    vc_a = VectorClock()
    vc_a = vc_a.tick('node_a')
    vc_a = vc_a.tick('node_a')
    assert vc_a.clock == {'node_a': 2}
    
    # Node B
    vc_b = VectorClock()
    vc_b = vc_b.tick('node_b')
    assert vc_b.clock == {'node_b': 1}
    
    # Merge
    vc_merged = vc_a.update(vc_b)
    assert vc_merged.clock == {'node_a': 2, 'node_b': 1}
    
    # Causal ordering
    vc_a2 = vc_a.tick('node_a')
    assert vc_a.happens_before(vc_a2)
    assert not vc_a2.happens_before(vc_a)
    
    # Concurrent
    vc_b2 = vc_b.tick('node_b')
    assert vc_a2.concurrent(vc_b2)
    
    print("✓ Vector clock tests passed")


if __name__ == "__main__":
    test_vector_clock()
