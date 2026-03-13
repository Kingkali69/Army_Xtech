import requests
import json

# Test POST endpoint directly
url = 'http://localhost:8888/api/mitel/device/action'
data = {
    'device_id': 'c82ff29e66539639',
    'action': 'unquarantine'
}

print(f"Testing POST to {url}")
print(f"Data: {data}")

try:
    response = requests.post(url, json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
