#!/usr/bin/env python3
"""
STEP 7: Adapters Integration
============================

Bridge existing PlatformAdapters with our foundation.
Adapters observe OS events → emit ops → state model → CRDT merge.
Merged state → adapters apply back to OS.

Uses existing PlatformAdapters from backend ecosystem.
"""

import sys
import os
import logging
import threading
import time
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass

# Add paths
base_dir = os.path.dirname(__file__)
substrate_dir = os.path.join(base_dir, '..')
workspace_dir = os.path.join(substrate_dir, '..')
sys.path.insert(0, os.path.join(workspace_dir, 'cloudsync-core-main'))
sys.path.insert(0, os.path.join(substrate_dir, 'step_1_state_store'))
sys.path.insert(0, os.path.join(substrate_dir, 'step_2_state_model'))
sys.path.insert(0, os.path.join(substrate_dir, 'step_3_crdt_merge'))

try:
    from step_1_state_store.state_store import StateOp, OpType
    from step_2_state_model.state_model import StateModel
except ImportError:
    # Fallback: direct import
    import importlib.util
    state_store_path = os.path.join(substrate_dir, 'step_1_state_store', 'state_store.py')
    state_model_path = os.path.join(substrate_dir, 'step_2_state_model', 'state_model.py')
    
    spec = importlib.util.spec_from_file_location("state_store", state_store_path)
    state_store_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(state_store_mod)
    StateOp = state_store_mod.StateOp
    OpType = state_store_mod.OpType
    
    spec = importlib.util.spec_from_file_location("state_model", state_model_path)
    state_model_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(state_model_mod)
    StateModel = state_model_mod.StateModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AdapterBridge:
    """
    Bridge between PlatformAdapters and our foundation.
    
    Flow:
    1. Adapter observes OS event
    2. Bridge creates StateOp
    3. State model applies op (CRDT merge happens)
    4. Merged state → Bridge applies back to OS via adapter
    """
    
    def __init__(self, adapter, state_model: StateModel, node_id: str):
        """
        Initialize adapter bridge.
        
        Args:
            adapter: PlatformAdapter instance
            state_model: State model instance
            node_id: Node ID for ops
        """
        self.adapter = adapter
        self.state_model = state_model
        self.node_id = node_id
        
        # Event handlers
        self.event_handlers: Dict[str, Callable] = {}
        
        # Running state
        self.running = False
        self.observe_thread: Optional[threading.Thread] = None
        
        logger.info(f"[ADAPTER_BRIDGE] Initialized for {adapter.__class__.__name__}")
    
    def start(self):
        """Start adapter bridge"""
        if self.running:
            return
        
        self.running = True
        
        # Initialize adapter
        try:
            if hasattr(self.adapter, 'initialize'):
                import asyncio
                if asyncio.iscoroutinefunction(self.adapter.initialize):
                    asyncio.run(self.adapter.initialize())
                else:
                    self.adapter.initialize()
        except Exception as e:
            logger.warning(f"[ADAPTER_BRIDGE] Adapter initialize failed: {e}")
        
        # Start observation thread
        self.observe_thread = threading.Thread(
            target=self._observe_loop,
            daemon=True,
            name=f"adapter-bridge-{self.adapter.__class__.__name__}"
        )
        self.observe_thread.start()
        logger.info(f"[ADAPTER_BRIDGE] Started")
    
    def stop(self):
        """Stop adapter bridge"""
        self.running = False
        if self.observe_thread:
            self.observe_thread.join(timeout=2)
        logger.info(f"[ADAPTER_BRIDGE] Stopped")
    
    def _observe_loop(self):
        """Observe OS events and emit ops"""
        while self.running:
            try:
                # Get system events from adapter
                if hasattr(self.adapter, 'get_system_events'):
                    try:
                        import asyncio
                        if asyncio.iscoroutinefunction(self.adapter.get_system_events):
                            events = asyncio.run(self.adapter.get_system_events())
                        else:
                            events = self.adapter.get_system_events()
                        
                        # Process events
                        if events:
                            for event in events:
                                self._process_event(event)
                    except Exception as e:
                        logger.debug(f"[ADAPTER_BRIDGE] Failed to get events: {e}")
                
                # Also check for system info updates periodically
                if hasattr(self.adapter, 'get_system_info'):
                    try:
                        info = self.adapter.get_system_info()
                        if info:
                            # Create op for system info
                            self._process_system_info(info)
                    except Exception as e:
                        logger.debug(f"[ADAPTER_BRIDGE] Failed to get system info: {e}")
                
                time.sleep(5)  # Poll interval (less frequent)
                
            except Exception as e:
                logger.debug(f"[ADAPTER_BRIDGE] Observe loop error: {e}")
                time.sleep(5)
    
    def _process_system_info(self, info: Dict[str, Any]):
        """Process system info and create StateOp"""
        try:
            import uuid
            op = StateOp(
                op_id=str(uuid.uuid4()),
                op_type=OpType.SET,
                key=f"system_info.{self.adapter.platform_name}",
                value=info,
                node_id=self.node_id
            )
            self.state_model.apply_op(op)
        except Exception as e:
            logger.debug(f"[ADAPTER_BRIDGE] Failed to process system info: {e}")
    
    def _process_event(self, event):
        """
        Process OS event and create StateOp.
        
        Args:
            event: OS event from adapter
        """
        try:
            # Create StateOp from event
            op = self._event_to_op(event)
            if op:
                # Apply to state model (CRDT merge happens)
                self.state_model.apply_op(op)
                logger.debug(f"[ADAPTER_BRIDGE] Processed event: {event.get('type', 'unknown')}")
        except Exception as e:
            logger.debug(f"[ADAPTER_BRIDGE] Failed to process event: {e}")
    
    def _event_to_op(self, event: Dict[str, Any]) -> Optional[StateOp]:
        """
        Convert OS event to StateOp.
        
        Args:
            event: OS event dict
            
        Returns:
            StateOp or None
        """
        try:
            import uuid
            
            event_type = event.get('type', 'unknown')
            event_data = event.get('data', {})
            
            # Create op key based on event type
            key = f"os_events.{event_type}.{event.get('id', str(uuid.uuid4()))}"
            
            # Create StateOp
            op = StateOp(
                op_id=str(uuid.uuid4()),
                op_type=OpType.SET,
                key=key,
                value={
                    'type': event_type,
                    'data': event_data,
                    'timestamp': event.get('timestamp', time.time()),
                    'source': self.adapter.__class__.__name__
                },
                node_id=self.node_id
            )
            
            return op
            
        except Exception as e:
            logger.debug(f"[ADAPTER_BRIDGE] Failed to convert event to op: {e}")
            return None
    
    def apply_state_to_os(self, state_key: str, value: Any):
        """
        Apply merged state back to OS via adapter.
        
        Args:
            state_key: State key
            value: State value
        """
        try:
            # Check if this is an OS-related state change
            if state_key.startswith('os_events.'):
                # Extract event info
                parts = state_key.split('.')
                if len(parts) >= 2:
                    event_type = parts[1]
                    
                    # Create response action for adapter
                    if hasattr(self.adapter, 'execute_response'):
                        response_action = {
                            'action_type': 'apply_state',
                            'target': state_key,
                            'parameters': {
                                'value': value,
                                'event_type': event_type
                            }
                        }
                        
                        import asyncio
                        if asyncio.iscoroutinefunction(self.adapter.execute_response):
                            asyncio.run(self.adapter.execute_response(response_action))
                        else:
                            self.adapter.execute_response(response_action)
                        
                        logger.debug(f"[ADAPTER_BRIDGE] Applied state to OS: {state_key}")
        except Exception as e:
            logger.debug(f"[ADAPTER_BRIDGE] Failed to apply state to OS: {e}")


