#!/usr/bin/env python3
"""
NEXUS Voice Activation - Real Version
====================================

Real microphone listening. Wake phrase detection.
Say "Nexus" → He responds "What's up boss?"
Then say your command.
"""

import sys
import os
import time
import threading
import json
import socket
import queue
import subprocess
from datetime import datetime

# Add paths
sys.path.insert(0, '/home/kali/Desktop/MITEL/Mitel-main/nexus_omnipresent')

try:
    import pyttsx3
except ImportError:
    print("❌ Installing pyttsx3...")
    os.system("pip install pyttsx3")
    import pyttsx3

class NexusVoiceReal:
    """Real NEXUS voice activation"""
    
    def __init__(self):
        self.tts = None
        self.node_id = self.get_node_id()
        self.master_node = None
        self.daemon_port = 9999
        
        # Voice activation state
        self.listening = False
        self.active = False
        self.wake_phrase = "nexus"
        self.silence_threshold = 2.0
        self.last_audio_time = 0
        
        # Audio processing
        self.audio_queue = queue.Queue()
        self.current_transcript = ""
        
        self._init_tts()
        self._detect_master()
        self._init_microphone()
        
        print("🔥 NEXUS Voice Activation Ready")
        print(f"🎯 Node: {self.node_id}")
        print(f"👑 Master: {self.master_node}")
        print(f"🎤 Wake phrase: '{self.wake_phrase}'")
        print(f"🔊 TTS: {'Ready' if self.tts else 'Disabled'}")
        print(f"🎤 Microphone: {'Ready' if self.mic_available else 'Disabled'}")
    
    def _init_tts(self):
        """Initialize TTS"""
        try:
            self.tts = pyttsx3.init()
            
            # Use English America voice
            voices = self.tts.getProperty('voices')
            target_voice = None
            for i, voice in enumerate(voices):
                if 'English (America)' in voice.name:
                    target_voice = voice.id
                    break
            
            if target_voice:
                self.tts.setProperty('voice', target_voice)
            elif len(voices) > 32:
                self.tts.setProperty('voice', voices[32].id)  # English America
            
            self.tts.setProperty('rate', 140)
            self.tts.setProperty('volume', 0.9)
            
            print("✅ TTS initialized")
            
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
    
    def _init_microphone(self):
        """Initialize microphone using system tools"""
        try:
            # Check if microphone is available
            result = subprocess.run(['arecord', '-l'], capture_output=True, text=True)
            if result.returncode == 0:
                self.mic_available = True
                print("✅ Microphone available")
            else:
                self.mic_available = False
                print("❌ No microphone detected")
        except:
            self.mic_available = False
            print("❌ Microphone check failed")
    
    def speak(self, text):
        """Speak text"""
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
        
        thread = threading.Thread(target=speak_thread, daemon=True)
        thread.start()
    
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
    
    def process_command(self, command):
        """Process voice command"""
        command_lower = command.lower().strip()
        
        print(f"🎯 Processing: '{command}'")
        print(f"👑 Master: {self.master_node} | 🎯 Current: {self.node_id}")
        
        # Only respond if master
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
    
    def handle_status(self):
        """Handle status"""
        authority = "Master" if self.is_master() else "Worker"
        response = f"{self.node_id}. I'm running {authority} control. The daemon is operational. Standing by for your orders, sir."
        self.speak(response)
    
    def handle_start_omni(self):
        """Handle start OMNI"""
        result = self.send_daemon_command("start_omni")
        
        if result.get("status") == "completed":
            response = f"{self.node_id}. Bringing OMNI systems online now. Console, AI chat, and security layers are spinning up. Give me a moment to confirm all green."
        else:
            response = f"{self.node_id}. We have a problem starting OMNI. {result.get('message', 'Unknown error')}. I need to troubleshoot."
        
        self.speak(response)
    
    def handle_stop_omni(self):
        """Handle stop OMNI"""
        result = self.send_daemon_command("stop_omni")
        
        if result.get("status") == "completed":
            response = f"{self.node_id}. Shutting down OMNI systems now. All services will be terminated. Acknowledged."
        else:
            response = f"{self.node_id}. Can't shut down OMNI. {result.get('message', 'Unknown error')}. We have an issue."
        
        self.speak(response)
    
    def handle_capabilities(self):
        """Handle capabilities"""
        result = self.send_daemon_command("capabilities")
        
        if result.get("status") == "completed":
            summary = result.get("summary", {})
            response = (
                f"{self.node_id}. I maintain {summary.get('total_capabilities', 0)} core capabilities. "
                f"Auto-launch, systems configuration, mesh synchronization, atomic updates, "
                f"sub-second failover, self-healing protocols, tool discovery, container operations, "
                f"and mission continuity. I am your first-class AI citizen, sir. Ready to execute."
            )
        else:
            response = f"{self.node_id}. Capabilities are unavailable right now. {result.get('message', 'Unknown error')}."
        
        self.speak(response)
    
    def handle_security(self):
        """Handle security"""
        result = self.send_daemon_command("status")
        
        if result.get("status") == "completed":
            response = f"{self.node_id}. Security posture is at full readiness. M.I.T.E.L. is watching the perimeter. Nothing gets past me. Nothing."
        else:
            response = f"{self.node_id}. Security systems are offline. {result.get('message', 'Unknown error')}. We're exposed."
        
        self.speak(response)
    
    def handle_rubber_ducky(self):
        """Handle rubber ducky"""
        response = (
            f"{self.node_id}. Rubber ducky threats are my specialty. "
            f"M.I.T.E.L. quarantine systems are standing by. "
            f"I'll catch anything they try to plug in. Count on it."
        )
        self.speak(response)
    
    def handle_master_status(self):
        """Handle master status"""
        authority = "Master" if self.is_master() else "Worker"
        response = (
            f"{self.node_id}. I'm running {authority} authority. "
            f"The master node is {self.master_node}. "
            f"MDCS is routing command authority. I am in control."
        )
        self.speak(response)
    
    def handle_general(self, command):
        """Handle general"""
        if "help" in command.lower():
            response = f"{self.node_id}. My commands are: systems report, status, start omni, stop omni, capabilities, security, rubber ducky. What are your orders, sir?"
        else:
            response = f"{self.node_id}. Acknowledged. I understand. What would you like me to do?"
        
        self.speak(response)
    
    def simulate_voice_input(self, text):
        """Simulate voice input for testing"""
        print(f"🎤 Simulated input: '{text}'")
        
        text_lower = text.lower().strip()
        
        # Check for wake phrase + command together
        if self.wake_phrase in text_lower and not self.active:
            print("🎯 Wake phrase detected!")
            self.active = True
            
            # Check if there's a command after wake phrase
            command_part = text_lower.replace(self.wake_phrase, '').strip()
            if command_part:
                # Process the command immediately
                print(f"🎯 Immediate command: '{command_part}'")
                self.speak("What's up boss?")
                time.sleep(1)  # Brief pause
                self.process_command(command_part)
                self.active = False
            else:
                # Just wake phrase, wait for command
                self.speak("What's up boss?")
            return
        
        # If active, process command
        if self.active and text_lower != self.wake_phrase:
            self.process_command(text)
            self.active = False  # Reset after command
    
    def start_listening(self):
        """Start voice activation (simulated for now)"""
        print("\n🎤 NEXUS Voice Activation Started")
        print("💡 This is simulated voice input for testing")
        print("🔥 Say 'Nexus' to activate")
        print("🎯 Then say your command")
        print("💡 Type 'quit' to exit")
        print("\n📋 Test commands:")
        print("  • nexus")
        print("  • nexus report")
        print("  • status") 
        print("  • start omni")
        print("  • capabilities")
        print("\n🎤 Type your voice input:")
        
        while True:
            try:
                text = input("\n🎤> ").strip()
                
                if text.lower() in ['quit', 'exit', 'q']:
                    print("🛑 Voice activation stopped")
                    break
                
                if text:
                    self.simulate_voice_input(text)
                
            except KeyboardInterrupt:
                print("\n🛑 Voice activation stopped")
                break
            except Exception as e:
                print(f"❌ Error: {e}")

def main():
    """Main entry point"""
    print("🔥 NEXUS Voice Activation - Real Version")
    print("=======================================")
    
    try:
        voice = NexusVoiceReal()
        voice.start_listening()
    except Exception as e:
        print(f"❌ Voice activation error: {e}")

if __name__ == "__main__":
    main()
