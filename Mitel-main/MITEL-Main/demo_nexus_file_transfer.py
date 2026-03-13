#!/usr/bin/env python3
"""
NEXUS File Transfer Demo
========================

Demonstrates NEXUS (first-class citizen AI) controlling file transfers.
NEXUS makes intelligent decisions about routing, priority, and optimization.
"""

import sys
import os
import tempfile

# Add paths
base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(base_dir, 'substrate', 'ai_layer'))
sys.path.insert(0, os.path.join(base_dir, 'substrate', 'step_5_files_as_payloads'))

from nexus_file_transfer import NexusFileTransfer
from file_transfer_ai import NetworkCondition
from trinity_enhanced_llm import TrinityEnhancedLLM

def create_test_file(size_mb: float = 1.0) -> str:
    """Create a test file"""
    test_file = tempfile.NamedTemporaryFile(delete=False, suffix='.bin')
    test_file.write(b'0' * int(size_mb * 1024 * 1024))
    test_file.close()
    return test_file.name

def main():
    print("="*70)
    print("  NEXUS FILE TRANSFER DEMO")
    print("="*70)
    print()
    print("NEXUS (first-class citizen AI) is controlling file transfers")
    print("NEXUS makes intelligent decisions about routing, priority, optimization")
    print()
    
    # Initialize NEXUS
    print("Initializing NEXUS...")
    nexus_llm = TrinityEnhancedLLM()
    print("✅ NEXUS initialized")
    print()
    
    # Initialize NEXUS file transfer controller
    node_id = "demo_node_001"
    nexus_ft = NexusFileTransfer(node_id=node_id, nexus_llm=nexus_llm)
    print("✅ NEXUS file transfer controller initialized")
    print()
    
    # Simulate network conditions
    print("Simulating network conditions...")
    condition1 = NetworkCondition(100.0, 10.0, 0.0, 1.0)
    nexus_ft.update_network_metrics("peer_001", condition1)
    print("  Peer 001: 100 Mbps, 10ms latency")
    
    condition2 = NetworkCondition(25.0, 50.0, 0.01, 5.0)
    nexus_ft.update_network_metrics("peer_002", condition2)
    print("  Peer 002: 25 Mbps, 50ms latency")
    
    condition3 = NetworkCondition(5.0, 200.0, 0.05, 20.0)
    nexus_ft.update_network_metrics("peer_003", condition3)
    print("  Peer 003: 5 Mbps, 200ms latency")
    print()
    
    # Test 1: Small urgent file
    print("="*70)
    print("  TEST 1: Small Urgent File")
    print("="*70)
    test_file_1 = create_test_file(size_mb=0.1)  # 100KB
    print(f"File: {test_file_1} ({os.path.getsize(test_file_1)} bytes)")
    print()
    print("Asking NEXUS to make transfer decision...")
    
    network_conditions = {
        "peer_001": NetworkCondition(100.0, 10.0, 0.0, 1.0),
        "peer_002": NetworkCondition(25.0, 50.0, 0.01, 5.0),
        "peer_003": NetworkCondition(5.0, 200.0, 0.05, 20.0)
    }
    
    decision = nexus_ft.make_transfer_decision(
        file_path=test_file_1,
        file_size=os.path.getsize(test_file_1),
        available_peers=["peer_001", "peer_002", "peer_003"],
        network_conditions=network_conditions,
        context={"urgent": True}
    )
    
    print()
    print("NEXUS Decision:")
    print(f"  Priority: {decision.priority.name}")
    print(f"  Chunk Size: {decision.optimal_chunk_size // 1024} KB")
    print(f"  Selected Peer: {decision.optimal_path}")
    print(f"  Retry Strategy: {'Yes' if decision.should_retry else 'No'} (delay: {decision.retry_delay}s)")
    print(f"  Reasoning: {decision.reasoning}")
    print()
    
    # Test 2: Large file
    print("="*70)
    print("  TEST 2: Large File")
    print("="*70)
    test_file_2 = create_test_file(size_mb=50.0)  # 50MB
    print(f"File: {test_file_2} ({os.path.getsize(test_file_2)} bytes)")
    print()
    print("Asking NEXUS to make transfer decision...")
    
    decision2 = nexus_ft.make_transfer_decision(
        file_path=test_file_2,
        file_size=os.path.getsize(test_file_2),
        available_peers=["peer_001", "peer_002", "peer_003"],
        network_conditions=network_conditions,
        context={}
    )
    
    print()
    print("NEXUS Decision:")
    print(f"  Priority: {decision2.priority.name}")
    print(f"  Chunk Size: {decision2.optimal_chunk_size // 1024} KB")
    print(f"  Selected Peer: {decision2.optimal_path}")
    print(f"  Reasoning: {decision2.reasoning}")
    print()
    
    # Test 3: Simulate transfer completion and learning
    print("="*70)
    print("  TEST 3: NEXUS Learning from Results")
    print("="*70)
    print("Simulating successful transfer...")
    
    nexus_ft.record_transfer_result(
        file_path=test_file_1,
        success=True,
        transfer_time=2.5,
        bytes_transferred=os.path.getsize(test_file_1),
        peer_id="peer_001",
        decision=decision
    )
    print("✅ NEXUS learned from successful transfer")
    print()
    
    # Cleanup
    print("Cleaning up...")
    for f in [test_file_1, test_file_2]:
        if os.path.exists(f):
            os.remove(f)
    
    print()
    print("="*70)
    print("  DEMO COMPLETE")
    print("="*70)
    print()
    print("Key Features Demonstrated:")
    print("  ✓ NEXUS makes transfer decisions")
    print("  ✓ NEXUS selects optimal peer")
    print("  ✓ NEXUS optimizes chunk size")
    print("  ✓ NEXUS determines priority")
    print("  ✓ NEXUS learns from results")
    print()
    print("NEXUS is controlling file transfers - first-class citizen active!")
    print()

if __name__ == "__main__":
    main()
