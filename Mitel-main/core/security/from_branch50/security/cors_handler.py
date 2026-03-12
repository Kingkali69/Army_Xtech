#!/usr/bin/env python3
"""
CORS Handler Framework
Implements proper Cross-Origin Resource Sharing (CORS) with whitelisting.
Replaces dangerous wildcard (*) CORS with strict origin validation.
"""

from typing import List, Optional, Set, Dict
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse


class CORSConfig:
    """CORS configuration"""

    def __init__(
        self,
        allowed_origins: Optional[List[str]] = None,
        allowed_methods: Optional[List[str]] = None,
        allowed_headers: Optional[List[str]] = None,
        exposed_headers: Optional[List[str]] = None,
        max_age: int = 3600,
        allow_credentials: bool = False,
        require_csrf_token: bool = True
    ):
        """
        Initialize CORS configuration

        Args:
            allowed_origins: List of allowed origins (None = same origin only)
            allowed_methods: List of allowed HTTP methods
            allowed_headers: List of allowed request headers
            exposed_headers: List of headers exposed to client
            max_age: Preflight cache duration in seconds
            allow_credentials: Allow credentials (cookies, auth headers)
            require_csrf_token: Require CSRF token for state-changing operations
        """
        # Allowed origins - NEVER use '*' in production
        self.allowed_origins: Set[str] = set(allowed_origins or [])

        # Allowed methods
        self.allowed_methods: Set[str] = set(allowed_methods or [
            'GET', 'POST', 'OPTIONS'
        ])

        # Allowed headers
        self.allowed_headers: Set[str] = set(allowed_headers or [
            'Content-Type',
            'Authorization',
            'X-Requested-With',
            'X-CSRF-Token'
        ])

        # Exposed headers
        self.exposed_headers: Set[str] = set(exposed_headers or [
            'Content-Type',
            'Content-Length'
        ])

        self.max_age = max_age
        self.allow_credentials = allow_credentials
        self.require_csrf_token = require_csrf_token

        # State-changing methods that require CSRF protection
        self.state_changing_methods = {'POST', 'PUT', 'PATCH', 'DELETE'}

    def add_allowed_origin(self, origin: str):
        """Add an allowed origin"""
        self.allowed_origins.add(origin)

    def remove_allowed_origin(self, origin: str):
        """Remove an allowed origin"""
        self.allowed_origins.discard(origin)

    def is_origin_allowed(self, origin: str) -> bool:
        """
        Check if origin is allowed

        Args:
            origin: Origin to check

        Returns:
            True if origin is allowed
        """
        if not origin:
            return False

        # If no origins configured, only allow same-origin
        if not self.allowed_origins:
            return False

        # Check exact match
        if origin in self.allowed_origins:
            return True

        # Check wildcard subdomains (e.g., *.example.com)
        for allowed in self.allowed_origins:
            if allowed.startswith('*.'):
                domain = allowed[2:]
                parsed = urlparse(origin)
                if parsed.netloc.endswith('.' + domain) or parsed.netloc == domain:
                    return True

        return False


