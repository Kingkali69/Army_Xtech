#!/usr/bin/env python3
"""
Mesh module wrapper for secure_socket_tunnel.py
This allows secure_socket_tunnel to work with mesh_manager.py
"""

# Simply re-export all functions from secure_socket_tunnel
from secure_socket_tunnel import (
    send,
    receive,
    broadcast,
    get_peers,
    status,
    start_tunnel,
    stop_tunnel
)

# Module metadata
__version__ = "1.0.0"
__description__ = "Secure socket tunnel with AES-256-GCM encryption"
