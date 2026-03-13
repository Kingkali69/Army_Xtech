#!/usr/bin/env python3
"""
UNIFIED CONTROL - Control Windows/Android from Linux
No more switching between Cursor instances
"""
import os
import sys
import json
import urllib.request
import base64

MASTER_IP = "192.168.1.116"
MASTER_PORT = 7890

def get_token():
    """Get mesh API token"""
    try:
        with open('MESH_API_TOKEN.txt', 'r') as f:
            for line in f:
                if line.startswith('TOKEN:'):
                    return line.split('TOKEN:')[1].strip()
            f.seek(0)
            return f.read().strip()
    except:
        return None

def execute_on_windows(command):
    """Execute command on Windows via mesh"""
    token = get_token()
    if not token:
        print("❌ No token")
        return None
    
    url = f"http://{MASTER_IP}:{MASTER_PORT}/mesh/execute"
    headers = {
        'X-Mesh-Token': token,
        'Content-Type': 'application/json'
    }
    data = {
        'platforms': 'windows',
        'command': command,
        'async': False
    }
    
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode('utf-8'),
            headers=headers
        )
        
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode('utf-8'))
            windows_result = result.get('results', {}).get('windows', {})
            return windows_result
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def push_file_to_windows(file_path, desktop_filename=None):
    """Push file to Windows Desktop"""
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False
    
    with open(file_path, 'rb') as f:
        file_content = f.read()
    
    file_data = base64.b64encode(file_content).decode('utf-8')
    
    if desktop_filename is None:
        desktop_filename = os.path.basename(file_path)
    
    token = get_token()
    if not token:
        print("❌ No token")
        return False
    
    url = f"http://{MASTER_IP}:{MASTER_PORT}/mesh/push_file"
    headers = {
        'X-Mesh-Token': token,
        'Content-Type': 'application/json'
    }
    data = {
        'platforms': 'windows',
        'file_path': desktop_filename,
        'file_data': file_data
    }
    
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode('utf-8'),
            headers=headers
        )
        
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode('utf-8'))
            windows_result = result.get('results', {}).get('windows', {})
            
            if windows_result.get('status') == 'success':
                print(f"✅ Pushed {desktop_filename} to Windows Desktop")
                return True
            else:
                print(f"❌ Failed: {windows_result.get('error', 'Unknown')}")
                return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def get_windows_status():
    """Get Windows node status"""
    token = get_token()
    if not token:
        return None
    
    url = f"http://{MASTER_IP}:{MASTER_PORT}/mesh/nodes"
    headers = {'X-Mesh-Token': token}
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode('utf-8'))
            nodes = result.get('nodes', [])
            
            for node in nodes:
                if node.get('platform', '').lower() == 'windows':
                    return node
            return None
    except:
        return None

def interactive_mode():
    """Interactive control mode"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║         UNIFIED CONTROL - Windows from Linux                ║
╚══════════════════════════════════════════════════════════════╝

Control Windows without switching Cursor instances.

Commands:
  exec <command>     - Execute command on Windows
  push <file>        - Push file to Windows Desktop
  status             - Check if Windows is connected
  help               - Show this help
  exit               - Exit

Example:
  exec dir C:\\Users\\kali\\Desktop
  push windows_launchers/OPEN_HUD.py OPEN_HUD.py
""")
    
    while True:
        try:
            cmd = input("\n[UNIFIED] > ").strip()
            
            if not cmd:
                continue
            
            if cmd == 'exit':
                break
            elif cmd == 'help':
                print("Commands: exec, push, status, help, exit")
            elif cmd == 'status':
                node = get_windows_status()
                if node:
                    print(f"✅ Windows connected: {node.get('ip')}:{node.get('port')}")
                else:
                    print("❌ Windows not connected")
            elif cmd.startswith('exec '):
                command = cmd[5:].strip()
                print(f"Executing on Windows: {command}")
                result = execute_on_windows(command)
                if result:
                    status = result.get('status', 'unknown')
                    output = result.get('output', '')
                    error = result.get('error', '')
                    if output:
                        print(output)
                    if error:
                        print(f"Error: {error}")
                else:
                    print("❌ Failed to execute")
            elif cmd.startswith('push '):
                parts = cmd[5:].strip().split()
                if len(parts) >= 1:
                    file_path = parts[0]
                    desktop_name = parts[1] if len(parts) > 1 else None
                    push_file_to_windows(file_path, desktop_name)
                else:
                    print("Usage: push <file_path> [desktop_filename]")
            else:
                print("Unknown command. Type 'help' for commands.")
                
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Command line mode
        if sys.argv[1] == 'exec' and len(sys.argv) > 2:
            command = ' '.join(sys.argv[2:])
            result = execute_on_windows(command)
            if result:
                print(result.get('output', ''))
                if result.get('error'):
                    print(f"Error: {result.get('error')}")
        elif sys.argv[1] == 'push' and len(sys.argv) > 2:
            file_path = sys.argv[2]
            desktop_name = sys.argv[3] if len(sys.argv) > 3 else None
            push_file_to_windows(file_path, desktop_name)
        elif sys.argv[1] == 'status':
            node = get_windows_status()
            if node:
                print(f"✅ Windows: {node.get('ip')}:{node.get('port')}")
            else:
                print("❌ Windows not connected")
        else:
            print("Usage: unified_control.py [exec|push|status] [args...]")
    else:
        # Interactive mode
        interactive_mode()

