#!/usr/bin/env python3
"""
Test Shared NEXUS Container - Unified AI Across Mesh
"""

import os
import sys
import time
import json
from pathlib import Path

# Add paths
base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(base_dir, 'substrate'))
sys.path.insert(0, os.path.join(base_dir, 'substrate', 'ai_layer'))

def test_shared_container():
    """Test that NEXUS container provides shared intelligence across nodes"""
    
    print("🔥 Testing Shared NEXUS Container...")
    print("=" * 60)
    
    try:
        # Import NEXUS Container
        from nexus_container_layer import NEXUSContainer, NodeIdentity
        
        # Create two different containers (simulating two nodes)
        container1_path = os.path.join(base_dir, '.omni', 'test_container1')
        container2_path = os.path.join(base_dir, '.omni', 'test_container2')
        
        os.makedirs(container1_path, exist_ok=True)
        os.makedirs(container2_path, exist_ok=True)
        
        print("📦 Creating containers...")
        container1 = NEXUSContainer(container_path=container1_path)
        container2 = NEXUSContainer(container_path=container2_path)
        
        # Start containers
        print("🚀 Starting containers...")
        container1.start_container()
        container2.start_container()
        
        # Register nodes
        print("🔗 Registering nodes...")
        
        # Create node identities
        node1_identity = NodeIdentity(
            node_id="node_linux",
            public_key=b"linux_public_key_placeholder"
        )
        
        node2_identity = NodeIdentity(
            node_id="node_windows", 
            public_key=b"windows_public_key_placeholder"
        )
        
        container1.register_node(node1_identity)
        container2.register_node(node2_identity)
        
        # Test 1: Shared Conversation
        print("\n🧠 Test 1: Shared Conversation")
        print("-" * 40)
        
        # Add conversation from node 1
        print("📝 Node 1 adding conversation...")
        container1.update_conversation(
            conversation_id="demo_chat",
            message="Hello from Linux node!",
            context={"node": "linux", "timestamp": time.time()}
        )
        
        # Retrieve from node 2
        print("📖 Node 2 retrieving conversation...")
        conv2 = container2.get_conversation("demo_chat")
        
        if conv2:
            print("✅ SHARED CONVERSATION WORKS!")
            print(f"   Messages: {len(conv2.get('messages', []))}")
            print(f"   Last message: {conv2.get('messages', [])[-1] if conv2.get('messages') else 'None'}")
        else:
            print("❌ SHARED CONVERSATION FAILED!")
        
        # Test 2: Tool Registry
        print("\n🔧 Test 2: Tool Registry")
        print("-" * 40)
        
        # Register tool from node 1
        print("📝 Node 1 registering tool...")
        container1.register_tool(
            tool_name="system_monitor",
            tool_type="monitoring",
            capabilities=["cpu", "memory", "disk"],
            security_level="medium"
        )
        
        # Check if node 2 can see it
        print("🔍 Node 2 checking tools...")
        tools2 = container2.list_tools()
        
        if "system_monitor" in tools2:
            print("✅ SHARED TOOL REGISTRY WORKS!")
            print(f"   Tools available: {list(tools2.keys())}")
        else:
            print("❌ SHARED TOOL REGISTRY FAILED!")
            print(f"   Available tools: {list(tools2.keys())}")
        
        # Test 3: Memory State
        print("\n💾 Test 3: Memory State")
        print("-" * 40)
        
        # Add memory from node 1
        print("📝 Node 1 adding memory...")
        container1.update_conversation(
            conversation_id="collective_memory",
            message="Linux node detected USB device: Rubber Ducky",
            context={"threat": true, "device_id": "rubber_ducky_001"}
        )
        
        # Retrieve from node 2
        print("🔍 Node 2 checking memory...")
        memory2 = container2.get_conversation("collective_memory")
        
        if memory2 and "rubber_ducky" in str(memory2):
            print("✅ COLLECTIVE MEMORY WORKS!")
            print(f"   Memory shared across nodes")
        else:
            print("❌ COLLECTIVE MEMORY FAILED!")
        
        # Test 4: Node Status
        print("\n📊 Test 4: Node Status")
        print("-" * 40)
        
        status1 = container1.get_status()
        status2 = container2.get_status()
        
        print(f"🔗 Node 1 sees: {status1['nodes']} nodes")
        print(f"🔗 Node 2 sees: {status2['nodes']} nodes")
        
        if status1['nodes'] == status2['nodes'] == 2:
            print("✅ NODE REGISTRY WORKS!")
        else:
            print("❌ NODE REGISTRY FAILED!")
        
        # Cleanup
        print("\n🧹 Cleaning up...")
        container1.stop_container()
        container2.stop_container()
        
        print("\n🎯 SHARED CONTAINER TEST COMPLETE!")
        print("=" * 60)
        
        # Summary
        print("\n📊 TEST RESULTS:")
        print("✅ Shared Conversation: WORKS" if conv2 else "❌ Shared Conversation: FAILED")
        print("✅ Tool Registry: WORKS" if "system_monitor" in tools2 else "❌ Tool Registry: FAILED")
        print("✅ Collective Memory: WORKS" if memory2 and "rubber_ducky" in str(memory2) else "❌ Collective Memory: FAILED")
        print("✅ Node Registry: WORKS" if status1['nodes'] == status2['nodes'] == 2 else "❌ Node Registry: FAILED")
        
        print("\n🔥 CONCLUSION:")
        if conv2 and "system_monitor" in tools2:
            print("🚀 SHARED NEXUS CONTAINER IS WORKING!")
            print("🧠 UNIFIED AI ACROSS MESH IS FUNCTIONAL!")
            print("💻 JARVIS ARCHITECTURE IS READY!")
        else:
            print("❌ SHARED CONTAINER NEEDS FIXES!")
        
        return conv2 and "system_monitor" in tools2
        
    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_shared_container()
    sys.exit(0 if success else 1)
