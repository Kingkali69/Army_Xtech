#!/usr/bin/env python3
"""Quick test to check /api/status endpoint"""
import time
import requests
import json

print("Waiting 5 seconds for web console to start...")
time.sleep(5)

try:
    print("Fetching http://127.0.0.1:8888/api/status...")
    r = requests.get('http://127.0.0.1:8888/api/status', timeout=5)
    data = r.json()
    
    print("\n=== API STATUS RESPONSE ===")
    print(json.dumps(data, indent=2))
    
    print(f"\n=== PEER COUNT: {len(data.get('peers', []))} ===")
    
    if data.get('peers'):
        print("\n=== PEERS FOUND ===")
        for peer in data['peers']:
            print(f"  - {peer['node_id'][:16]}... @ {peer['ip']}:{peer['port']} ({peer['platform']})")
    else:
        print("\n=== NO PEERS FOUND ===")
        print("Discovery is running but peers dict is empty")
        
except Exception as e:
    print(f"\nERROR: {e}")
