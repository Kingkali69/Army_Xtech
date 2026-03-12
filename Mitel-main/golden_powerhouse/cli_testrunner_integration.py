"""
Test Runner Integration Module for G.Legion CLI

This module provides integration for test runner commands into the main CLI,
allowing sharing of engine instance and subsystem state.
"""

import asyncio
import argparse
import json
import logging
import sys
import time
from typing import Dict, Any, Optional, List, Callable, Awaitable

logger = logging.getLogger("G.Legion.TestRunner")

class TestRunnerIntegration:
    """Test Runner Integration for G.Legion Engine CLI"""
    
    def __init__(self, engine=None):
        """Initialize test runner with optional engine reference"""
        self.engine = engine
        self.last_test_result = None
        self.interactive_mode = False
    
    def set_engine(self, engine):
        """Set engine reference after initialization"""
        self.engine = engine
    
    def register_commands(self, subparsers):
        """Register test runner commands with the main CLI parser"""
        # Sync test commands
        sync_test_parser = subparsers.add_parser('sync-test', help='Synchronization testing commands')
        sync_test_subparsers = sync_test_parser.add_subparsers(dest='sync_test_command', help='Sync test commands')
        
        # Sync status command
        sync_status_parser = sync_test_subparsers.add_parser('status', help='Get sync status')
        sync_status_parser.add_argument('--json', action='store_true', help='Output in JSON format')
        
        # Test delta command
        test_delta_parser = sync_test_subparsers.add_parser('delta', help='Test delta creation and application')
        test_delta_parser.add_argument('--entity', '-e', required=True, help='Entity ID for the delta')
        test_delta_parser.add_argument('--operation', '-o', required=True, 
                                      choices=['create', 'update', 'delete'], 
                                      help='Operation type')
        test_delta_parser.add_argument('--data', '-d', help='JSON data for the delta')
        test_delta_parser.add_argument('--no-apply', action='store_true', help='Create but don\'t apply the delta')
        test_delta_parser.add_argument('--json', action='store_true', help='Output in JSON format')
        
        # Peer discovery test
        discover_parser = sync_test_subparsers.add_parser('discover', help='Test peer discovery')
        discover_parser.add_argument('--timeout', type=int, default=5, help='Discovery timeout in seconds')
        discover_parser.add_argument('--json', action='store_true', help='Output in JSON format')
        
        # Interactive test mode
        interactive_parser = sync_test_subparsers.add_parser('interactive', help='Enter interactive test mode')
        interactive_parser.add_argument('--scenario', help='Run a specific test scenario')
        
        # Register performance test commands
        perf_test_parser = subparsers.add_parser('perf-test', help='Performance testing commands')
        perf_test_subparsers = perf_test_parser.add_subparsers(dest='perf_test_command', help='Performance test commands')
        
        # Delta throughput test
        throughput_parser = perf_test_subparsers.add_parser('throughput', help='Test delta throughput')
        throughput_parser.add_argument('--count', '-c', type=int, default=100, help='Number of deltas to generate')
        throughput_parser.add_argument('--size', '-s', type=int, default=1024, help='Size of each delta in bytes')
        throughput_parser.add_argument('--parallel', '-p', type=int, default=1, help='Number of parallel operations')
        throughput_parser.add_argument('--json', action='store_true', help='Output in JSON format')
        
        # Network latency test
        latency_parser = perf_test_subparsers.add_parser('latency', help='Test network latency')
        latency_parser.add_argument('--peers', nargs='+', help='Specific peers to test')
        latency_parser.add_argument('--rounds', '-r', type=int, default=10, help='Number of test rounds')
        latency_parser.add_argument('--json', action='store_true', help='Output in JSON format')
        
        # Register integration test commands
        integration_test_parser = subparsers.add_parser('integration-test', help='Integration testing commands')
        integration_test_subparsers = integration_test_parser.add_subparsers(dest='integration_test_command', help='Integration test commands')
        
        # Test sync with authentication
        auth_sync_parser = integration_test_subparsers.add_parser('auth-sync', help='Test sync with authentication')
        auth_sync_parser.add_argument('--user', required=True, help='Username for authentication')
        auth_sync_parser.add_argument('--password', help='Password (will prompt if not provided)')
        auth_sync_parser.add_argument('--json', action='store_true', help='Output in JSON format')
        
        # E2E test command
        e2e_parser = integration_test_subparsers.add_parser('e2e', help='Run end-to-end test sequence')
        e2e_parser.add_argument('--scenario', required=True, help='Test scenario to run')
        e2e_parser.add_argument('--timeout', type=int, default=300, help='Test timeout in seconds')
        e2e_parser.add_argument('--json', action='store_true', help='Output in JSON format')
        
        # Register batch testing command
        batch_test_parser = subparsers.add_parser('batch-test', help='Run batch tests')
        batch_test_parser.add_argument('--file', '-f', required=True, help='Test definition file')
        batch_test_parser.add_argument('--output', '-o', help='Output file for results')
        batch_test_parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
        batch_test_parser.add_argument('--json', action='store_true', help='Output in JSON format')
    
    async def handle_command(self, args):
        """Handle test runner commands"""
        if not self.engine:
            logger.error("Engine reference not available")
            return 1
        
        # Dispatch to appropriate command handler
        if hasattr(args, 'command'):
            if args.command == 'sync-test':
                return await self._handle_sync_test_command(args)
            elif args.command == 'perf-test':
                return await self._handle_perf_test_command(args)
            elif args.command == 'integration-test':
                return await self._handle_integration_test_command(args)
            elif args.command == 'batch-test':
                return await self._handle_batch_test_command(args)
        
        logger.error("Unknown test command")
        return 1
    
    async def _handle_sync_test_command(self, args):
        """Handle sync test commands"""
        if not hasattr(args, 'sync_test_command') or not args.sync_test_command:
            logger.error("No sync test command specified")
            return 1
            
        if args.sync_test_command == 'status':
            return await self._cmd_sync_status(args)
        elif args.sync_test_command == 'delta':
            return await self._cmd_test_delta(args)
        elif args.sync_test_command == 'discover':
            return await self._cmd_discover(args)
        elif args.sync_test_command == 'interactive':
            return await self._cmd_interactive(args)
        
        logger.error(f"Unknown sync test command: {args.sync_test_command}")
        return 1
    
    async def _handle_perf_test_command(self, args):
        """Handle performance test commands"""
        if not hasattr(args, 'perf_test_command') or not args.perf_test_command:
            logger.error("No performance test command specified")
            return 1
            
        if args.perf_test_command == 'throughput':
            return await self._cmd_test_throughput(args)
        elif args.perf_test_command == 'latency':
            return await self._cmd_test_latency(args)
        
        logger.error(f"Unknown performance test command: {args.perf_test_command}")
        return 1
    
    async def _handle_integration_test_command(self, args):
        """Handle integration test commands"""
        if not hasattr(args, 'integration_test_command') or not args.integration_test_command:
            logger.error("No integration test command specified")
            return 1
            
        if args.integration_test_command == 'auth-sync':
            return await self._cmd_test_auth_sync(args)
        elif args.integration_test_command == 'e2e':
            return await self._cmd_test_e2e(args)
        
        logger.error(f"Unknown integration test command: {args.integration_test_command}")
        return 1
    
    async def _handle_batch_test_command(self, args):
        """Handle batch test command"""
        return await self._cmd_batch_test(args)
    
    async def _cmd_sync_status(self, args):
        """Get sync subsystem status"""
        try:
            if 'sp_sub' not in self.engine.subsystems:
                logger.error("SP-SUB subsystem not available")
                return 1
            
            # Get status from the sync coordinator
            sp_sub = self.engine.subsystems['sp_sub']
            status = await sp_sub.get_sync_status()
            
            if args.json:
                print(json.dumps(status, indent=2, default=str))
            else:
                print("Synchronization Status:")
                print(f"  Node ID: {status.get('node_id')}")
                print(f"  Last Sync: {status.get('last_sync_time', 'Never')}")
                print(f"  Sync In Progress: {status.get('sync_in_progress', False)}")
                
                online_peers = status.get('online_peers', 0)
                known_peers = status.get('known_peers', 0)
                print(f"  Peers: {online_peers} online, {known_peers} known")
                
                print(f"  Pending Conflicts: {status.get('pending_conflicts', 0)}")
                print(f"  Offline Queue Size: {status.get('offline_queue_size', 0)}")
            
            return 0
            
        except Exception as e:
            logger.error(f"Failed to get sync status: {e}")
            return 1
    
    async def _cmd_test_delta(self, args):
        """Test delta creation and application"""
        try:
            if 'sp_sub' not in self.engine.subsystems:
                logger.error("SP-SUB subsystem not available")
                return 1
            
            sp_sub = self.engine.subsystems['sp_sub']
            
            # Parse data if provided
            data = {}
            if args.data:
                try:
                    data = json.loads(args.data)
                except json.JSONDecodeError:
                    logger.error("Invalid JSON data")
                    return 1
            
            # Create delta
            if not hasattr(sp_sub, 'delta_engine') or not sp_sub.delta_engine:
                logger.error("Delta engine not available in SP-SUB")
                return 1
                
            delta = await sp_sub.delta_engine.create_manual_delta(
                entity_id=args.entity,
                operation=args.operation,
                data=data
            )
            
            # Apply the delta if requested
            apply_result = None
            if not args.no_apply:
                apply_result = await sp_sub.verify_and_apply([delta])
            
            # Store result for interactive mode
            self.last_test_result = {
                'delta': delta,
                'apply_result': apply_result
            }
            
            if args.json:
                print(json.dumps({
                    'delta': delta,
                    'apply_result': apply_result
                }, indent=2, default=str))
            else:
                print("Delta Test:")
                print(f"  Entity: {args.entity}")
                print(f"  Operation: {args.operation}")
                print(f"  Delta ID: {delta.get('id', 'N/A')}")
                
                if not args.no_apply:
                    print("  Application Result:")
                    if apply_result.get('success', False):
                        print(f"    Success: {apply_result.get('success')}")
                        print(f"    Applied: {apply_result.get('applied', 0)}")
                        print(f"    Failed: {apply_result.get('failed', 0)}")
                    else:
                        print(f"    Failed: {apply_result.get('error', 'Unknown error')}")
            
            return 0 if not apply_result or apply_result.get('success', False) else 1
            
        except Exception as e:
            logger.error(f"Delta test failed: {e}")
            return 1
    
    async def _cmd_discover(self, args):
        """Test peer discovery"""
        try:
            if 'sp_sub' not in self.engine.subsystems:
                logger.error("SP-SUB subsystem not available")
                return 1
            
            sp_sub = self.engine.subsystems['sp_sub']
            
            if not hasattr(sp_sub, 'sync_protocol') or not sp_sub.sync_protocol:
                logger.error("Sync protocol not available in SP-SUB")
                return 1
            
            # Trigger discovery
            print(f"Discovering peers (timeout: {args.timeout}s)...")
            peers = await sp_sub.sync_protocol.discover_peers()
            
            # Wait for discovery to complete
            await asyncio.sleep(args.timeout)
            
            # Get peer info
            peer_info = {}
            if hasattr(sp_sub.sync_protocol, 'get_known_peers'):
                peer_info = sp_sub.sync_protocol.get_known_peers()
            
            # Format output
            result = {
                'peers_found': len(peers),
                'peer_ids': peers,
                'peer_details': peer_info
            }
            
            if args.json:
                print(json.dumps(result, indent=2, default=str))
            else:
                print(f"Discovery complete: {len(peers)} peers found")
                if peers:
                    print("\nPeer Details:")
                    for peer_id, info in peer_info.items():
                        print(f"  {peer_id}:")
                        if isinstance(info, dict):
                            for key, value in info.items():
                                if key != 'capabilities':  # Skip verbose lists
                                    print(f"    {key}: {value}")
                        else:
                            print(f"    {info}")
            
            return 0
            
        except Exception as e:
            logger.error(f"Peer discovery test failed: {e}")
            return 1
    
    async def _cmd_interactive(self, args):
        """Enter interactive test mode"""
        if 'sp_sub' not in self.engine.subsystems:
            logger.error("SP-SUB subsystem not available")
            return 1
        
        # Run a specific scenario if provided
        if hasattr(args, 'scenario') and args.scenario:
            return await self._run_interactive_scenario(args.scenario)
        
        try:
            print("Entering interactive test mode. Type 'help' for commands, 'exit' to quit.")
            self.interactive_mode = True
            
            while self.interactive_mode:
                try:
                    command = input("test> ").strip()
                    
                    if command == 'exit':
                        self.interactive_mode = False
                        print("Exiting interactive mode")
                        
                    elif command == 'help':
                        self._print_interactive_help()
                        
                    elif command.startswith('delta'):
                        await self._handle_interactive_delta_command(command)
                        
                    elif command == 'status':
                        await self._cmd_sync_status(argparse.Namespace(json=False))
                        
                    elif command == 'discover':
                        await self._cmd_discover(argparse.Namespace(timeout=3, json=False))
                        
                    elif command == 'peers':
                        await self._display_peers()
                        
                    elif command.startswith('scenario'):
                        parts = command.split(maxsplit=1)
                        if len(parts) > 1:
                            await self._run_interactive_scenario(parts[1])
                        else:
                            print("Error: Missing scenario name. Usage: scenario <name>")
                            
                    else:
                        print(f"Unknown command: '{command}'. Type 'help' for available commands.")
                        
                except KeyboardInterrupt:
                    print("\nUse 'exit' to quit interactive mode")
                except EOFError:
                    self.interactive_mode = False
                    print("\nExiting interactive mode")
                except Exception as e:
                    print(f"Error executing command: {e}")
                    
            return 0
            
        except Exception as e:
            logger.error(f"Interactive mode error: {e}")
            self.interactive_mode = False
            return 1
    
    def _print_interactive_help(self):
        """Print help for interactive mode"""
        print("\nAvailable Commands:")
        print("  help                - Display this help message")
        print("  exit                - Exit interactive mode")
        print("  status              - Display sync status")
        print("  discover            - Discover peers")
        print("  peers               - List known peers")
        print("  delta <entity> <op> [data] - Create and test a delta")
        print("  scenario <name>     - Run a test scenario")
        print("\nExamples:")
        print("  delta user123 update {\"name\":\"New Name\"}")
        print("  delta file123 delete")
        print("  scenario basic-sync")
    
    async def _handle_interactive_delta_command(self, command):
        """Handle delta command in interactive mode"""
        parts = command.split(maxsplit=3)
        
        if len(parts) < 3:
            print("Error: Invalid delta command")
            print("Usage: delta <entity> <operation> [data]")
            return
        
        entity = parts[1]
        operation = parts[2]
        
        if operation not in ['create', 'update', 'delete']:
            print(f"Error: Invalid operation '{operation}'")
            print("Valid operations: create, update, delete")
            return
        
        data = {}
        if len(parts) > 3:
            try:
                data = json.loads(parts[3])
            except json.JSONDecodeError:
                print("Error: Invalid JSON data")
                return
        
        # Create delta command args
        args = argparse.Namespace(
            entity=entity,
            operation=operation,
            data=json.dumps(data) if data else None,
            no_apply=False,
            json=False
        )
        
        await self._cmd_test_delta(args)
    
    async def _display_peers(self):
        """Display known peers in interactive mode"""
        if 'sp_sub' not in self.engine.subsystems:
            print("SP-SUB subsystem not available")
            return
        
        sp_sub = self.engine.subsystems['sp_sub']
        
        if not hasattr(sp_sub, 'sync_protocol') or not sp_sub.sync_protocol:
            print("Sync protocol not available in SP-SUB")
            return
        
        if not hasattr(sp_sub.sync_protocol, 'get_known_peers'):
            print("Peer information not available")
            return
        
        peers = sp_sub.sync_protocol.get_known_peers()
        
        print(f"\nKnown Peers ({len(peers)}):")
        if not peers:
            print("  No peers found")
            return
            
        for peer_id, info in peers.items():
            print(f"  {peer_id}:")
            if isinstance(info, dict):
                for key, value in info.items():
                    if key != 'capabilities':  # Skip verbose lists
                        print(f"    {key}: {value}")
            else:
                print(f"    {info}")
    
    async def _run_interactive_scenario(self, scenario):
        """Run a test scenario in interactive mode"""
        print(f"Running test scenario: {scenario}")
        
        if scenario == "basic-sync":
            return await self._scenario_basic_sync()
        elif scenario == "crdt-conflicts":
            return await self._scenario_crdt_conflicts()
        elif scenario == "mesh-discovery":
            return await self._scenario_mesh_discovery()
        else:
            print(f"Unknown scenario: {scenario}")
            return 1
    
    async def _scenario_basic_sync(self):
        """Run a basic sync scenario"""
        try:
            print("Running Basic Sync Scenario")
            print("Step 1: Create a test delta")
            create_args = argparse.Namespace(
                entity="test-entity",
                operation="create",
                data='{"name":"Test Entity","type":"scenario"}',
                no_apply=False,
                json=False
            )
            await self._cmd_test_delta(create_args)
            
            print("\nStep 2: Discover peers")
            discover_args = argparse.Namespace(timeout=3, json=False)
            await self._cmd_discover(discover_args)
            
            print("\nStep 3: Check sync status")
            status_args = argparse.Namespace(json=False)
            await self._cmd_sync_status(status_args)
            
            print("\nStep 4: Update test entity")
            update_args = argparse.Namespace(
                entity="test-entity",
                operation="update",
                data='{"name":"Updated Entity","status":"active"}',
                no_apply=False,
                json=False
            )
            await self._cmd_test_delta(update_args)
            
            print("\nStep 5: Initiate sync with peers")
            if 'sp_sub' in self.engine.subsystems:
                sp_sub = self.engine.subsystems['sp_sub']
                result = await sp_sub.start_sync_cycle(dry_run=False)
                print(f"Sync result: {result.get('status')}")
                print(f"Peers contacted: {result.get('peers_contacted', 0)}")
                print(f"Deltas processed: {result.get('deltas_processed', 0)}")
            else:
                print("SP-SUB not available, skipping sync")
            
            print("\nBasic sync scenario completed")
            return 0
            
        except Exception as e:
            print(f"Error in basic sync scenario: {e}")
            return 1
    
    async def _scenario_crdt_conflicts(self):
        """Run a CRDT conflict resolution scenario"""
        print("CRDT conflict resolution scenario not implemented")
        return 1
    
    async def _scenario_mesh_discovery(self):
        """Run a mesh discovery scenario"""
        print("Mesh discovery scenario not implemented")
        return 1
    
    async def _cmd_test_throughput(self, args):
        """Test delta throughput"""
        try:
            if 'sp_sub' not in self.engine.subsystems:
                logger.error("SP-SUB subsystem not available")
                return 1
            
            sp_sub = self.engine.subsystems['sp_sub']
            
            if not hasattr(sp_sub, 'delta_engine') or not sp_sub.delta_engine:
                logger.error("Delta engine not available in SP-SUB")
                return 1
            
            print(f"Running throughput test with {args.count} deltas, {args.size} bytes each, {args.parallel} parallel operations")
            
            # Generate random data of specified size
            import random
            import string
            
            data_generator = lambda size: {
                'id': ''.join(random.choice(string.ascii_letters) for _ in range(8)),
                'timestamp': time.time(),
                'data': ''.join(random.choice(string.ascii_letters) for _ in range(size - 60))
            }
            
            # Create tasks for parallel execution
            async def create_and_apply_delta(i):
                entity_id = f"perf-test-{i}"
                data = data_generator(args.size)
                
                start_time = time.time()
                delta = await sp_sub.delta_engine.create_manual_delta(entity_id, "create", data)
                create_time = time.time() - start_time
                
                start_time = time.time()
                result = await sp_sub.verify_and_apply([delta])
                apply_time = time.time() - start_time
                
                return {
                    'index': i,
                    'entity_id': entity_id,
                    'create_time': create_time,
                    'apply_time': apply_time,
                    'success': result.get('success', False)
                }
            
            # Execute in batches for parallelism
            all_results = []
            total_start_time = time.time()
            
            for batch_start in range(0, args.count, args.parallel):
                batch_size = min(args.parallel, args.count - batch_start)
                batch_tasks = [create_and_apply_delta(i) for i in range(batch_start, batch_start + batch_size)]
                batch_results = await asyncio.gather(*batch_tasks)
                all_results.extend(batch_results)
                
                # Progress update
                completion = min(100, int((batch_start + batch_size) / args.count * 100))
                print(f"Progress: {completion}% ({batch_start + batch_size}/{args.count})")
            
            total_time = time.time() - total_start_time
            
            # Calculate statistics
            successful = sum(1 for r in all_results if r.get('success', False))
            avg_create_time = sum(r.get('create_time', 0) for r in all_results) / len(all_results)
            avg_apply_time = sum(r.get('apply_time', 0) for r in all_results) / len(all_results)
            operations_per_second = args.count / total_time if total_time > 0 else 0
            
            result = {
                'total_operations': args.count,
                'successful_operations': successful,
                'failed_operations': args.count - successful,
                'total_time_seconds': total_time,
                'operations_per_second': operations_per_second,
                'avg_create_time_seconds': avg_create_time,
                'avg_apply_time_seconds': avg_apply_time,
                'data_size_bytes': args.size,
                'parallelism': args.parallel
            }
            
            if args.json:
                print(json.dumps(result, indent=2))
            else:
                print("\nThroughput Test Results:")
                print(f"  Total deltas: {args.count}")
                print(f"  Successful: {successful} ({(successful/args.count)*100:.1f}%)")
                print(f"  Failed: {args.count - successful}")
                print(f"  Total time: {total_time:.2f} seconds")
                print(f"  Operations per second: {operations_per_second:.2f}")
                print(f"  Avg create time: {avg_create_time*1000:.2f} ms")
                print(f"  Avg apply time: {avg_apply_time*1000:.2f} ms")
            
            return 0
            
        except Exception as e:
            logger.error(f"Throughput test failed: {e}")
            return 1
    
    async def _cmd_test_latency(self, args):
        """Test network latency"""
        print("Network latency test not implemented")
        return 1
    
    async def _cmd_test_auth_sync(self, args):
        """Test sync with authentication"""
        print("Auth sync test not implemented")
        return 1
    
    async def _cmd_test_e2e(self, args):
        """Run end-to-end test sequence"""
        print("End-to-end test not implemented")
        return 1
    
    async def _cmd_batch_test(self, args):
        """Run batch tests"""
        try:
            if not args.file or not os.path.exists(args.file):
                logger.error(f"Test definition file not found: {args.file}")
                return 1
            
            print(f"Loading test definitions from {args.file}")
            
            # Load test definitions
            with open(args.file, 'r') as f:
                test_definitions = json.load(f)
            
            if not isinstance(test_definitions, list):
                logger.error("Invalid test definition format - expected array of tests")
                return 1
            
            # Run each test
            results = []
            for i, test in enumerate(test_definitions):
                test_name = test.get('name', f"Test {i+1}")
                test_type = test.get('type')
                test_params = test.get('parameters', {})
                
                if args.verbose:
                    print(f"\nRunning test: {test_name} ({test_type})")
                else:
                    print(f"Running test: {test_name}")
                
                # Execute test based on type
                start_time = time.time()
                success = False
                error_message = None
                
                try:
                    if test_type == 'delta':
                        args = argparse.Namespace(
                            entity=test_params.get('entity', 'test-entity'),
                            operation=test_params.get('operation', 'create'),
                            data=json.dumps(test_params.get('data', {})),
                            no_apply=False,
                            json=True
                        )
                        exit_code = await self._cmd_test_delta(args)
                        success = exit_code == 0
                        
                    elif test_type == 'sync':
                        if 'sp_sub' in self.engine.subsystems:
                            sp_sub = self.engine.subsystems['sp_sub']
                            dry_run = test_params.get('dry_run', False)
                            peers = test_params.get('peers')
                            
                            result = await sp_sub.start_sync_cycle(
                                peers=peers,
                                dry_run=dry_run
                            )
                            
                            success = result.get('status') == 'success'
                            if not success:
                                error_message = result.get('error', 'Sync failed')
                        else:
                            error_message = "SP-SUB not available"
                            success = False
                            
                    elif test_type == 'discover':
                        args = argparse.Namespace(
                            timeout=test_params.get('timeout', 3),
                            json=True
                        )
                        exit_code = await self._cmd_discover(args)
                        success = exit_code == 0
                        
                    else:
                        error_message = f"Unknown test type: {test_type}"
                        success = False
                        
                except Exception as e:
                    error_message = str(e)
                    success = False
                
                # Record test results
                duration = time.time() - start_time
                result = {
                    'name': test_name,
                    'type': test_type,
                    'success': success,
                    'duration': duration,
                    'error': error_message
                }
                
                results.append(result)
                
                # Print result
                if args.verbose or not success:
                    status = "SUCCESS" if success else "FAILED"
                    print(f"  Result: {status} ({duration:.2f}s)")
                    if error_message:
                        print(f"  Error: {error_message}")
            
            # Output final summary
            total_tests = len(results)
            successful_tests = sum(1 for r in results if r.get('success', False))
            total_duration = sum(r.get('duration', 0) for r in results)
            
            summary = {
                'total_tests': total_tests,
                'successful_tests': successful_tests,
                'failed_tests': total_tests - successful_tests,
                'total_duration': total_duration,
                'tests': results
            }
            
            if args.output:
                with open(args.output, 'w') as f:
                    json.dump(summary, f, indent=2)
                print(f"\nDetailed results written to {args.output}")
            
            if args.json:
                print(json.dumps(summary, indent=2))
            else:
                print("\nBatch Test Summary:")
                print(f"  Total tests: {total_tests}")
                print(f"  Successful: {successful_tests} ({(successful_tests/total_tests)*100:.1f}%)")
                print(f"  Failed: {total_tests - successful_tests}")
                print(f"  Total duration: {total_duration:.2f} seconds")
            
            return 0 if successful_tests == total_tests else 1
            
        except Exception as e:
            logger.error(f"Batch test failed: {e}")
            return 1
