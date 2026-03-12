#!/usr/bin/env python3
"""
GHOST COMMS - Encrypted P2P Communication System
Like WhatsApp but for hackers. End-to-end encrypted.

Features:
- End-to-end encryption (AES-256 + ECDH key exchange)
- P2P mesh networking (no central server needed)
- Real-time messaging
- Presence/status system
- Voice ready (hooks for WebRTC)
- Competition/rivalry system for Ghost Nation
"""

import os
import sys
import json
import time
import socket
import threading
import hashlib
import base64
import struct
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime

# Crypto imports - fallback if not available
try:
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.hazmat.primitives.kdf.hkdf import HKDF
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.backends import default_backend
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    print("[GHOST COMMS] ⚠️ cryptography not installed. Using basic encryption.")
    print("[GHOST COMMS] Install: pip install cryptography")


class MessageType(Enum):
    """Message types for the protocol"""
    HANDSHAKE = 'handshake'
    KEY_EXCHANGE = 'key_exchange'
    TEXT = 'text'
    PRESENCE = 'presence'
    FILE = 'file'
    VOICE = 'voice'
    CHALLENGE = 'challenge'  # For competitions
    TAUNT = 'taunt'  # Trash talk
    TEAM_INVITE = 'team_invite'
    SPECTATE_REQUEST = 'spectate_request'


class PresenceStatus(Enum):
    """User presence status"""
    ONLINE = 'online'
    AWAY = 'away'
    BUSY = 'busy'  # In competition
    INVISIBLE = 'invisible'
    OFFLINE = 'offline'


@dataclass
class GhostUser:
    """A user in the Ghost network"""
    ghost_id: str
    display_name: str
    public_key: Optional[bytes] = None
    status: PresenceStatus = PresenceStatus.OFFLINE
    last_seen: float = 0
    ip: str = ''
    port: int = 0
    team: str = ''  # Red/Blue team
    rank: int = 0
    wins: int = 0
    losses: int = 0
    avatar_url: str = ''
    
    def to_dict(self):
        d = asdict(self)
        d['status'] = self.status.value
        if self.public_key:
            d['public_key'] = base64.b64encode(self.public_key).decode()
        return d
    
    @classmethod
    def from_dict(cls, d):
        d['status'] = PresenceStatus(d.get('status', 'offline'))
        if d.get('public_key'):
            d['public_key'] = base64.b64decode(d['public_key'])
        return cls(**d)


@dataclass 
class GhostMessage:
    """An encrypted message"""
    msg_id: str
    msg_type: MessageType
    sender_id: str
    recipient_id: str
    timestamp: float
    content: str  # Encrypted content
    nonce: bytes = b''  # For encryption
    signature: bytes = b''  # Message signature
    
    def to_dict(self):
        return {
            'msg_id': self.msg_id,
            'msg_type': self.msg_type.value,
            'sender_id': self.sender_id,
            'recipient_id': self.recipient_id,
            'timestamp': self.timestamp,
            'content': self.content,
            'nonce': base64.b64encode(self.nonce).decode() if self.nonce else '',
            'signature': base64.b64encode(self.signature).decode() if self.signature else ''
        }
    
    @classmethod
    def from_dict(cls, d):
        return cls(
            msg_id=d['msg_id'],
            msg_type=MessageType(d['msg_type']),
            sender_id=d['sender_id'],
            recipient_id=d['recipient_id'],
            timestamp=d['timestamp'],
            content=d['content'],
            nonce=base64.b64decode(d['nonce']) if d.get('nonce') else b'',
            signature=base64.b64decode(d['signature']) if d.get('signature') else b''
        )


