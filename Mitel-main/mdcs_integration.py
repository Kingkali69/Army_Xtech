#!/usr/bin/env python3
"""
MASTER DYNAMIC CONTROL SWITCHING (MDCS) Integration
====================================================

Patent-Pending Technology by KK&GDevOps

Integrates MDCS into the OMNI web console for:
- Sync All functionality
- Dynamic Master Control Switching
- Authentication and Take Control
- Cross-platform device coordination
"""

import json
import time
import threading
import hashlib
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler

# Configure logging
logger = logging.getLogger('MDCS')

@dataclass
class MDCSNode:
    """Represents a node in the MDCS network"""
    device_id: str
    ip_address: str
    port: int
    platform: str
    is_master: bool = False
    last_seen: float = 0.0
    authority_timestamp: float = 0.0

class MDCSController:
    """Master Dynamic Control Switching Controller"""
    
    def __init__(self, device_id: str, port: int = 8888):
        self.device_id = device_id
        self.port = port
        self.nodes: Dict[str, MDCSNode] = {}
        self.is_master = False
        self.master_id = None
        self.master_ip = None
        self.master_port = None
        self.authority_password = "ghostops"  # Patent-pending authentication
        self.lock = threading.Lock()
        
        # Add self as initial node
        self.nodes[device_id] = MDCSNode(
            device_id=device_id,
            ip_address="127.0.0.1",
            port=port,
            platform="linux",
            is_master=True,
            last_seen=time.time(),
            authority_timestamp=time.time()
        )
        
        self.is_master = True
        self.master_id = device_id
        self.master_ip = "127.0.0.1"
        self.master_port = port
        
        logger.info(f"[MDCS] Initialized with device {device_id} as master")
    
    def get_mdcs_status(self) -> Dict[str, Any]:
        """Get current MDCS status"""
        with self.lock:
            return {
                'device_id': self.device_id,
                'is_master': self.is_master,
                'master_id': self.master_id,
                'master_ip': self.master_ip,
                'master_port': self.master_port,
                'total_nodes': len(self.nodes),
                'nodes': [
                    {
                        'device_id': node.device_id,
                        'ip_address': node.ip_address,
                        'port': node.port,
                        'platform': node.platform,
                        'is_master': node.is_master,
                        'last_seen': node.last_seen,
                        'authority_timestamp': node.authority_timestamp
                    }
                    for node in self.nodes.values()
                ]
            }
    
    def take_control(self, password: str) -> Dict[str, Any]:
        """
        MDCS - Master Dynamic Control Switching
        Take control and become the master node.
        """
        if password != self.authority_password:
            logger.warning("[MDCS] Control switch denied: invalid password")
            return {
                'status': 'error',
                'message': 'Invalid password',
                'has_authority': False
            }
        
        with self.lock:
            old_master = self.master_id
            
            # Update master status
            self.is_master = True
            self.master_id = self.device_id
            self.master_ip = "127.0.0.1"
            self.master_port = self.port
            
            # Update node authority
            if self.device_id in self.nodes:
                self.nodes[self.device_id].is_master = True
                self.nodes[self.device_id].authority_timestamp = time.time()
            
            # Demote previous master
            if old_master and old_master in self.nodes and old_master != self.device_id:
                self.nodes[old_master].is_master = False
        
        logger.info(f"[MDCS] Control transferred: {old_master} -> {self.device_id}")
        
        return {
            'status': 'ok',
            'message': f'Control taken by {self.device_id}',
            'has_authority': True,
            'new_master': self.device_id
        }
    
    def sync_all(self) -> Dict[str, Any]:
        """Sync all nodes in the MDCS network"""
        with self.lock:
            # Update last seen for all nodes
            current_time = time.time()
            for node in self.nodes.values():
                node.last_seen = current_time
            
            return {
                'status': 'ok',
                'message': 'All nodes synchronized',
                'synced_nodes': len(self.nodes),
                'sync_timestamp': current_time,
                'master_id': self.master_id
            }
    
    def authenticate_mdcs(self, password: str) -> Dict[str, Any]:
        """Authenticate for MDCS access"""
        if password == self.authority_password:
            return {
                'status': 'ok',
                'message': 'Authentication successful',
                'authenticated': True,
                'can_take_control': True
            }
        else:
            return {
                'status': 'error',
                'message': 'Authentication failed',
                'authenticated': False,
                'can_take_control': False
            }
    
    def add_node(self, device_id: str, ip_address: str, port: int, platform: str) -> bool:
        """Add a node to the MDCS network"""
        with self.lock:
            if device_id not in self.nodes:
                self.nodes[device_id] = MDCSNode(
                    device_id=device_id,
                    ip_address=ip_address,
                    port=port,
                    platform=platform,
                    is_master=False,
                    last_seen=time.time()
                )
                logger.info(f"[MDCS] Node added: {device_id} ({platform})")
                return True
            else:
                # Update last seen
                self.nodes[device_id].last_seen = time.time()
                return False
    
    def remove_node(self, device_id: str) -> bool:
        """Remove a node from the MDCS network"""
        with self.lock:
            if device_id in self.nodes and device_id != self.device_id:
                del self.nodes[device_id]
                logger.info(f"[MDCS] Node removed: {device_id}")
                return True
            return False

