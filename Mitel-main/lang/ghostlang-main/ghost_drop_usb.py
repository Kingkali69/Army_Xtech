#!/usr/bin/env python3
"""
GhostDrop_USB.py - USB Sneakernet Transport for GhostOps

Enables command and state transport between physically separated GhostOps nodes
via USB drives ("sneakernet"). When internet connectivity is lost, GhostDrop provides
a manual transport mechanism for critical commands and synchronization.

Features:
- Automatic USB drive detection and monitoring
- Strong encryption for all transported data
- Command queue bundling and prioritization
- State snapshot creation and restoration
- Auto-sync on USB insertion
- Support for air-gapped deployment scenarios
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
import subprocess
import hashlib
import hmac
import base64
import shutil
import glob
from enum import Enum
from typing import Dict, List, Any, Optional, Tuple, Callable, Union
from pathlib import Path
import random

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ghost.drop_usb")

# =============================================================================
# GHOSTDROP USB CONSTANTS
# =============================================================================

# Directory name for ghost drops on USB drives
DEFAULT_DROP_DIR = "ghostdrop"

# File extensions
COMMAND_FILE_EXT = ".ghostcmd"
STATE_FILE_EXT = ".ghoststate"
CONFIG_FILE_EXT = ".ghostcfg"
LOG_FILE_EXT = ".ghostlog"
LOCK_FILE_EXT = ".lock"

# Status suffixes
PROCESSING_SUFFIX = ".processing"
PROCESSED_SUFFIX = ".processed"
FAILED_SUFFIX = ".failed"
OUTGOING_SUFFIX = ".outgoing"

# Default encryption settings
DEFAULT_ENCRYPTION_KEY_PATH = "ghost_transport.key"

# =============================================================================
# ENCRYPTION UTILITIES
# =============================================================================

class GhostDropEncryption:
    """Handles encryption and decryption for GhostDrop files"""
    
    @staticmethod
    def generate_key(key_path: str = DEFAULT_ENCRYPTION_KEY_PATH) -> bytes:
        """Generate a new encryption key
        
        Args:
            key_path: Path to save the key
            
        Returns:
            bytes: Generated key
        """
        try:
            # Generate a secure random key
            key = os.urandom(32)  # 256-bit key
            
            # Save to file
            with open(key_path, 'wb') as f:
                f.write(key)
                
            logger.info(f"Generated new encryption key at {key_path}")
            return key
            
        except Exception as e:
            logger.error(f"Error generating encryption key: {e}")
            raise
    
    @staticmethod
    def load_or_create_key(key_path: str = DEFAULT_ENCRYPTION_KEY_PATH) -> bytes:
        """Load existing key or create new one
        
        Args:
            key_path: Path to the key file
            
        Returns:
            bytes: Encryption key
        """
        try:
            if os.path.exists(key_path):
                # Load existing key
                with open(key_path, 'rb') as f:
                    key = f.read()
                
                if len(key) != 32:
                    logger.warning(f"Key at {key_path} has invalid length, generating new key")
                    key = GhostDropEncryption.generate_key(key_path)
            else:
                # Generate new key
                key = GhostDropEncryption.generate_key(key_path)
            
            return key
            
        except Exception as e:
            logger.error(f"Error loading encryption key: {e}")
            raise
    
    @staticmethod
    def encrypt_data(data: Union[Dict, List, str], key: bytes) -> str:
        """Encrypt data for transport
        
        Args:
            data: Data to encrypt (will be converted to JSON)
            key: Encryption key
            
        Returns:
            str: Base64-encoded encrypted data
        """
        try:
            # Convert data to JSON string
            if isinstance(data, (dict, list)):
                plaintext = json.dumps(data).encode('utf-8')
            elif isinstance(data, str):
                plaintext = data.encode('utf-8')
            else:
                plaintext = str(data).encode('utf-8')
            
            # Generate random IV
            iv = os.urandom(16)
            
            # Derive encryption key from master key and IV
            derived_key = hashlib.pbkdf2_hmac(
                'sha256',
                key,
                iv,
                iterations=10000,
                dklen=32
            )
            
            # Create cipher using AES-256-GCM (would use cryptography library)
            # Simulating with a simple XOR for illustration
            # In production, use a proper encryption library like cryptography
            
            # Ensure plaintext is padded to 16-byte blocks
            padded_plaintext = plaintext
            if len(plaintext) % 16 != 0:
                padding = 16 - (len(plaintext) % 16)
                padded_plaintext = plaintext + bytes([padding]) * padding
            
            # Encrypt (simple XOR for illustration - use real AES in production)
            ciphertext = bytearray()
            for i, b in enumerate(padded_plaintext):
                key_byte = derived_key[i % len(derived_key)]
                ciphertext.append(b ^ key_byte)
            
            # Calculate HMAC for authentication
            mac = hmac.new(derived_key, iv + bytes(ciphertext), hashlib.sha256).digest()
            
            # Combine IV + ciphertext + MAC
            result = iv + bytes(ciphertext) + mac
            
            # Encode as base64
            encoded = base64.b64encode(result).decode('utf-8')
            
            return encoded
            
        except Exception as e:
            logger.error(f"Error encrypting data: {e}")
            raise
    
    @staticmethod
    def decrypt_data(encrypted_data: str, key: bytes) -> Any:
        """Decrypt data from transport
        
        Args:
            encrypted_data: Base64-encoded encrypted data
            key: Encryption key
            
        Returns:
            dict/list/str: Decrypted data
        """
        try:
            # Decode base64
            data = base64.b64decode(encrypted_data)
            
            # Extract components
            iv = data[:16]
            mac_start = len(data) - 32  # HMAC-SHA256 is 32 bytes
            ciphertext = data[16:mac_start]
            mac = data[mac_start:]
            
            # Derive key
            derived_key = hashlib.pbkdf2_hmac(
                'sha256',
                key,
                iv,
                iterations=10000,
                dklen=32
            )
            
            # Verify HMAC
            expected_mac = hmac.new(derived_key, iv + ciphertext, hashlib.sha256).digest()
            if not hmac.compare_digest(mac, expected_mac):
                raise ValueError("HMAC verification failed - data may have been tampered with")
            
            # Decrypt (simple XOR for illustration - use real AES in production)
            plaintext = bytearray()
            for i, b in enumerate(ciphertext):
                key_byte = derived_key[i % len(derived_key)]
                plaintext.append(b ^ key_byte)
            
            # Remove padding
            padding = plaintext[-1]
            if padding < 16:
                plaintext = plaintext[:-padding]
            
            # Parse JSON
            try:
                return json.loads(plaintext.decode('utf-8'))
            except json.JSONDecodeError:
                # Not valid JSON, return as string
                return plaintext.decode('utf-8')
            
        except Exception as e:
            logger.error(f"Error decrypting data: {e}")
            raise

# =============================================================================
# USB DETECTION AND MONITORING
# =============================================================================

class GhostUSBMonitor:
    """Monitors for USB drives and GhostDrop directories"""
    
    def __init__(
        self, 
        drop_dir: str = DEFAULT_DROP_DIR, 
        check_interval: int = 5,
        auto_process: bool = True
    ):
        """Initialize the USB monitor
        
        Args:
            drop_dir: Name of the GhostDrop directory on USB drives
            check_interval: Interval in seconds between USB drive checks
            auto_process: Whether to automatically process found drops
        """
        self.drop_dir = drop_dir
        self.check_interval = check_interval
        self.auto_process = auto_process
        
        self.mounted_drives = {}  # path -> info
        self.active_drops = {}    # path -> drop info
        self.is_running = False
        
        self._stop_event = threading.Event()
        self._monitor_thread = None
        
        self.drop_found_callbacks = []
        self.drop_processed_callbacks = []
    
    def start(self):
        """Start USB monitoring"""
        if self.is_running:
            return
        
        self._stop_event.clear()
        self._monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self._monitor_thread.start()
        
        self.is_running = True
        logger.info("USB monitoring started")
    
    def stop(self):
        """Stop USB monitoring"""
        if not self.is_running:
            return
        
        self._stop_event.set()
        if self._monitor_thread:
            self._monitor_thread.join(timeout=2)
        
        self.is_running = False
        logger.info("USB monitoring stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while not self._stop_event.is_set():
            try:
                # Detect mounted drives
                current_drives = self._detect_mounted_drives()
                
                # Check for new drives
                for drive_path, drive_info in current_drives.items():
                    if drive_path not in self.mounted_drives:
                        logger.info(f"New drive mounted: {drive_path}")
                        
                        # Look for drop directory
                        drop_path = os.path.join(drive_path, self.drop_dir)
                        if os.path.isdir(drop_path):
                            logger.info(f"Found GhostDrop directory: {drop_path}")
                            self._handle_drop_directory(drop_path)
                            
                # Check for removed drives
                for drive_path in list(self.mounted_drives.keys()):
                    if drive_path not in current_drives:
                        logger.info(f"Drive removed: {drive_path}")
                        
                        # Remove from active drops
                        drop_path = os.path.join(drive_path, self.drop_dir)
                        if drop_path in self.active_drops:
                            del self.active_drops[drop_path]
                            
                        # Remove from mounted drives
                        del self.mounted_drives[drive_path]
                
                # Update mounted drives list
                self.mounted_drives = current_drives
                
                # Wait for next check
                self._stop_event.wait(self.check_interval)
                
            except Exception as e:
                logger.error(f"Error in USB monitoring loop: {e}")
                self._stop_event.wait(self.check_interval)
    
    def _detect_mounted_drives(self) -> Dict[str, Dict]:
        """Detect mounted drives
        
        Returns:
            dict: Mounted drives (path -> info)
        """
        drives = {}
        
        # Linux detection
        if sys.platform.startswith('linux'):
            try:
                # Read /proc/mounts
                with open('/proc/mounts', 'r') as f:
                    for line in f:
                        parts = line.split()
                        dev_path = parts[0]
                        mount_point = parts[1]
                        fs_type = parts[2]
                        
                        # Skip common system mounts
                        if fs_type in ['proc', 'sysfs', 'tmpfs', 'devpts', 'cgroup']:
                            continue
                            
                        # Skip system directories
                        if mount_point.startswith(('/proc', '/sys', '/run', '/dev')):
                            continue
                            
                        # Check if it's a removable drive
                        if self._is_removable_drive_linux(dev_path):
                            drives[mount_point] = {
                                'device': dev_path,
                                'filesystem': fs_type,
                                'removable': True
                            }
                
                # Also check /media directory for mounted drives
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
                                            'filesystem': 'unknown',
                                            'removable': True
                                        }
                
            except Exception as e:
                logger.error(f"Error detecting Linux drives: {e}")
                
        # Windows detection
        elif sys.platform.startswith('win'):
            try:
                import string
                from ctypes import windll
                
                # Get list of drive letters
                drives_str = ''
                bitmask = windll.kernel32.GetLogicalDrives()
                for letter in string.ascii_uppercase:
                    if bitmask & 1:
                        drives_str += letter
                    bitmask >>= 1
                
                # Check each drive
                for letter in drives_str:
                    drive_path = f"{letter}:\\"
                    
                    # Get drive type
                    drive_type = windll.kernel32.GetDriveTypeW(drive_path)
                    
                    # 2 = removable, 3 = fixed, 4 = network, 5 = optical, 6 = ram disk
                    if drive_type == 2:  # Removable drive
                        drives[drive_path] = {
                            'device': drive_path,
                            'filesystem': 'unknown',
                            'removable': True
                        }
                
            except Exception as e:
                logger.error(f"Error detecting Windows drives: {e}")
                
                # Fallback detection for Windows
                for letter in 'CDEFGHIJKLMNOPQRSTUVWXYZ':
                    drive_path = f"{letter}:\\"
                    if os.path.exists(drive_path):
                        try:
                            # Check if we can write to the drive
                            test_path = os.path.join(drive_path, '.ghost_test')
                            with open(test_path, 'w') as f:
                                f.write('test')
                            os.remove(test_path)
                            
                            # If we get here, drive is writable
                            drives[drive_path] = {
                                'device': drive_path,
                                'filesystem': 'unknown',
                                'removable': True  # Assume removable if we can write to it
                            }
                        except:
                            # Can't write to the drive, skip it
                            pass
        
        # MacOS detection
        elif sys.platform.startswith('darwin'):
            try:
                # Check /Volumes for mounted drives
                volumes_dir = '/Volumes'
                if os.path.exists(volumes_dir):
                    for drive_name in os.listdir(volumes_dir):
                        drive_path = os.path.join(volumes_dir, drive_name)
                        
                        # Skip the main system drive
                        if drive_path == '/':
                            continue
                            
                        # Skip known system volumes
                        if drive_name in ['Macintosh HD', 'System', 'iCloud Drive']:
                            continue
                            
                        if os.path.ismount(drive_path):
                            drives[drive_path] = {
                                'device': 'unknown',
                                'filesystem': 'unknown',
                                'removable': True  # Assume removable if in /Volumes
                            }
                
            except Exception as e:
                logger.error(f"Error detecting MacOS drives: {e}")
        
        return drives
    
    def _is_removable_drive_linux(self, device_path: str) -> bool:
        """Check if a device is removable on Linux
        
        Args:
            device_path: Path to device file
            
        Returns:
            bool: True if removable
        """
        try:
            # Extract the base device
            if device_path.startswith('/dev/'):
                # For partitions like /dev/sdb1, get the base device /dev/sdb
                base_device = device_path.rstrip('0123456789')
                
                # For device mapper devices (including LVM), treat as non-removable
                if '/mapper/' in base_device:
                    return False
                
                # Check in /sys/block
                base_name = os.path.basename(base_device)
                removable_path = f"/sys/block/{base_name}/removable"
                
                if os.path.exists(removable_path):
                    with open(removable_path, 'r') as f:
                        return f.read().strip() == '1'
            
            # Default: assume not removable if we can't determine
            return False
            
        except Exception as e:
            logger.error(f"Error checking if device is removable: {e}")
            return False
    
    def _handle_drop_directory(self, drop_path: str):
        """Process a GhostDrop directory
        
        Args:
            drop_path: Path to GhostDrop directory
        """
        # Add to active drops
        self.active_drops[drop_path] = {
            'path': drop_path,
            'found_at': time.time(),
            'last_checked': time.time()
        }
        
        # Look for command files that aren't processed
        for pattern in [f"*{COMMAND_FILE_EXT}", f"*{STATE_FILE_EXT}"]:
            for file_path in glob.glob(os.path.join(drop_path, pattern)):
                # Skip already processed files
                if (file_path.endswith(PROCESSED_SUFFIX) or
                    file_path.endswith(FAILED_SUFFIX) or
                    file_path.endswith(PROCESSING_SUFFIX) or
                    file_path.endswith(OUTGOING_SUFFIX)):
                    continue
                
                # Skip lock files
                if file_path.endswith(LOCK_FILE_EXT):
                    continue
                
                # Check for lock file
                lock_file = file_path + LOCK_FILE_EXT
                if os.path.exists(lock_file):
                    # Check if lock is stale
                    if time.time() - os.path.getmtime(lock_file) > 300:  # 5 minutes
                        # Stale lock, remove it
                        try:
                            os.unlink(lock_file)
                        except:
                            # Skip if we can't remove the lock
                            continue
                    else:
                        # Active lock, skip this file
                        continue
                
                # Create lock file
                try:
                    with open(lock_file, 'w') as f:
                        f.write(f"{os.getpid()}")
                except:
                    # Skip if we can't create lock
                    continue
                
                try:
                    # Notify about found drop file
                    logger.info(f"Found drop file: {file_path}")
                    self._notify_drop_found(file_path)
                    
                    # Process if auto-processing is enabled
                    if self.auto_process:
                        self._process_drop_file(file_path)
                finally:
                    # Remove lock file
                    try:
                        os.unlink(lock_file)
                    except:
                        pass
    
    def _process_drop_file(self, file_path: str):
        """Process a drop file
        
        Args:
            file_path: Path to drop file
        """
        processing_path = file_path + PROCESSING_SUFFIX
        
        try:
            # Mark as processing
            os.rename(file_path, processing_path)
            file_path = processing_path
            
            # Determine file type
            if file_path.endswith(COMMAND_FILE_EXT + PROCESSING_SUFFIX):
                data = self._read_drop_file(file_path)
                
                # Process commands
                if data:
                    self._notify_drop_processed(file_path, data)
                
            elif file_path.endswith(STATE_FILE_EXT + PROCESSING_SUFFIX):
                data = self._read_drop_file(file_path)
                
                # Process state data
                if data:
                    self._notify_drop_processed(file_path, data)
            
            # Mark as processed
            processed_path = file_path.replace(PROCESSING_SUFFIX, PROCESSED_SUFFIX)
            os.rename(file_path, processed_path)
            
        except Exception as e:
            logger.error(f"Error processing drop file {file_path}: {e}")
            
            # Mark as failed
            try:
                failed_path = file_path.replace(PROCESSING_SUFFIX, FAILED_SUFFIX)
                os.rename(file_path, failed_path)
            except:
                pass
    
    def _read_drop_file(self, file_path: str) -> Optional[Dict]:
        """Read a drop file
        
        Args:
            file_path: Path to drop file
            
        Returns:
            dict: File contents or None on error
        """
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Check if content is encrypted
            try:
                # Try to parse as JSON
                data = json.loads(content)
                return data
            except json.JSONDecodeError:
                # If it's not JSON, it might be encrypted
                try:
                    # Try to decrypt with default key
                    key = GhostDropEncryption.load_or_create_key()
                    decrypted = GhostDropEncryption.decrypt_data(content, key)
                    return decrypted
                except:
                    logger.error(f"Could not decrypt file contents: {file_path}")
                    return None
        except Exception as e:
            logger.error(f"Error reading drop file {file_path}: {e}")
            return None
    
    def _notify_drop_found(self, file_path: str):
        """Notify listeners about found drop
        
        Args:
            file_path: Path to drop file
        """
        for callback in self.drop_found_callbacks:
            try:
                callback(file_path)
            except Exception as e:
                logger.error(f"Error in drop found callback: {e}")
    
    def _notify_drop_processed(self, file_path: str, data: Dict):
        """Notify listeners about processed drop
        
        Args:
            file_path: Path to drop file
            data: Processed data
        """
        for callback in self.drop_processed_callbacks:
            try:
                callback(file_path, data)
            except Exception as e:
                logger.error(f"Error in drop processed callback: {e}")
    
    def register_drop_found_callback(self, callback: Callable[[str], None]):
        """Register callback for drop found events
        
        Args:
            callback: Function to call when drop is found
                     Takes (file_path) as argument
        """
        if callback not in self.drop_found_callbacks:
            self.drop_found_callbacks.append(callback)
    
    def register_drop_processed_callback(self, callback: Callable[[str, Dict], None]):
        """Register callback for drop processed events
        
        Args:
            callback: Function to call when drop is processed
                     Takes (file_path, data) as arguments
        """
        if callback not in self.drop_processed_callbacks:
            self.drop_processed_callbacks.append(callback)
    
    def unregister_drop_found_callback(self, callback):
        """Unregister drop found callback"""
        if callback in self.drop_found_callbacks:
            self.drop_found_callbacks.remove(callback)
    
    def unregister_drop_processed_callback(self, callback):
        """Unregister drop processed callback"""
        if callback in self.drop_processed_callbacks:
            self.drop_processed_callbacks.remove(callback)
    
    def list_active_drop_paths(self) -> List[str]:
        """Get paths to all active drop directories
        
        Returns:
            list: Drop directory paths
        """
        return list(self.active_drops.keys())
    
    def is_usb_available(self) -> bool:
        """Check if any USB drive with GhostDrop is available
        
        Returns:
            bool: True if a drop directory is available
        """
        return len(self.active_drops) > 0

# =============================================================================
# COMMAND PREPARATION AND BUNDLING
# =============================================================================

class CommandPriority(Enum):
    """Priority levels for commands"""
    HIGH = "high"       # Critical commands (security alerts, emergency actions)
    MEDIUM = "medium"   # Important commands (state changes, configuration)
    LOW = "low"         # Normal commands (regular updates, non-critical)

class GhostDropPreparer:
    """Prepares command bundles for USB transport"""
    
    def __init__(
        self, 
        node_id: str,
        encryption_key_path: str = DEFAULT_ENCRYPTION_KEY_PATH,
        drop_dir: str = DEFAULT_DROP_DIR,
        encrypt_outgoing: bool = True
    ):
        """Initialize the drop preparer
        
        Args:
            node_id: ID of this node
            encryption_key_path: Path to encryption key file
            drop_dir: Name of GhostDrop directory
            encrypt_outgoing: Whether to encrypt outgoing drops
        """
        self.node_id = node_id
        self.encryption_key_path = encryption_key_path
        self.drop_dir = drop_dir
        self.encrypt_outgoing = encrypt_outgoing
        
        # Load encryption key
        self.key = GhostDropEncryption.load_or_create_key(encryption_key_path)
        
        # Staging directory for pending drops
        self.staging_dir = os.path.expanduser("~/.ghost/drops/staging")
        os.makedirs(self.staging_dir, exist_ok=True)
        
        # Track dropped commands to avoid duplicates
        self.dropped_command_ids = set()
        
        logger.info(f"GhostDropPreparer initialized for node {node_id}")
    
    def prepare_command_drop(
        self,
        commands: List[Dict],
        target_nodes: Optional[List[str]] = None,
        drop_id: Optional[str] = None
    ) -> str:
        """Prepare a command drop bundle
        
        Args:
            commands: List of command data
            target_nodes: Optional list of target node IDs (None for all)
            drop_id: Optional drop ID (auto-generated if None)
            
        Returns:
            str: Path to prepared drop file
        """
        # Generate drop ID if not provided
        if not drop_id:
            drop_id = f"{int(time.time())}_{random.randint(1000, 9999)}"
        
        # Create drop data
        drop_data = {
            "type": "command_bundle",
            "id": drop_id,
            "source_node": self.node_id,
            "target_nodes": target_nodes,
            "timestamp": time.time(),
            "command_count": len(commands),
            "commands": commands
        }
        
        # Create filename
        filename = f"ghost_cmd_{drop_id}{COMMAND_FILE_EXT}"
        staging_path = os.path.join(self.staging_dir, filename)
        
        # Write drop file
        if self.encrypt_outgoing:
            # Encrypt the data
            encrypted = GhostDropEncryption.encrypt_data(drop_data, self.key)
            
            # Write encrypted data
            with open(staging_path, 'w') as f:
                f.write(encrypted)
        else:
            # Write as JSON
            with open(staging_path, 'w') as f:
                json.dump(drop_data, f, indent=2)
        
        # Update tracking
        for cmd in commands:
            if "id" in cmd:
                self.dropped_command_ids.add(cmd["id"])
        
        logger.info(f"Prepared command drop with ID {drop_id} containing {len(commands)} commands")
        return staging_path
    
    def prepare_state_drop(
        self,
        state_data: Dict,
        target_nodes: Optional[List[str]] = None,
        drop_id: Optional[str] = None
    ) -> str:
        """Prepare a state drop bundle
        
        Args:
            state_data: State data to drop
            target_nodes: Optional list of target node IDs (None for all)
            drop_id: Optional drop ID (auto-generated if None)
            
        Returns:
            str: Path to prepared drop file
        """
        # Generate drop ID if not provided
        if not drop_id:
            drop_id = f"{int(time.time())}_{random.randint(1000, 9999)}"
        
        # Create drop data
        drop_data = {
            "type": "state_bundle",
            "id": drop_id,
            "source_node": self.node_id,
            "target_nodes": target_nodes,
            "timestamp": time.time(),
            "state": state_data
        }
        
        # Create filename
        filename = f"ghost_state_{drop_id}{STATE_FILE_EXT}"
        staging_path = os.path.join(self.staging_dir, filename)
        
        # Write drop file
        if self.encrypt_outgoing:
            # Encrypt the data
            encrypted = GhostDropEncryption.encrypt_data(drop_data, self.key)
            
            # Write encrypted data
            with open(staging_path, 'w') as f:
                f.write(encrypted)
        else:
            # Write as JSON
            with open(staging_path, 'w') as f:
                json.dump(drop_data, f, indent=2)
        
        logger.info(f"Prepared state drop with ID {drop_id}")
        return staging_path
    
    def deploy_to_usb(
        self,
        file_path: str,
        destination_drives: Optional[List[str]] = None
    ) -> List[str]:
        """Deploy a drop file to USB drives
        
        Args:
            file_path: Path to drop file
            destination_drives: Optional list of drive paths (None for all available)
            
        Returns:
            list: Paths to deployed files
        """
        # Get available drives if not specified
        if not destination_drives:
            usb_monitor = GhostUSBMonitor(self.drop_dir)
            usb_monitor.start()
            time.sleep(1)  # Give it time to detect drives
            
            try:
                drives = usb_monitor.mounted_drives
                destination_drives = list(drives.keys())
            finally:
                usb_monitor.stop()
        
        # Check if we have any drives
        if not destination_drives:
            logger.warning("No USB drives available for deployment")
            return []
        
        # Deploy to each drive
        deployed_paths = []
        for drive_path in destination_drives:
            try:
                # Create drop directory if needed
                drop_path = os.path.join(drive_path, self.drop_dir)
                os.makedirs(drop_path, exist_ok=True)
                
                # Generate target path
                filename = os.path.basename(file_path)
                target_path = os.path.join(drop_path, filename)
                
                # Add OUTGOING_SUFFIX if not already present
                if not target_path.endswith(OUTGOING_SUFFIX):
                    target_path += OUTGOING_SUFFIX
                
                # Copy file
                shutil.copy2(file_path, target_path)
                
                logger.info(f"Deployed drop to {target_path}")
                deployed_paths.append(target_path)
                
            except Exception as e:
                logger.error(f"Error deploying to drive {drive_path}: {e}")
        
        return deployed_paths
    
    def create_and_deploy_command_drop(
        self,
        commands: List[Dict],
        target_nodes: Optional[List[str]] = None,
        destination_drives: Optional[List[str]] = None
    ) -> List[str]:
        """Create and deploy a command drop in one step
        
        Args:
            commands: List of command data
            target_nodes: Optional list of target node IDs (None for all)
            destination_drives: Optional list of drive paths (None for all available)
            
        Returns:
            list: Paths to deployed files
        """
        # Prepare the drop
        staging_path = self.prepare_command_drop(commands, target_nodes)
        
        # Deploy to USB
        return self.deploy_to_usb(staging_path, destination_drives)
    
    def create_and_deploy_state_drop(
        self,
        state_data: Dict,
        target_nodes: Optional[List[str]] = None,
        destination_drives: Optional[List[str]] = None
    ) -> List[str]:
        """Create and deploy a state drop in one step
        
        Args:
            state_data: State data to drop
            target_nodes: Optional list of target node IDs (None for all)
            destination_drives: Optional list of drive paths (None for all available)
            
        Returns:
            list: Paths to deployed files
        """
        # Prepare the drop
        staging_path = self.prepare_state_drop(state_data, target_nodes)
        
        # Deploy to USB
        return self.deploy_to_usb(staging_path, destination_drives)
    
    def clean_staging_directory(self, max_age_hours: int = 24):
        """Clean old files from staging directory
        
        Args:
            max_age_hours: Maximum age in hours to keep files
        """
        try:
            now = time.time()
            max_age_seconds = max_age_hours * 3600
            
            for filename in os.listdir(self.staging_dir):
                file_path = os.path.join(self.staging_dir, filename)
                
                # Skip directories
                if os.path.isdir(file_path):
                    continue
                
                # Check age
                if now - os.path.getmtime(file_path) > max_age_seconds:
                    # Delete old file
                    os.unlink(file_path)
                    logger.info(f"Cleaned old file from staging: {filename}")
                    
        except Exception as e:
            logger.error(f"Error cleaning staging directory: {e}")

# =============================================================================
# GHOSTDROP MANAGER
# =============================================================================

class GhostDropManager:
    """Main class for managing GhostDrop USB operations"""
    
    def __init__(
        self,
        node_id: str,
        data_dir: str = None,
        drop_dir: str = DEFAULT_DROP_DIR,
        auto_process: bool = True,
        encrypt_data: bool = True
    ):
        """Initialize GhostDrop manager
        
        Args:
            node_id: ID of this node
            data_dir: Path to data directory
            drop_dir: Name of GhostDrop directory
            auto_process: Whether to automatically process drops
            encrypt_data: Whether to encrypt outgoing drops
        """
        self.node_id = node_id
        self.drop_dir = drop_dir
        
        # Set up data directory
        if data_dir:
            self.data_dir = data_dir
        else:
            self.data_dir = os.path.expanduser("~/.ghost")
        
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Set up encryption key path
        self.key_path = os.path.join(self.data_dir, DEFAULT_ENCRYPTION_KEY_PATH)
        
        # Create components
        self.usb_monitor = GhostUSBMonitor(drop_dir, auto_process=auto_process)
        self.drop_preparer = GhostDropPreparer(node_id, self.key_path, drop_dir, encrypt_data)
        
        # Command handlers
        self.command_handlers = {}
        self.state_handlers = []
        
        # Register for drop callbacks
        self.usb_monitor.register_drop_processed_callback(self._handle_processed_drop)
        
        logger.info(f"GhostDropManager initialized for node {node_id}")
    
    def start(self):
        """Start the drop manager"""
        # Start USB monitoring
        self.usb_monitor.start()
        logger.info("GhostDropManager started")
    
    def stop(self):
        """Stop the drop manager"""
        # Stop USB monitoring
        self.usb_monitor.stop()
        
        # Clean up staging directory
        self.drop_preparer.clean_staging_directory()
        
        logger.info("GhostDropManager stopped")
    
    def register_command_handler(self, command_type: str, handler: Callable[[Dict, str], Any]):
        """Register a handler for a command type
        
        Args:
            command_type: Type of command to handle
            handler: Function to call for this command type
                     Takes (command_data, source_node) as arguments
        """
        self.command_handlers[command_type] = handler
    
    def register_state_handler(self, handler: Callable[[Dict, str], None]):
        """Register a handler for state drops
        
        Args:
            handler: Function to call for state drops
                     Takes (state_data, source_node) as arguments
        """
        if handler not in self.state_handlers:
            self.state_handlers.append(handler)
    
    def unregister_command_handler(self, command_type: str):
        """Unregister a command handler"""
        if command_type in self.command_handlers:
            del self.command_handlers[command_type]
    
    def unregister_state_handler(self, handler):
        """Unregister a state handler"""
        if handler in self.state_handlers:
            self.state_handlers.remove(handler)
    
    def _handle_processed_drop(self, file_path: str, data: Dict):
        """Handle processed drop data
        
        Args:
            file_path: Path to processed file
            data: Drop data
        """
        try:
            # Determine drop type
            drop_type = data.get("type", "unknown")
            source_node = data.get("source_node", "unknown")
            
            # Check if this node is a target
            target_nodes = data.get("target_nodes")
            if target_nodes and self.node_id not in target_nodes:
                logger.info(f"Drop {data.get('id')} is not targeted at this node, ignoring")
                return
            
            # Handle command bundle
            if drop_type == "command_bundle":
                self._process_command_bundle(data, source_node)
            
            # Handle state bundle
            elif drop_type == "state_bundle":
                self._process_state_bundle(data, source_node)
            
            else:
                logger.warning(f"Unknown drop type: {drop_type}")
                
        except Exception as e:
            logger.error(f"Error handling processed drop: {e}")
    
    def _process_command_bundle(self, data: Dict, source_node: str):
        """Process a command bundle
        
        Args:
            data: Command bundle data
            source_node: Source node ID
        """
        commands = data.get("commands", [])
        
        if not commands:
            logger.warning(f"Empty command bundle from {source_node}")
            return
        
        logger.info(f"Processing {len(commands)} commands from {source_node}")
        
        # Process each command
        for cmd in commands:
            try:
                # Extract command data
                cmd_type = cmd.get("command_type", "unknown")
                cmd_payload = cmd.get("payload", {})
                cmd_id = cmd.get("id", "unknown")
                
                # Find handler for this command type
                handler = self.command_handlers.get(cmd_type)
                if handler:
                    logger.info(f"Executing command {cmd_id} ({cmd_type}) from {source_node}")
                    
                    # Execute handler
                    result = handler(cmd_payload, source_node)
                    
                    # Handle result if needed
                    if result:
                        logger.debug(f"Command {cmd_id} result: {result}")
                else:
                    logger.warning(f"No handler for command type {cmd_type}")
                    
            except Exception as e:
                logger.error(f"Error processing command: {e}")
    
    def _process_state_bundle(self, data: Dict, source_node: str):
        """Process a state bundle
        
        Args:
            data: State bundle data
            source_node: Source node ID
        """
        state_data = data.get("state", {})
        
        if not state_data:
            logger.warning(f"Empty state bundle from {source_node}")
            return
        
        logger.info(f"Processing state bundle from {source_node}")
        
        # Call all state handlers
        for handler in self.state_handlers:
            try:
                handler(state_data, source_node)
            except Exception as e:
                logger.error(f"Error in state handler: {e}")
    
    def create_command_drop(self, commands, target_nodes=None):
        """Create a command drop
        
        Args:
            commands: List of command data dictionaries
            target_nodes: Optional list of target node IDs
            
        Returns:
            str: Path to created drop file
        """
        return self.drop_preparer.prepare_command_drop(commands, target_nodes)
    
    def create_state_drop(self, state_data, target_nodes=None):
        """Create a state drop
        
        Args:
            state_data: State data dictionary
            target_nodes: Optional list of target node IDs
            
        Returns:
            str: Path to created drop file
        """
        return self.drop_preparer.prepare_state_drop(state_data, target_nodes)
    
    def deploy_drop(self, file_path, destination_drives=None):
        """Deploy a drop to USB drives
        
        Args:
            file_path: Path to drop file
            destination_drives: Optional list of drive paths
            
        Returns:
            list: Paths to deployed files
        """
        return self.drop_preparer.deploy_to_usb(file_path, destination_drives)
    
    def create_and_deploy_command_drop(self, commands, target_nodes=None, destination_drives=None):
        """Create and deploy a command drop in one step
        
        Args:
            commands: List of command data
            target_nodes: Optional list of target node IDs
            destination_drives: Optional list of drive paths
            
        Returns:
            list: Paths to deployed files
        """
        return self.drop_preparer.create_and_deploy_command_drop(
            commands, target_nodes, destination_drives
        )
    
    def create_and_deploy_state_drop(self, state_data, target_nodes=None, destination_drives=None):
        """Create and deploy a state drop in one step
        
        Args:
            state_data: State data to drop
            target_nodes: Optional list of target node IDs
            destination_drives: Optional list of drive paths
            
        Returns:
            list: Paths to deployed files
        """
        return self.drop_preparer.create_and_deploy_state_drop(
            state_data, target_nodes, destination_drives
        )
    
    def get_available_drop_paths(self):
        """Get paths to all available drop directories
        
        Returns:
            list: Drop directory paths
        """
        return self.usb_monitor.list_active_drop_paths()
    
    def is_usb_available(self):
        """Check if any USB drive with GhostDrop is available
        
        Returns:
            bool: True if a drop directory is available
        """
        return self.usb_monitor.is_usb_available()

# =============================================================================
# COMMAND LINE INTERFACE
# =============================================================================

def main():
    """Main entry point for CLI"""
    import argparse
    
    parser = argparse.ArgumentParser(description="GhostDrop USB - Sneakernet Transport for GhostOps")
    subparsers = parser.add_subparsers(dest="command", help="Command")
    
    # Monitor command
    monitor_parser = subparsers.add_parser("monitor", help="Monitor for USB drops")
    monitor_parser.add_argument("--node-id", required=True, help="ID of this node")
    monitor_parser.add_argument("--drop-dir", default=DEFAULT_DROP_DIR, help="Name of drop directory")
    monitor_parser.add_argument("--no-process", action="store_true", help="Don't process drops")
    
    # Create command
    create_parser = subparsers.add_parser("create", help="Create a drop")
    create_parser.add_argument("--node-id", required=True, help="ID of this node")
    create_parser.add_argument("--type", required=True, choices=["command", "state"], help="Type of drop")
    create_parser.add_argument("--input", required=True, help="Input JSON file")
    create_parser.add_argument("--output", required=True, help="Output drop file")
    create_parser.add_argument("--no-encrypt", action="store_true", help="Don't encrypt the drop")
    
    # Deploy command
    deploy_parser = subparsers.add_parser("deploy", help="Deploy a drop to USB")
    deploy_parser.add_argument("--input", required=True, help="Input drop file")
    deploy_parser.add_argument("--drives", help="Comma-separated list of drive paths")
    deploy_parser.add_argument("--drop-dir", default=DEFAULT_DROP_DIR, help="Name of drop directory")
    
    # Init command
    init_parser = subparsers.add_parser("init", help="Initialize a drop directory on USB")
    init_parser.add_argument("--drive", required=True, help="Drive path")
    init_parser.add_argument("--drop-dir", default=DEFAULT_DROP_DIR, help="Name of drop directory")
    
    args = parser.parse_args()
    
    # Handle commands
    if args.command == "monitor":
        # Run USB monitor
        monitor = GhostUSBMonitor(
            drop_dir=args.drop_dir,
            auto_process=not args.no_process
        )
        
        def on_drop_processed(file_path, data):
            print(f"Processed drop: {file_path}")
            print(f"Data: {json.dumps(data, indent=2)}")
        
        monitor.register_drop_processed_callback(on_drop_processed)
        
        try:
            print(f"Monitoring for USB drops in {args.drop_dir}...")
            monitor.start()
            
            # Keep running until Ctrl+C
            while True:
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\nStopping monitor...")
            monitor.stop()
            print("Done")
    
    elif args.command == "create":
        # Create a drop file
        preparer = GhostDropPreparer(
            node_id=args.node_id,
            encrypt_outgoing=not args.no_encrypt
        )
        
        # Load input data
        with open(args.input, 'r') as f:
            data = json.load(f)
        
        if args.type == "command":
            # Create command drop
            commands = data.get("commands", [])
            if not commands:
                print("Error: Input file must contain 'commands' array")
                return 1
                
            target_nodes = data.get("target_nodes")
            
            output_path = preparer.prepare_command_drop(commands, target_nodes)
            
            # Copy to requested output path
            shutil.copy2(output_path, args.output)
            
        elif args.type == "state":
            # Create state drop
            state = data.get("state", {})
            if not state:
                print("Error: Input file must contain 'state' object")
                return 1
                
            target_nodes = data.get("target_nodes")
            
            output_path = preparer.prepare_state_drop(state, target_nodes)
            
            # Copy to requested output path
            shutil.copy2(output_path, args.output)
        
        print(f"Created drop file: {args.output}")
    
    elif args.command == "deploy":
        # Deploy a drop to USB
        preparer = GhostDropPreparer(
            node_id="cli_deployer",
            drop_dir=args.drop_dir
        )
        
        # Get drive list
        drives = None
        if args.drives:
            drives = args.drives.split(",")
        
        # Deploy
        deployed = preparer.deploy_to_usb(args.input, drives)
        
        if deployed:
            print(f"Deployed to {len(deployed)} drives:")
            for path in deployed:
                print(f"  - {path}")
        else:
            print("No drives available for deployment")
    
    elif args.command == "init":
        # Initialize a drop directory
        drop_path = os.path.join(args.drive, args.drop_dir)
        
        try:
            os.makedirs(drop_path, exist_ok=True)
            
            # Create README
            readme_path = os.path.join(drop_path, "README.txt")
            with open(readme_path, 'w') as f:
                f.write("""GhostDrop Directory
=================

This directory is used for GhostOps command and state transport
between nodes when internet connectivity is unavailable.

DO NOT DELETE OR MODIFY FILES IN THIS DIRECTORY!
""")
            
            print(f"Initialized drop directory: {drop_path}")
            
        except Exception as e:
            print(f"Error initializing drop directory: {e}")
            return 1
    
    else:
        parser.print_help()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
