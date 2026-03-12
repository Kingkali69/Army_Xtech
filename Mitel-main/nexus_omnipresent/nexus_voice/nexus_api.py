#!/usr/bin/env python3
"""
NEXUS API Layer
==============

Pulls live data from OMNI endpoints and NEXUS daemon.
Real-time data for voice responses.
"""

import requests
import socket
import json
from datetime import datetime

class NexusAPI:
    """Live data connection to OMNI and NEXUS"""
    
    def __init__(self, omni_host="localhost", omni_port=8888, nexus_port=9999):
        self.omni_base = f"http://{omni_host}:{omni_port}"
        self.nexus_port = nexus_port
        self.session = requests.Session()
        self.session.timeout = 5
    
    def get_systems_report(self):
        """Get comprehensive systems report"""
        try:
            # Get NEXUS status
            nexus_status = self.get_nexus_status()
            
            # Get OMNI status
            omni_status = self.get_omni_status()
            
            # Get M.I.T.E.L. security status
            security_status = self.get_security_status()
            
            # Combine into report
            report = {
                "fabric_health": self._calculate_health(nexus_status, omni_status),
                "nodes": nexus_status.get("nodes", 1),
                "quorum": "STABLE" if nexus_status.get("running", False) else "UNSTABLE",
                "latency": self._calculate_latency(),
                "threats_quarantined": security_status.get("quarantined", 0),
                "threats_active": security_status.get("active", 0),
                "flags": self._generate_flags(security_status),
                "status": self._overall_status(nexus_status, omni_status),
                "services": {
                    "console": omni_status.get("console_running", False),
                    "ai_chat": omni_status.get("ai_chat_running", False),
                    "daemon": nexus_status.get("running", False)
                },
                "timestamp": datetime.now().isoformat()
            }
            
            return report
            
        except Exception as e:
            return {
                "status": "ERROR",
                "error": str(e),
                "fabric_health": "UNKNOWN",
                "nodes": 0,
                "quorum": "DOWN",
                "latency": "UNKNOWN",
                "threats_quarantined": 0,
                "threats_active": 0,
                "flags": [f"System error: {str(e)}"],
                "timestamp": datetime.now().isoformat()
            }
    
    def get_nexus_status(self):
        """Get NEXUS daemon status"""
        try:
            # Connect to daemon socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            sock.connect(('localhost', self.nexus_port))
            
            # Send status command
            command = {"action": "status", "timestamp": datetime.now().isoformat()}
            sock.send(json.dumps(command).encode('utf-8'))
            
            # Get response
            response = sock.recv(4096).decode('utf-8')
            sock.close()
            
            result = json.loads(response)
            
            return {
                "running": True,
                "services": result.get("services", {}),
                "processes": result.get("processes", []),
                "ports": result.get("ports", {}),
                "timestamp": result.get("timestamp")
            }
            
        except Exception as e:
            return {"running": False, "error": str(e)}
    
    def get_omni_status(self):
        """Get OMNI web console status"""
        try:
            # Check if console is responding
            response = self.session.get(f"{self.omni_base}/", timeout=3)
            
            # Check AI chat
            chat_response = self.session.get(f"http://localhost:8889/", timeout=3)
            
            return {
                "console_running": response.status_code == 200,
                "ai_chat_running": chat_response.status_code == 200,
                "console_status": response.status_code,
                "chat_status": chat_response.status_code
            }
            
        except Exception as e:
            return {
                "console_running": False,
                "ai_chat_running": False,
                "error": str(e)
            }
    
    def get_security_status(self):
        """Get M.I.T.E.L. security status"""
        try:
            # For now, simulate security status
            # In real implementation, this would query M.I.T.E.L. subsystem
            
            # Check if M.I.T.E.L. process is running
            import subprocess
            result = subprocess.run(['pgrep', '-f', 'mitel_subsystem.py'], 
                                  capture_output=True, text=True)
            
            mitel_running = result.returncode == 0
            
            # Simulate some security data
            return {
                "mitel_running": mitel_running,
                "quarantined": 1 if mitel_running else 0,  # Your rubber ducky
                "active": 0,
                "last_threat": "USB device quarantined" if mitel_running else "None",
                "perimeter": "SECURE" if mitel_running else "UNMONITORED"
            }
            
        except Exception as e:
            return {
                "mitel_running": False,
                "quarantined": 0,
                "active": 0,
                "error": str(e)
            }
    
    def execute_nexus_command(self, command):
        """Execute command through NEXUS daemon"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            sock.connect(('localhost', self.nexus_port))
            
            # Send command
            cmd_data = {
                "action": command,
                "timestamp": datetime.now().isoformat()
            }
            sock.send(json.dumps(cmd_data).encode('utf-8'))
            
            # Get response
            response = sock.recv(8192).decode('utf-8')
            sock.close()
            
            result = json.loads(response)
            return result
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Command execution failed: {e}",
                "timestamp": datetime.now().isoformat()
            }
    
    def _calculate_health(self, nexus_status, omni_status):
        """Calculate overall fabric health"""
        health_score = 100
        
        if not nexus_status.get("running", False):
            health_score -= 50
        
        if not omni_status.get("console_running", False):
            health_score -= 25
        
        if not omni_status.get("ai_chat_running", False):
            health_score -= 25
        
        return f"{max(0, health_score)}%"
    
    def _calculate_latency(self):
        """Calculate system latency"""
        try:
            start_time = datetime.now()
            response = self.session.get(f"{self.omni_base}/", timeout=3)
            end_time = datetime.now()
            
            latency_ms = (end_time - start_time).total_seconds() * 1000
            return f"{int(latency_ms)}ms"
            
        except:
            return "HIGH"
    
    def _generate_flags(self, security_status):
        """Generate system flags"""
        flags = []
        
        if security_status.get("mitel_running", False):
            flags.append("M.I.T.E.L. security active")
        
        if security_status.get("quarantined", 0) > 0:
            flags.append(f"{security_status['quarantined']} threats quarantined")
        
        if not security_status.get("mitel_running", False):
            flags.append("Security monitoring OFFLINE")
        
        return flags
    
    def _overall_status(self, nexus_status, omni_status):
        """Determine overall system status"""
        if nexus_status.get("running", False) and omni_status.get("console_running", False):
            return "OPERATIONAL"
        elif nexus_status.get("running", False):
            return "DEGRADED"
        else:
            return "OFFLINE"

# Test function
def test_api():
    """Test API connection"""
    api = NexusAPI()
    report = api.get_systems_report()
    print("NEXUS Systems Report:")
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    test_api()
