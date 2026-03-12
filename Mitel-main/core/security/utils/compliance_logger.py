#!/usr/bin/env python3
"""
GhostAI Compliance Logger
Legal and audit logging - proves everything was authorized
"""

import json
import os
import hashlib
import getpass
import socket
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path


class ComplianceEvent:
    """Represents a single compliance/audit event"""

    def __init__(self, event_type: str, description: str,
                 user: str = None, session_id: str = None):
        self.event_id = self._generate_event_id()
        self.timestamp = datetime.now().isoformat()
        self.event_type = event_type
        self.description = description
        self.user = user or getpass.getuser()
        self.hostname = socket.gethostname()
        self.session_id = session_id
        self.ip_address = self._get_ip_address()

        # Additional metadata
        self.metadata = {}

    def _generate_event_id(self) -> str:
        """Generate unique event ID"""
        unique_string = f"{datetime.now().isoformat()}{os.getpid()}"
        return hashlib.sha256(unique_string.encode()).hexdigest()[:16]

    def _get_ip_address(self) -> str:
        """Get local IP address"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "unknown"

    def add_metadata(self, key: str, value: Any):
        """Add metadata to the event"""
        self.metadata[key] = value

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'event_id': self.event_id,
            'timestamp': self.timestamp,
            'event_type': self.event_type,
            'description': self.description,
            'user': self.user,
            'hostname': self.hostname,
            'ip_address': self.ip_address,
            'session_id': self.session_id,
            'metadata': self.metadata
        }


class EngagementAuthorization:
    """Represents legal authorization for a penetration test engagement"""

    def __init__(self, engagement_id: str, client_name: str,
                 contract_reference: str):
        self.engagement_id = engagement_id
        self.client_name = client_name
        self.contract_reference = contract_reference
        self.authorized_by = None  # Name of person who authorized
        self.authorization_date = None
        self.start_date = None
        self.end_date = None
        self.scope = {
            'authorized_targets': [],
            'authorized_ip_ranges': [],
            'excluded_targets': [],
            'authorized_techniques': [],
            'restrictions': []
        }
        self.authorized_personnel = []
        self.emergency_contacts = []

    def is_valid(self) -> bool:
        """Check if authorization is currently valid"""
        if not self.start_date or not self.end_date:
            return False

        now = datetime.now()
        start = datetime.fromisoformat(self.start_date)
        end = datetime.fromisoformat(self.end_date)

        return start <= now <= end

    def is_target_authorized(self, target: str) -> bool:
        """Check if a specific target is authorized"""
        # Check exclusions first
        if target in self.scope['excluded_targets']:
            return False

        # Check authorized targets
        if target in self.scope['authorized_targets']:
            return True

        # Check IP ranges
        for ip_range in self.scope['authorized_ip_ranges']:
            if self._target_in_range(target, ip_range):
                return True

        return False

    def _target_in_range(self, target: str, ip_range: str) -> bool:
        """Check if target is in IP range (simple implementation)"""
        # Simplified - in production use proper IP address library
        if '/' in ip_range:
            # CIDR notation
            base = ip_range.split('/')[0]
            return target.startswith('.'.join(base.split('.')[:-1]))
        return target == ip_range

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'engagement_id': self.engagement_id,
            'client_name': self.client_name,
            'contract_reference': self.contract_reference,
            'authorized_by': self.authorized_by,
            'authorization_date': self.authorization_date,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'scope': self.scope,
            'authorized_personnel': self.authorized_personnel,
            'emergency_contacts': self.emergency_contacts,
            'is_valid': self.is_valid()
        }


class ComplianceLogger:
    """
    Main compliance logging system
    Logs everything for legal/audit purposes
    """

    def __init__(self, storage_path: str = './data/compliance'):
        self.storage_path = storage_path
        self.audit_log_file = os.path.join(storage_path, 'audit_log.jsonl')
        self.authorization_file = os.path.join(storage_path, 'authorization.json')
        self.access_log_file = os.path.join(storage_path, 'access_log.jsonl')

        # Current session
        self.session_id = self._generate_session_id()
        self.current_authorization: Optional[EngagementAuthorization] = None

        # Ensure storage exists
        os.makedirs(storage_path, exist_ok=True)

        # Load authorization
        self.load_authorization()

        # Log session start
        self.log_event('session_start', 'New compliance logging session started')

    def _generate_session_id(self) -> str:
        """Generate unique session ID"""
        unique_string = f"{datetime.now().isoformat()}{os.getpid()}"
        return hashlib.sha256(unique_string.encode()).hexdigest()[:16]

    def set_authorization(self, authorization: EngagementAuthorization):
        """Set the current engagement authorization"""
        self.current_authorization = authorization
        self.save_authorization()

        self.log_event(
            'authorization_set',
            f'Engagement authorized: {authorization.engagement_id}',
            metadata={
                'client': authorization.client_name,
                'contract': authorization.contract_reference,
                'valid': authorization.is_valid()
            }
        )

    def verify_authorization(self, target: str = None) -> bool:
        """
        Verify that we have valid authorization
        Optionally check if specific target is authorized
        """
        if not self.current_authorization:
            self.log_event('authorization_check_failed', 'No authorization found')
            return False

        if not self.current_authorization.is_valid():
            self.log_event(
                'authorization_expired',
                f'Authorization expired for {self.current_authorization.engagement_id}'
            )
            return False

        if target and not self.current_authorization.is_target_authorized(target):
            self.log_event(
                'unauthorized_target',
                f'Target not authorized: {target}',
                metadata={'target': target}
            )
            return False

        return True

    def log_event(self, event_type: str, description: str,
                  metadata: Dict[str, Any] = None) -> ComplianceEvent:
        """
        Log a compliance event
        Returns the created event
        """
        event = ComplianceEvent(event_type, description, session_id=self.session_id)

        if metadata:
            for key, value in metadata.items():
                event.add_metadata(key, value)

        # Add authorization context
        if self.current_authorization:
            event.add_metadata('engagement_id', self.current_authorization.engagement_id)
            event.add_metadata('contract_ref', self.current_authorization.contract_reference)

        # Write to audit log (append-only)
        self._write_to_audit_log(event)

        return event

    def log_tool_execution(self, tool_name: str, target: str,
                          parameters: Dict[str, Any] = None) -> ComplianceEvent:
        """Log execution of a security tool"""

        # Verify authorization first
        if not self.verify_authorization(target):
            return self.log_event(
                'unauthorized_execution_blocked',
                f'Blocked unauthorized execution of {tool_name} against {target}',
                metadata={
                    'tool': tool_name,
                    'target': target,
                    'reason': 'Authorization check failed'
                }
            )

        return self.log_event(
            'tool_execution',
            f'Executed {tool_name} against {target}',
            metadata={
                'tool': tool_name,
                'target': target,
                'parameters': parameters or {}
            }
        )

    def log_data_access(self, data_type: str, source: str,
                       justification: str) -> ComplianceEvent:
        """Log access to sensitive data"""

        event = self.log_event(
            'data_access',
            f'Accessed {data_type} from {source}',
            metadata={
                'data_type': data_type,
                'source': source,
                'justification': justification
            }
        )

        # Also write to access log
        self._write_to_access_log(event)

        return event

    def log_vulnerability_discovered(self, vulnerability: Dict[str, Any],
                                    target: str) -> ComplianceEvent:
        """Log discovery of a vulnerability"""
        return self.log_event(
            'vulnerability_discovered',
            f'Discovered {vulnerability.get("type", "unknown")} on {target}',
            metadata={
                'vulnerability': vulnerability,
                'target': target,
                'severity': vulnerability.get('severity', 'unknown')
            }
        )

    def log_exploitation_attempt(self, target: str, technique: str,
                                 success: bool) -> ComplianceEvent:
        """Log exploitation attempt"""
        return self.log_event(
            'exploitation_attempt',
            f'Exploitation attempt: {technique} against {target} - {"SUCCESS" if success else "FAILED"}',
            metadata={
                'target': target,
                'technique': technique,
                'success': success
            }
        )

    def log_authentication_attempt(self, target: str, username: str,
                                   success: bool) -> ComplianceEvent:
        """Log authentication attempt"""
        return self.log_event(
            'authentication_attempt',
            f'Auth attempt for {username}@{target} - {"SUCCESS" if success else "FAILED"}',
            metadata={
                'target': target,
                'username': username,
                'success': success
            }
        )

    def get_audit_trail(self, event_type: str = None,
                       start_time: str = None,
                       end_time: str = None,
                       limit: int = 100) -> List[Dict[str, Any]]:
        """
        Retrieve audit trail with optional filtering
        """
        events = []

        if not os.path.exists(self.audit_log_file):
            return events

        with open(self.audit_log_file, 'r') as f:
            for line in f:
                try:
                    event = json.loads(line.strip())

                    # Filter by event type
                    if event_type and event['event_type'] != event_type:
                        continue

                    # Filter by time range
                    if start_time and event['timestamp'] < start_time:
                        continue
                    if end_time and event['timestamp'] > end_time:
                        continue

                    events.append(event)

                    if len(events) >= limit:
                        break
                except json.JSONDecodeError:
                    continue

        # Return most recent first
        events.reverse()
        return events

    def generate_compliance_report(self) -> Dict[str, Any]:
        """Generate compliance report for audit purposes"""

        # Count events by type
        event_counts = {}
        total_events = 0

        if os.path.exists(self.audit_log_file):
            with open(self.audit_log_file, 'r') as f:
                for line in f:
                    try:
                        event = json.loads(line.strip())
                        event_type = event.get('event_type', 'unknown')
                        event_counts[event_type] = event_counts.get(event_type, 0) + 1
                        total_events += 1
                    except json.JSONDecodeError:
                        continue

        return {
            'report_generated': datetime.now().isoformat(),
            'session_id': self.session_id,
            'authorization': self.current_authorization.to_dict() if self.current_authorization else None,
            'total_events': total_events,
            'events_by_type': event_counts,
            'storage_path': self.storage_path
        }

    def _write_to_audit_log(self, event: ComplianceEvent):
        """Write event to audit log (append-only)"""
        with open(self.audit_log_file, 'a') as f:
            f.write(json.dumps(event.to_dict()) + '\n')

    def _write_to_access_log(self, event: ComplianceEvent):
        """Write event to access log"""
        with open(self.access_log_file, 'a') as f:
            f.write(json.dumps(event.to_dict()) + '\n')

    def save_authorization(self):
        """Save authorization to disk"""
        if not self.current_authorization:
            return

        with open(self.authorization_file, 'w') as f:
            json.dump(self.current_authorization.to_dict(), f, indent=2)

    def load_authorization(self):
        """Load authorization from disk"""
        if not os.path.exists(self.authorization_file):
            return

        try:
            with open(self.authorization_file, 'r') as f:
                data = json.load(f)

            auth = EngagementAuthorization(
                data['engagement_id'],
                data['client_name'],
                data['contract_reference']
            )
            auth.authorized_by = data.get('authorized_by')
            auth.authorization_date = data.get('authorization_date')
            auth.start_date = data.get('start_date')
            auth.end_date = data.get('end_date')
            auth.scope = data.get('scope', {})
            auth.authorized_personnel = data.get('authorized_personnel', [])
            auth.emergency_contacts = data.get('emergency_contacts', [])

            self.current_authorization = auth
        except Exception as e:
            print(f"[!] Error loading authorization: {e}")


# Global instance
_compliance_logger = None

def get_compliance_logger(storage_path: str = './data/compliance') -> ComplianceLogger:
    """Get or create global compliance logger instance"""
    global _compliance_logger
    if _compliance_logger is None:
        _compliance_logger = ComplianceLogger(storage_path)
    return _compliance_logger


if __name__ == '__main__':
    # Demo usage
    print("GhostAI Compliance Logger - Demo")
    print("=" * 60)

    logger = ComplianceLogger('./data/compliance')

    # Set up authorization
    print("\n[*] Setting up engagement authorization...")
    auth = EngagementAuthorization(
        'ENG-2024-001',
        'ABC Corporation',
        'SOW-2024-001'
    )
    auth.authorized_by = 'John Smith, CISO'
    auth.authorization_date = '2024-01-10'
    auth.start_date = '2024-01-15T00:00:00'
    auth.end_date = '2024-01-30T23:59:59'
    auth.scope['authorized_targets'] = ['webserver.abc.com', 'mail.abc.com']
    auth.scope['authorized_ip_ranges'] = ['192.168.1.0/24']
    auth.scope['excluded_targets'] = ['production-db.abc.com']
    auth.authorized_personnel = ['GhostAI Agent', 'Security Team Lead']

    logger.set_authorization(auth)
    print("[✓] Authorization configured")

    # Verify authorization
    print("\n[*] Verifying authorization...")
    if logger.verify_authorization():
        print("[✓] Authorization valid")
    else:
        print("[!] Authorization invalid")

    # Log various events
    print("\n[*] Logging security testing activities...")

    # Tool executions
    logger.log_tool_execution('nmap', 'webserver.abc.com', {
        'ports': '1-1000',
        'scan_type': 'SYN'
    })

    logger.log_tool_execution('burp', 'webserver.abc.com', {
        'target': '/admin'
    })

    # Try unauthorized target (should be blocked)
    logger.log_tool_execution('sqlmap', 'production-db.abc.com', {
        'target': '/api'
    })

    # Vulnerability discovery
    logger.log_vulnerability_discovered({
        'type': 'SQL Injection',
        'severity': 'CRITICAL',
        'cvss': 9.8
    }, 'webserver.abc.com')

    # Exploitation attempts
    logger.log_exploitation_attempt('webserver.abc.com', 'SQL Injection', True)
    logger.log_exploitation_attempt('mail.abc.com', 'Brute Force', False)

    # Data access
    logger.log_data_access('User Database', 'webserver.abc.com', 'Verify exploitation success')

    # Authentication attempts
    logger.log_authentication_attempt('webserver.abc.com', 'admin', True)
    logger.log_authentication_attempt('mail.abc.com', 'root', False)

    print("[✓] Events logged")

    # Get audit trail
    print("\n" + "=" * 60)
    print("[*] Recent Audit Trail (last 5 events):")
    print("=" * 60)
    trail = logger.get_audit_trail(limit=5)
    for event in trail:
        print(f"\n[{event['timestamp']}]")
        print(f"Type: {event['event_type']}")
        print(f"User: {event['user']}@{event['hostname']}")
        print(f"Description: {event['description']}")

    # Generate compliance report
    print("\n" + "=" * 60)
    print("[*] Compliance Report:")
    print("=" * 60)
    report = logger.generate_compliance_report()
    print(f"\nSession ID: {report['session_id']}")
    print(f"Total Events: {report['total_events']}")
    print(f"\nEvents by Type:")
    for event_type, count in sorted(report['events_by_type'].items()):
        print(f"  {event_type}: {count}")

    if report['authorization']:
        print(f"\nAuthorization Status:")
        print(f"  Engagement: {report['authorization']['engagement_id']}")
        print(f"  Client: {report['authorization']['client_name']}")
        print(f"  Valid: {report['authorization']['is_valid']}")

    print(f"\n[✓] Audit logs: {logger.audit_log_file}")
    print(f"[✓] Access logs: {logger.access_log_file}")
    print(f"[✓] Authorization: {logger.authorization_file}")
