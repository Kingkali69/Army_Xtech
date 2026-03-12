#!/usr/bin/env python3
"""
Security Audit Logger
Comprehensive logging of security-relevant events.
Logs authentication, file operations, tool executions, and errors.
"""

import os
import json
import time
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, List
from enum import Enum
from pathlib import Path


class EventType(Enum):
    """Security event types"""
    # Authentication events
    AUTH_SUCCESS = "auth_success"
    AUTH_FAILURE = "auth_failure"
    AUTH_LOGOUT = "auth_logout"
    TOKEN_CREATED = "token_created"
    TOKEN_EXPIRED = "token_expired"
    TOKEN_INVALID = "token_invalid"

    # Authorization events
    ACCESS_GRANTED = "access_granted"
    ACCESS_DENIED = "access_denied"

    # File operations
    FILE_READ = "file_read"
    FILE_WRITE = "file_write"
    FILE_DELETE = "file_delete"
    FILE_UPLOAD = "file_upload"
    FILE_DOWNLOAD = "file_download"
    FILE_SYNC = "file_sync"

    # Tool/Command execution
    TOOL_EXECUTION = "tool_execution"
    COMMAND_EXECUTION = "command_execution"
    PLUGIN_LOADED = "plugin_loaded"

    # API events
    API_REQUEST = "api_request"
    API_ERROR = "api_error"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"

    # Security events
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    VALIDATION_FAILED = "validation_failed"
    INJECTION_ATTEMPT = "injection_attempt"
    PATH_TRAVERSAL_ATTEMPT = "path_traversal_attempt"


