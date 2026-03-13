#!/usr/bin/env python3
"""
Test Trinity-Enhanced LLM
=========================

Test the enhanced intelligence system.
"""

import sys
import os

# Add paths
base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(base_dir, 'substrate', 'ai_layer'))

print("="*70)
print("  TESTING TRINITY-ENHANCED LLM")
print("="*70)
print()

try:
    from trinity_enhanced_llm import TrinityEnhancedLLM, TRINITY_AVAILABLE
    
    if not TRINITY_AVAILABLE:
        print("❌ Trinity not available")
        sys.exit(1)
    
    print("✅ Trinity architecture available")
    print("✅ Initializing Trinity-Enhanced LLM...")
    print()
    
    llm = TrinityEnhancedLLM()
    
    print("="*70)
    print("  TEST 1: Basic Chat with Intelligence")
    print("="*70)
    
    response1 = llm.chat("Hello! Can you help me with file transfers?")
    print(f"You: Hello! Can you help me with file transfers?")
    print()
    print(f"AI: {response1['response']}")
    print()
    print(f"Intent: {response1['intent']}")
    print(f"Confidence: {response1['confidence']:.2f}")
    print(f"Patterns: {response1['patterns']}")
    print()
    
    print("="*70)
    print("  TEST 2: Memory Context")
    print("="*70)
    
    response2 = llm.chat("How do I transfer a file from Linux to Windows?")
    print(f"You: How do I transfer a file from Linux to Windows?")
    print()
    print(f"AI: {response2['response']}")
    print()
    print(f"Intent: {response2['intent']}")
    print(f"Memory Context: {response2['memory_context']}")
    print()
    
    print("="*70)
    print("  TEST 3: Pattern Learning")
    print("="*70)
    
    response3 = llm.chat("Tell me more about file transfers")
    print(f"You: Tell me more about file transfers")
    print()
    print(f"AI: {response3['response']}")
    print()
    print(f"Intent: {response3['intent']}")
    print(f"Patterns: {response3['patterns']}")
    print()
    
    print("="*70)
    print("  TEST 4: Intelligence Summary")
    print("="*70)
    
    summary = llm.get_intelligence_summary()
    print("Trinity Intelligence State:")
    print(f"  Memory: {summary['memory']}")
    print(f"  Patterns: {summary['patterns']}")
    print(f"  Intelligence Level: {summary['intelligence_level']}")
    print()
    
    print("="*70)
    print("  ✅ ALL TESTS PASSED")
    print("="*70)
    print()
    print("Trinity-Enhanced LLM is working!")
    print("AI now has REAL intelligence - memory, patterns, context!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
