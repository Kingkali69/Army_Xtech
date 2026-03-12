#!/usr/bin/env python3
"""
GhostComms - Internet-Independent Communication Integration

This script integrates all GhostComms components to create a complete
offline-capable communication system for GhostHUD. It handles automatic
fallback during internet outages, USB transport, and low-fidelity 
command passing.

Features:
- Automatic detection of internet connectivity
- Transparent fallback between communication methods
- Command queue management and prioritization
- USB sneakernet support for air-gapped communication
- Lo-Fi communication for critical commands
- Integration with existing GhostHUD architecture
"""

import os
import sys
import time
import json
import signal
import logging
import threading
import socket
import argparse
from typing import Dict, List, Any, Optional, Callable, Tuple
import urllib.request
import importlib.util
import subprocess
import random
import uuid
from enum import Enum, auto
from pathlib import Path

# Import GhostComms modules
try:
    # Try to import directly first
    from ghost_fallback_daemon import GhostFallbackDaemon, ConnectivityStatus, TransportMode, CommandPriority
    from ghost_drop_usb import GhostDropManager, CommandPriority as DropCommandPriority
    from ghost_pinger_lofi import GhostPinger, LoFiCommand, LoFiMedium, NodeStatus
except ImportError:
    # Get the directory of this script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Add to path for imports
    sys.path.append(current_dir)
    
    try:
        from ghost_fallback_daemon import GhostFallbackDaemon, ConnectivityStatus, TransportMode, CommandPriority
        from ghost_drop_usb import GhostDropManager, CommandPriority as DropCommandPriority
        from ghost_pinger_lofi import GhostPinger, LoFiCommand, LoFiMedium, NodeStatus
    except ImportError:
        print("Error: Could not import GhostComms modules. Ensure they are in the same directory.")
        sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ghost.comms")

# =============================================================================
# GHOSTHUD CONNECTOR CLASS
# =============================================================================

class GhostHUDConnector:
    """Connects to existing GhostHUD infrastructure"""
    
    def __init__(
        self,
        node_id: str,
        auth_key: str,
        master_ip: Optional[str] = None,
        master_port: int = 7890,
        local_port: int = 7891
    ):
        """Initialize connector
        
        Args:
            node_id: Node ID
            auth_key: Auth key
            master_ip: IP of master node (None if this is master)
            master_port: Port of master node
            local_port: Local port
        """
        self.node_id = node_id
        self.auth_key = auth_key
        self.master_ip = master_ip
        self.master_port = master_port
        self.local_port = local_port
        self.is_master = master_ip is None
        
        # State
        self.connected = False
        self.last_sync = 0
        self.command_callbacks = []
        
    def check_connection(self) -> bool:
        """Check if we can connect to the master
        
        Returns:
            bool: True if connected
        """
        if self.is_master:
            # Master is always "connected"
            self.connected = True
            return True
            
        if not self.master_ip:
            return False
            
        try:
            # Try to connect to master
            with urllib.request.urlopen(f"http://{self.master_ip}:{self.master_port}/status") as response:
                if response.status == 200:
                    self.connected = True
                    return True
        except Exception:
            self.connected = False
            
        return False
    
    def register_command_callback(self, callback: Callable[[Dict, str], None]):
        """Register callback for commands
        
        Args:
            callback: Function to call for commands
                     Takes (command_data, command_type) as arguments
        """
        if callback not in self.command_callbacks:
            self.command_callbacks.append(callback)
    
    def unregister_command_callback(self, callback):
        """Unregister command callback"""
        if callback in self.command_callbacks:
            self.command_callbacks.remove(callback)
    
    def sync_with_master(self) -> bool:
        """Sync with master node
        
        Returns:
            bool: True if successful
        """
        if self.is_master:
            # Master doesn't need to sync
            return True
            
        if not self.master_ip or not self.connected:
            return False
            
        try:
            # Get status from master
            with urllib.request.urlopen(f"http://{self.master_ip}:{self.master_port}/status") as response:
                if response.status == 200:
                    data = json.loads(response.read().decode())
                    
                    # Check if sync is needed
                    master_sync = data.get('last_sync', 0)
                    if master_sync > self.last_sync:
                        self.last_sync = master_sync
                        
                        # Notify callbacks about commands
                        if 'commands' in data:
                            for cmd in data['commands']:
                                for callback in self.command_callbacks:
                                    try:
                                        callback(cmd, cmd.get('type', 'unknown'))
                                    except Exception as e:
                                        logger.error(f"Error in command callback: {e}")
                        
                        return True
                        
        except Exception as e:
            logger.error(f"Error syncing with master: {e}")
            
        return False
    
    def send_command(self, command_type: str, payload: Dict[str, Any]) -> bool:
        """Send a command to master
        
        Args:
            command_type: Command type
            payload: Command data
            
        Returns:
            bool: True if successful
        """
        if self.is_master:
            # Master processes commands locally
            for callback in self.command_callbacks:
                try:
                    callback({'type': command_type, **payload}, command_type)
                except Exception as e:
                    logger.error(f"Error in command callback: {e}")
                    
            return True
            
        if not self.master_ip or not self.connected:
            return False
            
        try:
            # Send command to master
            url = f"http://{self.master_ip}:{self.master_port}/sync/{command_type}"
            
            # Add device ID if missing
            if 'device_id' not in payload:
                payload['device_id'] = self.node_id
                
            # Create request
            request = urllib.request.Request(
                url,
                data=json.dumps(payload).encode(),
                headers={'Content-Type': 'application/json'}
            )
            
            # Send request
            with urllib.request.urlopen(request) as response:
                if response.status == 200:
                    return True
                    
        except Exception as e:
            logger.error(f"Error sending command to master: {e}")
            
        return False

