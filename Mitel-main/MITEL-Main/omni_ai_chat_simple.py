#!/usr/bin/env python3
"""
OMNI AI Chat Interface - Simple Version
======================================

Fallback AI chat that works without heavy dependencies.
Shows OMNI's AI capabilities without requiring Trinity.
"""

import sys
import os
import time
import threading
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime
import json
import socket
import argparse

# Add paths
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'substrate', 'ai_layer'))

class SimpleAI:
    """Simple AI fallback for OMNI chat"""
    
    def __init__(self):
        self.responses = {
            "hello": "🔥 OMNI AI online! I'm ready to help with infrastructure operations, threat detection, and system management.",
            "help": "🎯 I can help with:\n• System status monitoring\n• USB threat analysis\n• Healing kit deployment\n• NEXUS container operations\n• M.I.T.E.L. security queries",
            "status": "🛡️ OMNI Systems Status:\n✅ M.I.T.E.L. Security: ACTIVE\n✅ NEXUS Container: OPERATIONAL\n✅ Self-Healing: READY\n✅ Hive Intelligence: CONNECTED",
            "mitel": "🔒 M.I.T.E.L. provides zero-trust USB security. All devices are quarantined by default. Recent rubber ducky attack successfully neutralized.",
            "nexus": "🧠 NEXUS Container enables shared AI consciousness across mesh nodes. Features tool discovery, unified memory, and hive intelligence.",
            "healing": "🚑 Self-Healing First Aid Kits available:\n• State Corruption Recovery (30s)\n• Process Crash Recovery (15s)\n• Network Disconnect Recovery (10s)\n• Memory Leak Recovery (20s)\n• USB Attack Recovery (5s)",
            "default": "🔥 OMNI AI processing... I'm here to help with infrastructure operations, security, and system management. Try 'help' for commands."
        }
    
    def generate_response(self, message):
        """Generate AI response"""
        message_lower = message.lower()
        
        for key, response in self.responses.items():
            if key in message_lower:
                return response
        
        return self.responses["default"]

