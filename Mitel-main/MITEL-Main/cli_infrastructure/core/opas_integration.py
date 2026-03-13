#!/usr/bin/env python3
"""
OPAS Integration Layer
Connects OPAS to GhostHUD engine and HTTP adapter.
"""

import os
import json
from opas_core import OPAS, create_opas_http_handlers

def integrate_opas_with_engine(engine):
    work_dir = os.path.dirname(os.path.abspath(__file__))
    node_id = getattr(engine.config, 'device_id', None)
    
    opas = OPAS(work_dir=work_dir, node_id=node_id)
    
    if hasattr(engine, 'state') and hasattr(engine.state, 'nodes'):
        for device_id, node_info in engine.state.nodes.items():
            if device_id != node_id:
                opas.register_node(
                    node_id=device_id,
                    ip=node_info.get('ip', ''),
                    port=node_info.get('port', 7890),
                    platform=node_info.get('platform', 'unknown'),
                    ssh_user=node_info.get('ssh_user'),
                    ssh_port=node_info.get('ssh_port', 22)
                )
    
    opas.start()
    engine.opas = opas
    
    return opas


def add_opas_routes_to_adapter(adapter_class):
    original_do_get = adapter_class.do_GET
    original_do_post = adapter_class.do_POST
    
    def new_do_get(self):
        if hasattr(self, 'engine') and hasattr(self.engine, 'opas'):
            handle_get, _ = create_opas_http_handlers(self.engine.opas)
            result = handle_get(self.path)
            if result:
                self.send_json(result)
                return
        original_do_get(self)
    
    def new_do_post(self):
        if hasattr(self, 'engine') and hasattr(self.engine, 'opas'):
            _, handle_post = create_opas_http_handlers(self.engine.opas)
            if self.path.startswith('/opas/') or self.path == '/ui/resync':
                data = self.read_json() if self.headers.get('Content-Length') else {}
                result = handle_post(self.path, data)
                if result:
                    self.send_json(result)
                    return
        original_do_post(self)
    
    adapter_class.do_GET = new_do_get
    adapter_class.do_POST = new_do_post


# Node configuration - can be overridden via environment variable or config file
# Format: JSON string with node configurations
# Example: export GHOSTOPS_NODES_CONFIG='{"windows": {"ip": "192.168.1.235", ...}}'
import os
import json

def _load_nodes_config():
    """Load node configuration from environment or return empty dict"""
    config_json = os.environ.get('GHOSTOPS_NODES_CONFIG')
    if config_json:
        try:
            return json.loads(config_json)
        except json.JSONDecodeError:
            print("[OPAS] Warning: Invalid GHOSTOPS_NODES_CONFIG JSON, using empty config")
            return {}
    
    # Check for config file
    config_file = os.path.expanduser('~/.ghostops/nodes_config.json')
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"[OPAS] Warning: Could not load config file: {e}")
    
    return {}

# Load configuration (empty by default - nodes should be discovered/registered dynamically)
NODES_CONFIG = _load_nodes_config()


def setup_opas_standalone():
    work_dir = os.path.dirname(os.path.abspath(__file__))
    opas = OPAS(work_dir=work_dir)
    
    for name, info in NODES_CONFIG.items():
        opas.register_node(
            node_id=name,
            ip=info["ip"],
            port=info["port"],
            platform=info["platform"],
            ssh_user=info.get("ssh_user"),
            ssh_port=info.get("ssh_port", 22)
        )
    
    return opas


if __name__ == "__main__":
    opas = setup_opas_standalone()
    opas.start()
    
    print("[OPAS] Standalone mode - forcing full sync...")
    result = opas.force_sync()
    print(json.dumps(result, indent=2))
    
    opas.stop()