class GhostCrypto:
    """End-to-end encryption using ECDH + AES-256-GCM"""
    
    def __init__(self):
        if CRYPTO_AVAILABLE:
            # Generate ECDH key pair
            self.private_key = ec.generate_private_key(ec.SECP384R1(), default_backend())
            self.public_key = self.private_key.public_key()
        else:
            self.private_key = None
            self.public_key = None
        
        # Shared secrets with peers (peer_id -> shared_key)
        self.shared_secrets: Dict[str, bytes] = {}
    
    def get_public_key_bytes(self) -> bytes:
        """Export public key for sharing"""
        if not CRYPTO_AVAILABLE:
            return b'NO_CRYPTO'
        return self.public_key.public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
    
    def derive_shared_secret(self, peer_id: str, peer_public_key_bytes: bytes):
        """Derive shared secret from peer's public key (ECDH)"""
        if not CRYPTO_AVAILABLE:
            # Fallback: use peer_id as "key" (NOT SECURE - just for testing)
            self.shared_secrets[peer_id] = hashlib.sha256(peer_id.encode()).digest()
            return
        
        peer_public_key = serialization.load_der_public_key(
            peer_public_key_bytes, 
            backend=default_backend()
        )
        
        # ECDH key exchange
        shared_key = self.private_key.exchange(ec.ECDH(), peer_public_key)
        
        # Derive AES key using HKDF
        derived_key = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=b'ghost_comms_v1',
            backend=default_backend()
        ).derive(shared_key)
        
        self.shared_secrets[peer_id] = derived_key
    
    def encrypt(self, peer_id: str, plaintext: str) -> tuple:
        """Encrypt message for peer. Returns (ciphertext, nonce)"""
        if peer_id not in self.shared_secrets:
            raise ValueError(f"No shared secret with {peer_id}")
        
        key = self.shared_secrets[peer_id]
        plaintext_bytes = plaintext.encode('utf-8')
        
        if CRYPTO_AVAILABLE:
            nonce = os.urandom(12)
            aesgcm = AESGCM(key)
            ciphertext = aesgcm.encrypt(nonce, plaintext_bytes, None)
            return base64.b64encode(ciphertext).decode(), nonce
        else:
            # Basic XOR "encryption" (NOT SECURE - fallback only)
            key_repeated = (key * (len(plaintext_bytes) // len(key) + 1))[:len(plaintext_bytes)]
            ciphertext = bytes(a ^ b for a, b in zip(plaintext_bytes, key_repeated))
            return base64.b64encode(ciphertext).decode(), b'NO_NONCE'
    
    def decrypt(self, peer_id: str, ciphertext: str, nonce: bytes) -> str:
        """Decrypt message from peer"""
        if peer_id not in self.shared_secrets:
            raise ValueError(f"No shared secret with {peer_id}")
        
        key = self.shared_secrets[peer_id]
        ciphertext_bytes = base64.b64decode(ciphertext)
        
        if CRYPTO_AVAILABLE:
            aesgcm = AESGCM(key)
            plaintext = aesgcm.decrypt(nonce, ciphertext_bytes, None)
            return plaintext.decode('utf-8')
        else:
            # Basic XOR "decryption"
            key_repeated = (key * (len(ciphertext_bytes) // len(key) + 1))[:len(ciphertext_bytes)]
            plaintext = bytes(a ^ b for a, b in zip(ciphertext_bytes, key_repeated))
            return plaintext.decode('utf-8')


class GhostComms:
    """
    Main P2P encrypted communication system
    
    Usage:
        comms = GhostComms(ghost_id="ghost_linux_001", display_name="ShadowHunter")
        comms.start(port=9001)
        comms.connect_peer("192.168.1.100", 9001)
        comms.send_message("ghost_win_001", "Ready to get pwned?")
    """
    
    def __init__(self, ghost_id: str, display_name: str):
        self.ghost_id = ghost_id
        self.display_name = display_name
        self.crypto = GhostCrypto()
        
        # Network
        self.listen_port = 9001
        self.server_socket = None
        self.running = False
        
        # Peers
        self.peers: Dict[str, GhostUser] = {}
        self.peer_connections: Dict[str, socket.socket] = {}
        
        # My profile
        self.my_profile = GhostUser(
            ghost_id=ghost_id,
            display_name=display_name,
            public_key=self.crypto.get_public_key_bytes(),
            status=PresenceStatus.ONLINE,
            last_seen=time.time()
        )
        
        # Message handlers
        self.message_handlers: Dict[MessageType, List[Callable]] = {
            t: [] for t in MessageType
        }
        
        # Message history
        self.message_history: List[GhostMessage] = []
        
        print(f"[GHOST COMMS] Initialized as {display_name} ({ghost_id})")
    
    def on_message(self, msg_type: MessageType, handler: Callable):
        """Register handler for message type"""
        self.message_handlers[msg_type].append(handler)
    
    def start(self, port: int = 9001):
        """Start listening for connections"""
        self.listen_port = port
        self.running = True
        
        # Start server thread
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(('0.0.0.0', port))
        self.server_socket.listen(10)
        
        threading.Thread(target=self._accept_loop, daemon=True).start()
        
        # Start presence broadcast
        threading.Thread(target=self._presence_loop, daemon=True).start()
        
        print(f"[GHOST COMMS] 🔊 Listening on port {port}")
        print(f"[GHOST COMMS] 🔒 End-to-end encryption: {'ENABLED' if CRYPTO_AVAILABLE else 'FALLBACK MODE'}")
    
    def stop(self):
        """Stop the comms system"""
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        for conn in self.peer_connections.values():
            try:
                conn.close()
            except:
                pass
        print("[GHOST COMMS] Stopped")
    
    def _accept_loop(self):
        """Accept incoming connections"""
        while self.running:
            try:
                conn, addr = self.server_socket.accept()
                print(f"[GHOST COMMS] 📥 Connection from {addr}")
                threading.Thread(
                    target=self._handle_connection, 
                    args=(conn, addr),
                    daemon=True
                ).start()
            except:
                if self.running:
                    import traceback
                    traceback.print_exc()
    
    def _handle_connection(self, conn: socket.socket, addr):
        """Handle incoming connection"""
        peer_id = None
        
        try:
            while self.running:
                # Read message length (4 bytes)
                length_data = conn.recv(4)
                if not length_data:
                    break
                
                msg_length = struct.unpack('!I', length_data)[0]
                
                # Read message
                data = b''
                while len(data) < msg_length:
                    chunk = conn.recv(min(4096, msg_length - len(data)))
                    if not chunk:
                        break
                    data += chunk
                
                if len(data) < msg_length:
                    break
                
                # Parse message
                msg_dict = json.loads(data.decode('utf-8'))
                msg = GhostMessage.from_dict(msg_dict)
                
                # Handle handshake
                if msg.msg_type == MessageType.HANDSHAKE:
                    peer_data = json.loads(msg.content)
                    peer = GhostUser.from_dict(peer_data)
                    peer_id = peer.ghost_id
                    peer.ip = addr[0]
                    
                    self.peers[peer_id] = peer
                    self.peer_connections[peer_id] = conn
                    
                    # Send our handshake back
                    self._send_handshake(conn)
                    
                    print(f"[GHOST COMMS] 🤝 Handshake with {peer.display_name} ({peer_id})")
                    continue
                
                # Handle key exchange
                if msg.msg_type == MessageType.KEY_EXCHANGE:
                    peer_public_key = base64.b64decode(msg.content)
                    self.crypto.derive_shared_secret(msg.sender_id, peer_public_key)
                    print(f"[GHOST COMMS] 🔑 Key exchange complete with {msg.sender_id}")
                    continue
                
                # Decrypt and handle message
                if msg.sender_id in self.crypto.shared_secrets:
                    try:
                        decrypted = self.crypto.decrypt(
                            msg.sender_id, 
                            msg.content, 
                            msg.nonce
                        )
                        msg.content = decrypted
                    except Exception as e:
                        print(f"[GHOST COMMS] ⚠️ Decryption failed: {e}")
                
                # Store in history
                self.message_history.append(msg)
                
                # Call handlers
                for handler in self.message_handlers.get(msg.msg_type, []):
                    try:
                        handler(msg)
                    except Exception as e:
                        print(f"[GHOST COMMS] Handler error: {e}")
                
                # Default handling
                self._default_message_handler(msg)
                
        except Exception as e:
            if self.running:
                print(f"[GHOST COMMS] Connection error: {e}")
        finally:
            if peer_id and peer_id in self.peer_connections:
                del self.peer_connections[peer_id]
                if peer_id in self.peers:
                    self.peers[peer_id].status = PresenceStatus.OFFLINE
            conn.close()
    
    def _default_message_handler(self, msg: GhostMessage):
        """Default handler for messages"""
        sender = self.peers.get(msg.sender_id)
        sender_name = sender.display_name if sender else msg.sender_id
        
        if msg.msg_type == MessageType.TEXT:
            print(f"[💬 {sender_name}] {msg.content}")
        
        elif msg.msg_type == MessageType.TAUNT:
            print(f"[🔥 TAUNT from {sender_name}] {msg.content}")
        
        elif msg.msg_type == MessageType.CHALLENGE:
            print(f"[⚔️ CHALLENGE from {sender_name}] {msg.content}")
        
        elif msg.msg_type == MessageType.PRESENCE:
            status = msg.content
            if sender:
                sender.status = PresenceStatus(status)
                print(f"[👤 {sender_name}] Status: {status}")
    
    def _send_handshake(self, conn: socket.socket):
        """Send handshake with our info"""
        msg = GhostMessage(
            msg_id=self._gen_msg_id(),
            msg_type=MessageType.HANDSHAKE,
            sender_id=self.ghost_id,
            recipient_id='',
            timestamp=time.time(),
            content=json.dumps(self.my_profile.to_dict())
        )
        self._send_raw(conn, msg)
    
    def _send_key_exchange(self, peer_id: str):
        """Send our public key to peer"""
        if peer_id not in self.peer_connections:
            return
        
        msg = GhostMessage(
            msg_id=self._gen_msg_id(),
            msg_type=MessageType.KEY_EXCHANGE,
            sender_id=self.ghost_id,
            recipient_id=peer_id,
            timestamp=time.time(),
            content=base64.b64encode(self.crypto.get_public_key_bytes()).decode()
        )
        self._send_raw(self.peer_connections[peer_id], msg)
    
    def _send_raw(self, conn: socket.socket, msg: GhostMessage):
        """Send raw message to connection"""
        data = json.dumps(msg.to_dict()).encode('utf-8')
        length = struct.pack('!I', len(data))
        conn.sendall(length + data)
    
    def _gen_msg_id(self) -> str:
        """Generate unique message ID"""
        return hashlib.sha256(
            f"{self.ghost_id}:{time.time()}:{os.urandom(8).hex()}".encode()
        ).hexdigest()[:16]
    
    def _presence_loop(self):
        """Broadcast presence periodically"""
        while self.running:
            time.sleep(30)  # Every 30 seconds
            self.broadcast_presence()
    
    def connect_peer(self, ip: str, port: int = 9001) -> bool:
        """Connect to a peer"""
        try:
            conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            conn.settimeout(10)
            conn.connect((ip, port))
            
            # Send handshake
            self._send_handshake(conn)
            
            # Handle responses in background
            threading.Thread(
                target=self._handle_connection,
                args=(conn, (ip, port)),
                daemon=True
            ).start()
            
            # Wait for handshake response
            time.sleep(0.5)
            
            # Send key exchange
            for peer_id in list(self.peers.keys()):
                if self.peers[peer_id].ip == ip:
                    self._send_key_exchange(peer_id)
                    
                    # Derive shared secret from their key
                    if self.peers[peer_id].public_key:
                        self.crypto.derive_shared_secret(
                            peer_id, 
                            self.peers[peer_id].public_key
                        )
                    break
            
            print(f"[GHOST COMMS] ✅ Connected to {ip}:{port}")
            return True
            
        except Exception as e:
            print(f"[GHOST COMMS] ❌ Failed to connect to {ip}:{port}: {e}")
            return False
    
    def send_message(self, peer_id: str, content: str, 
                     msg_type: MessageType = MessageType.TEXT) -> bool:
        """Send encrypted message to peer"""
        if peer_id not in self.peer_connections:
            print(f"[GHOST COMMS] ❌ Not connected to {peer_id}")
            return False
        
        try:
            # Encrypt if we have shared secret
            nonce = b''
            if peer_id in self.crypto.shared_secrets:
                content, nonce = self.crypto.encrypt(peer_id, content)
            
            msg = GhostMessage(
                msg_id=self._gen_msg_id(),
                msg_type=msg_type,
                sender_id=self.ghost_id,
                recipient_id=peer_id,
                timestamp=time.time(),
                content=content,
                nonce=nonce
            )
            
            self._send_raw(self.peer_connections[peer_id], msg)
            self.message_history.append(msg)
            return True
            
        except Exception as e:
            print(f"[GHOST COMMS] ❌ Send failed: {e}")
            return False
    
    def broadcast_message(self, content: str, msg_type: MessageType = MessageType.TEXT):
        """Send message to all connected peers"""
        for peer_id in self.peer_connections:
            self.send_message(peer_id, content, msg_type)
    
    def broadcast_presence(self):
        """Broadcast current status to all peers"""
        for peer_id in self.peer_connections:
            self.send_message(peer_id, self.my_profile.status.value, MessageType.PRESENCE)
    
    def set_status(self, status: PresenceStatus):
        """Set my status and broadcast"""
        self.my_profile.status = status
        self.broadcast_presence()
    
    # Competition features
    def send_taunt(self, peer_id: str, taunt: str):
        """Send trash talk to opponent"""
        return self.send_message(peer_id, taunt, MessageType.TAUNT)
    
    def send_challenge(self, peer_id: str, challenge_details: str):
        """Challenge a peer to competition"""
        return self.send_message(peer_id, challenge_details, MessageType.CHALLENGE)
    
    def get_online_peers(self) -> List[GhostUser]:
        """Get list of online peers"""
        return [p for p in self.peers.values() if p.status != PresenceStatus.OFFLINE]
    
    def get_chat_history(self, peer_id: str = None) -> List[GhostMessage]:
        """Get chat history, optionally filtered by peer"""
        if peer_id:
            return [m for m in self.message_history 
                   if m.sender_id == peer_id or m.recipient_id == peer_id]
        return self.message_history


# CLI for testing
if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Ghost Comms - Encrypted P2P Chat')
    parser.add_argument('--name', default='Ghost', help='Display name')
    parser.add_argument('--port', type=int, default=9001, help='Listen port')
    parser.add_argument('--connect', help='Peer IP to connect to')
    
    args = parser.parse_args()
    
    # Generate ghost ID from hostname
    ghost_id = f"ghost_{socket.gethostname().lower().replace('-', '_')}"
    
    comms = GhostComms(ghost_id, args.name)
    comms.start(args.port)
    
    if args.connect:
        time.sleep(0.5)
        comms.connect_peer(args.connect)
    
    print("\nCommands:")
    print("  /peers     - List connected peers")
    print("  /status X  - Set status (online/away/busy)")
    print("  /taunt ID MSG - Send taunt")
    print("  /challenge ID MSG - Send challenge")
    print("  /quit      - Exit")
    print("  (anything else) - Send to all peers")
    print()
    
    try:
        while True:
            line = input()
            
            if line.startswith('/peers'):
                peers = comms.get_online_peers()
                if peers:
                    for p in peers:
                        print(f"  {p.ghost_id}: {p.display_name} [{p.status.value}]")
                else:
                    print("  No peers connected")
            
            elif line.startswith('/status '):
                status = line.split(' ', 1)[1]
                comms.set_status(PresenceStatus(status))
            
            elif line.startswith('/taunt '):
                parts = line.split(' ', 2)
                if len(parts) >= 3:
                    comms.send_taunt(parts[1], parts[2])
            
            elif line.startswith('/challenge '):
                parts = line.split(' ', 2)
                if len(parts) >= 3:
                    comms.send_challenge(parts[1], parts[2])
            
            elif line == '/quit':
                break
            
            else:
                comms.broadcast_message(line)
                
    except KeyboardInterrupt:
        pass
    
    comms.stop()

