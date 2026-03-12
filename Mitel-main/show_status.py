#!/usr/bin/env python3
"""
Show OMNI Status - Simple Visual Output
========================================

Shows system status with controlled test intervals.
Run this to see the demo lock tests running periodically.
"""

import sys
import os
import time
from datetime import datetime
from omni_core import OmniCore
from substrate.step_8_demo_lock.demo_lock import DemoLock

import logging
logging.getLogger().setLevel(logging.ERROR)  # Suppress most logs

def main():
    print('\n' + '='*70)
    print('  OMNI FOUNDATION - LIVE STATUS & TESTS')
    print('='*70)
    print(f'  Started: {datetime.now().strftime("%H:%M:%S")}')
    print('='*70 + '\n')
    
    # Start core
    print('  Starting OMNI Core...')
    core = OmniCore()
    core.start()
    print('  ✅ Core started\n')
    
    # Show initial status
    print('  SYSTEM STATUS:')
    print(f'    Node: {core.node_id}')
    print(f'    Platform: {core.config["platform"]}')
    print(f'    Status: {core.status.value}')
    print(f'    IP: {core.config["local_ip"]}:7777')
    print('')
    
    # Components
    print('  COMPONENTS:')
    print('    ✓ State Store')
    print('    ✓ State Model')
    print('    ✓ Sync Engine')
    print('    ✓ File Transfer')
    print('    ✓ Recovery Engine')
    print('    ✓ Adapter Manager')
    print('')
    
    # Run demo lock every 30 seconds
    print('  Running Demo Lock tests every 30 seconds...')
    print('  Press Ctrl+C to stop\n')
    
    test_count = 0
    
    try:
        while True:
            time.sleep(30)
            test_count += 1
            
            print(f'\n  [{datetime.now().strftime("%H:%M:%S")}] TEST #{test_count}')
            print('  ' + '-'*66)
            
            demo = DemoLock()
            result = demo.run_demo()
            
            if result:
                print('  ✅ ALL TESTS PASSED')
            else:
                print(f'  ❌ FAILED: {demo.failed_tests}')
            
            print('  ' + '-'*66)
            print(f'  Next test in 30 seconds...\n')
            
    except KeyboardInterrupt:
        print('\n\n  Stopping...')
        core.stop()
        print('  ✅ Stopped\n')

if __name__ == "__main__":
    main()
