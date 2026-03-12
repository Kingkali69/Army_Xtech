#!/usr/bin/env python3
"""
OMNI Voice Launcher
===================

Voice-activated system launcher for OMNI.
Say "Start OMNI" or "Start this motherfucker up" and NEXUS will launch everything.
"""

import sys
import os
import subprocess
import time
import threading
from datetime import datetime

# Add paths
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'substrate', 'ai_layer'))

class VoiceLauncher:
    """Voice-activated OMNI launcher"""
    
    def __init__(self):
        self.running = False
        self.omni_processes = []
        
    def start_omni_system(self):
        """Start the complete OMNI system"""
        print("🔥 VOICE COMMAND RECEIVED: Starting OMNI System...")
        print("🎯 NEXUS Intelligence activating...")
        
        try:
            # Change to OMNI directory
            os.chdir('/home/kali/Desktop/MITEL/Mitel-main')
            
            # Start the complete demo
            process = subprocess.Popen(
                ['./START_COMPLETE_DEMO.sh'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            self.omni_processes.append(process)
            
            print("✅ OMNI System Started!")
            print("🌐 Console: http://localhost:8888")
            print("💬 AI Chat: http://localhost:8889")
            print("🛡️ M.I.T.E.L. Security: ACTIVE")
            print("🧠 NEXUS Intelligence: OPERATIONAL")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to start OMNI: {e}")
            return False
    
    def stop_omni_system(self):
        """Stop the OMNI system"""
        print("🛑 VOICE COMMAND: Stopping OMNI System...")
        
        try:
            # Kill all OMNI processes
            subprocess.run(['pkill', '-f', 'omni_web_console.py'], check=False)
            subprocess.run(['pkill', '-f', 'omni_ai_chat_simple.py'], check=False)
            subprocess.run(['pkill', '-f', 'START_COMPLETE_DEMO.sh'], check=False)
            
            # Wait for processes to stop
            time.sleep(2)
            
            print("✅ OMNI System Stopped")
            return True
            
        except Exception as e:
            print(f"❌ Failed to stop OMNI: {e}")
            return False
    
    def get_system_status(self):
        """Get OMNI system status"""
        try:
            # Check if processes are running
            console_running = subprocess.run(['pgrep', '-f', 'omni_web_console.py'], 
                                          capture_output=True).returncode == 0
            chat_running = subprocess.run(['pgrep', '-f', 'omni_ai_chat_simple.py'], 
                                         capture_output=True).returncode == 0
            
            status = {
                'console': 'RUNNING' if console_running else 'STOPPED',
                'ai_chat': 'RUNNING' if chat_running else 'STOPPED',
                'overall': 'OPERATIONAL' if console_running else 'OFFLINE'
            }
            
            return status
            
        except Exception as e:
            return {'error': str(e)}
    
    def process_voice_command(self, command):
        """Process voice command"""
        command_lower = command.lower()
        
        if any(word in command_lower for word in ['start', 'launch', 'activate', 'begin']):
            if any(word in command_lower for word in ['omni', 'system', 'engine', 'motherfucker']):
                return self.start_omni_system()
        
        elif any(word in command_lower for word in ['stop', 'kill', 'shutdown', 'terminate']):
            if any(word in command_lower for word in ['omni', 'system', 'engine']):
                return self.stop_omni_system()
        
        elif any(word in command_lower for word in ['status', 'check', 'running']):
            return self.get_system_status()
        
        else:
            print(f"🤖 NEXUS: Voice command not recognized - '{command}'")
            print("💡 Try: 'Start OMNI', 'Stop OMNI', or 'System Status'")
            return False

def main():
    """Main voice launcher interface"""
    print("🔥 OMNI Voice Launcher - NEXUS Intelligence")
    print("==========================================")
    print("🎯 Voice Commands:")
    print("   • 'Start OMNI' or 'Start this motherfucker up'")
    print("   • 'Stop OMNI' or 'Shutdown system'")
    print("   • 'System status' or 'Check running'")
    print("")
    print("💡 Type commands below or use voice integration")
    print("🛑 Type 'quit' to exit")
    print("")
    
    launcher = VoiceLauncher()
    
    # Command loop
    while True:
        try:
            command = input("🎤 Voice Command: ").strip()
            
            if command.lower() in ['quit', 'exit', 'q']:
                print("🛑 Voice Launcher Stopped")
                break
            
            if command:
                result = launcher.process_voice_command(command)
                
                if isinstance(result, dict):
                    print("📊 System Status:")
                    for key, value in result.items():
                        print(f"   {key}: {value}")
                elif result:
                    print("✅ Command executed successfully")
                else:
                    print("❌ Command failed")
            
        except KeyboardInterrupt:
            print("\n🛑 Voice Launcher Stopped")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
