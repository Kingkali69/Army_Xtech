#!/usr/bin/env python3
"""
Test Local LLM Integration
==========================

Quick test to verify TinyLlama model is working.
"""

import sys
import os

# Add paths
base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(base_dir, 'substrate', 'ai_layer'))

print("="*70)
print("  TESTING LOCAL LLM (TinyLlama)")
print("="*70)
print()

try:
    from local_llm_integration import LocalLLM, LLAMA_CPP_AVAILABLE
    
    if not LLAMA_CPP_AVAILABLE:
        print("❌ llama-cpp-python not installed")
        print("   Install with: pip install llama-cpp-python")
        sys.exit(1)
    
    print("✅ llama-cpp-python available")
    print()
    
    # Check if model exists
    model_path = os.path.expanduser("~/.omni/models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf")
    if not os.path.exists(model_path):
        print(f"❌ Model not found: {model_path}")
        print("   Download it first!")
        sys.exit(1)
    
    print(f"✅ Model found: {model_path}")
    print(f"   Size: {os.path.getsize(model_path) / (1024*1024):.2f} MB")
    print()
    
    print("Loading model (this may take a moment)...")
    llm = LocalLLM()
    print()
    
    print("="*70)
    print("  TEST 1: Simple Generation")
    print("="*70)
    prompt = "What is artificial intelligence?"
    print(f"Prompt: {prompt}")
    print()
    print("Generating response...")
    response = llm.generate(prompt, max_tokens=100, temperature=0.7)
    print(f"Response: {response}")
    print()
    
    print("="*70)
    print("  TEST 2: Chat Completion")
    print("="*70)
    messages = [
        {"role": "system", "content": "You are a helpful AI assistant."},
        {"role": "user", "content": "Explain file transfer optimization in one sentence."}
    ]
    print("Messages:", messages)
    print()
    print("Generating response...")
    response = llm.chat(messages, max_tokens=100)
    print(f"Response: {response}")
    print()
    
    print("="*70)
    print("  TEST 3: File Transfer Analysis")
    print("="*70)
    analysis = llm.analyze_transfer_decision(
        file_path="/path/to/document.pdf",
        file_size=10 * 1024 * 1024,  # 10 MB
        network_conditions={
            'bandwidth_mbps': 25.0,
            'latency_ms': 50.0,
            'packet_loss': 0.01
        }
    )
    print("Analysis:", analysis)
    print()
    
    print("="*70)
    print("  ✅ ALL TESTS PASSED")
    print("="*70)
    print()
    print("Local LLM is ready for integration!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
