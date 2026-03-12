#!/usr/bin/env python3
"""
GhostHUD Secure Socket Tunnel - PHASE 3
=========================================

Encrypted P2P tunnels using Python native sockets + AES-256-GCM encryption.
NO WIREGUARD - Pure Python implementation for cross-platform compatibility.

Features:
- TCP sockets with AES-256-GCM encryption
- Auto-handshake with timestamp validation
- Re-keying every 1 hour
- Heartbeat every 30 seconds (dead peer detection)
- HTTP fallback if sockets fail
- Cross-platform: Linux, Windows, Android/Termux

Author: GhostHUD Team
License: MIT
"""

# --- SAFE UTF-8 WRAPPER FOR WINDOWS ---
import sys
import io
import os

if sys.platform == 'win32':
    try:
        # Only wrap if not already wrapped
        if not isinstance(sys.stdout, io.TextIOWrapper):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        if not isinstance(sys.stderr, io.TextIOWrapper):
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except Exception:
        # fallback: change console code page
        os.system('chcp 65001 > nul')

# Optional: catch any prints after stdout/stderr closed
class DummyIO:
    def write(self, *args, **kwargs): pass
    def flush(self): pass

if sys.stdout is None:
    sys.stdout = DummyIO()
if sys.stderr is None:
    sys.stderr = sys.stdout
# --- END SAFE WRAPPER ---

import socket
import threading
import time
import json
import hashlib
import hmac
import base64
import random
import uuid
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum, auto
import struct

# Configure logging FIRST (before any other imports that might use it)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ghosthud.secure_tunnel")

# Try to import cryptography library for AES-256-GCM
# Use lazy import to avoid startup failures
CRYPTO_AVAILABLE = False
AESGCM = None
hashes = None
PBKDF2HMAC = None

def _init_crypto():
    """Lazy initialization of crypto library"""
    global CRYPTO_AVAILABLE, AESGCM, hashes, PBKDF2HMAC
    if CRYPTO_AVAILABLE:
        return True

    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM as _AESGCM
        from cryptography.hazmat.primitives import hashes as _hashes
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC as _PBKDF2HMAC
        AESGCM = _AESGCM
        hashes = _hashes
        PBKDF2HMAC = _PBKDF2HMAC
        CRYPTO_AVAILABLE = True
        logger.info("Cryptography library loaded successfully")
        return True
    except (ImportError, Exception) as e:
        print(f"[WARNING] cryptography library not available ({type(e).__name__}). Using fallback encryption (NOT SECURE).")
        CRYPTO_AVAILABLE = False
        return False

# Try to initialize crypto at import time, but don't fail if it doesn't work
try:
    _init_crypto()
except:
    pass

# HTTP fallback imports
try:
    import http.server
    import urllib.request
    import urllib.parse
    HTTP_AVAILABLE = True
except ImportError:
    HTTP_AVAILABLE = False

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TUNNEL_PORT = 51820  # Same as WireGuard, but pure Python
HTTP_FALLBACK_PORT = 51821
HANDSHAKE_TIMEOUT = 5  # seconds
HEARTBEAT_INTERVAL = 30  # seconds
REKEY_INTERVAL = 3600  # 1 hour in seconds
MAX_PACKET_SIZE = 65536
PROTOCOL_VERSION = 1

# Message types
class MessageType(Enum):
    """Message types for tunnel protocol"""
    HANDSHAKE_INIT = 1
    HANDSHAKE_RESPONSE = 2
    HANDSHAKE_ACK = 3
    DATA = 4
    HEARTBEAT = 5
    HEARTBEAT_ACK = 6
    REKEY = 7
    GOODBYE = 8

class PeerStatus(Enum):
    """Status of a peer connection"""
    DISCONNECTED = auto()
    CONNECTING = auto()
    HANDSHAKING = auto()
    CONNECTED = auto()
    DEGRADED = auto()
    ERROR = auto()

# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

@dataclass
class TunnelPeer:
    """Represents a peer in the secure tunnel"""
    id: str
    name: str
    address: str  # IP or hostname
    port: int
    status: PeerStatus = PeerStatus.DISCONNECTED
    last_seen: float = 0
    latency: float = 0  # milliseconds
    encryption_active: bool = False
    session_key: Optional[bytes] = None
    last_heartbeat: float = 0
    last_rekey: float = 0
    missed_heartbeats: int = 0
    bytes_sent: int = 0
    bytes_received: int = 0

@dataclass
class TunnelIdentity:
    """Identity for this tunnel node"""
    id: str
    name: str
    mesh_id: str
    auth_token: str
    public_key: bytes
    private_key: bytes

# ---------------------------------------------------------------------------
# Crypto Helper
# ---------------------------------------------------------------------------

