#!/usr/bin/env python3
"""
Input Validation Framework
Sanitizes and validates all user inputs to prevent injection attacks and malformed data.
"""

import json
import re
from typing import Dict, Any, Optional, List
from urllib.parse import parse_qs, unquote


class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass


class InputValidator:
    """
    Comprehensive input validation framework
    - Validates JSON schemas
    - Sanitizes query parameters
    - Sanitizes form inputs
    - Rejects oversized requests
    - Prevents injection attacks
    """

    # Size limits (bytes)
    MAX_JSON_SIZE = 1 * 1024 * 1024      # 1MB
    MAX_REQUEST_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_STRING_LENGTH = 10000
    MAX_ARRAY_LENGTH = 1000
    MAX_OBJECT_DEPTH = 10

    # Dangerous patterns (injection prevention)
    SQL_INJECTION_PATTERNS = [
        r"(\bSELECT\b|\bINSERT\b|\bUPDATE\b|\bDELETE\b|\bDROP\b|\bUNION\b|\bEXEC\b)",
        r"(--|;|\/\*|\*\/|xp_|sp_)",
        r"(\bOR\b\s+\d+\s*=\s*\d+|\bAND\b\s+\d+\s*=\s*\d+)",
    ]

    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe",
        r"<object",
        r"<embed",
    ]

    PATH_TRAVERSAL_PATTERNS = [
        r"\.\./",
        r"\.\.",
        r"%2e%2e",
        r"%252e%252e",
    ]

    COMMAND_INJECTION_PATTERNS = [
        r"[;&|`$()]",
        r"\$\{",
        r"\$\(",
        r">\s*/dev/",
    ]

    def __init__(self):
        """Initialize validator"""
        self.compiled_patterns = {
            'sql': [re.compile(p, re.IGNORECASE) for p in self.SQL_INJECTION_PATTERNS],
            'xss': [re.compile(p, re.IGNORECASE) for p in self.XSS_PATTERNS],
            'path': [re.compile(p, re.IGNORECASE) for p in self.PATH_TRAVERSAL_PATTERNS],
            'command': [re.compile(p) for p in self.COMMAND_INJECTION_PATTERNS],
        }

    def validate_request_size(self, content_length: int) -> None:
        """
        Validate request size doesn't exceed limits

        Args:
            content_length: Size of request in bytes

        Raises:
            ValidationError: If request exceeds size limits
        """
        if content_length > self.MAX_REQUEST_SIZE:
            raise ValidationError(
                f"Request size {content_length} exceeds maximum allowed {self.MAX_REQUEST_SIZE} bytes"
            )

    def validate_json(self, json_string: str) -> Dict[str, Any]:
        """
        Validate and parse JSON input

        Args:
            json_string: JSON string to validate

        Returns:
            Parsed JSON object

        Raises:
            ValidationError: If JSON is invalid or exceeds size limits
        """
        # Check size
        json_size = len(json_string.encode('utf-8'))
        if json_size > self.MAX_JSON_SIZE:
            raise ValidationError(
                f"JSON size {json_size} exceeds maximum allowed {self.MAX_JSON_SIZE} bytes"
            )

        # Parse JSON
        try:
            data = json.loads(json_string)
        except json.JSONDecodeError as e:
            raise ValidationError(f"Malformed JSON: {str(e)}")

        # Validate structure
        self._validate_json_structure(data, depth=0)

        return data

    def _validate_json_structure(self, obj: Any, depth: int = 0) -> None:
        """
        Recursively validate JSON structure

        Args:
            obj: Object to validate
            depth: Current recursion depth

        Raises:
            ValidationError: If structure is invalid
        """
        # Check depth
        if depth > self.MAX_OBJECT_DEPTH:
            raise ValidationError(f"JSON nesting depth exceeds maximum {self.MAX_OBJECT_DEPTH}")

        # Validate based on type
        if isinstance(obj, dict):
            if len(obj) > self.MAX_ARRAY_LENGTH:
                raise ValidationError(f"Object has too many keys (max {self.MAX_ARRAY_LENGTH})")
            for key, value in obj.items():
                if not isinstance(key, str):
                    raise ValidationError("Object keys must be strings")
                self._validate_json_structure(value, depth + 1)

        elif isinstance(obj, list):
            if len(obj) > self.MAX_ARRAY_LENGTH:
                raise ValidationError(f"Array length exceeds maximum {self.MAX_ARRAY_LENGTH}")
            for item in obj:
                self._validate_json_structure(item, depth + 1)

        elif isinstance(obj, str):
            if len(obj) > self.MAX_STRING_LENGTH:
                raise ValidationError(f"String length exceeds maximum {self.MAX_STRING_LENGTH}")

    def sanitize_string(self, value: str, allow_html: bool = False) -> str:
        """
        Sanitize string input

        Args:
            value: String to sanitize
            allow_html: Whether to allow HTML (default: False)

        Returns:
            Sanitized string

        Raises:
            ValidationError: If string contains dangerous patterns
        """
        if not isinstance(value, str):
            raise ValidationError("Value must be a string")

        # Check length
        if len(value) > self.MAX_STRING_LENGTH:
            raise ValidationError(f"String exceeds maximum length {self.MAX_STRING_LENGTH}")

        # Check for SQL injection
        for pattern in self.compiled_patterns['sql']:
            if pattern.search(value):
                raise ValidationError("Input contains potentially dangerous SQL patterns")

        # Check for XSS
        if not allow_html:
            for pattern in self.compiled_patterns['xss']:
                if pattern.search(value):
                    raise ValidationError("Input contains potentially dangerous script patterns")

        # Check for command injection
        for pattern in self.compiled_patterns['command']:
            if pattern.search(value):
                raise ValidationError("Input contains potentially dangerous command patterns")

        return value

    def sanitize_path(self, path: str) -> str:
        """
        Sanitize file path to prevent path traversal

        Args:
            path: File path to sanitize

        Returns:
            Sanitized path

        Raises:
            ValidationError: If path contains traversal patterns
        """
        if not isinstance(path, str):
            raise ValidationError("Path must be a string")

        # Decode URL encoding
        decoded_path = unquote(path)

        # Check for path traversal
        for pattern in self.compiled_patterns['path']:
            if pattern.search(decoded_path):
                raise ValidationError("Path contains potentially dangerous traversal patterns")

        # Additional checks
        if decoded_path.startswith('/'):
            raise ValidationError("Absolute paths are not allowed")

        if '\x00' in decoded_path:
            raise ValidationError("Null bytes in path are not allowed")

        return decoded_path

    def sanitize_query_params(self, query_string: str) -> Dict[str, str]:
        """
        Sanitize URL query parameters

        Args:
            query_string: Query string to sanitize

        Returns:
            Dictionary of sanitized parameters

        Raises:
            ValidationError: If parameters contain dangerous patterns
        """
        if not query_string:
            return {}

        # Parse query string
        parsed = parse_qs(query_string, keep_blank_values=True)

        # Sanitize each parameter
        sanitized = {}
        for key, values in parsed.items():
            # Take first value only
            value = values[0] if values else ""

            # Sanitize key and value
            clean_key = self.sanitize_string(key)
            clean_value = self.sanitize_string(value)

            sanitized[clean_key] = clean_value

        return sanitized

    def validate_email(self, email: str) -> str:
        """
        Validate email format

        Args:
            email: Email to validate

        Returns:
            Validated email

        Raises:
            ValidationError: If email format is invalid
        """
        email = self.sanitize_string(email)

        # Simple email regex
        email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

        if not email_pattern.match(email):
            raise ValidationError("Invalid email format")

        if len(email) > 254:  # RFC 5321
            raise ValidationError("Email address too long")

        return email.lower()

    def validate_username(self, username: str) -> str:
        """
        Validate username format

        Args:
            username: Username to validate

        Returns:
            Validated username

        Raises:
            ValidationError: If username format is invalid
        """
        username = self.sanitize_string(username)

        # Alphanumeric, underscore, hyphen only
        username_pattern = re.compile(r'^[a-zA-Z0-9_-]{3,32}$')

        if not username_pattern.match(username):
            raise ValidationError(
                "Username must be 3-32 characters and contain only letters, numbers, underscores, and hyphens"
            )

        return username

    def validate_ip_address(self, ip: str) -> str:
        """
        Validate IP address format

        Args:
            ip: IP address to validate

        Returns:
            Validated IP address

        Raises:
            ValidationError: If IP format is invalid
        """
        # IPv4 pattern
        ipv4_pattern = re.compile(
            r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}'
            r'(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
        )

        # IPv6 pattern (simplified)
        ipv6_pattern = re.compile(
            r'^(([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}|'
            r'([0-9a-fA-F]{1,4}:){1,7}:|'
            r'([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4})$'
        )

        if not (ipv4_pattern.match(ip) or ipv6_pattern.match(ip)):
            raise ValidationError("Invalid IP address format")

        return ip

    def validate_port(self, port: int) -> int:
        """
        Validate port number

        Args:
            port: Port number to validate

        Returns:
            Validated port number

        Raises:
            ValidationError: If port is invalid
        """
        if not isinstance(port, int):
            try:
                port = int(port)
            except (ValueError, TypeError):
                raise ValidationError("Port must be an integer")

        if port < 1 or port > 65535:
            raise ValidationError("Port must be between 1 and 65535")

        return port

    def validate_schema(self, data: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate data against a schema

        Args:
            data: Data to validate
            schema: Schema definition with expected fields and types

        Returns:
            Validated data

        Raises:
            ValidationError: If data doesn't match schema
        """
        if not isinstance(data, dict):
            raise ValidationError("Data must be a dictionary")

        validated = {}

        for field, field_def in schema.items():
            required = field_def.get('required', False)
            field_type = field_def.get('type')
            validator = field_def.get('validator')

            # Check if field exists
            if field not in data:
                if required:
                    raise ValidationError(f"Required field '{field}' is missing")
                continue

            value = data[field]

            # Check type
            if field_type and not isinstance(value, field_type):
                raise ValidationError(
                    f"Field '{field}' must be of type {field_type.__name__}"
                )

            # Apply validator function
            if validator and callable(validator):
                try:
                    value = validator(value)
                except Exception as e:
                    raise ValidationError(f"Validation failed for field '{field}': {str(e)}")

            validated[field] = value

        return validated


# Singleton instance
validator = InputValidator()


# Convenience functions
def validate_json(json_string: str) -> Dict[str, Any]:
    """Validate JSON input"""
    return validator.validate_json(json_string)


def sanitize_string(value: str, allow_html: bool = False) -> str:
    """Sanitize string input"""
    return validator.sanitize_string(value, allow_html)


def sanitize_path(path: str) -> str:
    """Sanitize file path"""
    return validator.sanitize_path(path)


def sanitize_query_params(query_string: str) -> Dict[str, str]:
    """Sanitize query parameters"""
    return validator.sanitize_query_params(query_string)


def validate_request_size(content_length: int) -> None:
    """Validate request size"""
    return validator.validate_request_size(content_length)