# =============================================================================
# GHOSTCOMMS SYSTEM CLASS
# =============================================================================

class GhostCommsSystem:
    """GhostComms system integrating all components"""
    
    def __init__(
        self,
        node_id: str,
        auth_key: str,
        data_dir: str,
        master_ip: Optional[str] = None,
        master_port: int = 7890
    ):
        """Initialize the GhostComms system
        
        Args:
            node_id: Node ID
            auth_key: Auth key
            data_dir: Data directory
            master_ip: IP of master node (None if this is master)
            master_port: Port of master node
        """
        self.node_id = node_id
        self.auth_key = auth_key
        self.data_dir = os.path.abspath(data_dir)
        self.master_ip = master_ip
        self.master_port = master_port
        self.is_master = master_ip is None
        
        # Ensure data directory exists
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Create components
        self._create_components()
        
        # State
        self.transport_mode = TransportMode.INTERNET
        self._stop_event = threading.Event()
        self._monitor_thread = None
        
        logger.info(f"GhostComms initialized for node {node_id} ({'MASTER' if self.is_master else 'PEER'})")
    
    def _create_components(self):
        """Create system components"""
        # Create GhostHUD connector
        self.hud_connector = GhostHUDConnector(
            node_id=self.node_id,
            auth_key=self.auth_key,
            master_ip=self.master_ip,
            master_port=self.master_port
        )
        
        # Create fallback daemon
        self.fallback_daemon = GhostFallbackDaemon(
            node_id=self.node_id,
            data_dir=os.path.join(self.data_dir, "fallback"),
            auth_key=self.auth_key,
            master_ip=self.master_ip,
            master_port=self.master_port
        )
        
        # Create USB drop manager
        self.drop_manager = GhostDropManager(
            node_id=self.node_id,
            data_dir=os.path.join(self.data_dir, "drops"),
            auto_process=True
        )
        
        # Create lo-fi pinger
        pinger_config = {
            "network_port": self.master_port + 1000,  # Use a different port for lo-fi
            "heartbeat_interval": 60,
            "simulate_loss": 0.1  # Simulate some packet loss
        }
        
        self.pinger = GhostPinger(
            node_id=self.node_id,
            role="MASTER" if self.is_master else "PEER",
            auth_key=self.auth_key,
            data_dir=os.path.join(self.data_dir, "lofi"),
            config=pinger_config
        )
        
        # Register callbacks
        self.hud_connector.register_command_callback(self._handle_hud_command)
        self.fallback_daemon.register_command_handler("sync_all", self._handle_fallback_sync_all)
        self.fallback_daemon.register_command_handler("authority", self._handle_fallback_authority)
        self.fallback_daemon.register_command_handler("page_change", self._handle_fallback_page)
        self.fallback_daemon.register_command_handler("tool_activate", self._handle_fallback_tool)
        self.drop_manager.register_command_handler("sync_all", self._handle_drop_sync_all)
        self.drop_manager.register_command_handler("authority", self._handle_drop_authority)
        self.drop_manager.register_command_handler("page_change", self._handle_drop_page)
        self.drop_manager.register_command_handler("tool_activate", self._handle_drop_tool)
        self.pinger.register_command_handler(LoFiCommand.SYNC.value, self._handle_lofi_sync)
        self.pinger.register_command_handler(LoFiCommand.AUTH.value, self._handle_lofi_auth)
        self.pinger.register_command_handler(LoFiCommand.MODE.value, self._handle_lofi_mode)
    
    def start(self):
        """Start the GhostComms system"""
        # Start components
        self.fallback_daemon.start()
        self.drop_manager.start()
        self.pinger.start()
        
        # Start monitoring thread
        self._stop_event.clear()
        self._monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self._monitor_thread.start()
        
        logger.info("GhostComms system started")
    
    def stop(self):
        """Stop the GhostComms system"""
        # Stop monitoring thread
        self._stop_event.set()
        if self._monitor_thread:
            self._monitor_thread.join(timeout=1)
            
        # Stop components
        self.fallback_daemon.stop()
        self.drop_manager.stop()
        self.pinger.stop()
        
        logger.info("GhostComms system stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        # Check HUD connection initially
        self.hud_connector.check_connection()
        
        while not self._stop_event.is_set():
            try:
                # Check connectivity and update transport mode
                connectivity = self.fallback_daemon.connectivity.status
                current_mode = self.transport_mode
                
                # Determine transport mode based on connectivity
                if connectivity == ConnectivityStatus.ONLINE:
                    # Try to connect to HUD
                    if self.hud_connector.check_connection():
                        self.transport_mode = TransportMode.INTERNET
                    else:
                        self.transport_mode = TransportMode.MESH_ONLY
                elif connectivity == ConnectivityStatus.LOCAL_ONLY:
                    self.transport_mode = TransportMode.MESH_ONLY
                elif connectivity == ConnectivityStatus.ISOLATED:
                    # Check if USB is available
                    if self.drop_manager.is_usb_available():
                        self.transport_mode = TransportMode.USB
                    else:
                        self.transport_mode = TransportMode.LO_FI
                
                # Check if mode changed
                if current_mode != self.transport_mode:
                    logger.info(f"Transport mode changed: {current_mode.value} -> {self.transport_mode.value}")
                    
                    # Update fallback daemon
                    self.fallback_daemon._handle_fallback_mode({
                        "mode": self.transport_mode.value
                    }, self.node_id)
                    
                    # Send status update via lo-fi
                    self.pinger.send_status({
                        "mode": self.transport_mode.value,
                        "conn": connectivity.name,
                        "role": "MASTER" if self.is_master else "PEER"
                    })
                
                # Sync with HUD if online
                if self.transport_mode == TransportMode.INTERNET and self.hud_connector.connected:
                    self.hud_connector.sync_with_master()
                
                # Process any pending commands
                
                # Wait before next check
                self._stop_event.wait(5)  # Check every 5 seconds
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                self._stop_event.wait(5)  # Wait before retry
    
    def send_command(
        self, 
        command_type: str, 
        payload: Dict[str, Any],
        priority: CommandPriority = CommandPriority.MEDIUM,
        target_node: Optional[str] = None
    ) -> bool:
        """Send a command using the appropriate transport
        
        Args:
            command_type: Command type
            payload: Command data
            priority: Command priority
            target_node: Target node (None for broadcast)
            
        Returns:
            bool: True if sent successfully
        """
        # Add source node if missing
        if 'source' not in payload:
            payload['source'] = self.node_id
            
        # Try primary transport based on current mode
        success = False
        
        if self.transport_mode == TransportMode.INTERNET:
            # Try HUD connector first
            if self.hud_connector.connected:
                success = self.hud_connector.send_command(command_type, payload)
                
            # Fall back to mesh if HUD fails
            if not success:
                success = self._send_via_fallback(command_type, payload, priority, target_node)
                
        elif self.transport_mode == TransportMode.MESH_ONLY:
            success = self._send_via_fallback(command_type, payload, priority, target_node)
            
        elif self.transport_mode == TransportMode.USB:
            success = self._send_via_usb(command_type, payload, priority, target_node)
            
        elif self.transport_mode == TransportMode.LO_FI:
            success = self._send_via_lofi(command_type, payload, target_node)
            
        return success
    
    def _send_via_fallback(
        self, 
        command_type: str, 
        payload: Dict[str, Any],
        priority: CommandPriority,
        target_node: Optional[str]
    ) -> bool:
        """Send command via fallback daemon
        
        Args:
            command_type: Command type
            payload: Command data
            priority: Command priority
            target_node: Target node (None for broadcast)
            
        Returns:
            bool: True if sent successfully
        """
        # Queue command in fallback daemon
        cmd_id = self.fallback_daemon.queue_command(
            command_type=command_type,
            payload=payload,
            target_node=target_node,
            priority=priority
        )
        
        return cmd_id is not None
    
    def _send_via_usb(
        self, 
        command_type: str, 
        payload: Dict[str, Any],
        priority: CommandPriority,
        target_node: Optional[str]
    ) -> bool:
        """Send command via USB
        
        Args:
            command_type: Command type
            payload: Command data
            priority: Command priority
            target_node: Target node (None for broadcast)
            
        Returns:
            bool: True if sent successfully
        """
        # Map priority
        drop_priority = DropCommandPriority.MEDIUM
        if priority == CommandPriority.HIGH:
            drop_priority = DropCommandPriority.HIGH
        elif priority == CommandPriority.LOW:
            drop_priority = DropCommandPriority.LOW
        
        # Create command data
        command = {
            "command_type": command_type,
            "payload": payload,
            "source_node": self.node_id,
            "priority": drop_priority.name,
            "id": str(uuid.uuid4()),
            "created_at": time.time()
        }
        
        if target_node:
            command["target_node"] = target_node
            
        # Create drop with target nodes
        target_nodes = [target_node] if target_node else None
        deployed = self.drop_manager.create_and_deploy_command_drop(
            commands=[command],
            target_nodes=target_nodes
        )
        
        return len(deployed) > 0
    
    def _send_via_lofi(
        self, 
        command_type: str, 
        payload: Dict[str, Any],
        target_node: Optional[str]
    ) -> bool:
        """Send command via lo-fi
        
        Args:
            command_type: Command type
            payload: Command data
            target_node: Target node (None for broadcast)
            
        Returns:
            bool: True if sent successfully
        """
        # Map command type to lo-fi command
        lofi_cmd = LoFiCommand.EXEC  # Default to exec
        
        if command_type == "sync_all":
            lofi_cmd = LoFiCommand.SYNC
        elif command_type == "authority":
            lofi_cmd = LoFiCommand.AUTH
        elif command_type == "page_change":
            lofi_cmd = LoFiCommand.MODE
        elif command_type == "tool_activate":
            lofi_cmd = LoFiCommand.EXEC
            
        # Create minimal payload
        minimal_payload = {
            "op": command_type,
            "src": self.node_id
        }
        
        # Add essential data from original payload
        if command_type == "authority":
            minimal_payload["auth"] = payload.get("has_authority", False)
            minimal_payload["id"] = payload.get("device_id", "unknown")
        elif command_type == "page_change":
            minimal_payload["page"] = payload.get("page", 1)
        elif command_type == "tool_activate":
            minimal_payload["tool"] = payload.get("tool", "unknown")
            
        # Send via lo-fi
        cmd_id = self.pinger.send_command(
            command_type=lofi_cmd,
            target_node=target_node,
            payload=minimal_payload
        )
        
        return cmd_id is not None
    
    # Command handlers
    
    def _handle_hud_command(self, command_data: Dict[str, Any], command_type: str):
        """Handle command from HUD
        
        Args:
            command_data: Command data
            command_type: Command type
        """
        logger.info(f"Received HUD command: {command_type}")
        
        # Forward to fallback daemon
        self.fallback_daemon.queue_command(
            command_type=command_type,
            payload=command_data,
            priority=CommandPriority.MEDIUM
        )
        
        # Forward to lo-fi for critical commands
        if command_type in ["sync_all", "authority"]:
            self._send_via_lofi(command_type, command_data, None)
    
    def _handle_fallback_sync_all(self, payload: Dict[str, Any], source_node: str) -> Dict[str, Any]:
        """Handle sync_all from fallback
        
        Args:
            payload: Command data
            source_node: Source node
            
        Returns:
            dict: Result data
        """
        logger.info(f"Received fallback sync_all from {source_node}")
        
        # Forward to HUD if connected
        if self.hud_connector.connected:
            self.hud_connector.send_command("sync_all", payload)
            
        # Always forward to lo-fi
        self._send_via_lofi("sync_all", payload, None)
            
        return {"status": "forwarded"}
    
    def _handle_fallback_authority(self, payload: Dict[str, Any], source_node: str) -> Dict[str, Any]:
        """Handle authority from fallback
        
        Args:
            payload: Command data
            source_node: Source node
            
        Returns:
            dict: Result data
        """
        logger.info(f"Received fallback authority from {source_node}")
        
        # Forward to HUD if connected
        if self.hud_connector.connected:
            self.hud_connector.send_command("authority", payload)
            
        # Always forward to lo-fi
        self._send_via_lofi("authority", payload, None)
            
        return {"status": "forwarded"}
    
    def _handle_fallback_page(self, payload: Dict[str, Any], source_node: str) -> Dict[str, Any]:
        """Handle page_change from fallback
        
        Args:
            payload: Command data
            source_node: Source node
            
        Returns:
            dict: Result data
        """
        logger.info(f"Received fallback page_change from {source_node}")
        
        # Forward to HUD if connected
        if self.hud_connector.connected:
            self.hud_connector.send_command("page_change", payload)
            
        return {"status": "forwarded"}
    
    def _handle_fallback_tool(self, payload: Dict[str, Any], source_node: str) -> Dict[str, Any]:
        """Handle tool_activate from fallback
        
        Args:
            payload: Command data
            source_node: Source node
            
        Returns:
            dict: Result data
        """
        logger.info(f"Received fallback tool_activate from {source_node}")
        
        # Forward to HUD if connected
        if self.hud_connector.connected:
            self.hud_connector.send_command("tool_activate", payload)
            
        return {"status": "forwarded"}
    
    def _handle_drop_sync_all(self, payload: Dict[str, Any], source_node: str):
        """Handle sync_all from USB drop
        
        Args:
            payload: Command data
            source_node: Source node
        """
        logger.info(f"Received USB drop sync_all from {source_node}")
        
        # Forward to fallback daemon
        self.fallback_daemon.queue_command(
            command_type="sync_all",
            payload=payload,
            priority=CommandPriority.HIGH
        )
        
        # Forward to HUD if connected
        if self.hud_connector.connected:
            self.hud_connector.send_command("sync_all", payload)
            
        # Always forward to lo-fi
        self._send_via_lofi("sync_all", payload, None)
    
    def _handle_drop_authority(self, payload: Dict[str, Any], source_node: str):
        """Handle authority from USB drop
        
        Args:
            payload: Command data
            source_node: Source node
        """
        logger.info(f"Received USB drop authority from {source_node}")
        
        # Forward to fallback daemon
        self.fallback_daemon.queue_command(
            command_type="authority",
            payload=payload,
            priority=CommandPriority.HIGH
        )
        
        # Forward to HUD if connected
        if self.hud_connector.connected:
            self.hud_connector.send_command("authority", payload)
            
        # Always forward to lo-fi
        self._send_via_lofi("authority", payload, None)
    
    def _handle_drop_page(self, payload: Dict[str, Any], source_node: str):
        """Handle page_change from USB drop
        
        Args:
            payload: Command data
            source_node: Source node
        """
        logger.info(f"Received USB drop page_change from {source_node}")
        
        # Forward to fallback daemon
        self.fallback_daemon.queue_command(
            command_type="page_change",
            payload=payload,
            priority=CommandPriority.MEDIUM
        )
        
        # Forward to HUD if connected
        if self.hud_connector.connected:
            self.hud_connector.send_command("page_change", payload)
    
    def _handle_drop_tool(self, payload: Dict[str, Any], source_node: str):
        """Handle tool_activate from USB drop
        
        Args:
            payload: Command data
            source_node: Source node
        """
        logger.info(f"Received USB drop tool_activate from {source_node}")
        
        # Forward to fallback daemon
        self.fallback_daemon.queue_command(
            command_type="tool_activate",
            payload=payload,
            priority=CommandPriority.MEDIUM
        )
        
        # Forward to HUD if connected
        if self.hud_connector.connected:
            self.hud_connector.send_command("tool_activate", payload)
    
    def _handle_lofi_sync(self, payload: Dict[str, Any], source_node: str) -> Dict[str, Any]:
        """Handle SYNC from lo-fi
        
        Args:
            payload: Command data
            source_node: Source node
            
        Returns:
            dict: Result data
        """
        logger.info(f"Received lo-fi SYNC from {source_node}")
        
        # Extract data
        op = payload.get("op", "sync_all")
        src = payload.get("src", source_node)
        
        # Create full payload
        full_payload = {
            "device_id": src,
            "source": src,
            "timestamp": time.time()
        }
        
        # Forward to fallback daemon
        self.fallback_daemon.queue_command(
            command_type=op,
            payload=full_payload,
            priority=CommandPriority.HIGH
        )
        
        # Forward to HUD if connected
        if self.hud_connector.connected:
            self.hud_connector.send_command(op, full_payload)
            
        return {"status": "synced"}
    
    def _handle_lofi_auth(self, payload: Dict[str, Any], source_node: str) -> Dict[str, Any]:
        """Handle AUTH from lo-fi
        
        Args:
            payload: Command data
            source_node: Source node
            
        Returns:
            dict: Result data
        """
        logger.info(f"Received lo-fi AUTH from {source_node}")
        
        # Extract data
        has_auth = payload.get("auth", False)
        device_id = payload.get("id", source_node)
        src = payload.get("src", source_node)
        
        # Create full payload
        full_payload = {
            "device_id": device_id,
            "has_authority": has_auth,
            "source": src,
            "timestamp": time.time()
        }
        
        # Forward to fallback daemon
        self.fallback_daemon.queue_command(
            command_type="authority",
            payload=full_payload,
            priority=CommandPriority.HIGH
        )
        
        # Forward to HUD if connected
        if self.hud_connector.connected:
            self.hud_connector.send_command("authority", full_payload)
            
        return {"status": "auth_updated"}
    
    def _handle_lofi_mode(self, payload: Dict[str, Any], source_node: str) -> Dict[str, Any]:
        """Handle MODE from lo-fi
        
        Args:
            payload: Command data
            source_node: Source node
            
        Returns:
            dict: Result data
        """
        logger.info(f"Received lo-fi MODE from {source_node}")
        
        # Extract data
        op = payload.get("op", "page_change")
        page = payload.get("page", 1)
        src = payload.get("src", source_node)
        
        # Create full payload
        full_payload = {
            "page": page,
            "source": src,
            "timestamp": time.time()
        }
        
        # Forward to fallback daemon
        self.fallback_daemon.queue_command(
            command_type=op,
            payload=full_payload,
            priority=CommandPriority.MEDIUM
        )
        
        # Forward to HUD if connected
        if self.hud_connector.connected:
            self.hud_connector.send_command(op, full_payload)
            
        return {"status": "mode_updated"}
    
    def get_status(self) -> Dict[str, Any]:
        """Get system status
        
        Returns:
            dict: Status information
        """
        # Get component status
        fallback_status = self.fallback_daemon.get_status()
        
        status = {
            "node_id": self.node_id,
            "is_master": self.is_master,
            "transport_mode": self.transport_mode.value,
            "connectivity": fallback_status["connectivity"],
            "hud_connected": self.hud_connector.connected,
            "usb_available": self.drop_manager.is_usb_available(),
            "peer_count": fallback_status["peer_count"],
            "command_queue_size": fallback_status["command_queue_size"],
            "lofi_nodes": len(self.pinger.get_nodes()),
            "fallback": fallback_status
        }
        
        return status

# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="GhostComms - Internet-Independent Communication Integration")
    
    parser.add_argument("--node-id", required=True, help="Node ID")
    parser.add_argument("--auth-key", default="ghostops", help="Authentication key")
    parser.add_argument("--data-dir", default="./ghost_data", help="Data directory")
    parser.add_argument("--master-ip", help="Master node IP (omit for master node)")
    parser.add_argument("--master-port", type=int, default=7890, help="Master node port")
    
    args = parser.parse_args()
    
    # Create GhostComms system
    system = GhostCommsSystem(
        node_id=args.node_id,
        auth_key=args.auth_key,
        data_dir=args.data_dir,
        master_ip=args.master_ip,
        master_port=args.master_port
    )
    
    # Handle signals
    def signal_handler(sig, frame):
        print("\nStopping GhostComms...")
        system.stop()
        sys.exit(0)
        
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start system
    system.start()
    
    try:
        # Print initial status
        print("GhostComms System Started")
        print("=" * 50)
        print(f"Node ID: {args.node_id}")
        print(f"Role: {'MASTER' if not args.master_ip else 'PEER'}")
        print(f"Data directory: {args.data_dir}")
        print("=" * 50)
        
        # Keep running until Ctrl+C
        while True:
            # Print status every 60 seconds
            status = system.get_status()
            print(f"\nStatus update ({time.strftime('%Y-%m-%d %H:%M:%S')})")
            print(f"Transport mode: {status['transport_mode']}")
            print(f"Connectivity: {status['connectivity']}")
            print(f"HUD connected: {status['hud_connected']}")
            print(f"USB available: {status['usb_available']}")
            print(f"Peers: {status['peer_count']}")
            print(f"Lo-Fi nodes: {status['lofi_nodes']}")
            print(f"Command queue: {status['command_queue_size']}")
            
            time.sleep(60)
            
    except KeyboardInterrupt:
        print("\nStopping GhostComms...")
        system.stop()
        print("Done")

if __name__ == "__main__":
    main()
