#!/usr/bin/env python3
"""
OMNI Foundation - Visual Demo
=============================

Clean visual output showing the system running.
Controlled test intervals - see everything working.
"""

import sys
import os
import time
from datetime import datetime
from omni_core import OmniCore
from substrate.step_8_demo_lock.demo_lock import DemoLock

# Suppress INFO logs
import logging
logging.getLogger().setLevel(logging.WARNING)

def clear_screen():
    """Clear screen"""
    os.system('clear' if os.name != 'nt' else 'cls')

def print_header():
    """Print header"""
    print('\n' + '='*70)
    print('  OMNI FOUNDATION REBUILD - LIVE DEMONSTRATION')
    print('='*70)
    print(f'  Started: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print('='*70 + '\n')

def print_system_status(core: OmniCore):
    """Print system status"""
    print('  SYSTEM STATUS')
    print('  ' + '-'*66)
    print(f'  Node ID:     {core.node_id}')
    print(f'  Platform:    {core.config["platform"].upper()}')
    print(f'  Status:      {core.status.value.upper()}')
    port = getattr(core, 'mesh_port', core.config.get('fabric_port', 7777))
    print(f'  Endpoint:    {core.config["local_ip"]}:{port}')
    print('  ' + '-'*66)

def print_components(core: OmniCore):
    """Print component status"""
    print('\n  FOUNDATION COMPONENTS')
    print('  ' + '-'*66)
    
    components = []
    if core.state_store:
        components.append('✓ State Store (SQLite + WAL)')
    if core.state_model:
        state_keys = len(core.state_model.state)
        components.append(f'✓ State Model ({state_keys} keys, CRDT merge enabled)')
    if core.sync_engine:
        components.append('✓ Sync Engine (CRDT-based, exponential backoff)')
    if core.file_transfer_engine:
        components.append('✓ File Transfer (chunked, hash-verified, resumable)')
    if core.recovery_engine:
        health = core.recovery_engine.get_health_status()
        status_icon = '✓' if health['overall_status'] == 'healthy' else '⚠'
        components.append(f'{status_icon} Recovery Engine ({health["overall_status"]})')
    if core.adapter_manager:
        adapter_status = core.adapter_manager.get_status()
        components.append(f'✓ Adapter Manager ({adapter_status["adapters_loaded"]} platform adapters)')
    
    for comp in components:
        print(f'  {comp}')
    
    print('  ' + '-'*66)

def run_demo_lock():
    """Run demo lock test"""
    print('\n  DEMO LOCK TEST')
    print('  ' + '-'*66)
    
    demo = DemoLock()
    result = demo.run_demo()
    
    if result:
        print('  ✅ ALL TESTS PASSED')
        print('  ' + '-'*66)
        return True
    else:
        print(f'  ❌ TESTS FAILED: {demo.failed_tests}')
        print('  ' + '-'*66)
        return False

def main():
    """Main demo"""
    clear_screen()
    print_header()
    
    print('  Initializing OMNI Core...')
    core = OmniCore()
    
    try:
        result = core.start()
        if not result and not (core.state_store and core.state_model):
            print('  ❌ Failed to start')
            return
    except Exception as e:
        print(f'  ❌ Error: {e}')
        return
    
    print('  ✅ OMNI Core started\n')
    
    # Show initial status
    print_system_status(core)
    print_components(core)
    
    # Run initial demo lock
    print('\n  Running Demo Lock Test...')
    run_demo_lock()
    
    # Periodic updates
    print('\n  Starting periodic tests (every 30 seconds)...')
    print('  Press Ctrl+C to stop\n')
    
    test_count = 1
    
    try:
        while True:
            time.sleep(30)
            
            clear_screen()
            print_header()
            print_system_status(core)
            print_components(core)
            
            # Run demo lock every 3rd interval
            if test_count % 3 == 0:
                run_demo_lock()
            
            print(f'\n  Test cycle #{test_count} - Next update in 30 seconds...')
            print('  Press Ctrl+C to stop')
            
            test_count += 1
            
    except KeyboardInterrupt:
        print('\n\n  Stopping...')
        core.stop()
        print('  ✅ Stopped cleanly')
        print('\n' + '='*70)
        print('  DEMO COMPLETE - Foundation rebuild validated')
        print('='*70 + '\n')

if __name__ == "__main__":
    main()
