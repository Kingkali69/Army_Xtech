#!/usr/bin/env python3
# cli_test_runner.py
# G.Legion Framework - CLI Test Runner

import asyncio
import argparse
import json
import sys
import os
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Import the engine core and SP subsystem
try:
    from engine_core import EngineCore
    ENGINE_AVAILABLE = True
except ImportError:
    ENGINE_AVAILABLE = False

try:
    from sp_subsystem_v5_complete import EnhancedGhostSyncProtocol, SyncCoordinator
    SP_AVAILABLE = True
except ImportError:
    SP_AVAILABLE = False

class CLITestRunner:
    """CLI Test Runner for G.Legion Framework"""
    
    def __init__(self):
        self.logger = self._setup_logging()
        self.engine = None
        self.sync_coordinator = None
        
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for CLI"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[logging.StreamHandler(sys.stdout)]
        )
        return logging.getLogger("GLegion.CLI")
    
    async def start_engine(self, config_path: str = "config/engine_config.yaml") -> Dict[str, Any]:
        """Start the G.Legion engine"""
        if not ENGINE_AVAILABLE:
            return {
                'status': 'error',
                'message': 'Engine core not available - check engine_core.py'
            }
        
        try:
            self.logger.info("Starting G.Legion Engine...")
            
            # Create engine instance
            self.engine = EngineCore(config_path)
            
            # Initialize and start
            await self.engine.initialize()
            await self.engine.start()
            
            # Get status
            status = self.engine.get_status()
            
            return {
                'status': 'success',
                'message': 'G.Legion Engine started successfully',
                'engine_status': status,
                'node_id': status.get('node_id'),
                'subsystems_running': status.get('subsystems', {})
            }
            
        except Exception as e:
            self.logger.error(f"Failed to start engine: {e}")
            return {
                'status': 'error',
                'message': f'Engine startup failed: {str(e)}',
                'error': str(e)
            }
    
    async def stop_engine(self) -> Dict[str, Any]:
        """Stop the G.Legion engine"""
        if not self.engine:
            return {
                'status': 'error',
                'message': 'No engine running'
            }
        
        try:
            self.logger.info("Stopping G.Legion Engine...")
            await self.engine.stop()
            self.engine = None
            
            return {
                'status': 'success',
                'message': 'G.Legion Engine stopped'
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Engine stop failed: {str(e)}',
                'error': str(e)
            }
    
    async def get_engine_status(self) -> Dict[str, Any]:
        """Get engine status"""
        if not self.engine:
            return {
                'status': 'not_running',
                'message': 'Engine not started'
            }
        
        try:
            status = self.engine.get_status()
            return {
                'status': 'success',
                'engine_status': status
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Failed to get status: {str(e)}',
                'error': str(e)
            }
    
    async def init_sync_coordinator(self, config_file: str = None) -> Dict[str, Any]:
        """Initialize standalone sync coordinator"""
        if not SP_AVAILABLE:
            return {
                'status': 'error',
                'message': 'SP Subsystem not available - check sp_subsystem_v5_complete.py'
            }
        
        try:
            self.logger.info("Initializing Sync Coordinator...")
            
            # Create sync coordinator
            self.sync_coordinator = SyncCoordinator(config_file)
            await self.sync_coordinator.initialize()
            
            status = await self.sync_coordinator.get_sync_status()
            
            return {
                'status': 'success',
                'message': 'Sync Coordinator initialized',
                'sync_status': status
            }
            
        except Exception as e:
            self.logger.error(f"Failed to initialize sync coordinator: {e}")
            return {
                'status': 'error',
                'message': f'Sync coordinator initialization failed: {str(e)}',
                'error': str(e)
            }
    
    async def perform_sync(self, peers: Optional[str] = None, dry_run: bool = False) -> Dict[str, Any]:
        """Perform sync operation"""
        # Try engine first, then standalone coordinator
        if self.engine and 'sp_sub' in self.engine.subsystems:
            try:
                sp_subsystem = self.engine.subsystems['sp_sub']
                if hasattr(sp_subsystem, 'coordinator'):
                    coordinator = sp_subsystem.coordinator
                elif hasattr(sp_subsystem, 'sync'):
                    # Use the sync method directly
                    peer_list = peers.split(',') if peers else None
                    return await sp_subsystem.sync(peer_list, dry_run)
                else:
                    return {
                        'status': 'error',
                        'message': 'SP subsystem does not support sync operations'
                    }
            except Exception as e:
                return {
                    'status': 'error',
                    'message': f'Engine sync failed: {str(e)}',
                    'error': str(e)
                }
        
        elif self.sync_coordinator:
            try:
                peer_list = peers.split(',') if peers else None
                result = await self.sync_coordinator.start_sync_cycle(peer_list, dry_run)
                return {
                    'status': 'success',
                    'sync_result': result
                }
            except Exception as e:
                return {
                    'status': 'error',
                    'message': f'Standalone sync failed: {str(e)}',
                    'error': str(e)
                }
        
        else:
            # Initialize standalone coordinator and try sync
            init_result = await self.init_sync_coordinator()
            if init_result['status'] == 'success':
                return await self.perform_sync(peers, dry_run)
            else:
                return init_result
    
    async def get_sync_status(self) -> Dict[str, Any]:
        """Get sync status"""
        # Try engine first, then standalone coordinator
        if self.engine and 'sp_sub' in self.engine.subsystems:
            try:
                sp_subsystem = self.engine.subsystems['sp_sub']
                if hasattr(sp_subsystem, 'get_status'):
                    status = await sp_subsystem.get_status()
                    return {
                        'status': 'success',
                        'sync_status': status
                    }
                else:
                    return {
                        'status': 'error',
                        'message': 'SP subsystem does not support status operations'
                    }
            except Exception as e:
                return {
                    'status': 'error',
                    'message': f'Engine sync status failed: {str(e)}',
                    'error': str(e)
                }
        
        elif self.sync_coordinator:
            try:
                status = await self.sync_coordinator.get_sync_status()
                return {
                    'status': 'success',
                    'sync_status': status
                }
            except Exception as e:
                return {
                    'status': 'error',
                    'message': f'Standalone sync status failed: {str(e)}',
                    'error': str(e)
                }
        
        else:
            return {
                'status': 'not_initialized',
                'message': 'No sync coordinator available'
            }
    
    async def create_test_delta(self, user_id: str = None) -> Dict[str, Any]:
        """Create test delta for demonstration"""
        if self.sync_coordinator:
            try:
                delta = await self.sync_coordinator.create_test_delta(user_id)
                return {
                    'status': 'success',
                    'delta': delta
                }
            except Exception as e:
                return {
                    'status': 'error',
                    'message': f'Failed to create test delta: {str(e)}',
                    'error': str(e)
                }
        else:
            return {
                'status': 'error',
                'message': 'No sync coordinator available'
            }
    
    def print_result(self, result: Dict[str, Any], command: str):
        """Print formatted result"""
        print(f"\n=== {command.upper()} RESULT ===")
        
        if result.get('status') == 'success':
            print("✅ SUCCESS")
            if 'message' in result:
                print(f"Message: {result['message']}")
        else:
            print("❌ FAILED")
            if 'message' in result:
                print(f"Error: {result['message']}")
        
        # Print detailed information
        for key, value in result.items():
            if key not in ['status', 'message']:
                if isinstance(value, dict):
                    print(f"\n{key.replace('_', ' ').title()}:")
                    for sub_key, sub_value in value.items():
                        if isinstance(sub_value, dict):
                            print(f"  {sub_key}: {json.dumps(sub_value, indent=4)}")
                        else:
                            print(f"  {sub_key}: {sub_value}")
                else:
                    print(f"{key.replace('_', ' ').title()}: {value}")
        
        print("=" * 50)
    
    async def run_interactive_mode(self):
        """Run interactive CLI mode"""
        print("🚀 G.Legion Interactive CLI")
        print("Commands: start, stop, status, sync, sync-status, test-delta, help, exit")
        
        while True:
            try:
                command = input("\nG.Legion> ").strip().lower()
                
                if command == 'exit':
                    break
                elif command == 'help':
                    self._print_help()
                elif command == 'start':
                    result = await self.start_engine()
                    self.print_result(result, 'start')
                elif command == 'stop':
                    result = await self.stop_engine()
                    self.print_result(result, 'stop')
                elif command == 'status':
                    result = await self.get_engine_status()
                    self.print_result(result, 'status')
                elif command == 'sync':
                    peers = input("Enter peers (comma-separated, or press Enter for auto-discovery): ").strip()
                    dry_run = input("Dry run? (y/N): ").strip().lower() == 'y'
                    result = await self.perform_sync(peers if peers else None, dry_run)
                    self.print_result(result, 'sync')
                elif command == 'sync-status':
                    result = await self.get_sync_status()
                    self.print_result(result, 'sync-status')
                elif command == 'test-delta':
                    user_id = input("Enter user ID (or press Enter for auto): ").strip()
                    result = await self.create_test_delta(user_id if user_id else None)
                    self.print_result(result, 'test-delta')
                else:
                    print(f"Unknown command: {command}")
                    self._print_help()
                    
            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except EOFError:
                break
            except Exception as e:
                print(f"Error: {e}")
    
    def _print_help(self):
        """Print help information"""
        print("""
Available Commands:
  start       - Start G.Legion Engine
  stop        - Stop G.Legion Engine
  status      - Get engine status
  sync        - Perform sync operation
  sync-status - Get sync status
  test-delta  - Create test delta
  help        - Show this help
  exit        - Exit CLI
        """)


