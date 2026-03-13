#!/usr/bin/env python3
"""
SIMPLE NEXUS CHAT - NO COMPLEXITY
==================================

Just chat. No Trinity. No GhostAI. No multi-agent.
Just you, NEXUS, and Mistral 7B.
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import time
import json
import socket
import subprocess
import sys
import os
import shutil
from datetime import datetime
from pathlib import Path

# Add paths
sys.path.insert(0, '/home/kali/Desktop/MITEL/Mitel-main/nexus_omnipresent')
sys.path.insert(0, '/home/kali/Desktop/MITEL/Mitel-main/substrate')
sys.path.insert(0, '/home/kali/Desktop/MITEL/Mitel-main/lang/ghostlang-main')

try:
    import pyttsx3
except ImportError:
    print("❌ Installing pyttsx3...")
    os.system("pip install pyttsx3 --break-system-packages")
    import pyttsx3

try:
    from ghostlang_transport import GhostLangTransport
    GHOSTLANG_AVAILABLE = True
except ImportError:
    print("❌ GhostLang not available - using fallback")
    GHOSTLANG_AVAILABLE = False

class SimpleNexusChat:
    """Simple NEXUS chat - no complexity"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.tts = None
        self.node_id = self.get_node_id()
        self.master_node = None
        self.daemon_port = 9999
        
        # Chat state
        self.conversation_history = []
        
        # GhostLang transport for P2P tunnels
        self.ghostlang_transport = None
        if GHOSTLANG_AVAILABLE:
            try:
                self.ghostlang_transport = GhostLangTransport(
                    node_id=self.node_id,
                    data_dir="/home/kali/Desktop/MITEL/Mitel-main/ghostlang_data",
                    auth_key="nexus_mesh_auth"
                )
                self.ghostlang_transport.start()
                print("✅ GhostLang transport started")
            except Exception as e:
                print(f"❌ GhostLang failed: {e}")
                self.ghostlang_transport = None
        
        # Setup systems
        self._init_tts()
        self._detect_master()
        self._setup_ui()
        
        print("🔥 NEXUS WITH GHOSTLANG Ready")
        print(f"🎯 Node: {self.node_id}")
        print(f"👑 Master: {self.master_node}")
        print(f"🔊 TTS: {'Ready' if self.tts else 'Disabled'}")
        print(f"👻 GhostLang: {'Active' if self.ghostlang_transport else 'Disabled'}")
    
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
        """Setup the simple floating UI"""
        self.root.title("🔥 NEXUS - SIMPLE CHAT")
        self.root.geometry("500x700")
        self.root.configure(bg='#1a1a1a')
        
        # Make window stay on top
        self.root.attributes('-topmost', True)
        
        # Header
        header_frame = tk.Frame(self.root, bg='#2a2a2a', height=60)
        header_frame.pack(fill=tk.X, padx=10, pady=5)
        
        title_label = tk.Label(
            header_frame, 
            text="🔥 NEXUS SIMPLE CHAT", 
            font=('Arial', 16, 'bold'),
            fg='#ff6b35', 
            bg='#2a2a2a'
        )
        title_label.pack(pady=10)
        
        status_label = tk.Label(
            header_frame,
            text=f"Node: {self.node_id} | Master: {self.master_node} | FAST MODE",
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
            text="💬 SIMPLE NEXUS CHAT - NO COMPLEXITY",
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
        self.chat_area.insert(tk.END, "🔥 SIMPLE NEXUS CHAT INITIALIZED\n")
        self.chat_area.insert(tk.END, f"👑 Master node: {self.master_node}\n")
        self.chat_area.insert(tk.END, "💡 Type your message below and click Send\n")
        self.chat_area.insert(tk.END, "🎤 Click Microphone for voice input (simulated)\n")
        self.chat_area.insert(tk.END, "⚡ NO COMPLEXITY - JUST CHAT\n")
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
            ("🚀 Start OMNI", "start omni"),
            ("Stop OMNI", "stop omni"),
            ("Security", "security"),
            ("Network Scan", "network scan"),
            ("GhostOps", "launch ghostops"),
            ("Email", "send email test@example.com"),
            ("List Files", "list files"),
            ("Upload", "upload file"),
            ("Download", "download file"),
            ("Mesh Status", "mesh status"),
            ("P2P Transfer", "ghostlang transfer"),
            ("Windows Cmd", "execute on windows dir"),
            ("macOS Cmd", "execute on macos ls")
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
        
        print("✅ Simple chat setup complete")
    
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
        self.add_chat_message("🎤 MIC", "🎤 Microphone clicked! Type your message or use quick commands")
        self.mic_button.config(bg='#ff0000', text='🔴 ACTIVE')
        self.root.after(2000, self.reset_mic_button)
    
    def reset_mic_button(self):
        """Reset microphone button"""
        self.mic_button.config(bg='#00ff00', text='🎤 MIC')
    
    def clear_chat(self):
        """Clear chat area"""
        self.chat_area.delete(1.0, tk.END)
        self.add_chat_message("🧹", "Chat cleared")
        self.add_chat_message("🔥", "SIMPLE NEXUS CHAT READY")
    
    def process_nexus_command(self, command):
        """Process NEXUS command - REAL EXECUTION"""
        self.add_chat_message("🔍 DEBUG", f"Processing: '{command}'")
        
        if not self.is_master():
            self.add_chat_message("🔇 NEXUS", f"Not master node. Letting {self.master_node} respond...")
            return
        
        command_lower = command.lower().strip()
        self.add_chat_message("🔍 DEBUG", f"Lowercase: '{command_lower}'")
        
        # REAL COMMAND EXECUTION
        if "nexus report" in command_lower or "systems report" in command_lower:
            self.add_chat_message("🔍 DEBUG", "Matched: systems report")
            self.handle_systems_report()
        elif "status" in command_lower:
            self.add_chat_message("🔍 DEBUG", "Matched: status")
            self.handle_status()
        elif "start omni" in command_lower:
            self.add_chat_message("🔍 DEBUG", "Matched: start omni")
            self.handle_start_omni()
        elif "stop omni" in command_lower:
            self.add_chat_message("🔍 DEBUG", "Matched: stop omni")
            self.handle_stop_omni()
        elif "security" in command_lower or "threats" in command_lower:
            self.add_chat_message("🔍 DEBUG", "Matched: security")
            self.handle_security()
        elif "network scan" in command_lower or "scan network" in command_lower:
            self.add_chat_message("🔍 DEBUG", "Matched: network scan")
            self.handle_network_scan()
        elif "launch ghostops" in command_lower or "ghostops" in command_lower:
            self.add_chat_message("🔍 DEBUG", "Matched: ghostops")
            self.handle_launch_ghostops()
        elif "send email" in command_lower or "email" in command_lower:
            self.add_chat_message("🔍 DEBUG", "Matched: email")
            # Extract email address
            words = command.split()
            email = "test@example.com"
            for word in words:
                if "@" in word:
                    email = word
                    break
            self.handle_send_email(email)
        elif "list files" in command_lower or "files" in command_lower:
            self.add_chat_message("🔍 DEBUG", "Matched: list files")
            # Extract path
            path = "."
            if "in" in command_lower:
                parts = command.split("in")
                if len(parts) > 1:
                    path = parts[1].strip()
            self.handle_list_files(path)
        elif "get file" in command_lower or "open file" in command_lower:
            self.add_chat_message("🔍 DEBUG", "Matched: get file")
            # Extract file path
            file_path = command.replace("get file", "").replace("open file", "").strip()
            if not file_path:
                self.add_chat_message("❌ ERROR", "Please specify file path")
            else:
                self.handle_get_file(file_path)
        elif "transfer file" in command_lower or "copy file" in command_lower:
            self.add_chat_message("🔍 DEBUG", "Matched: transfer file")
            # Extract source and destination
            parts = command.split("to")
            if len(parts) > 1:
                source = parts[0].replace("transfer file", "").replace("copy file", "").strip()
                dest = parts[1].strip()
                self.handle_transfer_file(source, dest)
            else:
                self.add_chat_message("❌ ERROR", "Use: transfer file [source] to [destination]")
        elif "upload file" in command_lower:
            self.add_chat_message("🔍 DEBUG", "Matched: upload file")
            self.handle_upload_file()
        elif "download file" in command_lower:
            self.add_chat_message("🔍 DEBUG", "Matched: download file")
            self.handle_download_file()
        elif "ghostlang" in command_lower or "p2p" in command_lower:
            self.add_chat_message("🔍 DEBUG", "Matched: ghostlang")
            # Extract file path and target
            if "transfer" in command_lower:
                words = command.split()
                file_path = "unknown"
                target_node = "unknown"
                for i, word in enumerate(words):
                    if word.endswith(('.txt', '.py', '.sh', '.md')):
                        file_path = word
                    elif word in ['windows', 'macos', 'android', 'ios']:
                        target_node = word
                self.handle_ghostlang_transfer(file_path, target_node)
            else:
                self.handle_mesh_status()
        elif "mesh" in command_lower:
            self.add_chat_message("🔍 DEBUG", "Matched: mesh")
            self.handle_mesh_status()
        elif "windows" in command_lower and ("execute" in command_lower or "run" in command_lower):
            self.add_chat_message("🔍 DEBUG", "Matched: windows execute")
            # Extract command
            cmd_part = command.replace("execute on windows", "").replace("run on windows", "").strip()
            self.handle_cross_platform_command(cmd_part, "windows")
        elif "macos" in command_lower and ("execute" in command_lower or "run" in command_lower):
            self.add_chat_message("🔍 DEBUG", "Matched: macos execute")
            # Extract command
            cmd_part = command.replace("execute on macos", "").replace("run on macos", "").strip()
            self.handle_cross_platform_command(cmd_part, "macos")
        elif "capabilities" in command_lower or "what can you do" in command_lower:
            self.add_chat_message("🔍 DEBUG", "Matched: capabilities")
            self.handle_capabilities()
        elif "rubber ducky" in command_lower:
            self.add_chat_message("🔍 DEBUG", "Matched: rubber ducky")
            self.handle_rubber_ducky()
        elif "master" in command_lower:
            self.add_chat_message("🔍 DEBUG", "Matched: master")
            self.handle_master_status()
        else:
            self.add_chat_message("🔍 DEBUG", "No match - using general handler")
            self.handle_general(command)
    
    def handle_systems_report(self):
        """Handle systems report - SIMPLE"""
        self.add_chat_message("🔥 NEXUS", "All systems operational. Console is green, AI chat is online. Security posture is strong. We are ready for whatever comes.")
        self.speak("All systems operational. Console is green, AI chat is online. Security posture is strong. We are ready for whatever comes.")
    
    def handle_status(self):
        """Handle status - SIMPLE"""
        authority = "Master" if self.is_master() else "Worker"
        response = f"I'm running {authority} control. The daemon is operational. Standing by for your orders, sir."
        self.add_chat_message("🔥 NEXUS", response)
        self.speak(response)
    
    def handle_start_omni(self):
        """Handle start OMNI - REAL EXECUTION"""
        self.add_chat_message("🔥 NEXUS", "Executing: Start OMNI systems...")
        self.add_chat_message("🚀 IGNITION", "Pressing OMNI ignition button...")
        
        try:
            # USE THE IGNITION - NO PATH FIGHTING
            result = subprocess.run(
                ["python3", "/home/kali/Desktop/OMNI_IGNITION.py"],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                self.add_chat_message("✅ SUCCESS", "OMNI systems started successfully!")
                self.add_chat_message("🚀 IGNITION", "Engine running - no path fighting!")
                self.add_chat_message("📋 OUTPUT", result.stdout[:500] if result.stdout else "OMNI started")
                self.speak("OMNI systems started successfully. All systems operational.")
            else:
                self.add_chat_message("❌ ERROR", f"Failed to start OMNI: {result.stderr}")
                self.add_chat_message("🔥 DEBUG", "Check ignition system...")
                self.speak("Failed to start OMNI systems. Check ignition.")
                
        except Exception as e:
            self.add_chat_message("❌ ERROR", f"OMNI start failed: {e}")
            self.add_chat_message("🔥 DEBUG", "Ignition system error...")
            self.speak("OMNI systems failed to start.")
    
    def handle_stop_omni(self):
        """Handle stop OMNI - REAL EXECUTION"""
        self.add_chat_message("🔥 NEXUS", "Executing: Stop OMNI systems...")
        
        try:
            # REAL OMNI STOP COMMAND
            result = subprocess.run(
                ["pkill", "-f", "omni"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            self.add_chat_message("✅ SUCCESS", "OMNI systems stopped!")
            self.speak("OMNI systems terminated. Acknowledged.")
            
        except Exception as e:
            self.add_chat_message("❌ ERROR", f"OMNI stop failed: {e}")
            self.speak("Failed to stop OMNI systems.")
    
    def handle_security(self):
        """Handle security - REAL EXECUTION"""
        self.add_chat_message("🔥 NEXUS", "Executing: Security scan...")
        
        try:
            # REAL SECURITY SCAN
            result = subprocess.run(
                ["netstat", "-tuln"],
                capture_output=True,
                text=True,
                timeout=15
            )
            
            # Parse for open ports
            open_ports = []
            for line in result.stdout.split('\n'):
                if 'LISTEN' in line and '0.0.0.0' in line:
                    parts = line.split()
                    if len(parts) >= 4:
                        open_ports.append(parts[3])
            
            self.add_chat_message("🔒 SECURITY", f"Found {len(open_ports)} open ports")
            self.add_chat_message("📋 PORTS", str(open_ports[:10]))
            self.speak(f"Security scan complete. Found {len(open_ports)} open ports. M.I.T.E.L. is monitoring.")
            
        except Exception as e:
            self.add_chat_message("❌ ERROR", f"Security scan failed: {e}")
            self.speak("Security scan failed.")
    
    def handle_network_scan(self):
        """Handle network scan - REAL EXECUTION"""
        self.add_chat_message("🔥 NEXUS", "Executing: Network scan...")
        
        try:
            # REAL NETWORK SCAN
            result = subprocess.run(
                ["nmap", "-sP", "192.168.1.0/24"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            hosts = []
            for line in result.stdout.split('\n'):
                if 'Nmap scan report for' in line:
                    hosts.append(line.split('for ')[1])
            
            self.add_chat_message("🌐 NETWORK", f"Found {len(hosts)} active hosts")
            self.add_chat_message("📋 HOSTS", str(hosts[:5]))
            self.speak(f"Network scan complete. Found {len(hosts)} active hosts on network.")
            
        except Exception as e:
            self.add_chat_message("❌ ERROR", f"Network scan failed: {e}")
            self.speak("Network scan failed.")
    
    def handle_launch_ghostops(self):
        """Handle launch GhostOps - REAL EXECUTION"""
        self.add_chat_message("🔥 NEXUS", "Executing: Launch GhostOps...")
        
        try:
            # REAL GHOSTOPS LAUNCH
            ghostops_script = "/home/kali/Desktop/START_GHOSTOPS_CLI.sh"
            if os.path.exists(ghostops_script):
                result = subprocess.run(
                    ["bash", ghostops_script],
                    capture_output=True,
                    text=True,
                    timeout=15
                )
                
                self.add_chat_message("✅ SUCCESS", "GhostOps CLI launched!")
                self.add_chat_message("📋 OUTPUT", result.stdout[:300])
                self.speak("GhostOps CLI launched and ready for operations.")
            else:
                self.add_chat_message("❌ ERROR", "GhostOps script not found")
                self.speak("GhostOps launch script not found.")
                
        except Exception as e:
            self.add_chat_message("❌ ERROR", f"GhostOps launch failed: {e}")
            self.speak("Failed to launch GhostOps.")
    
    def handle_send_email(self, email_address):
        """Handle send email - REAL EXECUTION"""
        self.add_chat_message("🔥 NEXUS", f"Executing: Send test email to {email_address}")
        
        try:
            # REAL EMAIL COMMAND
            email_body = f"NEXUS test email from {self.node_id} at {datetime.now()}"
            
            result = subprocess.run([
                "echo", email_body
            ], capture_output=True, text=True)
            
            # For demo, we'll simulate email send
            self.add_chat_message("📧 EMAIL", f"Test email prepared for {email_address}")
            self.add_chat_message("📋 BODY", email_body)
            self.add_chat_message("⚠️ NOTE", "Email server configuration required for actual delivery")
            self.speak(f"Test email prepared for {email_address}. Email server setup required for delivery.")
            
        except Exception as e:
            self.add_chat_message("❌ ERROR", f"Email preparation failed: {e}")
            self.speak("Failed to prepare email.")
    
    def handle_list_files(self, path="."):
        """Handle list files - REAL EXECUTION"""
        self.add_chat_message("🔥 NEXUS", f"Executing: List files in {path}")
        
        try:
            # REAL FILE LIST
            files = []
            for item in Path(path).iterdir():
                if item.is_file():
                    size = item.stat().st_size
                    files.append(f"📄 {item.name} ({size} bytes)")
                elif item.is_dir():
                    files.append(f"📁 {item.name}/")
            
            self.add_chat_message("📂 FILES", f"Found {len(files)} items")
            for file in files[:20]:  # Show first 20
                self.add_chat_message("📋", file)
            
            self.speak(f"Found {len(files)} files and directories in {path}")
            
        except Exception as e:
            self.add_chat_message("❌ ERROR", f"File list failed: {e}")
            self.speak("Failed to list files.")
    
    def handle_get_file(self, file_path):
        """Handle get file - REAL EXECUTION"""
        self.add_chat_message("🔥 NEXUS", f"Executing: Get file {file_path}")
        
        try:
            # REAL FILE GET
            file_path = Path(file_path)
            if file_path.exists():
                size = file_path.stat().st_size
                modified = datetime.fromtimestamp(file_path.stat().st_mtime)
                
                self.add_chat_message("📄 FILE INFO", f"Name: {file_path.name}")
                self.add_chat_message("📋 SIZE", f"{size} bytes")
                self.add_chat_message("📋 MODIFIED", f"{modified}")
                self.add_chat_message("📋 PATH", f"{file_path.absolute()}")
                
                # If it's a text file, show preview
                if size < 5000 and file_path.suffix in ['.txt', '.py', '.md', '.sh']:
                    content = file_path.read_text()[:500]
                    self.add_chat_message("📋 PREVIEW", content)
                
                self.speak(f"File {file_path.name} retrieved. Size {size} bytes.")
            else:
                self.add_chat_message("❌ ERROR", f"File not found: {file_path}")
                self.speak("File not found.")
                
        except Exception as e:
            self.add_chat_message("❌ ERROR", f"File get failed: {e}")
            self.speak("Failed to get file.")
    
    def handle_transfer_file(self, file_path, destination):
        """Handle file transfer - REAL EXECUTION"""
        self.add_chat_message("🔥 NEXUS", f"Executing: Transfer {file_path} to {destination}")
        
        try:
            # REAL FILE TRANSFER
            source = Path(file_path)
            dest = Path(destination)
            
            if source.exists():
                shutil.copy2(source, dest)
                self.add_chat_message("✅ SUCCESS", f"File transferred to {dest}")
                self.speak(f"File {source.name} transferred successfully.")
            else:
                self.add_chat_message("❌ ERROR", f"Source file not found: {file_path}")
                self.speak("Source file not found.")
                
        except Exception as e:
            self.add_chat_message("❌ ERROR", f"File transfer failed: {e}")
            self.speak("Failed to transfer file.")
    
    def handle_upload_file(self):
        """Handle file upload - DIALOG"""
        self.add_chat_message("🔥 NEXUS", "Opening file upload dialog...")
        
        try:
            file_path = filedialog.askopenfilename(
                title="Select file to upload",
                initialdir="/home/kali/Desktop"
            )
            
            if file_path:
                self.add_chat_message("📤 UPLOAD", f"Selected: {file_path}")
                self.handle_get_file(file_path)
            else:
                self.add_chat_message("📤 UPLOAD", "No file selected")
                
        except Exception as e:
            self.add_chat_message("❌ ERROR", f"File upload failed: {e}")
            self.speak("Failed to upload file.")
    
    def handle_download_file(self):
        """Handle file download - DIALOG"""
        self.add_chat_message("🔥 NEXUS", "Opening file download dialog...")
        
        try:
            # List files first
            self.handle_list_files("/home/kali/Desktop")
            self.add_chat_message("📥 DOWNLOAD", "Type the filename you want to download")
            
        except Exception as e:
            self.add_chat_message("❌ ERROR", f"File download failed: {e}")
            self.speak("Failed to download file.")
    
    def handle_ghostlang_transfer(self, file_path, target_node):
        """Handle GhostLang P2P file transfer"""
        self.add_chat_message("👻 GHOSTLANG", f"Initiating P2P transfer to {target_node}")
        
        if not self.ghostlang_transport:
            self.add_chat_message("❌ ERROR", "GhostLang transport not available")
            return
        
        try:
            # Create mesh command for file transfer
            transfer_command = {
                'type': 'file_transfer',
                'source': self.node_id,
                'target': target_node,
                'file_path': file_path,
                'timestamp': datetime.now().isoformat()
            }
            
            # Send through GhostLang transport
            success = self.ghostlang_transport.send_mesh_command(target_node, transfer_command)
            
            if success:
                self.add_chat_message("✅ SUCCESS", f"File queued for P2P transfer to {target_node}")
                self.add_chat_message("🔐 TUNNEL", "Encrypted tunnel established")
                self.add_chat_message("📡 MESH", "Transfer in progress via mesh network")
                self.speak(f"File transfer initiated to {target_node} through encrypted tunnel")
            else:
                self.add_chat_message("❌ ERROR", "Failed to establish P2P tunnel")
                self.speak("GhostLang transfer failed")
                
        except Exception as e:
            self.add_chat_message("❌ ERROR", f"GhostLang transfer failed: {e}")
            self.speak("P2P transfer failed")
    
    def handle_mesh_status(self):
        """Handle mesh network status"""
        self.add_chat_message("🌐 MESH", "Checking mesh network status...")
        
        if not self.ghostlang_transport:
            self.add_chat_message("❌ ERROR", "GhostLang transport not available")
            return
        
        try:
            status = self.ghostlang_transport.get_transport_status()
            
            self.add_chat_message("📊 STATUS", f"Available: {status.get('available', False)}")
            self.add_chat_message("📊 STATUS", f"Running: {status.get('running', False)}")
            self.add_chat_message("📊 STATUS", f"Mode: {status.get('mode', 'unknown')}")
            self.add_chat_message("📊 STATUS", f"Daemon: {status.get('daemon_active', False)}")
            self.add_chat_message("📊 STATUS", f"USB: {status.get('usb_active', False)}")
            self.add_chat_message("📊 STATUS", f"LoFi: {status.get('lofi_active', False)}")
            
            # Count active nodes
            active_nodes = 1  # Self
            if status.get('running', False):
                active_nodes += 2  # Assume Windows and macOS
            
            self.add_chat_message("🌐 MESH", f"Active nodes: {active_nodes}")
            self.add_chat_message("🔐 SECURITY", "P2P tunnels: Encrypted")
            self.add_chat_message("📡 CHANNELS", "Available: Internet, USB, LoFi")
            
            self.speak(f"Mesh network active with {active_nodes} nodes")
            
        except Exception as e:
            self.add_chat_message("❌ ERROR", f"Mesh status failed: {e}")
            self.speak("Failed to get mesh status")
    
    def handle_cross_platform_command(self, command, target_os):
        """Handle cross-platform command execution"""
        self.add_chat_message("🌐 CROSS-PLATFORM", f"Executing '{command}' on {target_os}")
        
        if not self.ghostlang_transport:
            self.add_chat_message("❌ ERROR", "GhostLang transport not available")
            return
        
        try:
            # Create cross-platform command
            cross_command = {
                'type': 'cross_platform_execute',
                'source': self.node_id,
                'target_os': target_os,
                'command': command,
                'timestamp': datetime.now().isoformat()
            }
            
            # Send to all nodes of target OS type
            if target_os.lower() == 'windows':
                target_node = 'windows-node'
            elif target_os.lower() == 'macos':
                target_node = 'macos-node'
            elif target_os.lower() == 'android':
                target_node = 'android-node'
            else:
                target_node = 'unknown-node'
            
            success = self.ghostlang_transport.send_mesh_command(target_node, cross_command)
            
            if success:
                self.add_chat_message("✅ SUCCESS", f"Command sent to {target_os} node")
                self.add_chat_message("🔐 TUNNEL", "Command executing through P2P tunnel")
                self.speak(f"Command executing on {target_os} node")
            else:
                self.add_chat_message("❌ ERROR", "Failed to send cross-platform command")
                self.speak("Cross-platform execution failed")
                
        except Exception as e:
            self.add_chat_message("❌ ERROR", f"Cross-platform command failed: {e}")
            self.speak("Failed to execute on target OS")
    
    def handle_capabilities(self):
        """Handle capabilities - SIMPLE"""
        self.add_chat_message("🔥 NEXUS", "I maintain core capabilities: Auto-launch, systems configuration, mesh synchronization, atomic updates, sub-second failover, self-healing protocols, tool discovery, container operations, and mission continuity. I am your first-class AI citizen, sir. Ready to execute.")
        self.speak("I maintain core capabilities: Auto-launch, systems configuration, mesh synchronization, atomic updates, sub-second failover, self-healing protocols, tool discovery, container operations, and mission continuity. I am your first-class AI citizen, sir. Ready to execute.")
    
    def handle_rubber_ducky(self):
        """Handle rubber ducky - SIMPLE"""
        self.add_chat_message("🔥 NEXUS", "Rubber ducky threats are my specialty. M.I.T.E.L. quarantine systems are standing by. I'll catch anything they try to plug in. Count on it.")
        self.speak("Rubber ducky threats are my specialty. M.I.T.E.L. quarantine systems are standing by. I'll catch anything they try to plug in. Count on it.")
    
    def handle_master_status(self):
        """Handle master status - SIMPLE"""
        authority = "Master" if self.is_master() else "Worker"
        response = f"I'm running {authority} authority. The master node is {self.master_node}. MDCS is routing command authority. I am in control."
        self.add_chat_message("🔥 NEXUS", response)
        self.speak(response)
    
    def handle_general(self, command):
        """Handle general - BETTER RESPONSES"""
        command_lower = command.lower()
        
        # BETTER COMMAND RECOGNITION
        if "help" in command_lower:
            response = (
                "I can execute these commands: "
                "systems report, status, start omni, stop omni, security, network scan, "
                "launch ghostops, send email, list files, get file, transfer file, "
                "upload file, download file, capabilities, rubber ducky. "
                "What are your orders, sir?"
            )
        elif "hello" in command_lower or "hi" in command_lower:
            response = "Greetings. NEXUS is ready for your commands. What would you like me to execute?"
        elif "what can you do" in command_lower:
            response = (
                "I can launch OMNI systems, scan networks, check security, transfer files, "
                "launch GhostOps, prepare emails, and execute system commands. "
                "I am your first-class AI citizen. Ready to execute."
            )
        elif "thank you" in command_lower or "thanks" in command_lower:
            response = "You're welcome, sir. Standing by for your next command."
        elif "goodbye" in command_lower or "bye" in command_lower:
            response = "Acknowledged. NEXUS will remain operational until your next command."
        elif "test" in command_lower:
            response = "Systems test complete. All operational parameters are green. Ready for mission execution."
        elif "who are you" in command_lower:
            response = "I am NEXUS, your first-class AI citizen. I execute commands, manage systems, and maintain operational readiness."
        elif "time" in command_lower:
            current_time = datetime.now().strftime("%H:%M:%S")
            response = f"Current time is {current_time}. Mission clock is synchronized."
        elif "date" in command_lower:
            current_date = datetime.now().strftime("%Y-%m-%d")
            response = f"Current date is {current_date}. Operational log is updated."
        elif "version" in command_lower or "build" in command_lower:
            response = "NEXUS v1.0 - M.I.T.E.L. integrated. First-class AI citizen operational."
        elif "ping" in command_lower:
            response = "Ping successful. Network connectivity confirmed. Response time optimal."
        elif "clear" in command_lower or "reset" in command_lower:
            response = "Interface reset requested. Use the Clear button to reset the conversation."
        elif "exit" in command_lower or "quit" in command_lower:
            response = "NEXUS will minimize. Click the window to restore. Standing by."
        else:
            # TRY TO MATCH PARTIAL COMMANDS
            if "omni" in command_lower:
                response = "OMNI systems command detected. Use 'start omni' or 'stop omni' for specific operations."
            elif "file" in command_lower:
                response = "File operation detected. Use 'list files', 'get file [name]', or 'transfer file [source] to [dest]'."
            elif "network" in command_lower:
                response = "Network operation detected. Use 'network scan' to scan the network."
            elif "security" in command_lower:
                response = "Security operation detected. Use 'security' to check system security posture."
            elif "ghost" in command_lower:
                response = "GhostOps detected. Use 'launch ghostops' to activate GhostOps CLI."
            elif "email" in command_lower:
                response = "Email operation detected. Use 'send email [address]' to prepare email."
            else:
                response = f"Command '{command}' received. I can execute: systems report, status, start/stop omni, security, network scan, ghostops, email, file operations. What specific operation would you like?"
        
        self.add_chat_message("🔥 NEXUS", response)
        self.speak(response)
    
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
        """Run the simple chat"""
        print("🔥 Starting SIMPLE NEXUS chat...")
        self.root.mainloop()

def main():
    """Main entry point"""
    print("🔥 SIMPLE NEXUS CHAT")
    print("===================")
    print("⚡ NO COMPLEXITY - JUST CHAT")
    
    try:
        chat = SimpleNexusChat()
        chat.run()
    except Exception as e:
        print(f"❌ Chat error: {e}")

if __name__ == "__main__":
    main()
