#!/usr/bin/env python3
"""
Ghost File Messenger
====================
Direct peer-to-peer file transfer like email attachments.
Browse files, select peer, send with message - receive in inbox.
"""

import os
import json
import base64
import hashlib
import time
import requests
from pathlib import Path
from typing import List, Dict, Optional, Any


class GhostFileMessenger:
    """
    File messenger for direct peer-to-peer file transfer.
    Like email attachments but through mesh network.
    """
    
    def __init__(self, node_id: str, port: int = 7890, project_dir: str = None):
        self.node_id = node_id
        self.port = port
        self.project_dir = project_dir or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Inbox/Outbox directories
        inbox_base = os.path.join(self.project_dir, 'ghost_inbox')
        outbox_base = os.path.join(self.project_dir, 'ghost_outbox')
        
        self.inbox_dir = os.path.join(inbox_base, node_id)
        self.outbox_dir = os.path.join(outbox_base, node_id)
        
        os.makedirs(self.inbox_dir, exist_ok=True)
        os.makedirs(self.outbox_dir, exist_ok=True)
        
        print(f"[FileMessenger] Initialized - Node: {node_id}, Inbox: {self.inbox_dir}")
    
    def get_file_list(self, directory: str = None) -> List[Dict[str, Any]]:
        """
        Get browsable file list for sending.
        Scans project directory for files.
        """
        if directory is None:
            directory = self.project_dir
        
        files = []
        try:
            for root, dirs, filenames in os.walk(directory):
                # Skip hidden and system directories
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'ghost_inbox', 'ghost_outbox']]
                
                for filename in filenames:
                    if filename.startswith('.'):
                        continue
                    
                    file_path = os.path.join(root, filename)
                    try:
                        rel_path = os.path.relpath(file_path, directory)
                        size = os.path.getsize(file_path)
                        
                        files.append({
                            'name': filename,
                            'path': file_path,
                            'rel_path': rel_path,
                            'size': size,
                            'size_human': self._format_size(size)
                        })
                    except Exception as e:
                        continue  # Skip files we can't read
        except Exception as e:
            print(f"[FileMessenger] Error scanning files: {e}")
        
        # Sort by name
        files.sort(key=lambda x: x['name'].lower())
        return files
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    
    def send_file_to_peer(self, file_path: str, target_peer_ip: str, target_peer_port: int, message: str = "") -> Dict[str, Any]:
        """
        Send file directly to specific peer like messenger.
        Returns status dict with success/error info.
        """
        try:
            if not os.path.exists(file_path):
                return {'status': 'error', 'message': f'File not found: {file_path}'}
            
            # Read file
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            file_name = os.path.basename(file_path)
            file_hash = hashlib.sha256(file_data).hexdigest()
            file_size = len(file_data)
            
            # Check file size (limit to 100MB for safety)
            if file_size > 100 * 1024 * 1024:
                return {'status': 'error', 'message': 'File too large (max 100MB)'}
            
            payload = {
                'action': 'receive_file',
                'sender': self.node_id,
                'file_name': file_name,
                'file_data': base64.b64encode(file_data).decode(),
                'file_hash': file_hash,
                'file_size': file_size,
                'message': message,
                'timestamp': time.time()
            }
            
            # Send to peer
            url = f"http://{target_peer_ip}:{target_peer_port}/action/file_message"
            print(f"[FileMessenger] Sending {file_name} ({file_size} bytes) to {target_peer_ip}:{target_peer_port}")
            
            try:
                response = requests.post(url, json=payload, timeout=30)
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"[FileMessenger] ✅ File sent successfully: {file_name}")
                    return {'status': 'success', 'message': f'File sent to {target_peer_ip}', **result}
                else:
                    error_msg = response.text[:200]
                    print(f"[FileMessenger] ❌ Send failed: {response.status_code} - {error_msg}")
                    return {'status': 'error', 'message': f'Failed to send: {response.status_code} - {error_msg}'}
                    
            except requests.exceptions.ConnectionError:
                return {'status': 'error', 'message': f'Connection refused - peer not reachable at {target_peer_ip}:{target_peer_port}'}
            except requests.exceptions.Timeout:
                return {'status': 'error', 'message': f'Timeout - peer did not respond at {target_peer_ip}:{target_peer_port}'}
            except Exception as e:
                return {'status': 'error', 'message': f'Network error: {str(e)}'}
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {'status': 'error', 'message': f'Send error: {str(e)}'}
    
    def receive_file_message(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Receive file from peer like messenger.
        Validates hash, saves to inbox, creates message metadata.
        """
        try:
            file_name = payload.get('file_name')
            file_data_b64 = payload.get('file_data')
            file_hash = payload.get('file_hash')
            sender = payload.get('sender', 'unknown')
            message = payload.get('message', '')
            timestamp = payload.get('timestamp', time.time())
            
            if not all([file_name, file_data_b64, file_hash]):
                return {'status': 'error', 'message': 'Missing required fields'}
            
            # Decode file data
            file_data = base64.b64decode(file_data_b64)
            
            # Verify hash
            calculated_hash = hashlib.sha256(file_data).hexdigest()
            if calculated_hash != file_hash:
                return {'status': 'error', 'message': 'File corruption detected - hash mismatch'}
            
            # Save to inbox with sender prefix and timestamp
            safe_filename = f"{sender}_{int(timestamp)}_{file_name}"
            # Remove any invalid characters
            safe_filename = "".join(c for c in safe_filename if c.isalnum() or c in "._-")
            file_path = os.path.join(self.inbox_dir, safe_filename)
            
            # Handle duplicates
            counter = 1
            original_path = file_path
            while os.path.exists(file_path):
                base, ext = os.path.splitext(original_path)
                file_path = f"{base}_{counter}{ext}"
                counter += 1
            
            with open(file_path, 'wb') as f:
                f.write(file_data)
            
            # Create message metadata
            message_data = {
                'sender': sender,
                'file_name': file_name,
                'safe_filename': os.path.basename(file_path),
                'file_path': file_path,
                'file_size': len(file_data),
                'file_hash': file_hash,
                'message': message,
                'timestamp': timestamp,
                'received_time': time.time(),
                'status': 'received'
            }
            
            # Save message info
            msg_file = os.path.join(self.inbox_dir, f"{os.path.basename(file_path)}.msg")
            with open(msg_file, 'w') as f:
                json.dump(message_data, f, indent=2)
            
            print(f"[FileMessenger] ✅ File received from {sender}: {file_name} ({len(file_data)} bytes)")
            
            return {
                'status': 'success',
                'message': f'File received from {sender}',
                'file_path': file_path,
                'file_name': file_name
            }
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {'status': 'error', 'message': f'Receive error: {str(e)}'}
    
    def get_inbox_messages(self) -> List[Dict[str, Any]]:
        """
        Get received files like messenger inbox.
        Returns list of message metadata dicts, sorted newest first.
        """
        messages = []
        try:
            for item in os.listdir(self.inbox_dir):
                if item.endswith('.msg'):
                    msg_path = os.path.join(self.inbox_dir, item)
                    try:
                        with open(msg_path, 'r') as f:
                            message_data = json.load(f)
                        
                        # Verify file still exists
                        if os.path.exists(message_data.get('file_path', '')):
                            messages.append(message_data)
                    except Exception as e:
                        continue  # Skip corrupted message files
            
            # Sort by timestamp, newest first
            messages.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
            
        except Exception as e:
            print(f"[FileMessenger] Error reading inbox: {e}")
        
        return messages
    
    def get_available_peers(self, engine=None) -> List[Dict[str, Any]]:
        """
        Discover available peers for file sending.
        Integrates with existing peer discovery system.
        """
        peers = []
        
        try:
            # Get peers from engine status if available
            if engine and hasattr(engine, 'get_status'):
                status = engine.get_status()
                nodes = status.get('nodes', {})
                
                for node_id, node_data in nodes.items():
                    if node_id != self.node_id:  # Don't include self
                        peers.append({
                            'id': node_id,
                            'ip': node_data.get('ip'),
                            'port': node_data.get('port', 7890),
                            'name': node_data.get('platform', 'unknown'),
                            'platform': node_data.get('platform', 'unknown')
                        })
        except Exception as e:
            print(f"[FileMessenger] Error getting peers from engine: {e}")
        
        # If no peers found, add localhost for testing
        if not peers:
            peers.append({
                'id': 'localhost',
                'ip': '127.0.0.1',
                'port': self.port,
                'name': 'Local Server',
                'platform': 'local'
            })
        
        return peers
    
    def delete_received_file(self, file_path: str) -> Dict[str, Any]:
        """Delete a received file and its message metadata"""
        try:
            if not os.path.exists(file_path):
                return {'status': 'error', 'message': 'File not found'}
            
            # Delete file
            os.remove(file_path)
            
            # Delete message metadata if exists
            msg_file = f"{file_path}.msg"
            if os.path.exists(msg_file):
                os.remove(msg_file)
            
            return {'status': 'success', 'message': 'File deleted'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