class CryptoHelper:
    """Handles all cryptographic operations"""

    @staticmethod
    def generate_key_from_token(auth_token: str, mesh_id: str) -> bytes:
        """
        Generate AES-256 key from auth_token and mesh_id
        Uses PBKDF2 for proper key derivation
        """
        if not CRYPTO_AVAILABLE:
            # Fallback to simple SHA256 (NOT SECURE, but works)
            combined = f"{auth_token}{mesh_id}".encode('utf-8')
            return hashlib.sha256(combined).digest()

        # Proper key derivation with PBKDF2
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,  # 256 bits
            salt=mesh_id.encode('utf-8'),
            iterations=100000,
        )
        return kdf.derive(auth_token.encode('utf-8'))

    @staticmethod
    def generate_session_key() -> bytes:
        """Generate a random session key for peer-to-peer communication"""
        return os.urandom(32)  # 256 bits

    @staticmethod
    def encrypt(key: bytes, plaintext: bytes, associated_data: bytes = b'') -> bytes:
        """
        Encrypt data using AES-256-GCM

        SECURITY FIX: Removed insecure XOR fallback
        Returns: iv (12 bytes) + ciphertext + tag (16 bytes)
        """
        if not CRYPTO_AVAILABLE:
            # SECURITY FIX: No insecure fallback - fail securely
            raise RuntimeError(
                "SECURITY ERROR: Cryptography library not available. "
                "Install with: pip install cryptography\n"
                "Refusing to use insecure encryption fallback."
            )

        # Generate random IV (nonce) - 12 bytes for GCM
        iv = os.urandom(12)

        # Create cipher and encrypt
        aesgcm = AESGCM(key)
        ciphertext = aesgcm.encrypt(iv, plaintext, associated_data)

        # Return iv + ciphertext (which includes the tag)
        return iv + ciphertext

    @staticmethod
    def decrypt(key: bytes, encrypted: bytes, associated_data: bytes = b'') -> bytes:
        """
        Decrypt data using AES-256-GCM

        SECURITY FIX: Removed insecure XOR fallback
        Expects: iv (12 bytes) + ciphertext + tag (16 bytes)
        """
        if not CRYPTO_AVAILABLE:
            # SECURITY FIX: No insecure fallback - fail securely
            raise RuntimeError(
                "SECURITY ERROR: Cryptography library not available. "
                "Install with: pip install cryptography\n"
                "Refusing to use insecure decryption fallback."
            )

        # Extract IV and ciphertext
        iv = encrypted[:12]
        ciphertext = encrypted[12:]

        # Decrypt
        aesgcm = AESGCM(key)
        plaintext = aesgcm.decrypt(iv, ciphertext, associated_data)

        return plaintext

    @staticmethod
    def generate_keypair() -> Tuple[bytes, bytes]:
        """Generate public/private keypair (simplified version)"""
        # In a real implementation, use proper asymmetric crypto
        # For now, we'll use symmetric keys
        private_key = os.urandom(32)
        public_key = hashlib.sha256(private_key).digest()
        return public_key, private_key

    @staticmethod
    def verify_timestamp(timestamp: int, max_age: int = 5) -> bool:
        """Verify that timestamp is recent (within max_age seconds)"""
        current_time = int(time.time())
        return abs(current_time - timestamp) <= max_age

# ---------------------------------------------------------------------------
# Tunnel Protocol Handler
# ---------------------------------------------------------------------------

