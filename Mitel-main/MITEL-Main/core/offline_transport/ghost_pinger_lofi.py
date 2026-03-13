#!/usr/bin/env python3
"""
GhostPinger_LoFi.py - Low Fidelity Communication Transport

Enables minimal command transport between Ghost nodes using extremely low-bandwidth
channels like simulated radio waves, light pulses, or acoustic signals.
This module focuses on sending micro-payloads with minimal but critical commands
when other communication channels are unavailable.

Features:
- Command encoding with minimal bandwidth requirements
- Multiple transport simulations (acoustic, radio, light)
- Heartbeat protocol for node status monitoring
- Future expansion for real hardware (LoRa, Ham radio, infrared)
"""

import os
import sys
import time
import json
import uuid
import logging
import threading
import queue
import signal
import datetime
import random
import string
import hashlib
import hmac
import base64
import binascii
import struct
import socket
from enum import Enum, auto
from typing import Dict, List, Any, Optional, Tuple, Callable, Union, Set
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ghost.lofi")

# =============================================================================
# LOW FIDELITY COMMUNICATION CONSTANTS
# =============================================================================

# Command prefixes for low-fi transport
COMMAND_PREFIX = "[GHOSTCMD]"
HEARTBEAT_PREFIX = "[GHOSTHB]"
ACK_PREFIX = "[GHOSTACK]"
STATUS_PREFIX = "[GHOSTSTAT]"

# Node Roles
ROLE_MASTER = "MASTER"
ROLE_PEER = "PEER"

# Communication medium types
class LoFiMedium(Enum):
    """Available communication medium types"""
    ACOUSTIC = "acoustic"         # Sound-based communication
    RADIO = "radio"               # Radio frequency communication
    LIGHT = "light"               # Light-based communication (blinking LEDs, etc)
    NETWORK = "network"           # Network-based simulation

# Status types
class NodeStatus(Enum):
    """Node status values"""
    UNKNOWN = "UNKNOWN"           # Status not yet determined
    ALIVE = "ALIVE"               # Node is responding to pings
    DEGRADED = "DEGRADED"         # Node is responding but with issues
    DEAD = "DEAD"                 # Node is not responding
    ISOLATED = "ISOLATED"         # Node is isolated from network

# Minimal command set for extremely low bandwidth channels
class LoFiCommand(Enum):
    """Command types that can be sent over lo-fi channels"""
    PING = "PING"                 # Simple ping to check if node is alive
    RESTART = "RESTART"           # Restart service or node
    SHUTDOWN = "SHUTDOWN"         # Shutdown service or node
    RESET = "RESET"               # Reset to default state
    LOCK = "LOCK"                 # Lock access/security lockdown
    UNLOCK = "UNLOCK"             # Unlock access
    STATUS = "STATUS"             # Request status update
    MODE = "MODE"                 # Change operating mode
    SYNC = "SYNC"                 # Trigger sync operation
    ALERT = "ALERT"               # Send security alert
    AUTH = "AUTH"                 # Authentication command
    EXEC = "EXEC"                 # Execute specific operation

# =============================================================================
# ENCODING AND DECODING
# =============================================================================

