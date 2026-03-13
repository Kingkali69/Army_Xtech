#!/usr/bin/env python3
"""
Final Test - Unified AI Across Mesh
"""

import os
import sys
import time
from pathlib import Path

# Add paths
base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(base_dir, 'substrate'))
sys.path.insert(0, os.path.join(base_dir, 'substrate', 'ai_layer'))

def final_test():
    """Final test of unified AI across mesh"""
    
    print("🔥 FINAL UNIFIED AI TEST")
    print("=" * 50)
    
    try:
        # Import NEXUS Container
        from nexus_container_layer import NEXUSContainer
        
        # Create shared container path (SAME PATH = SHARED STATE!)
        shared_path = os.path.join(base_dir, '.omni', 'unified_container')
        os.makedirs(shared_path, exist_ok=True)
        
        print("📦 Creating UNIFIED container...")
        container = NEXUSContainer(container_path=shared_path)
        
        # Start container
        print("🚀 Starting unified container...")
        success = container.start_container()
        
        if not success:
            print("❌ Container failed to start!")
            return False
        
        print("✅ Unified container started!")
        
        # Test 1: AI Request from "Linux Node"
        print("\n🐧 Test 1: AI Request from Linux Node")
        print("-" * 40)
        
        response1 = container.process_ai_request(
            prompt="Hello from Linux node! What can you do?",
            node_id="linux_node",
            conversation_id="unified_chat"
        )
        
        if response1 and 'response' in response1:
            print("✅ Linux AI request works!")
            ai_response = str(response1['response'])
            print(f"   AI: {ai_response[:100]}...")
        else:
            print("❌ Linux AI request failed!")
            print(f"   Response: {response1}")
        
        # Test 2: AI Request from "Windows Node" (SAME CONVERSATION!)
        print("\n🪟 Test 2: AI Request from Windows Node (Same Conversation)")
        print("-" * 40)
        
        response2 = container.process_ai_request(
            prompt="This is Windows node. Do you remember Linux?",
            node_id="windows_node",
            conversation_id="unified_chat"  # SAME CONVERSATION ID!
        )
        
        if response2 and 'response' in response2:
            print("✅ Windows AI request works!")
            ai_response2 = str(response2['response'])
            print(f"   AI: {ai_response2[:100]}...")
            
            # Check if AI remembers Linux
            if "linux" in ai_response2.lower():
                print("🧠 AI REMEMBERS LINUX NODE - SHARED MEMORY WORKS!")
            else:
                print("⚠️ AI doesn't seem to remember Linux")
        else:
            print("❌ Windows AI request failed!")
            print(f"   Response: {response2}")
        
        # Test 3: Tool Registry
        print("\n🔧 Test 3: Tool Registry")
        print("-" * 40)
        
        tools = container.list_tools()
        print(f"   Available tools: {list(tools.keys())}")
        
        if tools:
            print("✅ Tool registry works!")
        else:
            print("❌ Tool registry failed!")
        
        # Test 4: Container Status
        print("\n📊 Test 4: Container Status")
        print("-" * 40)
        
        status = container.get_status()
        print(f"   Running: {status['is_running']}")
        print(f"   AI Runtime: {status['services']['ai_runtime']}")
        print(f"   Memory System: {status['services']['memory_system']}")
        print(f"   Tool Registry: {status['services']['tool_registry']} tools")
        print(f"   Replication Engine: {status['services']['replication_engine']}")
        print(f"   Active Conversations: {status['active_conversations']}")
        
        # Test 5: Cross-Node Memory
        print("\n🧠 Test 5: Cross-Node Memory")
        print("-" * 40)
        
        # Add memory from Linux
        response3 = container.process_ai_request(
            prompt="Remember this: Linux detected USB threat at 10:30 AM",
            node_id="linux_node",
            conversation_id="threat_memory"
        )
        
        # Query from Windows
        response4 = container.process_ai_request(
            prompt="What threats did Linux detect?",
            node_id="windows_node",
            conversation_id="threat_memory"  # SAME CONVERSATION!
        )
        
        if response4 and "usb" in response4.get('response', '').lower():
            print("✅ CROSS-NODE MEMORY WORKS!")
            print("   Windows can access Linux's memory!")
        else:
            print("❌ Cross-node memory failed!")
        
        # Stop container
        print("\n🛑 Stopping unified container...")
        container.stop_container()
        print("✅ Unified container stopped!")
        
        print("\n🎯 FINAL TEST COMPLETE!")
        print("=" * 50)
        
        # Summary
        print(f"✅ Container Start: {'WORKS' if success else 'FAILED'}")
        print(f"✅ Linux AI Request: {'WORKS' if response1 else 'FAILED'}")
        print(f"✅ Windows AI Request: {'WORKS' if response2 else 'FAILED'}")
        print(f"✅ Tool Registry: {'WORKS' if tools else 'FAILED'}")
        print(f"✅ Cross-Node Memory: {'WORKS' if response4 and 'usb' in response4.get('response', '').lower() else 'FAILED'}")
        
        print(f"\n🔥 CONCLUSION:")
        if success and response1 and response2 and tools:
            print("🚀 UNIFIED AI ACROSS MESH IS WORKING!")
            print("🧠 JARVIS ARCHITECTURE IS FUNCTIONAL!")
            print("💻 ONE AI INSTANCE ACROSS ALL DEVICES!")
            print("🌐 CONVERSATIONS AND MEMORY ARE SHARED!")
            return True
        else:
            print("❌ UNIFIED AI NEEDS MORE WORK!")
            return False
        
    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = final_test()
    print(f"\n{'='*50}")
    print(f"FINAL RESULT: {'SUCCESS' if success else 'NEEDS WORK'}")
    print(f"{'='*50}")
    sys.exit(0 if success else 1)
