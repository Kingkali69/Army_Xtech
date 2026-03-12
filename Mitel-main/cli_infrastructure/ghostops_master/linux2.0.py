#!/usr/bin/env python3
"""
GhostOps Linux Master Node with Plugin System
Run this on your Linux server
"""

import os, sys, socket, json, time, threading, random
from http.server import HTTPServer, BaseHTTPRequestHandler
import webbrowser

# CONFIG
PORT = 7890
AUTH_KEY = "ghostops"
DEVICE_ID = f"linux_{socket.gethostname()}"
LOCAL_IP = socket.gethostbyname(socket.gethostname())

# Plugin system
try:
    from plugin_loader import PluginLoader
    plugin_loader = PluginLoader()
    modules_loaded = plugin_loader.load_all_modules()
    print(f"[+] Loaded {len(modules_loaded)} modules: {', '.join(modules_loaded.keys())}")
    _PLUGINS_AVAILABLE = True
except Exception as e:
    print(f"[!] Plugin system unavailable: {e}")
    plugin_loader = None
    _PLUGINS_AVAILABLE = False

# STATE
nodes = {}
last_sync = 0
tool_state = None
page_state = 1
authority = None
commands = []

print(f"""
===========================================
  GHOSTOPS MASTER NODE - {LOCAL_IP}:{PORT}
===========================================
  AUTH KEY: {AUTH_KEY}
  DEVICE ID: {DEVICE_ID}
  PLUGINS: {'Enabled' if _PLUGINS_AVAILABLE else 'Disabled'}
===========================================
""")