class EventSeverity(Enum):
    """Event severity levels"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AuditLogger:
    """
    Comprehensive security audit logger
    - Logs all security events
    - Rotates logs daily
    - Keeps 30 days of history
    - Thread-safe logging
    """

    def __init__(
        self,
        log_directory: str = "/var/log/ghostops/security",
        retention_days: int = 30,
        enable_console: bool = True,
        enable_file: bool = True
    ):
        """
        Initialize audit logger

        Args:
            log_directory: Directory to store log files
            retention_days: Number of days to keep logs
            enable_console: Enable console logging
            enable_file: Enable file logging
        """
        self.log_directory = Path(log_directory)
        self.retention_days = retention_days
        self.enable_console = enable_console
        self.enable_file = enable_file

        # Create log directory
        if self.enable_file:
            self.log_directory.mkdir(parents=True, exist_ok=True)

        # Thread lock for safe logging
        self.lock = threading.Lock()

        # Configure Python logging
        self.logger = logging.getLogger('security_audit')
        self.logger.setLevel(logging.DEBUG)

        # Clear existing handlers
        self.logger.handlers = []

        # Console handler
        if self.enable_console:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_formatter = logging.Formatter(
                '%(asctime)s - SECURITY - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)

        # File handler (daily rotation)
        if self.enable_file:
            self._setup_file_handler()

        # Start cleanup thread
        self.cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self.cleanup_thread.start()

    def _setup_file_handler(self):
        """Setup file handler with daily rotation"""
        log_file = self.log_directory / f"security_{datetime.now().strftime('%Y%m%d')}.log"

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)

    def _get_current_log_file(self) -> Path:
        """Get current log file path"""
        return self.log_directory / f"security_{datetime.now().strftime('%Y%m%d')}.log"

    def log_event(
        self,
        event_type: EventType,
        severity: EventSeverity = EventSeverity.INFO,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        success: bool = True
    ):
        """
        Log a security event

        Args:
            event_type: Type of event
            severity: Event severity
            user_id: Optional user identifier
            ip_address: Optional IP address
            details: Optional additional details
            success: Whether the event was successful
        """
        with self.lock:
            # Build event data
            event = {
                'timestamp': datetime.now().isoformat(),
                'event_type': event_type.value,
                'severity': severity.value,
                'success': success,
            }

            if user_id:
                event['user_id'] = user_id

            if ip_address:
                event['ip_address'] = ip_address

            if details:
                event['details'] = details

            # Log to Python logger
            log_message = json.dumps(event)

            if severity == EventSeverity.CRITICAL:
                self.logger.critical(log_message)
            elif severity == EventSeverity.ERROR:
                self.logger.error(log_message)
            elif severity == EventSeverity.WARNING:
                self.logger.warning(log_message)
            elif severity == EventSeverity.INFO:
                self.logger.info(log_message)
            else:
                self.logger.debug(log_message)

    # Authentication logging
    def log_auth_success(self, user_id: str, ip_address: str, details: Optional[Dict] = None):
        """Log successful authentication"""
        self.log_event(
            EventType.AUTH_SUCCESS,
            EventSeverity.INFO,
            user_id=user_id,
            ip_address=ip_address,
            details=details,
            success=True
        )

    def log_auth_failure(self, user_id: Optional[str], ip_address: str, reason: str):
        """Log failed authentication"""
        self.log_event(
            EventType.AUTH_FAILURE,
            EventSeverity.WARNING,
            user_id=user_id,
            ip_address=ip_address,
            details={'reason': reason},
            success=False
        )

    def log_logout(self, user_id: str, ip_address: str):
        """Log logout"""
        self.log_event(
            EventType.AUTH_LOGOUT,
            EventSeverity.INFO,
            user_id=user_id,
            ip_address=ip_address,
            success=True
        )

    # File operation logging
    def log_file_read(self, user_id: str, file_path: str, ip_address: str, success: bool = True):
        """Log file read operation"""
        self.log_event(
            EventType.FILE_READ,
            EventSeverity.INFO,
            user_id=user_id,
            ip_address=ip_address,
            details={'file_path': file_path},
            success=success
        )

    def log_file_write(self, user_id: str, file_path: str, ip_address: str, size: Optional[int] = None, success: bool = True):
        """Log file write operation"""
        details = {'file_path': file_path}
        if size:
            details['size_bytes'] = size

        self.log_event(
            EventType.FILE_WRITE,
            EventSeverity.INFO,
            user_id=user_id,
            ip_address=ip_address,
            details=details,
            success=success
        )

    def log_file_delete(self, user_id: str, file_path: str, ip_address: str, success: bool = True):
        """Log file delete operation"""
        self.log_event(
            EventType.FILE_DELETE,
            EventSeverity.WARNING,
            user_id=user_id,
            ip_address=ip_address,
            details={'file_path': file_path},
            success=success
        )

    def log_file_sync(self, user_id: str, ip_address: str, file_count: int, success: bool = True):
        """Log file sync operation"""
        self.log_event(
            EventType.FILE_SYNC,
            EventSeverity.INFO,
            user_id=user_id,
            ip_address=ip_address,
            details={'file_count': file_count},
            success=success
        )

    # Tool execution logging
    def log_tool_execution(
        self,
        user_id: str,
        tool_name: str,
        ip_address: str,
        arguments: Optional[Dict] = None,
        success: bool = True
    ):
        """Log tool execution"""
        details = {'tool_name': tool_name}
        if arguments:
            details['arguments'] = arguments

        self.log_event(
            EventType.TOOL_EXECUTION,
            EventSeverity.INFO,
            user_id=user_id,
            ip_address=ip_address,
            details=details,
            success=success
        )

    def log_command_execution(
        self,
        user_id: str,
        command: str,
        ip_address: str,
        success: bool = True
    ):
        """Log command execution"""
        self.log_event(
            EventType.COMMAND_EXECUTION,
            EventSeverity.WARNING,
            user_id=user_id,
            ip_address=ip_address,
            details={'command': command},
            success=success
        )

    # API logging
    def log_api_request(
        self,
        endpoint: str,
        method: str,
        ip_address: str,
        user_id: Optional[str] = None,
        status_code: int = 200,
        response_time_ms: Optional[float] = None
    ):
        """Log API request"""
        details = {
            'endpoint': endpoint,
            'method': method,
            'status_code': status_code,
        }

        if response_time_ms:
            details['response_time_ms'] = response_time_ms

        severity = EventSeverity.INFO
        if status_code >= 500:
            severity = EventSeverity.ERROR
        elif status_code >= 400:
            severity = EventSeverity.WARNING

        self.log_event(
            EventType.API_REQUEST,
            severity,
            user_id=user_id,
            ip_address=ip_address,
            details=details,
            success=(status_code < 400)
        )

    def log_api_error(
        self,
        endpoint: str,
        method: str,
        ip_address: str,
        error: str,
        user_id: Optional[str] = None
    ):
        """Log API error"""
        self.log_event(
            EventType.API_ERROR,
            EventSeverity.ERROR,
            user_id=user_id,
            ip_address=ip_address,
            details={
                'endpoint': endpoint,
                'method': method,
                'error': error,
            },
            success=False
        )

    def log_rate_limit_exceeded(
        self,
        ip_address: str,
        limit_type: str,
        user_id: Optional[str] = None
    ):
        """Log rate limit exceeded"""
        self.log_event(
            EventType.RATE_LIMIT_EXCEEDED,
            EventSeverity.WARNING,
            user_id=user_id,
            ip_address=ip_address,
            details={'limit_type': limit_type},
            success=False
        )

    # Security event logging
    def log_suspicious_activity(
        self,
        activity_type: str,
        ip_address: str,
        details: Dict[str, Any],
        user_id: Optional[str] = None
    ):
        """Log suspicious activity"""
        details['activity_type'] = activity_type

        self.log_event(
            EventType.SUSPICIOUS_ACTIVITY,
            EventSeverity.CRITICAL,
            user_id=user_id,
            ip_address=ip_address,
            details=details,
            success=False
        )

    def log_validation_failed(
        self,
        validation_type: str,
        ip_address: str,
        reason: str,
        user_id: Optional[str] = None
    ):
        """Log validation failure"""
        self.log_event(
            EventType.VALIDATION_FAILED,
            EventSeverity.WARNING,
            user_id=user_id,
            ip_address=ip_address,
            details={
                'validation_type': validation_type,
                'reason': reason,
            },
            success=False
        )

    def log_injection_attempt(
        self,
        injection_type: str,
        ip_address: str,
        payload: str,
        user_id: Optional[str] = None
    ):
        """Log injection attempt"""
        self.log_event(
            EventType.INJECTION_ATTEMPT,
            EventSeverity.CRITICAL,
            user_id=user_id,
            ip_address=ip_address,
            details={
                'injection_type': injection_type,
                'payload': payload[:500],  # Limit payload length
            },
            success=False
        )

    def log_path_traversal_attempt(
        self,
        ip_address: str,
        attempted_path: str,
        user_id: Optional[str] = None
    ):
        """Log path traversal attempt"""
        self.log_event(
            EventType.PATH_TRAVERSAL_ATTEMPT,
            EventSeverity.CRITICAL,
            user_id=user_id,
            ip_address=ip_address,
            details={'attempted_path': attempted_path},
            success=False
        )

    # Log rotation and cleanup
    def _cleanup_loop(self):
        """Background thread for log cleanup"""
        while True:
            # Run cleanup once per day
            time.sleep(86400)  # 24 hours
            self._cleanup_old_logs()

    def _cleanup_old_logs(self):
        """Remove logs older than retention period"""
        if not self.enable_file:
            return

        with self.lock:
            cutoff_date = datetime.now() - timedelta(days=self.retention_days)

            # Find and remove old log files
            for log_file in self.log_directory.glob("security_*.log"):
                try:
                    # Extract date from filename
                    date_str = log_file.stem.split('_')[1]
                    file_date = datetime.strptime(date_str, '%Y%m%d')

                    # Delete if older than retention period
                    if file_date < cutoff_date:
                        log_file.unlink()
                        self.logger.info(f"Deleted old log file: {log_file}")
                except (ValueError, IndexError) as e:
                    self.logger.warning(f"Could not parse log file date: {log_file}")

    def get_recent_events(
        self,
        event_type: Optional[EventType] = None,
        user_id: Optional[str] = None,
        hours: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Get recent security events

        Args:
            event_type: Filter by event type
            user_id: Filter by user ID
            hours: Number of hours to look back

        Returns:
            List of matching events
        """
        events = []
        cutoff_time = datetime.now() - timedelta(hours=hours)

        # Read today's log file
        log_file = self._get_current_log_file()
        if not log_file.exists():
            return events

        try:
            with open(log_file, 'r') as f:
                for line in f:
                    try:
                        # Parse log line - extract JSON after the log prefix
                        if '{' in line:
                            json_start = line.index('{')
                            event_data = json.loads(line[json_start:])

                            # Parse timestamp
                            event_time = datetime.fromisoformat(event_data['timestamp'])

                            # Filter by time
                            if event_time < cutoff_time:
                                continue

                            # Filter by event type
                            if event_type and event_data.get('event_type') != event_type.value:
                                continue

                            # Filter by user
                            if user_id and event_data.get('user_id') != user_id:
                                continue

                            events.append(event_data)
                    except (json.JSONDecodeError, ValueError):
                        continue
        except IOError as e:
            self.logger.error(f"Error reading log file: {e}")

        return events


