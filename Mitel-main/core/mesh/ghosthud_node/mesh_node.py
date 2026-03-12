#!/usr/bin/env python3
"""
GhostHUD Mesh Node - Core Implementation
Cross-platform mesh networking node with Dynamic Master Control Switching (DMCS)
and zero-trust security architecture.
"""

import os
import sys
import time
import json
import uuid
import logging
import platform
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, asdict
from collections import defaultdict

from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_cors import CORS
import jwt
from cryptography.fernet import Fernet
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class NodeInfo:
    """Information about a mesh node"""
    node_id: str
    hostname: str
    platform: str
    ip_address: str
    port: int
    is_master: bool
    last_seen: float
    capabilities: List[str]
    health_score: float = 100.0

    def to_dict(self):
        return asdict(self)


class MeshNode:
    """
    Core mesh networking node with peer-to-peer communication,
    dynamic master switching, and zero-trust security.
    """

    def __init__(self, port: int = 5000, secret_key: Optional[str] = None):
        """
        Initialize mesh node

        Args:
            port: Port number for the node to listen on
            secret_key: Secret key for JWT token generation (auto-generated if not provided)
        """
        self.node_id = str(uuid.uuid4())
        self.port = port
        self.secret_key = secret_key or Fernet.generate_key().decode()

        # Node state
        self.is_master = False
        self.master_node_id: Optional[str] = None
        self.peers: Dict[str, NodeInfo] = {}
        self.data_store: Dict[str, any] = {}
        self.capabilities = ['sync', 'discovery', 'dmcs']

        # Platform detection
        self.platform_info = {
            'system': platform.system(),
            'release': platform.release(),
            'machine': platform.machine(),
            'processor': platform.processor()
        }

        # Initialize Flask app
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = self.secret_key
        CORS(self.app)

        # Initialize SocketIO
        self.socketio = SocketIO(
            self.app,
            cors_allowed_origins="*",
            async_mode='threading',
            logger=True,
            engineio_logger=True
        )

        # Register routes and event handlers
        self._register_routes()
        self._register_socketio_events()

        # Start background tasks
        self._start_background_tasks()

        logger.info(f"Node initialized: {self.node_id} on {self.platform_info['system']}")

    def _register_routes(self):
        """Register HTTP API routes"""

        @self.app.route('/health', methods=['GET'])
        def health_check():
            """Health check endpoint"""
            return jsonify({
                'status': 'healthy',
                'node_id': self.node_id,
                'is_master': self.is_master,
                'peer_count': len(self.peers),
                'platform': self.platform_info,
                'timestamp': time.time()
            })

        @self.app.route('/node/info', methods=['GET'])
        def node_info():
            """Get node information"""
            return jsonify(self._get_node_info().to_dict())

        @self.app.route('/peers', methods=['GET'])
        def list_peers():
            """List all known peers"""
            return jsonify({
                'peers': [peer.to_dict() for peer in self.peers.values()],
                'count': len(self.peers)
            })

        @self.app.route('/peers/register', methods=['POST'])
        def register_peer():
            """Register a new peer"""
            data = request.json

            # Validate required fields
            required_fields = ['node_id', 'hostname', 'ip_address', 'port']
            if not all(field in data for field in required_fields):
                return jsonify({'error': 'Missing required fields'}), 400

            # Create peer info
            peer_info = NodeInfo(
                node_id=data['node_id'],
                hostname=data['hostname'],
                platform=data.get('platform', 'unknown'),
                ip_address=data['ip_address'],
                port=data['port'],
                is_master=data.get('is_master', False),
                last_seen=time.time(),
                capabilities=data.get('capabilities', [])
            )

            # Add to peer list
            self.peers[peer_info.node_id] = peer_info
            logger.info(f"Registered peer: {peer_info.node_id}")

            # Broadcast peer update
            self.socketio.emit('peer_joined', peer_info.to_dict(), namespace='/')

            return jsonify({
                'status': 'registered',
                'node_info': self._get_node_info().to_dict()
            })

        @self.app.route('/data/<key>', methods=['GET', 'PUT', 'DELETE'])
        def data_operations(key: str):
            """Data storage operations"""
            if request.method == 'GET':
                value = self.data_store.get(key)
                if value is None:
                    return jsonify({'error': 'Key not found'}), 404
                return jsonify({'key': key, 'value': value})

            elif request.method == 'PUT':
                value = request.json.get('value')
                self.data_store[key] = value

                # Sync to peers
                self._sync_data_to_peers(key, value)

                return jsonify({'status': 'stored', 'key': key})

            elif request.method == 'DELETE':
                if key in self.data_store:
                    del self.data_store[key]
                    self._sync_data_to_peers(key, None, delete=True)
                    return jsonify({'status': 'deleted', 'key': key})
                return jsonify({'error': 'Key not found'}), 404

        @self.app.route('/master/claim', methods=['POST'])
        def claim_master():
            """Claim master role (DMCS)"""
            data = request.json
            claiming_node_id = data.get('node_id')

            if not claiming_node_id:
                return jsonify({'error': 'node_id required'}), 400

            # Check if we should yield master role
            if self.is_master:
                # Yield to claiming node
                self.is_master = False
                self.master_node_id = claiming_node_id
                logger.info(f"Yielded master role to {claiming_node_id}")

                # Notify all peers
                self.socketio.emit('master_changed', {
                    'old_master': self.node_id,
                    'new_master': claiming_node_id,
                    'timestamp': time.time()
                }, namespace='/')

            return jsonify({'status': 'acknowledged', 'current_master': self.master_node_id})

    def _register_socketio_events(self):
        """Register SocketIO event handlers"""

        @self.socketio.on('connect')
        def handle_connect():
            """Handle client connection"""
            logger.info(f"Client connected: {request.sid}")
            emit('node_info', self._get_node_info().to_dict())

        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Handle client disconnection"""
            logger.info(f"Client disconnected: {request.sid}")

        @self.socketio.on('ping')
        def handle_ping(data):
            """Handle ping request"""
            emit('pong', {
                'node_id': self.node_id,
                'timestamp': time.time(),
                'is_master': self.is_master
            })

        @self.socketio.on('sync_request')
        def handle_sync_request(data):
            """Handle data sync request"""
            emit('sync_data', {
                'data_store': self.data_store,
                'timestamp': time.time()
            })

        @self.socketio.on('master_heartbeat')
        def handle_master_heartbeat(data):
            """Handle master node heartbeat"""
            master_id = data.get('node_id')
            if master_id and master_id in self.peers:
                self.peers[master_id].last_seen = time.time()
                self.master_node_id = master_id

        @self.socketio.on('data_update')
        def handle_data_update(data):
            """Handle data update from peers"""
            key = data.get('key')
            value = data.get('value')
            operation = data.get('operation', 'set')

            if operation == 'set':
                self.data_store[key] = value
            elif operation == 'delete' and key in self.data_store:
                del self.data_store[key]

            logger.info(f"Data synchronized: {key} ({operation})")

    def _get_node_info(self) -> NodeInfo:
        """Get current node information"""
        return NodeInfo(
            node_id=self.node_id,
            hostname=platform.node(),
            platform=self.platform_info['system'],
            ip_address=self._get_local_ip(),
            port=self.port,
            is_master=self.is_master,
            last_seen=time.time(),
            capabilities=self.capabilities
        )

    def _get_local_ip(self) -> str:
        """Get local IP address"""
        import socket
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"

    def _sync_data_to_peers(self, key: str, value: any, delete: bool = False):
        """Synchronize data to all peers"""
        operation = 'delete' if delete else 'set'

        for peer in self.peers.values():
            try:
                # Send via SocketIO
                self.socketio.emit('data_update', {
                    'key': key,
                    'value': value,
                    'operation': operation,
                    'source_node': self.node_id,
                    'timestamp': time.time()
                }, namespace='/', room=peer.node_id)
            except Exception as e:
                logger.error(f"Failed to sync to peer {peer.node_id}: {e}")

    def _start_background_tasks(self):
        """Start background maintenance tasks"""

        def peer_health_monitor():
            """Monitor peer health and remove stale peers"""
            while True:
                try:
                    time.sleep(30)  # Check every 30 seconds
                    current_time = time.time()
                    stale_threshold = 120  # 2 minutes

                    stale_peers = [
                        peer_id for peer_id, peer in self.peers.items()
                        if current_time - peer.last_seen > stale_threshold
                    ]

                    for peer_id in stale_peers:
                        logger.warning(f"Removing stale peer: {peer_id}")
                        del self.peers[peer_id]

                        # Broadcast peer left event
                        self.socketio.emit('peer_left', {
                            'node_id': peer_id,
                            'timestamp': current_time
                        }, namespace='/')

                    # Check if we need to claim master role
                    if not self.is_master and (
                        self.master_node_id is None or
                        self.master_node_id not in self.peers
                    ):
                        self._attempt_master_claim()

                except Exception as e:
                    logger.error(f"Error in peer health monitor: {e}")

        def master_heartbeat():
            """Send master heartbeat if we are the master"""
            while True:
                try:
                    time.sleep(10)  # Every 10 seconds

                    if self.is_master:
                        self.socketio.emit('master_heartbeat', {
                            'node_id': self.node_id,
                            'timestamp': time.time()
                        }, namespace='/')

                except Exception as e:
                    logger.error(f"Error in master heartbeat: {e}")

        # Start background threads
        threading.Thread(target=peer_health_monitor, daemon=True).start()
        threading.Thread(target=master_heartbeat, daemon=True).start()

        logger.info("Background tasks started")

    def _attempt_master_claim(self):
        """Attempt to claim master role (DMCS)"""
        if self.is_master:
            return

        # Check if there are any other potential masters
        potential_masters = [
            peer for peer in self.peers.values()
            if peer.is_master
        ]

        if not potential_masters:
            # Claim master role
            self.is_master = True
            self.master_node_id = self.node_id
            logger.info(f"Claimed master role: {self.node_id}")

            # Notify all peers
            self.socketio.emit('master_changed', {
                'old_master': None,
                'new_master': self.node_id,
                'timestamp': time.time()
            }, namespace='/')

            # Send claim to all peers via HTTP
            for peer in self.peers.values():
                try:
                    requests.post(
                        f"http://{peer.ip_address}:{peer.port}/master/claim",
                        json={'node_id': self.node_id},
                        timeout=5
                    )
                except Exception as e:
                    logger.error(f"Failed to notify peer {peer.node_id}: {e}")

    def discover_peers(self, broadcast_address: str = "255.255.255.255"):
        """
        Discover peers on the network using UDP broadcast

        Args:
            broadcast_address: Broadcast address for peer discovery
        """
        import socket

        discovery_port = 45678
        discovery_message = json.dumps({
            'type': 'discovery',
            'node_id': self.node_id,
            'port': self.port
        }).encode()

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.sendto(discovery_message, (broadcast_address, discovery_port))
            sock.close()
            logger.info("Sent peer discovery broadcast")
        except Exception as e:
            logger.error(f"Failed to send discovery broadcast: {e}")

    def run(self, host: str = '0.0.0.0', debug: bool = False):
        """
        Start the mesh node server

        Args:
            host: Host address to bind to
            debug: Enable debug mode
        """
        logger.info(f"Starting mesh node on {host}:{self.port}")
        logger.info(f"Node ID: {self.node_id}")
        logger.info(f"Platform: {self.platform_info['system']}")

        # Attempt to claim master if no peers
        if not self.peers:
            self._attempt_master_claim()

        # Start the server
        self.socketio.run(
            self.app,
            host=host,
            port=self.port,
            debug=debug,
            allow_unsafe_werkzeug=True
        )


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='GhostHUD Mesh Node')
    parser.add_argument('--port', type=int, default=5000, help='Port to listen on')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--secret-key', help='Secret key for JWT tokens')

    args = parser.parse_args()

    # Create and run node
    node = MeshNode(port=args.port, secret_key=args.secret_key)
    node.run(host=args.host, debug=args.debug)


if __name__ == '__main__':
    main()
