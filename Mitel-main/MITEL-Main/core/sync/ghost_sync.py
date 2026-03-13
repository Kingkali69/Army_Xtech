#!/usr/bin/env python3
"""
GHOST SYNC - Reliable file sync using OS tools (rsync/robocopy)
No more janky HTTP sync. Uses battle-tested tools.

Features:
- rsync for Linux/Android
- robocopy for Windows  
- SSH tunnels for encryption
- Auto-watch and push
- Works across all platforms
"""

import os
import sys
import subprocess
import threading
import time
import json
import socket
import hashlib
from pathlib import Path
from typing import Dict, List, Optional

class GhostSync:
    """Cross-platform file sync using rsync/robocopy over SSH"""
    
    def __init__(self, project_dir: str = None):
        self.project_dir = project_dir or os.path.dirname(os.path.abspath(__file__))
        self.nodes: Dict[str, dict] = {}  # {node_id: {ip, port, platform, ssh_user}}
        self.platform = self._detect_platform()
        self.watching = False
        self.watch_thread = None
        
        # Files to sync (core engine files)
        self.sync_files = [
            '*.py',  # All Python files
            '*.html',
            '*.js', 
            '*.css',
            '*.json',
            '*.md',
            '*.txt',
            '*.sh',
            '*.bat'
        ]
        
        # Exclude patterns
        self.exclude = [
            '__pycache__',
            '*.pyc',
            '.git',
            '.buildozer',
            'backup*',
            '*.backup',
            'cache',
            '*.log',
            'build',
            'dist'
        ]
        
        print(f"[GHOST SYNC] Initialized on {self.platform}")
        print(f"[GHOST SYNC] Project: {self.project_dir}")
    
    def _detect_platform(self) -> str:
        """Detect current platform"""
        if sys.platform == 'win32':
            return 'windows'
        elif 'android' in str(os.environ.get('PREFIX', '')).lower():
            return 'android'
        else:
            return 'linux'
    
    def add_node(self, node_id: str, ip: str, platform: str, 
                 ssh_user: str = None, ssh_port: int = 22,
                 remote_path: str = None):
        """Add a node to sync to"""
        self.nodes[node_id] = {
            'ip': ip,
            'platform': platform,
            'ssh_user': ssh_user or ('kali' if platform == 'linux' else 'user'),
            'ssh_port': ssh_port,
            'remote_path': remote_path or self._default_remote_path(platform)
        }
        print(f"[GHOST SYNC] Added node: {node_id} ({platform}) at {ip}")
    
    def _default_remote_path(self, platform: str) -> str:
        """Get default remote path for platform"""
        if platform == 'windows':
            return '/c/Users/kali/Desktop/Omni/N.O.Q.C.G.O.E-main'
        elif platform == 'android':
            return '/data/data/com.termux/files/home/ghostops'
        else:
            return '/home/kali/ghostops'
    
    def _build_rsync_cmd(self, node: dict) -> List[str]:
        """Build rsync command for a node"""
        cmd = ['rsync', '-avz', '--delete', '--progress']
        
        # Add excludes
        for exc in self.exclude:
            cmd.extend(['--exclude', exc])
        
        # Source (trailing slash = contents only)
        cmd.append(f"{self.project_dir}/")
        
        # Destination
        if node['ssh_user']:
            dest = f"{node['ssh_user']}@{node['ip']}:{node['remote_path']}/"
        else:
            dest = f"{node['ip']}:{node['remote_path']}/"
        
        # SSH port if not default
        if node['ssh_port'] != 22:
            cmd.extend(['-e', f"ssh -p {node['ssh_port']}"])
        
        cmd.append(dest)
        return cmd
    
    def _build_robocopy_cmd(self, node: dict) -> List[str]:
        """Build robocopy command for Windows→Windows sync"""
        # Convert remote path to UNC
        remote_unc = f"\\\\{node['ip']}\\{node['remote_path'].replace('/', '\\')}"
        
        cmd = [
            'robocopy',
            self.project_dir,
            remote_unc,
            '/MIR',  # Mirror (delete extra files on dest)
            '/Z',    # Restartable mode
            '/W:1',  # Wait 1 second between retries
            '/R:3',  # Retry 3 times
        ]
        
        # Add excludes
        for exc in self.exclude:
            cmd.extend(['/XD', exc])
        
        return cmd
    
    def push_to_node(self, node_id: str) -> bool:
        """Push files to a specific node"""
        if node_id not in self.nodes:
            print(f"[GHOST SYNC] [ERROR] Unknown node: {node_id}")
            return False
        
        node = self.nodes[node_id]
        print(f"[GHOST SYNC] >> Pushing to {node_id} ({node['ip']})...")
        
        try:
            # Choose sync method based on platforms
            if self.platform == 'windows' and node['platform'] == 'windows':
                # Windows to Windows: use robocopy
                cmd = self._build_robocopy_cmd(node)
            else:
                # Everything else: use rsync over SSH
                cmd = self._build_rsync_cmd(node)
            
            print(f"[GHOST SYNC] Running: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0 or (self.platform == 'windows' and result.returncode < 8):
                print(f"[GHOST SYNC] ✅ Push to {node_id} complete")
                return True
            else:
                print(f"[GHOST SYNC] [ERROR] Push to {node_id} failed:")
                print(result.stderr)
                return False
                
        except subprocess.TimeoutExpired:
            print(f"[GHOST SYNC] [ERROR] Push to {node_id} timed out")
            return False
        except FileNotFoundError as e:
            print(f"[GHOST SYNC] [ERROR] Tool not found: {e}")
            print("[GHOST SYNC] Make sure rsync (Linux/Android) or robocopy (Windows) is installed")
            return False
        except Exception as e:
            print(f"[GHOST SYNC] [ERROR] Push error: {e}")
            return False
    
    def push_all(self) -> Dict[str, bool]:
        """Push to all nodes"""
        results = {}
        print(f"[GHOST SYNC] >> Pushing to {len(self.nodes)} node(s)...")
        
        for node_id in self.nodes:
            results[node_id] = self.push_to_node(node_id)
        
        success = sum(1 for r in results.values() if r)
        failed = len(results) - success
        print(f"[GHOST SYNC] Complete: {success} succeeded, {failed} failed")
        
        return results
    
    def watch_and_push(self, debounce_seconds: float = 2.0):
        """Watch for file changes and auto-push"""
        if self.platform == 'windows':
            self._watch_windows(debounce_seconds)
        else:
            self._watch_linux(debounce_seconds)
    
    def _watch_linux(self, debounce: float):
        """Watch using inotifywait (Linux/Android)"""
        try:
            # Check if inotifywait is available
            subprocess.run(['which', 'inotifywait'], check=True, capture_output=True)
        except:
            print("[GHOST SYNC] ⚠️ inotifywait not found. Install: apt install inotify-tools")
            return
        
        print(f"[GHOST SYNC] [WATCH] Watching {self.project_dir} for changes...")
        self.watching = True
        
        last_push = 0
        
        cmd = [
            'inotifywait', '-m', '-r',
            '-e', 'modify,create,delete,move',
            '--exclude', '(__pycache__|\.git|\.pyc|backup)',
            self.project_dir
        ]
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        try:
            for line in process.stdout:
                if not self.watching:
                    break
                
                # Debounce - don't push more than once per N seconds
                now = time.time()
                if now - last_push >= debounce:
                    print(f"[GHOST SYNC] [CHANGE] Change detected: {line.strip()}")
                    self.push_all()
                    last_push = time.time()
        except KeyboardInterrupt:
            pass
        finally:
            process.terminate()
            self.watching = False
    
    def _watch_windows(self, debounce: float):
        """Watch using Python watchdog or polling (Windows)"""
        try:
            from watchdog.observers import Observer
            from watchdog.events import FileSystemEventHandler
            
            class ChangeHandler(FileSystemEventHandler):
                def __init__(handler_self):
                    handler_self.last_push = 0
                    handler_self.sync = self
                
                def on_any_event(handler_self, event):
                    # Skip excluded patterns
                    for exc in self.exclude:
                        if exc.replace('*', '') in event.src_path:
                            return
                    
                    now = time.time()
                    if now - handler_self.last_push >= debounce:
                        print(f"[GHOST SYNC] [CHANGE] Change: {event.src_path}")
                        handler_self.sync.push_all()
                        handler_self.last_push = time.time()
            
            observer = Observer()
            observer.schedule(ChangeHandler(), self.project_dir, recursive=True)
            observer.start()
            
            print(f"[GHOST SYNC] [WATCH] Watching {self.project_dir} for changes...")
            self.watching = True
            
            try:
                while self.watching:
                    time.sleep(1)
            except KeyboardInterrupt:
                pass
            finally:
                observer.stop()
                observer.join()
                
        except ImportError:
            print("[GHOST SYNC] ⚠️ watchdog not installed. Using polling...")
            self._watch_polling(debounce)
    
    def _watch_polling(self, debounce: float):
        """Fallback: poll for changes"""
        print(f"[GHOST SYNC] [WATCH] Watching {self.project_dir} (polling mode)...")
        self.watching = True
        
        def get_dir_hash():
            """Get hash of all file mtimes"""
            hashes = []
            for root, dirs, files in os.walk(self.project_dir):
                # Skip excluded dirs
                dirs[:] = [d for d in dirs if not any(
                    d.startswith(exc.replace('*', '')) for exc in self.exclude
                )]
                for f in files:
                    if any(f.endswith(exc.replace('*', '')) for exc in self.exclude):
                        continue
                    try:
                        path = os.path.join(root, f)
                        hashes.append(f"{path}:{os.path.getmtime(path)}")
                    except:
                        pass
            return hashlib.md5('|'.join(sorted(hashes)).encode()).hexdigest()
        
        last_hash = get_dir_hash()
        last_push = time.time()
        
        try:
            while self.watching:
                time.sleep(debounce)
                current_hash = get_dir_hash()
                
                if current_hash != last_hash:
                    print("[GHOST SYNC] [CHANGE] Changes detected")
                    self.push_all()
                    last_hash = current_hash
                    last_push = time.time()
        except KeyboardInterrupt:
            pass
        finally:
            self.watching = False
    
    def stop_watching(self):
        """Stop watching for changes"""
        self.watching = False
        print("[GHOST SYNC] [WATCH] Stopped watching")


class GhostTunnel:
    """
    Encrypted P2P tunnels for secure communication
    Like WhatsApp - end-to-end encrypted
    """
    
    def __init__(self, local_port: int = 9000):
        self.local_port = local_port
        self.tunnels: Dict[str, dict] = {}  # Active tunnels
        self.encryption_key = None
        
    def create_tunnel(self, peer_ip: str, peer_port: int = 9000) -> bool:
        """Create encrypted tunnel to peer using SSH"""
        tunnel_id = f"{peer_ip}:{peer_port}"
        
        # Use SSH tunnel for encryption
        cmd = [
            'ssh', '-N', '-L',
            f"{self.local_port}:localhost:{peer_port}",
            f"user@{peer_ip}"
        ]
        
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            self.tunnels[tunnel_id] = {
                'process': process,
                'peer_ip': peer_ip,
                'peer_port': peer_port,
                'local_port': self.local_port
            }
            
            print(f"[TUNNEL] 🔒 Encrypted tunnel to {tunnel_id} established")
            return True
            
        except Exception as e:
            print(f"[TUNNEL] [ERROR] Failed to create tunnel: {e}")
            return False
    
    def close_tunnel(self, peer_ip: str, peer_port: int = 9000):
        """Close tunnel to peer"""
        tunnel_id = f"{peer_ip}:{peer_port}"
        
        if tunnel_id in self.tunnels:
            self.tunnels[tunnel_id]['process'].terminate()
            del self.tunnels[tunnel_id]
            print(f"[TUNNEL] 🔓 Tunnel to {tunnel_id} closed")


# CLI interface
if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Ghost Sync - Cross-platform file sync')
    parser.add_argument('command', choices=['push', 'watch', 'add-node', 'list'],
                       help='Command to run')
    parser.add_argument('--node', help='Node ID')
    parser.add_argument('--ip', help='Node IP address')
    parser.add_argument('--platform', choices=['linux', 'windows', 'android'],
                       help='Node platform')
    parser.add_argument('--user', help='SSH username')
    parser.add_argument('--path', help='Remote path')
    
    args = parser.parse_args()
    
    sync = GhostSync()
    
    # Load saved nodes
    nodes_file = os.path.join(sync.project_dir, '.ghost_nodes.json')
    if os.path.exists(nodes_file):
        with open(nodes_file, 'r') as f:
            saved_nodes = json.load(f)
            for node_id, node_info in saved_nodes.items():
                sync.nodes[node_id] = node_info
    
    if args.command == 'add-node':
        if not args.node or not args.ip or not args.platform:
            print("Usage: ghost_sync.py add-node --node NAME --ip IP --platform PLATFORM")
            sys.exit(1)
        
        sync.add_node(
            args.node, args.ip, args.platform,
            ssh_user=args.user,
            remote_path=args.path
        )
        
        # Save nodes
        with open(nodes_file, 'w') as f:
            json.dump(sync.nodes, f, indent=2)
        
    elif args.command == 'list':
        if not sync.nodes:
            print("No nodes configured. Add with: ghost_sync.py add-node ...")
        else:
            print("Configured nodes:")
            for node_id, info in sync.nodes.items():
                print(f"  {node_id}: {info['ip']} ({info['platform']})")
    
    elif args.command == 'push':
        if not sync.nodes:
            print("No nodes configured. Add with: ghost_sync.py add-node ...")
            sys.exit(1)
        
        if args.node:
            sync.push_to_node(args.node)
        else:
            sync.push_all()
    
    elif args.command == 'watch':
        if not sync.nodes:
            print("No nodes configured. Add with: ghost_sync.py add-node ...")
            sys.exit(1)
        
        sync.watch_and_push()