def create_parser():
    """Create argument parser"""
    parser = argparse.ArgumentParser(description='G.Legion Framework CLI Test Runner')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Start command
    start_parser = subparsers.add_parser('start', help='Start G.Legion Engine')
    start_parser.add_argument('--config', '-c', default='config/engine_config.yaml',
                             help='Engine configuration file')
    
    # Stop command
    subparsers.add_parser('stop', help='Stop G.Legion Engine')
    
    # Status command
    subparsers.add_parser('status', help='Get engine status')
    
    # Sync command
    sync_parser = subparsers.add_parser('sync', help='Perform sync operation')
    sync_parser.add_argument('--peers', '-p', help='Comma-separated list of peer addresses')
    sync_parser.add_argument('--dry-run', '-d', action='store_true', help='Perform dry run')
    sync_parser.add_argument('--config', '-c', help='Sync configuration file')
    
    # Sync status command
    subparsers.add_parser('sync-status', help='Get sync status')
    
    # Test delta command
    test_delta_parser = subparsers.add_parser('test-delta', help='Create test delta')
    test_delta_parser.add_argument('--user-id', '-u', help='User ID for test delta')
    
    # Interactive mode
    subparsers.add_parser('interactive', help='Start interactive CLI mode')
    
    return parser


async def main():
    """Main CLI entry point"""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    runner = CLITestRunner()
    
    try:
        if args.command == 'start':
            result = await runner.start_engine(args.config)
            runner.print_result(result, 'start')
            
            # Keep engine running until interrupted
            if result.get('status') == 'success':
                print("\nEngine is running. Press Ctrl+C to stop...")
                try:
                    while True:
                        await asyncio.sleep(1)
                except KeyboardInterrupt:
                    print("\nStopping engine...")
                    stop_result = await runner.stop_engine()
                    runner.print_result(stop_result, 'stop')
        
        elif args.command == 'stop':
            result = await runner.stop_engine()
            runner.print_result(result, 'stop')
        
        elif args.command == 'status':
            result = await runner.get_engine_status()
            runner.print_result(result, 'status')
        
        elif args.command == 'sync':
            # Initialize sync coordinator if needed
            if hasattr(args, 'config') and args.config:
                init_result = await runner.init_sync_coordinator(args.config)
                if init_result['status'] != 'success':
                    runner.print_result(init_result, 'sync-init')
                    return
            
            result = await runner.perform_sync(args.peers, args.dry_run)
            runner.print_result(result, 'sync')
        
        elif args.command == 'sync-status':
            result = await runner.get_sync_status()
            runner.print_result(result, 'sync-status')
        
        elif args.command == 'test-delta':
            result = await runner.create_test_delta(args.user_id)
            runner.print_result(result, 'test-delta')
        
        elif args.command == 'interactive':
            await runner.run_interactive_mode()
    
    except KeyboardInterrupt:
        print("\nOperation cancelled")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        # Cleanup
        if runner.engine:
            try:
                await runner.stop_engine()
            except Exception:
                pass


if __name__ == "__main__":
    # Ensure we can import required modules
    if not ENGINE_AVAILABLE and not SP_AVAILABLE:
        print("❌ Neither engine_core.py nor sp_subsystem_v5_complete.py are available!")
        print("Please ensure at least one of these files exists in the current directory.")
        sys.exit(1)
    
    if not ENGINE_AVAILABLE:
        print("⚠️  engine_core.py not available - engine commands will be limited")
    
    if not SP_AVAILABLE:
        print("⚠️  sp_subsystem_v5_complete.py not available - sync commands will be limited")
    
    asyncio.run(main())
