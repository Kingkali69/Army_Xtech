#!/usr/bin/env python3
"""
UI Sync Live - Instant cross-device UI synchronization
Drop-in integration for GhostHUD
"""

import json
import time
import threading
import hashlib
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.request import Request, urlopen
from urllib.error import URLError
from typing import Dict, Any, List, Optional

class UIState:
    def __init__(self):
        self.state = {
            'page': 0,
            'panels': {},
            'scroll': {},
            'forms': {},
            'selected': [],
            'visibility': {},
            'custom': {},
            'ts': 0,
            'hash': ''
        }
        self.lock = threading.Lock()
        self.last_hash = ''
    
    def update(self, changes: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        with self.lock:
            old_hash = self.state.get('hash', '')
            for k, v in changes.items():
                if k != 'hash' and k != 'ts':
                    self.state[k] = v
            self.state['ts'] = time.time()
            self.state['hash'] = self._compute_hash()
            if self.state['hash'] != old_hash:
                return self._get_diff(old_hash)
            return None
    
    def get(self) -> Dict[str, Any]:
        with self.lock:
            return self.state.copy()
    
    def apply(self, state: Dict[str, Any]):
        with self.lock:
            for k, v in state.items():
                self.state[k] = v
    
    def _compute_hash(self) -> str:
        s = json.dumps({k: v for k, v in self.state.items() if k not in ('hash', 'ts')}, sort_keys=True)
        return hashlib.md5(s.encode()).hexdigest()[:12]
    
    def _get_diff(self, old_hash: str) -> Dict[str, Any]:
        return {'full': self.state.copy(), 'prev_hash': old_hash}


class UISyncNode:
    def __init__(self, device_id: str, port: int = 7890, is_master: bool = False):
        self.device_id = device_id
        self.port = port
        self.is_master = is_master
        self.master_id = device_id if is_master else None
        self.master_ip = '127.0.0.1' if is_master else None
        self.master_port = port if is_master else None
        self.peers: Dict[str, Dict[str, Any]] = {}
        self.ui_state = UIState()
        self.running = False
        self.callbacks: List[callable] = []
        self.file_hashes: Dict[str, str] = {}
        self.sync_dir = os.getcwd()
        self._lock = threading.Lock()
    
    def start(self):
        self.running = True
        if self.is_master:
            threading.Thread(target=self._broadcast_loop, daemon=True).start()
        else:
            threading.Thread(target=self._poll_loop, daemon=True).start()
        threading.Thread(target=self._file_watch_loop, daemon=True).start()
    
    def stop(self):
        self.running = False
    
    def register_peer(self, device_id: str, ip: str, port: int):
        with self._lock:
            self.peers[device_id] = {'ip': ip, 'port': port, 'last_seen': time.time()}
    
    def set_master(self, master_id: str, master_ip: str, master_port: int):
        with self._lock:
            self.master_id = master_id
            self.master_ip = master_ip
            self.master_port = master_port
            self.is_master = (master_id == self.device_id)
    
    def take_control(self) -> bool:
        if self.is_master:
            return True
        old_master_id = self.master_id
        self.is_master = True
        self.master_id = self.device_id
        self.master_ip = '127.0.0.1'
        self.master_port = self.port
        self._announce_master_change()
        self.stop()
        self.start()
        return True
    
    def update_ui(self, changes: Dict[str, Any], local: bool = True) -> bool:
        if local and not self.is_master:
            return self._forward_to_master(changes)
        diff = self.ui_state.update(changes)
        if diff and self.is_master:
            self._broadcast_state()
        for cb in self.callbacks:
            try:
                cb(changes)
            except:
                pass
        return True
    
    def get_ui_state(self) -> Dict[str, Any]:
        return self.ui_state.get()
    
    def on_state_change(self, callback: callable):
        self.callbacks.append(callback)
    
    def _broadcast_loop(self):
        while self.running and self.is_master:
            self._broadcast_state()
            time.sleep(0.5)
    
    def _broadcast_state(self):
        state = self.ui_state.get()
        data = json.dumps({
            'type': 'ui_sync',
            'state': state,
            'master': self.device_id,
            'ts': time.time()
        }).encode()
        with self._lock:
            peers = list(self.peers.items())
        for pid, pinfo in peers:
            if pid == self.device_id:
                continue
            try:
                req = Request(
                    f"http://{pinfo['ip']}:{pinfo['port']}/ui/sync",
                    data=data,
                    headers={'Content-Type': 'application/json'}
                )
                urlopen(req, timeout=1)
            except:
                pass
    
    def _poll_loop(self):
        while self.running and not self.is_master:
            if self.master_ip and self.master_port:
                try:
                    url = f"http://{self.master_ip}:{self.master_port}/ui/state"
                    with urlopen(url, timeout=2) as resp:
                        data = json.loads(resp.read())
                        if data.get('status') == 'ok':
                            remote_state = data.get('ui_state', {})
                            local_hash = self.ui_state.get().get('hash', '')
                            remote_hash = remote_state.get('hash', '')
                            if remote_hash and remote_hash != local_hash:
                                self.ui_state.apply(remote_state)
                                for cb in self.callbacks:
                                    try:
                                        cb(remote_state)
                                    except:
                                        pass
                except:
                    pass
            time.sleep(0.5)
    
    def _forward_to_master(self, changes: Dict[str, Any]) -> bool:
        if not self.master_ip or not self.master_port:
            return False
        try:
            data = json.dumps({
                'type': 'ui_update',
                'changes': changes,
                'source': self.device_id
            }).encode()
            req = Request(
                f"http://{self.master_ip}:{self.master_port}/ui/update",
                data=data,
                headers={'Content-Type': 'application/json'}
            )
            urlopen(req, timeout=2)
            return True
        except:
            return False
    
    def _announce_master_change(self):
        data = json.dumps({
            'type': 'master_change',
            'new_master': self.device_id,
            'ip': '127.0.0.1',
            'port': self.port,
            'ts': time.time()
        }).encode()
        with self._lock:
            peers = list(self.peers.items())
        for pid, pinfo in peers:
            if pid == self.device_id:
                continue
            try:
                req = Request(
                    f"http://{pinfo['ip']}:{pinfo['port']}/ui/master_change",
                    data=data,
                    headers={'Content-Type': 'application/json'}
                )
                urlopen(req, timeout=1)
            except:
                pass
    
    def _file_watch_loop(self):
        while self.running:
            if self.is_master:
                self._scan_and_sync_files()
            time.sleep(2)
    
    def _scan_and_sync_files(self):
        if not self.is_master:
            return
        for root, dirs, files in os.walk(self.sync_dir):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
            for f in files:
                if f.endswith(('.py', '.html', '.css', '.js', '.json')):
                    fpath = os.path.join(root, f)
                    try:
                        with open(fpath, 'rb') as fp:
                            content = fp.read()
                        fhash = hashlib.md5(content).hexdigest()
                        old_hash = self.file_hashes.get(fpath, '')
                        if fhash != old_hash:
                            self.file_hashes[fpath] = fhash
                            if old_hash:
                                self._push_file(fpath, content, fhash)
                    except:
                        pass
    
    def _push_file(self, fpath: str, content: bytes, fhash: str):
        import base64
        rel_path = os.path.relpath(fpath, self.sync_dir)
        data = json.dumps({
            'type': 'file_sync',
            'path': rel_path,
            'content': base64.b64encode(content).decode(),
            'hash': fhash,
            'ts': time.time()
        }).encode()
        with self._lock:
            peers = list(self.peers.items())
        for pid, pinfo in peers:
            if pid == self.device_id:
                continue
            try:
                req = Request(
                    f"http://{pinfo['ip']}:{pinfo['port']}/file/sync",
                    data=data,
                    headers={'Content-Type': 'application/json'}
                )
                urlopen(req, timeout=5)
            except:
                pass
    
    def apply_file_sync(self, rel_path: str, content: bytes, fhash: str) -> bool:
        fpath = os.path.join(self.sync_dir, rel_path)
        os.makedirs(os.path.dirname(fpath), exist_ok=True)
        with open(fpath, 'wb') as fp:
            fp.write(content)
        self.file_hashes[fpath] = fhash
        return True
    
    def handle_ui_sync(self, data: Dict[str, Any]):
        if self.is_master:
            return
        state = data.get('state', {})
        master = data.get('master', '')
        if master and master != self.master_id:
            self.master_id = master
        local_hash = self.ui_state.get().get('hash', '')
        remote_hash = state.get('hash', '')
        if remote_hash and remote_hash != local_hash:
            self.ui_state.apply(state)
            for cb in self.callbacks:
                try:
                    cb(state)
                except:
                    pass
    
    def handle_master_change(self, data: Dict[str, Any]):
        new_master = data.get('new_master', '')
        ip = data.get('ip', '')
        port = data.get('port', 7890)
        if new_master and new_master != self.device_id:
            self.is_master = False
            self.master_id = new_master
            self.master_ip = ip
            self.master_port = port
            self.stop()
            self.start()


def create_sync_handlers(sync_node: UISyncNode):
    import base64
    
    def handle_get(path: str) -> Optional[Dict[str, Any]]:
        if path == '/ui/state':
            return {'status': 'ok', 'ui_state': sync_node.get_ui_state(), 'is_master': sync_node.is_master}
        return None
    
    def handle_post(path: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if path == '/ui/sync':
            sync_node.handle_ui_sync(data)
            return {'status': 'ok'}
        if path == '/ui/update':
            changes = data.get('changes', data.get('ui_changes', {}))
            sync_node.update_ui(changes, local=False)
            return {'status': 'ok'}
        if path == '/ui/master_change':
            sync_node.handle_master_change(data)
            return {'status': 'ok'}
        if path == '/file/sync':
            rel_path = data.get('path', '')
            content = base64.b64decode(data.get('content', ''))
            fhash = data.get('hash', '')
            if rel_path:
                sync_node.apply_file_sync(rel_path, content, fhash)
            return {'status': 'ok'}
        return None
    
    return handle_get, handle_post


JS_SYNC_CODE = '''
// UI Sync Client - Drop into any page
(function() {
  var lastHash = '';
  var isMaster = false;
  var syncInterval = 500;
  
  function getUIState() {
    return {
      page: parseInt(location.hash.replace('#page-', '') || '0'),
      scroll: {x: window.scrollX, y: window.scrollY},
      visibility: {},
      ts: Date.now()
    };
  }
  
  function applyUIState(state) {
    if (state.page !== undefined && state.page !== parseInt(location.hash.replace('#page-', '') || '0')) {
      location.hash = '#page-' + state.page;
    }
    if (state.scroll) {
      window.scrollTo(state.scroll.x || 0, state.scroll.y || 0);
    }
  }
  
  function syncToServer(changes) {
    fetch('/ui/update', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ui_changes: changes})
    }).catch(function(){});
  }
  
  function pollServer() {
    if (isMaster) return;
    fetch('/ui/state').then(function(r){return r.json();}).then(function(data) {
      if (data.status === 'ok' && data.ui_state) {
        var h = data.ui_state.hash || '';
        if (h && h !== lastHash) {
          lastHash = h;
          applyUIState(data.ui_state);
        }
        isMaster = data.is_master || false;
      }
    }).catch(function(){});
  }
  
  window.addEventListener('hashchange', function() {
    if (isMaster) {
      syncToServer({page: parseInt(location.hash.replace('#page-', '') || '0')});
    }
  });
  
  setInterval(pollServer, syncInterval);
  
  window.UISyncClient = {
    sync: syncToServer,
    getState: getUIState,
    apply: applyUIState
  };
})();
'''


if __name__ == '__main__':
    import sys
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--device', default='node1')
    parser.add_argument('--port', type=int, default=7890)
    parser.add_argument('--master', action='store_true')
    parser.add_argument('--connect', help='master_ip:port')
    args = parser.parse_args()
    
    node = UISyncNode(args.device, args.port, args.master)
    
    if args.connect and not args.master:
        parts = args.connect.split(':')
        node.set_master('master', parts[0], int(parts[1]) if len(parts) > 1 else 7890)
    
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass
        
        def do_GET(self):
            if self.path == '/ui/state':
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'status': 'ok',
                    'ui_state': node.get_ui_state(),
                    'is_master': node.is_master
                }).encode())
            else:
                self.send_response(404)
                self.end_headers()
        
        def do_POST(self):
            length = int(self.headers.get('Content-Length', 0))
            data = json.loads(self.rfile.read(length)) if length else {}
            
            if self.path == '/ui/sync':
                node.handle_ui_sync(data)
            elif self.path == '/ui/update':
                changes = data.get('changes', data.get('ui_changes', {}))
                node.update_ui(changes, local=False)
            elif self.path == '/ui/master_change':
                node.handle_master_change(data)
            elif self.path == '/file/sync':
                import base64
                rel_path = data.get('path', '')
                content = base64.b64decode(data.get('content', ''))
                fhash = data.get('hash', '')
                if rel_path:
                    node.apply_file_sync(rel_path, content, fhash)
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"status":"ok"}')
    
    node.start()
    print(f"[UI SYNC] {args.device} running on port {args.port} ({'MASTER' if args.master else 'MIRROR'})")
    
    server = HTTPServer(('0.0.0.0', args.port), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        node.stop()

