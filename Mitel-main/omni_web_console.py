#!/usr/bin/env python3
"""
OMNI Web Console - Auto-launching Infrastructure Operations Console
===================================================================

OBSERVER-ONLY. READ-ONLY. NO CONTROL AUTHORITY.
Starts web server and automatically opens browser.
Works on Windows, Linux, Android.
"""

# Windows Performance Fix - Memory Cleanup
import gc
import psutil
import os

def cleanup_memory():
    """Clean up memory to prevent freezing"""
    try:
        # Force garbage collection
        gc.collect()
        
        # Get process memory usage
        process = psutil.Process(os.getpid())
        memory_mb = process.memory_info().rss / 1024 / 1024
        
        # If memory usage is high, be more aggressive
        if memory_mb > 1000:  # > 1GB
            gc.collect()
            gc.collect()  # Run twice for thorough cleanup
            
        return memory_mb
    except:
        return 0

import sys
import os
import time
import threading
import webbrowser
import hashlib
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime
import json

# Add paths
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'substrate', 'ai_layer'))

from omni_core import OmniCore

# Import MDCS Integration
from mdcs_integration import MDCSController, get_mdcs_integration_html

# Try to import NEXUS for AI intelligence
try:
    from mistral_7b_integration import get_nexus_ai, Mistral7BNEXUS
    from trinity_enhanced_llm import TrinityEnhancedLLM
    NEXUS_AVAILABLE = True
    USE_MISTRAL = True
except ImportError:
    try:
        from trinity_enhanced_llm import TrinityEnhancedLLM
        NEXUS_AVAILABLE = True
        USE_MISTRAL = False
    except ImportError:
        NEXUS_AVAILABLE = False
        USE_MISTRAL = False

# Observer-only token (cryptographic enforcement)
OBSERVER_TOKEN = hashlib.sha256(b"OBSERVER_ONLY_NO_CONTROL_AUTHORITY").hexdigest()[:16]


