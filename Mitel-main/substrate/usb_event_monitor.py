#!/usr/bin/env python3
"""
NEXUS USB Event Monitor
======================

Monitors USB events using udevadm for M.I.T.E.L. integration
Catches USB device add/remove events like Windows autoplay
"""

import subprocess
import threading
import time
import json
import logging
from typing import Dict, Any, Callable
from datetime import datetime

logger = logging.getLogger('NEXUS_USB_MONITOR')

class USBEventMonitor:
    """USB Event Monitor using udevadm"""
    
    def __init__(self, callback: Callable[[str, Dict[str, Any]], None]):
        self.callback = callback
        self.is_running = False
        self.monitor_thread = None
        
    def start_monitoring(self):
        """Start USB event monitoring"""
        if self.is_running:
            return
            
        self.is_running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("[USB_MONITOR] USB event monitoring started")
        
    def stop_monitoring(self):
        """Stop USB event monitoring"""
        self.is_running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("[USB_MONITOR] USB event monitoring stopped")
        
    def _monitor_loop(self):
        """Main monitoring loop using udevadm"""
        try:
            # Start udevadm monitor for USB events
            cmd = [
                'udevadm', 'monitor',
                '--subsystem-match=usb',
                '--subsystem-match=block',
                '--property',
                '--kernel'
            ]
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            
            logger.info("[USB_MONITOR] udevadm monitor started")
            
            while self.is_running:
                try:
                    line = process.stdout.readline()
                    if not line:
                        break
                        
                    line = line.strip()
                    if line:
                        self._parse_udev_event(line)
                        
                except Exception as e:
                    logger.error(f"[USB_MONITOR] Error processing event: {e}")
                    
        except Exception as e:
            logger.error(f"[USB_MONITOR] Monitor error: {e}")
            
    def _parse_udev_event(self, line: str):
        """Parse udev event line"""
        try:
            # Parse udev event format
            if line.startswith('KERNEL') and 'add' in line or 'remove' in line:
                parts = line.split()
                if len(parts) >= 3:
                    action = parts[2]  # add or remove
                    device_path = parts[1]
                    
                    # Get detailed device information
                    device_info = self._get_device_info(device_path)
                    
                    # Create event
                    event = {
                        'action': action,
                        'device_path': device_path,
                        'timestamp': datetime.now().isoformat(),
                        **device_info
                    }
                    
                    # Call callback
                    self.callback('usb_event', event)
                    logger.info(f"[USB_MONITOR] USB {action}: {device_path}")
                    
        except Exception as e:
            logger.error(f"[USB_MONITOR] Event parse error: {e}")
            
    def _get_device_info(self, device_path: str) -> Dict[str, Any]:
        """Get detailed device information"""
        device_info = {}
        
        try:
            # Use udevadm info to get device details
            cmd = ['udevadm', 'info', '--query=property', '--name', device_path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                for line in result.stdout.split('\n'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        device_info[key.lower()] = value
                        
        except Exception as e:
            logger.debug(f"[USB_MONITOR] Device info error: {e}")
            
        return device_info

class MITELUSBIntegration:
    """M.I.T.E.L. USB Integration with Event Monitor"""
    
    def __init__(self, mitel_subsystem):
        self.mitel = mitel_subsystem
        self.usb_monitor = USBEventMonitor(self._handle_usb_event)
        self.is_running = False
        
    def start(self):
        """Start USB monitoring integration"""
        try:
            self.usb_monitor.start_monitoring()
            self.is_running = True
            logger.info("[MITEL_USB] USB integration started")
            
        except Exception as e:
            logger.error(f"[MITEL_USB] Failed to start: {e}")
            
    def stop(self):
        """Stop USB monitoring integration"""
        try:
            self.usb_monitor.stop_monitoring()
            self.is_running = False
            logger.info("[MITEL_USB] USB integration stopped")
            
        except Exception as e:
            logger.error(f"[MITEL_USB] Failed to stop: {e}")
            
    def _handle_usb_event(self, event_type: str, event_data: Dict[str, Any]):
        """Handle USB events from monitor"""
        try:
            action = event_data.get('action', '')
            device_path = event_data.get('device_path', '')
            
            logger.info(f"[MITEL_USB] USB event: {action} - {device_path}")
            
            if action == 'add':
                self._handle_usb_add(event_data)
            elif action == 'remove':
                self._handle_usb_remove(event_data)
                
        except Exception as e:
            logger.error(f"[MITEL_USB] Event handling error: {e}")
            
    def _handle_usb_add(self, event_data: Dict[str, Any]):
        """Handle USB device addition"""
        try:
            # Convert to M.I.T.E.L. device format
            device = self._convert_to_mitel_device(event_data)
            
            if device:
                logger.info(f"[MITEL_USB] USB device added: {device.get('name', 'Unknown')}")
                
                # Trigger M.I.T.E.L. device processing
                # This would integrate with the existing M.I.T.E.L. device handling
                self.mitel._process_device_event(device)
                
        except Exception as e:
            logger.error(f"[MITEL_USB] USB add handling error: {e}")
            
    def _handle_usb_remove(self, event_data: Dict[str, Any]):
        """Handle USB device removal"""
        try:
            device_id = event_data.get('devname', '') or event_data.get('device_path', '')
            
            logger.info(f"[MITEL_USB] USB device removed: {device_id}")
            
            # Trigger M.I.T.E.L. device removal handling
            # This would integrate with existing M.I.T.E.L. removal logic
            
        except Exception as e:
            logger.error(f"[MITEL_USB] USB remove handling error: {e}")
            
    def _convert_to_mitel_device(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert udev event to M.I.T.E.L. device format"""
        try:
            device = {
                'device_id': event_data.get('devname', '') or event_data.get('device_path', ''),
                'name': event_data.get('id_model', '') or event_data.get('id_vendor', 'Unknown USB Device'),
                'device_type': 'storage' if 'block' in event_data.get('subsystem', '') else 'usb',
                'vendor_id': event_data.get('id_vendor_id', ''),
                'product_id': event_data.get('id_model_id', ''),
                'serial_number': event_data.get('id_serial_short', ''),
                'mac_address': '',
                'electrical_profile': {},
                'timing_characteristics': {},
                'timestamp': datetime.now().isoformat()
            }
            
            return device
            
        except Exception as e:
            logger.error(f"[MITEL_USB] Device conversion error: {e}")
            return None

# Installation helper
def install_udev_rules():
    """Install udev rules for USB monitoring"""
    try:
        import shutil
        
        # Copy udev rules to system directory
        src = "/home/kali/Desktop/MITEL/Mitel-main/config/udev/99-nexus-usb.rules"
        dst = "/etc/udev/rules.d/99-nexus-usb.rules"
        
        shutil.copy2(src, dst)
        
        # Reload udev rules
        subprocess.run(['udevadm', 'control', '--reload-rules'], check=True)
        
        logger.info("[USB_MONITOR] udev rules installed successfully")
        return True
        
    except Exception as e:
        logger.error(f"[USB_MONITOR] Failed to install udev rules: {e}")
        return False

if __name__ == "__main__":
    # Test USB monitoring
    logging.basicConfig(level=logging.INFO)
    
    def test_callback(event_type: str, event_data: Dict[str, Any]):
        print(f"Event: {event_type}")
        print(f"Data: {json.dumps(event_data, indent=2)}")
    
    monitor = USBEventMonitor(test_callback)
    monitor.start_monitoring()
    
    print("USB monitor started. Plug/unplug USB devices to test...")
    print("Press Ctrl+C to stop")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        monitor.stop_monitoring()
        print("USB monitor stopped")
