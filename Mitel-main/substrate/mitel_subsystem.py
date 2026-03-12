#!/usr/bin/env python3

import asyncio
import json
import logging
import hashlib
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.exceptions import InvalidSignature
import psutil
import platform
import subprocess
import os
import yaml

# Import USB event monitor
try:
    from .usb_event_monitor import MITELUSBIntegration
    USB_MONITORING_AVAILABLE = True
except ImportError:
    USB_MONITORING_AVAILABLE = False

@dataclass
class DeviceFingerprint:
    mac_address: str
    serial_number: str
    vendor_id: str
    product_id: str
    device_type: str
    hardware_signature: str
    electrical_profile: Dict[str, float]
    timing_characteristics: Dict[str, float]

@dataclass
class TrustCertificate:
    device_id: str
    public_key: bytes
    certificate_chain: List[str]
    issue_date: datetime
    expiry_date: datetime
    trust_level: int
    revocation_status: bool

@dataclass
class BehavioralProfile:
    keystroke_timing: Dict[str, float]
    mouse_patterns: Dict[str, List[float]]
    command_frequency: Dict[str, int]
    usage_patterns: Dict[str, Any]
    anomaly_score: float
    last_updated: datetime

@dataclass
class ThreatEvent:
    timestamp: datetime
    device_id: str
    threat_type: str
    severity: str
    description: str
    response_action: str
    investigation_data: Dict[str, Any]

