#!/usr/bin/env python3
"""
Unified UI Synchronization Engine
==================================
Combines the best features from ui_mirror_system and ui_sync_engine:
- Real-time event-based sync (from ui_sync_engine)
- File sync with hot updates (from ui_mirror_system)
- Master failover & offline mode (from ui_mirror_system)
- Polling-based fallback (ChatGPT-style for reliability)
- Plugin architecture for extensibility
"""

import json
import time
import threading
import queue
import os
import hashlib
import logging
import copy
from typing import Dict, Any, Optional, List, Callable
from collections import deque
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class UIState:
    """Unified UI state structure"""
    page_id: str = 'dashboard'
    tool_state: str = 'none'
    button_states: Dict[str, Dict[str, Any]] = None
    modal_states: Dict[str, bool] = None
    form_values: Dict[str, Any] = None
    progress_bars: Dict[str, int] = None
    status_indicators: Dict[str, str] = None
    authority_holder: Optional[str] = None
    timestamp: float = 0.0
    sequence: int = 0
    scroll_positions: Dict[str, float] = None
    command_output: str = ''
    
    def __post_init__(self):
        if self.button_states is None:
            self.button_states = {}
        if self.modal_states is None:
            self.modal_states = {}
        if self.form_values is None:
            self.form_values = {}
        if self.progress_bars is None:
            self.progress_bars = {}
        if self.status_indicators is None:
            self.status_indicators = {}
        if self.scroll_positions is None:
            self.scroll_positions = {}
        if self.timestamp == 0.0:
            self.timestamp = time.time()
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UIState':
        return cls(**data)
    
    def compute_hash(self) -> str:
        """Compute state hash for change detection"""
        state_str = json.dumps(self.to_dict(), sort_keys=True)
        return hashlib.md5(state_str.encode()).hexdigest()[:16]


class UISyncEvent:
    """UI synchronization event"""
    def __init__(self, event_type: str, target: str, data: Dict[str, Any], authority: str):
        self.event_type = event_type
        self.target = target
        self.data = data
        self.authority = authority
        self.timestamp = time.time()
        self.sequence = int(time.time() * 1000000)  # Microsecond precision
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_type': self.event_type,
            'target': self.target,
            'data': self.data,
            'authority': self.authority,
            'timestamp': self.timestamp,
            'sequence': self.sequence
        }


