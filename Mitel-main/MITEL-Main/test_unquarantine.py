import requests
import json

# Get device list
print("=" * 60)
print("GETTING DEVICE LIST...")
print("=" * 60)

response = requests.get('http://192.168.1.239:8888/api/mitel/devices')
data = response.json()

print(f"Total devices: {data['total']}")
print(f"Quarantined: {data['quarantined']}")
print(f"Trusted: {data['trusted']}")
print()

if data['devices']:
    first_device = data['devices'][0]
    device_id = first_device['device_id']
    device_name = first_device['name']
    device_status = first_device['trust_status']
    
    print(f"First device: {device_name}")
    print(f"Device ID: {device_id}")
    print(f"Status: {device_status}")
    print()
    
    if device_status == 'quarantined':
        print("=" * 60)
        print("UNQUARANTINING DEVICE...")
        print("=" * 60)
        
        unquarantine_response = requests.post(
            'http://192.168.1.239:8888/api/mitel/device/action',
            json={'device_id': device_id, 'action': 'unquarantine'}
        )
        
        print(f"Response status: {unquarantine_response.status_code}")
        print(f"Response: {unquarantine_response.text}")
        print()
        
        # Check device list again
        print("=" * 60)
        print("CHECKING DEVICE LIST AFTER UNQUARANTINE...")
        print("=" * 60)
        
        response2 = requests.get('http://192.168.1.239:8888/api/mitel/devices')
        data2 = response2.json()
        
        print(f"Quarantined: {data2['quarantined']}")
        print(f"Trusted: {data2['trusted']}")
        print()
        
        # Find the device we just unquarantined
        for device in data2['devices']:
            if device['device_id'] == device_id:
                print(f"Device {device_name}:")
                print(f"  Status: {device['trust_status']}")
                print(f"  Expected: trusted")
                print(f"  SUCCESS: {device['trust_status'] == 'trusted'}")
                break
    else:
        print(f"Device is already {device_status}, not quarantined")
else:
    print("No devices found")
