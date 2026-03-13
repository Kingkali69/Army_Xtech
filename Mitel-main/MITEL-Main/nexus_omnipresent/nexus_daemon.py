#!/usr/bin/env python3
"""
NEXUS OMNIPRESENT DAEMON
========================

Core daemon that lives in substrate layer.
Always listening, always ready to execute commands.
This is JARVIS becoming omnipresent.
"""

import os
import sys
import time
import json
import socket
import threading
import subprocess
from datetime import datetime
import logging

# Add substrate paths
sys.path.insert(0, '/home/kali/Desktop/MITEL/Mitel-main')
sys.path.insert(0, '/home/kali/Desktop/MITEL/Mitel-main/substrate/ai_layer')

class NexusDaemon:
    """NEXUS Omnipresent Daemon - Core system intelligence"""
    
    def __init__(self):
        self.running = False
        self.commands = {}
        self.omni_context = {}
        self.socket_port = 9999
        self.server_socket = None
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='[NEXUS_DAEMON] %(asctime)s - %(message)s',
            handlers=[
                logging.FileHandler('/tmp/nexus_daemon.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        self.logger.info("🔥 NEXUS Daemon initializing...")
        
    def start_daemon(self):
        """Start the omnipresent daemon"""
        self.running = True
        
        # Load OMNI context
        self.load_omni_context()
        
        # Load NEXUS capabilities
        self.load_nexus_capabilities()
        
        # Start command server
        self.start_command_server()
        
        # Start background tasks
        self.start_background_tasks()
        
        self.logger.info("🚀 NEXUS Daemon is OMNIPRESENT")
        self.logger.info("🎯 Ready to execute commands through substrate")
        
        # Main daemon loop
        self.daemon_loop()
    
    def load_omni_context(self):
        """Load OMNI codebase context"""
        self.logger.info("📚 Loading OMNI context...")
        
        try:
            # Key OMNI files and their purposes
            self.omni_context = {
                'main_console': '/home/kali/Desktop/MITEL/Mitel-main/omni_web_console.py',
                'ai_chat': '/home/kali/Desktop/MITEL/Mitel-main/omni_ai_chat_simple.py',
                'mitel_subsystem': '/home/kali/Desktop/MITEL/Mitel-main/substrate/mitel_subsystem.py',
                'nexus_container': '/home/kali/Desktop/MITEL/Mitel-main/substrate/ai_layer/nexus_container_layer.py',
                'command_executor': '/home/kali/Desktop/MITEL/Mitel-main/substrate/ai_layer/ai_command_executor.py',
                'launchers': {
                    'complete_demo': '/home/kali/Desktop/MITEL/Mitel-main/START_COMPLETE_DEMO.sh',
                    'real_launcher': '/home/kali/Desktop/MITEL/Mitel-main/OMNI_REAL_LAUNCHER.sh'
                },
                'ports': {
                    'console': 8888,
                    'ai_chat': 8889,
                    'substrate': 7777
                },
                'processes': {
                    'console': 'omni_web_console.py',
                    'ai_chat': 'omni_ai_chat_simple.py',
                    'substrate': 'omni_core.py'
                }
            }
            
            self.logger.info("✅ OMNI context loaded")
            self.logger.info(f"📁 Monitoring {len(self.omni_context)} key components")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to load OMNI context: {e}")
    
    def load_nexus_capabilities(self):
        """Load NEXUS expanded capabilities"""
        self.logger.info("🧠 Loading NEXUS capabilities...")
        
        try:
            # Import capabilities module
            sys.path.insert(0, '/home/kali/Desktop/MITEL/Mitel-main/nexus_omnipresent')
            from nexus_capabilities import NexusCapabilities
            
            # Initialize capabilities
            self.nexus_capabilities = NexusCapabilities()
            
            # Get capability summary
            summary = self.nexus_capabilities.get_capability_summary()
            
            self.logger.info("✅ NEXUS capabilities loaded")
            self.logger.info(f"🎯 {summary['total_capabilities']} core capabilities")
            self.logger.info(f"🔧 {summary['total_tools']} tools discovered")
            self.logger.info(f"🚨 {len(summary['critical_tools'])} critical tools")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to load NEXUS capabilities: {e}")
            self.nexus_capabilities = None
    
    def start_command_server(self):
        """Start socket server for receiving commands"""
        def server_loop():
            try:
                self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self.server_socket.bind(('localhost', self.socket_port))
                self.server_socket.listen(5)
                
                self.logger.info(f"🌐 Command server listening on port {self.socket_port}")
                
                while self.running:
                    try:
                        client_socket, address = self.server_socket.accept()
                        threading.Thread(target=self.handle_command, args=(client_socket,)).start()
                    except Exception as e:
                        if self.running:
                            self.logger.error(f"❌ Command server error: {e}")
                            
            except Exception as e:
                self.logger.error(f"❌ Failed to start command server: {e}")
        
        server_thread = threading.Thread(target=server_loop, daemon=True)
        server_thread.start()
    
    def handle_command(self, client_socket):
        """Handle incoming command from UI"""
        try:
            # Receive command
            data = client_socket.recv(4096).decode('utf-8')
            if not data:
                return
            
            command = json.loads(data)
            self.logger.info(f"🎯 Received command: {command.get('action', 'unknown')}")
            
            # Execute command
            result = self.execute_command(command)
            
            # Send response
            response = json.dumps(result)
            client_socket.send(response.encode('utf-8'))
            
        except Exception as e:
            self.logger.error(f"❌ Command handling error: {e}")
            error_response = json.dumps({
                'status': 'error',
                'message': str(e),
                'timestamp': datetime.now().isoformat()
            })
            client_socket.send(error_response.encode('utf-8'))
        finally:
            client_socket.close()
    
    def execute_command(self, command):
        """Execute command through substrate"""
        action = command.get('action', '').lower()
        
        try:
            if action == 'start_omni':
                return self.start_omni_engine()
            elif action == 'stop_omni':
                return self.stop_omni_engine()
            elif action == 'restart_omni':
                return self.restart_omni_engine()
            elif action == 'status':
                return self.get_system_status()
            elif action == 'fix_broken':
                return self.fix_broken_services()
            elif action == 'kill_port':
                port = command.get('port')
                return self.kill_process_on_port(port)
            elif action == 'clear_python':
                return self.clear_python_processes()
            elif action == 'auto_discover':
                return self.execute_nexus_capability('auto_discover_tools')
            elif action == 'auto_recover':
                return self.execute_nexus_capability('auto_recover')
            elif action == 'continue_operations':
                return self.execute_nexus_capability('continue_operations')
            elif action == 'capabilities':
                return self.get_capabilities_summary()
            else:
                return {
                    'status': 'unknown_command',
                    'message': f'Unknown command: {action}',
                    'available_commands': list(self.get_available_commands()),
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            self.logger.error(f"❌ Command execution failed: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def start_omni_engine(self):
        """Start OMNI engine - MASTER COMMAND"""
        self.logger.info("🚀 Starting OMNI engine...")
        
        results = []
        
        # Step 1: Kill conflicting processes
        self.logger.info("🛑 Killing conflicting processes...")
        self.kill_process_on_port(8888)
        self.kill_process_on_port(8889)
        self.clear_python_processes()
        time.sleep(2)
        
        # Step 2: Start OMNI console
        self.logger.info("🖥️ Starting OMNI console...")
        try:
            console_path = self.omni_context['main_console']
            subprocess.Popen([
                'python3', console_path,
                '--port', str(self.omni_context['ports']['console']),
                '--no-browser'
            ], cwd='/home/kali/Desktop/MITEL/Mitel-main')
            results.append("✅ OMNI Console started")
            time.sleep(3)
        except Exception as e:
            results.append(f"❌ Console failed: {e}")
        
        # Step 3: Start AI chat
        self.logger.info("💬 Starting AI chat...")
        try:
            chat_path = self.omni_context['ai_chat']
            subprocess.Popen([
                'python3', chat_path,
                '--port', str(self.omni_context['ports']['ai_chat']),
                '--no-browser'
            ], cwd='/home/kali/Desktop/MITEL/Mitel-main')
            results.append("✅ AI Chat started")
            time.sleep(2)
        except Exception as e:
            results.append(f"❌ AI Chat failed: {e}")
        
        # Step 4: Verify services
        self.logger.info("🔍 Verifying services...")
        verification = self.verify_services()
        results.extend(verification)
        
        # Step 5: Report
        return {
            'status': 'completed',
            'action': 'start_omni',
            'results': results,
            'services': self.get_service_status(),
            'urls': {
                'console': f"http://localhost:{self.omni_context['ports']['console']}",
                'ai_chat': f"http://localhost:{self.omni_context['ports']['ai_chat']}"
            },
            'timestamp': datetime.now().isoformat()
        }
    
    def stop_omni_engine(self):
        """Stop OMNI engine"""
        self.logger.info("🛑 Stopping OMNI engine...")
        
        results = []
        
        # Kill all OMNI processes
        for process_name in self.omni_context['processes'].values():
            try:
                subprocess.run(['pkill', '-f', process_name], check=False)
                results.append(f"✅ Killed {process_name}")
            except Exception as e:
                results.append(f"❌ Failed to kill {process_name}: {e}")
        
        time.sleep(2)
        
        return {
            'status': 'completed',
            'action': 'stop_omni',
            'results': results,
            'timestamp': datetime.now().isoformat()
        }
    
    def restart_omni_engine(self):
        """Restart OMNI engine"""
        self.logger.info("🔄 Restarting OMNI engine...")
        
        # Stop first
        stop_result = self.stop_omni_engine()
        time.sleep(3)
        
        # Then start
        start_result = self.start_omni_engine()
        
        return {
            'status': 'completed',
            'action': 'restart_omni',
            'stop_result': stop_result,
            'start_result': start_result,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_system_status(self):
        """Get comprehensive system status"""
        self.logger.info("📊 Getting system status...")
        
        return {
            'status': 'completed',
            'action': 'status',
            'services': self.get_service_status(),
            'processes': self.get_running_processes(),
            'ports': self.get_port_status(),
            'omni_context': {
                'console_file': os.path.exists(self.omni_context['main_console']),
                'ai_chat_file': os.path.exists(self.omni_context['ai_chat']),
                'launcher_file': os.path.exists(self.omni_context['launchers']['real_launcher'])
            },
            'timestamp': datetime.now().isoformat()
        }
    
    def fix_broken_services(self):
        """Auto-diagnose and fix broken services"""
        self.logger.info("🔧 Fixing broken services...")
        
        results = []
        
        # Check what's broken
        status = self.get_service_status()
        
        # Fix console if broken
        if not status.get('console_running', False):
            results.append("🔧 Console not running - restarting...")
            try:
                console_path = self.omni_context['main_console']
                subprocess.Popen([
                    'python3', console_path,
                    '--port', str(self.omni_context['ports']['console']),
                    '--no-browser'
                ], cwd='/home/kali/Desktop/MITEL/Mitel-main')
                results.append("✅ Console restarted")
            except Exception as e:
                results.append(f"❌ Console restart failed: {e}")
        
        # Fix AI chat if broken
        if not status.get('ai_chat_running', False):
            results.append("🔧 AI Chat not running - restarting...")
            try:
                chat_path = self.omni_context['ai_chat']
                subprocess.Popen([
                    'python3', chat_path,
                    '--port', str(self.omni_context['ports']['ai_chat']),
                    '--no-browser'
                ], cwd='/home/kali/Desktop/MITEL/Mitel-main')
                results.append("✅ AI Chat restarted")
            except Exception as e:
                results.append(f"❌ AI Chat restart failed: {e}")
        
        return {
            'status': 'completed',
            'action': 'fix_broken',
            'results': results,
            'new_status': self.get_service_status(),
            'timestamp': datetime.now().isoformat()
        }
    
    def kill_process_on_port(self, port):
        """Kill process running on specific port"""
        if not port:
            return {'status': 'error', 'message': 'No port specified'}
        
        try:
            # Find process on port
            result = subprocess.run(
                ['lsof', '-ti', f':{port}'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                pids = result.stdout.strip().split('\n')
                killed = []
                for pid in pids:
                    if pid:
                        subprocess.run(['kill', '-9', pid], check=False)
                        killed.append(pid)
                
                return {
                    'status': 'completed',
                    'action': 'kill_port',
                    'port': port,
                    'killed_pids': killed,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'status': 'completed',
                    'action': 'kill_port',
                    'port': port,
                    'message': 'No process found on port',
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'action': 'kill_port',
                'port': port,
                'message': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def clear_python_processes(self):
        """Clear all Python processes (except daemon)"""
        try:
            # Get all Python processes
            result = subprocess.run(
                ['ps', 'aux'],
                capture_output=True,
                text=True
            )
            
            lines = result.stdout.split('\n')
            killed = []
            
            for line in lines:
                if 'python3' in line and 'nexus_daemon.py' not in line:
                    parts = line.split()
                    if len(parts) > 1:
                        pid = parts[1]
                        try:
                            subprocess.run(['kill', '-9', pid], check=False)
                            killed.append(pid)
                        except:
                            pass
            
            return {
                'status': 'completed',
                'action': 'clear_python',
                'killed_pids': killed,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'action': 'clear_python',
                'message': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def get_service_status(self):
        """Get status of OMNI services"""
        services = {}
        
        # Check console
        console_running = self.check_port(self.omni_context['ports']['console'])
        services['console_running'] = console_running
        
        # Check AI chat
        ai_chat_running = self.check_port(self.omni_context['ports']['ai_chat'])
        services['ai_chat_running'] = ai_chat_running
        
        # Check processes
        for name, process in self.omni_context['processes'].items():
            running = subprocess.run(['pgrep', '-f', process], capture_output=True).returncode == 0
            services[f'{name}_process'] = running
        
        return services
    
    def get_running_processes(self):
        """Get list of running OMNI processes"""
        processes = []
        
        for name, process in self.omni_context['processes'].items():
            try:
                result = subprocess.run(['pgrep', '-f', process], capture_output=True, text=True)
                if result.returncode == 0:
                    pids = result.stdout.strip().split('\n')
                    processes.append({
                        'name': name,
                        'process': process,
                        'pids': [pid for pid in pids if pid]
                    })
            except:
                pass
        
        return processes
    
    def get_port_status(self):
        """Get status of OMNI ports"""
        ports = {}
        
        for name, port in self.omni_context['ports'].items():
            ports[name] = {
                'port': port,
                'open': self.check_port(port),
                'process': self.get_process_on_port(port)
            }
        
        return ports
    
    def check_port(self, port):
        """Check if port is open"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            return result == 0
        except:
            return False
    
    def get_process_on_port(self, port):
        """Get process running on port"""
        try:
            result = subprocess.run(['lsof', '-ti', f':{port}'], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
            return None
        except:
            return None
    
    def verify_services(self):
        """Verify services are responding"""
        results = []
        
        # Check console URL
        if self.check_port(self.omni_context['ports']['console']):
            results.append("✅ Console responding on port 8888")
        else:
            results.append("❌ Console not responding")
        
        # Check AI chat URL
        if self.check_port(self.omni_context['ports']['ai_chat']):
            results.append("✅ AI Chat responding on port 8889")
        else:
            results.append("❌ AI Chat not responding")
        
        return results
    
    def get_available_commands(self):
        """Get list of available commands"""
        return [
            'start_omni',
            'stop_omni', 
            'restart_omni',
            'status',
            'fix_broken',
            'kill_port',
            'clear_python',
            'auto_discover',
            'auto_recover',
            'continue_operations',
            'capabilities'
        ]
    
    def start_background_tasks(self):
        """Start background monitoring tasks"""
        def monitor_loop():
            while self.running:
                try:
                    # Monitor system health
                    self.monitor_system_health()
                    time.sleep(30)  # Check every 30 seconds
                except Exception as e:
                    self.logger.error(f"❌ Background monitoring error: {e}")
                    time.sleep(5)
        
        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()
    
    def monitor_system_health(self):
        """Monitor system health"""
        services = self.get_service_status()
        
        # Log any issues
        if not services.get('console_running', False):
            self.logger.warning("⚠️ Console not running")
        
        if not services.get('ai_chat_running', False):
            self.logger.warning("⚠️ AI Chat not running")
    
    def daemon_loop(self):
        """Main daemon loop"""
        self.logger.info("🔥 NEXUS daemon loop started")
        
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("🛑 NEXUS daemon stopping...")
            self.stop_daemon()
    
    def stop_daemon(self):
        """Stop the daemon"""
        self.running = False
        
        if self.server_socket:
            self.server_socket.close()
        
        self.logger.info("✅ NEXUS daemon stopped")
    
    def execute_nexus_capability(self, capability_name, action=None, params=None):
        """Execute NEXUS capability with MDCS authority"""
        if not self.nexus_capabilities:
            return {
                'status': 'error',
                'message': 'NEXUS capabilities not loaded',
                'timestamp': datetime.now().isoformat()
            }
        
        try:
            # Use authority-aware execution
            result = self.nexus_capabilities.execute_capability_with_authority(
                capability_name, action, params
            )
            
            # Log execution with authority info
            authority_status = self.nexus_capabilities.get_authority_status()
            self.logger.info(f"🎯 Executed capability: {capability_name} (authority: {authority_status['authority_level']})")
            
            return result
        except Exception as e:
            self.logger.error(f"❌ Capability execution failed: {e}")
            return {
                'status': 'error',
                'message': f'Capability execution failed: {e}',
                'capability': capability_name,
                'timestamp': datetime.now().isoformat()
            }
    
    def get_capabilities_summary(self):
        """Get NEXUS capabilities summary"""
        if not self.nexus_capabilities:
            return {
                'status': 'error',
                'message': 'NEXUS capabilities not loaded',
                'timestamp': datetime.now().isoformat()
            }
        
        try:
            summary = self.nexus_capabilities.get_capability_summary()
            
            return {
                'status': 'completed',
                'action': 'capabilities',
                'summary': summary,
                'detailed_capabilities': {
                    name: {
                        'description': cap['description'],
                        'actions': cap['actions'],
                        'features': [k for k in cap.keys() if k not in ['description', 'actions']]
                    }
                    for name, cap in self.nexus_capabilities.capabilities.items()
                },
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Failed to get capabilities: {e}',
                'timestamp': datetime.now().isoformat()
            }

def main():
    """Main entry point"""
    daemon = NexusDaemon()
    
    try:
        daemon.start_daemon()
    except KeyboardInterrupt:
        print("\n🛑 Stopping NEXUS daemon...")
        daemon.stop_daemon()
    except Exception as e:
        print(f"❌ Daemon error: {e}")
        daemon.stop_daemon()

if __name__ == "__main__":
    main()