class LoFiEncoder:
    """Encodes and decodes messages for low-fi transport"""
    
    @staticmethod
    def encode_command(
        command_type: LoFiCommand,
        source_node: str,
        target_node: Optional[str] = None,
        payload: Optional[Dict] = None,
        auth_token: Optional[str] = None,
        compact: bool = False
    ) -> str:
        """Encode a command for lo-fi transport
        
        Args:
            command_type: Command type
            source_node: ID of source node
            target_node: ID of target node (None for broadcast)
            payload: Optional command payload
            auth_token: Authentication token
            compact: Whether to use compact format
            
        Returns:
            str: Encoded command string
        """
        if compact:
            # Ultra-compact format for severely bandwidth-limited channels
            # Format: [CMD]|TYPE|SRC|TGT|TOKEN|PAYLOAD
            cmd_parts = [
                COMMAND_PREFIX,
                command_type.value,
                source_node,
                target_node or "*",  # * for broadcast
                auth_token or "-",   # - for no token
            ]
            
            # Add minimal payload if provided
            if payload:
                # Only include essential fields for minimal size
                compact_payload = {}
                for key, value in payload.items():
                    if key in ["op", "arg", "val", "id"]:
                        compact_payload[key] = value
                
                payload_str = base64.b64encode(json.dumps(compact_payload).encode()).decode()
                cmd_parts.append(payload_str)
            else:
                cmd_parts.append("-")
                
            return "|".join(cmd_parts)
        else:
            # Standard format for normal low-fi channels
            # More readable, less bandwidth efficient
            cmd_data = {
                "type": command_type.value,
                "from": source_node,
                "to": target_node or "broadcast",
                "time": time.time(),
                "id": str(uuid.uuid4())[:8],
            }
            
            # Add authentication if provided
            if auth_token:
                cmd_data["auth"] = auth_token
                
            # Add payload if provided
            if payload:
                cmd_data["payload"] = payload
                
            # Format the command string
            return f"{COMMAND_PREFIX} {json.dumps(cmd_data)}"
    
    @staticmethod
    def encode_heartbeat(
        node_id: str,
        status: NodeStatus,
        auth_token: Optional[str] = None,
        compact: bool = False
    ) -> str:
        """Encode a heartbeat message
        
        Args:
            node_id: ID of node sending heartbeat
            status: Status of the node
            auth_token: Optional authentication token
            compact: Whether to use compact format
            
        Returns:
            str: Encoded heartbeat string
        """
        if compact:
            # Ultra-compact format
            # Format: [HB]|ID|STATUS|TOKEN
            hb_parts = [
                HEARTBEAT_PREFIX,
                node_id,
                status.value,
                auth_token or "-"
            ]
            return "|".join(hb_parts)
        else:
            # Standard format
            hb_data = {
                "node": node_id,
                "status": status.value,
                "time": time.time()
            }
            
            # Add authentication if provided
            if auth_token:
                hb_data["auth"] = auth_token
                
            return f"{HEARTBEAT_PREFIX} {json.dumps(hb_data)}"
    
    @staticmethod
    def encode_ack(
        command_id: str,
        node_id: str,
        success: bool = True,
        auth_token: Optional[str] = None,
        compact: bool = False
    ) -> str:
        """Encode an acknowledgement message
        
        Args:
            command_id: ID of command being acknowledged
            node_id: ID of node sending ack
            success: Whether command was successful
            auth_token: Optional authentication token
            compact: Whether to use compact format
            
        Returns:
            str: Encoded ack string
        """
        if compact:
            # Ultra-compact format
            # Format: [ACK]|ID|NODE|SUCCESS|TOKEN
            ack_parts = [
                ACK_PREFIX,
                command_id,
                node_id,
                "1" if success else "0",
                auth_token or "-"
            ]
            return "|".join(ack_parts)
        else:
            # Standard format
            ack_data = {
                "cmd_id": command_id,
                "node": node_id,
                "success": success,
                "time": time.time()
            }
            
            # Add authentication if provided
            if auth_token:
                ack_data["auth"] = auth_token
                
            return f"{ACK_PREFIX} {json.dumps(ack_data)}"
    
    @staticmethod
    def encode_status(
        node_id: str,
        status: Dict[str, Any],
        auth_token: Optional[str] = None,
        compact: bool = False
    ) -> str:
        """Encode a status message
        
        Args:
            node_id: ID of node sending status
            status: Status information
            auth_token: Optional authentication token
            compact: Whether to use compact format
            
        Returns:
            str: Encoded status string
        """
        if compact:
            # Ultra-compact format
            # Format: [STAT]|ID|STATSTR|TOKEN
            # Create compact status string
            status_str = ""
            for key, val in status.items():
                if key in ["mode", "conn", "auth", "err"]:
                    status_str += f"{key}:{val},"
            
            stat_parts = [
                STATUS_PREFIX,
                node_id,
                status_str.rstrip(","),
                auth_token or "-"
            ]
            return "|".join(stat_parts)
        else:
            # Standard format
            stat_data = {
                "node": node_id,
                "time": time.time(),
                "status": status
            }
            
            # Add authentication if provided
            if auth_token:
                stat_data["auth"] = auth_token
                
            return f"{STATUS_PREFIX} {json.dumps(stat_data)}"
    
    @staticmethod
    def decode_message(message: str) -> Optional[Dict]:
        """Decode a lo-fi message
        
        Args:
            message: Encoded message string
            
        Returns:
            dict: Decoded message or None if invalid
        """
        try:
            message = message.strip()
            
            # Determine message type
            if message.startswith(COMMAND_PREFIX):
                return LoFiEncoder._decode_command(message)
            elif message.startswith(HEARTBEAT_PREFIX):
                return LoFiEncoder._decode_heartbeat(message)
            elif message.startswith(ACK_PREFIX):
                return LoFiEncoder._decode_ack(message)
            elif message.startswith(STATUS_PREFIX):
                return LoFiEncoder._decode_status(message)
            else:
                logger.warning(f"Unknown message type: {message}")
                return None
                
        except Exception as e:
            logger.error(f"Error decoding message: {e}")
            return None
    
    @staticmethod
    def _decode_command(message: str) -> Dict:
        """Decode a command message
        
        Args:
            message: Encoded command string
            
        Returns:
            dict: Decoded command
        """
        # Check for compact format
        if "|" in message:
            # Parse compact format
            parts = message.split("|")
            
            # Need at least prefix, type, source, target, token
            if len(parts) < 5:
                raise ValueError(f"Invalid compact command format: {message}")
                
            result = {
                "message_type": "command",
                "command_type": parts[1],
                "source_node": parts[2],
                "target_node": parts[3] if parts[3] != "*" else None,
                "auth_token": parts[4] if parts[4] != "-" else None,
            }
            
            # Parse payload if present
            if len(parts) >= 6 and parts[5] != "-":
                try:
                    payload_data = json.loads(base64.b64decode(parts[5]).decode())
                    result["payload"] = payload_data
                except:
                    result["payload"] = {"raw": parts[5]}
            
            return result
        else:
            # Parse standard format
            json_str = message[len(COMMAND_PREFIX):].strip()
            data = json.loads(json_str)
            
            result = {
                "message_type": "command",
                "command_type": data.get("type"),
                "source_node": data.get("from"),
                "target_node": data.get("to") if data.get("to") != "broadcast" else None,
                "command_id": data.get("id"),
                "timestamp": data.get("time"),
                "auth_token": data.get("auth"),
                "payload": data.get("payload")
            }
            
            return result
    
    @staticmethod
    def _decode_heartbeat(message: str) -> Dict:
        """Decode a heartbeat message
        
        Args:
            message: Encoded heartbeat string
            
        Returns:
            dict: Decoded heartbeat
        """
        # Check for compact format
        if "|" in message:
            # Parse compact format
            parts = message.split("|")
            
            # Need at least prefix, node_id, status, token
            if len(parts) < 4:
                raise ValueError(f"Invalid compact heartbeat format: {message}")
                
            result = {
                "message_type": "heartbeat",
                "node_id": parts[1],
                "status": parts[2],
                "auth_token": parts[3] if parts[3] != "-" else None,
            }
            
            return result
        else:
            # Parse standard format
            json_str = message[len(HEARTBEAT_PREFIX):].strip()
            data = json.loads(json_str)
            
            result = {
                "message_type": "heartbeat",
                "node_id": data.get("node"),
                "status": data.get("status"),
                "timestamp": data.get("time"),
                "auth_token": data.get("auth")
            }
            
            return result
    
    @staticmethod
    def _decode_ack(message: str) -> Dict:
        """Decode an ack message
        
        Args:
            message: Encoded ack string
            
        Returns:
            dict: Decoded ack
        """
        # Check for compact format
        if "|" in message:
            # Parse compact format
            parts = message.split("|")
            
            # Need at least prefix, cmd_id, node_id, success, token
            if len(parts) < 5:
                raise ValueError(f"Invalid compact ack format: {message}")
                
            result = {
                "message_type": "ack",
                "command_id": parts[1],
                "node_id": parts[2],
                "success": parts[3] == "1",
                "auth_token": parts[4] if parts[4] != "-" else None,
            }
            
            return result
        else:
            # Parse standard format
            json_str = message[len(ACK_PREFIX):].strip()
            data = json.loads(json_str)
            
            result = {
                "message_type": "ack",
                "command_id": data.get("cmd_id"),
                "node_id": data.get("node"),
                "success": data.get("success", True),
                "timestamp": data.get("time"),
                "auth_token": data.get("auth")
            }
            
            return result
    
    @staticmethod
    def _decode_status(message: str) -> Dict:
        """Decode a status message
        
        Args:
            message: Encoded status string
            
        Returns:
            dict: Decoded status
        """
        # Check for compact format
        if "|" in message:
            # Parse compact format
            parts = message.split("|")
            
            # Need at least prefix, node_id, status_str, token
            if len(parts) < 4:
                raise ValueError(f"Invalid compact status format: {message}")
                
            # Parse status string
            status_data = {}
            status_parts = parts[2].split(",")
            for status_part in status_parts:
                if ":" in status_part:
                    key, val = status_part.split(":", 1)
                    status_data[key] = val
                
            result = {
                "message_type": "status",
                "node_id": parts[1],
                "status": status_data,
                "auth_token": parts[3] if parts[3] != "-" else None,
            }
            
            return result
        else:
            # Parse standard format
            json_str = message[len(STATUS_PREFIX):].strip()
            data = json.loads(json_str)
            
            result = {
                "message_type": "status",
                "node_id": data.get("node"),
                "status": data.get("status", {}),
                "timestamp": data.get("time"),
                "auth_token": data.get("auth")
            }
            
            return result