class GhostServer(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return
    
    def _send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
    
    def do_OPTIONS(self):
        self.send_response(200)
        self._send_cors_headers()
        self.end_headers()
    
    def send_json(self, data):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self._send_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def read_json(self):
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length > 0:
            return json.loads(self.rfile.read(content_length).decode())
        return {}
    
    def do_GET(self):
        if self.path.startswith('/status'):
            self.send_json({
                'status': 'online',
                'nodes': nodes,
                'device_id': DEVICE_ID,
                'authority': authority,
                'tool': tool_state,
                'page': page_state,
                'last_sync': last_sync,
                'plugins_enabled': _PLUGINS_AVAILABLE
            })
        
        elif self.path.startswith('/nodes'):
            self.send_json(nodes)
        
        elif self.path.startswith('/modules'):
            if not _PLUGINS_AVAILABLE:
                self.send_json({'status': 'error', 'message': 'Plugins not available'})
                return
            
            if self.path == '/modules' or self.path == '/modules/':
                self.send_json({
                    'status': 'success',
                    'modules': plugin_loader.get_all_info(),
                    'module_status': plugin_loader.get_all_status()
                })
            elif self.path.startswith('/modules/'):
                parts = self.path.split('/')
                if len(parts) >= 3:
                    module_name = parts[2]
                    module = plugin_loader.get_module(module_name)
                    if module:
                        self.send_json(module.get_status())
                    else:
                        self.send_json({'status': 'error', 'message': 'Module not found'})
        
        elif self.path.startswith('/module/'):
            if not _PLUGINS_AVAILABLE:
                self.send_json({'status': 'error', 'message': 'Plugins not available'})
                return
            
            parts = self.path.split('/')
            if len(parts) >= 3:
                module_name = parts[2].split('?')[0]
                module = plugin_loader.get_module(module_name)
                if module:
                    try:
                        result = module.handle_request(self, "GET", None)
                        self.send_json(result)
                    except Exception as e:
                        self.send_json({'status': 'error', 'message': str(e)})
                else:
                    self.send_json({'status': 'error', 'message': f'Module not found: {module_name}'})
        
        elif self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self._send_cors_headers()
            self.end_headers()
            self.wfile.write(HTML.encode())
        
        else:
            self.send_json({'status': 'error', 'message': 'Not found'})
    
    def do_POST(self):
        if self.path == '/auth/login':
            data = self.read_json()
            if data.get('key', '') == AUTH_KEY:
                self.send_json({'status': 'authenticated', 'token': f"token_{random.randint(1000, 9999)}"})
            else:
                self.send_json({'status': 'error', 'message': 'Invalid authentication key'})
            return
        
        if self.path.startswith('/module/'):
            if not _PLUGINS_AVAILABLE:
                self.send_json({'status': 'error', 'message': 'Plugins not available'})
                return
            
            parts = self.path.split('/')
            if len(parts) >= 3:
                module_name = parts[2].split('?')[0]
                module = plugin_loader.get_module(module_name)
                if module:
                    try:
                        data = self.read_json()
                        result = module.handle_request(self, "POST", data)
                        self.send_json(result)
                    except Exception as e:
                        self.send_json({'status': 'error', 'message': str(e)})
                else:
                    self.send_json({'status': 'error', 'message': f'Module not found: {module_name}'})
                return
        
        if self.path == '/sync/discover':
            data = self.read_json()
            device_id = data.get('device_id')
            if device_id:
                nodes[device_id] = {
                    'platform': data.get('platform', 'unknown'),
                    'last_seen': time.time()
                }
                global last_sync
                last_sync = time.time()
                self.send_json({'status': 'ok', 'node_count': len(nodes), 'auth_key': AUTH_KEY})
                print(f"[+] Node connected: {device_id}")
            else:
                self.send_json({'status': 'error', 'message': 'Missing device_id'})
        
        elif self.path == '/sync/tool':
            data = self.read_json()
            global tool_state
            tool_state = data.get('tool')
            print(f"[+] Tool activated: {tool_state}")
            self.send_json({'status': 'ok'})
        
        elif self.path == '/sync/page':
            data = self.read_json()
            global page_state
            page_state = data.get('page', 1)
            print(f"[+] Page changed: {page_state}")
            self.send_json({'status': 'ok'})
        
        else:
            self.send_json({'status': 'error', 'message': 'Unknown endpoint'})

HTML = """<!DOCTYPE html>
<html><head><title>GhostOps Master</title>
<style>
body{background:#111;color:#0f0;font-family:monospace;margin:0;padding:20px}
.container{max-width:1200px;margin:0 auto}
.header{text-align:center;border-bottom:2px solid #0f0;padding:20px 0;margin-bottom:20px}
.logo{font-size:48px;letter-spacing:5px;text-shadow:0 0 10px #0f0}
.status{display:flex;justify-content:space-around;margin:20px 0}
.status-item{border:1px solid #0f0;padding:15px;text-align:center;flex:1;margin:5px;background:rgba(0,20,0,.3)}
.controls{display:flex;gap:10px;margin:20px 0}
.btn{background:#000;color:#0f0;border:1px solid #0f0;padding:10px 20px;cursor:pointer;font-family:monospace;transition:.3s}
.btn:hover{background:#030;box-shadow:0 0 15px #0f0}
.output{border:1px solid #0f0;padding:15px;background:#000;min-height:200px;max-height:400px;overflow-y:auto;margin:20px 0}
</style>
</head><body>
<div class="container">
<div class="header"><div class="logo">GHOSTOPS MASTER</div><div>Linux Control Node</div></div>
<div class="status">
<div class="status-item"><div>Status:</div><div id="status">ONLINE</div></div>
<div class="status-item"><div>Nodes:</div><div id="nodes">0</div></div>
<div class="status-item"><div>Plugins:</div><div id="plugins">Loading...</div></div>
</div>
<div class="controls">
<button class="btn" onclick="listModules()">List Modules</button>
<button class="btn" onclick="listNodes()">List Nodes</button>
<button class="btn" onclick="authenticate()">Authenticate</button>
</div>
<div class="output" id="output">GhostOps Master Node Online<br>Waiting for connections...</div>
</div>
<script>
function log(m){document.getElementById('output').innerHTML+='<br>'+m}
function authenticate(){
const k=prompt('Enter auth key:');
fetch('/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({key:k})})
.then(r=>r.json()).then(d=>log(d.status==='authenticated'?'✓ Authenticated':'✗ Auth failed'))
}
function listModules(){
fetch('/modules').then(r=>r.json()).then(d=>{
if(d.modules){
log('=== MODULES ===');
Object.keys(d.modules).forEach(name=>log(`• ${name}: ${d.modules[name].description}`))
}else{log('Plugins not available')}
})
}
function listNodes(){
fetch('/nodes').then(r=>r.json()).then(d=>{
log('=== NODES ===');
Object.keys(d).forEach(name=>log(`• ${name}: ${d[name].platform}`))
})
}
function updateStatus(){
fetch('/status').then(r=>r.json()).then(d=>{
document.getElementById('nodes').textContent=Object.keys(d.nodes||{}).length;
document.getElementById('plugins').textContent=d.plugins_enabled?'Enabled':'Disabled';
})
}
updateStatus();
setInterval(updateStatus,5000);
</script>
</body></html>"""

if __name__ == "__main__":
    try:
        server = HTTPServer(('0.0.0.0', PORT), GhostServer)
        print(f"[+] Master server running at http://{LOCAL_IP}:{PORT}")
        print(f"[+] Plugins: {'Enabled' if _PLUGINS_AVAILABLE else 'Disabled'}")
        print(f"[+] Press Ctrl+C to stop\n")
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[+] Shutting down")
        server.shutdown()

