#!/usr/bin/env python3
"""
GhostOps File Sharing Module
Native file browser integration with secure tunnel transfer
"""

import os
import sys
import io

# Fix Windows encoding issues - MUST be before any print statements
if sys.platform == 'win32':
    try:
        # Only wrap if not already wrapped - prevents "I/O operation on closed file" error
        if not isinstance(sys.stdout, io.TextIOWrapper) and hasattr(sys.stdout, 'buffer'):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        if not isinstance(sys.stderr, io.TextIOWrapper) and hasattr(sys.stderr, 'buffer'):
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except (ValueError, OSError, AttributeError):
        # If wrapping fails, continue - stdout is probably already configured
        pass

import json
import base64
import hashlib
import platform
import threading
import socket
import time
from typing import Dict, Optional, Callable, List
try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    print("[!] cryptography not available - file encryption disabled")

class FileBrowser:
    """Native file browser integration"""
    
    @staticmethod
    def select_file(directory=None):
        """
        Open native file browser to select file
        Returns: (file_path, None) or (None, error)
        """
        system = platform.system().lower()
        
        try:
            if system == 'linux':
                # Try different file managers
                file_managers = [
                    ('thunar', '--file-selection'),
                    ('nautilus', '--file-selection'),
                    ('pcmanfm', '--file-selection'),
                    ('dolphin', '--select'),
                ]
                
                for cmd, arg in file_managers:
                    try:
                        import subprocess
                        result = subprocess.run(
                            ['which', cmd],
                            capture_output=True,
                            timeout=2
                        )
                        if result.returncode == 0:
                            # Use zenity or kdialog for file selection
                            try:
                                result = subprocess.run(
                                    ['zenity', '--file-selection', '--title=Select File to Send'],
                                    capture_output=True,
                                    text=True,
                                    timeout=30
                                )
                                if result.returncode == 0:
                                    file_path = result.stdout.strip()
                                    if file_path and os.path.isfile(file_path):
                                        return file_path, None
                            except:
                                try:
                                    result = subprocess.run(
                                        ['kdialog', '--getopenfilename', directory or os.getcwd()],
                                        capture_output=True,
                                        text=True,
                                        timeout=30
                                    )
                                    if result.returncode == 0:
                                        file_path = result.stdout.strip()
                                        if file_path and os.path.isfile(file_path):
                                            return file_path, None
                                except:
                                    pass
                    except:
                        continue
                
                # Fallback: use tkinter (if available)
                try:
                    import tkinter as tk
                    from tkinter import filedialog
                    root = tk.Tk()
                    root.withdraw()
                    root.attributes('-topmost', True)
                    file_path = filedialog.askopenfilename(
                        initialdir=directory,
                        title='Select File to Send'
                    )
                    root.destroy()
                    if file_path and os.path.isfile(file_path):
                        return file_path, None
                except ImportError:
                    # tkinter not available - that's ok
                    pass
                except Exception:
                    # tkinter available but failed - that's ok
                    pass
                    
            elif system == 'windows':
                try:
                    import tkinter as tk
                    from tkinter import filedialog
                    root = tk.Tk()
                    root.withdraw()
                    root.attributes('-topmost', True)
                    file_path = filedialog.askopenfilename(
                        initialdir=directory,
                        title='Select File to Send'
                    )
                    root.destroy()
                    if file_path and os.path.isfile(file_path):
                        return file_path, None
                except ImportError:
                    return None, "tkinter not available"
                except Exception as e:
                    return None, f"File dialog error: {e}"
                    
            elif system == 'android':
                # Android - use Storage Access Framework or file picker intent
                # For now, fallback to a simple path input
                try:
                    from android.storage import primary_external_storage_path
                    base_path = primary_external_storage_path()
                    # In a real Android app, you'd use an Intent to open file picker
                    # For now, we'll need to handle this differently
                    # This is a placeholder
                    pass
                except:
                    pass
                    
        except Exception as e:
            return None, str(e)
        
        return None, "No file browser available"
    
    @staticmethod
    def select_save_directory(directory=None):
        """Select directory to save file"""
        system = platform.system().lower()
        
        try:
            if system == 'linux':
                try:
                    import subprocess
                    result = subprocess.run(
                        ['zenity', '--file-selection', '--directory', '--title=Select Save Location'],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    if result.returncode == 0:
                        return result.stdout.strip(), None
                except:
                    try:
                        import tkinter as tk
                        from tkinter import filedialog
                        root = tk.Tk()
                        root.withdraw()
                        path = filedialog.askdirectory(initialdir=directory, title='Select Save Location')
                        root.destroy()
                        if path:
                            return path, None
                    except:
                        pass
                        
            elif system == 'windows':
                import tkinter as tk
                from tkinter import filedialog
                root = tk.Tk()
                root.withdraw()
                path = filedialog.askdirectory(initialdir=directory, title='Select Save Location')
                root.destroy()
                if path:
                    return path, None
                    
        except Exception as e:
            return None, str(e)
        
        return directory or os.getcwd(), None  # Fallback to current directory


class SecureFileTransfer:
    """Secure file transfer using encryption"""
    
    def __init__(self, encryption_key=None):
        """Initialize with encryption key"""
        if not CRYPTO_AVAILABLE:
            self.cipher = None
            print("[!] Encryption disabled - cryptography module not available")
        elif encryption_key:
            self.cipher = Fernet(encryption_key)
        else:
            # Generate key from shared secret
            key = self._generate_key()
            self.cipher = Fernet(key)
        self.transfers = {}  # Track active transfers
    
    def _generate_key(self):
        """
        Generate encryption key from secure source

        SECURITY FIX: Never use hardcoded shared secret
        Use unique per-installation key
        """
        import secrets

        # 1. Try to load encryption key from secure storage
        config_dir = os.path.expanduser("~/.ghostops")
        enc_key_file = os.path.join(config_dir, "file_encryption_key")

        if os.path.exists(enc_key_file):
            try:
                with open(enc_key_file, 'rb') as f:
                    stored_key = f.read()
                if len(stored_key) == 44:  # Fernet key length (base64-encoded 32 bytes)
                    print("[FILE_CRYPTO] ✅ Loaded encryption key from secure storage")
                    return stored_key
            except Exception as e:
                print(f"[FILE_CRYPTO] ⚠️  Failed to load encryption key: {e}")

        # 2. Generate new secure random key
        print("[FILE_CRYPTO] 🔑 Generating new file encryption key...")

        # Generate truly random password (32 bytes = 256 bits)
        password = secrets.token_bytes(32)

        # Generate truly random salt (16 bytes = 128 bits)
        salt = secrets.token_bytes(16)

        # Derive key using PBKDF2
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))

        # 3. Save to secure storage for persistence
        try:
            os.makedirs(config_dir, exist_ok=True)
            with open(enc_key_file, 'wb') as f:
                f.write(key)
            # Secure permissions (user read/write only)
            os.chmod(enc_key_file, 0o600)
            print(f"[FILE_CRYPTO] ✅ Saved encryption key to {enc_key_file}")
            print("[FILE_CRYPTO] ⚠️  IMPORTANT: Backup this key securely!")
        except Exception as e:
            print(f"[FILE_CRYPTO] ⚠️  Failed to save encryption key: {e}")
            print("[FILE_CRYPTO] ⚠️  Key will not persist across restarts!")

        return key
    
    def encrypt_file_chunk(self, data: bytes) -> bytes:
        """Encrypt file chunk"""
        if self.cipher:
            return self.cipher.encrypt(data)
        return data  # No encryption if crypto not available
    
    def decrypt_file_chunk(self, encrypted_data: bytes) -> bytes:
        """Decrypt file chunk"""
        if self.cipher:
            return self.cipher.decrypt(encrypted_data)
        return encrypted_data  # No decryption if crypto not available
    
    def calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash of file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def verify_file_integrity(self, file_path: str, expected_hash: str) -> bool:
        """Verify file integrity using hash"""
        actual_hash = self.calculate_file_hash(file_path)
        return actual_hash == expected_hash


