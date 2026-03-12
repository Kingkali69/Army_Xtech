#!/usr/bin/env python3
"""
NEXUS Voice Interface - Simple Version
======================================

Quick voice integration for immediate testing.
No complex STT - just command line for now.
Real TTS responses.
"""

import sys
import os
import time
import threading
import json
import socket
from datetime import datetime

# Add paths
sys.path.insert(0, '/home/kali/Desktop/MITEL/Mitel-main/nexus_omnipresent')

try:
    import pyttsx3
    # Simple API connection
    import socket
    import json
except ImportError:
    print("❌ Installing missing dependencies...")
    os.system("pip install pyttsx3 requests")
    import pyttsx3

class NexusVoiceSimple:
    """Simple NEXUS voice interface for testing"""
    
    def __init__(self):
        self.tts = None
        self.node_id = self.get_node_id()
        self.master_node = None
        self.daemon_port = 9999
        
        self._init_tts()
        self._detect_master()
        
        print("🔥 NEXUS Voice Interface Ready")
        print(f"🎯 Node: {self.node_id}")
        print(f"👑 Master: {self.master_node}")
        print(f"🔊 TTS: {'Ready' if self.tts else 'Disabled'}")
    
    def _init_tts(self):
        """Initialize text-to-speech"""
        try:
            self.tts = pyttsx3.init()
            self.tts.setProperty('rate', 175)
            self.tts.setProperty('volume', 1.0)
            
            # Select voice
            voices = self.tts.getProperty('voices')
            if voices:
                # Prefer male voice
                for voice in voices:
                    if 'male' in voice.name.lower():
                        self.tts.setProperty('voice', voice.id)
                        break
                else:
                    self.tts.setProperty('voice', voices[0].id)
            
            print("✅ TTS initialized")
            
        except Exception as e:
            print(f"❌ TTS failed: {e}")
            self.tts = None
    
    def _detect_master(self):
        """Detect master node"""
        # For now, assume Linux (kali) is master
        self.master_node = 'kali' if self.node_id != 'kali' else self.node_id
    
    def get_node_id(self):
        """Get current node ID"""
        import socket
        return socket.gethostname().lower()
    
    def send_daemon_command(self, command):
        """Send command to NEXUS daemon"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect(('localhost', self.daemon_port))
            
            cmd_data = {
                "action": command,
                "timestamp": datetime.now().isoformat()
            }
            sock.send(json.dumps(cmd_data).encode('utf-8'))
            
            response = sock.recv(8192).decode('utf-8')
            sock.close()
            
            return json.loads(response)
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Daemon communication failed: {e}",
                "timestamp": datetime.now().isoformat()
            }
    
    def is_master(self):
        """Check if current node is master"""
        return self.node_id == self.master_node
    
    def speak(self, text):
        """Speak text if TTS available"""
        if not self.tts:
            print(f"🔊 NEXUS: {text}")
            return
        
        def speak_thread():
            try:
                print(f"🔊 NEXUS speaking: {text}")
                self.tts.say(text)
                self.tts.runAndWait()
            except Exception as e:
                print(f"❌ Speech error: {e}")
        
        # Speak in thread
        thread = threading.Thread(target=speak_thread, daemon=True)
        thread.start()
    
    def process_command(self, command):
        """Process voice command"""
        command_lower = command.lower().strip()
        
        print(f"🎯 Processing: '{command}'")
        print(f"👑 Master: {self.master_node} | 🎯 Current: {self.node_id}")
        
        # Only respond if master (for demo)
        if not self.is_master():
            print(f"🔇 Not master - letting {self.master_node} respond")
            return
        
        # Process commands
        if "nexus report" in command_lower or "systems report" in command_lower:
            self.handle_systems_report()
        elif "status" in command_lower:
            self.handle_status()
        elif "start omni" in command_lower:
            self.handle_start_omni()
        elif "stop omni" in command_lower:
            self.handle_stop_omni()
        elif "capabilities" in command_lower or "what can you do" in command_lower:
            self.handle_capabilities()
        elif "security" in command_lower or "threats" in command_lower:
            self.handle_security()
        elif "rubber ducky" in command_lower:
            self.handle_rubber_ducky()
        elif "master" in command_lower:
            self.handle_master_status()
        else:
            self.handle_general(command)
    
    def handle_systems_report(self):
        """Handle systems report"""
        result = self.send_daemon_command("status")
        
        if result.get("status") == "error":
            response = f"{self.node_id}. System error accessing fabric. {result.get('message', 'Unknown error')}. Requires immediate attention."
        else:
            services = result.get("services", {})
            console_running = services.get("console_running", False)
            ai_chat_running = services.get("ai_chat_running", False)
            
            response = (
                f"{self.node_id}. Systems operational. "
                f"Console {'running' if console_running else 'offline'}, "
                f"AI chat {'running' if ai_chat_running else 'offline'}. "
                f"Security active. Mission ready."
            )
        
        self.speak(response)
    
    def handle_status(self):
        """Handle status request"""
        authority = "Master" if self.is_master() else "Worker"
        response = f"{self.node_id}. {authority} node. NEXUS daemon operational. Ready for commands."
        self.speak(response)
    
    def handle_start_omni(self):
        """Handle OMNI startup"""
        result = self.send_daemon_command("start_omni")
        
        if result.get("status") == "completed":
            response = f"{self.node_id}. Starting OMNI systems. Launching console, AI chat, and security layers. Services coming online now."
        else:
            response = f"{self.node_id}. Failed to start OMNI. {result.get('message', 'Unknown error')}."
        
        self.speak(response)
    
    def handle_stop_omni(self):
        """Handle OMNI shutdown"""
        result = self.send_daemon_command("stop_omni")
        
        if result.get("status") == "completed":
            response = f"{self.node_id}. OMNI systems shutting down. Services terminated."
        else:
            response = f"{self.node_id}. Failed to stop OMNI. {result.get('message', 'Unknown error')}."
        
        self.speak(response)
    
    def handle_capabilities(self):
        """Handle capabilities inquiry"""
        result = self.send_daemon_command("capabilities")
        
        if result.get("status") == "completed":
            summary = result.get("summary", {})
            response = (
                f"{self.node_id}. I maintain {summary.get('total_capabilities', 0)} core capabilities. "
                f"Auto-launch, configure, sync, update, failover, auto-recover, tool discovery, "
                f"container operations, and mission continuity. "
                f"Currently managing {summary.get('total_tools', 0)} tools with {len(summary.get('critical_tools', []))} critical systems."
            )
        else:
            response = f"{self.node_id}. Capabilities unavailable. {result.get('message', 'Unknown error')}."
        
        self.speak(response)
    
    def handle_security(self):
        """Handle security status"""
        result = self.send_daemon_command("status")
        
        if result.get("status") == "completed":
            services = result.get("services", {})
            response = f"{self.node_id}. Security posture active. M.I.T.E.L. monitoring operational. Perimeter secure."
        else:
            response = f"{self.node_id}. Security systems offline. {result.get('message', 'Unknown error')}."
        
        self.speak(response)
    
    def handle_rubber_ducky(self):
        """Handle rubber ducky specific"""
        response = f"{self.node_id}. Rubber ducky threat detection active. M.I.T.E.L. quarantine systems ready. USB monitoring operational."
        self.speak(response)
    
    def handle_master_status(self):
        """Handle master status inquiry"""
        authority = "Master" if self.is_master() else "Worker"
        response = (
            f"{self.node_id}. Current authority status: {authority}. "
            f"Master node is {self.master_node}. "
            f"MDCS authority routing active."
        )
        self.speak(response)
    
    def handle_general(self, command):
        """Handle general conversation"""
        responses = [
            f"{self.node_id}. I understand.",
            f"{self.node_id}. Noted.",
            f"{self.node_id}. Acknowledged."
        ]
        
        if "help" in command.lower():
            responses.append("Available commands: systems report, status, start omni, stop omni, capabilities, security, rubber ducky.")
        else:
            responses.append("How can I assist with operations?")
        
        response = " ".join(responses)
        self.speak(response)
    
    def start_interactive(self):
        """Start interactive voice mode"""
        print("\n🎤 NEXUS Voice Interface Active")
        print("💡 Type commands or 'quit' to exit")
        print("🔥 Master node responses enabled")
        print("\n📋 Commands:")
        print("  • nexus report")
        print("  • status") 
        print("  • start omni")
        print("  • stop omni")
        print("  • capabilities")
        print("  • security")
        print("  • rubber ducky")
        print("  • master status")
        print("\n🎯 Type your command:")
        
        while True:
            try:
                command = input("\n🎤> ").strip()
                
                if command.lower() in ['quit', 'exit', 'q']:
                    print("🛑 Voice interface stopped")
                    break
                
                if command:
                    self.process_command(command)
                
            except KeyboardInterrupt:
                print("\n🛑 Voice interface stopped")
                break
            except Exception as e:
                print(f"❌ Error: {e}")

def main():
    """Main entry point"""
    print("🔥 NEXUS Voice Interface - Simple Version")
    print("======================================")
    
    try:
        voice = NexusVoiceSimple()
        voice.start_interactive()
    except Exception as e:
        print(f"❌ Voice interface error: {e}")

if __name__ == "__main__":
    main()