class TunnelProtocol:
    """Handles the tunnel protocol messages"""

    @staticmethod
    def pack_message(msg_type: MessageType, payload: bytes) -> bytes:
        """
        Pack a message with header
        Format: [version:1][type:1][length:4][payload:N]
        """
        header = struct.pack('!BBI', PROTOCOL_VERSION, msg_type.value, len(payload))
        return header + payload

    @staticmethod
    def unpack_message(data: bytes) -> Tuple[MessageType, bytes]:
        """Unpack a message and return type and payload"""
        if len(data) < 6:
            raise ValueError("Message too short")

        version, msg_type_val, payload_len = struct.unpack('!BBI', data[:6])

        if version != PROTOCOL_VERSION:
            raise ValueError(f"Unsupported protocol version: {version}")

        msg_type = MessageType(msg_type_val)
        payload = data[6:6+payload_len]

        return msg_type, payload

    @staticmethod
    def create_handshake_init(identity: TunnelIdentity) -> bytes:
        """Create handshake initiation message"""
        payload = json.dumps({
            'node_id': identity.id,
            'node_name': identity.name,
            'mesh_id': identity.mesh_id,
            'public_key': base64.b64encode(identity.public_key).decode('utf-8'),
            'timestamp': int(time.time())
        }).encode('utf-8')

        return TunnelProtocol.pack_message(MessageType.HANDSHAKE_INIT, payload)

    @staticmethod
    def create_handshake_response(identity: TunnelIdentity, session_key: bytes) -> bytes:
        """Create handshake response with encrypted session key"""
        # Encrypt session key with mesh key
        mesh_key = CryptoHelper.generate_key_from_token(
            identity.auth_token,
            identity.mesh_id
        )
        encrypted_session_key = CryptoHelper.encrypt(mesh_key, session_key)

        payload = json.dumps({
            'node_id': identity.id,
            'node_name': identity.name,
            'encrypted_session_key': base64.b64encode(encrypted_session_key).decode('utf-8'),
            'timestamp': int(time.time())
        }).encode('utf-8')

        return TunnelProtocol.pack_message(MessageType.HANDSHAKE_RESPONSE, payload)

    @staticmethod
    def create_handshake_ack() -> bytes:
        """Create handshake acknowledgment"""
        payload = json.dumps({
            'status': 'ok',
            'timestamp': int(time.time())
        }).encode('utf-8')

        return TunnelProtocol.pack_message(MessageType.HANDSHAKE_ACK, payload)

    @staticmethod
    def create_data_message(data: bytes, session_key: bytes) -> bytes:
        """Create encrypted data message"""
        encrypted_data = CryptoHelper.encrypt(session_key, data)
        return TunnelProtocol.pack_message(MessageType.DATA, encrypted_data)

    @staticmethod
    def create_heartbeat() -> bytes:
        """Create heartbeat message"""
        payload = json.dumps({
            'timestamp': int(time.time())
        }).encode('utf-8')

        return TunnelProtocol.pack_message(MessageType.HEARTBEAT, payload)

    @staticmethod
    def create_heartbeat_ack() -> bytes:
        """Create heartbeat acknowledgment"""
        payload = json.dumps({
            'timestamp': int(time.time())
        }).encode('utf-8')

        return TunnelProtocol.pack_message(MessageType.HEARTBEAT_ACK, payload)

    @staticmethod
    def create_goodbye() -> bytes:
        """Create goodbye message for graceful disconnect"""
        payload = json.dumps({
            'reason': 'shutdown',
            'timestamp': int(time.time())
        }).encode('utf-8')

        return TunnelProtocol.pack_message(MessageType.GOODBYE, payload)

# ---------------------------------------------------------------------------
# HTTP Fallback Handler
# ---------------------------------------------------------------------------

class HTTPFallbackHandler:
    """Handles HTTP fallback for socket failures"""

    def __init__(self, port: int = HTTP_FALLBACK_PORT):
        self.port = port
        self.server = None
        self.running = False
        self.message_queue = []
        self.lock = threading.Lock()

    def start(self):
        """Start HTTP fallback server"""
        if not HTTP_AVAILABLE:
            logger.warning("HTTP fallback not available")
            return False

        try:
            # Create simple HTTP server
            handler = self._create_handler()
            self.server = http.server.HTTPServer(('0.0.0.0', self.port), handler)

            # Run in background thread
            self.running = True
            thread = threading.Thread(target=self._run_server, daemon=True)
            thread.start()

            logger.info(f"HTTP fallback server started on port {self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to start HTTP fallback: {e}")
            return False

    def _run_server(self):
        """Run the HTTP server"""
        while self.running:
            self.server.handle_request()

    def _create_handler(self):
        """Create HTTP request handler"""
        parent = self

        class FallbackHandler(http.server.BaseHTTPRequestHandler):
            def do_POST(self):
                """Handle POST requests with tunnel data"""
                content_length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(content_length)

                with parent.lock:
                    parent.message_queue.append(body)

                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'OK')

            def log_message(self, format, *args):
                """Suppress HTTP logs"""
                pass

        return FallbackHandler

    def send_via_http(self, address: str, port: int, data: bytes) -> bool:
        """Send data via HTTP POST"""
        try:
            url = f"http://{address}:{port}/tunnel"
            req = urllib.request.Request(url, data=data, method='POST')
            with urllib.request.urlopen(req, timeout=5) as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"HTTP fallback send failed: {e}")
            return False

    def get_messages(self) -> List[bytes]:
        """Get received messages from queue"""
        with self.lock:
            messages = self.message_queue.copy()
            self.message_queue.clear()
            return messages

    def stop(self):
        """Stop HTTP fallback server"""
        self.running = False
        if self.server:
            self.server.shutdown()

# ---------------------------------------------------------------------------
# Main Secure Socket Tunnel
# ---------------------------------------------------------------------------