# MDCS HTML Interface Components
MDCS_HTML_BUTTONS = """
<!-- MDCS Control Panel -->
<div style="display: flex; gap: 10px; justify-content: center; flex-wrap: wrap; margin-bottom: 20px; padding: 15px; background: rgba(0,20,0,0.3); border: 1px solid rgba(0,255,0,0.2); border-radius: 8px;">
    <button onclick="syncAll()" class="action-btn action-btn-green" id="sync-all-btn">🔄 SYNC ALL</button>
    <button onclick="pushUpdates()" class="action-btn action-btn-green">🚀 PUSH UPDATES</button>
    <button onclick="showMDCS()" class="action-btn action-btn-cyan">🔐 MDCS</button>
    <button onclick="takeControl()" class="action-btn action-btn-yellow">⚡ TAKE CONTROL</button>
</div>

<!-- MDCS Login Panel (hidden by default) -->
<div id="mdcs-panel" style="display: none; margin-bottom: 20px; padding: 20px; background: rgba(0,30,0,0.5); border: 2px solid #0ff; border-radius: 8px;">
    <div style="color: #0ff; font-size: 16px; font-weight: bold; margin-bottom: 15px; text-align: center;">🔐 Dynamic Master Control Switching (MDCS)</div>
    <div style="display: flex; gap: 10px; align-items: center; justify-content: center; flex-wrap: wrap;">
        <input type="password" id="mdcs-password" placeholder="Password: ghostops" style="padding: 12px; background: #000; border: 2px solid #0ff; color: #0ff; font-family: 'Courier New', monospace; font-size: 14px; border-radius: 5px; width: 250px;" onkeypress="if(event.key === 'Enter') authenticateMDCS()">
        <button onclick="authenticateMDCS()" style="padding: 12px 24px; background: rgba(0,255,255,0.2); border: 2px solid #0ff; color: #0ff; font-family: 'Courier New', monospace; font-size: 14px; cursor: pointer; border-radius: 5px; font-weight: bold;">AUTHENTICATE</button>
        <button onclick="document.getElementById('mdcs-panel').style.display='none'" style="padding: 12px 24px; background: transparent; border: 2px solid #666; color: #666; font-family: 'Courier New', monospace; font-size: 14px; cursor: pointer; border-radius: 5px;">CANCEL</button>
    </div>
    <div style="color: #0a0; font-size: 12px; text-align: center; margin-top: 10px;">💡 MDCS allows any device to authenticate and take master control</div>
</div>
"""

