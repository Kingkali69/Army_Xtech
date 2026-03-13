#!/usr/bin/env python3
"""
NEXUS Network Scanner Tool
==========================

Part of the NEXUS Collective Tool Registry
Performs comprehensive network scanning with service detection
Executes in secure sandbox environment
"""

import sys
import json
import socket
import subprocess
import threading
import time
from datetime import datetime

def scan_network(inputs):
    """Perform network scan based on inputs"""
    try:
        target = inputs.get('target', '127.0.0.1')
        ports = inputs.get('ports', [22, 80, 443, 8080, 8888])
        timeout = inputs.get('timeout', 5)
        
        results = []
        open_ports = []
        services = []
        
        for port in ports:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(timeout)
                result = sock.connect_ex((target, port))
                
                if result == 0:
                    port_info = {
                        "port": port,
                        "status": "open",
                        "service": get_service_name(port),
                        "timestamp": datetime.now().isoformat()
                    }
                    open_ports.append(port)
                    services.append(port_info["service"])
                    results.append(port_info)
                
                sock.close()
                
            except Exception as e:
                results.append({
                    "port": port,
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
        
        return {
            "success": True,
            "target": target,
            "results": results,
            "open_ports": open_ports,
            "services": services,
            "scan_duration": len(ports) * timeout,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

def get_service_name(port):
    """Get common service name for port"""
    service_map = {
        21: "FTP",
        22: "SSH",
        23: "Telnet",
        25: "SMTP",
        53: "DNS",
        80: "HTTP",
        110: "POP3",
        143: "IMAP",
        443: "HTTPS",
        993: "IMAPS",
        995: "POP3S",
        8080: "HTTP-Alt",
        8888: "NEXUS Console",
        8443: "HTTPS-Alt"
    }
    return service_map.get(port, f"Unknown-{port}")

if __name__ == "__main__":
    # Get inputs from command line (passed by NEXUS sandbox)
    if len(sys.argv) > 1:
        try:
            inputs = json.loads(sys.argv[1])
            result = scan_network(inputs)
            print(json.dumps(result, indent=2))
        except Exception as e:
            print(json.dumps({
                "success": False,
                "error": f"Tool execution failed: {str(e)}"
            }))
    else:
        print(json.dumps({
            "success": False,
            "error": "No inputs provided"
        }))
