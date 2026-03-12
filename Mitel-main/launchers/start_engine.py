#!/usr/bin/env python3
"""
RUSTIC Framework - Engine Launcher
Easy startup script
"""

import sys
import os

# Add core to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def main():
    print("🚀 Starting RUSTIC Engine...")
    
    try:
        from core.engine.engine import SecurityEngine
        import asyncio
        
        engine = SecurityEngine()
        asyncio.run(engine.start())
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure core files are in place")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