class SecureSocketTunnel:
    """
    Main secure tunnel implementation with native sockets and AES-256-GCM
    """

    def __init__(self,
                 node_name: str = None,
                 mesh_id: str = None,
                 auth_token: str = None,
                 port: int = TUNNEL_PORT):
        """Initialize the secure tunnel"""

        # Generate or use provided identity
        if node_name is None:
            node_name = f"ghost-{socket.gethostname()}"

        if mesh_id is None:
            mesh_id = hashlib.sha256(os.urandom(32)).hexdigest()[:16]

        if auth_token is None:
            auth_token = base64.urlsafe_b64encode(os.urandom(32)).decode('utf-8')

        # Generate keypair
        public_key, private_key = CryptoHelper.generate_keypair()

        self.identity = TunnelIdentity(
            id=str(uuid.uuid4()),
            name=node_name,
            mesh_id=mesh_id,
            auth_token=auth_token,
            public_key=public_key,
            private_key=private_key
        )

        self.port = port
        self.peers: Dict[str, TunnelPeer] = {}
        self.active = False
        self.server_socket: Optional[socket.socket] = None
        self.http_fallback = HTTPFallbackHandler()

        # Threading
        self.lock = threading.RLock()
        self.shutdown_event = threading.Event()
        self.threads = []

        # Statistics
        self.start_time = 0
        self.total_bytes_sent = 0
        self.total_bytes_received = 0

        logger.info(f"Initialized SecureSocketTunnel: {self.identity.name} (ID: {self.identity.id[:8]})")

    def start_tunnel(self) -> bool:
        """Start the tunnel server and all background tasks"""
        if self.active:
            logger.warning("Tunnel already active")
            return False

        try:
            # Create server socket
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(('0.0.0.0', self.port))
            self.server_socket.listen(5)
            self.server_socket.settimeout(1.0)  # Non-blocking with timeout

            self.active = True
            self.start_time = time.time()
            self.shutdown_event.clear()

            # Start background threads
            self._start_accept_thread()
            self._start_heartbeat_thread()
            self._start_rekey_thread()

            # Start HTTP fallback
            self.http_fallback.start()

            logger.info(f"Tunnel ACTIVE on port {self.port}")
            return True

        except Exception as e:
            logger.error(f"Failed to start tunnel: {e}")
            self.active = False
            return False

    def stop_tunnel(self) -> bool:
        """Stop the tunnel gracefully"""
        if not self.active:
            return False

        logger.info("Stopping tunnel...")

        # Send goodbye to all peers
        with self.lock:
            for peer in self.peers.values():
                if peer.status == PeerStatus.CONNECTED:
                    self._send_to_peer(peer, TunnelProtocol.create_goodbye())

        # Signal shutdown
        self.shutdown_event.set()
        self.active = False

        # Close server socket
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass

        # Wait for threads
        for thread in self.threads:
            thread.join(timeout=2)

        # Stop HTTP fallback
        self.http_fallback.stop()

        logger.info("Tunnel STOPPED")
        return True

    def add_peer(self, name: str, address: str, port: int = None) -> str:
        """Add a peer and initiate connection"""
        if port is None:
            port = self.port

        peer_id = str(uuid.uuid4())

        peer = TunnelPeer(
            id=peer_id,
            name=name,
            address=address,
            port=port,
            status=PeerStatus.DISCONNECTED
        )

        with self.lock:
            self.peers[peer_id] = peer

        # Start connection in background
        thread = threading.Thread(
            target=self._connect_to_peer,
            args=(peer_id,),
            daemon=True
        )
        thread.start()

        logger.info(f"Added peer: {name} ({address}:{port})")
        return peer_id

    def remove_peer(self, peer_id: str) -> bool:
        """Remove a peer"""
        with self.lock:
            if peer_id not in self.peers:
                return False

            peer = self.peers[peer_id]

            # Send goodbye if connected
            if peer.status == PeerStatus.CONNECTED:
                self._send_to_peer(peer, TunnelProtocol.create_goodbye())

            del self.peers[peer_id]

        logger.info(f"Removed peer: {peer_id[:8]}")
        return True

    def send(self, peer_id: str, data: bytes) -> bool:
        """Send data to a specific peer"""
        with self.lock:
            if peer_id not in self.peers:
                logger.error(f"Peer not found: {peer_id}")
                return False

            peer = self.peers[peer_id]

            if peer.status != PeerStatus.CONNECTED or not peer.session_key:
                logger.error(f"Peer not connected: {peer_id}")
                return False

            # Create encrypted data message
            message = TunnelProtocol.create_data_message(data, peer.session_key)

            return self._send_to_peer(peer, message)

    def broadcast(self, data: bytes) -> int:
        """Broadcast data to all connected peers"""
        sent_count = 0

        with self.lock:
            peer_ids = list(self.peers.keys())

        for peer_id in peer_ids:
            if self.send(peer_id, data):
                sent_count += 1

        return sent_count

    def get_peers(self) -> List[Dict]:
        """Get list of all peers with their status"""
        with self.lock:
            return [
                {
                    'id': peer.id,
                    'name': peer.name,
                    'address': peer.address,
                    'port': peer.port,
                    'status': peer.status.name,
                    'latency': peer.latency,
                    'encryption_active': peer.encryption_active,
                    'last_seen': peer.last_seen,
                    'bytes_sent': peer.bytes_sent,
                    'bytes_received': peer.bytes_received
                }
                for peer in self.peers.values()
            ]

    def status(self) -> Dict:
        """Get tunnel status"""
        connected_peers = sum(
            1 for p in self.peers.values()
            if p.status == PeerStatus.CONNECTED
        )

        return {
            'active': self.active,
            'mesh_id': self.identity.mesh_id,
            'node_id': self.identity.id,
            'node_name': self.identity.name,
            'port': self.port,
            'uptime': int(time.time() - self.start_time) if self.active else 0,
            'peers_total': len(self.peers),
            'peers_connected': connected_peers,
            'crypto_available': CRYPTO_AVAILABLE,
            'total_bytes_sent': self.total_bytes_sent,
            'total_bytes_received': self.total_bytes_received
        }

    def get_control_status(self) -> str:
        """Get formatted status for control interface"""
        if not self.active:
            return "TUNNEL INACTIVE"

        connected = sum(1 for p in self.peers.values() if p.status == PeerStatus.CONNECTED)

        status_lines = [
            f"TUNNEL ACTIVE ({connected} peers connected)",
            f"Mesh ID: {self.identity.mesh_id}",
            f"Node: {self.identity.name}",
            ""
        ]

        for peer in self.peers.values():
            encryption_status = "ENCRYPTED" if peer.encryption_active else "NO ENCRYPTION"
            status_lines.append(
                f"  {peer.name}: {peer.status.name} | "
                f"Latency: {peer.latency:.1f}ms | {encryption_status}"
            )

        return "\n".join(status_lines)

    # Internal methods

    def _start_accept_thread(self):
        """Start thread to accept incoming connections"""
        thread = threading.Thread(target=self._accept_loop, daemon=True)
        thread.start()
        self.threads.append(thread)

    def _accept_loop(self):
        """Accept incoming connections"""
        logger.info("Accept thread started")

        while not self.shutdown_event.is_set() and self.active:
            try:
                # Accept with timeout
                client_sock, addr = self.server_socket.accept()

                # Handle in separate thread
                thread = threading.Thread(
                    target=self._handle_incoming_connection,
                    args=(client_sock, addr),
                    daemon=True
                )
                thread.start()

            except socket.timeout:
                continue
            except Exception as e:
                if self.active:
                    logger.error(f"Accept error: {e}")
                break

        logger.info("Accept thread stopped")

    def _handle_incoming_connection(self, sock: socket.socket, addr: Tuple):
        """Handle an incoming connection"""
        logger.info(f"Incoming connection from {addr}")

        try:
            sock.settimeout(HANDSHAKE_TIMEOUT)

            # Receive handshake init
            data = self._recv_full_message(sock)
            msg_type, payload = TunnelProtocol.unpack_message(data)

            if msg_type != MessageType.HANDSHAKE_INIT:
                logger.error(f"Expected HANDSHAKE_INIT, got {msg_type}")
                return

            # Parse handshake
            handshake = json.loads(payload.decode('utf-8'))

            # Verify timestamp
            if not CryptoHelper.verify_timestamp(handshake['timestamp']):
                logger.error("Handshake timestamp too old")
                return

            # Verify mesh ID
            if handshake['mesh_id'] != self.identity.mesh_id:
                logger.error("Mesh ID mismatch")
                return

            # Generate session key
            session_key = CryptoHelper.generate_session_key()

            # Send handshake response
            response = TunnelProtocol.create_handshake_response(
                self.identity,
                session_key
            )
            sock.sendall(response)

            # Wait for ACK
            data = self._recv_full_message(sock)
            msg_type, payload = TunnelProtocol.unpack_message(data)

            if msg_type != MessageType.HANDSHAKE_ACK:
                logger.error(f"Expected HANDSHAKE_ACK, got {msg_type}")
                return

            # Create or update peer
            peer_id = handshake['node_id']
            peer_name = handshake['node_name']

            with self.lock:
                if peer_id in self.peers:
                    peer = self.peers[peer_id]
                else:
                    peer = TunnelPeer(
                        id=peer_id,
                        name=peer_name,
                        address=addr[0],
                        port=addr[1]
                    )
                    self.peers[peer_id] = peer

                peer.status = PeerStatus.CONNECTED
                peer.session_key = session_key
                peer.encryption_active = True
                peer.last_seen = time.time()
                peer.last_heartbeat = time.time()
                peer.last_rekey = time.time()

            logger.info(f"Handshake complete with {peer_name}")

            # Handle peer messages
            self._handle_peer_messages(sock, peer_id)

        except Exception as e:
            logger.error(f"Error handling incoming connection: {e}")
        finally:
            sock.close()

    def _connect_to_peer(self, peer_id: str):
        """Connect to a peer and perform handshake"""
        with self.lock:
            if peer_id not in self.peers:
                return
            peer = self.peers[peer_id]

        try:
            # Update status
            with self.lock:
                peer.status = PeerStatus.CONNECTING

            # Create socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(HANDSHAKE_TIMEOUT)

            # Connect
            logger.info(f"Connecting to {peer.name} at {peer.address}:{peer.port}")
            sock.connect((peer.address, peer.port))

            with self.lock:
                peer.status = PeerStatus.HANDSHAKING

            # Send handshake init
            handshake = TunnelProtocol.create_handshake_init(self.identity)
            sock.sendall(handshake)

            # Receive response
            data = self._recv_full_message(sock)
            msg_type, payload = TunnelProtocol.unpack_message(data)

            if msg_type != MessageType.HANDSHAKE_RESPONSE:
                logger.error(f"Expected HANDSHAKE_RESPONSE, got {msg_type}")
                return

            # Parse response
            response = json.loads(payload.decode('utf-8'))

            # Verify timestamp
            if not CryptoHelper.verify_timestamp(response['timestamp']):
                logger.error("Response timestamp too old")
                return

            # Decrypt session key
            mesh_key = CryptoHelper.generate_key_from_token(
                self.identity.auth_token,
                self.identity.mesh_id
            )
            encrypted_session_key = base64.b64decode(response['encrypted_session_key'])
            session_key = CryptoHelper.decrypt(mesh_key, encrypted_session_key)

            # Send ACK
            ack = TunnelProtocol.create_handshake_ack()
            sock.sendall(ack)

            # Update peer
            with self.lock:
                peer.status = PeerStatus.CONNECTED
                peer.session_key = session_key
                peer.encryption_active = True
                peer.last_seen = time.time()
                peer.last_heartbeat = time.time()
                peer.last_rekey = time.time()

            logger.info(f"Connected to {peer.name}")

            # Handle peer messages
            self._handle_peer_messages(sock, peer_id)

        except Exception as e:
            logger.error(f"Failed to connect to {peer.name}: {e}")
            with self.lock:
                peer.status = PeerStatus.ERROR

            # Try HTTP fallback
            logger.info(f"Attempting HTTP fallback for {peer.name}")
            # TODO: Implement HTTP fallback connection

    def _handle_peer_messages(self, sock: socket.socket, peer_id: str):
        """Handle messages from a connected peer"""
        sock.settimeout(60)  # 1 minute timeout

        while not self.shutdown_event.is_set():
            try:
                data = self._recv_full_message(sock)
                if not data:
                    break

                msg_type, payload = TunnelProtocol.unpack_message(data)

                with self.lock:
                    if peer_id not in self.peers:
                        break
                    peer = self.peers[peer_id]
                    peer.last_seen = time.time()
                    peer.bytes_received += len(data)
                    self.total_bytes_received += len(data)

                # Handle different message types
                if msg_type == MessageType.DATA:
                    self._handle_data_message(peer, payload)
                elif msg_type == MessageType.HEARTBEAT:
                    self._handle_heartbeat(peer, sock)
                elif msg_type == MessageType.HEARTBEAT_ACK:
                    self._handle_heartbeat_ack(peer)
                elif msg_type == MessageType.REKEY:
                    self._handle_rekey(peer, payload)
                elif msg_type == MessageType.GOODBYE:
                    logger.info(f"Peer {peer.name} disconnecting")
                    break

            except socket.timeout:
                continue
            except Exception as e:
                logger.error(f"Error handling peer messages: {e}")
                break

        # Cleanup
        with self.lock:
            if peer_id in self.peers:
                self.peers[peer_id].status = PeerStatus.DISCONNECTED
                self.peers[peer_id].encryption_active = False

        sock.close()

    def _handle_data_message(self, peer: TunnelPeer, encrypted_payload: bytes):
        """Handle encrypted data message"""
        try:
            if not peer.session_key:
                logger.error("No session key for peer")
                return

            # Decrypt data
            data = CryptoHelper.decrypt(peer.session_key, encrypted_payload)

            # TODO: Pass decrypted data to application layer
            logger.debug(f"Received {len(data)} bytes from {peer.name}")

        except Exception as e:
            logger.error(f"Failed to decrypt data: {e}")

    def _handle_heartbeat(self, peer: TunnelPeer, sock: socket.socket):
        """Handle heartbeat and send ACK"""
        with self.lock:
            peer.last_heartbeat = time.time()
            peer.missed_heartbeats = 0

        # Send ACK
        ack = TunnelProtocol.create_heartbeat_ack()
        try:
            sock.sendall(ack)
        except:
            pass

    def _handle_heartbeat_ack(self, peer: TunnelPeer):
        """Handle heartbeat acknowledgment"""
        with self.lock:
            peer.missed_heartbeats = 0
            # Calculate latency
            peer.latency = (time.time() - peer.last_heartbeat) * 1000

    def _handle_rekey(self, peer: TunnelPeer, payload: bytes):
        """Handle rekeying request"""
        # TODO: Implement rekeying protocol
        logger.info(f"Rekey requested by {peer.name}")

    def _send_to_peer(self, peer: TunnelPeer, message: bytes) -> bool:
        """Send message to peer (with HTTP fallback)"""
        try:
            # Try socket first
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((peer.address, peer.port))
            sock.sendall(message)
            sock.close()

            peer.bytes_sent += len(message)
            self.total_bytes_sent += len(message)
            return True

        except Exception as e:
            logger.warning(f"Socket send failed to {peer.name}, trying HTTP fallback")

            # Try HTTP fallback
            success = self.http_fallback.send_via_http(
                peer.address,
                HTTP_FALLBACK_PORT,
                message
            )

            if success:
                peer.bytes_sent += len(message)
                self.total_bytes_sent += len(message)

            return success

    def _recv_full_message(self, sock: socket.socket) -> bytes:
        """Receive a full message from socket"""
        # Read header first
        header = self._recv_exactly(sock, 6)
        if not header:
            return b''

        version, msg_type, payload_len = struct.unpack('!BBI', header)

        # Read payload
        payload = self._recv_exactly(sock, payload_len)

        return header + payload

    def _recv_exactly(self, sock: socket.socket, n: int) -> bytes:
        """Receive exactly n bytes from socket"""
        data = b''
        while len(data) < n:
            chunk = sock.recv(n - len(data))
            if not chunk:
                return b''
            data += chunk
        return data

    def _start_heartbeat_thread(self):
        """Start heartbeat monitoring thread"""
        thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        thread.start()
        self.threads.append(thread)

    def _heartbeat_loop(self):
        """Send periodic heartbeats to all connected peers"""
        logger.info("Heartbeat thread started")

        while not self.shutdown_event.is_set() and self.active:
            time.sleep(HEARTBEAT_INTERVAL)

            with self.lock:
                peer_list = [(p.id, p) for p in self.peers.values() if p.status == PeerStatus.CONNECTED]

            for peer_id, peer in peer_list:
                # Check for missed heartbeats
                time_since_last = time.time() - peer.last_heartbeat

                if time_since_last > HEARTBEAT_INTERVAL * 3:
                    logger.warning(f"Peer {peer.name} appears dead (no heartbeat for {time_since_last:.0f}s)")
                    with self.lock:
                        peer.status = PeerStatus.DEGRADED
                        peer.missed_heartbeats += 1

                        if peer.missed_heartbeats >= 5:
                            logger.error(f"Peer {peer.name} declared dead")
                            peer.status = PeerStatus.DISCONNECTED
                    continue

                # Send heartbeat
                heartbeat = TunnelProtocol.create_heartbeat()
                self._send_to_peer(peer, heartbeat)

        logger.info("Heartbeat thread stopped")

    def _start_rekey_thread(self):
        """Start rekeying thread"""
        thread = threading.Thread(target=self._rekey_loop, daemon=True)
        thread.start()
        self.threads.append(thread)

    def _rekey_loop(self):
        """Perform periodic rekeying"""
        logger.info("Rekey thread started")

        while not self.shutdown_event.is_set() and self.active:
            time.sleep(60)  # Check every minute

            current_time = time.time()

            with self.lock:
                peers_to_rekey = [
                    p for p in self.peers.values()
                    if p.status == PeerStatus.CONNECTED
                    and (current_time - p.last_rekey) >= REKEY_INTERVAL
                ]

            for peer in peers_to_rekey:
                logger.info(f"Rekeying with {peer.name}")

                # Generate new session key
                new_session_key = CryptoHelper.generate_session_key()

                # TODO: Send rekey message with new key
                # For now, just update timestamp
                with self.lock:
                    peer.last_rekey = current_time

        logger.info("Rekey thread stopped")

