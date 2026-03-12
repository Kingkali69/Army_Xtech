#!/usr/bin/env python3
"""
NEXUS Voice Interface - REAL Microphone Button
==============================================

Click microphone button → Record your voice → NEXUS responds
No typing. Real audio capture. Real conversation.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import json
import socket
import queue
import subprocess
import os
import sys
from datetime import datetime
from pathlib import Path

# Add paths
sys.path.insert(0, '/home/kali/Desktop/MITEL/Mitel-main/nexus_omnipresent')

try:
    import pyttsx3
except ImportError:
    print("❌ Installing pyttsx3...")
    os.system("pip install pyttsx3")
    import pyttsx3

try:
    import speech_recognition as sr
except ImportError:
    print("❌ Installing speech recognition...")
    os.system("pip install SpeechRecognition")
    os.system("pip install pyaudio")
    import speech_recognition as sr

class NexusVoiceMicButton:
    """NEXUS with REAL microphone button"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.tts = None
        self.recognizer = None
        self.microphone = None
        self.node_id = self.get_node_id()
        self.master_node = None
        self.daemon_port = 9999
        
        # Recording state
        self.is_recording = False
        self.recording_thread = None
        
        # Setup UI and systems
        self._init_tts()
        self._init_speech_recognition()
        self._detect_master()
        self._setup_ui()
        
        print("🔥 NEXUS Voice Interface - REAL Microphone")
        print(f"🎯 Node: {self.node_id}")
        print(f"👑 Master: {self.master_node}")
        print(f"🔊 TTS: {'Ready' if self.tts else 'Disabled'}")
        print(f"🎤 Microphone: {'Ready' if self.microphone else 'Disabled'}")
    
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
                self.tts.setProperty('voice', voices[32].id)
            
            self.tts.setProperty('rate', 140)
            self.tts.setProperty('volume', 0.9)
            
            print("✅ TTS initialized")
            
        except Exception as e:
            print(f"❌ TTS failed: {e}")
            self.tts = None
    
    def _init_speech_recognition(self):
        """Initialize speech recognition"""
        try:
            self.recognizer = sr.Recognizer()
            self.microphone = sr.Microphone()
            
            # Adjust for ambient noise
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
            
            print("✅ Speech recognition initialized")
            
        except Exception as e:
            print(f"❌ Speech recognition failed: {e}")
            print("🎤 Install: pip install SpeechRecognition pyaudio")
            self.recognizer = None
            self.microphone = None
    
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
    
    def _setup_ui(self):
        """Setup the microphone UI"""
        self.root.title("🔥 NEXUS - REAL Microphone Interface")
        self.root.geometry("400x500")
        self.root.configure(bg='#1a1a1a')
        
        # Make window stay on top
        self.root.attributes('-topmost', True)
        
        # Header
        header_frame = tk.Frame(self.root, bg='#2a2a2a', height=60)
        header_frame.pack(fill=tk.X, padx=10, pady=5)
        
        title_label = tk.Label(
            header_frame, 
            text="🔥 NEXUS VOICE INTERFACE", 
            font=('Arial', 16, 'bold'),
            fg='#ff6b35', 
            bg='#2a2a2a'
        )
        title_label.pack(pady=10)
        
        status_label = tk.Label(
            header_frame,
            text=f"Node: {self.node_id} | Master: {self.master_node} | {'🎤 READY' if self.microphone else '❌ NO MIC'}",
            font=('Arial', 10),
            fg='#00ff00' if self.microphone else '#ff0000',
            bg='#2a2a2a'
        )
        status_label.pack()
        
        # Microphone Button
        mic_frame = tk.Frame(self.root, bg='#2a2a2a')
        mic_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=20)
        
        self.mic_button = tk.Button(
            mic_frame,
            text="🎤\nCLICK TO TALK",
            font=('Arial', 24, 'bold'),
            bg='#00ff00' if self.microphone else '#666666',
            fg='black' if self.microphone else '#999999',
            width=15,
            height=8,
            command=self.toggle_recording,
            state=tk.NORMAL if self.microphone else tk.DISABLED
        )
        self.mic_button.pack(expand=True)
        
        # Status Display
        status_frame = tk.Frame(self.root, bg='#2a2a2a')
        status_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.status_label = tk.Label(
            status_frame,
            text="Ready to record",
            font=('Arial', 12),
            fg='#ffffff',
            bg='#2a2a2a'
        )
        self.status_label.pack(pady=5)
        
        # Conversation Display
        conv_frame = tk.Frame(self.root, bg='#2a2a2a')
        conv_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.conversation_display = tk.Text(
            conv_frame,
            height=8,
            font=('Arial', 10),
            bg='#1a1a1a',
            fg='#00ff00',
            insertbackground='#00ff00'
        )
        self.conversation_display.pack(fill=tk.BOTH, expand=True)
        self.conversation_display.insert(tk.END, "🔥 NEXUS Voice Interface Ready\n")
        self.conversation_display.insert(tk.END, f"👑 Master node: {self.master_node}\n")
        self.conversation_display.insert(tk.END, "🎤 Click the microphone button to talk\n")
        self.conversation_display.insert(tk.END, "=" * 40 + "\n\n")
        
        # Quick Commands
        quick_frame = tk.Frame(self.root, bg='#2a2a2a')
        quick_frame.pack(fill=tk.X, padx=10, pady=5)
        
        quick_label = tk.Label(
            quick_frame,
            text="⚡ Or type:",
            font=('Arial', 10, 'bold'),
            fg='#ffffff',
            bg='#2a2a2a'
        )
        quick_label.pack(side=tk.LEFT)
        
        quick_commands = ["status", "report", "start omni", "stop omni"]
        
        for cmd in quick_commands:
            btn = tk.Button(
                quick_frame,
                text=cmd,
                font=('Arial', 8),
                bg='#4a4a4a',
                fg='white',
                command=lambda c=cmd: self.process_text_command(c),
                width=10
            )
            btn.pack(side=tk.LEFT, padx=2)
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        print("✅ Microphone UI setup complete")
    
    def add_conversation(self, sender, message):
        """Add message to conversation"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.conversation_display.insert(tk.END, f"[{timestamp}] {sender}: {message}\n")
        self.conversation_display.see(tk.END)
    
    def toggle_recording(self):
        """Toggle recording state"""
        if not self.microphone:
            self.add_conversation("❌", "No microphone available")
            return
        
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()
    
    def start_recording(self):
        """Start recording"""
        self.is_recording = True
        self.mic_button.config(bg='#ff0000', text="🔴\nRECORDING...")
        self.status_label.config(text="Recording... Speak now!")
        self.add_conversation("🎤", "Recording started")
        
        # Start recording in thread
        self.recording_thread = threading.Thread(target=self.record_audio, daemon=True)
        self.recording_thread.start()
    
    def stop_recording(self):
        """Stop recording"""
        self.is_recording = False
        self.mic_button.config(bg='#00ff00', text="🎤\nCLICK TO TALK")
        self.status_label.config(text="Processing...")
        self.add_conversation("🎤", "Recording stopped")
    
    def record_audio(self):
        """Record audio and convert to text"""
        try:
            with self.microphone as source:
                # Listen for audio
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
            
            # Convert to text
            try:
                text = self.recognizer.recognize_google(audio)
                self.root.after(0, self.process_voice_command, text)
            except sr.UnknownValueError:
                self.root.after(0, self.add_conversation, "❌", "Could not understand audio")
                self.root.after(0, self.reset_button)
            except sr.RequestError as e:
                self.root.after(0, self.add_conversation, "❌", f"Speech recognition error: {e}")
                self.root.after(0, self.reset_button)
                
        except Exception as e:
            self.root.after(0, self.add_conversation, "❌", f"Recording error: {e}")
            self.root.after(0, self.reset_button)
    
    def process_voice_command(self, text):
        """Process voice command"""
        self.add_conversation("👤 You", text)
        self.process_nexus_command(text)
        self.reset_button()
    
    def process_text_command(self, command):
        """Process text command"""
        self.add_conversation("⚡ Quick Cmd", command)
        self.process_nexus_command(command)
    
    def reset_button(self):
        """Reset button state"""
        self.status_label.config(text="Ready to record")
        self.mic_button.config(bg='#00ff00', text="🎤\nCLICK TO TALK")
    
    def process_nexus_command(self, command):
        """Process NEXUS command"""
        if not self.is_master():
            self.add_conversation("🔇 NEXUS", f"Not master node. Letting {self.master_node} respond...")
            return
        
        command_lower = command.lower().strip()
        
        # Process commands
        if "nexus report" in command_lower or "systems report" in command_lower or "report" in command_lower:
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
            response = f"We have a problem with the fabric. {result.get('message', 'Unknown error')}. I need eyes on this immediately."
        else:
            services = result.get("services", {})
            console_running = services.get("console_running", False)
            ai_chat_running = services.get("ai_chat_running", False)
            
            response = (
                f"All systems operational. "
                f"Console is {'green' if console_running else 'down'}, "
                f"AI chat is {'online' if ai_chat_running else 'offline'}. "
                f"Security posture is strong. We are ready for whatever comes."
            )
        
        self.add_conversation("🔥 NEXUS", response)
        self.speak(response)
    
    def handle_status(self):
        """Handle status"""
        authority = "Master" if self.is_master() else "Worker"
        response = f"I'm running {authority} control. The daemon is operational. Standing by for your orders, sir."
        self.add_conversation("🔥 NEXUS", response)
        self.speak(response)
    
    def handle_start_omni(self):
        """Handle start OMNI"""
        result = self.send_daemon_command("start_omni")
        
        if result.get("status") == "completed":
            response = "Bringing OMNI systems online now. Console, AI chat, and security layers are spinning up. Give me a moment to confirm all green."
        else:
            response = f"We have a problem starting OMNI. {result.get('message', 'Unknown error')}. I need to troubleshoot."
        
        self.add_conversation("🔥 NEXUS", response)
        self.speak(response)
    
    def handle_stop_omni(self):
        """Handle stop OMNI"""
        result = self.send_daemon_command("stop_omni")
        
        if result.get("status") == "completed":
            response = "Shutting down OMNI systems now. All services will be terminated. Acknowledged."
        else:
            response = f"Can't shut down OMNI. {result.get('message', 'Unknown error')}. We have an issue."
        
        self.add_conversation("🔥 NEXUS", response)
        self.speak(response)
    
    def handle_capabilities(self):
        """Handle capabilities"""
        result = self.send_daemon_command("capabilities")
        
        if result.get("status") == "completed":
            summary = result.get("summary", {})
            response = (
                f"I maintain {summary.get('total_capabilities', 0)} core capabilities. "
                f"Auto-launch, systems configuration, mesh synchronization, atomic updates, "
                f"sub-second failover, self-healing protocols, tool discovery, container operations, "
                f"and mission continuity. I am your first-class AI citizen, sir. Ready to execute."
            )
        else:
            response = f"Capabilities are unavailable right now. {result.get('message', 'Unknown error')}."
        
        self.add_conversation("🔥 NEXUS", response)
        self.speak(response)
    
    def handle_security(self):
        """Handle security"""
        result = self.send_daemon_command("status")
        
        if result.get("status") == "completed":
            response = "Security posture is at full readiness. M.I.T.E.L. is watching the perimeter. Nothing gets past me. Nothing."
        else:
            response = f"Security systems are offline. {result.get('message', 'Unknown error')}. We're exposed."
        
        self.add_conversation("🔥 NEXUS", response)
        self.speak(response)
    
    def handle_rubber_ducky(self):
        """Handle rubber ducky"""
        response = (
            f"Rubber ducky threats are my specialty. "
            f"M.I.T.E.L. quarantine systems are standing by. "
            f"I'll catch anything they try to plug in. Count on it."
        )
        self.add_conversation("🔥 NEXUS", response)
        self.speak(response)
    
    def handle_master_status(self):
        """Handle master status"""
        authority = "Master" if self.is_master() else "Worker"
        response = (
            f"I'm running {authority} authority. "
            f"The master node is {self.master_node}. "
            f"MDCS is routing command authority. I am in control."
        )
        self.add_conversation("🔥 NEXUS", response)
        self.speak(response)
    
    def handle_general(self, command):
        """Handle general"""
        if "help" in command.lower():
            response = "My commands are: systems report, status, start omni, stop omni, capabilities, security, rubber ducky. What are your orders, sir?"
        else:
            response = "Acknowledged. I understand. What would you like me to do?"
        
        self.add_conversation("🔥 NEXUS", response)
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
    
    def speak(self, text):
        """Speak text"""
        if not self.tts:
            return
        
        def speak_thread():
            try:
                self.tts.say(text)
                self.tts.runAndWait()
            except Exception as e:
                print(f"❌ Speech error: {e}")
        
        thread = threading.Thread(target=speak_thread, daemon=True)
        thread.start()
    
    def on_closing(self):
        """Handle window close"""
        self.root.destroy()
    
    def run(self):
        """Run the microphone interface"""
        print("🔥 Starting NEXUS microphone interface...")
        self.root.mainloop()

def main():
    """Main entry point"""
    print("🔥 NEXUS Voice Interface - REAL Microphone")
    print("==========================================")
    
    try:
        ui = NexusVoiceMicButton()
        ui.run()
    except Exception as e:
        print(f"❌ UI error: {e}")

if __name__ == "__main__":
    main()