class ChatHandler(BaseHTTPRequestHandler):
    """Simple chat web handler"""
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/':
            self.send_html_page()
        elif self.path == '/chat':
            self.send_chat_interface()
        else:
            self.send_error(404)
    
    def do_POST(self):
        """Handle POST requests"""
        if self.path == '/api/chat':
            self.handle_chat_message()
        else:
            self.send_error(404)
    
    def send_html_page(self):
        """Send main HTML page"""
        html = """
<!DOCTYPE html>
<html>
<head>
    <title>🔥 OMNI AI Chat - NEXUS Intelligence</title>
    <meta charset="utf-8">
    <style>
        body { 
            background: #0a0a0a; 
            color: #00ff00; 
            font-family: 'Courier New', monospace; 
            margin: 0; 
            padding: 20px;
        }
        .container { 
            max-width: 800px; 
            margin: 0 auto; 
            background: #111; 
            border: 2px solid #00ff00; 
            border-radius: 10px; 
            padding: 20px;
        }
        .header { 
            text-align: center; 
            color: #00ff00; 
            margin-bottom: 20px;
        }
        .chat-box { 
            height: 400px; 
            border: 1px solid #00ff00; 
            background: #000; 
            padding: 10px; 
            overflow-y: auto; 
            margin-bottom: 20px;
        }
        .input-area { 
            display: flex; 
            gap: 10px;
        }
        input { 
            flex: 1; 
            background: #222; 
            color: #00ff00; 
            border: 1px solid #00ff00; 
            padding: 10px; 
            font-family: monospace;
        }
        button { 
            background: #00ff00; 
            color: #000; 
            border: none; 
            padding: 10px 20px; 
            font-weight: bold; 
            cursor: pointer;
        }
        .message { 
            margin: 10px 0; 
            padding: 5px 10px;
        }
        .user { 
            color: #00ffff; 
            text-align: right;
        }
        .ai { 
            color: #00ff00;
        }
        .status { 
            text-align: center; 
            color: #ffff00; 
            margin-bottom: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔥 OMNI AI Chat</h1>
            <h2>NEXUS Intelligence Interface</h2>
        </div>
        
        <div class="status">
            🛡️ M.I.T.E.L. Security: ACTIVE | 🧠 NEXUS: OPERATIONAL | 🚑 Healing: READY
        </div>
        
        <div class="chat-box" id="chatBox">
            <div class="message ai">
                🔥 OMNI AI online! I'm your NEXUS intelligence interface. I can help with system operations, security analysis, and healing protocols.
            </div>
        </div>
        
        <div class="input-area">
            <input type="text" id="messageInput" placeholder="Enter your message..." />
            <button onclick="sendMessage()">Send</button>
        </div>
    </div>

    <script>
        function sendMessage() {
            const input = document.getElementById('messageInput');
            const message = input.value.trim();
            
            if (!message) return;
            
            const chatBox = document.getElementById('chatBox');
            
            // Add user message
            chatBox.innerHTML += '<div class="message user">👤 You: ' + message + '</div>';
            
            // Send to API
            fetch('/api/chat', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({message: message})
            })
            .then(response => response.json())
            .then(data => {
                chatBox.innerHTML += '<div class="message ai">🤖 OMNI: ' + data.response + '</div>';
                chatBox.scrollTop = chatBox.scrollHeight;
            });
            
            input.value = '';
            input.focus();
        }
        
        document.getElementById('messageInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
    </script>
</body>
</html>
        """
        
        self.send_response(200, 'text/html', html)
    
    def send_chat_interface(self):
        """Send chat interface JSON"""
        self.send_json({
            'status': 'OMNI AI Chat Interface',
            'features': [
                'NEXUS Container Intelligence',
                'M.I.T.E.L. Security Analysis',
                'Self-Healing Protocol Management',
                'Hive Intelligence Queries'
            ]
        })
    
    def handle_chat_message(self):
        """Handle chat message API"""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode('utf-8'))
            message = data.get('message', '')
            
            # Generate AI response
            ai = SimpleAI()
            response = ai.generate_response(message)
            
            self.send_json({
                'response': response,
                'timestamp': datetime.now().isoformat(),
                'status': 'success'
            })
            
        except Exception as e:
            self.send_json({
                'response': f'Error: {str(e)}',
                'timestamp': datetime.now().isoformat(),
                'status': 'error'
            })
    
    def send_response(self, status, content_type, content):
        """Send HTTP response"""
        self.send_response(status)
        self.send_header('Content-type', content_type)
        self.send_header('Content-length', str(len(content.encode('utf-8'))))
        self.end_headers()
        self.wfile.write(content.encode('utf-8'))
    
    def send_json(self, data):
        """Send JSON response"""
        json_data = json.dumps(data, indent=2)
        self.send_response(200, 'application/json', json_data)
    
    def log_message(self, format, *args):
        """Suppress default logging"""
        pass

def find_free_port(start_port=8889):
    """Find a free port starting from start_port"""
    for port in range(start_port, start_port + 100):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                return port
        except OSError:
            continue
    return None

def start_ai_chat_server(port=8889, no_browser=False):
    """Start the OMNI AI Chat server"""
    
    # Find free port
    free_port = find_free_port(port)
    if not free_port:
        print("❌ No free ports available")
        return
    
    # Create server
    server = HTTPServer(('0.0.0.0', free_port), ChatHandler)
    
    print(f"🔥 OMNI AI Chat Server Started!")
    print(f"🌐 URL: http://localhost:{free_port}")
    print(f"🤖 AI: Simple NEXUS Intelligence")
    print(f"🛡️ Security: M.I.T.E.L. Integration Ready")
    print(f"🚑 Healing: First Aid Kit Commands Available")
    print(f"🛑 Press Ctrl+C to stop")
    print("-" * 50)
    
    # Open browser if not disabled
    if not no_browser:
        def open_browser():
            time.sleep(1)
            webbrowser.open(f'http://localhost:{free_port}')
        
        browser_thread = threading.Thread(target=open_browser, daemon=True)
        browser_thread.start()
    
    # Start server
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 OMNI AI Chat Server Stopped")
        server.shutdown()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='OMNI AI Chat - Simple NEXUS Intelligence')
    parser.add_argument('--port', type=int, default=8889, help='Port for chat server')
    parser.add_argument('--no-browser', action='store_true', help='Don\'t open browser')
    args = parser.parse_args()
    
    start_ai_chat_server(args.port, args.no_browser)
