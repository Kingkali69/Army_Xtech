"""
GhostAI Security Layer
Handles authentication, authorization, encryption, and compliance logging.
"""

import hashlib
import hmac
import json
import secrets
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from cryptography.hazmat.backends import default_backend
import base64


@dataclass
class User:
    """User object."""
    user_id: str
    username: str
    role: str  # 'admin', 'operator', 'viewer'
    permissions: List[str]
    token: Optional[str] = None
    token_expiry: Optional[str] = None


@dataclass
class Contract:
    """Contract verification object."""
    contract_id: str
    signed: bool
    authorized_by: str
    signature: str
    timestamp: str


@dataclass
class SecurityEvent:
    """Security event for compliance logging."""
    event_id: str
    user_id: str
    action: str
    resource: str
    result: str  # 'success', 'denied', 'failed'
    timestamp: str
    details: Optional[Dict[str, Any]] = None


class SecurityLayer:
    """Central security manager for GhostAI."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize security layer.

        Args:
            config: Optional security configuration
        """
        self.config = config or {}
        self.encryption_key = self._load_or_create_encryption_key()
        self.cipher = Fernet(self.encryption_key)
        self.sessions: Dict[str, User] = {}
        self.security_log: List[SecurityEvent] = []

        # Permission definitions
        self.permission_matrix = {
            'admin': ['upload_contract', 'start_engagement', 'view_status', 'view_report',
                     'view_patterns', 'configure_system', 'manage_users'],
            'operator': ['upload_contract', 'start_engagement', 'view_status', 'view_report',
                        'view_patterns'],
            'viewer': ['view_status', 'view_report']
        }

    def _load_or_create_encryption_key(self) -> bytes:
        """Load or create encryption key.

        Returns:
            Encryption key bytes
        """
        key_file = Path.home() / ".ghostops" / "encryption.key"

        if key_file.exists():
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            # Create new key
            key_file.parent.mkdir(exist_ok=True)
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            # Set restrictive permissions
            key_file.chmod(0o600)
            return key

    # Authentication
    def authenticate_user(self, username: str, password: str, protocol: str = "local") -> Optional[User]:
        """Authenticate user.

        Args:
            username: Username
            password: Password
            protocol: Authentication protocol ('local', 'dead_duck', 'oauth')

        Returns:
            User object if authenticated, None otherwise
        """
        if protocol == "local":
            return self._authenticate_local(username, password)
        elif protocol == "dead_duck":
            return self._authenticate_dead_duck(username, password)
        else:
            return None

    def _authenticate_local(self, username: str, password: str) -> Optional[User]:
        """Local authentication (for testing/development).

        Args:
            username: Username
            password: Password

        Returns:
            User object if authenticated, None otherwise
        """
        # Simple demonstration - in production, use proper password hashing
        # and user database
        test_users = {
            'admin': {'password': 'admin123', 'role': 'admin'},
            'operator': {'password': 'operator123', 'role': 'operator'},
            'viewer': {'password': 'viewer123', 'role': 'viewer'}
        }

        if username in test_users and test_users[username]['password'] == password:
            role = test_users[username]['role']
            user = User(
                user_id=f"local_{username}",
                username=username,
                role=role,
                permissions=self.permission_matrix.get(role, [])
            )

            # Generate session token
            token = self._generate_token(user.user_id)
            user.token = token
            user.token_expiry = (datetime.now() + timedelta(hours=24)).isoformat()

            # Store session
            self.sessions[token] = user

            # Log authentication
            self._log_security_event(
                user_id=user.user_id,
                action='authenticate',
                resource='system',
                result='success'
            )

            return user

        # Log failed authentication
        self._log_security_event(
            user_id=username,
            action='authenticate',
            resource='system',
            result='failed'
        )

        return None

    def _authenticate_dead_duck(self, username: str, credentials: str) -> Optional[User]:
        """Authenticate using Dead Duck protocol.

        Args:
            username: Username
            credentials: Dead Duck credentials

        Returns:
            User object if authenticated, None otherwise
        """
        # Dead Duck protocol authentication
        # This would integrate with the actual Dead Duck authentication system
        # For now, this is a placeholder

        try:
            # Verify Dead Duck credentials
            # In production, this would call the Dead Duck auth service
            is_valid = self._verify_dead_duck_credentials(username, credentials)

            if is_valid:
                user = User(
                    user_id=f"dd_{username}",
                    username=username,
                    role='operator',  # Default role for Dead Duck users
                    permissions=self.permission_matrix.get('operator', [])
                )

                token = self._generate_token(user.user_id)
                user.token = token
                user.token_expiry = (datetime.now() + timedelta(hours=24)).isoformat()

                self.sessions[token] = user

                self._log_security_event(
                    user_id=user.user_id,
                    action='authenticate_dd',
                    resource='system',
                    result='success'
                )

                return user

        except Exception as e:
            self._log_security_event(
                user_id=username,
                action='authenticate_dd',
                resource='system',
                result='failed',
                details={'error': str(e)}
            )

        return None

    def _verify_dead_duck_credentials(self, username: str, credentials: str) -> bool:
        """Verify Dead Duck credentials.

        Args:
            username: Username
            credentials: Credentials to verify

        Returns:
            True if valid, False otherwise
        """
        # Placeholder for Dead Duck protocol verification
        # In production, this would integrate with the actual Dead Duck system
        return False

    def _generate_token(self, user_id: str) -> str:
        """Generate secure session token.

        Args:
            user_id: User ID

        Returns:
            Session token
        """
        random_data = secrets.token_bytes(32)
        timestamp = str(time.time()).encode()
        user_data = user_id.encode()

        # Combine data
        data = random_data + timestamp + user_data

        # Create token
        token = base64.urlsafe_b64encode(data).decode()
        return token

    def verify_token(self, token: str) -> Optional[User]:
        """Verify session token.

        Args:
            token: Session token

        Returns:
            User object if valid, None otherwise
        """
        if token not in self.sessions:
            return None

        user = self.sessions[token]

        # Check expiry
        if user.token_expiry:
            expiry = datetime.fromisoformat(user.token_expiry)
            if datetime.now() > expiry:
                # Token expired
                del self.sessions[token]
                self._log_security_event(
                    user_id=user.user_id,
                    action='token_expired',
                    resource='session',
                    result='denied'
                )
                return None

        return user

    def logout(self, token: str) -> bool:
        """Logout user.

        Args:
            token: Session token

        Returns:
            True if successful, False otherwise
        """
        if token in self.sessions:
            user = self.sessions[token]
            del self.sessions[token]

            self._log_security_event(
                user_id=user.user_id,
                action='logout',
                resource='session',
                result='success'
            )
            return True
        return False

    # Authorization
    def check_permission(self, user: User, permission: str) -> bool:
        """Check if user has permission.

        Args:
            user: User object
            permission: Permission to check

        Returns:
            True if user has permission, False otherwise
        """
        has_permission = permission in user.permissions

        self._log_security_event(
            user_id=user.user_id,
            action='check_permission',
            resource=permission,
            result='success' if has_permission else 'denied'
        )

        return has_permission

    def authorize_action(self, token: str, action: str) -> tuple[bool, Optional[User]]:
        """Authorize an action.

        Args:
            token: Session token
            action: Action to authorize

        Returns:
            Tuple of (authorized, user)
        """
        user = self.verify_token(token)
        if not user:
            self._log_security_event(
                user_id='unknown',
                action=action,
                resource='unknown',
                result='denied',
                details={'reason': 'invalid_token'}
            )
            return False, None

        authorized = self.check_permission(user, action)
        return authorized, user

    # Contract Verification
    def verify_contract(self, contract_data: Dict[str, Any]) -> tuple[bool, Optional[Contract]]:
        """Verify contract is signed and authorized.

        Args:
            contract_data: Contract data

        Returns:
            Tuple of (verified, Contract object)
        """
        # Check for required fields
        required_fields = ['contract_id', 'authorized_by', 'signature']
        for field in required_fields:
            if field not in contract_data:
                return False, None

        # Verify signature
        contract_id = contract_data['contract_id']
        authorized_by = contract_data['authorized_by']
        provided_signature = contract_data['signature']

        # Compute expected signature
        signature_data = f"{contract_id}:{authorized_by}".encode()
        expected_signature = hashlib.sha256(signature_data).hexdigest()

        # In production, use proper digital signatures
        is_valid = provided_signature == expected_signature

        contract = Contract(
            contract_id=contract_id,
            signed=is_valid,
            authorized_by=authorized_by,
            signature=provided_signature,
            timestamp=datetime.now().isoformat()
        )

        self._log_security_event(
            user_id=authorized_by,
            action='verify_contract',
            resource=contract_id,
            result='success' if is_valid else 'failed'
        )

        return is_valid, contract

    def sign_contract(self, contract_id: str, user_id: str) -> str:
        """Sign a contract.

        Args:
            contract_id: Contract ID
            user_id: User ID

        Returns:
            Signature string
        """
        signature_data = f"{contract_id}:{user_id}".encode()
        signature = hashlib.sha256(signature_data).hexdigest()

        self._log_security_event(
            user_id=user_id,
            action='sign_contract',
            resource=contract_id,
            result='success'
        )

        return signature

    # Encryption
    def encrypt_data(self, data: Any) -> str:
        """Encrypt sensitive data.

        Args:
            data: Data to encrypt (will be JSON serialized)

        Returns:
            Encrypted data as base64 string
        """
        try:
            # Serialize to JSON
            json_data = json.dumps(data)
            encrypted = self.cipher.encrypt(json_data.encode())
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            raise Exception(f"Encryption failed: {str(e)}")

    def decrypt_data(self, encrypted_data: str) -> Any:
        """Decrypt sensitive data.

        Args:
            encrypted_data: Encrypted data as base64 string

        Returns:
            Decrypted data
        """
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted = self.cipher.decrypt(encrypted_bytes)
            return json.loads(decrypted.decode())
        except Exception as e:
            raise Exception(f"Decryption failed: {str(e)}")

    def encrypt_targets(self, targets: List[str]) -> str:
        """Encrypt target list.

        Args:
            targets: List of targets

        Returns:
            Encrypted targets
        """
        return self.encrypt_data(targets)

    def decrypt_targets(self, encrypted_targets: str) -> List[str]:
        """Decrypt target list.

        Args:
            encrypted_targets: Encrypted targets

        Returns:
            List of targets
        """
        return self.decrypt_data(encrypted_targets)

    def encrypt_findings(self, findings: List[Dict[str, Any]]) -> str:
        """Encrypt findings.

        Args:
            findings: List of findings

        Returns:
            Encrypted findings
        """
        return self.encrypt_data(findings)

    def decrypt_findings(self, encrypted_findings: str) -> List[Dict[str, Any]]:
        """Decrypt findings.

        Args:
            encrypted_findings: Encrypted findings

        Returns:
            List of findings
        """
        return self.decrypt_data(encrypted_findings)

    # Compliance Logging
    def _log_security_event(self, user_id: str, action: str, resource: str,
                           result: str, details: Optional[Dict[str, Any]] = None):
        """Log security event for compliance.

        Args:
            user_id: User ID
            action: Action performed
            resource: Resource accessed
            result: Result of action
            details: Optional additional details
        """
        event = SecurityEvent(
            event_id=secrets.token_hex(16),
            user_id=user_id,
            action=action,
            resource=resource,
            result=result,
            timestamp=datetime.now().isoformat(),
            details=details
        )

        self.security_log.append(event)

        # In production, also write to secure audit log file
        self._write_audit_log(event)

    def _write_audit_log(self, event: SecurityEvent):
        """Write event to audit log file.

        Args:
            event: Security event to log
        """
        audit_file = Path.home() / ".ghostops" / "audit.log"
        audit_file.parent.mkdir(exist_ok=True)

        log_entry = {
            'event_id': event.event_id,
            'user_id': event.user_id,
            'action': event.action,
            'resource': event.resource,
            'result': event.result,
            'timestamp': event.timestamp,
            'details': event.details
        }

        with open(audit_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')

    def get_security_log(self, user_id: Optional[str] = None,
                        action: Optional[str] = None,
                        limit: int = 100) -> List[SecurityEvent]:
        """Get security log entries.

        Args:
            user_id: Optional user filter
            action: Optional action filter
            limit: Maximum number of entries

        Returns:
            List of security events
        """
        filtered = self.security_log

        if user_id:
            filtered = [e for e in filtered if e.user_id == user_id]

        if action:
            filtered = [e for e in filtered if e.action == action]

        return filtered[-limit:]

    # Tool Execution Authorization
    def authorize_tool_execution(self, user: User, tool_name: str) -> bool:
        """Authorize tool execution.

        Args:
            user: User object
            tool_name: Tool to execute

        Returns:
            True if authorized, False otherwise
        """
        # Check if user has start_engagement permission
        authorized = self.check_permission(user, 'start_engagement')

        self._log_security_event(
            user_id=user.user_id,
            action='execute_tool',
            resource=tool_name,
            result='success' if authorized else 'denied'
        )

        return authorized

    # Security Statistics
    def get_security_stats(self) -> Dict[str, Any]:
        """Get security statistics.

        Returns:
            Dictionary with security statistics
        """
        total_events = len(self.security_log)
        by_action = {}
        by_result = {}
        failed_logins = 0

        for event in self.security_log:
            # Count by action
            by_action[event.action] = by_action.get(event.action, 0) + 1

            # Count by result
            by_result[event.result] = by_result.get(event.result, 0) + 1

            # Count failed logins
            if event.action in ['authenticate', 'authenticate_dd'] and event.result == 'failed':
                failed_logins += 1

        return {
            'total_events': total_events,
            'active_sessions': len(self.sessions),
            'by_action': by_action,
            'by_result': by_result,
            'failed_logins': failed_logins,
            'recent_events': [
                {
                    'user_id': e.user_id,
                    'action': e.action,
                    'result': e.result,
                    'timestamp': e.timestamp
                }
                for e in self.security_log[-10:]
            ]
        }


# Global security layer instance
_security_layer: Optional[SecurityLayer] = None


def get_security_layer() -> SecurityLayer:
    """Get global security layer instance.

    Returns:
        SecurityLayer instance
    """
    global _security_layer
    if _security_layer is None:
        _security_layer = SecurityLayer()
    return _security_layer
