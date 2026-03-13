#!/usr/bin/env python3
"""
Simple USB Test - No container, no console, just USB detection
"""

import sys
import os
sys.path.append('/home/kali/Desktop/MITEL/Mitel-main')

from substrate.mitel_subsystem import MITELSubsystem

def test_usb_detection():
    print("🔌 Testing USB Detection Only...")
    print("=" * 50)
    
    # Simple config
    config = {'zero_trust': True, 'quarantine_unknown': True}
    
    try:
        # Initialize M.I.T.E.L.
        mitel = MITELSubsystem(config)
        print("✅ M.I.T.E.L. initialized")
        
        # Scan devices
        devices = mitel._scan_connected_devices()
        print(f"📱 Found {len(devices)} devices:")
        
        storage_devices = []
        for device in devices:
            device_type = device.get('device_type', 'unknown')
            name = device.get('name', 'Unknown')
            print(f"  - {name} ({device_type})")
            
            if device_type == 'storage':
                storage_devices.append(device)
        
        print(f"\n🚀 STORAGE DEVICES: {len(storage_devices)}")
        for device in storage_devices:
            print(f"  📁 {device.get('name', 'Unknown')}")
            print(f"     Device ID: {device.get('device_id', 'N/A')}")
            print(f"     Size: {device.get('size', 'N/A')}")
        
        return len(storage_devices) > 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_usb_detection()
    if success:
        print("\n✅ USB Detection Working!")
    else:
        print("\n❌ No USB storage devices found")
    
    print("\n🔌 Try plugging/unplugging USB devices and run again")