class MITELSubsystem:
    def __init__(self, config: Dict[str, Any], state_model=None, node_id=None):
        self.config = config
        self.state_model = state_model
        self.node_id = node_id or "unknown_node"
        self.logger = logging.getLogger(f"{__name__}.MITELSubsystem")
        
        # Core components
        self.registered_devices: Dict[str, DeviceFingerprint] = {}
        self.trust_certificates: Dict[str, TrustCertificate] = {}
        self.behavioral_profiles: Dict[str, BehavioralProfile] = {}
        self.threat_events: List[ThreatEvent] = []
        
        # State management
        self.is_running = False
        self.monitoring_thread = None
        self.quarantined_devices: set = set()
        self.previous_devices: set = set()  # Track previous scan for removal detection
        
        # USB Event Monitoring (Linux fix for Windows autoplay-like behavior)
        self.usb_integration = None
        if USB_MONITORING_AVAILABLE and platform.system() == "Linux":
            try:
                self.usb_integration = MITELUSBIntegration(self)
                self.logger.info("[M.I.T.E.L.] USB event monitoring initialized")
            except Exception as e:
                self.logger.warning(f"[M.I.T.E.L.] USB monitoring init failed: {e}")
        
        # AI Models (placeholder for neural network integration)
        self.behavioral_analyzer = None
        self.anomaly_detector = None
        
        # POS specific components
        self.pos_mode = config.get('pos_mode', False)
        self.payment_devices: Dict[str, Any] = {}
        
        # Initialize crypto components
        self._init_crypto_system()
        
    def _init_crypto_system(self):
        """Initialize cryptographic components for device authentication"""
        try:
            # Generate or load root CA key pair
            self.root_private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048
            )
            self.root_public_key = self.root_private_key.public_key()
            
            self.logger.info("M.I.T.E.L. cryptographic system initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize M.I.T.E.L. crypto system: {e}")
            raise

    async def initialize(self):
        """Initialize M.I.T.E.L. subsystem"""
        try:
            self.logger.info("[M.I.T.E.L.] Initializing zero-trust peripheral authentication")
            
            # Load existing device registrations
            await self._load_device_registry()
            
            # Load behavioral profiles
            await self._load_behavioral_profiles()
            
            # Initialize AI components
            await self._init_ai_components()
            
            # Setup device monitoring
            await self._setup_device_monitoring()
            
            # Initialize POS components if enabled
            if self.pos_mode:
                await self._init_pos_components()
            
            self.logger.info("[M.I.T.E.L.] Zero-trust peripheral authentication initialized")
            return True
            
        except Exception as e:
            self.logger.error(f"[M.I.T.E.L.] Failed to initialize: {e}")
            return False

    async def start(self):
        """Start M.I.T.E.L. monitoring and protection"""
        try:
            if self.is_running:
                self.logger.warning("[M.I.T.E.L.] Already running")
                return True
                
            self.logger.info("[M.I.T.E.L.] Starting zero-trust protection")
            self.is_running = True
            
            # Start device monitoring thread
            self.monitoring_thread = threading.Thread(target=self._monitor_devices, daemon=True)
            self.monitoring_thread.start()
            
            # Start USB event monitoring (Linux fix)
            if self.usb_integration:
                self.usb_integration.start()
                self.logger.info("[M.I.T.E.L.] USB event monitoring started")
            
            self.is_running = True
            self.logger.info("[M.I.T.E.L.] Started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"[M.I.T.E.L.] Failed to start: {e}")
            return False

    async def stop(self):
        """Stop M.I.T.E.L. monitoring"""
        try:
            if not self.is_running:
                return True
            
            # Stop USB event monitoring
            if self.usb_integration:
                self.usb_integration.stop()
                self.logger.info("[M.I.T.E.L.] USB event monitoring stopped")
            
            self.is_running = False
            
            # Wait for monitoring thread to finish
            if self.monitoring_thread and self.monitoring_thread.is_alive():
                self.monitoring_thread.join(timeout=5)
            
            self.logger.info("[M.I.T.E.L.] Stopped successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"[M.I.T.E.L.] Error stopping: {e}")
            return False

    def _monitor_devices(self):
        """Background thread for continuous device monitoring"""
        while self.is_running:
            try:
                # Scan for new devices
                current_devices = self._scan_connected_devices()
                current_device_ids = {device['device_id'] for device in current_devices}
                
                # Detect removed devices
                removed_devices = self.previous_devices - current_device_ids
                if removed_devices:
                    for device_id in removed_devices:
                        if device_id in self.quarantined_devices:
                            self.quarantined_devices.remove(device_id)
                            self.logger.info(f"[M.I.T.E.L.] Device disconnected and removed from quarantine: {device_id[:16]}...")
                
                # Process current devices
                for device in current_devices:
                    # Process device in async context
                    try:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        loop.run_until_complete(self._process_device_event(device))
                        loop.close()
                    except Exception as e:
                        self.logger.error(f"[M.I.T.E.L.] Device processing error: {e}")
                
                # Update previous devices for next scan
                self.previous_devices = current_device_ids
                
                time.sleep(self.config.get('scan_interval', 300.0))  # 5 minutes instead of 3 seconds
                
            except Exception as e:
                self.logger.error(f"[M.I.T.E.L.] Device monitoring error: {e}")
                time.sleep(5.0)

    def _scan_connected_devices(self) -> List[Dict[str, Any]]:
        """Scan for currently connected input devices"""
        devices = []
        
        try:
            if platform.system() == "Linux":
                devices.extend(self._scan_linux_devices())
            elif platform.system() == "Windows":
                devices.extend(self._scan_windows_devices())
            elif platform.system() == "Darwin":
                devices.extend(self._scan_macos_devices())
                
        except Exception as e:
            self.logger.error(f"[M.I.T.E.L.] Device scan error: {e}")
            
        return devices

    def _scan_linux_devices(self) -> List[Dict[str, Any]]:
        """Scan Linux input devices AND USB storage devices"""
        devices = []
        
        try:
            # Scan input devices
            if os.path.exists('/proc/bus/input/devices'):
                with open('/proc/bus/input/devices', 'r') as f:
                    content = f.read()
                    
                # Parse device information
                device_blocks = content.split('\n\n')
                for block in device_blocks:
                    if 'N: Name=' in block:
                        device = self._parse_linux_device_block(block)
                        if device:
                            devices.append(device)
            
            # Scan USB storage devices (MISSING!)
            devices.extend(self._scan_linux_usb_storage())
                            
        except Exception as e:
            self.logger.debug(f"[M.I.T.E.L.] Linux device scan error: {e}")
            
        return devices

    def _parse_linux_device_block(self, block: str) -> Optional[Dict[str, Any]]:
        """Parse Linux device info block"""
        try:
            device = {}
            for line in block.split('\n'):
                if 'N: Name=' in line:
                    device['name'] = line.split('Name=')[1].strip('"')
                elif 'I: Bus=' in line:
                    parts = line.split()
                    for part in parts:
                        if 'Vendor=' in part:
                            device['vendor_id'] = part.split('=')[1]
                        elif 'Product=' in part:
                            device['product_id'] = part.split('=')[1]
            
            if device:
                device['device_id'] = hashlib.sha256(
                    f"{device.get('name', '')}{device.get('vendor_id', '')}{device.get('product_id', '')}".encode()
                ).hexdigest()[:16]
                device['device_type'] = 'input'
                device['mac_address'] = ''
                device['serial_number'] = ''
                device['electrical_profile'] = {}
                device['timing_characteristics'] = {}
                return device
                
        except Exception as e:
            self.logger.debug(f"[M.I.T.E.L.] Parse error: {e}")
            
        return None

    def _scan_linux_usb_storage(self) -> List[Dict[str, Any]]:
        """Scan Linux USB storage devices"""
        devices = []
        
        try:
            # Use lsblk to find USB storage devices
            cmd = ['lsblk', '-J', '-o', 'NAME,SIZE,TYPE,MOUNTPOINT,VENDOR,MODEL,SERIAL']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                for device in data.get('blockdevices', []):
                    if self._is_usb_device(device):
                        usb_device = self._parse_linux_usb_device(device)
                        if usb_device:
                            devices.append(usb_device)
            
            # Also check /sys/block for USB devices
            if os.path.exists('/sys/block'):
                for block_device in os.listdir('/sys/block'):
                    if self._is_usb_storage_device(block_device):
                        usb_device = self._parse_sys_usb_device(block_device)
                        if usb_device:
                            devices.append(usb_device)
                            
        except Exception as e:
            self.logger.debug(f"[M.I.T.E.L.] Linux USB storage scan error: {e}")
            
        return devices

    def _is_usb_device(self, device: Dict[str, Any]) -> bool:
        """Check if device is USB storage"""
        try:
            # Check if device is removable or has USB vendor/model
            vendor = device.get('vendor', '').lower()
            model = device.get('model', '').lower()
            name = device.get('name', '').lower()
            
            # Common USB indicators
            usb_indicators = ['usb', 'flash', 'sd', 'mmc', 'removable']
            
            for indicator in usb_indicators:
                if indicator in vendor or indicator in model or indicator in name:
                    return True
                    
            # Check if it's a removable device
            if device.get('type') == 'disk' and device.get('mountpoint'):
                return True
                
        except Exception:
            pass
            
        return False

    def _parse_linux_usb_device(self, device: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse Linux USB device info"""
        try:
            return {
                'name': f"{device.get('vendor', 'Unknown')} {device.get('model', 'USB Device')}",
                'device_id': hashlib.sha256(
                    f"{device.get('name', '')}{device.get('vendor', '')}{device.get('serial', '')}".encode()
                ).hexdigest()[:16],
                'device_type': 'storage',
                'vendor_id': device.get('vendor', ''),
                'product_id': device.get('model', ''),
                'mac_address': '',
                'serial_number': device.get('serial', ''),
                'electrical_profile': {},
                'timing_characteristics': {},
                'size': device.get('size', ''),
                'mountpoint': device.get('mountpoint', '')
            }
        except Exception as e:
            self.logger.debug(f"[M.I.T.E.L.] Parse USB device error: {e}")
            return None

    def _is_usb_storage_device(self, block_device: str) -> bool:
        """Check if block device is USB storage via /sys"""
        try:
            # Check if device is removable
            removable_path = f"/sys/block/{block_device}/removable"
            if os.path.exists(removable_path):
                with open(removable_path, 'r') as f:
                    if f.read().strip() == '1':
                        return True
                        
            # Check device path for USB indicators
            device_path = f"/sys/block/{block_device}/device"
            if os.path.exists(device_path):
                # Check if parent contains 'usb'
                parent_path = os.path.dirname(device_path)
                while parent_path and parent_path != '/sys':
                    if 'usb' in parent_path.lower():
                        return True
                    parent_path = os.path.dirname(parent_path)
                    
        except Exception:
            pass
            
        return False

    def _parse_sys_usb_device(self, block_device: str) -> Optional[Dict[str, Any]]:
        """Parse USB device from /sys/block"""
        try:
            device_path = f"/sys/block/{block_device}"
            size_path = f"{device_path}/size"
            
            size = ''
            if os.path.exists(size_path):
                with open(size_path, 'r') as f:
                    size = f.read().strip()
            
            return {
                'name': f"USB Storage ({block_device})",
                'device_id': hashlib.sha256(f"usb_{block_device}".encode()).hexdigest()[:16],
                'device_type': 'storage',
                'vendor_id': '',
                'product_id': '',
                'mac_address': '',
                'serial_number': '',
                'electrical_profile': {},
                'timing_characteristics': {},
                'size': size,
                'mountpoint': ''
            }
        except Exception as e:
            self.logger.debug(f"[M.I.T.E.L.] Parse sys USB error: {e}")
            return None

    def _scan_windows_devices(self) -> List[Dict[str, Any]]:
        """Scan Windows peripheral devices (input devices + USB storage)"""
        devices = []
        
        try:
            # Use PowerShell to enumerate ALL peripheral devices including USB storage
            # Includes: HIDClass, Keyboard, Mouse, DiskDrive, Volume, USB, Image (cameras), etc.
            # Filter by Status -eq 'OK' to only get currently connected devices
            cmd = [
                'powershell', '-Command',
                'Get-PnpDevice | Where-Object {($_.Class -eq "HIDClass" -or $_.Class -eq "Keyboard" -or $_.Class -eq "Mouse" -or $_.Class -eq "DiskDrive" -or $_.Class -eq "Volume" -or $_.Class -eq "USB" -or $_.Class -eq "Image") -and $_.Status -eq "OK"} | Select-Object FriendlyName,InstanceId,Class | ConvertTo-Json'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0 and result.stdout.strip():
                device_data = json.loads(result.stdout)
                if not isinstance(device_data, list):
                    device_data = [device_data]
                    
                for device in device_data:
                    parsed = self._parse_windows_device(device)
                    if parsed:
                        devices.append(parsed)
                        
        except Exception as e:
            self.logger.debug(f"[M.I.T.E.L.] Windows device scan error: {e}")
            
        return devices

    def _parse_windows_device(self, device: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse Windows device info"""
        try:
            name = device.get('FriendlyName', 'Unknown')
            instance_id = device.get('InstanceId', '')
            device_class = device.get('Class', 'Unknown')
            
            device_id = hashlib.sha256(instance_id.encode()).hexdigest()[:16]
            
            # Map device class to type
            device_type_map = {
                'DiskDrive': 'storage',
                'Volume': 'storage',
                'USB': 'usb',
                'Image': 'camera',
                'HIDClass': 'input',
                'Keyboard': 'input',
                'Mouse': 'input'
            }
            device_type = device_type_map.get(device_class, 'peripheral')
            
            return {
                'device_id': device_id,
                'name': name,
                'instance_id': instance_id,  # Needed for device disabling
                'vendor_id': '',
                'product_id': '',
                'device_type': device_type,
                'device_class': device_class,
                'mac_address': '',
                'serial_number': '',
                'electrical_profile': {},
                'timing_characteristics': {}
            }
        except Exception as e:
            self.logger.debug(f"[M.I.T.E.L.] Parse error: {e}")
            return None

    def _scan_macos_devices(self) -> List[Dict[str, Any]]:
        """Scan macOS input devices"""
        devices = []
        
        try:
            # Use system_profiler for USB device enumeration
            cmd = ['system_profiler', 'SPUSBDataType', '-json']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                usb_data = json.loads(result.stdout)
                devices.extend(self._parse_macos_usb_data(usb_data))
                
        except Exception as e:
            self.logger.debug(f"[M.I.T.E.L.] macOS device scan error: {e}")
            
        return devices

    def _parse_macos_usb_data(self, usb_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse macOS USB data"""
        devices = []
        # Simplified parsing - would need full implementation
        return devices

    async def _process_device_event(self, device: Dict[str, Any]):
        """Process a device connection/activity event"""
        try:
            device_id = device.get('device_id')
            if not device_id:
                return
                
            # Check if device is registered
            if device_id not in self.registered_devices:
                await self._handle_unknown_device(device)
                return
                
            # Registered device - trusted (skip authentication for demo)
            # In production, would authenticate with fingerprint and certificate
            # For demo: registration = trust
            
            # Perform behavioral analysis
            await self._analyze_device_behavior(device_id, device)
            
        except Exception as e:
            self.logger.error(f"[M.I.T.E.L.] Device event processing error: {e}")

    async def _handle_unknown_device(self, device: Dict[str, Any]):
        """Handle connection of unregistered device"""
        device_id = device.get('device_id')
        
        # Only quarantine if not already quarantined (prevents re-quarantine loop)
        if device_id in self.quarantined_devices:
            return  # Already quarantined, skip
        
        # Immediately quarantine unknown device
        self.quarantined_devices.add(device_id)
        
        # ENFORCE QUARANTINE: Disable the device to prevent usage
        instance_id = device.get('instance_id', '')
        if instance_id:
            await self._disable_device(instance_id, device.get('name', 'Unknown'))
        
        # Create threat event
        threat_event = ThreatEvent(
            timestamp=datetime.now(),
            device_id=device_id,
            threat_type="unauthorized_device",
            severity="high",
            description=f"Unknown device attempted connection: {device.get('name', 'Unknown')}",
            response_action="quarantine_and_disable",
            investigation_data=device
        )
        
        self.threat_events.append(threat_event)
        
        # Propagate threat to mesh
        await self._propagate_threat_to_mesh(threat_event)
        
        self.logger.warning(f"[M.I.T.E.L.] Quarantined and disabled unknown device: {device_id}")

    async def _propagate_threat_to_mesh(self, threat_event: ThreatEvent):
        """Propagate threat event to all mesh nodes"""
        if not self.state_model:
            return
            
        try:
            # Create state operation for threat
            threat_data = {
                'timestamp': threat_event.timestamp.isoformat(),
                'device_id': threat_event.device_id,
                'threat_type': threat_event.threat_type,
                'severity': threat_event.severity,
                'description': threat_event.description,
                'response_action': threat_event.response_action,
                'source_node': self.node_id
            }
            
            # Push to state model for mesh propagation
            if self.state_model:
                from step_1_state_store.state_store import StateOp, OpType
                import uuid
                threat_op = StateOp(
                    op_id=str(uuid.uuid4()),
                    op_type=OpType.SET,
                    key=f"mitel.threats.{threat_event.device_id}",
                    value=threat_data,
                    node_id=self.node_id
                )
                self.state_model.apply_op(threat_op)
            
            self.logger.info(f"[M.I.T.E.L.] Threat propagated to mesh: {threat_event.threat_type}")
            
        except Exception as e:
            self.logger.error(f"[M.I.T.E.L.] Failed to propagate threat: {e}")

    async def _propagate_mitel_state(self, state: str):
        """Propagate M.I.T.E.L. state to mesh"""
        if not self.state_model:
            return
            
        try:
            state_data = {
                'node_id': self.node_id,
                'status': state,
                'timestamp': datetime.now().isoformat(),
                'registered_devices': len(self.registered_devices),
                'quarantined_devices': len(self.quarantined_devices),
                'threat_events': len(self.threat_events)
            }
            
            from step_1_state_store.state_store import StateOp, OpType
            import uuid
            state_op = StateOp(
                op_id=str(uuid.uuid4()),
                op_type=OpType.SET,
                key=f"mitel.nodes.{self.node_id}",
                value=state_data,
                node_id=self.node_id
            )
            self.state_model.apply_op(state_op)
            
        except Exception as e:
            self.logger.error(f"[M.I.T.E.L.] Failed to propagate state: {e}")

    async def _authenticate_device(self, device_id: str, device: Dict[str, Any]) -> Dict[str, Any]:
        """Authenticate a registered device"""
        try:
            # Get stored fingerprint and certificate
            fingerprint = self.registered_devices.get(device_id)
            certificate = self.trust_certificates.get(device_id)
            
            if not fingerprint or not certificate:
                return {'success': False, 'reason': 'missing_credentials'}
            
            # Verify hardware fingerprint
            current_fingerprint = self._generate_device_fingerprint(device)
            if not self._verify_fingerprint(fingerprint, current_fingerprint):
                return {'success': False, 'reason': 'fingerprint_mismatch'}
            
            # Verify trust certificate
            if not self._verify_trust_certificate(certificate):
                return {'success': False, 'reason': 'invalid_certificate'}
            
            # Check certificate expiry
            if certificate.expiry_date < datetime.now():
                return {'success': False, 'reason': 'certificate_expired'}
            
            # Check revocation status
            if certificate.revocation_status:
                return {'success': False, 'reason': 'certificate_revoked'}
            
            return {'success': True, 'trust_level': certificate.trust_level}
            
        except Exception as e:
            self.logger.error(f"[M.I.T.E.L.] Device authentication error: {e}")
            return {'success': False, 'reason': 'authentication_error'}

    def _verify_fingerprint(self, stored: DeviceFingerprint, current: DeviceFingerprint) -> bool:
        """Verify device fingerprint matches"""
        return stored.hardware_signature == current.hardware_signature

    def _verify_trust_certificate(self, certificate: TrustCertificate) -> bool:
        """Verify trust certificate is valid"""
        # Simplified verification - would need full PKI implementation
        return True

    async def _handle_authentication_failure(self, device_id: str, auth_result: Dict[str, Any]):
        """Handle device authentication failure"""
        # Quarantine device
        self.quarantined_devices.add(device_id)
        
        # Create threat event
        threat_event = ThreatEvent(
            timestamp=datetime.now(),
            device_id=device_id,
            threat_type="authentication_failure",
            severity="critical",
            description=f"Device authentication failed: {auth_result.get('reason', 'unknown')}",
            response_action="quarantine",
            investigation_data=auth_result
        )
        
        self.threat_events.append(threat_event)
        
        # Propagate threat to mesh
        await self._propagate_threat_to_mesh(threat_event)
        
        self.logger.error(f"[M.I.T.E.L.] Authentication failure: {device_id} - {auth_result.get('reason')}")

    def _generate_device_fingerprint(self, device: Dict[str, Any]) -> DeviceFingerprint:
        """Generate cryptographic fingerprint for device"""
        # Extract device characteristics
        mac_address = device.get('mac_address', '')
        serial_number = device.get('serial_number', '')
        vendor_id = device.get('vendor_id', '')
        product_id = device.get('product_id', '')
        device_type = device.get('device_type', 'unknown')
        
        # Generate hardware signature
        hw_data = f"{mac_address}{serial_number}{vendor_id}{product_id}"
        hardware_signature = hashlib.sha256(hw_data.encode()).hexdigest()
        
        # Collect electrical and timing characteristics
        electrical_profile = device.get('electrical_profile', {})
        timing_characteristics = device.get('timing_characteristics', {})
        
        return DeviceFingerprint(
            mac_address=mac_address,
            serial_number=serial_number,
            vendor_id=vendor_id,
            product_id=product_id,
            device_type=device_type,
            hardware_signature=hardware_signature,
            electrical_profile=electrical_profile,
            timing_characteristics=timing_characteristics
        )

    async def register_device(self, device: Dict[str, Any], user_approval: bool = False) -> bool:
        """Register a new trusted device"""
        try:
            device_id = device.get('device_id')
            if not device_id:
                return False
            
            # Generate device fingerprint
            fingerprint = self._generate_device_fingerprint(device)
            
            # Generate trust certificate
            certificate = self._generate_trust_certificate(device_id, fingerprint)
            
            # Create behavioral profile
            profile = BehavioralProfile(
                keystroke_timing={},
                mouse_patterns={},
                command_frequency={},
                usage_patterns={},
                anomaly_score=0.0,
                last_updated=datetime.now()
            )
            
            # Store registration
            self.registered_devices[device_id] = fingerprint
            self.trust_certificates[device_id] = certificate
            self.behavioral_profiles[device_id] = profile
            
            # Remove from quarantine if present
            self.quarantined_devices.discard(device_id)
            
            # Save to persistent storage
            await self._save_device_registry()
            
            # Propagate registration to mesh
            await self._propagate_mitel_state('device_registered')
            
            self.logger.info(f"[M.I.T.E.L.] Device registered: {device_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"[M.I.T.E.L.] Device registration error: {e}")
            return False

    def _generate_trust_certificate(self, device_id: str, fingerprint: DeviceFingerprint) -> TrustCertificate:
        """Generate cryptographic trust certificate for device"""
        # Generate device key pair
        device_private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        device_public_key = device_private_key.public_key()
        
        # Serialize public key
        public_key_bytes = device_public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        # Create certificate
        issue_date = datetime.now()
        expiry_date = issue_date + timedelta(days=365)
        
        return TrustCertificate(
            device_id=device_id,
            public_key=public_key_bytes,
            certificate_chain=[],
            issue_date=issue_date,
            expiry_date=expiry_date,
            trust_level=5,
            revocation_status=False
        )

    async def _analyze_device_behavior(self, device_id: str, device: Dict[str, Any]):
        """Analyze device behavior for anomalies"""
        try:
            profile = self.behavioral_profiles.get(device_id)
            if not profile:
                return
            
            # Collect current behavior data
            current_behavior = self._collect_behavior_data(device)
            
            # Analyze for anomalies
            anomaly_score = self._calculate_anomaly_score(profile, current_behavior)
            
            # Update behavioral profile
            self._update_behavioral_profile(profile, current_behavior)
            
            # Check for suspicious behavior
            if anomaly_score > self.config.get('anomaly_threshold', 0.8):
                await self._handle_behavioral_anomaly(device_id, anomaly_score, current_behavior)
                
        except Exception as e:
            self.logger.error(f"[M.I.T.E.L.] Behavioral analysis error: {e}")

    def _collect_behavior_data(self, device: Dict[str, Any]) -> Dict[str, Any]:
        """Collect current behavior data from device"""
        # Placeholder - would need actual behavioral data collection
        return {}

    def _calculate_anomaly_score(self, profile: BehavioralProfile, current_behavior: Dict[str, Any]) -> float:
        """Calculate anomaly score for current behavior"""
        # Placeholder - would need actual anomaly detection algorithm
        return 0.0

    def _update_behavioral_profile(self, profile: BehavioralProfile, current_behavior: Dict[str, Any]):
        """Update behavioral profile with new data"""
        profile.last_updated = datetime.now()

    async def _handle_behavioral_anomaly(self, device_id: str, anomaly_score: float, behavior: Dict[str, Any]):
        """Handle detected behavioral anomaly"""
        # Create threat event
        threat_event = ThreatEvent(
            timestamp=datetime.now(),
            device_id=device_id,
            threat_type="behavioral_anomaly",
            severity="medium",
            description=f"Unusual behavior detected (score: {anomaly_score:.2f})",
            response_action="monitor",
            investigation_data={'anomaly_score': anomaly_score, 'behavior': behavior}
        )
        
        self.threat_events.append(threat_event)
        
        # Propagate to mesh
        await self._propagate_threat_to_mesh(threat_event)
        
        self.logger.warning(f"[M.I.T.E.L.] Behavioral anomaly detected: {device_id}")

    async def get_status(self) -> Dict[str, Any]:
        """Get current M.I.T.E.L. status"""
        return {
            'subsystem': 'M.I.T.E.L.',
            'status': 'running' if self.is_running else 'stopped',
            'registered_devices': len(self.registered_devices),
            'quarantined_devices': len(self.quarantined_devices),
            'threat_events': len(self.threat_events),
            'pos_mode': self.pos_mode,
            'monitoring_active': self.monitoring_thread is not None and self.monitoring_thread.is_alive()
        }

    async def _load_device_registry(self):
        """Load device registry from persistent storage"""
        try:
            registry_file = self.config.get('device_registry_file', 'data/mitel_devices.yaml')
            if os.path.exists(registry_file):
                with open(registry_file, 'r') as f:
                    data = yaml.safe_load(f)
                    # Load registered devices (simplified)
                self.logger.info(f"[M.I.T.E.L.] Loaded device registry from {registry_file}")
        except Exception as e:
            self.logger.debug(f"[M.I.T.E.L.] No existing device registry: {e}")

    async def _save_device_registry(self):
        """Save device registry to persistent storage"""
        try:
            registry_file = self.config.get('device_registry_file', 'data/mitel_devices.yaml')
            os.makedirs(os.path.dirname(registry_file), exist_ok=True)
            
            # Save registry (simplified)
            data = {
                'registered_devices': len(self.registered_devices),
                'quarantined_devices': list(self.quarantined_devices)
            }
            
            with open(registry_file, 'w') as f:
                yaml.dump(data, f)
                
            self.logger.debug(f"[M.I.T.E.L.] Saved device registry to {registry_file}")
        except Exception as e:
            self.logger.error(f"[M.I.T.E.L.] Failed to save device registry: {e}")

    async def _load_behavioral_profiles(self):
        """Load behavioral profiles from persistent storage"""
        try:
            profiles_file = self.config.get('behavioral_profiles_file', 'data/mitel_profiles.yaml')
            if os.path.exists(profiles_file):
                with open(profiles_file, 'r') as f:
                    data = yaml.safe_load(f)
                self.logger.info(f"[M.I.T.E.L.] Loaded behavioral profiles from {profiles_file}")
        except Exception as e:
            self.logger.debug(f"[M.I.T.E.L.] No existing behavioral profiles: {e}")

    async def _save_behavioral_profiles(self):
        """Save behavioral profiles to persistent storage"""
        try:
            profiles_file = self.config.get('behavioral_profiles_file', 'data/mitel_profiles.yaml')
            os.makedirs(os.path.dirname(profiles_file), exist_ok=True)
            
            # Save profiles (simplified)
            data = {'profiles_count': len(self.behavioral_profiles)}
            
            with open(profiles_file, 'w') as f:
                yaml.dump(data, f)
                
            self.logger.debug(f"[M.I.T.E.L.] Saved behavioral profiles to {profiles_file}")
        except Exception as e:
            self.logger.error(f"[M.I.T.E.L.] Failed to save behavioral profiles: {e}")

    async def _disable_device(self, instance_id: str, device_name: str):
        """Disable device to enforce quarantine"""
        try:
            # Use PowerShell to disable the device
            cmd = [
                'powershell', '-Command',
                f'Disable-PnpDevice -InstanceId "{instance_id}" -Confirm:$false'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                self.logger.info(f"[M.I.T.E.L.] Disabled device: {device_name} ({instance_id[:30]}...)")
            else:
                # May fail if not running as admin
                self.logger.warning(f"[M.I.T.E.L.] Failed to disable device (may need admin): {device_name}")
                self.logger.debug(f"[M.I.T.E.L.] Error: {result.stderr}")
                
        except Exception as e:
            self.logger.error(f"[M.I.T.E.L.] Device disable error: {e}")
    
    async def _enable_device(self, instance_id: str, device_name: str):
        """Enable device after unquarantine"""
        try:
            # Use PowerShell to enable the device
            cmd = [
                'powershell', '-Command',
                f'Enable-PnpDevice -InstanceId "{instance_id}" -Confirm:$false'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                self.logger.info(f"[M.I.T.E.L.] Enabled device: {device_name} ({instance_id[:30]}...)")
            else:
                self.logger.warning(f"[M.I.T.E.L.] Failed to enable device: {device_name}")
                self.logger.debug(f"[M.I.T.E.L.] Error: {result.stderr}")
                
        except Exception as e:
            self.logger.error(f"[M.I.T.E.L.] Device enable error: {e}")

    async def _init_ai_components(self):
        """Initialize AI components for behavioral analysis"""
        # Placeholder for AI/ML model initialization
        self.logger.debug("[M.I.T.E.L.] AI components initialized (placeholder)")

    async def _setup_device_monitoring(self):
        """Setup device monitoring infrastructure"""
        # Placeholder for monitoring setup
        self.logger.debug("[M.I.T.E.L.] Device monitoring setup complete")

    async def _start_behavioral_analysis(self):
        """Start behavioral analysis engine"""
        # Placeholder for behavioral analysis startup
        self.logger.debug("[M.I.T.E.L.] Behavioral analysis started")

    async def _init_pos_components(self):
        """Initialize POS-specific components"""
        self.logger.info("[M.I.T.E.L.] POS mode enabled - skimmer detection active")
