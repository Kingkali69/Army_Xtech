#!/usr/bin/env python3
"""
Parameter Sanitizer - Input validation for security tools
Validates all parameters before they're used in subprocess calls
"""

import re
import os
from typing import Any, Optional, List, Union
from pathlib import Path


class ValidationError(Exception):
    """Raised when parameter validation fails"""
    pass


class ParameterSanitizer:
    """Validates and sanitizes parameters for security tools"""

    # Regular expressions for validation
    IP_PATTERN = re.compile(r'^(\d{1,3}\.){3}\d{1,3}$')
    IPV6_PATTERN = re.compile(r'^([0-9a-fA-F]{0,4}:){7}[0-9a-fA-F]{0,4}$')
    HOSTNAME_PATTERN = re.compile(r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$')
    PORT_PATTERN = re.compile(r'^\d{1,5}$')
    DOMAIN_PATTERN = re.compile(r'^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$')
    URL_PATTERN = re.compile(r'^https?://[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*(/.*)?$')

    # Dangerous characters and sequences
    DANGEROUS_CHARS = ['|', ';', '&', '$', '`', '\n', '\r', '>', '<', '(', ')', '{', '}', '!']
    DANGEROUS_SEQUENCES = ['../', '/../', '${', '$(', '&&', '||', ';', '|&']

    @staticmethod
    def validate_ip(ip: str) -> str:
        """
        Validate IP address (IPv4 or IPv6)
        Returns: validated IP string
        Raises: ValidationError if invalid
        """
        if not isinstance(ip, str):
            raise ValidationError(f"IP must be a string, got {type(ip).__name__}")

        ip = ip.strip()

        # Check for dangerous characters
        if any(char in ip for char in ParameterSanitizer.DANGEROUS_CHARS):
            raise ValidationError(f"IP contains dangerous characters: {ip}")

        # Validate IPv4
        if ParameterSanitizer.IP_PATTERN.match(ip):
            octets = ip.split('.')
            for octet in octets:
                if int(octet) > 255:
                    raise ValidationError(f"Invalid IP address: {ip} (octet > 255)")
            return ip

        # Validate IPv6
        if ParameterSanitizer.IPV6_PATTERN.match(ip):
            return ip

        raise ValidationError(f"Invalid IP address format: {ip}")

    @staticmethod
    def validate_hostname(hostname: str) -> str:
        """
        Validate hostname
        Returns: validated hostname
        Raises: ValidationError if invalid
        """
        if not isinstance(hostname, str):
            raise ValidationError(f"Hostname must be a string, got {type(hostname).__name__}")

        hostname = hostname.strip()

        # Check for dangerous characters
        if any(char in hostname for char in ParameterSanitizer.DANGEROUS_CHARS):
            raise ValidationError(f"Hostname contains dangerous characters: {hostname}")

        # Check for dangerous sequences
        if any(seq in hostname for seq in ParameterSanitizer.DANGEROUS_SEQUENCES):
            raise ValidationError(f"Hostname contains dangerous sequences: {hostname}")

        # Validate format
        if not ParameterSanitizer.HOSTNAME_PATTERN.match(hostname):
            raise ValidationError(f"Invalid hostname format: {hostname}")

        return hostname

    @staticmethod
    def validate_port(port: Union[int, str]) -> int:
        """
        Validate port number (1-65535)
        Returns: validated port as integer
        Raises: ValidationError if invalid
        """
        if isinstance(port, str):
            if not ParameterSanitizer.PORT_PATTERN.match(port):
                raise ValidationError(f"Invalid port format: {port}")
            port = int(port)

        if not isinstance(port, int):
            raise ValidationError(f"Port must be int or string, got {type(port).__name__}")

        if port < 1 or port > 65535:
            raise ValidationError(f"Port out of range (1-65535): {port}")

        return port

    @staticmethod
    def validate_port_range(ports: str) -> str:
        """
        Validate port range (e.g., "80,443,8000-9000")
        Returns: validated port range string
        Raises: ValidationError if invalid
        """
        if not isinstance(ports, str):
            raise ValidationError(f"Port range must be a string, got {type(ports).__name__}")

        ports = ports.strip()

        # Check for dangerous characters
        if any(char in ports for char in ParameterSanitizer.DANGEROUS_CHARS):
            raise ValidationError(f"Port range contains dangerous characters: {ports}")

        # Validate format: only digits, commas, and hyphens
        if not re.match(r'^[\d,\-]+$', ports):
            raise ValidationError(f"Invalid port range format: {ports}")

        # Validate individual ports and ranges
        for part in ports.split(','):
            part = part.strip()
            if '-' in part:
                start, end = part.split('-', 1)
                ParameterSanitizer.validate_port(start)
                ParameterSanitizer.validate_port(end)
            else:
                ParameterSanitizer.validate_port(part)

        return ports

    @staticmethod
    def validate_url(url: str) -> str:
        """
        Validate URL
        Returns: validated URL
        Raises: ValidationError if invalid
        """
        if not isinstance(url, str):
            raise ValidationError(f"URL must be a string, got {type(url).__name__}")

        url = url.strip()

        # Check for dangerous characters
        dangerous_url_chars = ['|', ';', '&', '$', '`', '\n', '\r', '<', '>', '{', '}']
        if any(char in url for char in dangerous_url_chars):
            raise ValidationError(f"URL contains dangerous characters: {url}")

        # Validate format
        if not ParameterSanitizer.URL_PATTERN.match(url):
            raise ValidationError(f"Invalid URL format: {url}")

        return url

    @staticmethod
    def validate_file_path(path: str, must_exist: bool = False, no_traversal: bool = True) -> str:
        """
        Validate file path
        Returns: validated absolute path
        Raises: ValidationError if invalid
        """
        if not isinstance(path, str):
            raise ValidationError(f"Path must be a string, got {type(path).__name__}")

        path = path.strip()

        # Check for dangerous characters
        if any(char in path for char in ['|', ';', '&', '$', '`', '\n', '\r']):
            raise ValidationError(f"Path contains dangerous characters: {path}")

        # Check for path traversal
        if no_traversal:
            if any(seq in path for seq in ['../', '/../', '..\\', '\\..\\', '..']):
                raise ValidationError(f"Path contains traversal sequences: {path}")

        # Convert to absolute path
        try:
            abs_path = os.path.abspath(path)
        except Exception as e:
            raise ValidationError(f"Invalid path: {path} ({e})")

        # Check if file exists (if required)
        if must_exist and not os.path.exists(abs_path):
            raise ValidationError(f"Path does not exist: {abs_path}")

        return abs_path

    @staticmethod
    def validate_username(username: str) -> str:
        """
        Validate username (alphanumeric, underscore, hyphen only)
        Returns: validated username
        Raises: ValidationError if invalid
        """
        if not isinstance(username, str):
            raise ValidationError(f"Username must be a string, got {type(username).__name__}")

        username = username.strip()

        # Validate format: alphanumeric, underscore, hyphen only
        if not re.match(r'^[a-zA-Z0-9_\-]+$', username):
            raise ValidationError(f"Invalid username format: {username}")

        if len(username) < 1 or len(username) > 64:
            raise ValidationError(f"Username length must be 1-64 characters: {username}")

        return username

    @staticmethod
    def validate_hash(hash_value: str, hash_type: str = None) -> str:
        """
        Validate hash value
        Returns: validated hash
        Raises: ValidationError if invalid
        """
        if not isinstance(hash_value, str):
            raise ValidationError(f"Hash must be a string, got {type(hash_value).__name__}")

        hash_value = hash_value.strip()

        # Check for dangerous characters
        if not re.match(r'^[a-fA-F0-9]+$', hash_value):
            raise ValidationError(f"Hash contains invalid characters: {hash_value}")

        # Validate length based on hash type
        valid_lengths = {
            'md5': 32,
            'sha1': 40,
            'sha256': 64,
            'sha512': 128
        }

        if hash_type:
            expected_len = valid_lengths.get(hash_type.lower())
            if expected_len and len(hash_value) != expected_len:
                raise ValidationError(f"Invalid {hash_type} hash length: {len(hash_value)} (expected {expected_len})")

        return hash_value

    @staticmethod
    def validate_string_safe(value: str, max_length: int = 1024) -> str:
        """
        Validate generic string for safety (no command injection characters)
        Returns: validated string
        Raises: ValidationError if invalid
        """
        if not isinstance(value, str):
            raise ValidationError(f"Value must be a string, got {type(value).__name__}")

        # Check for dangerous characters
        if any(char in value for char in ParameterSanitizer.DANGEROUS_CHARS):
            raise ValidationError(f"String contains dangerous characters: {value}")

        # Check for dangerous sequences
        if any(seq in value for seq in ParameterSanitizer.DANGEROUS_SEQUENCES):
            raise ValidationError(f"String contains dangerous sequences: {value}")

        # Check length
        if len(value) > max_length:
            raise ValidationError(f"String too long: {len(value)} (max {max_length})")

        return value

    @staticmethod
    def validate_integer(value: Union[int, str], min_val: int = None, max_val: int = None) -> int:
        """
        Validate integer value
        Returns: validated integer
        Raises: ValidationError if invalid
        """
        if isinstance(value, str):
            if not re.match(r'^-?\d+$', value):
                raise ValidationError(f"Invalid integer format: {value}")
            value = int(value)

        if not isinstance(value, int):
            raise ValidationError(f"Value must be int or string, got {type(value).__name__}")

        if min_val is not None and value < min_val:
            raise ValidationError(f"Integer too small: {value} (min {min_val})")

        if max_val is not None and value > max_val:
            raise ValidationError(f"Integer too large: {value} (max {max_val})")

        return value

    @staticmethod
    def validate_boolean(value: Union[bool, str, int]) -> bool:
        """
        Validate boolean value
        Returns: validated boolean
        Raises: ValidationError if invalid
        """
        if isinstance(value, bool):
            return value

        if isinstance(value, str):
            value = value.lower().strip()
            if value in ['true', '1', 'yes', 'on']:
                return True
            elif value in ['false', '0', 'no', 'off']:
                return False
            else:
                raise ValidationError(f"Invalid boolean string: {value}")

        if isinstance(value, int):
            if value == 0:
                return False
            elif value == 1:
                return True
            else:
                raise ValidationError(f"Invalid boolean integer: {value}")

        raise ValidationError(f"Value must be bool, string, or int, got {type(value).__name__}")
