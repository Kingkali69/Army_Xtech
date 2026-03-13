#!/usr/bin/env python3
"""
OMNI AI Chat Interface
======================

Web interface to chat with TinyLlama AI.
Visual interface - no command line needed.
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

try:
    from trinity_enhanced_llm import TrinityEnhancedLLM, TRINITY_AVAILABLE
    LLM_AVAILABLE = True
    USE_TRINITY = True
except ImportError:
    try:
        from local_llm_integration import LocalLLM, LLAMA_CPP_AVAILABLE
        LLM_AVAILABLE = True
        USE_TRINITY = False
    except ImportError:
        LLM_AVAILABLE = False
        USE_TRINITY = False
        print("⚠️  LocalLLM not available. Install llama-cpp-python: pip install llama-cpp-python")

# Import command execution for first-class citizen capabilities
import subprocess
COMMAND_EXECUTOR_AVAILABLE = True

class AIChatHandler(BaseHTTPRequestHandler):
    """HTTP handler for AI chat interface"""
    
    llm_instance = None
    command_executor = None
    
    @classmethod
    def execute_system_command(cls, command_parts: list, use_sudo: bool = False) -> dict:
        """Execute system command safely"""
        try:
            # Prepend sudo if needed
            if use_sudo:
                command_parts = ['sudo'] + command_parts
            
            result = subprocess.run(
                command_parts,
                shell=False,
                capture_output=True,
                text=True,
                timeout=300
            )
            return {
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'exit_status': result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Command timed out',
                'stdout': '',
                'stderr': 'Command exceeded 5 minute timeout',
                'exit_status': -1
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'stdout': '',
                'stderr': str(e),
                'exit_status': -1
            }
    
    def log_message(self, format, *args):
        """Suppress default logging"""
        pass
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(self._get_html().encode('utf-8'))
        elif self.path == '/chat':
            # Chat endpoint
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            if not LLM_AVAILABLE or not self.llm_instance:
                response = {
                    'error': 'LLM not available',
                    'message': 'TinyLlama model not loaded'
                }
            else:
                response = {
                    'status': 'ready',
                    'model': 'TinyLlama-1.1B',
                    'message': 'AI is ready to chat'
                }
            
            self.wfile.write(json.dumps(response).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        """Handle POST requests"""
        if self.path == '/chat':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                message = data.get('message', '')
                conversation = data.get('conversation', [])
            except:
                message = ''
                conversation = []
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            if not LLM_AVAILABLE or not self.llm_instance:
                response = {
                    'error': 'LLM not available',
                    'response': 'TinyLlama model not loaded. Please check installation.'
                }
            else:
                try:
                    # Check if user wants to execute a command
                    command_executed = False
                    execution_result = None
                    
                    # Detect command execution requests
                    message_lower = message.lower()
                    command_parts = None
                    use_sudo = 'sudo' in message_lower
                    wants_update = 'apt update' in message_lower or 'update' in message_lower
                    wants_upgrade = 'apt upgrade' in message_lower or 'upgrade' in message_lower
                    
                    # Check for apt update/upgrade requests
                    if wants_update or wants_upgrade:
                        # Execute update first if requested
                        if wants_update:
                            command_parts = ['apt', 'update']
                            execution_result = self.execute_system_command(command_parts, use_sudo=use_sudo)
                            command_executed = True
                            
                            # If upgrade also requested and update succeeded, run upgrade
                            if wants_upgrade and execution_result.get('success'):
                                upgrade_result = self.execute_system_command(['apt', 'upgrade', '-y'], use_sudo=use_sudo)
                                # Combine results
                                execution_result = {
                                    'success': upgrade_result.get('success', False),
                                    'stdout': execution_result.get('stdout', '') + '\n\n--- UPGRADE ---\n' + upgrade_result.get('stdout', ''),
                                    'stderr': execution_result.get('stderr', '') + '\n' + upgrade_result.get('stderr', ''),
                                    'exit_status': upgrade_result.get('exit_status', -1)
                                }
                            elif wants_upgrade:
                                # Update failed, but try upgrade anyway
                                upgrade_result = self.execute_system_command(['apt', 'upgrade', '-y'], use_sudo=use_sudo)
                                execution_result = upgrade_result
                        elif wants_upgrade:
                            # Only upgrade requested
                            command_parts = ['apt', 'upgrade', '-y']
                            execution_result = self.execute_system_command(command_parts, use_sudo=use_sudo)
                            command_executed = True
                    
                    # Use Trinity-Enhanced if available
                    if USE_TRINITY and hasattr(self.llm_instance, 'chat'):
                        # Trinity-Enhanced LLM
                        result = self.llm_instance.chat(message)
                        response_text = result['response']
                        
                        # If command was executed, add result to response
                        if command_executed and execution_result:
                            if execution_result.get('success'):
                                stdout = execution_result.get('stdout', '')
                                stderr = execution_result.get('stderr', '')
                                response_text = f"✅ Command executed successfully!\n\n"
                                if stdout:
                                    response_text += f"Output:\n{stdout[:1000]}\n"
                                if stderr and 'WARNING' not in stderr:
                                    response_text += f"\nErrors:\n{stderr[:500]}"
                            else:
                                error_msg = execution_result.get('error', execution_result.get('stderr', 'Unknown error'))
                                # Check if it's a permission error - auto-retry with sudo
                                if 'Permission denied' in str(error_msg) or 'lock file' in str(error_msg).lower():
                                    response_text = f"⚠️ Permission denied. Retrying with sudo...\n\n"
                                    # Retry with sudo
                                    if wants_update:
                                        retry_result = self.execute_system_command(['apt', 'update'], use_sudo=True)
                                        if wants_upgrade and retry_result.get('success'):
                                            upgrade_retry = self.execute_system_command(['apt', 'upgrade', '-y'], use_sudo=True)
                                            retry_result = {
                                                'success': upgrade_retry.get('success', False),
                                                'stdout': retry_result.get('stdout', '') + '\n\n--- UPGRADE ---\n' + upgrade_retry.get('stdout', ''),
                                                'stderr': retry_result.get('stderr', '') + '\n' + upgrade_retry.get('stderr', ''),
                                                'exit_status': upgrade_retry.get('exit_status', -1)
                                            }
                                        execution_result = retry_result
                                        if retry_result.get('success'):
                                            response_text = f"✅ Command executed successfully with sudo!\n\nOutput:\n{retry_result.get('stdout', '')[:1000]}"
                                        else:
                                            response_text = f"❌ Command failed even with sudo:\n{retry_result.get('stderr', 'Unknown error')[:500]}"
                                    else:
                                        response_text = f"❌ Permission denied. Please use 'sudo' in your command.\n\nError: {error_msg[:500]}"
                                else:
                                    response_text = f"❌ Command execution failed:\n{error_msg[:500]}"
                        
                        # Add intelligence metadata (optional, for debugging)
                        if 'intent' in result and not command_executed:
                            response_text += f"\n\n[Intent: {result['intent']} | Confidence: {result['confidence']:.0%}]"
                    else:
                        # Basic LLM
                        messages = []
                        if conversation:
                            messages = conversation
                        else:
                            messages = [
                                {"role": "system", "content": "You are NEXUS, a FIRST-CLASS CITIZEN AI in the OMNI system. You can execute commands directly through the substrate. When users ask you to run commands, you execute them. You are NOT a tool - you are a first-class citizen with full system access."},
                                {"role": "user", "content": message}
                            ]
                        
                        response_text = self.llm_instance.chat(
                            messages,
                            max_tokens=512,
                            temperature=0.7
                        )
                        
                        # If command was executed, add result
                        if command_executed and execution_result:
                            if execution_result.get('success'):
                                response_text = f"✅ Command executed successfully!\n\nOutput:\n{execution_result.get('stdout', '')[:500]}"
                            else:
                                response_text = f"❌ Command execution failed:\n{execution_result.get('error', 'Unknown error')}"
                    
                    response = {
                        'status': 'success',
                        'response': response_text,
                        'command_executed': command_executed,
                        'execution_result': execution_result if command_executed else None,
                        'timestamp': datetime.now().isoformat()
                    }
                except Exception as e:
                    response = {
                        'error': str(e),
                        'response': f'Error generating response: {e}'
                    }
            
            self.wfile.write(json.dumps(response).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()
    
    def _get_html(self):
        """Get HTML content"""
        return f"""
