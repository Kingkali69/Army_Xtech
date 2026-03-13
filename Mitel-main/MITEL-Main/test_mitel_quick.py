#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Quick M.I.T.E.L. integration test - verify it loads"""

import os
import sys

base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, base_dir)
sys.path.insert(0, os.path.join(base_dir, 'substrate'))

print("Testing M.I.T.E.L. integration...")
print()

# Test 1: Can we import M.I.T.E.L.?
try:
    from mitel_subsystem import MITELSubsystem
    print("[PASS] M.I.T.E.L. module imports successfully")
except Exception as e:
    print(f"[FAIL] M.I.T.E.L. import failed: {e}")
    sys.exit(1)

# Test 2: Can we create M.I.T.E.L. instance?
try:
    config = {
        'enabled': True,
        'device_registry_file': 'data/mitel_devices.yaml',
        'behavioral_profiles_file': 'data/mitel_profiles.yaml',
        'anomaly_threshold': 0.8,
        'scan_interval': 1.0,
    }
    mitel = MITELSubsystem(config=config, state_model=None, node_id='test_node')
    print("[PASS] M.I.T.E.L. instance created")
except Exception as e:
    print(f"[FAIL] M.I.T.E.L. instance creation failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Can we initialize M.I.T.E.L.?
try:
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    success = loop.run_until_complete(mitel.initialize())
    loop.close()
    
    if success:
        print("[PASS] M.I.T.E.L. initialized successfully")
    else:
        print("[FAIL] M.I.T.E.L. initialization returned False")
        sys.exit(1)
except Exception as e:
    print(f"[FAIL] M.I.T.E.L. initialization failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Can we scan for devices?
try:
    devices = mitel._scan_connected_devices()
    print(f"[PASS] Device scan works - found {len(devices)} devices")
    
    if devices:
        print("\nDetected devices:")
        for i, device in enumerate(devices[:3], 1):
            print(f"  {i}. {device.get('name', 'Unknown')} (ID: {device.get('device_id', 'N/A')[:16]}...)")
    else:
        print("  (No devices detected - this is normal if no USB peripherals)")
        
except Exception as e:
    print(f"[FAIL] Device scan failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()
print("=" * 60)
print("M.I.T.E.L. INTEGRATION TEST: PASSED")
print("=" * 60)
print()
print("Next steps:")
print("1. Run full OMNI to test in mesh: ./launch_omni_complete.sh")
print("2. Check web console: http://localhost:8888/api/mitel")
print("3. Build visual UI components for demo")