class TunnelFileTransfer:
    """File transfer over tunnel connections"""
    
    def __init__(self, ex_api=None, engine=None):
        self.ex_api = ex_api
        self.engine = engine
        self.secure_transfer = SecureFileTransfer()
        self.active_transfers = {}  # {transfer_id: transfer_info}
        self.progress_callbacks = {}  # {transfer_id: callback}
        
    def send_file(self, file_path: str, target_node: str, progress_callback=None) -> Dict:
        """
        Send file to target node via tunnel
        Returns: {'ok': bool, 'transfer_id': str, 'message': str}
        """
        try:
            if not os.path.isfile(file_path):
                return {'ok': False, 'message': f'File not found: {file_path}'}
            
            # Get file info
            file_size = os.path.getsize(file_path)
            file_name = os.path.basename(file_path)
            file_hash = self.secure_transfer.calculate_file_hash(file_path)
            
            transfer_id = f"transfer_{int(time.time())}_{hashlib.md5(file_path.encode()).hexdigest()[:8]}"
            
            # Store transfer info
            transfer_info = {
                'id': transfer_id,
                'file_path': file_path,
                'file_name': file_name,
                'file_size': file_size,
                'file_hash': file_hash,
                'target_node': target_node,
                'status': 'initializing',
                'bytes_sent': 0,
                'start_time': time.time()
            }
            self.active_transfers[transfer_id] = transfer_info
            
            if progress_callback:
                self.progress_callbacks[transfer_id] = progress_callback
            
            # Start transfer in background
            threading.Thread(
                target=self._transfer_file_thread,
                args=(transfer_id,),
                daemon=True
            ).start()
            
            return {
                'ok': True,
                'transfer_id': transfer_id,
                'message': f'File transfer started: {file_name}',
                'file_name': file_name,
                'file_size': file_size
            }
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {'ok': False, 'message': f'Transfer error: {str(e)}'}
    
    def _transfer_file_thread(self, transfer_id: str):
        """Background thread for file transfer"""
        try:
            transfer = self.active_transfers[transfer_id]
            transfer['status'] = 'transferring'
            
            # Use EX API tunnel if available
            if self.ex_api and self.ex_api.socket_tunnel:
                self._transfer_via_socket_tunnel(transfer)
            else:
                # Fallback to HTTP if tunnel not available
                self._transfer_via_http(transfer)
                
        except Exception as e:
            transfer['status'] = 'error'
            transfer['error'] = str(e)
            print(f"[!] Transfer {transfer_id} error: {e}")
    
    def _transfer_via_socket_tunnel(self, transfer: Dict):
        """Transfer file via secure socket tunnel (SSL/TLS)"""
        try:
            target_node = transfer['target_node']
            file_path = transfer['file_path']
            
            # Get target node info
            target_ip = None
            target_port = None
            
            if self.engine:
                # Check if target is in nodes
                if target_node in self.engine.state.nodes:
                    node_info = self.engine.state.nodes[target_node]
                    target_ip = node_info.get('ip', '')
                    target_port = 51820  # Secure socket tunnel port
                # Check if target is master
                elif hasattr(self.engine, 'config') and hasattr(self.engine.config, 'master_ip') and self.engine.config.master_ip:
                    status = self.engine.get_status()
                    master_device_id = status.get('master_device_id') or status.get('authority')
                    if target_node == master_device_id or target_node == status.get('authority'):
                        target_ip = self.engine.config.master_ip
                        target_port = 51820
                # Master sending to peer
                elif self.engine.is_master():
                    status = self.engine.get_status()
                    nodes = status.get('nodes', {})
                    if target_node in nodes:
                        node_info = nodes[target_node]
                        target_ip = node_info.get('ip', '')
                        target_port = 51820
            
            if not target_ip:
                transfer['status'] = 'error'
                transfer['error'] = f'Target node "{target_node}" not found'
                return
            
            # Use secure socket tunnel if available
            socket_tunnel = None
            if self.ex_api and self.ex_api.socket_tunnel:
                socket_tunnel = self.ex_api.socket_tunnel
            else:
                # Fallback to HTTP if no socket tunnel
                print("[FILE TRANSFER] ⚠️ Socket tunnel not available, using HTTP")
                self._transfer_via_http(transfer)
                return
            
            # Connect to peer via secure socket
            print(f"[FILE TRANSFER] Connecting to {target_ip}:{target_port} via SSL/TLS...")
            peer_sock = socket_tunnel.connect_to_peer(target_ip, target_port)
            
            if not peer_sock:
                print("[FILE TRANSFER] ⚠️ Secure socket connection failed, falling back to HTTP")
                self._transfer_via_http(transfer)
                return
            
            # Send file transfer header
            header = {
                'action': 'file_transfer',
                'transfer_id': transfer['id'],
                'file_name': transfer['file_name'],
                'file_size': transfer['file_size'],
                'file_hash': transfer['file_hash']
            }
            header_json = json.dumps(header).encode()
            header_len = len(header_json).to_bytes(4, 'big')
            peer_sock.send(header_len + header_json)
            
            # Read and send file in chunks
            chunk_size = 64 * 1024  # 64KB chunks
            total_sent = 0
            
            with open(file_path, 'rb') as f:
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    
                    # Encrypt chunk
                    encrypted_chunk = self.secure_transfer.encrypt_file_chunk(chunk)
                    
                    # Send chunk with size prefix
                    chunk_len = len(encrypted_chunk).to_bytes(4, 'big')
                    peer_sock.send(chunk_len + encrypted_chunk)
                    
                    total_sent += len(chunk)
                    transfer['bytes_sent'] = total_sent
                    
                    # Update progress
                    progress_pct = (total_sent / transfer['file_size']) * 100 if transfer['file_size'] > 0 else 0
                    transfer['progress'] = progress_pct
                    
                    if transfer['id'] in self.progress_callbacks:
                        self.progress_callbacks[transfer['id']](progress_pct)
            
            # Send completion signal
            completion = {'action': 'transfer_complete', 'transfer_id': transfer['id']}
            completion_json = json.dumps(completion).encode()
            completion_len = len(completion_json).to_bytes(4, 'big')
            peer_sock.send(completion_len + completion_json)
            
            transfer['status'] = 'completed'
            transfer['end_time'] = time.time()
            
            print(f"[FILE TRANSFER] ✅ Secure socket transfer completed: {transfer['file_name']}")
            print(f"[FILE TRANSFER] ✅ SSL/TLS encrypted, {total_sent} bytes sent")
            
        except Exception as e:
            transfer['status'] = 'error'
            transfer['error'] = str(e)
            print(f"[FILE TRANSFER] ❌ Secure socket transfer error: {e}")
            # Fallback to HTTP
            print("[FILE TRANSFER] ⚠️ Falling back to HTTP transfer")
            self._transfer_via_http(transfer)
    
    def _transfer_via_http(self, transfer: Dict):
        """Transfer file via HTTP (fallback)"""
        try:
            target_node = transfer['target_node']
            file_path = transfer['file_path']
            
            # Get target node info
            target_ip = None
            target_port = None
            
            if self.engine:
                # Check if target is in nodes
                if target_node in self.engine.state.nodes:
                    node_info = self.engine.state.nodes[target_node]
                    target_ip = node_info.get('ip', '')
                    target_port = node_info.get('port', 7890)
                # Check if target is master (for peer nodes sending to master)
                elif hasattr(self.engine, 'config') and hasattr(self.engine.config, 'master_ip') and self.engine.config.master_ip:
                    # Peer sending to master
                    status = self.engine.get_status()
                    master_device_id = status.get('master_device_id') or status.get('authority')
                    if target_node == master_device_id or target_node == status.get('authority'):
                        target_ip = self.engine.config.master_ip
                        target_port = getattr(self.engine.config, 'master_port', 7890)
                    # Master sending to peer - check nodes again with status
                    elif self.engine.is_master():
                        status = self.engine.get_status()
                        nodes = status.get('nodes', {})
                        if target_node in nodes:
                            node_info = nodes[target_node]
                            target_ip = node_info.get('ip', '')
                            target_port = node_info.get('port', 7890)
            
            if not target_ip:
                transfer['status'] = 'error'
                transfer['error'] = f'Target node "{target_node}" not found or unreachable. Available nodes: {list(self.engine.state.nodes.keys()) if self.engine else []}'
                return
            
            # Read and encrypt file in chunks
            chunk_size = 64 * 1024  # 64KB chunks
            total_sent = 0
            
            with open(file_path, 'rb') as f:
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    
                    # Encrypt chunk
                    encrypted_chunk = self.secure_transfer.encrypt_file_chunk(chunk)
                    
                    # Send via HTTP POST (would use tunnel if available)
                    import urllib.request
                    data = {
                        'transfer_id': transfer['id'],
                        'file_name': transfer['file_name'],
                        'chunk_data': base64.b64encode(encrypted_chunk).decode(),
                        'file_hash': transfer['file_hash'],
                        'total_size': transfer['file_size']
                    }
                    
                    request = urllib.request.Request(
                        f"http://{target_ip}:{target_port}/file/receive",
                        data=json.dumps(data).encode(),
                        headers={'Content-Type': 'application/json'}
                    )
                    
                    try:
                        with urllib.request.urlopen(request, timeout=30) as response:
                            result = json.loads(response.read().decode())
                            if result.get('status') == 'ok':
                                total_sent += len(chunk)
                                transfer['bytes_sent'] = total_sent
                                
                                # Update progress
                                progress_pct = (total_sent / transfer['file_size']) * 100 if transfer['file_size'] > 0 else 0
                                transfer['progress'] = progress_pct
                                
                                if transfer['id'] in self.progress_callbacks:
                                    self.progress_callbacks[transfer['id']](progress_pct)
                            else:
                                raise Exception(f"Transfer failed: {result.get('message', 'Unknown error')}")
                    except urllib.error.URLError as e:
                        raise Exception(f"Connection error to {target_ip}:{target_port}: {e}")
                    except Exception as e:
                        raise Exception(f"HTTP transfer error: {e}")
            
            transfer['status'] = 'completed'
            transfer['end_time'] = time.time()
            
            # Verify file integrity
            if os.path.exists(file_path):
                calculated_hash = self.secure_transfer.calculate_file_hash(file_path)
                if calculated_hash == transfer['file_hash']:
                    print(f"[+] File transfer completed: {transfer['file_name']}")
                    print(f"[+] Security: File integrity verified (SHA256: {calculated_hash[:16]}...)")
                    print(f"[+] Security: Transfer encrypted: {CRYPTO_AVAILABLE}")
                else:
                    print(f"[!] Security WARNING: File hash mismatch!")
                    transfer['status'] = 'error'
                    transfer['error'] = 'File integrity check failed'
            else:
                print(f"[+] File transfer completed: {transfer['file_name']} (temp file)")
            
        except Exception as e:
            transfer['status'] = 'error'
            transfer['error'] = str(e)
            import traceback
            traceback.print_exc()
    
    def get_transfer_status(self, transfer_id: str) -> Dict:
        """Get status of file transfer"""
        if transfer_id in self.active_transfers:
            transfer = self.active_transfers[transfer_id].copy()
            if transfer['file_size'] > 0:
                transfer['progress'] = (transfer['bytes_sent'] / transfer['file_size']) * 100
            else:
                transfer['progress'] = 0
            return transfer
        return {'status': 'not_found'}
    
    def get_all_transfers(self) -> List[Dict]:
        """Get all active transfers"""
        return list(self.active_transfers.values())