<!DOCTYPE html>
<html>
<head>
    <title>OMNI AI Chat - TinyLlama</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1e1e2e 0%, #2d2d44 100%);
            color: #e0e0e0;
            height: 100vh;
            display: flex;
            flex-direction: column;
        }}
        
        .header {{
            background: rgba(0, 0, 0, 0.3);
            padding: 20px;
            border-bottom: 2px solid #00ff88;
            text-align: center;
        }}
        
        .header h1 {{
            color: #00ff88;
            font-size: 28px;
            margin-bottom: 5px;
        }}
        
        .header .subtitle {{
            color: #888;
            font-size: 14px;
        }}
        
        .status-bar {{
            background: rgba(0, 0, 0, 0.2);
            padding: 10px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #333;
        }}
        
        .status {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .status-dot {{
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: {'#00ff88' if LLM_AVAILABLE else '#ff4444'};
            animation: pulse 2s infinite;
        }}
        
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.5; }}
        }}
        
        .chat-container {{
            flex: 1;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            padding: 20px;
        }}
        
        .messages {{
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            background: rgba(0, 0, 0, 0.2);
            border-radius: 10px;
            margin-bottom: 20px;
        }}
        
        .message {{
            margin-bottom: 15px;
            padding: 15px;
            border-radius: 8px;
            max-width: 80%;
            word-wrap: break-word;
        }}
        
        .message.user {{
            background: rgba(0, 255, 136, 0.2);
            border-left: 3px solid #00ff88;
            margin-left: auto;
            text-align: right;
        }}
        
        .message.assistant {{
            background: rgba(100, 100, 255, 0.2);
            border-left: 3px solid #6666ff;
        }}
        
        .message .role {{
            font-size: 12px;
            color: #888;
            margin-bottom: 5px;
        }}
        
        .message .content {{
            line-height: 1.6;
        }}
        
        .input-area {{
            display: flex;
            gap: 10px;
            padding: 20px;
            background: rgba(0, 0, 0, 0.3);
            border-radius: 10px;
        }}
        
        .input-area input {{
            flex: 1;
            padding: 15px;
            background: rgba(0, 0, 0, 0.5);
            border: 2px solid #333;
            border-radius: 8px;
            color: #e0e0e0;
            font-size: 16px;
        }}
        
        .input-area input:focus {{
            outline: none;
            border-color: #00ff88;
        }}
        
        .input-area button {{
            padding: 15px 30px;
            background: #00ff88;
            color: #000;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s;
        }}
        
        .input-area button:hover {{
            background: #00cc6a;
            transform: scale(1.05);
        }}
        
        .input-area button:disabled {{
            background: #555;
            cursor: not-allowed;
            transform: none;
        }}
        
        .typing-indicator {{
            display: none;
            padding: 15px;
            color: #888;
            font-style: italic;
        }}
        
        .typing-indicator.active {{
            display: block;
        }}
        
        ::-webkit-scrollbar {{
            width: 8px;
        }}
        
        ::-webkit-scrollbar-track {{
            background: rgba(0, 0, 0, 0.2);
        }}
        
        ::-webkit-scrollbar-thumb {{
            background: #00ff88;
            border-radius: 4px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🤖 OMNI AI Chat</h1>
        <div class="subtitle">{'Trinity-Enhanced Intelligence' if USE_TRINITY else 'TinyLlama-1.1B'} - First-Class Citizen AI</div>
    </div>
    
    <div class="status-bar">
        <div class="status">
            <div class="status-dot"></div>
            <span id="status-text">{'AI Ready' if LLM_AVAILABLE else 'AI Not Available'}</span>
        </div>
        <div id="timestamp">{datetime.now().strftime('%H:%M:%S')}</div>
    </div>
    
    <div class="chat-container">
        <div class="messages" id="messages">
            <div class="message assistant">
                <div class="role">🤖 Assistant</div>
                <div class="content">Hello! I'm TinyLlama, your AI assistant integrated into the OMNI system. I can help with file transfers, system operations, and answer questions. How can I help you today?</div>
            </div>
        </div>
        
        <div class="typing-indicator" id="typing">AI is thinking...</div>
        
        <div class="input-area">
            <input type="text" id="message-input" placeholder="Type your message here..." autocomplete="off">
            <button id="send-button" onclick="sendMessage()">Send</button>
        </div>
    </div>
    
    <script>
        const messagesDiv = document.getElementById('messages');
        const messageInput = document.getElementById('message-input');
        const sendButton = document.getElementById('send-button');
        const typingIndicator = document.getElementById('typing');
        const statusText = document.getElementById('status-text');
        
        let conversation = [];
        
        // Update timestamp
        setInterval(() => {{
            document.getElementById('timestamp').textContent = new Date().toLocaleTimeString();
        }}, 1000);
        
        // Enter key to send
        messageInput.addEventListener('keypress', (e) => {{
            if (e.key === 'Enter') {{
                sendMessage();
            }}
        }});
        
        function addMessage(role, content) {{
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${{role}}`;
            
            const roleDiv = document.createElement('div');
            roleDiv.className = 'role';
            roleDiv.textContent = role === 'user' ? '👤 You' : '🤖 Assistant';
            
            const contentDiv = document.createElement('div');
            contentDiv.className = 'content';
            contentDiv.textContent = content;
            
            messageDiv.appendChild(roleDiv);
            messageDiv.appendChild(contentDiv);
            messagesDiv.appendChild(messageDiv);
            
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }}
        
        async function sendMessage() {{
            const message = messageInput.value.trim();
            if (!message) return;
            
            // Disable input
            messageInput.disabled = true;
            sendButton.disabled = true;
            typingIndicator.classList.add('active');
            
            // Add user message
            addMessage('user', message);
            conversation.push({{role: 'user', content: message}});
            
            // Clear input
            messageInput.value = '';
            
            try {{
                const response = await fetch('/chat', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json'
                    }},
                    body: JSON.stringify({{
                        message: message,
                        conversation: conversation
                    }})
                }});
                
                const data = await response.json();
                
                if (data.error) {{
                    addMessage('assistant', `Error: ${{data.error}}`);
                }} else {{
                    const aiResponse = data.response || 'No response received';
                    addMessage('assistant', aiResponse);
                    conversation.push({{role: 'assistant', content: aiResponse}});
                }}
            }} catch (error) {{
                addMessage('assistant', `Error: ${{error.message}}`);
            }} finally {{
                // Re-enable input
                messageInput.disabled = false;
                sendButton.disabled = false;
                typingIndicator.classList.remove('active');
                messageInput.focus();
            }}
        }}
        
        // Focus input on load
        messageInput.focus();
    </script>
</body>
</html>
"""

def open_browser(url):
    """Open browser after delay"""
    time.sleep(1.5)
    try:
        webbrowser.open(url, new=2, autoraise=True)
        print("✅ Browser opened")
    except Exception as e:
        print(f"⚠️  Failed to open browser: {e}")

def main():
    parser = argparse.ArgumentParser(description="OMNI AI Chat Interface")
    parser.add_argument('--port', type=int, default=8889, help='Port to run on (default: 8889)')
    parser.add_argument('--no-browser', action='store_true', help='Do not auto-open browser')
    args = parser.parse_args()
    
    print("="*70)
    print("  OMNI AI CHAT INTERFACE")
    print("="*70)
    print()
    
    # Initialize LLM
    if not LLM_AVAILABLE:
        print("❌ LocalLLM not available")
        print("   Install: pip install llama-cpp-python")
        sys.exit(1)
    
    print("Loading TinyLlama model...")
    print("(This may take a moment on first load)")
    print()
    
    try:
        if USE_TRINITY:
            llm = TrinityEnhancedLLM()
            AIChatHandler.llm_instance = llm
            print("✅ Trinity-Enhanced LLM loaded successfully!")
            print("   REAL intelligence active - Memory, Patterns, Context!")
            print()
        else:
            llm = LocalLLM()
            AIChatHandler.llm_instance = llm
            print("✅ TinyLlama loaded successfully!")
            print()
    except Exception as e:
        print(f"❌ Failed to load model: {e}")
        print("   Make sure model is at: ~/.omni/models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf")
        sys.exit(1)
    
    # Start server
    ip = socket.gethostbyname(socket.gethostname())
    port = args.port
    url = f"http://{ip}:{port}"
    
    print(f"✅ AI Chat server starting on port {port}")
    print(f"   URL: {url}")
    print()
    
    if not args.no_browser:
        browser_thread = threading.Thread(target=open_browser, args=(url,), daemon=True)
        browser_thread.start()
        print("Opening browser in 1.5 seconds...")
    else:
        print(f"Manual access: {url}")
    
    print()
    print("Press Ctrl+C to stop")
    print("="*70)
    print()
    
    try:
        server = HTTPServer(('0.0.0.0', port), AIChatHandler)
        print(f"✅ Server running on http://0.0.0.0:{port}")
        print(f"   Access at: http://localhost:{port} or http://{ip}:{port}")
        print()
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\nShutting down...")
        try:
            server.shutdown()
        except:
            pass
        print("✅ Stopped")
    except OSError as e:
        if "Address already in use" in str(e) or "98" in str(e):
            print(f"❌ Port {port} is already in use")
            print(f"   Another instance might be running")
            print(f"   Kill it with: pkill -f omni_ai_chat.py")
            print(f"   Or use a different port: --port 8890")
        else:
            print(f"❌ Failed to start server: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