# =============================================================================
# LOFI COMMUNICATION MEDIUMS
# =============================================================================

class LoFiMediumInterface:
    """Base interface for lo-fi communication mediums"""
    
    def __init__(self, medium_type: LoFiMedium, node_id: str):
        """Initialize the communication medium
        
        Args:
            medium_type: Type of medium
            node_id: ID of this node
        """
        self.medium_type = medium_type
        self.node_id = node_id
        self.is_running = False
        self.receive_callbacks = []
        
    def start(self):
        """Start the communication medium"""
        raise NotImplementedError("Subclasses must implement this method")
        
    def stop(self):
        """Stop the communication medium"""
        raise NotImplementedError("Subclasses must implement this method")
        
    def send_message(self, message: str) -> bool:
        """Send a message over the medium
        
        Args:
            message: Message to send
            
        Returns:
            bool: Success status
        """
        raise NotImplementedError("Subclasses must implement this method")
        
    def register_receive_callback(self, callback: Callable[[str, Dict[str, Any]], None]):
        """Register a callback for received messages
        
        Args:
            callback: Function to call when message is received
                     Takes (raw_message, message_data) as arguments
        """
        if callback not in self.receive_callbacks:
            self.receive_callbacks.append(callback)
            
    def unregister_receive_callback(self, callback):
        """Unregister a receive callback"""
        if callback in self.receive_callbacks:
            self.receive_callbacks.remove(callback)
            
    def _notify_message_received(self, raw_message: str, message_data: Dict[str, Any]):
        """Notify all callbacks about received message
        
        Args:
            raw_message: Raw message string
            message_data: Parsed message data
        """
        for callback in self.receive_callbacks:
            try:
                callback(raw_message, message_data)
            except Exception as e:
                logger.error(f"Error in receive callback: {e}")