class UnifiedUIEngine:
    """
    Unified UI Synchronization Engine
    
    Features:
    - Real-time event-based sync (primary)
    - Polling-based fallback (ChatGPT-style)
    - File sync with hot updates
    - Master failover & offline mode
    - Plugin architecture for extensibility
    """
    
    def __init__(self, engine_instance):
        self.engine = engine_instance
        
        # Setup logging
        self.logger = logging.getLogger('UnifiedUI')
        self.logger.setLevel(logging.INFO)
        
        # UI State
        self.current_state = UIState()
        self.previous_state = copy.deepcopy(self.current_state)
        self.state_history = deque(maxlen=100)
        
        # Event system
        self.event_queue = deque(maxlen=1000)
        self.sync_callbacks: Dict[str, Callable] = {}
        self.lock = threading.Lock()
        self.sequence_counter = 0
        
        # Master-Mirror state
        self.is_master = False
        self.master_device_id = None
        self.master_ip = None
        self.master_port = None
        self.peers: Dict[str, Dict[str, Any]] = {}
        self.mirror_devices = []  # Compatibility: List of device IDs that mirror this device
        
        # Sync settings
        self.sync_enabled = True
        self.broadcast_interval = 0.1  # 100ms for real-time
        self.poll_interval = 1.0  # 1s polling fallback (ChatGPT-style)
        self.running = False
        
        # Threads
        self.broadcast_thread = None
        self.poll_thread = None
        self.file_watcher_thread = None
        self.failover_thread = None
        
        # File sync (from ui_mirror_system)
        self.file_registry = {}
        self.pending_updates = queue.Queue()
        self.update_lock = threading.Lock()
        
        # Failover & offline mode
        self.master_last_seen = {}
        self.master_timeout = 8.0
        self.ping_timeout = 3.0
        self.consecutive_ping_failures = {}
        self.offline_mode = False
        self.offline_queue = []
        
        # Plugin system
        self.plugins: List[Callable] = []
        
        # Initialize based on engine role
        if self.engine.is_master():
            self.is_master = True
            self.master_device_id = self.engine.config.device_id
            self.current_state.authority_holder = self.engine.config.device_id
        else:
            # Find master from nodes
            for device_id, node_info in self.engine.state.nodes.items():
                if node_info.get('is_master', False):
                    self.master_device_id = device_id
                    self.master_ip = node_info.get('ip')
                    self.master_port = node_info.get('port', 7890)
                    self.current_state.authority_holder = device_id
                    break
        
        self.logger.info(f"[UnifiedUI] Initialized - Device: {self.engine.config.device_id}, Master: {self.is_master}")
    
    def start(self):
        """Start the unified engine"""
        if self.running:
            return
        
        self.running = True
        
        if self.is_master:
            # Master: Start broadcasting
            self.broadcast_thread = threading.Thread(target=self._broadcast_loop, daemon=True)
            self.broadcast_thread.start()
            self.logger.info("[UnifiedUI] Broadcast thread started (master mode)")
            
            # Start file watcher
            self.file_watcher_thread = threading.Thread(target=self._file_watcher_loop, daemon=True)
            self.file_watcher_thread.start()
            self.logger.info("[UnifiedUI] File watcher started")
        else:
            # Peer: Start polling (ChatGPT-style fallback)
            self.poll_thread = threading.Thread(target=self._poll_loop, daemon=True)
            self.poll_thread.start()
            self.logger.info("[UnifiedUI] Poll thread started (peer mode - ChatGPT-style)")
        
        # Start failover monitoring (all nodes)
        self.failover_thread = threading.Thread(target=self._failover_loop, daemon=True)
        self.failover_thread.start()
        self.logger.info("[UnifiedUI] Failover monitoring started")
        
        print("[UnifiedUI] Engine started")
    
    def stop(self):
        """Stop the unified engine"""
        self.running = False
        for thread in [self.broadcast_thread, self.poll_thread, self.file_watcher_thread, self.failover_thread]:
            if thread:
                thread.join(timeout=1)
        print("[UnifiedUI] Engine stopped")
    
    # ═══════════════════════════════════════════════════════════════
    # UI STATE MANAGEMENT
    # ═══════════════════════════════════════════════════════════════
    
    def update_state(self, **kwargs) -> bool:
        """Update UI state and trigger sync"""
        with self.lock:
            changed = False
            old_hash = self.current_state.compute_hash()
            
            for key, value in kwargs.items():
                if hasattr(self.current_state, key):
                    setattr(self.current_state, key, value)
                    changed = True
            
            if changed:
                self.current_state.timestamp = time.time()
                self.sequence_counter += 1
                self.current_state.sequence = self.sequence_counter
                
                # Save to history
                self.state_history.append({
                    'timestamp': time.time(),
                    'state': copy.deepcopy(self.current_state),
                    'hash': self.current_state.compute_hash()
                })
                
                # Trigger sync if master
                if self.is_master and self.sync_enabled:
                    self._broadcast_state()
                
                new_hash = self.current_state.compute_hash()
                self.logger.debug(f"[UnifiedUI] State updated: {old_hash[:8]} -> {new_hash[:8]}")
                return True
            
            return False
    
    def get_state_snapshot(self) -> Dict[str, Any]:
        """Get current UI state snapshot"""
        with self.lock:
            state_dict = self.current_state.to_dict()
            state_dict['hash'] = self.current_state.compute_hash()
            return state_dict
    
    def apply_state_snapshot(self, state_data: Dict[str, Any]) -> bool:
        """Apply UI state snapshot from master"""
        try:
            with self.lock:
                new_state = UIState.from_dict(state_data)
                # Only apply if sequence is newer
                if new_state.sequence > self.current_state.sequence:
                    self.previous_state = copy.deepcopy(self.current_state)
                    self.current_state = new_state
                    return True
            return False
        except Exception as e:
            self.logger.error(f"[UnifiedUI] Error applying snapshot: {e}")
            return False
    
    # ═══════════════════════════════════════════════════════════════
    # EVENT SYSTEM
    # ═══════════════════════════════════════════════════════════════
    
    def trigger_action(self, action_type: str, target: str, data: Dict[str, Any] = None) -> bool:
        """Trigger UI action and sync across mesh"""
        if data is None:
            data = {}
        
        event = UISyncEvent(
            event_type=action_type,
            target=target,
            data=data,
            authority=self.engine.config.device_id
        )
        
        with self.lock:
            self.event_queue.append(event)
        
        # Apply locally first
        self._apply_event_locally(event)
        
        # Broadcast if master
        if self.is_master and self.sync_enabled:
            self._broadcast_event(event)
        
        return True
    
    def receive_sync_event(self, event_data: Dict[str, Any]) -> bool:
        """Receive and apply sync event from another device"""
        try:
            # Skip if from self
            if event_data.get('authority') == self.engine.config.device_id:
                return False
            
            event = UISyncEvent(
                event_type=event_data['event_type'],
                target=event_data['target'],
                data=event_data['data'],
                authority=event_data['authority']
            )
            event.timestamp = event_data.get('timestamp', time.time())
            event.sequence = event_data.get('sequence', 0)
            
            # Apply event
            self._apply_event_locally(event)
            
            self.logger.debug(f"[UnifiedUI] Applied remote event: {event.event_type} from {event.authority}")
            return True
        
        except Exception as e:
            self.logger.error(f"[UnifiedUI] Error processing sync event: {e}")
            return False
    
    def _apply_event_locally(self, event: UISyncEvent):
        """Apply UI event to local state"""
        with self.lock:
            if event.event_type == 'button_click':
                self.current_state.button_states[event.target] = {
                    'clicked': True,
                    'timestamp': event.timestamp
                }
            elif event.event_type == 'page_change':
                self.current_state.page_id = event.data.get('page_id', 'dashboard')
            elif event.event_type == 'tool_activate':
                self.current_state.tool_state = event.data.get('tool_name', 'none')
            elif event.event_type == 'command_output':
                self.current_state.command_output = event.data.get('output', '')
            elif event.event_type == 'scroll':
                self.current_state.scroll_positions[event.target] = event.data.get('position', 0)
            elif event.event_type == 'authority_change':
                self.current_state.authority_holder = event.data.get('new_authority')
            
            self.current_state.timestamp = time.time()
            self.sequence_counter += 1
            self.current_state.sequence = self.sequence_counter
        
        # Trigger callbacks
        callback = self.sync_callbacks.get(event.event_type)
        if callback:
            callback(event)
    
    # ═══════════════════════════════════════════════════════════════
    # BROADCAST & POLLING (ChatGPT-style)
    # ═══════════════════════════════════════════════════════════════
    
    def _broadcast_loop(self):
        """Broadcast UI state to all peers (master only)"""
        while self.running:
            try:
                if self.is_master:
                    self._broadcast_state()
                time.sleep(self.broadcast_interval)
            except Exception as e:
                self.logger.error(f"[UnifiedUI] Broadcast error: {e}")
                time.sleep(1)
    
    def _broadcast_state(self):
        """Broadcast current UI state to all peers"""
        if not self.is_master:
            return
        
        peers = self.engine.state.nodes.copy()
        if len(peers) <= 1:
            return
        
        state_data = self.get_state_snapshot()
        
        for device_id, node_info in peers.items():
            if device_id == self.engine.config.device_id:
                continue
            
            threading.Thread(
                target=self._send_state_to_peer,
                args=(device_id, node_info, state_data),
                daemon=True
            ).start()
    
    def _send_state_to_peer(self, device_id: str, node_info: Dict[str, Any], state_data: Dict[str, Any]):
        """Send state to specific peer"""
        try:
            import urllib.request
            url = f"http://{node_info.get('ip', '')}:{node_info.get('port', 7890)}/ui_state"
            data = json.dumps(state_data).encode('utf-8')
            
            req = urllib.request.Request(url, data=data)
            req.add_header('Content-Type', 'application/json')
            
            with urllib.request.urlopen(req, timeout=2) as response:
                if response.status == 200:
                    self.logger.debug(f"[UnifiedUI] State synced to {device_id}")
        except Exception:
            pass  # Peer might be offline
    
    def _poll_loop(self):
        """Poll master for UI state (ChatGPT-style fallback)"""
        while self.running:
            try:
                if not self.is_master and self.master_device_id:
                    self._poll_master_state()
                time.sleep(self.poll_interval)
            except Exception as e:
                self.logger.error(f"[UnifiedUI] Poll error: {e}")
                time.sleep(self.poll_interval)
    
    def _poll_master_state(self):
        """Poll master for UI state updates"""
        if not self.master_device_id:
            return
        
        master_node = self.engine.state.nodes.get(self.master_device_id)
        if not master_node:
            return
        
        try:
            import urllib.request
            url = f"http://{master_node.get('ip', '')}:{master_node.get('port', 7890)}/ui_state"
            
            with urllib.request.urlopen(url, timeout=self.ping_timeout) as response:
                data = json.loads(response.read().decode('utf-8'))
                
                if data.get('status') == 'ok':
                    state_data = data.get('ui_state', {})
                    new_hash = data.get('hash', '')
                    current_hash = self.current_state.compute_hash()
                    
                    # Only update if changed
                    if new_hash != current_hash:
                        self.apply_state_snapshot(state_data)
                        self.master_last_seen[self.master_device_id] = time.time()
                        self.consecutive_ping_failures[self.master_device_id] = 0
        except Exception:
            # Master might be offline
            pass
    
    # ═══════════════════════════════════════════════════════════════
    # FILE SYNC (from ui_mirror_system)
    # ═══════════════════════════════════════════════════════════════
    
    def _file_watcher_loop(self):
        """Watch for file changes and propagate (master only)"""
        watch_interval = 1.0
        project_dir = os.path.dirname(os.path.abspath(__file__))
        last_check_time = time.time()
        last_hash_state = {}
        
        while self.running:
            try:
                if self.is_master and self.sync_enabled:
                    current_time = time.time()
                    if current_time - last_check_time >= watch_interval:
                        changes = self.detect_file_changes([project_dir])
                        if changes:
                            for change in changes:
                                file_key = change['file']
                                file_hash = change.get('hash', '')
                                if file_key not in last_hash_state or last_hash_state[file_key] != file_hash:
                                    result = self.propagate_file_update(change)
                                    if result.get('success'):
                                        self.logger.info(f"[UnifiedUI] Auto-propagated {change['file']}")
                                        last_hash_state[file_key] = file_hash
                        last_check_time = current_time
                    time.sleep(2.0)  # Slow down from 0.5s to 2s
            except Exception as e:
                self.logger.error(f"[UnifiedUI] File watcher error: {e}")
                time.sleep(watch_interval)
    
    def detect_file_changes(self, watch_paths: List[str] = None) -> List[Dict[str, Any]]:
        """Detect file changes in watched paths"""
        if watch_paths is None:
            watch_paths = [os.path.dirname(os.path.abspath(__file__))]
        
        changes = []
        for watch_path in watch_paths:
            if not os.path.exists(watch_path):
                continue
            
            for root, dirs, files in os.walk(watch_path):
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'backup']]
                
                for file in files:
                    if file.endswith('.pyc') or file.startswith('.'):
                        continue
                    
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, watch_path)
                    
                    registered = self.file_registry.get(file_path)
                    current_hash = self._compute_file_hash(file_path)
                    
                    if not registered or registered.get('hash') != current_hash:
                        metadata = self._register_file(file_path)
                        if metadata:
                            changes.append({
                                'action': 'modified' if registered else 'created',
                                'file': rel_path,
                                'absolute_path': file_path,
                                'hash': current_hash,
                                'timestamp': metadata.get('timestamp', time.time()),
                                'size': metadata.get('size', 0),
                                'metadata': metadata
                            })
        
        return changes
    
    def _compute_file_hash(self, file_path: str) -> str:
        """Compute SHA256 hash of file"""
        sha256 = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except Exception as e:
            self.logger.error(f"[UnifiedUI] Hash error: {e}")
            return ''
    
    def _register_file(self, file_path: str) -> Dict[str, Any]:
        """Register a file for sync tracking"""
        if not os.path.exists(file_path):
            return None
        
        try:
            stat = os.stat(file_path)
            file_hash = self._compute_file_hash(file_path)
            
            metadata = {
                'path': file_path,
                'hash': file_hash,
                'timestamp': stat.st_mtime,
                'size': stat.st_size,
                'node': self.engine.config.device_id
            }
            
            with self.update_lock:
                self.file_registry[file_path] = metadata
            
            return metadata
        except Exception as e:
            self.logger.error(f"[UnifiedUI] Register error: {e}")
            return None
    
    def propagate_file_update(self, file_update: Dict[str, Any]) -> Dict[str, Any]:
        """Propagate file update to all nodes"""
        if not self.is_master:
            return {'success': False, 'error': 'Not master'}
        
        file_path = file_update.get('absolute_path') or file_update.get('file')
        if not file_path:
            return {'success': False, 'error': 'No file path'}
        
        try:
            with open(file_path, 'rb') as f:
                file_content = f.read()
        except Exception as e:
            return {'success': False, 'error': str(e)}
        
        import base64
        file_data_b64 = base64.b64encode(file_content).decode('utf-8')
        
        target_nodes = [
            device_id for device_id in self.engine.state.nodes.keys()
            if device_id != self.engine.config.device_id
        ]
        
        results = {'success': True, 'propagated_to': [], 'failed': []}
        
        for device_id in target_nodes:
            node_info = self.engine.state.nodes.get(device_id)
            if not node_info:
                continue
            
            try:
                import urllib.request
                data = {
                    'file_path': file_update.get('file', os.path.basename(file_path)),
                    'absolute_path': file_path,
                    'file_data': file_data_b64,
                    'file_hash': file_update.get('hash', ''),
                    'file_size': file_update.get('size', len(file_content)),
                    'timestamp': file_update.get('timestamp', time.time()),
                    'source_node': self.engine.config.device_id
                }
                
                url = f"http://{node_info.get('ip', '')}:{node_info.get('port', 7890)}/file/hot_update"
                req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'))
                req.add_header('Content-Type', 'application/json')
                
                with urllib.request.urlopen(req, timeout=10) as response:
                    result = json.loads(response.read().decode('utf-8'))
                    if result.get('status') == 'ok':
                        results['propagated_to'].append({'node': device_id})
            except Exception as e:
                results['failed'].append({'node': device_id, 'error': str(e)})
        
        return results
    
    # ═══════════════════════════════════════════════════════════════
    # MASTER CONTROL & FAILOVER
    # ═══════════════════════════════════════════════════════════════
    
    def take_control(self) -> bool:
        """Take master control"""
        with self.lock:
            self.is_master = True
            self.master_device_id = self.engine.config.device_id
            self.current_state.authority_holder = self.engine.config.device_id
            self.current_state.timestamp = time.time()
            self.sequence_counter += 1
            self.current_state.sequence = self.sequence_counter
        
        # Restart threads
        self.stop()
        self.start()
        
        # Broadcast authority change
        self.trigger_action('authority_change', 'system', {
            'new_authority': self.engine.config.device_id,
            'timestamp': time.time()
        })
        
        self.logger.info(f"[UnifiedUI] {self.engine.config.device_id} took control")
        return True
    
    def register_peer(self, device_id: str, ip: str, port: int):
        """Register a peer device"""
        with self.lock:
            self.peers[device_id] = {'ip': ip, 'port': port, 'last_seen': time.time()}
        self.logger.info(f"[UnifiedUI] Registered peer: {device_id} at {ip}:{port}")
    
    def _failover_loop(self):
        """Monitor master status and handle failover"""
        check_interval = 3.0
        
        while self.running:
            try:
                if not self.is_master and self.master_device_id:
                    master_alive = self._ping_master()
                    
                    if master_alive:
                        self.master_last_seen[self.master_device_id] = time.time()
                        self.consecutive_ping_failures[self.master_device_id] = 0
                    else:
                        failures = self.consecutive_ping_failures.get(self.master_device_id, 0) + 1
                        self.consecutive_ping_failures[self.master_device_id] = failures
                        
                        last_seen = self.master_last_seen.get(self.master_device_id, time.time())
                        time_since_seen = time.time() - last_seen
                        
                        if time_since_seen > self.master_timeout or failures >= 3:
                            self.logger.warning(f"[UnifiedUI] Master {self.master_device_id} appears offline")
                            self.enable_offline_mode()
                            self.master_device_id = None
                            self.is_master = False
                
                time.sleep(check_interval)
            except Exception as e:
                self.logger.error(f"[UnifiedUI] Failover error: {e}")
                time.sleep(check_interval)
    
    def _ping_master(self) -> bool:
        """Ping master to check if alive"""
        if not self.master_device_id:
            return False
        
        master_node = self.engine.state.nodes.get(self.master_device_id)
        if not master_node:
            return False
        
        try:
            import urllib.request
            url = f"http://{master_node.get('ip', '')}:{master_node.get('port', 7890)}/status"
            with urllib.request.urlopen(url, timeout=self.ping_timeout) as response:
                data = json.loads(response.read().decode('utf-8'))
                return data.get('status') == 'online' and data.get('is_master', False)
        except Exception:
            return False
    
    def enable_offline_mode(self):
        """Enable offline mode"""
        self.offline_mode = True
        self.logger.info("[UnifiedUI] Offline mode enabled")
    
    def disable_offline_mode(self):
        """Disable offline mode"""
        self.offline_mode = False
        self.logger.info("[UnifiedUI] Offline mode disabled")
    
    # ═══════════════════════════════════════════════════════════════
    # COMPATIBILITY METHODS
    # ═══════════════════════════════════════════════════════════════
    
    def get_ui_state(self) -> Dict[str, Any]:
        """Get current UI state (compatibility)"""
        return self.get_state_snapshot()
    
    def set_master(self, master_id: str, master_ip: str = None, master_port: int = None):
        """Set master node (compatibility)"""
        with self.lock:
            self.master_id = master_id
            self.master_ip = master_ip
            self.master_port = master_port
            if master_id == self.engine.config.device_id:
                self.is_master = True
                self.master_device_id = master_id
                self.current_state.authority_holder = master_id
            else:
                self.is_master = False
                self.master_device_id = master_id
                self.current_state.authority_holder = master_id
    
    def register_sync_callback(self, event_type: str, callback: Callable):
        """Register callback for UI sync events"""
        self.sync_callbacks[event_type] = callback
    
    def enable_sync(self, enabled: bool = True):
        """Enable or disable UI synchronization"""
        self.sync_enabled = enabled
        self.logger.info(f"[UnifiedUI] Synchronization {'ENABLED' if enabled else 'DISABLED'}")
    
    # ═══════════════════════════════════════════════════════════════
    # FILE UPDATE APPLICATION (for hot_update endpoint)
    # ═══════════════════════════════════════════════════════════════
    
    def apply_file_update(self, file_update: Dict[str, Any]) -> Dict[str, Any]:
        """Apply file update received from master (compatibility method)"""
        file_path = file_update.get('absolute_path') or file_update.get('file_path')
        file_data_b64 = file_update.get('file_data')
        expected_hash = file_update.get('file_hash')
        source_node = file_update.get('source_node', 'unknown')
        
        if not file_path:
            return {'status': 'error', 'error': 'No file path provided'}
        
        if not file_data_b64:
            return {'status': 'error', 'error': 'No file data'}
        
        try:
            import base64
            file_content = base64.b64decode(file_data_b64)
            
            # Ensure directory exists
            file_dir = os.path.dirname(file_path)
            if file_dir:
                os.makedirs(file_dir, exist_ok=True)
            
            # Write file
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            # Verify hash if provided
            if expected_hash:
                actual_hash = self._compute_file_hash(file_path)
                hash_match = (actual_hash == expected_hash)
                
                if hash_match:
                    self._register_file(file_path)
                    self.logger.info(f"[UnifiedUI] Applied update from {source_node}: {file_path} (hash verified)")
                    return {
                        'status': 'ok',
                        'hash_match': True,
                        'timestamp': time.time(),
                        'file_path': file_path
                    }
                else:
                    self.logger.error(f"[UnifiedUI] Hash mismatch for {file_path}")
                    return {
                        'status': 'error',
                        'error': 'Hash mismatch',
                        'expected_hash': expected_hash[:16],
                        'actual_hash': actual_hash[:16]
                    }
            else:
                # No hash provided - just write it
                self._register_file(file_path)
                self.logger.info(f"[UnifiedUI] Applied update from {source_node}: {file_path}")
                return {
                    'status': 'ok',
                    'hash_match': False,
                    'timestamp': time.time(),
                    'file_path': file_path
                }
        except Exception as e:
            self.logger.error(f"[UnifiedUI] Error applying update: {e}")
            return {'status': 'error', 'error': str(e)}

