#!/usr/bin/env python3
"""
GhostLang Transport Adapter for OMNI
Enables mesh communication through alternative channels when network is isolated
"""

import os
import sys
import json
import logging
import threading
import time
from pathlib import Path
from typing import Dict, Any, Optional, Callable

# Add GhostLang to path
ghostlang_path = Path(__file__).parent.parent / 'lang' / 'ghostlang-main'
sys.path.insert(0, str(ghostlang_path))

try:
    from ghost_fallback_daemon import GhostFallbackDaemon, TransportMode
    from ghost_drop_usb import GhostDropManager
    from ghost_pinger_lofi import GhostPinger, LoFiMedium
    GHOSTLANG_AVAILABLE = True
except ImportError:
    GHOSTLANG_AVAILABLE = False

logger = logging.getLogger("omni.ghostlang_transport")


class GhostLangTransport:
    """
    Transport adapter that uses GhostLang for mesh communication
    when traditional network ports are blocked (e.g., campus WiFi isolation)
    """
    
    def __init__(self, node_id: str, data_dir: str, auth_key: str = "omni_mesh"):
        """
        Initialize GhostLang transport
        
        Args:
            node_id: OMNI node ID
            data_dir: Directory for GhostLang data
            auth_key: Authentication key for GhostLang
        """
        self.node_id = node_id
        self.data_dir = Path(data_dir)
        self.auth_key = auth_key
        
        # Create data directory
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Transport components
        self.fallback_daemon = None
        self.usb_manager = None
        self.lofi_pinger = None
        
        # State
        self.running = False
        self.current_mode = TransportMode.INTERNET if GHOSTLANG_AVAILABLE else None
        self.message_callbacks = []
        
        # Initialize if available
        if GHOSTLANG_AVAILABLE:
            self._initialize_ghostlang()
        else:
            logger.warning("[GHOSTLANG] GhostLang not available - transport disabled")
    
    def _initialize_ghostlang(self):
        """Initialize GhostLang components"""
        try:
            # Initialize fallback daemon
            self.fallback_daemon = GhostFallbackDaemon(
                node_id=self.node_id,
                auth_key=self.auth_key,
                data_dir=str(self.data_dir)
            )
            
            # Initialize USB manager
            self.usb_manager = GhostDropManager(
                node_id=self.node_id,
                data_dir=str(self.data_dir / 'usb')
            )
            
            # Initialize lo-fi pinger
            self.lofi_pinger = GhostPinger(
                node_id=self.node_id,
                role='PEER',
                medium=LoFiMedium.NETWORK
            )
            
            logger.info("[GHOSTLANG] Transport initialized")
            
        except Exception as e:
            logger.error(f"[GHOSTLANG] Failed to initialize: {e}")
            self.fallback_daemon = None
            self.usb_manager = None
            self.lofi_pinger = None
    
    def start(self):
        """Start GhostLang transport"""
        if not GHOSTLANG_AVAILABLE:
            logger.warning("[GHOSTLANG] Cannot start - not available")
            return False
        
        if self.running:
            return True
        
        try:
            self.running = True
            
            # Start fallback daemon
            if self.fallback_daemon:
                self.fallback_daemon.start()
            
            # Start USB monitoring
            if self.usb_manager:
                threading.Thread(
                    target=self._monitor_usb,
                    daemon=True,
                    name="ghostlang-usb-monitor"
                ).start()
            
            # Start lo-fi monitoring
            if self.lofi_pinger:
                threading.Thread(
                    target=self._monitor_lofi,
                    daemon=True,
                    name="ghostlang-lofi-monitor"
                ).start()
            
            logger.info("[GHOSTLANG] Transport started")
            return True
            
        except Exception as e:
            logger.error(f"[GHOSTLANG] Failed to start: {e}")
            self.running = False
            return False
    
    def stop(self):
        """Stop GhostLang transport"""
        self.running = False
        
        if self.fallback_daemon:
            self.fallback_daemon.stop()
        
        logger.info("[GHOSTLANG] Transport stopped")
    
    def send_mesh_command(self, target_node: str, command: Dict[str, Any]) -> bool:
        """
        Send mesh command through GhostLang transport
        
        Args:
            target_node: Target node ID
            command: Command data
            
        Returns:
            True if sent successfully
        """
        if not self.running:
            return False
        
        try:
            # Package command for GhostLang
            ghost_command = {
                'type': 'mesh_relay',
                'source': self.node_id,
                'target': target_node,
                'payload': command,
                'timestamp': time.time()
            }
            
            # Try to send through fallback daemon first
            if self.fallback_daemon:
                success = self.fallback_daemon.send_command(ghost_command)
                if success:
                    logger.debug(f"[GHOSTLANG] Sent command to {target_node} via daemon")
                    return True
            
            # Fallback to USB if daemon fails
            if self.usb_manager:
                self.usb_manager.queue_command(ghost_command)
                logger.debug(f"[GHOSTLANG] Queued command to {target_node} for USB transport")
                return True
            
            # Last resort: lo-fi
            if self.lofi_pinger:
                # Lo-fi is very limited, only for critical commands
                if command.get('priority') == 'critical':
                    self.lofi_pinger.send_command(ghost_command)
                    logger.debug(f"[GHOSTLANG] Sent critical command to {target_node} via lo-fi")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"[GHOSTLANG] Failed to send command: {e}")
            return False
    
    def register_message_callback(self, callback: Callable[[Dict[str, Any]], None]):
        """Register callback for received messages"""
        self.message_callbacks.append(callback)
    
    def _monitor_usb(self):
        """Monitor for USB drops"""
        while self.running:
            try:
                if self.usb_manager:
                    # Check for new drops
                    drops = self.usb_manager.check_for_drops()
                    for drop in drops:
                        self._handle_received_message(drop)
                
                time.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                logger.error(f"[GHOSTLANG] USB monitor error: {e}")
                time.sleep(10)
    
    def _monitor_lofi(self):
        """Monitor for lo-fi commands"""
        while self.running:
            try:
                if self.lofi_pinger:
                    # Check for incoming lo-fi commands
                    commands = self.lofi_pinger.receive_commands()
                    for cmd in commands:
                        self._handle_received_message(cmd)
                
                time.sleep(2)  # Check every 2 seconds
                
            except Exception as e:
                logger.error(f"[GHOSTLANG] Lo-fi monitor error: {e}")
                time.sleep(5)
    
    def _handle_received_message(self, message: Dict[str, Any]):
        """Handle received message from any transport"""
        try:
            # Verify it's a mesh relay command
            if message.get('type') != 'mesh_relay':
                return
            
            # Extract payload
            payload = message.get('payload')
            if not payload:
                return
            
            # Call registered callbacks
            for callback in self.message_callbacks:
                try:
                    callback(payload)
                except Exception as e:
                    logger.error(f"[GHOSTLANG] Callback error: {e}")
            
            logger.debug(f"[GHOSTLANG] Received mesh command from {message.get('source')}")
            
        except Exception as e:
            logger.error(f"[GHOSTLANG] Failed to handle message: {e}")
    
    def get_transport_status(self) -> Dict[str, Any]:
        """Get current transport status"""
        return {
            'available': GHOSTLANG_AVAILABLE,
            'running': self.running,
            'mode': self.current_mode.value if self.current_mode else 'unavailable',
            'daemon_active': self.fallback_daemon is not None and self.fallback_daemon.running if self.fallback_daemon else False,
            'usb_active': self.usb_manager is not None,
            'lofi_active': self.lofi_pinger is not None
        }
