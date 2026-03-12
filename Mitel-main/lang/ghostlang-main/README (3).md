# GhostComms: Internet-Independent Operations

A robust communication system for GhostHUD that maintains operations even when internet connectivity is lost. This system provides multiple fallback mechanisms including mesh networking, USB sneakernet, and lo-fi communication channels.

## Components

1. **GhostFallbackDaemon**: Core daemon that handles automatic detection of connectivity loss and switches to alternative transport methods.

2. **GhostDrop_USB**: USB sneakernet transport for command and state carrier via portable drives.

3. **GhostPinger_LoFi**: Low-fidelity communication transport for critical commands when all other channels are unavailable.

4. **GhostComms**: Integration module that brings everything together into a cohesive system.

## Features

- Automatic detection of internet connectivity
- Seamless fallback between communication modes:
  - Internet (Normal mode)
  - Mesh-only (Local network only)
  - USB sneakernet (Air-gapped/isolated)
  - Lo-Fi channels (Last resort, minimal bandwidth)
- Command queuing, buffering, and replay
- USB drive auto-detection
- Heartbeat monitoring for node status
- End-to-end encryption for all transports
- Compatible with existing GhostHUD infrastructure

## Requirements

- Python 3.6+
- Standard libraries: socket, json, threading, etc.
- Optional: netifaces, miniupnpc, pystun3 (for better NAT traversal)
- Optional: qrcode, Pillow (for QR code functionality)

## Installation

1. Copy all `.py` files to your GhostHUD directory.

2. Install optional dependencies (for full functionality):

```bash
pip install netifaces miniupnpc pystun3 qrcode Pillow
```

## Usage

### Starting the GhostComms System

Start the integrated system with:

```bash
# For master node
python ghost_comms.py --node-id master_hostname --auth-key your_auth_key --data-dir /path/to/data

# For peer node
python ghost_comms.py --node-id peer_hostname --auth-key your_auth_key --data-dir /path/to/data --master-ip 192.168.1.235
```

### Using Individual Components

#### GhostFallbackDaemon

```bash
# Start the fallback daemon
python ghost_fallback_daemon.py --node-id your_node_id --auth-key your_auth_key --data-dir /path/to/data --master-ip 192.168.1.235
```

#### GhostDrop_USB

```bash
# Initialize a USB drive for GhostDrop
python ghost_drop_usb.py init --drive /media/usb_drive

# Monitor for drops
python ghost_drop_usb.py monitor --node-id your_node_id

# Create and deploy a command to USB
python ghost_drop_usb.py create --node-id your_node_id --type command --input command_data.json --output command.ghostcmd
python ghost_drop_usb.py deploy --input command.ghostcmd
```

#### GhostPinger_LoFi

```bash
# Start the lo-fi pinger
python ghost_pinger_lofi.py start --node-id your_node_id --role PEER --medium network

# Monitor for lo-fi commands
python ghost_pinger_lofi.py monitor --node-id your_node_id

# Send a lo-fi command
python ghost_pinger_lofi.py send --node-id your_node_id --type PING
```

## Command Types

The GhostComms system supports the following core command types:

1. `sync_all`: Trigger a full synchronization
2. `authority`: Grant or revoke authority to a node
3. `page_change`: Change the active page/view
4. `tool_activate`: Activate a specific tool
5. `fallback_test`: Test the fallback system
6. `fallback_ping`: Check if a node is alive
7. `fallback_status`: Get the status of a node
8. `fallback_echo`: Simple echo command
9. `fallback_mode`: Force a transport mode change

## Architecture

The system uses a layered approach to communication:

1. **Top layer**: GhostHUD API and user interface
2. **Middle layer**: GhostComms integration
3. **Bottom layer**: Transport mechanisms (Internet, Mesh, USB, Lo-Fi)

Data flows between nodes using the best available transport, automatically falling back to lower bandwidth methods as needed.

## Security

- All USB transports are encrypted
- Authentication tokens for all command verification
- Command signing for integrity
- USB drops require physical access (air gap security)

## Example: Handling Internet Outage

1. Internet connection goes down
2. GhostFallbackDaemon detects the outage
3. System switches to mesh-only mode
4. If mesh is unavailable, switches to USB mode
5. Commands are queued and transported via USB drives
6. When internet returns, queued commands are processed

## Future Extensions

- Radio-based transport (LoRa, Ham)
- Audio/visual channels for extreme scenarios
- Satellite uplink integration
- Mesh network expansion
- Mobile app integration

## Troubleshooting

- **Command not executing**: Check connectivity status and transport mode
- **USB drops not detected**: Ensure proper permissions on USB mount points
- **Lo-Fi not working**: Verify network port configuration
- **Peer not connecting**: Check authentication keys match

Use the `--help` flag with any command for specific options.