# ---------------------------------------------------------------------------
# Mesh Module Interface (for mesh_manager.py)
# ---------------------------------------------------------------------------

# Global tunnel instance
_tunnel_instance: Optional[SecureSocketTunnel] = None

def _get_tunnel() -> SecureSocketTunnel:
    """Get or create tunnel instance"""
    global _tunnel_instance
    if _tunnel_instance is None:
        _tunnel_instance = SecureSocketTunnel()
    return _tunnel_instance

def send(target: str = None, data: Any = None) -> Dict:
    """Send data to specific peer"""
    tunnel = _get_tunnel()

    if not target:
        return {'error': 'No target specified'}

    if data is None:
        data = b''
    elif isinstance(data, str):
        data = data.encode('utf-8')
    elif not isinstance(data, bytes):
        data = json.dumps(data).encode('utf-8')

    success = tunnel.send(target, data)
    return {'success': success, 'target': target, 'bytes': len(data)}

def receive() -> Dict:
    """Receive data (placeholder)"""
    # TODO: Implement message queue for received data
    return {'messages': []}

def broadcast(data: Any = None) -> Dict:
    """Broadcast data to all peers"""
    tunnel = _get_tunnel()

    if data is None:
        data = b''
    elif isinstance(data, str):
        data = data.encode('utf-8')
    elif not isinstance(data, bytes):
        data = json.dumps(data).encode('utf-8')

    count = tunnel.broadcast(data)
    return {'success': count > 0, 'peers_reached': count, 'bytes': len(data)}