# Singleton instance
audit_logger = AuditLogger()


# Convenience functions
def log_auth_success(user_id: str, ip_address: str):
    """Log successful authentication"""
    audit_logger.log_auth_success(user_id, ip_address)


def log_auth_failure(user_id: Optional[str], ip_address: str, reason: str):
    """Log failed authentication"""
    audit_logger.log_auth_failure(user_id, ip_address, reason)


def log_file_operation(operation: str, user_id: str, file_path: str, ip_address: str):
    """Log file operation"""
    if operation == 'read':
        audit_logger.log_file_read(user_id, file_path, ip_address)
    elif operation == 'write':
        audit_logger.log_file_write(user_id, file_path, ip_address)
    elif operation == 'delete':
        audit_logger.log_file_delete(user_id, file_path, ip_address)


def log_tool_execution(user_id: str, tool_name: str, ip_address: str):
    """Log tool execution"""
    audit_logger.log_tool_execution(user_id, tool_name, ip_address)


def log_api_request(endpoint: str, method: str, ip_address: str, status_code: int):
    """Log API request"""
    audit_logger.log_api_request(endpoint, method, ip_address, status_code=status_code)


def log_security_event(event_type: str, ip_address: str, details: Dict[str, Any]):
    """Log generic security event"""
    audit_logger.log_suspicious_activity(event_type, ip_address, details)