class AdapterManager:
    """
    Manages all platform adapters.
    
    Loads appropriate adapter for current platform.
    Bridges adapters with our foundation.
    """
    
    def __init__(self, state_model: StateModel, node_id: str):
        """
        Initialize adapter manager.
        
        Args:
            state_model: State model instance
            node_id: Node ID
        """
        self.state_model = state_model
        self.node_id = node_id
        
        # Adapter bridges
        self.bridges: Dict[str, AdapterBridge] = {}
        
        logger.info(f"[ADAPTER_MANAGER] Initialized")
    
    def load_platform_adapter(self, platform: str):
        """
        Load platform adapter for current platform.
        
        Args:
            platform: Platform name ('linux', 'windows', 'macos', 'android', 'ios')
        """
        try:
            # Try to load from engine_core (simpler, synchronous adapters)
            adapter_path = os.path.join(
                os.path.dirname(__file__), '..', '..', 'cloudsync-core-main',
                'engine_core.py'
            )
            
            if os.path.exists(adapter_path):
                import importlib.util
                spec = importlib.util.spec_from_file_location("engine_core", adapter_path)
                engine_mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(engine_mod)
                
                # Get adapter class based on platform
                adapter_class = None
                if platform == 'linux':
                    adapter_class = getattr(engine_mod, 'LinuxAdapter', None)
                elif platform == 'windows':
                    adapter_class = getattr(engine_mod, 'WindowsAdapter', None)
                elif platform == 'macos' or platform == 'darwin':
                    adapter_class = getattr(engine_mod, 'MacOSAdapter', None)
                elif platform == 'generic':
                    adapter_class = getattr(engine_mod, 'GenericAdapter', None)
                
                # If no specific adapter found, try generic
                if not adapter_class:
                    adapter_class = getattr(engine_mod, 'GenericAdapter', None)
                
                if adapter_class:
                    # Create adapter instance (engine_core adapters take no args)
                    try:
                        adapter = adapter_class()
                    except TypeError:
                        # Some adapters might take platform_name
                        adapter = adapter_class(platform_name=platform)
                    
                    # Create bridge
                    bridge = AdapterBridge(adapter, self.state_model, self.node_id)
                    self.bridges[platform] = bridge
                    
                    logger.info(f"[ADAPTER_MANAGER] Loaded {platform} adapter from engine_core")
                    return bridge
                else:
                    logger.warning(f"[ADAPTER_MANAGER] Adapter class not found for {platform}, using generic")
                    # Fallback to generic adapter
                    GenericAdapter = getattr(engine_mod, 'GenericAdapter', None)
                    if GenericAdapter:
                        try:
                            adapter = GenericAdapter()
                        except TypeError:
                            adapter = GenericAdapter(platform_name=platform)
                        bridge = AdapterBridge(adapter, self.state_model, self.node_id)
                        self.bridges[platform] = bridge
                        logger.info(f"[ADAPTER_MANAGER] Using generic adapter for {platform}")
                        return bridge
                    return None
            else:
                logger.warning(f"[ADAPTER_MANAGER] Engine core file not found")
                return None
                
        except Exception as e:
            logger.error(f"[ADAPTER_MANAGER] Failed to load adapter: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return None
    
    def start_all(self):
        """Start all adapter bridges"""
        for bridge in self.bridges.values():
            bridge.start()
        logger.info(f"[ADAPTER_MANAGER] Started {len(self.bridges)} adapters")
    
    def stop_all(self):
        """Stop all adapter bridges"""
        for bridge in self.bridges.values():
            bridge.stop()
        logger.info(f"[ADAPTER_MANAGER] Stopped all adapters")
    
    def get_status(self) -> Dict[str, Any]:
        """Get adapter manager status"""
        return {
            'adapters_loaded': len(self.bridges),
            'platforms': list(self.bridges.keys()),
            'running': all(bridge.running for bridge in self.bridges.values())
        }


def test_adapter_bridge():
    """Test adapter bridge"""
    import importlib.util
    base_dir = os.path.dirname(__file__)
    substrate_dir = os.path.join(base_dir, '..')
    
    # Import state store
    state_store_path = os.path.join(substrate_dir, 'step_1_state_store', 'state_store.py')
    spec = importlib.util.spec_from_file_location("state_store", state_store_path)
    state_store_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(state_store_mod)
    get_state_store = state_store_mod.get_state_store
    
    # Import state model
    state_model_path = os.path.join(substrate_dir, 'step_2_state_model', 'state_model.py')
    spec = importlib.util.spec_from_file_location("state_model", state_model_path)
    state_model_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(state_model_mod)
    get_state_model = state_model_mod.get_state_model
    
    store = get_state_store(db_path='/tmp/test_adapters.db')
    model = get_state_model(state_store=store, node_id='test_node')
    
    manager = AdapterManager(model, 'test_node')
    
    # Try to load Linux adapter
    bridge = manager.load_platform_adapter('linux')
    if bridge:
        print('✓ Adapter bridge test passed')
        print(f'  Adapters loaded: {len(manager.bridges)}')
    else:
        print('⚠ Adapter not available (expected if backend ecosystem not loaded)')
    
    store.close()


if __name__ == "__main__":
    test_adapter_bridge()
