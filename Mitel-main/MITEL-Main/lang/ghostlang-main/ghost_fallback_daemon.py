#!/usr/bin/env python3
"""
GhostFallbackDaemon.py - Internet-Independent Ghost Operations

Maintains mesh network communications when internet connectivity is lost,
by switching to alternative transport mechanisms including:
- USB drives (sneakernet)
- Local mesh networks (without internet dependency)
- Offline command buffering with opportunistic synchronization
- Future: LoRa, Ham radio, acoustic, etc.

Features:
- Continuous monitoring of internet connectivity
- Automatic mode switching based on connectivity status
- Command queue buffering and replay when connectivity returns
- Support for physical transport via USB drives ("sneakernet")
- Seamless integration with existing GhostHUD mesh architecture
"""

import os
import sys
import time
import json
import uuid
import socket
import logging
import threading
import queue
import signal
import datetime
import subprocess
import asyncio
import hashlib
import hmac
import base64
import urllib.request
from enum import Enum, auto
from typing import Dict, List, Any, Optional, Tuple, Callable
from pathlib import Path
import random

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ghost.fallback")

# =============================================================================
# CONNECTIVITY MANAGEMENT
# =============================================================================

class ConnectivityStatus(Enum):
    """Connectivity status levels"""
    ONLINE = auto()          # Full internet access
    DEGRADED = auto()        # Limited internet access
    LOCAL_ONLY = auto()      # No internet, but local network is available
    ISOLATED = auto()        # No connectivity, node is isolated
    UNKNOWN = auto()         # Status not yet determined

class TransportMode(Enum):
    """Available transport modes"""
    INTERNET = "internet"       # Normal internet-based transport
    MESH_ONLY = "mesh_only"     # Mesh network only, no internet
    USB = "usb"                 # USB sneakernet mode
    LO_FI = "lo_fi"             # Low-fidelity backup transport (future)

class GhostConnectivityMonitor:
    """Monitors internet and network connectivity"""
    
    def __init__(self, check_interval: int = 30):
        """Initialize the connectivity monitor
        
        Args:
            check_interval: Interval in seconds between connectivity checks
        """
        self.check_interval = check_interval
        self.status = ConnectivityStatus.UNKNOWN
        self.last_check_time = 0
        self.ping_hosts = [
            "8.8.8.8",          # Google DNS
            "1.1.1.1",          # Cloudflare DNS
            "9.9.9.9",          # Quad9 DNS
        ]
        self.status_listeners = []
        self._stop_event = threading.Event()
        self._monitor_thread = None
    
    def start(self):
        """Start connectivity monitoring"""
        if self._monitor_thread is not None:
            return
            
        self._stop_event.clear()
        self._monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self._monitor_thread.start()
        logger.info("Connectivity monitoring started")
    
    def stop(self):
        """Stop connectivity monitoring"""
        if self._monitor_thread is None:
            return
            
        self._stop_event.set()
        self._monitor_thread.join(timeout=2)
        self._monitor_thread = None
        logger.info("Connectivity monitoring stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while not self._stop_event.is_set():
            current_status = self.check_connectivity()
            
            # If status changed, notify listeners
            if current_status != self.status:
                old_status = self.status
                self.status = current_status
                self._notify_status_change(old_status, current_status)
                
            # Wait for the next check interval
            self._stop_event.wait(self.check_interval)
    
    def check_connectivity(self) -> ConnectivityStatus:
        """Check current connectivity status
        
        Returns:
            ConnectivityStatus: Current connectivity status
        """
        self.last_check_time = time.time()
        
        # Check for internet connectivity
        if self._check_internet():
            return ConnectivityStatus.ONLINE
            
        # Check for local network connectivity
        if self._check_local_network():
            return ConnectivityStatus.LOCAL_ONLY
            
        # No connectivity
        return ConnectivityStatus.ISOLATED
    
    def _check_internet(self) -> bool:
        """Check if we have internet connectivity
        
        Returns:
            bool: True if internet is accessible
        """
        # Try to connect to multiple ping hosts
        for host in self.ping_hosts:
            if self._ping_host(host):
                return True
                
        # Try HTTP request to several known sites
        try:
            # Try to fetch from Cloudflare's simple ping endpoint
            urllib.request.urlopen("https://1.1.1.1/", timeout=2)
            return True
        except:
            pass
            
        try:
            # Try to fetch from Google
            urllib.request.urlopen("https://www.google.com/", timeout=2)
            return True
        except:
            pass
            
        return False
    
    def _check_local_network(self) -> bool:
        """Check if local network is accessible
        
        Returns:
            bool: True if local network is accessible
        """
        # Try to resolve local gateway
        try:
            # Get default gateway
            if sys.platform.startswith('linux'):
                output = subprocess.check_output("ip route | grep default", shell=True).decode('utf-8')
                gateway = output.split()[2]
                return self._ping_host(gateway)
            elif sys.platform.startswith('win'):
                output = subprocess.check_output("ipconfig", shell=True).decode('utf-8')
                for line in output.split('\n'):
                    if "Default Gateway" in line:
                        gateway = line.split(":")[-1].strip()
                        if gateway and gateway != "":
                            return self._ping_host(gateway)
        except:
            pass
            
        # Try to check if we have a valid local IP
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("10.255.255.255", 1))  # Doesn't need to be reachable
            local_ip = s.getsockname()[0]
            s.close()
            
            # If we have a valid IP that's not localhost
            if local_ip and local_ip.startswith(("192.168.", "10.", "172.")):
                return True
        except:
            pass
            
        return False
    
    def _ping_host(self, host: str) -> bool:
        """Ping a host to check connectivity
        
        Args:
            host: Host to ping
            
        Returns:
            bool: True if ping was successful
        """
        try:
            # Create a socket to the host with a timeout
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1)
            s.connect((host, 53))  # DNS port
            s.close()
            return True
        except:
            pass
            
        # Fallback to regular ping
        param = '-n' if sys.platform.startswith('win') else '-c'
        try:
            subprocess.check_output(
                ['ping', param, '1', host],
                stderr=subprocess.STDOUT,
                universal_newlines=True
            )
            return True
        except:
            return False
    
    def register_status_listener(self, callback: Callable[[ConnectivityStatus, ConnectivityStatus], None]):
        """Register a callback for connectivity status changes
        
        Args:
            callback: Function to call when status changes. 
                     Takes (old_status, new_status) as arguments.
        """
        if callback not in self.status_listeners:
            self.status_listeners.append(callback)
    
    def unregister_status_listener(self, callback: Callable):
        """Unregister a status change callback
        
        Args:
            callback: Previously registered callback function
        """
        if callback in self.status_listeners:
            self.status_listeners.remove(callback)
    
    def _notify_status_change(self, old_status: ConnectivityStatus, new_status: ConnectivityStatus):
        """Notify all listeners of a status change
        
        Args:
            old_status: Previous connectivity status
            new_status: New connectivity status
        """
        logger.info(f"Connectivity changed: {old_status.name} -> {new_status.name}")
        
        for callback in self.status_listeners:
            try:
                callback(old_status, new_status)
            except Exception as e:
                logger.error(f"Error in status listener callback: {e}")