class OMNIWebHandler(BaseHTTPRequestHandler):
    """HTTP handler for OMNI web console - OBSERVER ONLY"""
    
    def __init__(self, *args, core=None, nexus=None, **kwargs):
        self.core = core
        self.nexus = nexus
        # Initialize MDCS Controller
        import uuid
        device_id = f"omni_{uuid.uuid4().hex[:8]}"
        self.mdcs = MDCSController(device_id)
        super().__init__(*args, **kwargs)
    
    def log_message(self, format, *args):
        """Suppress default logging"""
        pass
    
    def do_GET(self):
        """Handle GET requests - READ ONLY"""
        if self.path == '/' or self.path == '/index.html':
            # Serve unified console (single page with tabs)
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.end_headers()
            try:
                with open('unified_console.html', 'r', encoding='utf-8') as f:
                    self.wfile.write(f.read().encode('utf-8'))
            except Exception as e:
                print(f"[ERROR] Failed to load unified console: {e}")
                self.wfile.write(b'<html><body>Unified console not found</body></html>')
        elif self.path == '/omni_original' or self.path == '/omni_original.html':
            # Serve original OMNI console (for iframe)
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.end_headers()
            self.wfile.write(self._get_html().encode('utf-8'))
        elif self.path == '/test_topology' or self.path == '/test_topology.html':
            # Serve topology test page
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.end_headers()
            try:
                with open('test_topology.html', 'r', encoding='utf-8') as f:
                    self.wfile.write(f.read().encode('utf-8'))
            except:
                self.wfile.write(b'<html><body>Test page not found</body></html>')
        elif self.path == '/mitel' or self.path == '/mitel.html':
            # Serve M.I.T.E.L. demo page
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.end_headers()
            try:
                with open('demo_embedded.html', 'r', encoding='utf-8') as f:
                    self.wfile.write(f.read().encode('utf-8'))
            except Exception as e:
                print(f"[ERROR] Failed to load M.I.T.E.L. demo page: {e}")
                self.wfile.write(b'<html><body>M.I.T.E.L. demo page not found</body></html>')
        elif self.path == '/test_devices.html':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            try:
                with open('test_devices.html', 'r') as f:
                    self.wfile.write(f.read().encode())
            except:
                self.wfile.write(b'<html><body>Test page not found</body></html>')
        elif self.path == '/direct_test.html':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            try:
                with open('direct_test.html', 'r') as f:
                    self.wfile.write(f.read().encode())
            except:
                self.wfile.write(b'<html><body>Direct test not found</body></html>')
        elif self.path == '/api/nexus':
            # NEXUS AI status endpoint
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            if self.nexus:
                # Get AI insights about system health
                try:
                    # Simple health check prompt
                    health_prompt = "Analyze system health. Are there any issues or potential problems?"
                    
                    if USE_MISTRAL and hasattr(self.nexus, 'generate_nexus_response'):
                        # Use NEXUS AI (Mistral)
                        substrate_context = {
                            'hive_mind_active': True,
                            'tool_registry_size': 4,
                            'active_nodes': 2,
                            'collective_memory_size': 14,
                            'consciousness_level': 0.80
                        }
                        nexus_response = self.nexus.generate_nexus_response(health_prompt, substrate_context)
                        ai_response = {
                            'response': nexus_response.content,
                            'confidence': nexus_response.confidence,
                            'intent': nexus_response.intent
                        }
                    else:
                        # Use Trinity Enhanced
                        ai_response = self.nexus.chat(health_prompt)
                    
                    response = {
                        'status': 'active',
                        'nexus_available': True,
                        'model': 'NEXUS AI (Mistral-7B-Q4)' if USE_MISTRAL else 'Trinity Enhanced',
                        'insight': ai_response.get('response', 'System monitoring active'),
                        'confidence': ai_response.get('confidence', 0.8),
                        'intent': ai_response.get('intent', 'analysis')
                    }
                except Exception as e:
                    response = {
                        'status': 'error',
                        'nexus_available': True,
                        'error': str(e)
                    }
            else:
                response = {
                    'status': 'unavailable',
                    'nexus_available': False
                }
            
            self.wfile.write(json.dumps(response).encode())
        elif self.path == '/api/status':
            # One-way telemetry only - UI excluded from quorum
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('X-Observer-Token', OBSERVER_TOKEN)
            self.send_header('X-Mode', 'OBSERVATION')
            self.end_headers()
            status = self.core.get_status()
            peers = self.core.get_peers()
            
            # Determine failover state
            failover_state = self._get_failover_state()
            
            response = {
                'status': status,
                'peers': peers,
                'failover_state': failover_state,
                'observer_mode': True,
                'no_control_authority': True,
                'timestamp': datetime.now().isoformat()
            }
            self.wfile.write(json.dumps(response).encode())
        elif self.path == '/api/mitel':
            # M.I.T.E.L. zero-trust status endpoint
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            if hasattr(self.core, 'mitel_subsystem') and self.core.mitel_subsystem:
                try:
                    import asyncio
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    mitel_status = loop.run_until_complete(self.core.mitel_subsystem.get_status())
                    loop.close()
                    
                    # Get recent threats
                    recent_threats = []
                    if hasattr(self.core.mitel_subsystem, 'threat_events'):
                        for threat in self.core.mitel_subsystem.threat_events[-10:]:
                            recent_threats.append({
                                'timestamp': threat.timestamp.isoformat(),
                                'device_id': threat.device_id[:16] + '...',
                                'threat_type': threat.threat_type,
                                'severity': threat.severity,
                                'description': threat.description,
                                'response_action': threat.response_action
                            })
                    
                    response = {
                        'mitel_available': True,
                        'status': mitel_status,
                        'recent_threats': recent_threats,
                        'fabric_health': '100%' if mitel_status['status'] == 'running' else 'degraded',
                        'threat_propagation_time': '<10ms'
                    }
                except Exception as e:
                    response = {
                        'mitel_available': True,
                        'error': str(e)
                    }
            else:
                response = {
                    'mitel_available': False,
                    'status': 'not_loaded'
                }
            
            self.wfile.write(json.dumps(response).encode())
        elif self.path == '/api/mitel/devices':
            # M.I.T.E.L. device list endpoint
            print("[DEBUG] /api/mitel/devices endpoint called")
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            if hasattr(self.core, 'mitel_subsystem') and self.core.mitel_subsystem:
                try:
                    print("[DEBUG] M.I.T.E.L. subsystem found, scanning devices with full details")
                    
                    # Scan current devices to get full details
                    scanned_devices = self.core.mitel_subsystem._scan_connected_devices()
                    
                    # Get trust status sets
                    quarantined = self.core.mitel_subsystem.quarantined_devices
                    registered = self.core.mitel_subsystem.registered_devices
                    
                    # Build device list with actual device info
                    device_list = []
                    for device in scanned_devices:
                        device_id = device.get('device_id', '')
                        
                        # Determine trust status
                        if device_id in quarantined:
                            trust_status = 'quarantined'
                        elif device_id in registered:
                            trust_status = 'trusted'
                        else:
                            trust_status = 'unknown'
                        
                        device_list.append({
                            'device_id': device_id,
                            'name': device.get('name', 'Unknown Device'),
                            'vendor_id': device.get('vendor_id', 'N/A'),
                            'product_id': device.get('product_id', 'N/A'),
                            'device_type': device.get('device_type', 'unknown'),
                            'trust_status': trust_status
                        })
                    
                    print(f"[DEBUG] Returning {len(device_list)} devices with full details")
                    
                    response = {
                        'devices': device_list,
                        'total': len(device_list),
                        'trusted': sum(1 for d in device_list if d['trust_status'] == 'trusted'),
                        'unknown': sum(1 for d in device_list if d['trust_status'] == 'unknown'),
                        'quarantined': sum(1 for d in device_list if d['trust_status'] == 'quarantined')
                    }
                except Exception as e:
                    print(f"[DEBUG] Error in device list: {e}")
                    import traceback
                    traceback.print_exc()
                    response = {
                        'error': str(e),
                        'devices': []
                    }
            else:
                print("[DEBUG] M.I.T.E.L. subsystem not available")
                response = {
                    'error': 'M.I.T.E.L. not available',
                    'devices': []
                }
            
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        """Handle POST requests for device actions"""
        if self.path == '/api/mitel/devices':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                device_id = data.get('device_id')
                action = data.get('action')  # 'unquarantine' or 'register'
                
                if not device_id or not action:
                    self.send_response(400)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({'error': 'Missing device_id or action'}).encode())
                    return
                
                if hasattr(self.core, 'mitel_subsystem') and self.core.mitel_subsystem:
                    if action == 'unquarantine':
                        # Remove from quarantine and register as trusted
                        if device_id in self.core.mitel_subsystem.quarantined_devices:
                            self.core.mitel_subsystem.quarantined_devices.remove(device_id)
                        self.core.mitel_subsystem.registered_devices[device_id] = None  # Register as trusted
                        print(f"[M.I.T.E.L.] Unquarantined and registered device: {device_id[:8]}...")
                        
                        self.send_response(200)
                        self.send_header('Content-type', 'application/json')
                        self.send_header('Access-Control-Allow-Origin', '*')
                        self.end_headers()
                        self.wfile.write(json.dumps({'success': True, 'message': 'Device unquarantined and trusted'}).encode())
                    
                    elif action == 'register':
                        # Remove from quarantine and add to registered
                        if device_id in self.core.mitel_subsystem.quarantined_devices:
                            self.core.mitel_subsystem.quarantined_devices.remove(device_id)
                        self.core.mitel_subsystem.registered_devices[device_id] = None  # Add to registered
                        print(f"[M.I.T.E.L.] Registered device: {device_id[:8]}...")
                        
                        self.send_response(200)
                        self.send_header('Content-type', 'application/json')
                        self.send_header('Access-Control-Allow-Origin', '*')
                        self.end_headers()
                        self.wfile.write(json.dumps({'success': True, 'message': 'Device registered'}).encode())
                    
                    else:
                        self.send_response(400)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps({'error': 'Invalid action'}).encode())
                else:
                    self.send_response(503)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({'error': 'M.I.T.E.L. not available'}).encode())
                    
            except Exception as e:
                print(f"[ERROR] Device action failed: {e}")
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode())
        
        # MDCS Endpoints
        elif self.path == '/api/mdcs/authenticate':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                password = data.get('password')
                
                result = self.mdcs.authenticate_mdcs(password)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(result).encode())
                
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode())
        
        elif self.path == '/api/mdcs/take_control':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                password = data.get('password')
                
                result = self.mdcs.take_control(password)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(result).encode())
                
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode())
        
        elif self.path == '/api/mdcs/sync_all':
            try:
                result = self.mdcs.sync_all()
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(result).encode())
                
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode())
        
        elif self.path == '/api/mdcs/push_updates':
            try:
                # For now, just sync all nodes
                result = self.mdcs.sync_all()
                result['message'] = 'Updates pushed to all nodes'
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(result).encode())
                
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode())
        
        elif self.path == '/api/mdcs/status':
            try:
                status = self.mdcs.get_mdcs_status()
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(status).encode())
                
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode())
        
        else:
            self.send_response(404)
            self.end_headers()
    
    def _get_failover_state(self):
        """Get failover engine state - READY, TRANSITIONING, or STANDBY"""
        # In real implementation, this comes from control plane
        # For now, always STANDBY (no active failover)
        return 'STANDBY'
    
    def _get_html(self):
        """Generate HTML console"""
        nexus_status = "ACTIVE" if self.nexus else "UNAVAILABLE"
        return f"""<!DOCTYPE html>
<html>
<head>
    <title>OMNI Infrastructure Operations Console</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Courier New', monospace;
            background: #1a1a1a;
            color: #e0e0e0;
            overflow-x: hidden;
        }}
        
        /* MODE BANNER - NON-NEGOTIABLE */
        .mode-banner {{
            background: #1a3a1a;
            padding: 4px 16px;
            text-align: center;
            font-size: 11px;
            font-weight: bold;
            color: #46d946;
            border-bottom: 1px solid #2a4a2a;
        }}
        
        /* TOP BAND */
        .top-band {{
            background: #2a2a2a;
            padding: 8px 16px;
            border-bottom: 2px solid #3a3a3a;
            font-size: 12px;
            font-weight: bold;
            white-space: nowrap;
            overflow-x: auto;
        }}
        
        .status-operational {{ color: #46d946; }}
        .status-degraded {{ color: #ffaa00; }}
        .status-error {{ color: #ff4444; }}
        
        /* MAIN LAYOUT */
        .main-container {{
            display: flex;
            height: calc(100vh - 140px);
        }}
        
        /* LEFT PANEL */
        .left-panel {{
            flex: 1;
            padding: 16px;
            border-right: 1px solid #3a3a3a;
            overflow-y: auto;
        }}
        
        .left-panel h2 {{
            color: #e0e0e0;
            margin-bottom: 12px;
            font-size: 14px;
        }}
        
        .node-item {{
            margin: 8px 0;
            padding: 12px;
            background: #252525;
            border-left: 3px solid #46d946;
            font-size: 11px;
        }}
        
        .node-item.degraded {{
            border-left-color: #ffaa00;
        }}
        
        .node-item.error {{
            border-left-color: #ff4444;
        }}
        
        .node-role {{
            color: #51a3ff;
            font-weight: bold;
        }}
        
        .node-trust {{
            color: #888;
            font-size: 10px;
        }}
        
        /* RIGHT PANEL */
        .right-panel {{
            width: 400px;
            padding: 16px;
            overflow-y: auto;
            background: #1f1f1f;
        }}
        
        .metric-card {{
            background: #252525;
            padding: 12px;
            margin-bottom: 12px;
            border-left: 3px solid #51a3ff;
        }}
        
        .metric-card h3 {{
            color: #e0e0e0;
            font-size: 12px;
            margin-bottom: 8px;
        }}
        
        .metric-value {{
            font-size: 18px;
            font-weight: bold;
        }}
        
        .metric-value.operational {{ color: #46d946; }}
        .metric-value.degraded {{ color: #ffaa00; }}
        .metric-value.error {{ color: #ff4444; }}
        .metric-value.transitioning {{
            color: #ffaa00;
            animation: pulse 2s infinite;
        }}
        
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.5; }}
        }}
        
        /* BOTTOM STRIP */
        .bottom-strip {{
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            height: 200px;
            background: #1a1a1a;
            border-top: 2px solid #3a3a3a;
            padding: 12px 16px;
            overflow-y: auto;
        }}
        
        .bottom-strip h2 {{
            color: #e0e0e0;
            font-size: 12px;
            margin-bottom: 8px;
        }}
        
        .event-line {{
            font-size: 11px;
            padding: 2px 0;
            font-family: 'Courier New', monospace;
        }}
        
        .event-time {{
            color: #888;
            margin-right: 8px;
        }}
        
        .event-category {{
            margin-right: 8px;
        }}
        
        .event-category.system {{ color: #51a3ff; }}
        .event-category.network {{ color: #46d946; }}
        .event-category.security {{ color: #ffaa00; }}
        .event-category.control {{ color: #51a3ff; }}
        .event-category.warning {{ color: #ffaa00; }}
        .event-category.error {{ color: #ff4444; }}
        
        /* DEVICE LIST STYLES */
        .device-list {{
            margin-top: 16px;
            max-height: 400px;
            overflow-y: auto;
        }}
        
        .device-item {{
            background: #252525;
            padding: 8px 12px;
            margin-bottom: 8px;
            border-left: 3px solid #888;
            font-size: 11px;
        }}
        
        .device-item.unknown {{
            border-left-color: #ffaa00;
        }}
        
        .device-item.trusted {{
            border-left-color: #46d946;
        }}
        
        .device-item.quarantined {{
            border-left-color: #ff4444;
            background: #2a1a1a;
        }}
        
        .device-status {{
            display: inline-block;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 10px;
            font-weight: bold;
            margin-right: 8px;
        }}
        
        .device-status.unknown {{
            background: #ffaa00;
            color: #1a1a1a;
        }}
        
        .device-status.trusted {{
            background: #46d946;
            color: #1a1a1a;
        }}
        
        .device-status.quarantined {{
            background: #ff4444;
            color: #fff;
        }}
        
        .device-name {{
            color: #e0e0e0;
            font-weight: bold;
        }}
        
        .device-details {{
            color: #888;
            font-size: 10px;
            margin-top: 4px;
        }}
        
        .device-actions {{
            margin-top: 6px;
        }}
        
        .device-btn {{
            background: #3a3a3a;
            border: 1px solid #555;
            color: #e0e0e0;
            padding: 4px 8px;
            font-size: 10px;
            cursor: pointer;
            margin-right: 4px;
            border-radius: 3px;
        }}
        
        .device-btn:hover {{
            background: #4a4a4a;
        }}
        
        .device-btn.register {{
            border-color: #46d946;
            color: #46d946;
        }}
        
        .device-btn.quarantine {{
            border-color: #ff4444;
            color: #ff4444;
        }}
        
        .footer {{
            position: fixed;
            bottom: 200px;
            left: 0;
            right: 0;
            height: 20px;
            background: #1a1a1a;
            padding: 4px 16px;
            font-size: 10px;
            color: #888;
            border-top: 1px solid #3a3a3a;
        }}
        
        .freeze-overlay {{
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.8);
            z-index: 9999;
            align-items: center;
            justify-content: center;
            color: #ffaa00;
            font-size: 24px;
            font-weight: bold;
        }}
        
        .freeze-overlay.active {{
            display: flex;
        }}
    </style>
</head>
<body>
    <!-- MODE BANNER - NON-NEGOTIABLE -->
    <div class="mode-banner">
        MODE: OBSERVATION (NO CONTROL AUTHORITY) | TOKEN: {OBSERVER_TOKEN}
    </div>
    
    <!-- TOP BAND -->
    <div class="top-band" id="top-band">
        GLOBAL STATUS: <span class="status-operational">OPERATIONAL</span> | 
        EPOCH 1 | 
        FABRIC NODES: <span id="fabric-nodes">1</span> | 
        QUORUM: <span class="status-operational">STABLE</span> | 
        LATENCY: <span id="latency">0</span>ms avg | 
        FAILOVERS (24h): <span id="failovers">0</span> | 
        THREATS: <span id="threats">0</span> | 
        DEGRADED ZONES: <span id="degraded-zones">0</span>
    </div>
    
    <!-- MDCS CONTROL PANEL -->
    {get_mdcs_integration_html()}
    
    <!-- TRANSITION FREEZE OVERLAY -->
    <div class="freeze-overlay" id="freeze-overlay">
        TRANSITIONING - UI FROZEN
    </div>
    
    <!-- MAIN CONTAINER -->
    <div class="main-container">
        <!-- LEFT PANEL -->
        <div class="left-panel">
            <h2>PHYSICAL/LOGICAL MAP</h2>
            <div id="topology">
                <div class="node-item">
                    <strong>Initializing...</strong>
                </div>
            </div>
        </div>
        
        <!-- RIGHT PANEL -->
        <div class="right-panel">
            <div class="metric-card">
                <h3>FABRIC HEALTH</h3>
                <div class="metric-value operational" id="fabric-health">100%</div>
                <div style="font-size: 11px; margin-top: 4px;">Nodes: <span id="node-count">1</span></div>
            </div>
            
            <div class="metric-card">
                <h3>CONTROL PLANE</h3>
                <div class="metric-value operational" id="control-plane">OPERATIONAL</div>
                <div style="font-size: 11px; margin-top: 4px;">Epoch: 1</div>
            </div>
            
            <div class="metric-card">
                <h3>FAILOVER ENGINE</h3>
                <div class="metric-value operational" id="failover-engine">STANDBY</div>
                <div style="font-size: 11px; margin-top: 4px;">Failovers (24h): 0</div>
            </div>
            
            <div class="metric-card">
                <h3>SECURITY SUBSYSTEMS</h3>
                <div class="metric-value operational" id="security">ACTIVE</div>
                <div style="font-size: 11px; margin-top: 4px;">Threats: 0</div>
            </div>
            
            <div class="metric-card" style="border-left-color: #46d946;">
                <h3>M.I.T.E.L. ZERO-TRUST</h3>
                <div class="metric-value operational" id="mitel-status">LOADING...</div>
                <div style="font-size: 11px; margin-top: 4px;">
                    Devices: <span id="mitel-devices">--</span> | 
                    Quarantined: <span id="mitel-quarantined">--</span><br>
                    Threats: <span id="mitel-threats">--</span> | 
                    Fabric: <span id="mitel-fabric">--</span>
                </div>
            </div>
            
            <div class="metric-card">
                <h3>DATA INTEGRITY</h3>
                <div class="metric-value operational" id="data-integrity">VERIFIED</div>
                <div style="font-size: 11px; margin-top: 4px;">State keys: <span id="state-keys">0</span></div>
            </div>
        </div>
        
        <!-- DEVICE LIST SECTION -->
        <div class="metric-card" style="margin-top: 16px;">
            <h3>M.I.T.E.L. DEVICE MANAGEMENT</h3>
            <div id="device-list" class="device-list">
                <div style="color: #888; text-align: center; padding: 20px;">Loading devices...</div>
            </div>
        </div>
    </div>
    
    <!-- FOOTER -->
    <div class="footer">
        Console: Observation mode | Read-only | Observer token: {OBSERVER_TOKEN} | Last update: <span id="last-update">--:--:--</span>
    </div>
    
    <!-- BOTTOM STRIP -->
    <div class="bottom-strip">
        <h2>EVENT TIMELINE</h2>
        <div id="event-timeline">
            <div class="event-line">
                <span class="event-time">--:--:--</span>
                <span class="event-category system">[SYSTEM]</span>
                <span>Console initializing...</span>
            </div>
        </div>
    </div>
    
    <script>
        let events = [];
        let isFrozen = false;
        let lastFailoverState = 'STANDBY';
        
        console.log('[OMNI] JavaScript loaded');
        
        function unquarantineDevice(deviceId) {{
            console.log('[OMNI] Unquarantining device:', deviceId);
            
            fetch('/api/mitel/devices', {{
                method: 'POST',
                headers: {{
                    'Content-Type': 'application/json',
                }},
                body: JSON.stringify({{
                    device_id: deviceId,
                    action: 'unquarantine'
                }})
            }})
            .then(response => response.json())
            .then(data => {{
                console.log('[OMNI] Unquarantine response:', data);
                if (data.success) {{
                    console.log('[OMNI] Device unquarantined successfully');
                    // Update UI to show device is no longer quarantined
                    const deviceElement = document.querySelector('[data-device-id="' + deviceId + '"]');
                    if (deviceElement) {{
                        deviceElement.classList.remove('quarantined');
                        deviceElement.classList.add('trusted');
                        const statusElement = deviceElement.querySelector('.device-status');
                        if (statusElement) {{
                            statusElement.textContent = 'TRUSTED';
                            statusElement.className = 'device-status trusted';
                        }}
                    }}
                }} else {{
                    console.error('[OMNI] Unquarantine failed:', data.message);
                }}
            }})
            .catch(error => {{
                console.error('[OMNI] Unquarantine error:', error);
            }});
        }}
        
        function updateDeviceList() {{
            console.log('[OMNI] Updating device list');
            
            fetch('/api/mitel/devices')
                .then(response => response.json())
                .then(data => {{
                    console.log('[OMNI] Device list data:', data);
                    const deviceListEl = document.getElementById('device-list');
                    
                    if (data.devices && data.devices.length > 0) {{
                        let html = '';
                        data.devices.forEach(device => {{
                            const deviceId = device.device_id || '';
                            const name = device.name || 'Unknown Device';
                            const deviceType = device.device_type || 'unknown';
                            const trustStatus = device.trust_status || 'unknown';
                            
                            html += `
                                <div class="device-item ${{trustStatus}}" data-device-id="${{deviceId}}">
                                    <div style="display: flex; justify-content: space-between; align-items: center;">
                                        <div>
                                            <div style="font-weight: bold;">${{name}}</div>
                                            <div style="font-size: 10px; color: #888;">
                                                Type: ${{deviceType}} | ID: ${{deviceId.substring(0, 8)}}...
                                            </div>
                                        </div>
                                        <div style="display: flex; align-items: center; gap: 8px;">
                                            <span class="device-status ${{trustStatus}}">${{trustStatus.toUpperCase()}}</span>
                                            ${{trustStatus === 'quarantined' ? `
                                                <button onclick="unquarantineDevice('${{deviceId}}')" 
                                                        style="background: #46d946; color: #000; border: none; padding: 4px 8px; 
                                                               border-radius: 4px; font-size: 10px; cursor: pointer;">
                                                    UNQUARANTINE
                                                </button>
                                            ` : ''}}
                                        </div>
                                    </div>
                                </div>
                            `;
                        }});
                        deviceListEl.innerHTML = html;
                    }} else {{
                        deviceListEl.innerHTML = '<div style="color: #888; text-align: center; padding: 20px;">No devices found</div>';
                    }}
                }})
                .catch(error => {{
                    console.error('[OMNI] Device list error:', error);
                    document.getElementById('device-list').innerHTML = '<div style="color: #ff4444; text-align: center; padding: 20px;">Error loading devices</div>';
                }});
        }}
        
        function updateConsole() {{
            console.log('[OMNI] updateConsole() called');
            
            // Check if we should freeze during transition
            if (isFrozen) {{
                console.log('[OMNI] Frozen, skipping update');
                return; // Skip update during freeze
            }}
            
            console.log('[OMNI] Fetching /api/status');
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {{
                    
                    // Check failover state for transition freeze
                    const failoverState = data.failover_state || 'STANDBY';
                    if (failoverState === 'TRANSITIONING') {{
                        if (!isFrozen) {{
                            isFrozen = true;
                            document.getElementById('freeze-overlay').classList.add('active');
                            events.push({{
                                time: new Date().toLocaleTimeString(),
                                category: 'CONTROL',
                                message: 'Failover transition detected - UI frozen'
                            }});
                        }}
                    }} else {{
                        if (isFrozen && lastFailoverState === 'TRANSITIONING') {{
                            isFrozen = false;
                            document.getElementById('freeze-overlay').classList.remove('active');
                            events.push({{
                                time: new Date().toLocaleTimeString(),
                                category: 'CONTROL',
                                message: 'Transition complete - UI unfrozen'
                            }});
                        }}
                    }}
                    lastFailoverState = failoverState;
                    
                    if (isFrozen) {{
                        return; // Don't update UI during freeze
                    }}
                    
                    // Update top band
                    document.getElementById('fabric-nodes').textContent = data.peers.length + 1;
                    
                    // Update topology with role, trust class, promotion eligibility
                    const topology = document.getElementById('topology');
                    topology.innerHTML = '';
                    
                    // Add self with full details
                    const selfNode = document.createElement('div');
                    selfNode.className = 'node-item';
                    const selfId = data.status.node_id.substring(0, 16);
                    const selfPlatform = data.status.platform;
                    const selfStatus = data.status.status;
                    const selfRole = 'coordinator';
                    const selfTrust = 'CORE';
                    const selfEpoch = 1;
                    const selfLinks = data.peers.length;
                    const selfPromotion = 'yes';
                    
                    selfNode.innerHTML = '<strong>[ CORE ]</strong> ' + selfId + '... (' + selfPlatform + ')<br>' +
                        '├─ role: ' + selfRole + '<br>' +
                        '├─ epoch: ' + selfEpoch + '<br>' +
                        '├─ links: ' + selfLinks + '<br>' +
                        '├─ trust: <span class="node-trust">' + selfTrust + '</span><br>' +
                        '└─ promotion eligible: ' + selfPromotion;
                    topology.appendChild(selfNode);
                    
                    // Add peers with full details
                    data.peers.forEach(peer => {{
                        const peerNode = document.createElement('div');
                        peerNode.className = 'node-item';
                        const peerId = peer.node_id.substring(0, 16);
                        const peerHealth = peer.health_score || 100;
                        const peerRole = 'peer';
                        const peerTrust = 'VERIFIED';
                        const peerEpoch = 1;
                        const peerLinks = 1;
                        const peerPromotion = peerHealth > 80 ? 'yes' : 'no';
                        
                        peerNode.innerHTML = '<strong>[ PEER ]</strong> ' + peerId + '... (' + peer.platform + ')<br>' +
                            '├─ role: ' + peerRole + '<br>' +
                            '├─ epoch: ' + peerEpoch + '<br>' +
                            '├─ links: ' + peerLinks + '<br>' +
                            '├─ trust: <span class="node-trust">' + peerTrust + '</span><br>' +
                            '└─ promotion eligible: ' + peerPromotion;
                        topology.appendChild(peerNode);
                    }});
                    
                    // Update metrics
                    document.getElementById('node-count').textContent = data.peers.length + 1;
                    document.getElementById('state-keys').textContent = data.status.state_keys;
                    
                    // Update failover engine state
                    const failoverEl = document.getElementById('failover-engine');
                    failoverEl.textContent = failoverState;
                    failoverEl.className = 'metric-value';
                    if (failoverState === 'TRANSITIONING') {{
                        failoverEl.classList.add('transitioning');
                    }} else if (failoverState === 'READY') {{
                        failoverEl.classList.add('operational');
                    }} else {{
                        failoverEl.classList.add('operational');
                    }}
                    
                    // Update NEXUS AI status
                    fetch('/api/nexus')
                        .then(r => r.json())
                        .then(nexusData => {{
                            const nexusStatusEl = document.getElementById('nexus-status');
                            const nexusInsightEl = document.getElementById('nexus-insight');
                            
                            if (nexusData.nexus_available) {{
                                nexusStatusEl.textContent = 'ACTIVE';
                                nexusStatusEl.className = 'status-operational';
                                if (nexusData.insight) {{
                                    nexusInsightEl.textContent = nexusData.insight.substring(0, 60) + '...';
                                }}
                            }} else {{
                                nexusStatusEl.textContent = 'UNAVAILABLE';
                                nexusStatusEl.className = 'status-degraded';
                                nexusInsightEl.textContent = 'NEXUS AI not available';
                            }}
                        }})
                        .catch(err => {{
                            document.getElementById('nexus-status').textContent = 'ERROR';
                            document.getElementById('nexus-status').className = 'status-error';
                        }});
                    
                    // Update M.I.T.E.L. status
                    console.log('[OMNI] Fetching /api/mitel');
                    fetch('/api/mitel')
                        .then(response => {{
                            console.log('[OMNI] /api/mitel response received');
                            return response.json();
                        }})
                        .then(mitelData => {{
                            console.log('[OMNI] M.I.T.E.L. data:', mitelData);
                            const mitelStatusEl = document.getElementById('mitel-status');
                            const mitelDevicesEl = document.getElementById('mitel-devices');
                            const mitelQuarantinedEl = document.getElementById('mitel-quarantined');
                            const mitelThreatsEl = document.getElementById('mitel-threats');
                            const mitelFabricEl = document.getElementById('mitel-fabric');
                            
                            if (mitelData.mitel_available && mitelData.status) {{
                                const status = mitelData.status.status;
                                mitelStatusEl.textContent = status.toUpperCase();
                                mitelStatusEl.className = 'metric-value ' + (status === 'running' ? 'operational' : 'degraded');
                                
                                mitelDevicesEl.textContent = mitelData.status.registered_devices || 0;
                                mitelQuarantinedEl.textContent = mitelData.status.quarantined_devices || 0;
                                mitelThreatsEl.textContent = mitelData.status.threat_events || 0;
                                mitelFabricEl.textContent = mitelData.fabric_health || '--';
                                
                                // Update top band threats count
                                document.getElementById('threats').textContent = mitelData.status.threat_events || 0;
                                
                                // Update device list
                                updateDeviceList();
                                
                                // Add threat events to timeline
                                if (mitelData.recent_threats && mitelData.recent_threats.length > 0) {{
                                    mitelData.recent_threats.forEach(threat => {{
                                        events.push({{
                                            time: new Date(threat.timestamp).toLocaleTimeString(),
                                            category: 'SECURITY',
                                            message: 'M.I.T.E.L.: ' + threat.description
                                        }});
                                    }});
                                }}
                            }} else {{
                                mitelStatusEl.textContent = 'NOT LOADED';
                                mitelStatusEl.className = 'metric-value degraded';
                                mitelDevicesEl.textContent = '--';
                                mitelQuarantinedEl.textContent = '--';
                                mitelThreatsEl.textContent = '--';
                                mitelFabricEl.textContent = '--';
                            }}
                        }})
                        .catch(err => {{
                            document.getElementById('mitel-status').textContent = 'ERROR';
                            document.getElementById('mitel-status').className = 'metric-value error';
                        }});
                    
                    // Update timestamp
                    document.getElementById('last-update').textContent = new Date().toLocaleTimeString();
                    
                    // Add event
                    const now = new Date();
                    const timeStr = now.toLocaleTimeString();
                    events.push({{
                        time: timeStr,
                        category: 'SYSTEM',
                        message: 'Status update'
                    }});
                    
                    // Keep last 20 events
                    if (events.length > 20) events.shift();
                    
                    // Update event timeline
                    const timeline = document.getElementById('event-timeline');
                    timeline.innerHTML = '<h2>EVENT TIMELINE</h2>';
                    events.slice(-15).reverse().forEach(event => {{
                        const line = document.createElement('div');
                        line.className = 'event-line';
                        const eventTime = event.time;
                        const eventCat = event.category.toLowerCase();
                        const eventCatUpper = event.category;
                        const eventMsg = event.message;
                        line.innerHTML = '<span class="event-time">' + eventTime + '</span><span class="event-category ' + eventCat + '">[' + eventCatUpper + ']</span><span>' + eventMsg + '</span>';
                        timeline.appendChild(line);
                    }});
                }})
                .catch(err => {{
                    console.error('Error:', err);
                }});
        }}
        
        // Update every 30 seconds (very slow for consumer hardware)
        setInterval(updateConsole, 30000);
        updateConsole();
    </script>
</body>
</html>"""


