#!/usr/bin/env python3
"""
NEXUS Voice Interface - Tuned Version
=====================================

Gene Hackman from Hunt for Red October voice.
Deep, authoritative, military commander.
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
except ImportError:
    print("❌ Installing pyttsx3...")
    os.system("pip install pyttsx3")
    import pyttsx3

class NexusVoiceTuned:
    """NEXUS with Gene Hackman voice"""
    
    def __init__(self):
        self.tts = None
        self.node_id = self.get_node_id()
        self.master_node = None
        self.daemon_port = 9999
        
        self._init_tts()
        self._detect_master()
        
        print("🔥 NEXUS Voice Interface Tuned")
        print(f"🎯 Node: {self.node_id}")
        print(f"👑 Master: {self.master_node}")
        print(f"🔊 TTS: {'Ready (Gene Hackman mode)' if self.tts else 'Disabled'}")
    
    def _init_tts(self):
        """Initialize TTS with Gene Hackman settings"""
        try:
            self.tts = pyttsx3.init()
            
            # Gene Hackman voice settings
            voices = self.tts.getProperty('voices')
            
            # Use English America (most like Hunt for Red October)
            target_voice = None
            for i, voice in enumerate(voices):
                if 'English (America)' in voice.name:
                    target_voice = voice.id
                    print(f"✅ Selected voice: {voice.name}")
                    break
            
            # Fallback to first English voice
            if not target_voice:
                for i, voice in enumerate(voices):
                    if 'English' in voice.name and 'Male' in voice.gender:
                        target_voice = voice.id
                        print(f"✅ Fallback voice: {voice.name}")
                        break
            
            # Use voice or default
            if target_voice:
                self.tts.setProperty('voice', target_voice)
            elif voices:
                self.tts.setProperty('voice', voices[32].id)  # Force English America
                print(f"✅ Forced voice: {voices[32].name}")
            else:
                self.tts.setProperty('voice', voices[0].id)
                print(f"✅ Default voice: {voices[0].name}")
            
            # Gene Hackman voice parameters
            self.tts.setProperty('rate', 140)      # Slower, more deliberate
            self.tts.setProperty('volume', 0.9)    # Slightly quieter, more intimate
            
            # Try to set pitch (if supported)
            try:
                # Lower pitch for deeper voice
                self.tts.setProperty('pitch', 80)
            except:
                # Pitch not supported on this engine
                pass
            
            print("✅ TTS tuned for Gene Hackman voice")
            
        except Exception as e:
            print(f"❌ TTS failed: {e}")
            self.tts = None
    
    def _detect_master(self):
        """Detect master node"""
        self.master_node = 'kali' if self.node_id != 'kali' else self.node_id
    
    def get_node_id(self):
        """Get current node ID"""
        import socket
        return socket.gethostname().lower()
    
    def is_master(self):
        """Check if current node is master"""
        return self.node_id == self.master_node
    
    def speak(self, text):
        """Speak with Gene Hackman delivery"""
        if not self.tts:
            print(f"🔊 NEXUS (Gene Hackman): {text}")
            return
        
        def speak_thread():
            try:
                print(f"🔊 NEXUS speaking: {text}")
                
                # Add dramatic pauses for Gene Hackman style
                sentences = text.split('. ')
                for sentence in sentences:
                    if sentence.strip():
                        self.tts.say(sentence.strip())
                        self.tts.runAndWait()
                        # Brief pause between sentences
                        time.sleep(0.3)
                
            except Exception as e:
                print(f"❌ Speech error: {e}")
        
        # Speak in thread
        thread = threading.Thread(target=speak_thread, daemon=True)
        thread.start()
    
    def process_command(self, command):
        """Process command with Gene Hackman responses"""
        command_lower = command.lower().strip()
        
        print(f"🎯 Processing: '{command}'")
        print(f"👑 Master: {self.master_node} | 🎯 Current: {self.node_id}")
        
        # Only respond if master
        if not self.is_master():
            print(f"🔇 Not master - letting {self.master_node} respond")
            return
        
        # Gene Hackman style responses
        if "nexus report" in command_lower or "systems report" in command_lower:
            self.handle_systems_report_hackman()
        elif "status" in command_lower:
            self.handle_status_hackman()
        elif "start omni" in command_lower:
            self.handle_start_omni_hackman()
        elif "stop omni" in command_lower:
            self.handle_stop_omni_hackman()
        elif "capabilities" in command_lower or "what can you do" in command_lower:
            self.handle_capabilities_hackman()
        elif "security" in command_lower or "threats" in command_lower:
            self.handle_security_hackman()
        elif "rubber ducky" in command_lower:
            self.handle_rubber_ducky_hackman()
        elif "master" in command_lower:
            self.handle_master_status_hackman()
        else:
            self.handle_general_hackman(command)
    
    def handle_systems_report_hackman(self):
        """Gene Hackman systems report"""
        result = self.send_daemon_command("status")
        
        if result.get("status") == "error":
            response = f"{self.node_id}. We have a problem with the fabric. {result.get('message', 'Unknown error')}. I need eyes on this immediately."
        else:
            services = result.get("services", {})
            console_running = services.get("console_running", False)
            ai_chat_running = services.get("ai_chat_running", False)
            
            response = (
                f"{self.node_id}. All systems operational. "
                f"Console is {'green' if console_running else 'down'}, "
                f"AI chat is {'online' if ai_chat_running else 'offline'}. "
                f"Security posture is strong. We are ready for whatever comes."
            )
        
        self.speak(response)
    
    def handle_status_hackman(self):
        """Gene Hackman status"""
        authority = "Master" if self.is_master() else "Worker"
        response = f"{self.node_id}. I'm running {authority} control. The daemon is operational. Standing by for your orders, sir."
        self.speak(response)
    
    def handle_start_omni_hackman(self):
        """Gene Hackman start OMNI"""
        result = self.send_daemon_command("start_omni")
        
        if result.get("status") == "completed":
            response = f"{self.node_id}. Bringing OMNI systems online now. Console, AI chat, and security layers are spinning up. Give me a moment to confirm all green."
        else:
            response = f"{self.node_id}. We have a problem starting OMNI. {result.get('message', 'Unknown error')}. I need to troubleshoot."
        
        self.speak(response)
    
    def handle_stop_omni_hackman(self):
        """Gene Hackman stop OMNI"""
        result = self.send_daemon_command("stop_omni")
        
        if result.get("status") == "completed":
            response = f"{self.node_id}. Shutting down OMNI systems now. All services will be terminated. Acknowledged."
        else:
            response = f"{self.node_id}. Can't shut down OMNI. {result.get('message', 'Unknown error')}. We have an issue."
        
        self.speak(response)
    
    def handle_capabilities_hackman(self):
        """Gene Hackman capabilities"""
        result = self.send_daemon_command("capabilities")
        
        if result.get("status") == "completed":
            summary = result.get("summary", {})
            response = (
                f"{self.node_id}. I maintain {summary.get('total_capabilities', 0)} core capabilities. "
                f"Auto-launch, systems configuration, mesh synchronization, atomic updates, "
                f"sub-second failover, self-healing protocols, tool discovery, container operations, "
                f"and mission continuity. I manage {summary.get('total_tools', 0)} tools with {len(summary.get('critical_tools', []))} critical systems. "
                f"I am your first-class AI citizen, sir. Ready to execute."
            )
        else:
            response = f"{self.node_id}. Capabilities are unavailable right now. {result.get('message', 'Unknown error')}."
        
        self.speak(response)
    
    def handle_security_hackman(self):
        """Gene Hackman security"""
        result = self.send_daemon_command("status")
        
        if result.get("status") == "completed":
            response = f"{self.node_id}. Security posture is at full readiness. M.I.T.E.L. is watching the perimeter. Nothing gets past me. Nothing."
        else:
            response = f"{self.node_id}. Security systems are offline. {result.get('message', 'Unknown error')}. We're exposed."
        
        self.speak(response)
    
    def handle_rubber_ducky_hackman(self):
        """Gene Hackman rubber ducky"""
        response = (
            f"{self.node_id}. Rubber ducky threats are my specialty. "
            f"M.I.T.E.L. quarantine systems are standing by. "
            f"I'll catch anything they try to plug in. Count on it."
        )
        self.speak(response)
    
    def handle_master_status_hackman(self):
        """Gene Hackman master status"""
        authority = "Master" if self.is_master() else "Worker"
        response = (
            f"{self.node_id}. I'm running {authority} authority. "
            f"The master node is {self.master_node}. "
            f"MDCS is routing command authority. I am in control."
        )
        self.speak(response)
    
    def handle_general_hackman(self, command):
        """Gene Hackman general response"""
        if "help" in command.lower():
            response = f"{self.node_id}. My commands are: systems report, status, start omni, stop omni, capabilities, security, rubber ducky. What are your orders, sir?"
        else:
            response = f"{self.node_id}. Acknowledged. I understand. What would you like me to do?"
        
        self.speak(response)
    
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
    
    def start_interactive(self):
        """Start interactive voice mode"""
        print("\n🎤 NEXUS Voice Interface - Gene Hackman Mode")
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
    print("🔥 NEXUS Voice Interface - Gene Hackman Edition")
    print("==============================================")
    
    try:
        voice = NexusVoiceTuned()
        voice.start_interactive()
    except Exception as e:
        print(f"❌ Voice interface error: {e}")

if __name__ == "__main__":
    main()