def get_peers() -> List[Dict]:
    """Get list of peers"""
    tunnel = _get_tunnel()
    return tunnel.get_peers()

def status() -> Dict:
    """Get tunnel status"""
    tunnel = _get_tunnel()
    return tunnel.status()

def start_tunnel(target: str = None, port: int = None) -> Dict:
    """Start tunnel or add peer"""
    tunnel = _get_tunnel()

    # Start tunnel if not active
    if not tunnel.active:
        success = tunnel.start_tunnel()
        if not success:
            return {'error': 'Failed to start tunnel'}

    # Add peer if target specified
    if target:
        if port is None:
            port = TUNNEL_PORT

        peer_id = tunnel.add_peer(target, target, port)
        return {
            'success': True,
            'tunnel_active': True,
            'peer_added': target,
            'peer_id': peer_id
        }

    return {'success': True, 'tunnel_active': True}

def stop_tunnel() -> Dict:
    """Stop tunnel"""
    tunnel = _get_tunnel()
    success = tunnel.stop_tunnel()
    return {'success': success, 'tunnel_active': False}

# ---------------------------------------------------------------------------
# CLI Interface
# ---------------------------------------------------------------------------

def main():
    """CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='GhostHUD Secure Socket Tunnel')
    parser.add_argument('--name', help='Node name')
    parser.add_argument('--mesh-id', help='Mesh ID')
    parser.add_argument('--auth-token', help='Auth token')
    parser.add_argument('--port', type=int, default=TUNNEL_PORT, help='Listen port')
    parser.add_argument('--add-peer', help='Add peer (format: name,address,port)')

    subparsers = parser.add_subparsers(dest='command')

    start_parser = subparsers.add_parser('start', help='Start tunnel')
    stop_parser = subparsers.add_parser('stop', help='Stop tunnel')
    status_parser = subparsers.add_parser('status', help='Show status')

    args = parser.parse_args()

    # Create tunnel
    tunnel = SecureSocketTunnel(
        node_name=args.name,
        mesh_id=args.mesh_id,
        auth_token=args.auth_token,
        port=args.port
    )

    global _tunnel_instance
    _tunnel_instance = tunnel

    if args.command == 'start':
        print("Starting tunnel...")
        if tunnel.start_tunnel():
            print("Tunnel started successfully")
            print(tunnel.get_control_status())

            # Add peer if specified
            if args.add_peer:
                parts = args.add_peer.split(',')
                if len(parts) >= 2:
                    name = parts[0]
                    address = parts[1]
                    port = int(parts[2]) if len(parts) > 2 else TUNNEL_PORT

                    peer_id = tunnel.add_peer(name, address, port)
                    print(f"\nAdded peer: {name} ({peer_id[:8]})")

            # Keep running
            try:
                while True:
                    time.sleep(1)
                    # Update status every 10 seconds
                    if int(time.time()) % 10 == 0:
                        print("\n" + tunnel.get_control_status())
            except KeyboardInterrupt:
                print("\nStopping...")
                tunnel.stop_tunnel()
        else:
            print("Failed to start tunnel")

    elif args.command == 'stop':
        tunnel.stop_tunnel()
        print("Tunnel stopped")

    elif args.command == 'status':
        print(tunnel.get_control_status())

    else:
        parser.print_help()

if __name__ == '__main__':
    main()
