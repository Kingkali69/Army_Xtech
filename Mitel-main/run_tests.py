#!/usr/bin/env python3
"""
OMNI Demo Lock Tests - Controlled Intervals
===========================================

Runs demo lock tests at controlled intervals.
Shows clear output of what's being tested.
"""

import sys
import os
import time
from datetime import datetime
from substrate.step_8_demo_lock.demo_lock import DemoLock

import logging
logging.getLogger().setLevel(logging.ERROR)

def run_test_cycle(cycle_num: int):
    """Run one test cycle"""
    print(f'\n{"="*70}')
    print(f'  TEST CYCLE #{cycle_num} - {datetime.now().strftime("%H:%M:%S")}')
    print('='*70)
    
    demo = DemoLock()
    result = demo.run_demo()
    
    print('')
    if result:
        print('  ✅ ALL TESTS PASSED')
        print('  ✅ Foundation rebuild validated')
    else:
        print(f'  ❌ TESTS FAILED: {demo.failed_tests}')
    
    print('='*70)
    return result

def main():
    """Main test loop"""
    print('\n' + '='*70)
    print('  OMNI FOUNDATION - DEMO LOCK TESTS')
    print('='*70)
    print('  Running tests at controlled intervals')
    print('  Press Ctrl+C to stop')
    print('='*70)
    
    # Run initial test
    run_test_cycle(1)
    
    # Periodic tests every 30 seconds
    cycle = 2
    interval = 30
    
    print(f'\n  Next test in {interval} seconds...')
    
    try:
        while True:
            time.sleep(interval)
            run_test_cycle(cycle)
            print(f'\n  Next test in {interval} seconds...')
            cycle += 1
    except KeyboardInterrupt:
        print('\n\n  Tests stopped.')
        print('='*70 + '\n')

if __name__ == "__main__":
    main()
