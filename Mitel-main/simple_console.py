#!/usr/bin/env python3
"""
Simple Console - UI Only (No OmniCore Engine)
Just the web interface without the CPU-hungry engine
"""

import http.server
import socketserver
import json
import threading
import time
import webbrowser
from urllib.parse import urlparse, parse_qs

class SimpleConsoleHandler(http.server.SimpleHTTPRequestHandler):
    """Simple console handler - no engine, just UI"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def log_message(self, format, *args):
        """Suppress default logging"""
        pass
    
    def do_GET(self):
        """Handle GET requests - serve simple UI"""
        if self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            # Simple HTML without engine dependencies
            html = """
<!DOCTYPE html>
<html>
<head>
    <title>NEXUS Console - Simple Mode</title>
    <style>
        body { 
            background: #000; 
            color: #0f0; 
            font-family: 'Courier New', monospace; 
            margin: 20px;
        }
        .header { 
            border: 2px solid #0f0; 
            padding: 20px; 
            text-align: center;
            margin-bottom: 20px;
        }
        .status { 
            border: 1px solid #0f0; 
            padding: 15px; 
            margin: 10px 0;
        }
        .device-list {
            border: 1px solid #0f0;
            padding: 15px;
            margin: 10px 0;
            min-height: 200px;
        }
        .btn {
            background: #0f0;
            color: #000;
            border: none;
            padding: 10px 20px;
            margin: 5px;
            cursor: pointer;
            font-family: monospace;
        }
        .btn:hover { background: #0a0; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 NEXUS CONSOLE</h1>
        <h2>Simple Mode - UI Only</h2>
        <p>⚡ CPU Optimized - No Engine Running</p>
    </div>
    
    <div class="status">
        <h3>🔧 System Status</h3>
        <p>🌐 Console: <span id="console-status">ACTIVE</span></p>
        <p>🧠 Engine: <span style="color: #ff0;">DISABLED (Simple Mode)</span></p>
        <p>💻 CPU Usage: <span id="cpu-usage">NORMAL</span></p>
        <p>🔌 USB Monitoring: <span style="color: #ff0;">DISABLED</span></p>
    </div>
    
    <div class="device-list">
        <h3>🛡️ M.I.T.E.L. Device Management</h3>
        <p><em>Engine disabled - No device scanning</em></p>
        <button class="btn" onclick="alert('Engine disabled - Start full NEXUS to enable')">Enable Device Scanning</button>
    </div>
    
    <div class="status">
        <h3>🎯 Controls</h3>
        <button class="btn" onclick="window.open('http://192.168.1.161:8889', '_blank')">Open AI Chat</button>
        <button class="btn" onclick="alert('Start full NEXUS Engine for complete features')">Start Full Engine</button>
        <button class="btn" onclick="window.close()">Close Console</button>
    </div>
    
    <script>
        // Simple status update - no engine polling
        setInterval(() => {
            document.getElementById('console-status').textContent = 'ACTIVE';
            document.getElementById('cpu-usage').textContent = 'NORMAL';
        }, 5000);
        
        console.log('🚀 NEXUS Simple Console loaded - No engine running');
    </script>
</body>
</html>
            """
            
            self.wfile.write(html.encode())
        else:
            self.send_error(404)
    
    def do_POST(self):
        """Handle POST requests - simple responses"""
        if self.path == '/api/mitel/devices':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            # Simple response - no engine
            response = {
                'success': False,
                'message': 'Engine disabled - Start full NEXUS for device management'
            }
            
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_error(404)

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='NEXUS Simple Console - UI Only')
    parser.add_argument('--port', type=int, default=8888, help='Port to run on')
    parser.add_argument('--no-browser', action='store_true', help='Do not auto-open browser')
    args = parser.parse_args()
    
    # Get IP and URL
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
        s.close()
    except:
        ip = '127.0.0.1'
    
    port = args.port
    url = f"http://{ip}:{port}"
    
    print("="*70)
    print("🚀 NEXUS SIMPLE CONSOLE")
    print("⚡ CPU Optimized - UI Only (No Engine)")
    print("="*70)
    print(f"🌐 Server running at: {url}")
    print("🧠 Engine: DISABLED (Simple Mode)")
    print("💻 CPU Usage: NORMAL")
    print("🔌 USB Monitoring: DISABLED")
    print("="*70)
    
    # Create server
    with socketserver.TCPServer(('0.0.0.0', port), SimpleConsoleHandler) as httpd:
        print(f"✅ Simple console started on port {port}")
        
        # Auto-open browser if not disabled
        if not args.no_browser:
            def open_browser():
                time.sleep(1.5)
                try:
                    webbrowser.open(url)
                    print("✅ Browser opened")
                except Exception as e:
                    print(f"⚠ Could not auto-open browser: {e}")
            
            threading.Thread(target=open_browser, daemon=True).start()
        
        print("🎯 Simple console running - CPU usage should be normal")
        print("🛑 Press Ctrl+C to stop")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Simple console stopped")

if __name__ == '__main__':
    main()
