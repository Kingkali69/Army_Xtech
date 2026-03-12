#!/usr/bin/env python3
"""
NEXUS OMNIPRESENT UI
====================

Floating desktop interface for NEXUS commands.
Click the button or use voice activation.
This is JARVIS becoming accessible.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
import socket
import threading
import subprocess
import sys
import os
from datetime import datetime

class NexusUI:
    """NEXUS Floating UI - Always accessible interface"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.daemon_port = 9999
        self.voice_active = False
        
        # Setup window
        self.setup_window()
        
        # Create UI elements
        self.create_widgets()
        
        # Start daemon connection
        self.connect_to_daemon()
        
        # Start voice listener (if available)
        self.start_voice_listener()
    
    def setup_window(self):
        """Setup the floating window"""
        self.root.title("🔥 NEXUS")
        self.root.geometry("300x400")
        self.root.attributes('-topmost', True)  # Always on top
        self.root.configure(bg='#1a1a1a')
        
        # Make it look like a control panel
        self.root.overrideredirect(True)  # No window decorations
        
        # Position on screen
        screen_width = self.root.winfo_screenwidth()
        x = screen_width - 350
        y = 50
        self.root.geometry(f"+{x}+{y}")
    
    def create_widgets(self):
        """Create UI widgets"""
        
        # Header
        header = tk.Frame(self.root, bg='#1a1a1a')
        header.pack(fill='x', padx=10, pady=10)
        
        title = tk.Label(
            header,
            text="🔥 NEXUS",
            font=('Arial', 16, 'bold'),
            fg='#ff6b35',
            bg='#1a1a1a'
        )
        title.pack()
        
        subtitle = tk.Label(
            header,
            text="OMNIPRESENT CONTROL",
            font=('Arial', 10),
            fg='#888888',
            bg='#1a1a1a'
        )
        subtitle.pack()
        
        # Command buttons
        button_frame = tk.Frame(self.root, bg='#1a1a1a')
        button_frame.pack(fill='x', padx=10, pady=5)
        
        # Main command buttons
        commands = [
            ("🚀 START OMNI", "start_omni", "#00ff00"),
            ("🛑 STOP OMNI", "stop_omni", "#ff4444"),
            ("🔄 RESTART OMNI", "restart_omni", "#ffaa00"),
            ("📊 STATUS", "status", "#00aaff"),
            ("🔧 FIX BROKEN", "fix_broken", "#ff00ff"),
        ]
        
        for text, command, color in commands:
            btn = tk.Button(
                button_frame,
                text=text,
                command=lambda c=command: self.execute_command(c),
                bg=color,
                fg='white',
                font=('Arial', 10, 'bold'),
                relief='flat',
                cursor='hand2'
            )
            btn.pack(fill='x', pady=2)
        
        # Advanced controls
        advanced_frame = tk.LabelFrame(
            self.root,
            text="ADVANCED",
            bg='#1a1a1a',
            fg='#888888',
            font=('Arial', 9)
        )
        advanced_frame.pack(fill='x', padx=10, pady=10)
        
        # Port killer
        port_frame = tk.Frame(advanced_frame, bg='#1a1a1a')
        port_frame.pack(fill='x', padx=5, pady=2)
        
        tk.Label(
            port_frame,
            text="Kill Port:",
            bg='#1a1a1a',
            fg='#888888',
            font=('Arial', 9)
        ).pack(side='left')
        
        self.port_entry = tk.Entry(port_frame, width=8, bg='#333333', fg='white')
        self.port_entry.pack(side='left', padx=5)
        self.port_entry.insert(0, "8888")
        
        tk.Button(
            port_frame,
            text="KILL",
            command=self.kill_port,
            bg='#ff4444',
            fg='white',
            font=('Arial', 8, 'bold'),
            relief='flat'
        ).pack(side='left')
        
        # Clear Python
        tk.Button(
            advanced_frame,
            text="🧹 CLEAR ALL PYTHON",
            command=lambda: self.execute_command("clear_python"),
            bg='#ff6b35',
            fg='white',
            font=('Arial', 9, 'bold'),
            relief='flat'
        ).pack(fill='x', padx=5, pady=2)
        
        # Status display
        self.status_frame = tk.LabelFrame(
            self.root,
            text="STATUS",
            bg='#1a1a1a',
            fg='#888888',
            font=('Arial', 9)
        )
        self.status_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.status_text = tk.Text(
            self.status_frame,
            height=8,
            bg='#0a0a0a',
            fg='#00ff00',
            font=('Courier', 8),
            relief='flat'
        )
        self.status_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Voice indicator
        self.voice_label = tk.Label(
            self.root,
            text="🎤 Voice: OFF",
            bg='#1a1a1a',
            fg='#888888',
            font=('Arial', 8)
        )
        self.voice_label.pack(pady=5)
        
        # Close button
        tk.Button(
            self.root,
            text="❌ CLOSE",
            command=self.close_ui,
            bg='#333333',
            fg='white',
            font=('Arial', 8),
            relief='flat'
        ).pack(pady=5)
        
        # Make window draggable
        self.make_draggable()
    
    def make_draggable(self):
        """Make window draggable"""
        def start_move(event):
            self.start_x = event.x
            self.start_y = event.y
        
        def on_move(event):
            x = self.root.winfo_x() + (event.x - self.start_x)
            y = self.root.winfo_y() + (event.y - self.start_y)
            self.root.geometry(f"+{x}+{y}")
        
        self.root.bind("<Button-1>", start_move)
        self.root.bind("<B1-Motion>", on_move)
    
    def connect_to_daemon(self):
        """Connect to NEXUS daemon"""
        def connect():
            try:
                # Test connection
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                result = sock.connect_ex(('localhost', self.daemon_port))
                sock.close()
                
                if result == 0:
                    self.update_status("✅ Connected to NEXUS daemon")
                else:
                    self.update_status("❌ NEXUS daemon not running")
                    self.offer_start_daemon()
                    
            except Exception as e:
                self.update_status(f"❌ Connection error: {e}")
                self.offer_start_daemon()
        
        # Run in thread
        threading.Thread(target=connect, daemon=True).start()
    
    def offer_start_daemon(self):
        """Offer to start daemon"""
        if messagebox.askyesno("NEXUS Daemon", "NEXUS daemon is not running. Start it?"):
            try:
                # Start daemon in background
                daemon_path = "/home/kali/Desktop/MITEL/Mitel-main/nexus_omnipresent/nexus_daemon.py"
                subprocess.Popen(['python3', daemon_path], 
                               cwd='/home/kali/Desktop/MITEL/Mitel-main/nexus_omnipresent')
                self.update_status("🚀 Starting NEXUS daemon...")
                
                # Wait and reconnect
                self.root.after(3000, self.connect_to_daemon)
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to start daemon: {e}")
    
    def execute_command(self, action):
        """Execute command through daemon"""
        self.update_status(f"🎯 Executing: {action}")
        
        def send_command():
            try:
                # Connect to daemon
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect(('localhost', self.daemon_port))
                
                # Send command
                command = {
                    'action': action,
                    'timestamp': datetime.now().isoformat()
                }
                
                sock.send(json.dumps(command).encode('utf-8'))
                
                # Receive response
                response = sock.recv(4096).decode('utf-8')
                result = json.loads(response)
                
                # Display result
                self.display_result(result)
                
                sock.close()
                
            except Exception as e:
                self.update_status(f"❌ Command failed: {e}")
        
        # Run in thread
        threading.Thread(target=send_command, daemon=True).start()
    
    def kill_port(self):
        """Kill process on specific port"""
        port = self.port_entry.get().strip()
        if port:
            self.execute_command(f"kill_port:{port}")
        else:
            messagebox.showwarning("Warning", "Please enter a port number")
    
    def display_result(self, result):
        """Display command result"""
        status = result.get('status', 'unknown')
        action = result.get('action', 'unknown')
        timestamp = result.get('timestamp', '')
        
        # Format result for display
        output = f"[{timestamp[:19]}] {action.upper()}\n"
        output += f"Status: {status}\n"
        
        if 'results' in result:
            for res in result['results']:
                output += f"  {res}\n"
        
        if 'services' in result:
            services = result['services']
            output += "\nServices:\n"
            for service, running in services.items():
                status_icon = "✅" if running else "❌"
                output += f"  {status_icon} {service}\n"
        
        if 'urls' in result:
            urls = result['urls']
            output += "\nURLs:\n"
            for name, url in urls.items():
                output += f"  {name}: {url}\n"
        
        if 'message' in result:
            output += f"\nMessage: {result['message']}\n"
        
        self.update_status(output)
    
    def update_status(self, message):
        """Update status display"""
        self.status_text.insert('1.0', f"{message}\n")
        self.status_text.see('1.0')
        
        # Limit text length
        lines = self.status_text.get('1.0', 'end').split('\n')
        if len(lines) > 100:
            self.status_text.delete('100.0', 'end')
    
    def start_voice_listener(self):
        """Start voice listener (placeholder)"""
        # This would integrate with voice recognition
        # For now, just show it's available
        self.voice_label.config(text="🎤 Voice: Ready (say 'NEXUS')")
    
    def close_ui(self):
        """Close the UI"""
        if messagebox.askyesno("Close", "Close NEXUS UI?"):
            self.root.destroy()
    
    def run(self):
        """Run the UI"""
        self.root.mainloop()

def main():
    """Main entry point"""
    ui = NexusUI()
    ui.run()

if __name__ == "__main__":
    main()