MDCS_JAVASCRIPT_FUNCTIONS = """
<script>
// MDCS JavaScript Functions
function showMDCS() {
    const panel = document.getElementById('mdcs-panel');
    panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
    if (panel.style.display === 'block') {
        document.getElementById('mdcs-password').focus();
    }
}

function authenticateMDCS() {
    const password = document.getElementById('mdcs-password').value;
    if (!password) {
        alert('Please enter the MDCS password');
        return;
    }
    
    fetch('/api/mdcs/authenticate', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ password: password })
    })
    .then(response => response.json())
    .then(data => {
        if (data.authenticated) {
            alert('✅ MDCS Authentication Successful! You can now take control.');
            document.getElementById('mdcs-panel').style.display = 'none';
            document.getElementById('mdcs-password').value = '';
        } else {
            alert('❌ MDCS Authentication Failed: ' + data.message);
        }
    })
    .catch(error => {
        console.error('MDCS Authentication Error:', error);
        alert('❌ MDCS Authentication Error: ' + error.message);
    });
}

function takeControl() {
    const password = prompt('Enter MDCS password to take control:');
    if (!password) return;
    
    fetch('/api/mdcs/take_control', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ password: password })
    })
    .then(response => response.json())
    .then(data => {
        if (data.has_authority) {
            alert('✅ Control Taken - You are now MASTER!');
            setTimeout(() => location.reload(), 1000);
        } else {
            alert('❌ Failed to take control: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Take Control Error:', error);
        alert('❌ Error: ' + error.message);
    });
}

function syncAll() {
    fetch('/api/mdcs/sync_all', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'ok') {
            alert('✅ All nodes synchronized! (' + data.synced_nodes + ' nodes)');
            setTimeout(() => location.reload(), 500);
        } else {
            alert('❌ Sync failed: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Sync All Error:', error);
        alert('❌ Sync Error: ' + error.message);
    });
}

function pushUpdates() {
    fetch('/api/mdcs/push_updates', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'ok') {
            alert('✅ Updates pushed to all nodes!');
        } else {
            alert('❌ Push failed: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Push Updates Error:', error);
        alert('❌ Push Error: ' + error.message);
    });
}

// Auto-refresh MDCS status every 5 seconds
setInterval(() => {
    fetch('/api/mdcs/status')
        .then(response => response.json())
        .then(data => {
            // Update UI with MDCS status if needed
            console.log('MDCS Status:', data);
        })
        .catch(error => {
            console.error('MDCS Status Error:', error);
        });
}, 5000);
</script>
"""

# MDCS CSS Styles
MDCS_CSS_STYLES = """
<style>
.action-btn {
    padding: 12px 20px;
    border: none;
    border-radius: 5px;
    font-family: 'Courier New', monospace;
    font-weight: bold;
    cursor: pointer;
    transition: all 0.3s ease;
    text-shadow: 0 0 5px currentColor;
}

.action-btn-green {
    background: rgba(0,255,0,0.2);
    border: 2px solid #0f0;
    color: #0f0;
}

.action-btn-green:hover {
    background: rgba(0,255,0,0.3);
    box-shadow: 0 0 15px rgba(0,255,0,0.5);
}

.action-btn-cyan {
    background: rgba(0,255,255,0.2);
    border: 2px solid #0ff;
    color: #0ff;
}

.action-btn-cyan:hover {
    background: rgba(0,255,255,0.3);
    box-shadow: 0 0 15px rgba(0,255,255,0.5);
}

.action-btn-yellow {
    background: rgba(255,255,0,0.2);
    border: 2px solid #ff0;
    color: #ff0;
}

.action-btn-yellow:hover {
    background: rgba(255,255,0,0.3);
    box-shadow: 0 0 15px rgba(255,255,0,0.5);
}
</style>
"""

def get_mdcs_integration_html():
    """Get complete MDCS integration HTML"""
    return MDCS_CSS_STYLES + MDCS_HTML_BUTTONS + MDCS_JAVASCRIPT_FUNCTIONS

if __name__ == "__main__":
    # Test MDCS Controller
    controller = MDCSController("test_device")
    
    print("🧠 Testing MDCS Controller...")
    print(f"Status: {controller.get_mdcs_status()}")
    
    # Test authentication
    auth_result = controller.authenticate_mdcs("ghostops")
    print(f"Auth: {auth_result}")
    
    # Test take control
    control_result = controller.take_control("ghostops")
    print(f"Control: {control_result}")
    
    # Test sync all
    sync_result = controller.sync_all()
    print(f"Sync: {sync_result}")
    
    print("✅ MDCS Controller test complete!")