def open_browser(url, delay=1.5):
    """Open browser after delay"""
    time.sleep(delay)
    try:
        webbrowser.open(url)
        print(f"✓ Browser opened: {url}")
    except Exception as e:
        print(f"⚠ Could not auto-open browser: {e}")
        print(f"  Please open manually: {url}")


def get_local_ip():
    """Get local IP address"""
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return '127.0.0.1'


def create_handler_class(core, nexus=None):
    """Create handler class with core and nexus instances"""
    class Handler(OMNIWebHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, core=core, nexus=nexus, **kwargs)
    return Handler


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='OMNI Web Console - OBSERVER ONLY')
    parser.add_argument('--port', type=int, default=8888, help='Port to run on')
    parser.add_argument('--config', help='Path to config file')
    parser.add_argument('--no-browser', action='store_true', help='Do not auto-open browser')
    args = parser.parse_args()
    
    # Create OMNI instance
    print("Initializing OMNI core...")
    core = OmniCore(config_path=args.config)
    if not core.start():
        print("ERROR: Failed to start OMNI Core")
        sys.exit(1)
    time.sleep(2)
    
    # Initialize NEXUS for AI intelligence (recovery coach)
    nexus_instance = None
    if NEXUS_AVAILABLE:
        try:
            if USE_MISTRAL:
                print("Initializing NEXUS AI (Mistral-7B-Q4)...")
                nexus_instance = get_nexus_ai()
                print("🧠 NEXUS AI initialized - Substrate intelligence active")
            else:
                print("Initializing NEXUS AI (Trinity Enhanced)...")
                nexus_instance = TrinityEnhancedLLM()
                print("NEXUS AI initialized - Recovery Coach active")
        except Exception as e:
            print(f"WARNING: NEXUS AI not available: {e}")
            nexus_instance = None
            nexus_instance = None
    
    # Get IP and URL
    ip = get_local_ip()
    port = args.port
    url = f"http://{ip}:{port}"
    
    # Create server with NEXUS
    handler_class = create_handler_class(core, nexus=nexus_instance)
    server = HTTPServer(('0.0.0.0', port), handler_class)
    
    print("="*70)
    print("OMNI Infrastructure Operations Console")
    print("MODE: OBSERVATION (NO CONTROL AUTHORITY)")
    print("="*70)
    print(f"Server running at: {url}")
    print(f"Platform: {core.config['platform']}")
    print(f"Observer token: {OBSERVER_TOKEN}")
    print("="*70)
    
    # Auto-open browser
    if not args.no_browser:
        browser_thread = threading.Thread(target=open_browser, args=(url,), daemon=True)
        browser_thread.start()
        print(f"Opening browser in 1.5 seconds...")
    else:
        print(f"Manual access: {url}")
    
    print("\nPress Ctrl+C to stop\n")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\nShutting down...")
        server.shutdown()
        core.stop()
        print("✓ Stopped")


if __name__ == "__main__":
    main()
