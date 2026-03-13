#!/usr/bin/env python3
"""
UI Sync Integration - Patches existing GhostHUD to use ui_sync_live
Run once to integrate, or import and call integrate()
"""

import os
import sys

def integrate():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Patch ghostops_core.py to use UISyncNode
    core_patch = '''
# UI SYNC INTEGRATION - Added by ui_sync_integration.py
try:
    from ui_sync_live import UISyncNode, create_sync_handlers
    _ui_sync_available = True
except ImportError:
    _ui_sync_available = False
'''
    
    # Patch ghostops_adapter.py handlers
    adapter_get_patch = '''
        # UI SYNC LIVE - GET handlers
        if hasattr(engine, 'ui_sync') and engine.ui_sync:
            from ui_sync_live import create_sync_handlers
            handle_get, _ = create_sync_handlers(engine.ui_sync)
            result = handle_get(self.path)
            if result:
                self.send_json(result)
                return
'''
    
    adapter_post_patch = '''
        # UI SYNC LIVE - POST handlers
        if hasattr(engine, 'ui_sync') and engine.ui_sync:
            from ui_sync_live import create_sync_handlers
            _, handle_post = create_sync_handlers(engine.ui_sync)
            data = self.read_json() if self.headers.get('Content-Length') else {}
            result = handle_post(self.path, data)
            if result:
                self.send_json(result)
                return
'''
    
    print("[UI SYNC INTEGRATION] Patches ready")
    print("Add to ghostops_core.py __init__:")
    print("  self.ui_sync = UISyncNode(self.config.device_id, port, is_master=True)")
    print("  self.ui_sync.start()")
    print("")
    print("Add to ghostops_adapter.py do_GET (before other handlers):")
    print(adapter_get_patch)
    print("")
    print("Add to ghostops_adapter.py do_POST (before other handlers):")
    print(adapter_post_patch)
    
    return True


def patch_kali_js():
    """Returns JavaScript to add to kali.py for enhanced sync"""
    return '''
    // Enhanced UI Sync - Tracks all UI state changes
    (function() {
      var syncQueue = [];
      var syncTimer = null;
      var lastSyncHash = '';
      
      function queueSync(changes) {
        syncQueue.push(changes);
        if (!syncTimer) {
          syncTimer = setTimeout(flushSync, 100);
        }
      }
      
      function flushSync() {
        syncTimer = null;
        if (syncQueue.length === 0) return;
        var merged = {};
        syncQueue.forEach(function(c) {
          Object.keys(c).forEach(function(k) { merged[k] = c[k]; });
        });
        syncQueue = [];
        fetch('/ui/update', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({ui_changes: merged, ts: Date.now()})
        }).catch(function(){});
      }
      
      // Track page changes
      var origShowPage = window.showPage;
      window.showPage = function(n) {
        if (origShowPage) origShowPage(n);
        queueSync({page: parseInt(n)});
      };
      
      // Track panel visibility
      document.addEventListener('click', function(e) {
        var panel = e.target.closest('.panel');
        if (panel && panel.id) {
          queueSync({panels: {[panel.id]: panel.style.display !== 'none'}});
        }
      });
      
      // Track scroll
      var scrollTimer = null;
      window.addEventListener('scroll', function() {
        if (scrollTimer) clearTimeout(scrollTimer);
        scrollTimer = setTimeout(function() {
          queueSync({scroll: {x: window.scrollX, y: window.scrollY}});
        }, 200);
      });
      
      // Apply remote state
      window.applyRemoteUIState = function(state) {
        if (state.page !== undefined) {
          var pages = document.querySelectorAll('[id^="page-"]');
          pages.forEach(function(p) { p.style.display = 'none'; });
          var target = document.getElementById('page-' + state.page);
          if (target) target.style.display = 'block';
        }
        if (state.scroll) {
          window.scrollTo(state.scroll.x || 0, state.scroll.y || 0);
        }
        if (state.visibility) {
          Object.keys(state.visibility).forEach(function(id) {
            var el = document.getElementById(id);
            if (el) el.style.display = state.visibility[id] ? 'block' : 'none';
          });
        }
      };
      
      // Poll for updates (peer nodes)
      setInterval(function() {
        if (window.isMasterNode) return;
        fetch('/ui/state').then(function(r){return r.json();}).then(function(d) {
          if (d.status === 'ok' && d.ui_state && d.ui_state.hash !== lastSyncHash) {
            lastSyncHash = d.ui_state.hash;
            window.applyRemoteUIState(d.ui_state);
          }
        }).catch(function(){});
      }, 500);
    })();
'''


def get_node_registration_code():
    """Returns code for auto-registering peers"""
    return '''
def register_with_master(master_ip, master_port, my_device_id, my_ip, my_port):
    import urllib.request
    import json
    data = json.dumps({
        'device_id': my_device_id,
        'ip': my_ip,
        'port': my_port,
        'platform': 'auto'
    }).encode()
    req = urllib.request.Request(
        f'http://{master_ip}:{master_port}/discover',
        data=data,
        headers={'Content-Type': 'application/json'}
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read())
    except:
        return None
'''


if __name__ == '__main__':
    integrate()
    print("\n" + "="*60)
    print("JavaScript to add to kali.py (inside <script> tag):")
    print("="*60)
    print(patch_kali_js())

