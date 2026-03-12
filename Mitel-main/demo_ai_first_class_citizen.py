#!/usr/bin/env python3
"""
AI First-Class Citizen Demo
===========================

Demonstrates AI executing commands through the substrate.
Not a tool - a first-class citizen that can push commands
and receive responses back.

This is the "bank teller" - always available, no matter which OS.
"""

import sys
import os
import time
import tempfile

# Add paths
base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(base_dir, 'substrate', 'ai_layer'))
sys.path.insert(0, os.path.join(base_dir, 'substrate', 'filesystem'))

from ai_command_executor import AICommandExecutor, CommandStatus
from cross_platform_bridge import CrossPlatformBridge

def main():
    print("="*70)
    print("  AI FIRST-CLASS CITIZEN DEMO")
    print("="*70)
    print()
    print("AI is NOT a tool - AI is a FIRST-CLASS CITIZEN")
    print("AI can execute commands through the substrate")
    print("AI can push commands and receive responses back")
    print()
    print("This is the 'bank teller' - always available, no matter which OS")
    print()
    
    # Initialize AI command executor
    node_id = "demo_node_001"
    print(f"Initializing AI Command Executor...")
    print(f"Node ID: {node_id}")
    print()
    
    executor = AICommandExecutor(node_id=node_id)
    
    # Test 1: Local file operations
    print("="*70)
    print("  TEST 1: AI Executes Local File Operations")
    print("="*70)
    
    # Create test file
    test_file = tempfile.NamedTemporaryFile(delete=False, suffix='.txt')
    test_file.write(b"Hello from AI first-class citizen!")
    test_file.close()
    test_path = test_file.name
    
    print(f"Created test file: {test_path}")
    print()
    
    # AI checks if file exists
    print("AI checking if file exists...")
    cmd_id = executor.execute_command(
        command_type='file_exists',
        parameters={'file_path': test_path}
    )
    
    cmd = executor.wait_for_command(cmd_id)
    if cmd and cmd.status == CommandStatus.COMPLETE:
        print(f"✅ AI Response: File exists = {cmd.result.get('exists')}")
    print()
    
    # AI gets file info
    print("AI getting file info...")
    cmd_id = executor.execute_command(
        command_type='file_info',
        parameters={'file_path': test_path}
    )
    
    cmd = executor.wait_for_command(cmd_id)
    if cmd and cmd.status == CommandStatus.COMPLETE:
        print(f"✅ AI Response: File size = {cmd.result.get('size')} bytes")
    print()
    
    # AI lists directory
    print("AI listing directory...")
    cmd_id = executor.execute_command(
        command_type='file_list',
        parameters={'directory': os.path.dirname(test_path)}
    )
    
    cmd = executor.wait_for_command(cmd_id)
    if cmd and cmd.status == CommandStatus.COMPLETE:
        files = cmd.result.get('files', [])
        print(f"✅ AI Response: Found {len(files)} items in directory")
        for f in files[:5]:  # Show first 5
            print(f"  - {f['name']} ({'dir' if f['is_directory'] else 'file'})")
    print()
    
    # Test 2: Cross-platform bridge
    print("="*70)
    print("  TEST 2: Cross-Platform Bridge (AI as Bank Teller)")
    print("="*70)
    
    bridge = CrossPlatformBridge(node_id=node_id)
    
    print("AI can pull files from any OS:")
    print("  - Linux Thunar → Windows Explorer")
    print("  - Windows Explorer → Linux Thunar")
    print("  - macOS Finder → Any OS")
    print()
    
    # AI pulls file (simulated)
    print("AI pulling file through substrate...")
    result = bridge.get_file(
        remote_path="/remote/path/file.txt",
        local_path=os.path.join(os.path.dirname(test_path), "pulled_file.txt"),
        target_node=None  # Auto-discover
    )
    
    if result.get('success'):
        print(f"✅ AI successfully pulled file")
    else:
        print(f"ℹ️  AI command executed (simulated remote pull)")
    print()
    
    # Test 3: AI command through substrate
    print("="*70)
    print("  TEST 3: AI Command Through Substrate")
    print("="*70)
    
    print("AI pushing command through substrate...")
    print("Command flows: AI → Substrate → Target Node → Response → AI")
    print()
    
    # Simulate command push
    cmd_id = executor.execute_command(
        command_type='file_pull',
        target_node="remote_node_001",  # Would push through substrate
        parameters={
            'file_path': '/remote/path/file.txt',
            'target_path': '/local/path/file.txt'
        }
    )
    
    print(f"Command ID: {cmd_id[:12]}...")
    print(f"Command pushed through substrate")
    print()
    
    # Cleanup
    print("Cleaning up...")
    if os.path.exists(test_path):
        os.remove(test_path)
    
    print()
    print("="*70)
    print("  DEMO COMPLETE")
    print("="*70)
    print()
    print("Key Features Demonstrated:")
    print("  ✓ AI executes commands directly (not a tool)")
    print("  ✓ AI pushes commands through substrate")
    print("  ✓ AI receives responses back")
    print("  ✓ AI is first-class citizen")
    print("  ✓ Cross-platform file access")
    print("  ✓ AI as 'bank teller' - always available")
    print()
    print("December 26th - AI became first-class citizen!")
    print("AI can now push commands through substrate and get responses back.")
    print()

if __name__ == "__main__":
    main()
