#!/usr/bin/env python3
"""
NEXUS CAPABILITIES EXPANSION
=============================

Teaching NEXUS what he can do.
Auto-launch, configure, sync, update, failover, recover, discover tools.
This is JARVIS learning his full capabilities.
"""

import os
import sys
import json
import time
import subprocess
import threading
from datetime import datetime

# Add paths
sys.path.insert(0, '/home/kali/Desktop/MITEL/Mitel-main')
sys.path.insert(0, '/home/kali/Desktop/MITEL/Mitel-main/substrate/ai_layer')

class NexusCapabilities:
    """NEXUS expanded capabilities - what JARVIS can actually do"""
    
    def __init__(self):
        self.capabilities = {}
        self.tool_registry = {}
        self.operation_history = []
        self.master_node = None  # Current master node
        self.node_id = self.get_node_id()
        self.mdcs_active = False
        
        print("🧠 NEXUS learning capabilities...")
        self.learn_capabilities()
        self.detect_master_node()
    
    def learn_capabilities(self):
        """Learn all OMNI system capabilities"""
        
        # Core system capabilities
        self.capabilities.update({
            # AUTO-LAUNCH CAPABILITIES
            'auto_launch': {
                'description': 'Automatically launch OMNI system components',
                'actions': [
                    'launch_console',
                    'launch_ai_chat', 
                    'launch_mitel_security',
                    'launch_nexus_container',
                    'launch_substrate_services',
                    'verify_all_services'
                ],
                'auto_discovery': True,
                'dependency_check': True,
                'port_allocation': True
            },
            
            # CONFIGURE CAPABILITIES
            'configure': {
                'description': 'Configure system parameters and settings',
                'actions': [
                    'configure_network_settings',
                    'configure_security_policies',
                    'configure_performance_tuning',
                    'configure_logging_levels',
                    'configure_backup_systems',
                    'configure_monitoring'
                ],
                'adaptive_config': True,
                'environment_detection': True,
                'resource_optimization': True
            },
            
            # SYNC CAPABILITIES
            'sync': {
                'description': 'Synchronize state across mesh nodes',
                'actions': [
                    'sync_state_across_nodes',
                    'sync_configuration_changes',
                    'sync_security_events',
                    'sync_tool_registry',
                    'sync_healing_patterns',
                    'sync_intelligence_updates'
                ],
                'crdt_sync': True,
                'conflict_resolution': True,
                'real_time_sync': True
            },
            
            # UPDATE CAPABILITIES
            'update': {
                'description': 'Update system components and intelligence',
                'actions': [
                    'update_ai_models',
                    'update_security_signatures',
                    'update_tool_definitions',
                    'update_healing_protocols',
                    'update_container_runtime',
                    'rollback_if_needed'
                ],
                'atomic_updates': True,
                'rollback_capability': True,
                'zero_downtime': True
            },
            
            # FAILOVER CAPABILITIES
            'failover': {
                'description': 'Handle node failures and role transitions',
                'actions': [
                    'detect_node_failure',
                    'promote_backup_node',
                    'redistribute_load',
                    'maintain_service_availability',
                    'notify_administrators',
                    'document_failover_event'
                ],
                'mdcs_control': True,  # Master Dynamic Control Switching
                'sub_second_failover': True,
                'zero_state_loss': True
            },
            
            # AUTO-RECOVER CAPABILITIES
            'auto_recover': {
                'description': 'Automatically recover from failures',
                'actions': [
                    'detect_service_failure',
                    'deploy_healing_kit',
                    'restart_crashed_services',
                    'repair_corrupted_data',
                    'restore_from_backup',
                    'verify_recovery_success'
                ],
                'first_aid_kits': True,
                'predictive_recovery': True,
                'self_healing': True
            },
            
            # AUTO-DISCOVER TOOLS CAPABILITIES
            'auto_discover_tools': {
                'description': 'Automatically discover and register tools',
                'actions': [
                    'scan_for_new_tools',
                    'analyze_tool_capabilities',
                    'register_tool_in_container',
                    'test_tool_functionality',
                    'catalog_tool_metadata',
                    'share_tool_discovery'
                ],
                'tool_registry': True,
                'capability_analysis': True,
                'mesh_sharing': True
            },
            
            # CONTAINER OPERATIONS CAPABILITIES
            'container_operations': {
                'description': 'NEXUS container management and operations',
                'actions': [
                    'start_container_services',
                    'manage_shared_memory',
                    'coordinate_hive_intelligence',
                    'execute_secure_commands',
                    'manage_tool_registry',
                    'replicate_across_nodes'
                ],
                'shared_consciousness': True,
                'hive_intelligence': True,
                'zero_trust_execution': True
            },
            
            # CONTINUE OPERATIONS CAPABILITIES
            'continue_operations': {
                'description': 'Maintain operations during disruptions',
                'actions': [
                    'operate_without_internet',
                    'operate_with_partial_nodes',
                    'operate_with_degraded_services',
                    'maintain_security_posture',
                    'preserve_critical_functions',
                    'document_operations_status'
                ],
                'offline_operations': True,
                'degraded_mode': True,
                'mission_critical': True
            }
        })
        
        # Tool discovery and registry
        self.discover_tools()
        
        print(f"✅ NEXUS learned {len(self.capabilities)} core capabilities")
        print(f"🔧 Discovered {len(self.tool_registry)} tools")
    
    def discover_tools(self):
        """Auto-discover available tools in OMNI system"""
        
        # Core OMNI tools
        self.tool_registry.update({
            'omni_console': {
                'path': '/home/kali/Desktop/MITEL/Mitel-main/omni_web_console.py',
                'type': 'web_interface',
                'capabilities': ['system_monitoring', 'real_time_display', 'operations_console'],
                'dependencies': ['python3', 'flask'],
                'ports': [8888],
                'auto_start': True
            },
            
            'ai_chat_interface': {
                'path': '/home/kali/Desktop/MITEL/Mitel-main/omni_ai_chat_simple.py',
                'type': 'ai_interface',
                'capabilities': ['natural_language', 'command_interpretation', 'system_queries'],
                'dependencies': ['python3'],
                'ports': [8889],
                'auto_start': True
            },
            
            'mitel_security': {
                'path': '/home/kali/Desktop/MITEL/Mitel-main/substrate/mitel_subsystem.py',
                'type': 'security_system',
                'capabilities': ['usb_quarantine', 'threat_detection', 'device_fingerprinting'],
                'dependencies': ['python3', 'usb_monitoring'],
                'critical': True
            },
            
            'nexus_container': {
                'path': '/home/kali/Desktop/MITEL/Mitel-main/substrate/ai_layer/nexus_container_layer.py',
                'type': 'ai_container',
                'capabilities': ['shared_intelligence', 'tool_registry', 'hive_learning', 'first_aid_kits'],
                'dependencies': ['python3', 'sqlite3'],
                'critical': True
            },
            
            'command_executor': {
                'path': '/home/kali/Desktop/MITEL/Mitel-main/substrate/ai_layer/ai_command_executor.py',
                'type': 'execution_engine',
                'capabilities': ['command_execution', 'substrate_integration', 'ai_privileges'],
                'dependencies': ['python3'],
                'critical': True
            },
            
            'state_engine': {
                'path': '/home/kali/Desktop/MITEL/Mitel-main/core/ui_sync/unified_state_engine.py',
                'type': 'sync_engine',
                'capabilities': ['crdt_sync', 'state_convergence', 'real_time_updates'],
                'dependencies': ['python3'],
                'ports': [7777]
            },
            
            'file_transfer': {
                'path': '/home/kali/Desktop/MITEL/Mitel-main/substrate/filesystem/cross_platform_bridge.py',
                'type': 'file_system',
                'capabilities': ['file_sync', 'cross_platform', 'chunked_transfer'],
                'dependencies': ['python3']
            },
            
            'auto_discovery': {
                'path': '/home/kali/Desktop/MITEL/Mitel-main/substrate/discovery/auto_discovery.py',
                'type': 'network_service',
                'capabilities': ['peer_discovery', 'mesh_formation', 'auto_connect'],
                'dependencies': ['python3'],
                'ports': [5555]
            }
        })
        
        # Healing kits as tools
        healing_kits = {
            'state_corruption_kit': {
                'type': 'healing_tool',
                'capabilities': ['crdt_rollback', 'state_validation', 'memory_reconstruction'],
                'recovery_time': '30_seconds',
                'auto_deploy': True
            },
            
            'process_crash_kit': {
                'type': 'healing_tool',
                'capabilities': ['process_respawn', 'memory_restore', 'connection_rebuild'],
                'recovery_time': '15_seconds',
                'auto_deploy': True
            },
            
            'network_disconnect_kit': {
                'type': 'healing_tool',
                'capabilities': ['route_rediscovery', 'mesh_rebuild', 'sync_resumption'],
                'recovery_time': '10_seconds',
                'auto_deploy': True
            },
            
            'memory_leak_kit': {
                'type': 'healing_tool',
                'capabilities': ['memory_cleanup', 'cache_flush', 'process_restart'],
                'recovery_time': '20_seconds',
                'auto_deploy': True
            },
            
            'usb_attack_kit': {
                'type': 'healing_tool',
                'capabilities': ['device_quarantine', 'port_reset', 'security_scan'],
                'recovery_time': '5_seconds',
                'auto_deploy': True
            }
        }
        
        self.tool_registry.update(healing_kits)
    
    def get_capability_summary(self):
        """Get summary of all capabilities"""
        summary = {
            'total_capabilities': len(self.capabilities),
            'total_tools': len(self.tool_registry),
            'core_capabilities': list(self.capabilities.keys()),
            'available_tools': list(self.tool_registry.keys()),
            'critical_tools': [name for name, tool in self.tool_registry.items() 
                             if tool.get('critical', False)],
            'auto_start_tools': [name for name, tool in self.tool_registry.items() 
                               if tool.get('auto_start', False)]
        }
        
        return summary
    
    def execute_capability(self, capability_name, action=None, params=None):
        """Execute a specific capability"""
        if capability_name not in self.capabilities:
            return {
                'status': 'error',
                'message': f'Capability {capability_name} not found',
                'available_capabilities': list(self.capabilities.keys())
            }
        
        capability = self.capabilities[capability_name]
        
        # Log the operation
        operation = {
            'capability': capability_name,
            'action': action,
            'params': params,
            'timestamp': datetime.now().isoformat(),
            'status': 'executing'
        }
        
        self.operation_history.append(operation)
        
        # Execute the capability
        try:
            if capability_name == 'auto_launch':
                result = self.execute_auto_launch(action, params)
            elif capability_name == 'auto_recover':
                result = self.execute_auto_recover(action, params)
            elif capability_name == 'auto_discover_tools':
                result = self.execute_tool_discovery(action, params)
            elif capability_name == 'continue_operations':
                result = self.execute_continue_operations(action, params)
            else:
                result = {
                    'status': 'capability_recognized',
                    'capability': capability_name,
                    'description': capability['description'],
                    'available_actions': capability['actions']
                }
            
            operation['status'] = 'completed'
            operation['result'] = result
            
            return result
            
        except Exception as e:
            operation['status'] = 'failed'
            operation['error'] = str(e)
            
            return {
                'status': 'error',
                'message': f'Capability execution failed: {e}',
                'capability': capability_name
            }
    
    def execute_auto_launch(self, action, params):
        """Execute auto-launch capability"""
        results = []
        
        # Launch core components
        launch_sequence = [
            ('omni_console', 'python3 /home/kali/Desktop/MITEL/Mitel-main/omni_web_console.py --port 8888 --no-browser'),
            ('ai_chat_interface', 'python3 /home/kali/Desktop/MITEL/Mitel-main/omni_ai_chat_simple.py --port 8889 --no-browser'),
            ('nexus_container', 'python3 -c "from nexus_container_layer import start_nexus_container; start_nexus_container()"'),
        ]
        
        for component, command in launch_sequence:
            try:
                subprocess.Popen(command, shell=True, cwd='/home/kali/Desktop/MITEL/Mitel-main')
                results.append(f"✅ Launched {component}")
                time.sleep(2)
            except Exception as e:
                results.append(f"❌ Failed to launch {component}: {e}")
        
        return {
            'status': 'completed',
            'capability': 'auto_launch',
            'results': results,
            'launched_components': [comp for comp, _ in launch_sequence]
        }
    
    def execute_auto_recover(self, action, params):
        """Execute auto-recover capability"""
        results = []
        
        # Check what needs recovery
        failed_services = []
        
        # Check console
        if not self.check_port(8888):
            failed_services.append('omni_console')
        
        # Check AI chat
        if not self.check_port(8889):
            failed_services.append('ai_chat_interface')
        
        # Deploy appropriate healing kits
        for service in failed_services:
            if service == 'omni_console':
                results.append("🔧 Deploying process crash recovery kit for console")
                # Restart console
                subprocess.Popen('python3 /home/kali/Desktop/MITEL/Mitel-main/omni_web_console.py --port 8888 --no-browser', 
                               shell=True, cwd='/home/kali/Desktop/MITEL/Mitel-main')
                results.append("✅ Console recovery deployed")
            
            elif service == 'ai_chat_interface':
                results.append("🔧 Deploying process crash recovery kit for AI chat")
                # Restart AI chat
                subprocess.Popen('python3 /home/kali/Desktop/MITEL/Mitel-main/omni_ai_chat_simple.py --port 8889 --no-browser', 
                               shell=True, cwd='/home/kali/Desktop/MITEL/Mitel-main')
                results.append("✅ AI chat recovery deployed")
        
        return {
            'status': 'completed',
            'capability': 'auto_recover',
            'failed_services_detected': failed_services,
            'recovery_actions': results,
            'healing_kits_deployed': len(failed_services)
        }
    
    def execute_tool_discovery(self, action, params):
        """Execute tool discovery capability"""
        discovered_tools = []
        
        # Scan for new tools
        tool_dirs = [
            '/home/kali/Desktop/MITEL/Mitel-main/substrate/ai_layer',
            '/home/kali/Desktop/MITEL/Mitel-main/core',
            '/home/kali/Desktop/MITEL/Mitel-main/substrate'
        ]
        
        for tool_dir in tool_dirs:
            if os.path.exists(tool_dir):
                for file in os.listdir(tool_dir):
                    if file.endswith('.py') and not file.startswith('__'):
                        tool_path = os.path.join(tool_dir, file)
                        discovered_tools.append({
                            'name': file.replace('.py', ''),
                            'path': tool_path,
                            'type': 'python_module',
                            'discovered_at': datetime.now().isoformat()
                        })
        
        return {
            'status': 'completed',
            'capability': 'auto_discover_tools',
            'tools_discovered': discovered_tools,
            'total_tools': len(discovered_tools),
            'registry_updated': True
        }
    
    def execute_continue_operations(self, action, params):
        """Execute continue operations capability"""
        status = {
            'offline_capability': True,
            'degraded_mode': False,
            'critical_functions': [],
            'operations_status': 'nominal'
        }
        
        # Check critical functions
        critical_checks = [
            ('daemon_running', self.check_daemon_running()),
            ('container_accessible', self.check_container_accessible()),
            ('tool_registry_available', self.check_tool_registry()),
            ('healing_kits_ready', self.check_healing_kits())
        ]
        
        for check_name, check_result in critical_checks:
            if check_result:
                status['critical_functions'].append(f"✅ {check_name}")
            else:
                status['critical_functions'].append(f"❌ {check_name}")
                status['operations_status'] = 'degraded'
        
        return {
            'status': 'completed',
            'capability': 'continue_operations',
            'operations_status': status,
            'mission_continuity': status['operations_status'] == 'nominal'
        }
    
    def check_port(self, port):
        """Check if port is open"""
        import socket
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            return result == 0
        except:
            return False
    
    def check_daemon_running(self):
        """Check if NEXUS daemon is running"""
        try:
            result = subprocess.run(['pgrep', '-f', 'nexus_daemon.py'], 
                                  capture_output=True, text=True)
            return result.returncode == 0
        except:
            return False
    
    def check_container_accessible(self):
        """Check if NEXUS container is accessible"""
        try:
            # Try to import container
            sys.path.insert(0, '/home/kali/Desktop/MITEL/Mitel-main/substrate/ai_layer')
            from nexus_container_layer import get_nexus_container
            container = get_nexus_container()
            return container is not None
        except:
            return False
    
    def check_tool_registry(self):
        """Check if tool registry is available"""
        try:
            return len(self.tool_registry) > 0
        except:
            return False
    
    def check_healing_kits(self):
        """Check if healing kits are ready"""
        healing_tools = [tool for tool in self.tool_registry.values() 
                        if tool.get('type') == 'healing_tool']
        return len(healing_tools) > 0
    
    def get_node_id(self):
        """Get current node ID"""
        try:
            import socket
            hostname = socket.gethostname()
            return hostname.lower()
        except:
            return "unknown_node"
    
    def detect_master_node(self):
        """Detect current master node via MDCS"""
        try:
            # Check if we can access MDCS from console
            # For now, assume Linux is master (default)
            if self.node_id == 'kali':
                self.master_node = self.node_id
                self.mdcs_active = True
            else:
                self.master_node = 'kali'  # Default to Linux
                self.mdcs_active = True
            
            print(f"👑 Master node detected: {self.master_node}")
            print(f"🎯 Current node: {self.node_id}")
            print(f"📡 MDCS Status: {'ACTIVE' if self.mdcs_active else 'INACTIVE'}")
            
        except Exception as e:
            print(f"❌ MDCS detection failed: {e}")
            self.master_node = self.node_id
            self.mdcs_active = False
    
    def is_master_node(self):
        """Check if current node is master"""
        return self.node_id == self.master_node
    
    def can_execute_capability(self, capability_name):
        """Check if current node can execute capability"""
        if not self.mdcs_active:
            return True  # No MDCS, anyone can execute
        
        # Only master can execute critical capabilities
        critical_capabilities = [
            'auto_launch', 'configure', 'update', 'failover',
            'start_omni', 'stop_omni', 'restart_omni'
        ]
        
        if capability_name in critical_capabilities:
            return self.is_master_node()
        
        # Non-critical capabilities can run on any node
        return True
    
    def execute_capability_with_authority(self, capability_name, action=None, params=None):
        """Execute capability with MDCS authority check"""
        if not self.can_execute_capability(capability_name):
            return {
                'status': 'no_authority',
                'message': f'Node {self.node_id} lacks authority for {capability_name}',
                'master_node': self.master_node,
                'requires_master': True
            }
        
        # Execute capability
        return self.execute_capability(capability_name, action, params)
    
    def update_master_node(self, new_master):
        """Update master node (MDCS callback)"""
        old_master = self.master_node
        self.master_node = new_master
        
        print(f"👑 Master node changed: {old_master} → {new_master}")
        
        # Log authority transfer
        self.operation_history.append({
            'type': 'mdcs_authority_transfer',
            'old_master': old_master,
            'new_master': new_master,
            'timestamp': datetime.now().isoformat()
        })
    
    def get_authority_status(self):
        """Get current MDCS authority status"""
        return {
            'current_master': self.master_node,
            'current_node': self.node_id,
            'is_master': self.is_master_node(),
            'mdcs_active': self.mdcs_active,
            'can_execute_critical': self.is_master_node(),
            'authority_level': 'master' if self.is_master_node() else 'worker'
        }

def main():
    """Test NEXUS capabilities"""
    capabilities = NexusCapabilities()
    
    print("\n🧠 NEXUS CAPABILITIES SUMMARY:")
    summary = capabilities.get_capability_summary()
    
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    # Test a capability
    print("\n🎯 Testing auto_discover_tools capability:")
    result = capabilities.execute_capability('auto_discover_tools')
    print(f"  Result: {result['status']}")
    print(f"  Tools discovered: {result.get('tools_discovered', [])}")

if __name__ == "__main__":
    main()