class NetworkLoFiMedium(LoFiMediumInterface):
    """Network-based lo-fi communication medium
    
    This medium uses UDP broadcasting to simulate radio/acoustic communication
    """
    
    def __init__(
        self, 
        node_id: str,
        listen_port: int = 9876,
        broadcast_port: int = 9876,
        broadcast_addr: str = "255.255.255.255",
        simulate_loss: float = 0.0
    ):
        """Initialize the network medium
        
        Args:
            node_id: ID of this node
            listen_port: Port to listen on
            broadcast_port: Port to broadcast to
            broadcast_addr: Broadcast address
            simulate_loss: Packet loss rate (0.0-1.0)
        """
        super().__init__(LoFiMedium.NETWORK, node_id)
        self.listen_port = listen_port
        self.broadcast_port = broadcast_port
        self.broadcast_addr = broadcast_addr
        self.simulate_loss = simulate_loss
        
        self._listen_socket = None
        self._broadcast_socket = None
        self._listen_thread = None
        self._stop_event = threading.Event()
        
    def start(self):
        """Start the network medium"""
        if self.is_running:
            return
            
        # Create listen socket
        self._listen_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._listen_socket.bind(("0.0.0.0", self.listen_port))
        
        # Create broadcast socket
        self._broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        
        # Start listening thread
        self._stop_event.clear()
        self._listen_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._listen_thread.start()
        
        self.is_running = True
        logger.info(f"Network lo-fi medium started (port {self.listen_port})")
        
    def stop(self):
        """Stop the network medium"""
        if not self.is_running:
            return
            
        # Stop listening thread
        self._stop_event.set()
        if self._listen_thread:
            self._listen_thread.join(timeout=1)
            
        # Close sockets
        if self._listen_socket:
            self._listen_socket.close()
            
        if self._broadcast_socket:
            self._broadcast_socket.close()
            
        self.is_running = False
        logger.info("Network lo-fi medium stopped")
        
    def send_message(self, message: str) -> bool:
        """Send a message over the network
        
        Args:
            message: Message to send
            
        Returns:
            bool: Success status
        """
        if not self.is_running:
            logger.warning("Cannot send message, medium not running")
            return False
            
        try:
            # Simulate packet loss
            if random.random() < self.simulate_loss:
                logger.debug(f"Simulated packet loss: {message}")
                return True  # Return success even though it was dropped
                
            # Send message
            data = message.encode("utf-8")
            self._broadcast_socket.sendto(data, (self.broadcast_addr, self.broadcast_port))
            
            logger.debug(f"Sent message: {message}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False
            
    def _listen_loop(self):
        """Listen for incoming messages"""
        self._listen_socket.settimeout(0.5)
        
        while not self._stop_event.is_set():
            try:
                data, addr = self._listen_socket.recvfrom(4096)
                message = data.decode("utf-8")
                
                # Skip messages from self
                if message.find(f"from\":\"{self.node_id}\"") >= 0 or message.find(f"|{self.node_id}|") >= 0:
                    continue
                
                logger.debug(f"Received message: {message}")
                
                # Parse message
                try:
                    message_data = LoFiEncoder.decode_message(message)
                    if message_data:
                        self._notify_message_received(message, message_data)
                except Exception as e:
                    logger.error(f"Error parsing message: {e}")
                
            except socket.timeout:
                # Timeout is expected, just check stop event
                pass
            except Exception as e:
                logger.error(f"Error in listen loop: {e}")
                time.sleep(1)

class AcousticLoFiMedium(LoFiMediumInterface):
    """Simulated acoustic lo-fi communication
    
    This medium simulates acoustic communication by writing messages to a file
    and reading from it periodically, with simulated delay and interference.
    """
    
    def __init__(
        self, 
        node_id: str,
        channel_file: str = None,
        read_interval: float = 1.0,
        simulate_noise: float = 0.1,
        simulate_delay: float = 0.5
    ):
        """Initialize the acoustic medium
        
        Args:
            node_id: ID of this node
            channel_file: Path to channel file (None for default)
            read_interval: Interval in seconds between reads
            simulate_noise: Noise level (0.0-1.0)
            simulate_delay: Delay in seconds
        """
        super().__init__(LoFiMedium.ACOUSTIC, node_id)
        
        # Use default channel file if not provided
        if channel_file:
            self.channel_file = channel_file
        else:
            self.channel_file = os.path.expanduser("~/.ghost/acoustic_channel.txt")
            os.makedirs(os.path.dirname(self.channel_file), exist_ok=True)
            
        self.read_interval = read_interval
        self.simulate_noise = simulate_noise
        self.simulate_delay = simulate_delay
        
        self._read_thread = None
        self._stop_event = threading.Event()
        self._processed_messages = set()
        
    def start(self):
        """Start the acoustic medium"""
        if self.is_running:
            return
            
        # Ensure channel file exists
        if not os.path.exists(self.channel_file):
            with open(self.channel_file, 'w') as f:
                f.write("")
                
        # Start reading thread
        self._stop_event.clear()
        self._read_thread = threading.Thread(target=self._read_loop, daemon=True)
        self._read_thread.start()
        
        self.is_running = True
        logger.info(f"Acoustic lo-fi medium started (file {self.channel_file})")
        
    def stop(self):
        """Stop the acoustic medium"""
        if not self.is_running:
            return
            
        # Stop reading thread
        self._stop_event.set()
        if self._read_thread:
            self._read_thread.join(timeout=1)
            
        self.is_running = False
        logger.info("Acoustic lo-fi medium stopped")
        
    def send_message(self, message: str) -> bool:
        """Send a message over the acoustic medium
        
        Args:
            message: Message to send
            
        Returns:
            bool: Success status
        """
        if not self.is_running:
            logger.warning("Cannot send message, medium not running")
            return False
            
        try:
            # Add a unique message ID for deduplication
            message_id = hashlib.md5(message.encode()).hexdigest()[:8]
            timestamped_message = f"{message_id}:{time.time()}:{message}"
            
            # Simulate delay
            if self.simulate_delay > 0:
                time.sleep(self.simulate_delay)
                
            # Append to channel file
            with open(self.channel_file, 'a') as f:
                f.write(timestamped_message + "\n")
                
            logger.debug(f"Sent acoustic message: {message}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending acoustic message: {e}")
            return False
            
    def _read_loop(self):
        """Read incoming messages from channel file"""
        while not self._stop_event.is_set():
            try:
                # Wait for read interval
                self._stop_event.wait(self.read_interval)
                if self._stop_event.is_set():
                    break
                    
                # Read channel file
                messages = []
                try:
                    with open(self.channel_file, 'r') as f:
                        messages = f.readlines()
                except Exception:
                    # File might not exist yet
                    continue
                
                if not messages:
                    continue
                    
                # Process new messages
                for line in messages:
                    line = line.strip()
                    if not line:
                        continue
                        
                    # Split message ID, timestamp and content
                    parts = line.split(":", 2)
                    if len(parts) < 3:
                        continue
                        
                    msg_id, timestamp_str, message = parts
                    
                    # Skip if already processed
                    if msg_id in self._processed_messages:
                        continue
                        
                    # Add to processed set
                    self._processed_messages.add(msg_id)
                    
                    # Simulate noise
                    if random.random() < self.simulate_noise:
                        # Corrupt message
                        chars = list(message)
                        for i in range(int(len(chars) * self.simulate_noise)):
                            idx = random.randint(0, len(chars) - 1)
                            chars[idx] = random.choice(string.printable)
                        message = "".join(chars)
                    
                    # Parse message
                    try:
                        message_data = LoFiEncoder.decode_message(message)
                        if message_data:
                            # Notify callbacks
                            self._notify_message_received(message, message_data)
                    except Exception as e:
                        logger.error(f"Error parsing acoustic message: {e}")
                    
                # Limit size of processed messages set
                if len(self._processed_messages) > 1000:
                    # Keep the 500 most recent
                    self._processed_messages = set(list(self._processed_messages)[-500:])
                    
            except Exception as e:
                logger.error(f"Error in acoustic read loop: {e}")
                time.sleep(1)

# =============================================================================
# GHOST PINGER CORE
# =============================================================================

class GhostPinger:
    """Core class for lo-fi communication between Ghost nodes"""
    
    def __init__(
        self, 
        node_id: str,
        role: str = ROLE_PEER,
        auth_key: Optional[str] = None,
        data_dir: str = None,
        medium_type: LoFiMedium = LoFiMedium.NETWORK,
        config: Dict[str, Any] = None
    ):
        """Initialize the pinger
        
        Args:
            node_id: ID of this node
            role: Node role (MASTER or PEER)
            auth_key: Authentication key
            data_dir: Path to data directory
            medium_type: Communication medium type
            config: Additional configuration
        """
        self.node_id = node_id
        self.role = role
        self.auth_key = auth_key
        
        # Set up data directory
        if data_dir:
            self.data_dir = data_dir
        else:
            self.data_dir = os.path.expanduser("~/.ghost")
            
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Default configuration
        self.config = {
            "heartbeat_interval": 30,
            "heartbeat_timeout": 90,
            "retry_count": 3,
            "retry_delay": 2,
            "compact_format": True
        }
        
        # Apply custom config
        if config:
            self.config.update(config)
            
        # Create medium
        self.medium_type = medium_type
        self._create_medium()
        
        # Command handlers
        self.command_handlers = {}
        
        # Node tracking
        self.nodes = {}
        
        # Status and heartbeat
        self._heartbeat_thread = None
        self._status_thread = None
        self._stop_event = threading.Event()
        
        # Register for message callbacks
        self.medium.register_receive_callback(self._handle_message)
        
        # Register default command handlers
        self._register_default_handlers()
        
        logger.info(f"GhostPinger initialized for node {node_id} ({role})")
    
    def _create_medium(self):
        """Create the communication medium based on type"""
        if self.medium_type == LoFiMedium.NETWORK:
            # Configure network medium
            port = self.config.get("network_port", 9876)
            broadcast_addr = self.config.get("broadcast_addr", "255.255.255.255")
            simulate_loss = self.config.get("simulate_loss", 0.0)
            
            self.medium = NetworkLoFiMedium(
                node_id=self.node_id,
                listen_port=port,
                broadcast_port=port,
                broadcast_addr=broadcast_addr,
                simulate_loss=simulate_loss
            )
            
        elif self.medium_type == LoFiMedium.ACOUSTIC:
            # Configure acoustic medium
            channel_file = self.config.get("channel_file")
            read_interval = self.config.get("read_interval", 1.0)
            simulate_noise = self.config.get("simulate_noise", 0.1)
            simulate_delay = self.config.get("simulate_delay", 0.5)
            
            self.medium = AcousticLoFiMedium(
                node_id=self.node_id,
                channel_file=channel_file,
                read_interval=read_interval,
                simulate_noise=simulate_noise,
                simulate_delay=simulate_delay
            )
            
        elif self.medium_type == LoFiMedium.RADIO:
            # Simulated as network for now
            logger.info("Radio medium simulated using network")
            port = self.config.get("network_port", 9877)
            broadcast_addr = self.config.get("broadcast_addr", "255.255.255.255")
            simulate_loss = self.config.get("simulate_loss", 0.1)
            
            self.medium = NetworkLoFiMedium(
                node_id=self.node_id,
                listen_port=port,
                broadcast_port=port,
                broadcast_addr=broadcast_addr,
                simulate_loss=simulate_loss
            )
            
        elif self.medium_type == LoFiMedium.LIGHT:
            # Simulated as acoustic for now
            logger.info("Light medium simulated using acoustic")
            channel_file = self.config.get("channel_file")
            read_interval = self.config.get("read_interval", 0.5)
            simulate_noise = self.config.get("simulate_noise", 0.2)
            simulate_delay = self.config.get("simulate_delay", 0.2)
            
            self.medium = AcousticLoFiMedium(
                node_id=self.node_id,
                channel_file=channel_file,
                read_interval=read_interval,
                simulate_noise=simulate_noise,
                simulate_delay=simulate_delay
            )
            
        else:
            # Default to network
            logger.warning(f"Unknown medium type {self.medium_type}, using network")
            self.medium = NetworkLoFiMedium(node_id=self.node_id)
    
    def _register_default_handlers(self):
        """Register default command handlers"""
        self.register_command_handler(LoFiCommand.PING.value, self._handle_ping)
        self.register_command_handler(LoFiCommand.STATUS.value, self._handle_status_request)
        self.register_command_handler(LoFiCommand.RESTART.value, self._handle_restart)
        self.register_command_handler(LoFiCommand.SHUTDOWN.value, self._handle_shutdown)
        self.register_command_handler(LoFiCommand.MODE.value, self._handle_mode_change)
    
    def start(self):
        """Start the pinger"""
        # Start the medium
        self.medium.start()
        
        # Start heartbeat thread
        if self.config.get("heartbeat_interval") > 0:
            self._stop_event.clear()
            self._heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
            self._heartbeat_thread.start()
            
            # Send initial heartbeat
            self._send_heartbeat()
            
        logger.info("GhostPinger started")
    
    def stop(self):
        """Stop the pinger"""
        # Stop threads
        self._stop_event.set()
        
        if self._heartbeat_thread:
            self._heartbeat_thread.join(timeout=1)
            
        if self._status_thread:
            self._status_thread.join(timeout=1)
            
        # Stop medium
        self.medium.stop()
        
        logger.info("GhostPinger stopped")
    
    def register_command_handler(self, command_type: str, handler: Callable[[Dict, str], Any]):
        """Register a handler for a command type
        
        Args:
            command_type: Type of command to handle
            handler: Function to call for this command type
                     Takes (payload, source_node) as arguments
        """
        self.command_handlers[command_type] = handler
    
    def unregister_command_handler(self, command_type: str):
        """Unregister a command handler
        
        Args:
            command_type: Type of command to unregister
        """
        if command_type in self.command_handlers:
            del self.command_handlers[command_type]
    
    def send_command(
        self, 
        command_type: LoFiCommand,
        target_node: Optional[str] = None,
        payload: Optional[Dict] = None,
        retry_count: Optional[int] = None,
        retry_delay: Optional[float] = None
    ) -> Optional[str]:
        """Send a command to another node
        
        Args:
            command_type: Type of command
            target_node: Target node ID (None for broadcast)
            payload: Command payload
            retry_count: Number of retries (None for default)
            retry_delay: Delay between retries (None for default)
            
        Returns:
            str: Command ID or None on failure
        """
        # Get retry parameters
        retry_count = retry_count if retry_count is not None else self.config.get("retry_count", 3)
        retry_delay = retry_delay if retry_delay is not None else self.config.get("retry_delay", 2)
        
        # Generate command string
        command_str = LoFiEncoder.encode_command(
            command_type=command_type,
            source_node=self.node_id,
            target_node=target_node,
            payload=payload,
            auth_token=self.auth_key,
            compact=self.config.get("compact_format", True)
        )
        
        # Send with retries
        for attempt in range(retry_count + 1):
            success = self.medium.send_message(command_str)
            if success:
                # Extract command ID for return
                try:
                    data = LoFiEncoder.decode_message(command_str)
                    if data and "command_id" in data:
                        return data["command_id"]
                except:
                    pass
                    
                return "success"  # Return a placeholder on success
                
            if attempt < retry_count:
                # Wait before retry
                time.sleep(retry_delay)
                
        return None
    
    def send_heartbeat(self, status: NodeStatus = NodeStatus.ALIVE) -> bool:
        """Send a heartbeat message
        
        Args:
            status: Status to report
            
        Returns:
            bool: Success status
        """
        return self._send_heartbeat(status)
    
    def send_status(self, status_data: Dict[str, Any]) -> bool:
        """Send a status update
        
        Args:
            status_data: Status information
            
        Returns:
            bool: Success status
        """
        # Generate status message
        status_str = LoFiEncoder.encode_status(
            node_id=self.node_id,
            status=status_data,
            auth_token=self.auth_key,
            compact=self.config.get("compact_format", True)
        )
        
        # Send message
        return self.medium.send_message(status_str)
    
    def _handle_message(self, raw_message: str, message_data: Dict[str, Any]):
        """Handle a received message
        
        Args:
            raw_message: Raw message string
            message_data: Parsed message data
        """
        if not message_data:
            return
            
        # Check auth token if required
        if self.auth_key and message_data.get("auth_token") != self.auth_key:
            logger.warning(f"Rejected message with invalid auth token")
            return
            
        # Determine message type
        message_type = message_data.get("message_type")
        
        if message_type == "command":
            self._handle_command_message(message_data)
        elif message_type == "heartbeat":
            self._handle_heartbeat_message(message_data)
        elif message_type == "ack":
            self._handle_ack_message(message_data)
        elif message_type == "status":
            self._handle_status_message(message_data)
    
    def _handle_command_message(self, command_data: Dict[str, Any]):
        """Handle a command message
        
        Args:
            command_data: Command data
        """
        # Extract command info
        command_type = command_data.get("command_type")
        source_node = command_data.get("source_node")
        target_node = command_data.get("target_node")
        command_id = command_data.get("command_id", "unknown")
        payload = command_data.get("payload", {})
        
        # Check if this command is for us
        if target_node and target_node != self.node_id:
            # Not for us
            return
            
        logger.info(f"Received command {command_type} from {source_node}")
        
        # Update node status
        self._update_node_status(source_node, NodeStatus.ALIVE)
        
        # Find handler for this command type
        handler = self.command_handlers.get(command_type)
        if handler:
            try:
                # Execute handler
                result = handler(payload, source_node)
                
                # Send ACK if we have a command ID
                if command_id != "unknown":
                    self._send_ack(command_id, source_node, True)
                    
                return result
            except Exception as e:
                logger.error(f"Error executing command handler: {e}")
                
                # Send failed ACK
                if command_id != "unknown":
                    self._send_ack(command_id, source_node, False)
        else:
            logger.warning(f"No handler for command type {command_type}")
    
    def _handle_heartbeat_message(self, heartbeat_data: Dict[str, Any]):
        """Handle a heartbeat message
        
        Args:
            heartbeat_data: Heartbeat data
        """
        node_id = heartbeat_data.get("node_id")
        status_str = heartbeat_data.get("status")
        
        # Convert status string to enum
        status = NodeStatus.UNKNOWN
        try:
            status = NodeStatus(status_str)
        except:
            # Invalid status
            pass
            
        logger.debug(f"Received heartbeat from {node_id} ({status_str})")
        
        # Update node status
        self._update_node_status(node_id, status)
    
    def _handle_ack_message(self, ack_data: Dict[str, Any]):
        """Handle an ack message
        
        Args:
            ack_data: ACK data
        """
        command_id = ack_data.get("command_id")
        node_id = ack_data.get("node_id")
        success = ack_data.get("success", True)
        
        logger.info(f"Received ACK for command {command_id} from {node_id}: {'Success' if success else 'Failed'}")
        
        # Update node status
        self._update_node_status(node_id, NodeStatus.ALIVE)
    
    def _handle_status_message(self, status_data: Dict[str, Any]):
        """Handle a status message
        
        Args:
            status_data: Status data
        """
        node_id = status_data.get("node_id")
        status = status_data.get("status", {})
        
        logger.info(f"Received status from {node_id}: {status}")
        
        # Update node status
        self._update_node_status(node_id, NodeStatus.ALIVE)
        
        # Store status information
        if node_id in self.nodes:
            self.nodes[node_id]["status"] = status
        else:
            self.nodes[node_id] = {
                "id": node_id,
                "status": status,
                "last_seen": time.time(),
                "node_status": NodeStatus.ALIVE
            }
    
    def _heartbeat_loop(self):
        """Send periodic heartbeats"""
        interval = self.config.get("heartbeat_interval", 30)
        
        while not self._stop_event.is_set():
            # Send heartbeat
            self._send_heartbeat()
            
            # Check node timeouts
            self._check_node_timeouts()
            
            # Wait for next interval
            self._stop_event.wait(interval)
    
    def _send_heartbeat(self, status: NodeStatus = NodeStatus.ALIVE) -> bool:
        """Send a heartbeat message
        
        Args:
            status: Status to report
            
        Returns:
            bool: Success status
        """
        # Generate heartbeat message
        heartbeat_str = LoFiEncoder.encode_heartbeat(
            node_id=self.node_id,
            status=status,
            auth_token=self.auth_key,
            compact=self.config.get("compact_format", True)
        )
        
        # Send message
        return self.medium.send_message(heartbeat_str)
    
    def _send_ack(self, command_id: str, target_node: str, success: bool) -> bool:
        """Send an acknowledgement message
        
        Args:
            command_id: ID of command being acknowledged
            target_node: Target node ID
            success: Whether command was successful
            
        Returns:
            bool: Success status
        """
        # Generate ack message
        ack_str = LoFiEncoder.encode_ack(
            command_id=command_id,
            node_id=self.node_id,
            success=success,
            auth_token=self.auth_key,
            compact=self.config.get("compact_format", True)
        )
        
        # Send message
        return self.medium.send_message(ack_str)
    
    def _update_node_status(self, node_id: str, status: NodeStatus):
        """Update a node's status
        
        Args:
            node_id: ID of node
            status: New status
        """
        now = time.time()
        
        if node_id in self.nodes:
            # Update existing node
            self.nodes[node_id]["last_seen"] = now
            self.nodes[node_id]["node_status"] = status
        else:
            # Add new node
            self.nodes[node_id] = {
                "id": node_id,
                "last_seen": now,
                "node_status": status,
                "status": {}
            }
    
    def _check_node_timeouts(self):
        """Check for nodes that have timed out"""
        now = time.time()
        timeout = self.config.get("heartbeat_timeout", 90)
        
        for node_id, node in list(self.nodes.items()):
            # Skip self
            if node_id == self.node_id:
                continue
                
            # Check timeout
            if now - node["last_seen"] > timeout:
                # Node has timed out
                if node["node_status"] != NodeStatus.DEAD:
                    logger.info(f"Node {node_id} timed out")
                    node["node_status"] = NodeStatus.DEAD
    
    def get_nodes(self) -> Dict[str, Dict]:
        """Get all known nodes
        
        Returns:
            dict: Node information by ID
        """
        return self.nodes.copy()
    
    def get_node(self, node_id: str) -> Optional[Dict]:
        """Get information about a specific node
        
        Args:
            node_id: ID of node
            
        Returns:
            dict: Node information or None if not found
        """
        return self.nodes.get(node_id)
    
    def is_node_alive(self, node_id: str) -> bool:
        """Check if a node is alive
        
        Args:
            node_id: ID of node
            
        Returns:
            bool: True if node is alive
        """
        node = self.nodes.get(node_id)
        if not node:
            return False
            
        return node["node_status"] in [NodeStatus.ALIVE, NodeStatus.DEGRADED]
    
    # Default command handlers
    
    def _handle_ping(self, payload: Dict[str, Any], source_node: str) -> Dict[str, Any]:
        """Handle ping command
        
        Args:
            payload: Command payload
            source_node: Source node ID
            
        Returns:
            dict: Response data
        """
        logger.info(f"Ping from {source_node}")
        
        # Send a status update in response
        self.send_status({
            "mode": self.config.get("mode", "normal"),
            "conn": self.medium_type.value,
            "role": self.role
        })
        
        return {
            "status": "pong",
            "timestamp": time.time(),
            "node_id": self.node_id
        }
    
    def _handle_status_request(self, payload: Dict[str, Any], source_node: str) -> Dict[str, Any]:
        """Handle status request command
        
        Args:
            payload: Command payload
            source_node: Source node ID
            
        Returns:
            dict: Response data
        """
        logger.info(f"Status request from {source_node}")
        
        # Get status info
        status_data = {
            "mode": self.config.get("mode", "normal"),
            "conn": self.medium_type.value,
            "role": self.role,
            "uptime": time.time() - self.config.get("start_time", time.time()),
            "nodes": len(self.nodes)
        }
        
        # Send status update
        self.send_status(status_data)
        
        return {
            "status": "status_sent",
            "timestamp": time.time(),
            "node_id": self.node_id
        }
    
    def _handle_restart(self, payload: Dict[str, Any], source_node: str) -> Dict[str, Any]:
        """Handle restart command
        
        Args:
            payload: Command payload
            source_node: Source node ID
            
        Returns:
            dict: Response data
        """
        target = payload.get("target", "service")
        logger.info(f"Restart command from {source_node} (target: {target})")
        
        # This would need to be implemented with actual restart functionality
        
        return {
            "status": "restart_initiated",
            "target": target,
            "timestamp": time.time(),
            "node_id": self.node_id
        }
    
    def _handle_shutdown(self, payload: Dict[str, Any], source_node: str) -> Dict[str, Any]:
        """Handle shutdown command
        
        Args:
            payload: Command payload
            source_node: Source node ID
            
        Returns:
            dict: Response data
        """
        target = payload.get("target", "service")
        logger.info(f"Shutdown command from {source_node} (target: {target})")
        
        # This would need to be implemented with actual shutdown functionality
        
        return {
            "status": "shutdown_initiated",
            "target": target,
            "timestamp": time.time(),
            "node_id": self.node_id
        }
    
    def _handle_mode_change(self, payload: Dict[str, Any], source_node: str) -> Dict[str, Any]:
        """Handle mode change command
        
        Args:
            payload: Command payload
            source_node: Source node ID
            
        Returns:
            dict: Response data
        """
        mode = payload.get("mode", "normal")
        logger.info(f"Mode change command from {source_node}: {mode}")
        
        # Change mode in config
        old_mode = self.config.get("mode", "normal")
        self.config["mode"] = mode
        
        return {
            "status": "mode_changed",
            "old_mode": old_mode,
            "new_mode": mode,
            "timestamp": time.time(),
            "node_id": self.node_id
        }

# =============================================================================
# COMMAND LINE INTERFACE
# =============================================================================

def main():
    """Main entry point for CLI"""
    import argparse
    
    parser = argparse.ArgumentParser(description="GhostPinger - Low-Fi Communication for GhostOps")
    subparsers = parser.add_subparsers(dest="command", help="Command")
    
    # Start command
    start_parser = subparsers.add_parser("start", help="Start the pinger")
    start_parser.add_argument("--node-id", required=True, help="ID of this node")
    start_parser.add_argument("--role", choices=["MASTER", "PEER"], default="PEER", help="Node role")
    start_parser.add_argument("--medium", choices=[m.value for m in LoFiMedium], default="network", help="Medium type")
    start_parser.add_argument("--port", type=int, default=9876, help="Network port")
    start_parser.add_argument("--auth-key", help="Authentication key")
    
    # Send command
    send_parser = subparsers.add_parser("send", help="Send a command")
    send_parser.add_argument("--node-id", required=True, help="ID of this node")
    send_parser.add_argument("--target", help="Target node ID (omit for broadcast)")
    send_parser.add_argument("--medium", choices=[m.value for m in LoFiMedium], default="network", help="Medium type")
    send_parser.add_argument("--port", type=int, default=9876, help="Network port")
    send_parser.add_argument("--auth-key", help="Authentication key")
    send_parser.add_argument("--type", required=True, choices=[c.value for c in LoFiCommand], help="Command type")
    send_parser.add_argument("--payload", help="Command payload in JSON format")
    
    # Monitor command
    monitor_parser = subparsers.add_parser("monitor", help="Monitor for commands")
    monitor_parser.add_argument("--node-id", required=True, help="ID of this node")
    monitor_parser.add_argument("--medium", choices=[m.value for m in LoFiMedium], default="network", help="Medium type")
    monitor_parser.add_argument("--port", type=int, default=9876, help="Network port")
    monitor_parser.add_argument("--auth-key", help="Authentication key")
    
    args = parser.parse_args()
    
    # Handle commands
    if args.command == "start":
        # Create config
        config = {
            "network_port": args.port,
            "start_time": time.time(),
            "heartbeat_interval": 30,
            "mode": "normal"
        }
        
        # Create pinger
        pinger = GhostPinger(
            node_id=args.node_id,
            role=args.role,
            auth_key=args.auth_key,
            medium_type=LoFiMedium(args.medium),
            config=config
        )
        
        try:
            print(f"Starting GhostPinger for {args.node_id} ({args.role})...")
            pinger.start()
            
            # Keep running until Ctrl+C
            while True:
                # Print status every 60 seconds
                time.sleep(60)
                nodes = pinger.get_nodes()
                print(f"Known nodes ({len(nodes)}):")
                for node_id, node in nodes.items():
                    status = node["node_status"].value
                    last_seen = time.time() - node["last_seen"]
                    print(f"  {node_id}: {status} (last seen {last_seen:.1f}s ago)")
                
        except KeyboardInterrupt:
            print("\nStopping pinger...")
            pinger.stop()
            print("Done")
    
    elif args.command == "send":
        # Create config
        config = {
            "network_port": args.port,
            "start_time": time.time(),
            "heartbeat_interval": 0,  # No heartbeats for one-shot send
        }
        
        # Create pinger
        pinger = GhostPinger(
            node_id=args.node_id,
            role="PEER",
            auth_key=args.auth_key,
            medium_type=LoFiMedium(args.medium),
            config=config
        )
        
        try:
            print(f"Sending {args.type} command from {args.node_id} to {args.target or 'broadcast'}...")
            pinger.start()
            
            # Parse payload
            payload = None
            if args.payload:
                payload = json.loads(args.payload)
                
            # Send command
            command_id = pinger.send_command(
                command_type=LoFiCommand(args.type),
                target_node=args.target,
                payload=payload,
                retry_count=2
            )
            
            if command_id:
                print(f"Command sent successfully (ID: {command_id})")
                
                # Wait a bit for responses
                print("Waiting for responses...")
                time.sleep(5)
                
                # Print any responses
                nodes = pinger.get_nodes()
                if nodes:
                    print(f"Responses received from {len(nodes)} nodes:")
                    for node_id, node in nodes.items():
                        print(f"  {node_id}: {node['node_status'].value}")
                else:
                    print("No responses received")
            else:
                print("Failed to send command")
                
            # Stop pinger
            pinger.stop()
            
        except Exception as e:
            print(f"Error sending command: {e}")
    
    elif args.command == "monitor":
        # Create config
        config = {
            "network_port": args.port,
            "start_time": time.time(),
            "heartbeat_interval": 0,  # No heartbeats for monitor only
        }
        
        # Create pinger
        pinger = GhostPinger(
            node_id=args.node_id,
            role="PEER",
            auth_key=args.auth_key,
            medium_type=LoFiMedium(args.medium),
            config=config
        )
        
        # Set up command handler to print
        def print_command(payload, source_node):
            print(f"\nCommand from {source_node}:")
            print(f"  Payload: {payload}")
            return {"status": "received"}
            
        # Register handler for all command types
        for cmd_type in [c.value for c in LoFiCommand]:
            pinger.register_command_handler(cmd_type, print_command)
            
        try:
            print(f"Monitoring for commands as {args.node_id}...")
            pinger.start()
            
            # Send initial status
            pinger.send_status({
                "mode": "monitor",
                "conn": args.medium,
                "role": "PEER"
            })
            
            # Keep running until Ctrl+C
            while True:
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\nStopping monitor...")
            pinger.stop()
            print("Done")
    
    else:
        parser.print_help()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
