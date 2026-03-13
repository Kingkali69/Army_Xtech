#!/usr/bin/env python3
"""
Simple Test - Does Shared Container Work?
"""

import os
import sys
import time
from pathlib import Path

# Add paths
base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(base_dir, 'substrate'))
sys.path.insert(0, os.path.join(base_dir, 'substrate', 'ai_layer'))

def simple_test():
    """Simple test of shared container functionality"""
    
    print("🔥 SIMPLE SHARED CONTAINER TEST")
    print("=" * 50)
    
    try:
        # Import NEXUS Container
        from nexus_container_layer import NEXUSContainer
        
        # Create shared container path (same for both - this is key!)
        shared_path = os.path.join(base_dir, '.omni', 'shared_container')
        os.makedirs(shared_path, exist_ok=True)
        
        print("📦 Creating SHARED container...")
        container = NEXUSContainer(container_path=shared_path)
        
        # Start container
        print("🚀 Starting container...")
        success = container.start_container()
        
        if success:
            print("✅ Container started successfully!")
        else:
            print("❌ Container failed to start!")
            return False
        
        # Test conversation functionality
        print("\n🧠 Testing conversation...")
        
        # Add conversation
        container.update_conversation(
            conversation_id="test_chat",
            message="Hello from test!",
            context={"test": True, "timestamp": time.time()}
        )
        
        # Retrieve conversation
        conv = container.get_conversation("test_chat")
        
        if conv:
            print("✅ Conversation works!")
            print(f"   Messages: {len(conv.get('messages', []))}")
        else:
            print("❌ Conversation failed!")
        
        # Test tool registry
        print("\n🔧 Testing tool registry...")
        tools = container.list_tools()
        print(f"   Available tools: {list(tools.keys())}")
        
        if tools:
            print("✅ Tool registry works!")
        else:
            print("❌ Tool registry failed!")
        
        # Get status
        print("\n📊 Container status:")
        status = container.get_status()
        print(f"   Running: {status['is_running']}")
        print(f"   Services: {status['services']}")
        
        # Stop container
        print("\n🛑 Stopping container...")
        container.stop_container()
        print("✅ Container stopped!")
        
        print("\n🎯 SIMPLE TEST COMPLETE!")
        print("=" * 50)
        
        # Summary
        print(f"✅ Container Start: {'WORKS' if success else 'FAILED'}")
        print(f"✅ Conversation: {'WORKS' if conv else 'FAILED'}")
        print(f"✅ Tool Registry: {'WORKS' if tools else 'FAILED'}")
        
        if success and conv and tools:
            print("\n🚀 SHARED CONTAINER IS FUNCTIONAL!")
            print("🧠 UNIFIED AI ACROSS MESH IS POSSIBLE!")
            return True
        else:
            print("\n❌ SHARED CONTAINER NEEDS WORK!")
            return False
        
    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = simple_test()
    sys.exit(0 if success else 1)
