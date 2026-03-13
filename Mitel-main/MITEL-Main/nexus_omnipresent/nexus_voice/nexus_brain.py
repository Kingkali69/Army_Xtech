#!/usr/bin/env python3
"""
NEXUS Brain - Intent & Response Generation
=========================================

Understands what you're saying and generates intelligent responses.
This is JARVIS's conversational intelligence.
"""

import re
import json
from datetime import datetime
from .nexus_api import NexusAPI
from .config import NEXUS_PERSONA, NODE_NAME

class NexusBrain:
    """NEXUS conversational intelligence"""
    
    def __init__(self):
        self.api = NexusAPI()
        self.node_name = NODE_NAME
        self.persona = NEXUS_PERSONA
        
        # Intent patterns
        self.intents = {
            "systems report": self.handle_systems_report,
            "report": self.handle_systems_report,
            "status": self.handle_systems_report,
            "security": self.handle_security_brief,
            "threats": self.handle_threat_brief,
            "quarantine": self.handle_threat_brief,
            "nodes": self.handle_node_status,
            "health": self.handle_fabric_health,
            "start omni": self.handle_start_omni,
            "launch": self.handle_start_omni,
            "stop omni": self.handle_stop_omni,
            "restart": self.handle_restart_omni,
            "fix": self.handle_fix_broken,
            "repair": self.handle_fix_broken,
            "recover": self.handle_auto_recover,
            "discover": self.handle_auto_discover,
            "capabilities": self.handle_capabilities,
            "what can you do": self.handle_capabilities,
            "go dark": self.handle_go_dark,
            "eyes open": self.handle_eyes_open,
            "ghostops": self.handle_ghostops_mode,
            "rubber ducky": self.handle_rubber_ducky,
            "usb": self.handle_usb_security
        }
    
    def process_intent(self, transcript):
        """Process user transcript and determine intent"""
        transcript_lower = transcript.lower().strip()
        
        # Check for intent matches
        for intent_pattern, handler in self.intents.items():
            if intent_pattern in transcript_lower:
                return handler(transcript)
        
        # No specific intent - general conversation
        return self.handle_general_conversation(transcript)
    
    def handle_systems_report(self, transcript):
        """Handle systems report request"""
        report = self.api.get_systems_report()
        
        if report.get("status") == "ERROR":
            return f"{self.node_name}. System error accessing fabric. {report.get('error', 'Unknown error')}. Requires immediate attention."
        
        # Build natural response
        response_parts = [
            f"{self.node_name}.",
            f"{report['nodes']} nodes active, fabric health {report['fabric_health']}, quorum {report['quorum']}.",
            f"Latency {report['latency']}."
        ]
        
        # Security section
        if report['threats_quarantined'] > 0:
            response_parts.append(
                f"Security — {report['threats_quarantined']} threats quarantined, perimeter secure."
            )
        else:
            response_parts.append("Security — perimeter clean, no active threats.")
        
        # Add flags if any
        if report.get('flags'):
            for flag in report['flags'][:2]:  # Limit to 2 flags
                response_parts.append(flag)
        
        # Status conclusion
        if report['status'] == 'OPERATIONAL':
            response_parts.append("All systems green. Mission ready.")
        elif report['status'] == 'DEGRADED':
            response_parts.append("Systems degraded. Some services require attention.")
        else:
            response_parts.append("Systems offline. Immediate recovery required.")
        
        return " ".join(response_parts)
    
    def handle_security_brief(self, transcript):
        """Handle security status request"""
        report = self.api.get_systems_report()
        
        if report['threats_quarantined'] > 0:
            return (
                f"{self.node_name}. Security posture active. "
                f"{report['threats_quarantined']} threats contained in quarantine. "
                f"Perimeter monitoring at full readiness. "
                f"{'USB device classified and contained' if 'USB' in str(report.get('flags', [])) else 'No new threats detected.'}"
            )
        else:
            return f"{self.node_name}. Security clean. No active threats. Perimeter secure."
    
    def handle_threat_brief(self, transcript):
        """Handle specific threat inquiry"""
        return self.handle_security_brief(transcript)
    
    def handle_node_status(self, transcript):
        """Handle node status request"""
        report = self.api.get_systems_report()
        
        return (
            f"{self.node_name}. {report['nodes']} nodes confirmed in fabric. "
            f"Quorum status {report['quorum']}. "
            f"Mesh communication stable."
        )
    
    def handle_fabric_health(self, transcript):
        """Handle fabric health request"""
        report = self.api.get_systems_report()
        
        return (
            f"{self.node_name}. Fabric health {report['fabric_health']}. "
            f"Core systems {'operational' if report['status'] == 'OPERATIONAL' else 'degraded'}. "
            f"Ready for mission operations."
        )
    
    def handle_start_omni(self, transcript):
        """Handle OMNI startup command"""
        result = self.api.execute_nexus_command("start_omni")
        
        if result.get("status") == "completed":
            return (
                f"{self.node_name}. Starting OMNI systems. "
                f"Launching console, AI chat, and security layers. "
                f"Services coming online now."
            )
        else:
            return f"{self.node_name}. Failed to start OMNI. {result.get('message', 'Unknown error')}."
    
    def handle_stop_omni(self, transcript):
        """Handle OMNI shutdown command"""
        result = self.api.execute_nexus_command("stop_omni")
        
        if result.get("status") == "completed":
            return f"{self.node_name}. OMNI systems shutting down. Services terminated."
        else:
            return f"{self.node_name}. Failed to stop OMNI. {result.get('message', 'Unknown error')}."
    
    def handle_restart_omni(self, transcript):
        """Handle OMNI restart command"""
        result = self.api.execute_nexus_command("restart_omni")
        
        if result.get("status") == "completed":
            return f"{self.node_name}. Restarting OMNI systems. Full reboot in progress."
        else:
            return f"{self.node_name}. Failed to restart OMNI. {result.get('message', 'Unknown error')}."
    
    def handle_fix_broken(self, transcript):
        """Handle system repair command"""
        result = self.api.execute_nexus_command("fix_broken")
        
        if result.get("status") == "completed":
            return (
                f"{self.node_name}. System recovery initiated. "
                f"Deploying healing kits to failed services. "
                f"Auto-recovery in progress."
            )
        else:
            return f"{self.node_name}. Recovery failed. {result.get('message', 'Unknown error')}."
    
    def handle_auto_recover(self, transcript):
        """Handle auto-recovery command"""
        result = self.api.execute_nexus_command("auto_recover")
        
        if result.get("status") == "completed":
            return (
                f"{self.node_name}. Auto-recovery systems activated. "
                f"Scanning for failures and deploying countermeasures. "
                f"Self-healing protocols engaged."
            )
        else:
            return f"{self.node_name}. Auto-recovery failed. {result.get('message', 'Unknown error')}."
    
    def handle_auto_discover(self, transcript):
        """Handle tool discovery command"""
        result = self.api.execute_nexus_command("auto_discover")
        
        if result.get("status") == "completed":
            tools_found = result.get("tools_discovered", [])
            return (
                f"{self.node_name}. Tool discovery complete. "
                f"Found {len(tools_found)} new tools in substrate. "
                f"Registry updated and shared across mesh."
            )
        else:
            return f"{self.node_name}. Tool discovery failed. {result.get('message', 'Unknown error')}."
    
    def handle_capabilities(self, transcript):
        """Handle capabilities inquiry"""
        result = self.api.execute_nexus_command("capabilities")
        
        if result.get("status") == "completed":
            summary = result.get("summary", {})
            return (
                f"{self.node_name}. I maintain {summary.get('total_capabilities', 0)} core capabilities. "
                f"Auto-launch, configure, sync, update, failover, auto-recover, tool discovery, "
                f"container operations, and mission continuity. "
                f"Currently managing {summary.get('total_tools', 0)} tools with {len(summary.get('critical_tools', []))} critical systems."
            )
        else:
            return f"{self.node_name}. Capabilities unavailable. {result.get('message', 'Unknown error')}."
    
    def handle_go_dark(self, transcript):
        """Handle go dark mode"""
        return (
            f"{self.node_name}. Going dark. "
            f"Disabling external communications, activating silent operations. "
            f"Maintaining internal mesh only."
        )
    
    def handle_eyes_open(self, transcript):
        """Handle eyes open mode"""
        return (
            f"{self.node_name}. Eyes open. "
            f"Full sensor suite active, perimeter monitoring at maximum. "
            f"All systems observing."
        )
    
    def handle_ghostops_mode(self, transcript):
        """Handle GhostOps mode"""
        return (
            f"{self.node_name}. GhostOps mode engaged. "
            f"Operating with minimal footprint, enhanced stealth protocols. "
            f"Mission parameters locked."
        )
    
    def handle_rubber_ducky(self, transcript):
        """Handle rubber ducky specific inquiry"""
        report = self.api.get_systems_report()
        
        if report['threats_quarantined'] > 0:
            return (
                f"{self.node_name}. Rubber ducky threat detected and neutralized. "
                f"USB device quarantined before payload execution. "
                f"M.I.T.E.L. security successful. Perimeter remains secure."
            )
        else:
            return f"{self.node_name}. No rubber ducky threats detected. USB monitoring active."
    
    def handle_usb_security(self, transcript):
        """Handle USB security inquiry"""
        return self.handle_rubber_ducky(transcript)
    
    def handle_general_conversation(self, transcript):
        """Handle general conversation without specific intent"""
        # Acknowledge and offer assistance
        responses = [
            f"{self.node_name}. I understand.",
            f"{self.node_name}. Noted.",
            f"{self.node_name}. Acknowledged."
        ]
        
        # Add contextual offer
        if "start" in transcript.lower():
            responses.append("Would you like me to start OMNI systems?")
        elif "status" in transcript.lower() or "how" in transcript.lower():
            responses.append("Request systems report for current status.")
        elif "fix" in transcript.lower() or "problem" in transcript.lower():
            responses.append("I can execute recovery protocols if needed.")
        else:
            responses.append("How can I assist with operations?")
        
        return " ".join(responses)

# Test function
def test_brain():
    """Test brain responses"""
    brain = NexusBrain()
    
    test_inputs = [
        "systems report",
        "what's the security status",
        "start omni",
        "what can you do",
        "rubber ducky status"
    ]
    
    for test_input in test_inputs:
        print(f"USER: {test_input}")
        print(f"NEXUS: {brain.process_intent(test_input)}")
        print("-" * 50)

if __name__ == "__main__":
    test_brain()
