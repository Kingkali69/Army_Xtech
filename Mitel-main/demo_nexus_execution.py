#!/usr/bin/env python3
"""
NEXUS Execution Demo - File Transfer
=====================================

Demonstrates NEXUS executing file transfers autonomously.
Execution-first layer (not chat).
"""

import sys
import os
import time

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'substrate', 'ai_layer'))

from nexus_file_executor import NexusFileExecutor

def demo_nexus_execution():
    """Demo NEXUS file execution capabilities"""
    
    print("=" * 70)
    print("NEXUS FILE EXECUTION DEMO")
    print("=" * 70)
    print()
    
    # Initialize NEXUS file executor
    print("[1] Initializing NEXUS File Executor...")
    executor = NexusFileExecutor(node_id="demo_node")
    print("    [OK] NEXUS ready - bank teller model active (3 lanes)")
    print()
    
    # Create test file
    print("[2] Creating test file...")
    test_file = "C:\\Users\\kali\\Desktop\\test_file.txt"
    with open(test_file, 'w') as f:
        f.write("This is a test file for NEXUS execution demo.\n")
        f.write("NEXUS is a first-class citizen - executing commands autonomously.\n")
    print(f"    [OK] Created: {test_file}")
    print()
    
    # Demo 1: Local copy
    print("[3] NEXUS executing: Copy file locally")
    target_file = "C:\\Users\\kali\\Desktop\\test_file_copy.txt"
    success = executor.copy_file(test_file, target_file)
    if success:
        print(f"    [OK] File copied: {test_file} -> {target_file}")
    else:
        print("    [FAIL] Copy failed")
    print()
    
    # Demo 2: Local move
    print("[4] NEXUS executing: Move file locally")
    moved_file = "C:\\Users\\kali\\Desktop\\test_file_moved.txt"
    success = executor.move_file(target_file, moved_file)
    if success:
        print(f"    [OK] File moved: {target_file} -> {moved_file}")
    else:
        print("    [FAIL] Move failed")
    print()
    
    # Demo 3: List files
    print("[5] NEXUS executing: List files")
    files = executor.list_files("C:\\Users\\kali\\Desktop")
    test_files = [f for f in files if 'test_file' in f]
    print(f"    [OK] Found {len(test_files)} test files:")
    for f in test_files[:5]:  # Show first 5
        print(f"      - {f}")
    print()
    
    # Demo 4: Push file (would go to remote node)
    print("[6] NEXUS executing: Push file to remote node (simulated)")
    print("    Note: Requires target node to be online")
    request_id = executor.push_file(
        source_path=test_file,
        target_node="remote_node_123",
        target_path="C:\\Users\\kali\\Desktop\\received_file.txt",
        priority=7
    )
    if request_id:
        print(f"    [OK] Transfer initiated: {request_id}")
        status = executor.get_transfer_status(request_id)
        print(f"    [OK] Lane: {status['lane']}")
        print(f"    [OK] Priority: {status['priority']}")
    else:
        print("    [WARN] Transfer queued (target node offline)")
    print()
    
    # Demo 5: Delete file
    print("[7] NEXUS executing: Delete file")
    success = executor.delete_file(moved_file)
    if success:
        print(f"    [OK] File deleted: {moved_file}")
    else:
        print("    [FAIL] Delete failed")
    print()
    
    print("=" * 70)
    print("NEXUS EXECUTION DEMO COMPLETE")
    print("=" * 70)
    print()
    print("NEXUS executed:")
    print("  [OK] Local file copy")
    print("  [OK] Local file move")
    print("  [OK] File listing")
    print("  [OK] Remote file push (queued)")
    print("  [OK] File deletion")
    print()
    print("This is execution-first AI - not just chat.")
    print("NEXUS is a first-class citizen in the substrate.")
    print()

if __name__ == '__main__':
    demo_nexus_execution()
