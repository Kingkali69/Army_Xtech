#!/usr/bin/env python3
"""
NEXUS Floating Chat - PERSISTENT BOX
====================================

Always visible. Never disappears. Click microphone → Talk to NEXUS.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import time
import json
import socket
import subprocess
import sys
import os
from datetime import datetime

# Add paths
sys.path.insert(0, '/home/kali/Desktop/MITEL/Mitel-main/nexus_omnipresent')

try:
    import pyttsx3
except ImportError:
    print("❌ Installing pyttsx3...")
    os.system("pip install pyttsx3 --break-system-packages")
    import pyttsx3

class NexusFloatingChat:
    """Persistent floating NEXUS chat box"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.tts = None
        self.node_id = self.get_node_id()
        self.master_node = None
        self.daemon_port = 9999
        
        # Chat state
        self.conversation_history = []
        
        # Setup systems
        self._init_tts()
        self._detect_master()
        self._setup_ui()
        
        print("🔥 NEXUS Floating Chat Ready")
        print(f"🎯 Node: {self.node_id}")
        print(f"👑 Master: {self.master_node}")
        print(f"🔊 TTS: {'Ready' if self.tts else 'Disabled'}")
    
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
        """Setup the persistent floating UI"""
        self.root.title("🔥 NEXUS - PERSISTENT CHAT")
        self.root.geometry("500x700")
        self.root.configure(bg='#1a1a1a')
        
        # Make window stay on top
        self.root.attributes('-topmost', True)
        
        # Header
        header_frame = tk.Frame(self.root, bg='#2a2a2a', height=60)
        header_frame.pack(fill=tk.X, padx=10, pady=5)
        
        title_label = tk.Label(
            header_frame, 
            text="🔥 NEXUS OMNIPRESENT", 
            font=('Arial', 16, 'bold'),
            fg='#ff6b35', 
            bg='#2a2a2a'
        )
        title_label.pack(pady=10)
        
        status_label = tk.Label(
            header_frame,
            text=f"Node: {self.node_id} | Master: {self.master_node} | Status: ACTIVE",
            font=('Arial', 10),
            fg='#00ff00',
            bg='#2a2a2a'
        )
        status_label.pack()
        
        # Chat Area
        chat_frame = tk.Frame(self.root, bg='#2a2a2a')
        chat_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        chat_label = tk.Label(
            chat_frame,
            text="💬 PERSISTENT CHAT WITH NEXUS",
            font=('Arial', 12, 'bold'),
            fg='#ffffff',
            bg='#2a2a2a'
        )
        chat_label.pack(anchor=tk.W, pady=5)
        
        self.chat_area = scrolledtext.ScrolledText(
            chat_frame,
            height=20,
            font=('Courier', 10),
            bg='#0a0a0a',
            fg='#00ff00',
            insertbackground='#00ff00'
        )
        self.chat_area.pack(fill=tk.BOTH, expand=True)
        self.chat_area.insert(tk.END, "🔥 NEXUS PERSISTENT CHAT INITIALIZED\n")
        self.chat_area.insert(tk.END, f"👑 Master node: {self.master_node}\n")
        self.chat_area.insert(tk.END, "💡 Type your message below and click Send\n")
        self.chat_area.insert(tk.END, "🎤 Click Microphone for voice input (simulated)\n")
        self.chat_area.insert(tk.END, "=" * 60 + "\n\n")
        
        # Input Area
        input_frame = tk.Frame(self.root, bg='#2a2a2a')
        input_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.input_field = tk.Entry(
            input_frame,
            font=('Courier', 12),
            bg='#1a1a1a',
            fg='#ffffff',
            insertbackground='#ffffff'
        )
        self.input_field.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.input_field.bind('<Return>', lambda e: self.send_message())
        
        # Buttons
        button_frame = tk.Frame(self.root, bg='#2a2a2a')
        button_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Send Button
        self.send_button = tk.Button(
            button_frame,
            text="📤 SEND",
            font=('Arial', 12, 'bold'),
            bg='#ff6b35',
            fg='white',
            command=self.send_message,
            width=15
        )
        self.send_button.pack(side=tk.LEFT, padx=2)
        
        # Microphone Button
        self.mic_button = tk.Button(
            button_frame,
            text="🎤 MIC",
            font=('Arial', 12, 'bold'),
            bg='#00ff00',
            fg='black',
            command=self.toggle_microphone,
            width=15
        )
        self.mic_button.pack(side=tk.LEFT, padx=2)
        
        # Clear Button
        self.clear_button = tk.Button(
            button_frame,
            text="🧹 CLEAR",
            font=('Arial', 12, 'bold'),
            bg='#666666',
            fg='white',
            command=self.clear_chat,
            width=15
        )
        self.clear_button.pack(side=tk.LEFT, padx=2)
        
        # Quick Commands
        quick_frame = tk.Frame(self.root, bg='#2a2a2a')
        quick_frame.pack(fill=tk.X, padx=10, pady=5)
        
        quick_label = tk.Label(
            quick_frame,
            text="⚡ Quick Commands:",
            font=('Arial', 10, 'bold'),
            fg='#ffffff',
            bg='#2a2a2a'
        )
        quick_label.pack(side=tk.LEFT)
        
        quick_commands = [
            ("Status", "status"),
            ("Report", "nexus report"),
            ("Start OMNI", "start omni"),
            ("Stop OMNI", "stop omni"),
            ("Capabilities", "capabilities"),
            ("Security", "security")
        ]
        
        for text, command in quick_commands:
            btn = tk.Button(
                quick_frame,
                text=text,
                font=('Arial', 8),
                bg='#4a4a4a',
                fg='white',
                command=lambda c=command: self.quick_command(c),
                width=12
            )
            btn.pack(side=tk.LEFT, padx=2)
        
        # Focus on input field
        self.input_field.focus_set()
        
        # Handle window close - minimize instead of close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        print("✅ Persistent floating chat setup complete")
    
    def add_chat_message(self, sender, message):
        """Add message to chat"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.chat_area.insert(tk.END, f"[{timestamp}] {sender}: {message}\n")
        self.chat_area.see(tk.END)
        self.conversation_history.append({"time": timestamp, "sender": sender, "message": message})
    
    def send_message(self):
        """Send message to NEXUS"""
        message = self.input_field.get().strip()
        if not message:
            return
        
        # Add user message
        self.add_chat_message("👤 YOU", message)
        
        # Clear input
        self.input_field.delete(0, tk.END)
        
        # Process message
        self.process_nexus_command(message)
    
    def quick_command(self, command):
        """Execute quick command"""
        self.add_chat_message("⚡ QUICK CMD", command)
        self.process_nexus_command(command)
    
    def toggle_microphone(self):
        """Toggle microphone (simulated for now)"""
        self.add_chat_message("🎤 MIC", "🎤 Microphone clicked! (Type your message or use quick commands)")
        self.mic_button.config(bg='#ff0000', text='🔴 ACTIVE')
        self.root.after(2000, self.reset_mic_button)
    
    def reset_mic_button(self):
        """Reset microphone button"""
        self.mic_button.config(bg='#00ff00', text='🎤 MIC')
    
    def clear_chat(self):
        """Clear chat area"""
        self.chat_area.delete(1.0, tk.END)
        self.add_chat_message("🧹", "Chat cleared")
        self.add_chat_message("🔥", "NEXUS PERSISTENT CHAT READY")
    
    def process_nexus_command(self, command):
        """Process NEXUS command"""
        if not self.is_master():
            self.add_chat_message("🔇 NEXUS", f"Not master node. Letting {self.master_node} respond...")
            return
        
        command_lower = command.lower().strip()
        
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
        
        self.add_chat_message("🔥 NEXUS", response)
        self.speak(response)
    
    def handle_status(self):
        """Handle status"""
        authority = "Master" if self.is_master() else "Worker"
        response = f"I'm running {authority} control. The daemon is operational. Standing by for your orders, sir."
        self.add_chat_message("🔥 NEXUS", response)
        self.speak(response)
    
    def handle_start_omni(self):
        """Handle start OMNI"""
        result = self.send_daemon_command("start_omni")
        
        if result.get("status") == "completed":
            response = "Bringing OMNI systems online now. Console, AI chat, and security layers are spinning up. Give me a moment to confirm all green."
        else:
            response = f"We have a problem starting OMNI. {result.get('message', 'Unknown error')}. I need to troubleshoot."
        
        self.add_chat_message("🔥 NEXUS", response)
        self.speak(response)
    
    def handle_stop_omni(self):
        """Handle stop OMNI"""
        result = self.send_daemon_command("stop_omni")
        
        if result.get("status") == "completed":
            response = "Shutting down OMNI systems now. All services will be terminated. Acknowledged."
        else:
            response = f"Can't shut down OMNI. {result.get('message', 'Unknown error')}. We have an issue."
        
        self.add_chat_message("🔥 NEXUS", response)
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
        
        self.add_chat_message("🔥 NEXUS", response)
        self.speak(response)
    
    def handle_security(self):
        """Handle security"""
        result = self.send_daemon_command("status")
        
        if result.get("status") == "completed":
            response = "Security posture is at full readiness. M.I.T.E.L. is watching the perimeter. Nothing gets past me. Nothing."
        else:
            response = f"Security systems are offline. {result.get('message', 'Unknown error')}. We're exposed."
        
        self.add_chat_message("🔥 NEXUS", response)
        self.speak(response)
    
    def handle_rubber_ducky(self):
        """Handle rubber ducky"""
        response = (
            f"Rubber ducky threats are my specialty. "
            f"M.I.T.E.L. quarantine systems are standing by. "
            f"I'll catch anything they try to plug in. Count on it."
        )
        self.add_chat_message("🔥 NEXUS", response)
        self.speak(response)
    
    def handle_master_status(self):
        """Handle master status"""
        authority = "Master" if self.is_master() else "Worker"
        response = (
            f"I'm running {authority} authority. "
            f"The master node is {self.master_node}. "
            f"MDCS is routing command authority. I am in control."
        )
        self.add_chat_message("🔥 NEXUS", response)
        self.speak(response)
    
    def handle_general(self, command):
        """Handle general"""
        if "help" in command.lower():
            response = "My commands are: systems report, status, start omni, stop omni, capabilities, security, rubber ducky. What are your orders, sir?"
        else:
            response = "Acknowledged. I understand. What would you like me to do?"
        
        self.add_chat_message("🔥 NEXUS", response)
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
        """Handle window close - minimize instead of close"""
        self.root.withdraw()  # Hide window
        # Show it again after 1 second
        self.root.after(1000, self.show_window)
    
    def show_window(self):
        """Show window again"""
        self.root.deiconify()
    
    def run(self):
        """Run the persistent floating chat"""
        print("🔥 Starting persistent NEXUS floating chat...")
        self.root.mainloop()

def main():
    """Main entry point"""
    print("🔥 NEXUS PERSISTENT FLOATING CHAT")
    print("=================================")
    
    try:
        chat = NexusFloatingChat()
        chat.run()
    except Exception as e:
        print(f"❌ Chat error: {e}")

if __name__ == "__main__":
    main()
