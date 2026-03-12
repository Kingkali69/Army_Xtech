#!/usr/bin/env python3
"""
OMNI Foundation Demo - Visual Running Demo
==========================================

Shows the complete foundation rebuild running with periodic tests.
Controlled test intervals - you can see everything working.
"""

import sys
import os
import time
import threading
from datetime import datetime
from omni_core import OmniCore
from substrate.step_8_demo_lock.demo_lock import DemoLock

def print_header():
    """Print header"""
    print('\n' + '='*70)
    print('OMNI FOUNDATION REBUILD - LIVE DEMO')
    print('='*70)
    print(f'Started: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print('='*70 + '\n')

def print_status(core: OmniCore, test_count: int):
    """Print current status"""
    print(f'\n[{datetime.now().strftime("%H:%M:%S")}] STATUS UPDATE #{test_count}')
    print('-'*70)
    print(f'Node ID: {core.node_id[:20]}...')
    print(f'Platform: {core.config["platform"]}')
    print(f'Status: {core.status.value}')
    port = getattr(core, 'fabric_port', core.config.get('fabric_port', 7777))
    print(f'IP: {core.config["local_ip"]}:{port}')
    
    # Component status
    components = []
    if core.state_store:
        components.append('State Store')
    if core.state_model:
        state_keys = len(core.state_model.state)
        components.append(f'State Model ({state_keys} keys)')
    if core.sync_engine:
        components.append('Sync Engine')
    if core.file_transfer_engine:
        components.append('File Transfer')
    if core.recovery_engine:
        health = core.recovery_engine.get_health_status()
        components.append(f'Recovery ({health["overall_status"]})')
    if core.adapter_manager:
        adapter_status = core.adapter_manager.get_status()
        components.append(f'Adapters ({adapter_status["adapters_loaded"]})')
    
    print(f'Components: {", ".join(components)}')
    print('-'*70)

def run_demo_lock_test():
    """Run demo lock test"""
    print('\n[' + datetime.now().strftime("%H:%M:%S") + '] RUNNING DEMO LOCK TEST')
    print('-'*70)
    
    demo = DemoLock()
    result = demo.run_demo()
    
    if result:
        print('✅ ALL TESTS PASSED')
    else:
        print(f'❌ TESTS FAILED: {demo.failed_tests}')
    
    print('-'*70)
    return result

def main():
    """Main demo loop"""
    print_header()
    
    # Initialize core
    print('Initializing OMNI Core...')
    core = OmniCore()
    
    try:
        result = core.start()
        if not result:
            print('⚠ Warning: start() returned False, but checking if components initialized...')
            # Check if components are actually initialized
            if core.state_store and core.state_model:
                print('✅ Components initialized - continuing...')
            else:
                print('❌ Failed to start OMNI Core')
                return
    except Exception as e:
        print(f'❌ Error starting OMNI Core: {e}')
        return
    
    print('✅ OMNI Core started\n')
    
    # Initial status
    print_status(core, 0)
    
    # Run initial demo lock test
    print('\n[INITIAL] Running Demo Lock Test...')
    run_demo_lock_test()
    
    # Periodic tests
    test_count = 1
    test_interval = 30  # Test every 30 seconds
    
    print(f'\nStarting periodic tests (every {test_interval} seconds)...')
    print('Press Ctrl+C to stop\n')
    
    try:
        while True:
            time.sleep(test_interval)
            
            # Status update
            print_status(core, test_count)
            
            # Run demo lock test every 3rd interval
            if test_count % 3 == 0:
                run_demo_lock_test()
            
            test_count += 1
            
    except KeyboardInterrupt:
        print('\n\nStopping...')
        core.stop()
        print('✅ Stopped cleanly')
        print('\n' + '='*70)
        print('DEMO COMPLETE')
        print('='*70)

if __name__ == "__main__":
    main()
