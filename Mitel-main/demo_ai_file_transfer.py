#!/usr/bin/env python3
"""
AI-Assisted File Transfer Demo
===============================

Demonstrates first-class citizen AI for file transfers:
- AI determines priority
- AI optimizes chunk size
- AI selects optimal path
- AI predicts retry success
"""

import sys
import os
import time
import tempfile
from pathlib import Path

# Add paths
base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(base_dir, 'substrate', 'ai_layer'))
sys.path.insert(0, os.path.join(base_dir, 'substrate', 'step_5_files_as_payloads'))

from ai_integration import AIEnhancedFileTransferEngine
from file_transfer_ai import TransferPriority

def create_test_file(size_mb: float = 1.0) -> str:
    """Create a test file of specified size."""
    test_file = tempfile.NamedTemporaryFile(delete=False, suffix='.bin')
    test_file.write(b'0' * int(size_mb * 1024 * 1024))
    test_file.close()
    return test_file.name

def main():
    print("="*70)
    print("  AI-ASSISTED FILE TRANSFER DEMO")
    print("="*70)
    print()
    
    # Initialize AI-enhanced file transfer engine
    node_id = "demo_node_001"
    print(f"Initializing AI-enhanced file transfer engine...")
    print(f"Node ID: {node_id}")
    print()
    
    engine = AIEnhancedFileTransferEngine(node_id=node_id)
    
    # Simulate network conditions for different peers
    print("Simulating network conditions...")
    print()
    
    # Peer 1: High bandwidth, low latency (optimal)
    engine.update_network_metrics(
        peer_id="peer_001",
        bandwidth_mbps=100.0,
        latency_ms=10.0,
        packet_loss=0.0,
        jitter_ms=1.0
    )
    print("  Peer 001: 100 Mbps, 10ms latency, 0% loss")
    
    # Peer 2: Medium bandwidth, medium latency
    engine.update_network_metrics(
        peer_id="peer_002",
        bandwidth_mbps=25.0,
        latency_ms=50.0,
        packet_loss=0.01,
        jitter_ms=5.0
    )
    print("  Peer 002: 25 Mbps, 50ms latency, 1% loss")
    
    # Peer 3: Low bandwidth, high latency (poor)
    engine.update_network_metrics(
        peer_id="peer_003",
        bandwidth_mbps=5.0,
        latency_ms=200.0,
        packet_loss=0.05,
        jitter_ms=20.0
    )
    print("  Peer 003: 5 Mbps, 200ms latency, 5% loss")
    print()
    
    # Test 1: Small file (high priority)
    print("="*70)
    print("  TEST 1: Small File (High Priority)")
    print("="*70)
    test_file_1 = create_test_file(size_mb=0.1)  # 100KB
    print(f"Created test file: {test_file_1} ({os.path.getsize(test_file_1)} bytes)")
    
    decision_1 = engine.ai.make_transfer_decision(
        file_path=test_file_1,
        file_size=os.path.getsize(test_file_1),
        available_peers=["peer_001", "peer_002", "peer_003"],
        context={"urgent": True}
    )
    
    print(f"AI Decision:")
    print(f"  Priority: {decision_1.priority.name}")
    print(f"  Optimal Chunk Size: {decision_1.optimal_chunk_size // 1024} KB")
    print(f"  Selected Peer: {decision_1.optimal_path}")
    print(f"  Reasoning: {decision_1.reasoning}")
    print()
    
    # Test 2: Large file (low priority)
    print("="*70)
    print("  TEST 2: Large File (Low Priority)")
    print("="*70)
    test_file_2 = create_test_file(size_mb=50.0)  # 50MB
    print(f"Created test file: {test_file_2} ({os.path.getsize(test_file_2)} bytes)")
    
    decision_2 = engine.ai.make_transfer_decision(
        file_path=test_file_2,
        file_size=os.path.getsize(test_file_2),
        available_peers=["peer_001", "peer_002", "peer_003"],
        context={}
    )
    
    print(f"AI Decision:")
    print(f"  Priority: {decision_2.priority.name}")
    print(f"  Optimal Chunk Size: {decision_2.optimal_chunk_size // 1024} KB")
    print(f"  Selected Peer: {decision_2.optimal_path}")
    print(f"  Reasoning: {decision_2.reasoning}")
    print()
    
    # Test 3: Binary file (system file)
    print("="*70)
    print("  TEST 3: Binary File (System File)")
    print("="*70)
    test_file_3 = create_test_file(size_mb=2.0)  # 2MB
    # Rename to .bin to simulate binary
    binary_path = test_file_3.replace('.bin', '_binary.bin')
    os.rename(test_file_3, binary_path)
    print(f"Created test file: {binary_path} ({os.path.getsize(binary_path)} bytes)")
    
    decision_3 = engine.ai.make_transfer_decision(
        file_path=binary_path,
        file_size=os.path.getsize(binary_path),
        available_peers=["peer_001", "peer_002", "peer_003"],
        context={"system_file": True}
    )
    
    print(f"AI Decision:")
    print(f"  Priority: {decision_3.priority.name}")
    print(f"  Optimal Chunk Size: {decision_3.optimal_chunk_size // 1024} KB")
    print(f"  Selected Peer: {decision_3.optimal_path}")
    print(f"  Reasoning: {decision_3.reasoning}")
    print()
    
    # Test 4: Show AI learning
    print("="*70)
    print("  TEST 4: AI Learning from Transfer Results")
    print("="*70)
    
    # Simulate successful transfer
    engine.handle_transfer_completion(
        file_id="test_transfer_001",
        success=True,
        transfer_time=2.5,
        peer_id="peer_001"
    )
    print("Recorded successful transfer to peer_001")
    
    # Simulate failed transfer
    engine.handle_transfer_completion(
        file_id="test_transfer_002",
        success=False,
        transfer_time=30.0,
        peer_id="peer_003"
    )
    print("Recorded failed transfer to peer_003")
    
    print()
    print("AI has learned from these results and will optimize future transfers.")
    print()
    
    # Cleanup
    print("Cleaning up test files...")
    for f in [test_file_1, binary_path]:
        if os.path.exists(f):
            os.remove(f)
    
    print()
    print("="*70)
    print("  DEMO COMPLETE")
    print("="*70)
    print()
    print("Key Features Demonstrated:")
    print("  ✓ AI determines transfer priority")
    print("  ✓ AI optimizes chunk size based on network conditions")
    print("  ✓ AI selects optimal peer/path")
    print("  ✓ AI learns from transfer results")
    print("  ✓ AI adapts to network conditions")
    print()

if __name__ == "__main__":
    main()