# =============================================================================
# COMMAND QUEUE MANAGEMENT
# =============================================================================

class CommandPriority(Enum):
    """Priority levels for commands"""
    HIGH = 3      # Critical commands (security alerts, emergency actions)
    MEDIUM = 2    # Important commands (state changes, configuration updates)
    LOW = 1       # Normal commands (regular updates, non-critical actions)

class CommandStatus(Enum):
    """Status of a command in the queue"""
    PENDING = auto()      # Waiting to be processed
    IN_PROGRESS = auto()  # Currently being processed
    COMPLETED = auto()    # Successfully completed
    FAILED = auto()       # Failed to complete
    EXPIRED = auto()      # Command expired before processing

class Command:
    """Represents a command in the queue"""
    
    def __init__(
        self, 
        command_type: str,
        payload: Dict[str, Any],
        source_node: str,
        target_node: Optional[str] = None,
        priority: CommandPriority = CommandPriority.MEDIUM,
        expires_at: Optional[float] = None,
        requires_ack: bool = False
    ):
        """Initialize a new command
        
        Args:
            command_type: Type of command
            payload: Command data
            source_node: ID of node that created the command
            target_node: Optional target node, None for broadcast
            priority: Command priority
            expires_at: Optional expiration timestamp
            requires_ack: Whether command requires acknowledgement
        """
        self.id = str(uuid.uuid4())
        self.command_type = command_type
        self.payload = payload
        self.source_node = source_node
        self.target_node = target_node
        self.priority = priority
        self.created_at = time.time()
        self.expires_at = expires_at
        self.requires_ack = requires_ack
        self.status = CommandStatus.PENDING
        self.processed_at = None
        self.retries = 0
        self.max_retries = 3 if requires_ack else 0
        self.error = None
    
    def is_expired(self) -> bool:
        """Check if the command has expired
        
        Returns:
            bool: True if command has expired
        """
        if not self.expires_at:
            return False
        
        return time.time() > self.expires_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert command to dictionary for serialization
        
        Returns:
            dict: Command as dictionary
        """
        return {
            "id": self.id,
            "command_type": self.command_type,
            "payload": self.payload,
            "source_node": self.source_node,
            "target_node": self.target_node,
            "priority": self.priority.name,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "requires_ack": self.requires_ack,
            "status": self.status.name,
            "processed_at": self.processed_at,
            "retries": self.retries,
            "max_retries": self.max_retries,
            "error": self.error
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Command':
        """Create command from dictionary
        
        Args:
            data: Dictionary representation of command
            
        Returns:
            Command: Reconstructed command object
        """
        cmd = cls(
            command_type=data["command_type"],
            payload=data["payload"],
            source_node=data["source_node"],
            target_node=data.get("target_node"),
            priority=CommandPriority[data.get("priority", "MEDIUM")],
            expires_at=data.get("expires_at"),
            requires_ack=data.get("requires_ack", False)
        )
        
        # Restore command ID and timestamps
        cmd.id = data["id"]
        cmd.created_at = data["created_at"]
        cmd.status = CommandStatus[data.get("status", "PENDING")]
        cmd.processed_at = data.get("processed_at")
        cmd.retries = data.get("retries", 0)
        cmd.max_retries = data.get("max_retries", 3 if cmd.requires_ack else 0)
        cmd.error = data.get("error")
        
        return cmd

class CommandQueue:
    """Manages a queue of commands for processing"""
    
    def __init__(self, max_size: int = 1000):
        """Initialize command queue
        
        Args:
            max_size: Maximum number of commands to store
        """
        self.queue = []
        self.max_size = max_size
        self.lock = threading.RLock()
    
    def add_command(self, command: Command) -> bool:
        """Add a command to the queue
        
        Args:
            command: Command to add
            
        Returns:
            bool: True if command was added
        """
        with self.lock:
            # Check if queue is full
            if len(self.queue) >= self.max_size:
                # Try to remove expired commands
                self._remove_expired()
                
                # If still full, remove oldest LOW priority command
                if len(self.queue) >= self.max_size:
                    self._remove_oldest_low_priority()
                    
                # If still full, can't add
                if len(self.queue) >= self.max_size:
                    return False
            
            # Add the command
            self.queue.append(command)
            
            # Sort by priority (high to low) then creation time
            self.queue.sort(
                key=lambda cmd: (
                    -cmd.priority.value,  # Negative to sort high to low
                    cmd.created_at
                )
            )
            
            return True
    
    def get_next_command(self) -> Optional[Command]:
        """Get the next command to process
        
        Returns:
            Command: Next command or None if queue is empty
        """
        with self.lock:
            # Remove expired commands
            self._remove_expired()
            
            # Return next command or None
            if not self.queue:
                return None
            
            # Mark as in progress and return
            command = self.queue[0]
            command.status = CommandStatus.IN_PROGRESS
            return command
    
    def mark_completed(self, command_id: str) -> bool:
        """Mark a command as completed
        
        Args:
            command_id: ID of command to mark
            
        Returns:
            bool: True if command was found and marked
        """
        with self.lock:
            for i, cmd in enumerate(self.queue):
                if cmd.id == command_id:
                    cmd.status = CommandStatus.COMPLETED
                    cmd.processed_at = time.time()
                    self.queue.pop(i)
                    return True
            
            return False
    
    def mark_failed(self, command_id: str, error: str = None) -> bool:
        """Mark a command as failed
        
        Args:
            command_id: ID of command to mark
            error: Optional error message
            
        Returns:
            bool: True if command was found and marked
        """
        with self.lock:
            for i, cmd in enumerate(self.queue):
                if cmd.id == command_id:
                    cmd.retries += 1
                    cmd.error = error
                    
                    # If max retries reached, mark as failed and remove
                    if cmd.retries > cmd.max_retries:
                        cmd.status = CommandStatus.FAILED
                        cmd.processed_at = time.time()
                        self.queue.pop(i)
                    else:
                        # Reset status to pending for retry
                        cmd.status = CommandStatus.PENDING
                    
                    return True
            
            return False
    
    def get_all_commands(self) -> List[Command]:
        """Get all commands in the queue
        
        Returns:
            list: All commands
        """
        with self.lock:
            return self.queue.copy()
    
    def get_command_by_id(self, command_id: str) -> Optional[Command]:
        """Get a command by its ID
        
        Args:
            command_id: Command ID to find
            
        Returns:
            Command: Matching command or None if not found
        """
        with self.lock:
            for cmd in self.queue:
                if cmd.id == command_id:
                    return cmd
            
            return None
    
    def _remove_expired(self):
        """Remove expired commands from the queue"""
        # Find expired commands
        expired = []
        for i, cmd in enumerate(self.queue):
            if cmd.is_expired():
                cmd.status = CommandStatus.EXPIRED
                expired.append(i)
        
        # Remove from highest index to lowest
        for i in sorted(expired, reverse=True):
            self.queue.pop(i)
    
    def _remove_oldest_low_priority(self):
        """Remove the oldest LOW priority command"""
        low_priority = []
        for i, cmd in enumerate(self.queue):
            if cmd.priority == CommandPriority.LOW:
                low_priority.append((i, cmd.created_at))
        
        if low_priority:
            # Sort by creation time (oldest first)
            low_priority.sort(key=lambda x: x[1])
            # Remove the oldest
            self.queue.pop(low_priority[0][0])
    
    def clear(self):
        """Clear the command queue"""
        with self.lock:
            self.queue.clear()
    
    def save_to_file(self, filepath: str) -> bool:
        """Save the command queue to a file
        
        Args:
            filepath: Path to save file
            
        Returns:
            bool: True if saved successfully
        """
        try:
            with self.lock:
                # Convert commands to dictionaries
                commands = [cmd.to_dict() for cmd in self.queue]
                
                # Write to file
                with open(filepath, 'w') as f:
                    json.dump(commands, f, indent=2)
                
                return True
        except Exception as e:
            logger.error(f"Error saving command queue: {e}")
            return False
    
    def load_from_file(self, filepath: str) -> bool:
        """Load the command queue from a file
        
        Args:
            filepath: Path to load file
            
        Returns:
            bool: True if loaded successfully
        """
        try:
            if not os.path.exists(filepath):
                return False
                
            with open(filepath, 'r') as f:
                commands = json.load(f)
            
            with self.lock:
                self.queue.clear()
                
                for cmd_data in commands:
                    cmd = Command.from_dict(cmd_data)
                    self.queue.append(cmd)
                
                return True
        except Exception as e:
            logger.error(f"Error loading command queue: {e}")
            return False

# =============================================================================
# USB SNEAKERNET TRANSPORT
# =============================================================================

class USBDetector:
    """Detects USB drives and monitors for GhostDrop files"""
    
    def __init__(
        self, 
        drop_dir_name: str = "ghostdrop", 
        check_interval: int = 5
    ):
        """Initialize USB detector
        
        Args:
            drop_dir_name: Name of directory to look for
            check_interval: Interval in seconds between checks
        """
        self.drop_dir_name = drop_dir_name
        self.check_interval = check_interval
        self.detected_drives = {}  # path -> mount info
        self.detected_drops = {}   # path -> drop info
        self._stop_event = threading.Event()
        self._detector_thread = None
        self.drop_callbacks = []
    
    def start(self):
        """Start USB detection"""
        if self._detector_thread is not None:
            return
            
        self._stop_event.clear()
        self._detector_thread = threading.Thread(target=self._detection_loop, daemon=True)
        self._detector_thread.start()
        logger.info("USB detection started")
    
    def stop(self):
        """Stop USB detection"""
        if self._detector_thread is None:
            return
            
        self._stop_event.set()
        self._detector_thread.join(timeout=2)
        self._detector_thread = None
        logger.info("USB detection stopped")
    
    def _detection_loop(self):
        """Main detection loop"""
        while not self._stop_event.is_set():
            try:
                # Detect USB drives
                new_drives = self.detect_usb_drives()
                
                # Check for changes
                for drive_path, drive_info in new_drives.items():
                    if drive_path not in self.detected_drives:
                        logger.info(f"New USB drive detected: {drive_path}")
                        
                        # Look for drop directory
                        drop_path = os.path.join(drive_path, self.drop_dir_name)
                        if os.path.isdir(drop_path):
                            logger.info(f"GhostDrop directory found: {drop_path}")
                            self._process_drop_directory(drop_path)
                
                # Update detected drives
                self.detected_drives = new_drives
                
                # Wait for next check
                self._stop_event.wait(self.check_interval)
                
            except Exception as e:
                logger.error(f"Error in USB detection loop: {e}")
                self._stop_event.wait(self.check_interval)
    
    def detect_usb_drives(self) -> Dict[str, Dict[str, Any]]:
        """Detect USB drives
        
        Returns:
            dict: Detected drives (path -> info)
        """
        drives = {}
        
        # Linux detection
        if sys.platform.startswith('linux'):
            try:
                # Look in /dev/disk/by-id for USB drives
                if os.path.exists('/dev/disk/by-id'):
                    for device in os.listdir('/dev/disk/by-id'):
                        if 'usb' in device:
                            # Get real device path
                            dev_path = os.path.realpath(f'/dev/disk/by-id/{device}')
                            
                            # Check mounted partitions
                            with open('/proc/mounts', 'r') as f:
                                for line in f:
                                    parts = line.split()
                                    if parts[0].startswith(dev_path) or parts[0] == dev_path:
                                        mount_point = parts[1]
                                        drives[mount_point] = {
                                            'device': parts[0],
                                            'fs_type': parts[2],
                                            'mounted': True
                                        }
                
                # Check /media directory for mounted drives
                media_dirs = ['/media', '/run/media']
                for media_dir in media_dirs:
                    if os.path.exists(media_dir):
                        for user_dir in os.listdir(media_dir):
                            user_path = os.path.join(media_dir, user_dir)
                            if os.path.isdir(user_path):
                                for drive_dir in os.listdir(user_path):
                                    drive_path = os.path.join(user_path, drive_dir)
                                    if drive_path not in drives and os.path.ismount(drive_path):
                                        drives[drive_path] = {
                                            'device': 'unknown',
                                            'fs_type': 'unknown',
                                            'mounted': True
                                        }
            except Exception as e:
                logger.error(f"Error detecting Linux USB drives: {e}")
        
        # Windows detection
        elif sys.platform.startswith('win'):
            try:
                import win32api
                import win32file
                
                drives = win32api.GetLogicalDriveStrings().split('\000')[:-1]
                for drive in drives:
                    if win32file.GetDriveType(drive) == win32file.DRIVE_REMOVABLE:
                        drive_path = drive.rstrip('\\')
                        drives[drive_path] = {
                            'device': drive,
                            'fs_type': 'unknown',
                            'mounted': True
                        }
            except Exception as e:
                logger.error(f"Error detecting Windows USB drives: {e}")
        
        # MacOS detection
        elif sys.platform.startswith('darwin'):
            try:
                # Check /Volumes for mounted drives
                if os.path.exists('/Volumes'):
                    for drive_dir in os.listdir('/Volumes'):
                        drive_path = os.path.join('/Volumes', drive_dir)
                        if drive_path != '/' and os.path.ismount(drive_path):
                            drives[drive_path] = {
                                'device': 'unknown',
                                'fs_type': 'unknown',
                                'mounted': True
                            }
            except Exception as e:
                logger.error(f"Error detecting MacOS USB drives: {e}")
        
        return drives
    
    def _process_drop_directory(self, drop_path: str):
        """Process a GhostDrop directory
        
        Args:
            drop_path: Path to GhostDrop directory
        """
        try:
            # Check for command files
            command_files = []
            for item in os.listdir(drop_path):
                if item.endswith('.ghost') or item.endswith('.ghostcmd'):
                    command_files.append(os.path.join(drop_path, item))
            
            if command_files:
                logger.info(f"Found {len(command_files)} command files in {drop_path}")
                
                # Process each file
                for file_path in command_files:
                    self._process_command_file(file_path)
            
            # Check for export request file
            export_file = os.path.join(drop_path, '.ghost_export_request')
            if os.path.exists(export_file):
                logger.info(f"Found export request in {drop_path}")
                self._handle_export_request(drop_path)
                
        except Exception as e:
            logger.error(f"Error processing drop directory {drop_path}: {e}")
    
    def _process_command_file(self, file_path: str):
        """Process a command file
        
        Args:
            file_path: Path to command file
        """
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            logger.info(f"Processing command file: {file_path}")
            
            # Notify listeners
            for callback in self.drop_callbacks:
                try:
                    callback(data, file_path)
                except Exception as e:
                    logger.error(f"Error in drop callback: {e}")
                    
            # Mark as processed
            processed_path = file_path + '.processed'
            os.rename(file_path, processed_path)
            
        except Exception as e:
            logger.error(f"Error processing command file {file_path}: {e}")
            
            # Mark as failed
            failed_path = file_path + '.failed'
            try:
                os.rename(file_path, failed_path)
            except:
                pass
    
    def _handle_export_request(self, drop_path: str):
        """Handle an export request
        
        Args:
            drop_path: Path to GhostDrop directory
        """
        # Export functionality implemented by higher-level components
        pass
    
    def register_drop_callback(self, callback: Callable[[Dict[str, Any], str], None]):
        """Register a callback for USB drops
        
        Args:
            callback: Function to call when a drop is found.
                     Takes (data, file_path) as arguments.
        """
        if callback not in self.drop_callbacks:
            self.drop_callbacks.append(callback)
    
    def unregister_drop_callback(self, callback: Callable):
        """Unregister a drop callback
        
        Args:
            callback: Previously registered callback function
        """
        if callback in self.drop_callbacks:
            self.drop_callbacks.remove(callback)
    
    def create_drop(self, dest_path: str, data: Dict[str, Any], filename: Optional[str] = None) -> str:
        """Create a GhostDrop on a USB drive
        
        Args:
            dest_path: Path to destination directory
            data: Data to write to drop
            filename: Optional filename (default: auto-generated)
            
        Returns:
            str: Path to created file
        """
        # Ensure drop directory exists
        drop_path = os.path.join(dest_path, self.drop_dir_name)
        os.makedirs(drop_path, exist_ok=True)
        
        # Generate filename if not provided
        if not filename:
            timestamp = int(time.time())
            rand = random.randint(1000, 9999)
            filename = f"ghost_cmd_{timestamp}_{rand}.ghost"
        
        # Write data to file
        file_path = os.path.join(drop_path, filename)
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Created GhostDrop at {file_path}")
        return file_path

# =============================================================================
# FALLBACK DAEMON CORE
# =============================================================================

class GhostFallbackDaemon:
    """Core daemon for internet-independent Ghost operations"""
    
    def __init__(
        self, 
        node_id: str,
        data_dir: str,
        auth_key: str,
        master_ip: Optional[str] = None,
        master_port: int = 7890,
        drop_dir_name: str = "ghostdrop"
    ):
        """Initialize the fallback daemon
        
        Args:
            node_id: Ghost node ID
            data_dir: Path to data directory
            auth_key: Authentication key
            master_ip: IP address of master node (None for master node)
            master_port: Port of master node
            drop_dir_name: Name of drop directory on USB drives
        """
        self.node_id = node_id
        self.auth_key = auth_key
        self.master_ip = master_ip
        self.master_port = master_port
        self.is_master = master_ip is None
        self.is_running = False
        
        # Ensure data directory exists
        self.data_dir = os.path.abspath(data_dir)
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Create component instances
        self.connectivity = GhostConnectivityMonitor()
        self.command_queue = CommandQueue()
        self.usb_detector = USBDetector(drop_dir_name=drop_dir_name)
        
        # Current transport mode
        self.transport_mode = TransportMode.INTERNET
        
        # Command processing
        self._processing_thread = None
        self._stop_event = threading.Event()
        
        # Initialize command handler map
        self.command_handlers = {}
        self._register_default_handlers()
        
        # Track peers
        self.peers = {}
        
        # Command buffer
        self.command_buffer_path = os.path.join(self.data_dir, "command_buffer.json")
        # Load any existing command buffer
        self.command_queue.load_from_file(self.command_buffer_path)
        
        logger.info(f"GhostFallbackDaemon initialized - {'MASTER' if self.is_master else 'PEER'} node")
    
    def _register_default_handlers(self):
        """Register default command handlers"""
        # Basic handlers for common commands
        self.register_command_handler("sync_all", self._handle_sync_all)
        self.register_command_handler("authority", self._handle_authority)
        self.register_command_handler("page_change", self._handle_page_change)
        self.register_command_handler("tool_activate", self._handle_tool_activate)
        self.register_command_handler("heartbeat", self._handle_heartbeat)
        
        # Fallback-specific commands
        self.register_command_handler("fallback_test", self._handle_fallback_test)
        self.register_command_handler("fallback_ping", self._handle_fallback_ping)
        self.register_command_handler("fallback_status", self._handle_fallback_status)
        self.register_command_handler("fallback_echo", self._handle_fallback_echo)
        
        # Special handlers
        self.register_command_handler("fallback_mode", self._handle_fallback_mode)
    
    def start(self):
        """Start the fallback daemon"""
        if self.is_running:
            return
        
        # Register callbacks
        self.connectivity.register_status_listener(self._handle_connectivity_change)
        self.usb_detector.register_drop_callback(self._handle_usb_drop)
        
        # Start components
        self.connectivity.start()
        self.usb_detector.start()
        
        # Start command processing thread
        self._stop_event.clear()
        self._processing_thread = threading.Thread(target=self._process_commands, daemon=True)
        self._processing_thread.start()
        
        # Mark as running
        self.is_running = True
        logger.info("GhostFallbackDaemon started")
        
        # Send initial heartbeat to establish presence
        self._send_heartbeat()
    
    def stop(self):
        """Stop the fallback daemon"""
        if not self.is_running:
            return
        
        # Stop command processing
        self._stop_event.set()
        if self._processing_thread:
            self._processing_thread.join(timeout=2)
        
        # Stop components
        self.connectivity.stop()
        self.usb_detector.stop()
        
        # Save command buffer
        self.command_queue.save_to_file(self.command_buffer_path)
        
        # Mark as stopped
        self.is_running = False
        logger.info("GhostFallbackDaemon stopped")
    
    def _handle_connectivity_change(self, old_status: ConnectivityStatus, new_status: ConnectivityStatus):
        """Handle connectivity status changes
        
        Args:
            old_status: Previous connectivity status
            new_status: New connectivity status
        """
        logger.info(f"Connectivity changed: {old_status.name} -> {new_status.name}")
        
        # Decide on transport mode based on connectivity
        old_mode = self.transport_mode
        
        if new_status == ConnectivityStatus.ONLINE:
            self.transport_mode = TransportMode.INTERNET
        elif new_status == ConnectivityStatus.LOCAL_ONLY:
            self.transport_mode = TransportMode.MESH_ONLY
        elif new_status == ConnectivityStatus.ISOLATED:
            self.transport_mode = TransportMode.USB
        
        # If mode changed, notify
        if old_mode != self.transport_mode:
            logger.info(f"Transport mode changed: {old_mode.value} -> {self.transport_mode.value}")
            
            # If we're back online, process the command queue
            if self.transport_mode == TransportMode.INTERNET and old_mode != TransportMode.INTERNET:
                logger.info("Back online, processing command queue")
                self._process_offline_commands()
    
    def _process_offline_commands(self):
        """Process commands that were queued while offline"""
        # This is called when coming back online
        # The commands will be processed by the normal command processing thread
        pass
    
    def _handle_usb_drop(self, data: Dict[str, Any], file_path: str):
        """Handle a USB drop
        
        Args:
            data: Command data
            file_path: Path to command file
        """
        logger.info(f"Processing USB drop: {file_path}")
        
        try:
            # Parse commands from the file
            if "commands" in data:
                for cmd_data in data["commands"]:
                    # Convert to Command object
                    command = Command(
                        command_type=cmd_data["command_type"],
                        payload=cmd_data["payload"],
                        source_node=cmd_data["source_node"],
                        target_node=cmd_data.get("target_node"),
                        priority=CommandPriority[cmd_data.get("priority", "MEDIUM")],
                        expires_at=cmd_data.get("expires_at"),
                        requires_ack=cmd_data.get("requires_ack", False)
                    )
                    
                    # Add to queue
                    self.command_queue.add_command(command)
                    logger.info(f"Added command {command.id} from USB drop")
            
            # Process node information
            if "nodes" in data:
                for node_id, node_info in data["nodes"].items():
                    if node_id not in self.peers:
                        self.peers[node_id] = node_info
                        logger.info(f"Added peer {node_id} from USB drop")
            
            # Create response file
            self._create_usb_response(file_path)
            
        except Exception as e:
            logger.error(f"Error processing USB drop: {e}")
    
    def _create_usb_response(self, request_path: str):
        """Create a response file for a USB drop
        
        Args:
            request_path: Path to the request file
        """
        try:
            # Get drop directory
            drop_dir = os.path.dirname(request_path)
            
            # Create response data
            response_data = {
                "node_id": self.node_id,
                "timestamp": time.time(),
                "status": "processed",
                "transport_mode": self.transport_mode.value,
                "connectivity": self.connectivity.status.name,
                "commands": []
            }
            
            # Add command queue entries
            commands = self.command_queue.get_all_commands()
            for cmd in commands:
                response_data["commands"].append(cmd.to_dict())
            
            # Generate response filename
            base_name = os.path.basename(request_path)
            response_name = f"response_{base_name}"
            response_path = os.path.join(drop_dir, response_name)
            
            # Write response
            with open(response_path, 'w') as f:
                json.dump(response_data, f, indent=2)
                
            logger.info(f"Created USB response at {response_path}")
            
        except Exception as e:
            logger.error(f"Error creating USB response: {e}")
    
    def _send_heartbeat(self):
        """Send a heartbeat to establish presence"""
        # Create a heartbeat command
        heartbeat = Command(
            command_type="heartbeat",
            payload={
                "node_id": self.node_id,
                "timestamp": time.time(),
                "transport_mode": self.transport_mode.value,
                "connectivity": self.connectivity.status.name
            },
            source_node=self.node_id,
            priority=CommandPriority.LOW
        )
        
        # Add to queue
        self.command_queue.add_command(heartbeat)
    
    def _process_commands(self):
        """Process commands from the queue"""
        while not self._stop_event.is_set():
            try:
                # Get next command
                command = self.command_queue.get_next_command()
                if command:
                    self._execute_command(command)
                
                # Pause before next command
                self._stop_event.wait(0.1)
                
            except Exception as e:
                logger.error(f"Error processing commands: {e}")
                self._stop_event.wait(1)
    
    def _execute_command(self, command: Command):
        """Execute a command
        
        Args:
            command: Command to execute
        """
        logger.info(f"Executing command {command.id} ({command.command_type})")
        
        try:
            # If command is not for this node, forward it
            if command.target_node and command.target_node != self.node_id:
                self._forward_command(command)
                self.command_queue.mark_completed(command.id)
                return
                
            # Find handler for command type
            handler = self.command_handlers.get(command.command_type)
            if not handler:
                logger.warning(f"No handler for command type: {command.command_type}")
                self.command_queue.mark_failed(command.id, "No handler found")
                return
                
            # Execute handler
            result = handler(command.payload, command.source_node)
            
            # Mark as completed
            self.command_queue.mark_completed(command.id)
            
            # If command requires acknowledgement, send it
            if command.requires_ack:
                self._send_acknowledgement(command, result)
                
        except Exception as e:
            logger.error(f"Error executing command {command.id}: {e}")
            self.command_queue.mark_failed(command.id, str(e))
    
    def _forward_command(self, command: Command):
        """Forward a command to its target
        
        Args:
            command: Command to forward
        """
        # The actual forwarding depends on the transport mode
        if self.transport_mode == TransportMode.INTERNET:
            self._forward_via_internet(command)
        elif self.transport_mode == TransportMode.MESH_ONLY:
            self._forward_via_mesh(command)
        elif self.transport_mode == TransportMode.USB:
            # Queue for USB
            pass
        else:
            logger.warning(f"Cannot forward command in mode: {self.transport_mode.value}")
    
    def _forward_via_internet(self, command: Command):
        """Forward command via internet
        
        Args:
            command: Command to forward
        """
        # Determine destination based on target_node
        # For now, just use master node if we're a peer
        if not self.is_master and self.master_ip:
            try:
                # Create request data
                request_data = {
                    "command_id": command.id,
                    "command_type": command.command_type,
                    "payload": command.payload,
                    "source_node": command.source_node,
                    "target_node": command.target_node
                }
                
                # Send request
                request = urllib.request.Request(
                    f"http://{self.master_ip}:{self.master_port}/forward",
                    data=json.dumps(request_data).encode(),
                    headers={'Content-Type': 'application/json'}
                )
                
                with urllib.request.urlopen(request) as response:
                    result = json.loads(response.read().decode())
                    
                    if result.get("status") == "forwarded":
                        logger.info(f"Command {command.id} forwarded to {command.target_node}")
                        return
            except Exception as e:
                logger.error(f"Error forwarding command via internet: {e}")
                
        logger.warning(f"Could not forward command {command.id} via internet")
    
    def _forward_via_mesh(self, command: Command):
        """Forward command via mesh network
        
        Args:
            command: Command to forward
        """
        # This would use the mesh network to forward
        # For now, just log
        logger.info(f"Would forward command {command.id} via mesh to {command.target_node}")
    
    def _send_acknowledgement(self, command: Command, result: Any):
        """Send acknowledgement for a command
        
        Args:
            command: Executed command
            result: Result of execution
        """
        # Create acknowledgement command
        ack = Command(
            command_type="command_ack",
            payload={
                "ack_for": command.id,
                "result": result,
                "timestamp": time.time()
            },
            source_node=self.node_id,
            target_node=command.source_node,
            priority=CommandPriority.HIGH
        )
        
        # Add to queue
        self.command_queue.add_command(ack)
    
    def register_command_handler(self, command_type: str, handler: Callable[[Dict[str, Any], str], Any]):
        """Register a handler for a command type
        
        Args:
            command_type: Type of command to handle
            handler: Function to call for this command type.
                     Takes (payload, source_node) as arguments.
        """
        self.command_handlers[command_type] = handler
    
    def unregister_command_handler(self, command_type: str):
        """Unregister a command handler
        
        Args:
            command_type: Type of command to unregister
        """
        if command_type in self.command_handlers:
            del self.command_handlers[command_type]
    
    def queue_command(
        self,
        command_type: str,
        payload: Dict[str, Any],
        target_node: Optional[str] = None,
        priority: CommandPriority = CommandPriority.MEDIUM,
        requires_ack: bool = False
    ) -> str:
        """Queue a command for execution
        
        Args:
            command_type: Type of command
            payload: Command data
            target_node: Optional target node, None for broadcast
            priority: Command priority
            requires_ack: Whether command requires acknowledgement
            
        Returns:
            str: Command ID
        """
        # Create command
        command = Command(
            command_type=command_type,
            payload=payload,
            source_node=self.node_id,
            target_node=target_node,
            priority=priority,
            requires_ack=requires_ack
        )
        
        # Add to queue
        self.command_queue.add_command(command)
        
        return command.id
    
    def get_status(self) -> Dict[str, Any]:
        """Get daemon status
        
        Returns:
            dict: Status information
        """
        return {
            "node_id": self.node_id,
            "is_master": self.is_master,
            "is_running": self.is_running,
            "connectivity": self.connectivity.status.name,
            "transport_mode": self.transport_mode.value,
            "peer_count": len(self.peers),
            "command_queue_size": len(self.command_queue.get_all_commands())
        }
    
    # Default command handlers
    
    def _handle_sync_all(self, payload: Dict[str, Any], source_node: str) -> Dict[str, Any]:
        """Handle sync_all command
        
        Args:
            payload: Command data
            source_node: Source node ID
            
        Returns:
            dict: Result data
        """
        logger.info(f"Sync triggered by {source_node}")
        # This would normally trigger a sync - just return success
        return {"status": "synced", "timestamp": time.time()}
    
    def _handle_authority(self, payload: Dict[str, Any], source_node: str) -> Dict[str, Any]:
        """Handle authority command
        
        Args:
            payload: Command data
            source_node: Source node ID
            
        Returns:
            dict: Result data
        """
        device_id = payload.get("device_id", "unknown")
        has_authority = payload.get("has_authority", False)
        
        if has_authority:
            logger.info(f"Authority granted to {device_id}")
        else:
            logger.info(f"Authority revoked from {device_id}")
            
        return {
            "status": "authority_updated",
            "device_id": device_id,
            "has_authority": has_authority
        }
    
    def _handle_page_change(self, payload: Dict[str, Any], source_node: str) -> Dict[str, Any]:
        """Handle page_change command
        
        Args:
            payload: Command data
            source_node: Source node ID
            
        Returns:
            dict: Result data
        """
        page = payload.get("page", 1)
        logger.info(f"Page changed to {page} by {source_node}")
        
        return {"status": "page_changed", "page": page}
    
    def _handle_tool_activate(self, payload: Dict[str, Any], source_node: str) -> Dict[str, Any]:
        """Handle tool_activate command
        
        Args:
            payload: Command data
            source_node: Source node ID
            
        Returns:
            dict: Result data
        """
        tool = payload.get("tool", "unknown")
        logger.info(f"Tool {tool} activated by {source_node}")
        
        return {"status": "tool_activated", "tool": tool}
    
    def _handle_heartbeat(self, payload: Dict[str, Any], source_node: str) -> Dict[str, Any]:
        """Handle heartbeat command
        
        Args:
            payload: Command data
            source_node: Source node ID
            
        Returns:
            dict: Result data
        """
        # Update peer info
        if source_node not in self.peers:
            self.peers[source_node] = {
                "last_seen": time.time(),
                "transport_mode": payload.get("transport_mode", "unknown"),
                "connectivity": payload.get("connectivity", "unknown")
            }
        else:
            self.peers[source_node]["last_seen"] = time.time()
            self.peers[source_node]["transport_mode"] = payload.get("transport_mode", self.peers[source_node].get("transport_mode", "unknown"))
            self.peers[source_node]["connectivity"] = payload.get("connectivity", self.peers[source_node].get("connectivity", "unknown"))
            
        logger.info(f"Heartbeat from {source_node}")
        
        return {
            "status": "received",
            "timestamp": time.time(),
            "node_id": self.node_id
        }
    
    # Fallback-specific command handlers
    
    def _handle_fallback_test(self, payload: Dict[str, Any], source_node: str) -> Dict[str, Any]:
        """Handle fallback_test command
        
        Args:
            payload: Command data
            source_node: Source node ID
            
        Returns:
            dict: Result data
        """
        test_id = payload.get("test_id", "unknown")
        test_data = payload.get("test_data", {})
        
        logger.info(f"Fallback test {test_id} from {source_node}")
        
        return {
            "status": "test_complete",
            "test_id": test_id,
            "result": "success",
            "node_id": self.node_id,
            "timestamp": time.time()
        }
    
    def _handle_fallback_ping(self, payload: Dict[str, Any], source_node: str) -> Dict[str, Any]:
        """Handle fallback_ping command
        
        Args:
            payload: Command data
            source_node: Source node ID
            
        Returns:
            dict: Result data
        """
        ping_id = payload.get("ping_id", str(uuid.uuid4()))
        timestamp = payload.get("timestamp", time.time())
        
        logger.info(f"Ping from {source_node} ({ping_id})")
        
        return {
            "status": "pong",
            "ping_id": ping_id,
            "round_trip_time": time.time() - timestamp,
            "node_id": self.node_id,
            "transport_mode": self.transport_mode.value
        }
    
    def _handle_fallback_status(self, payload: Dict[str, Any], source_node: str) -> Dict[str, Any]:
        """Handle fallback_status command
        
        Args:
            payload: Command data
            source_node: Source node ID
            
        Returns:
            dict: Result data
        """
        logger.info(f"Status request from {source_node}")
        
        return {
            "status": "online",
            "node_id": self.node_id,
            "is_master": self.is_master,
            "connectivity": self.connectivity.status.name,
            "transport_mode": self.transport_mode.value,
            "peer_count": len(self.peers),
            "command_queue_size": len(self.command_queue.get_all_commands()),
            "timestamp": time.time()
        }
    
    def _handle_fallback_echo(self, payload: Dict[str, Any], source_node: str) -> Dict[str, Any]:
        """Handle fallback_echo command
        
        Args:
            payload: Command data
            source_node: Source node ID
            
        Returns:
            dict: Result data
        """
        message = payload.get("message", "")
        logger.info(f"Echo from {source_node}: {message}")
        
        return {
            "status": "echo_reply",
            "original_message": message,
            "node_id": self.node_id,
            "timestamp": time.time()
        }
    
    def _handle_fallback_mode(self, payload: Dict[str, Any], source_node: str) -> Dict[str, Any]:
        """Handle fallback_mode command (force mode change)
        
        Args:
            payload: Command data
            source_node: Source node ID
            
        Returns:
            dict: Result data
        """
        mode = payload.get("mode", "")
        
        if not mode or mode not in [m.value for m in TransportMode]:
            return {
                "status": "error",
                "message": f"Invalid mode: {mode}",
                "valid_modes": [m.value for m in TransportMode]
            }
            
        # Set the mode
        old_mode = self.transport_mode
        self.transport_mode = TransportMode(mode)
        
        logger.info(f"Transport mode forcibly changed: {old_mode.value} -> {self.transport_mode.value} by {source_node}")
        
        return {
            "status": "mode_changed",
            "old_mode": old_mode.value,
            "new_mode": self.transport_mode.value,
            "node_id": self.node_id,
            "timestamp": time.time()
        }

# =============================================================================
# MAIN ENTRYPOINT
# =============================================================================

def main():
    """Main entry point for the daemon"""
    import argparse
    
    parser = argparse.ArgumentParser(description="GhostFallbackDaemon - Internet-Independent Ghost Operations")
    parser.add_argument("--node-id", help="Ghost node ID (default: auto-generated)")
    parser.add_argument("--data-dir", default="./ghost_data", help="Path to data directory")
    parser.add_argument("--auth-key", default="ghostops", help="Authentication key")
    parser.add_argument("--master-ip", help="Master node IP (omit for master node)")
    parser.add_argument("--master-port", type=int, default=7890, help="Master node port")
    parser.add_argument("--drop-dir", default="ghostdrop", help="Name of drop directory on USB drives")
    
    args = parser.parse_args()
    
    # Generate node ID if not provided
    node_id = args.node_id
    if not node_id:
        # Generate based on hostname and node type
        prefix = "master" if not args.master_ip else "peer"
        hostname = socket.gethostname()
        node_id = f"{prefix}_{hostname}"
    
    # Create and start daemon
    daemon = GhostFallbackDaemon(
        node_id=node_id,
        data_dir=args.data_dir,
        auth_key=args.auth_key,
        master_ip=args.master_ip,
        master_port=args.master_port,
        drop_dir_name=args.drop_dir
    )
    
    # Handle signals
    def signal_handler(sig, frame):
        print("\nShutting down...")
        daemon.stop()
        sys.exit(0)
        
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start daemon
    daemon.start()
    
    # Keep running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        daemon.stop()

if __name__ == "__main__":
    main()