class CORSHandler:
    """
    CORS handler with security best practices
    - Whitelists specific origins (NO wildcards)
    - Validates origin on every request
    - Handles preflight requests
    - Enforces CSRF tokens for state-changing operations
    """

    def __init__(self, config: Optional[CORSConfig] = None):
        """
        Initialize CORS handler

        Args:
            config: CORS configuration (None = restrictive defaults)
        """
        self.config = config or CORSConfig()

    def is_preflight_request(self, handler: BaseHTTPRequestHandler) -> bool:
        """
        Check if request is a CORS preflight request

        Args:
            handler: HTTP request handler

        Returns:
            True if this is a preflight request
        """
        return (
            handler.command == 'OPTIONS' and
            'Origin' in handler.headers and
            'Access-Control-Request-Method' in handler.headers
        )

    def is_cors_request(self, handler: BaseHTTPRequestHandler) -> bool:
        """
        Check if request is a CORS request

        Args:
            handler: HTTP request handler

        Returns:
            True if this is a CORS request
        """
        return 'Origin' in handler.headers

    def validate_origin(self, handler: BaseHTTPRequestHandler) -> Optional[str]:
        """
        Validate request origin

        Args:
            handler: HTTP request handler

        Returns:
            Validated origin if allowed, None otherwise
        """
        origin = handler.headers.get('Origin')

        if not origin:
            # No origin header = same-origin request
            return None

        # Check if origin is allowed
        if self.config.is_origin_allowed(origin):
            return origin

        return None

    def validate_csrf_token(self, handler: BaseHTTPRequestHandler) -> bool:
        """
        Validate CSRF token for state-changing requests

        Args:
            handler: HTTP request handler

        Returns:
            True if CSRF token is valid or not required
        """
        # Only check for state-changing methods
        if handler.command not in self.config.state_changing_methods:
            return True

        # If CSRF not required, allow
        if not self.config.require_csrf_token:
            return True

        # Check for CSRF token
        csrf_token = handler.headers.get('X-CSRF-Token')
        if not csrf_token:
            return False

        # TODO: Validate token against session/stored token
        # For now, just check presence
        # In production, implement proper token validation
        return len(csrf_token) > 0

    def handle_preflight_request(self, handler: BaseHTTPRequestHandler) -> bool:
        """
        Handle CORS preflight (OPTIONS) request

        Args:
            handler: HTTP request handler

        Returns:
            True if preflight was handled successfully
        """
        # Validate origin
        origin = self.validate_origin(handler)
        if not origin:
            handler.send_response(403)
            handler.send_header('Content-Type', 'application/json')
            handler.end_headers()
            handler.wfile.write(b'{"error": "Origin not allowed"}')
            return False

        # Get requested method
        requested_method = handler.headers.get('Access-Control-Request-Method')
        if not requested_method or requested_method not in self.config.allowed_methods:
            handler.send_response(403)
            handler.send_header('Content-Type', 'application/json')
            handler.end_headers()
            handler.wfile.write(b'{"error": "Method not allowed"}')
            return False

        # Get requested headers
        requested_headers = handler.headers.get('Access-Control-Request-Headers', '')
        requested_headers_set = set(h.strip() for h in requested_headers.split(',') if h.strip())

        # Check if all requested headers are allowed
        if not requested_headers_set.issubset(self.config.allowed_headers):
            handler.send_response(403)
            handler.send_header('Content-Type', 'application/json')
            handler.end_headers()
            handler.wfile.write(b'{"error": "Headers not allowed"}')
            return False

        # Send preflight response
        handler.send_response(204)
        handler.send_header('Access-Control-Allow-Origin', origin)
        handler.send_header('Access-Control-Allow-Methods', ', '.join(self.config.allowed_methods))
        handler.send_header('Access-Control-Allow-Headers', ', '.join(self.config.allowed_headers))
        handler.send_header('Access-Control-Max-Age', str(self.config.max_age))

        if self.config.allow_credentials:
            handler.send_header('Access-Control-Allow-Credentials', 'true')

        handler.end_headers()
        return True

    def apply_cors_headers(self, handler: BaseHTTPRequestHandler) -> bool:
        """
        Apply CORS headers to response

        Args:
            handler: HTTP request handler

        Returns:
            True if CORS headers applied, False if origin not allowed
        """
        # Validate origin
        origin = self.validate_origin(handler)

        if not origin:
            # No origin or not allowed - don't add CORS headers
            # This is fine for same-origin requests
            if 'Origin' in handler.headers:
                # Origin was present but not allowed
                return False
            return True

        # Validate CSRF token for state-changing operations
        if handler.command in self.config.state_changing_methods:
            if not self.validate_csrf_token(handler):
                return False

        # Add CORS headers
        handler.send_header('Access-Control-Allow-Origin', origin)

        if self.config.exposed_headers:
            handler.send_header('Access-Control-Expose-Headers', ', '.join(self.config.exposed_headers))

        if self.config.allow_credentials:
            handler.send_header('Access-Control-Allow-Credentials', 'true')

        # Vary header to prevent caching issues
        handler.send_header('Vary', 'Origin')

        return True

    def is_sensitive_endpoint(self, path: str) -> bool:
        """
        Check if endpoint is sensitive and should reject cross-origin requests

        Args:
            path: Request path

        Returns:
            True if endpoint is sensitive
        """
        sensitive_endpoints = [
            '/auth',
            '/login',
            '/logout',
            '/admin',
            '/config',
            '/settings',
        ]

        for endpoint in sensitive_endpoints:
            if path.startswith(endpoint):
                return True

        return False

    def validate_cors_request(self, handler: BaseHTTPRequestHandler) -> Dict[str, any]:
        """
        Validate complete CORS request

        Args:
            handler: HTTP request handler

        Returns:
            Dictionary with validation results
        """
        result = {
            'allowed': False,
            'origin': None,
            'is_preflight': False,
            'is_cors': False,
            'csrf_valid': True,
            'error': None
        }

        # Check if CORS request
        result['is_cors'] = self.is_cors_request(handler)
        result['is_preflight'] = self.is_preflight_request(handler)

        # If not a CORS request, allow
        if not result['is_cors']:
            result['allowed'] = True
            return result

        # Validate origin
        origin = self.validate_origin(handler)
        result['origin'] = origin

        if not origin:
            result['error'] = 'Origin not allowed'
            return result

        # Check if sensitive endpoint
        if self.is_sensitive_endpoint(handler.path):
            result['error'] = 'Cross-origin requests not allowed for sensitive endpoints'
            return result

        # Validate CSRF for state-changing operations
        if handler.command in self.config.state_changing_methods:
            if not self.validate_csrf_token(handler):
                result['csrf_valid'] = False
                result['error'] = 'Invalid or missing CSRF token'
                return result

        # All checks passed
        result['allowed'] = True
        return result


# Singleton instance with secure defaults
cors_handler = CORSHandler()


# Convenience functions
def configure_cors(
    allowed_origins: List[str],
    allowed_methods: Optional[List[str]] = None,
    require_csrf: bool = True
) -> CORSHandler:
    """
    Configure CORS handler

    Args:
        allowed_origins: List of allowed origins
        allowed_methods: Optional list of allowed methods
        require_csrf: Require CSRF tokens for state-changing operations

    Returns:
        Configured CORS handler
    """
    config = CORSConfig(
        allowed_origins=allowed_origins,
        allowed_methods=allowed_methods,
        require_csrf_token=require_csrf
    )
    return CORSHandler(config)


def add_allowed_origin(origin: str):
    """Add an allowed origin to the default handler"""
    cors_handler.config.add_allowed_origin(origin)


def validate_and_apply_cors(handler: BaseHTTPRequestHandler) -> bool:
    """
    Validate CORS request and apply headers

    Args:
        handler: HTTP request handler

    Returns:
        True if request is allowed
    """
    # Handle preflight
    if cors_handler.is_preflight_request(handler):
        return cors_handler.handle_preflight_request(handler)

    # Validate regular CORS request
    validation = cors_handler.validate_cors_request(handler)
    if not validation['allowed']:
        return False

    return True
