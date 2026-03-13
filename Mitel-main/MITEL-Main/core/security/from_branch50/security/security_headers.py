#!/usr/bin/env python3
"""
Security Headers Framework
Adds comprehensive security headers to HTTP responses to prevent common attacks.
"""

from typing import Dict, Optional, List
from http.server import BaseHTTPRequestHandler


class SecurityHeaders:
    """
    Manages security headers for HTTP responses
    - Prevents XSS attacks
    - Prevents clickjacking
    - Enforces HTTPS
    - Controls content types
    - Implements CSP
    """

    # Default security headers
    DEFAULT_HEADERS = {
        # Prevent MIME type sniffing
        'X-Content-Type-Options': 'nosniff',

        # Prevent clickjacking
        'X-Frame-Options': 'DENY',

        # Enable XSS protection (legacy browsers)
        'X-XSS-Protection': '1; mode=block',

        # Force HTTPS for 1 year
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',

        # Content Security Policy - strict by default
        'Content-Security-Policy': "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'",

        # Referrer policy
        'Referrer-Policy': 'strict-origin-when-cross-origin',

        # Permissions policy (formerly Feature-Policy)
        'Permissions-Policy': 'geolocation=(), microphone=(), camera=(), payment=(), usb=(), magnetometer=(), gyroscope=(), accelerometer=()',

        # Prevent caching of sensitive data
        'Cache-Control': 'no-store, no-cache, must-revalidate, private',
        'Pragma': 'no-cache',
        'Expires': '0',
    }

    # Header presets for different security levels
    PRESETS = {
        'strict': {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains; preload',
            'Content-Security-Policy': "default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self'; font-src 'self'; connect-src 'self'; frame-ancestors 'none'",
            'Referrer-Policy': 'no-referrer',
            'Cache-Control': 'no-store, no-cache, must-revalidate, private',
        },
        'moderate': {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'SAMEORIGIN',
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': 'max-age=31536000',
            'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:",
            'Referrer-Policy': 'strict-origin-when-cross-origin',
        },
        'api': {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'Strict-Transport-Security': 'max-age=31536000',
            'Content-Security-Policy': "default-src 'none'",
            'Cache-Control': 'no-store',
        },
    }

    def __init__(self, preset: str = 'strict', custom_headers: Optional[Dict[str, str]] = None):
        """
        Initialize security headers

        Args:
            preset: Security preset ('strict', 'moderate', 'api', or 'default')
            custom_headers: Optional custom headers to add/override
        """
        # Start with preset or default
        if preset in self.PRESETS:
            self.headers = self.PRESETS[preset].copy()
        else:
            self.headers = self.DEFAULT_HEADERS.copy()

        # Apply custom headers
        if custom_headers:
            self.headers.update(custom_headers)

    def add_header(self, name: str, value: str):
        """
        Add or update a security header

        Args:
            name: Header name
            value: Header value
        """
        self.headers[name] = value

    def remove_header(self, name: str):
        """
        Remove a security header

        Args:
            name: Header name to remove
        """
        if name in self.headers:
            del self.headers[name]

    def get_headers(self) -> Dict[str, str]:
        """
        Get all security headers

        Returns:
            Dictionary of header name-value pairs
        """
        return self.headers.copy()

    def apply_to_handler(self, handler: BaseHTTPRequestHandler):
        """
        Apply security headers to an HTTP request handler

        Args:
            handler: HTTP request handler instance
        """
        for name, value in self.headers.items():
            handler.send_header(name, value)

    def apply_to_response_dict(self, response_headers: Dict[str, str]) -> Dict[str, str]:
        """
        Apply security headers to a response headers dictionary

        Args:
            response_headers: Existing response headers

        Returns:
            Updated response headers
        """
        updated = response_headers.copy()
        updated.update(self.headers)
        return updated

    def update_csp(self, directive: str, value: str):
        """
        Update a specific CSP directive

        Args:
            directive: CSP directive name (e.g., 'script-src', 'style-src')
            value: New value for the directive
        """
        if 'Content-Security-Policy' not in self.headers:
            self.headers['Content-Security-Policy'] = f"{directive} {value}"
            return

        csp = self.headers['Content-Security-Policy']
        directives = {}

        # Parse existing CSP
        for part in csp.split(';'):
            part = part.strip()
            if not part:
                continue
            parts = part.split(None, 1)
            if len(parts) == 2:
                directives[parts[0]] = parts[1]
            elif len(parts) == 1:
                directives[parts[0]] = ''

        # Update directive
        directives[directive] = value

        # Rebuild CSP
        new_csp = '; '.join(f"{k} {v}".strip() for k, v in directives.items())
        self.headers['Content-Security-Policy'] = new_csp

    def add_csp_source(self, directive: str, source: str):
        """
        Add a source to a CSP directive

        Args:
            directive: CSP directive name
            source: Source to add (e.g., 'https://example.com', "'unsafe-inline'")
        """
        if 'Content-Security-Policy' not in self.headers:
            self.headers['Content-Security-Policy'] = f"{directive} {source}"
            return

        csp = self.headers['Content-Security-Policy']
        directives = {}

        # Parse existing CSP
        for part in csp.split(';'):
            part = part.strip()
            if not part:
                continue
            parts = part.split(None, 1)
            if len(parts) == 2:
                directives[parts[0]] = parts[1]
            elif len(parts) == 1:
                directives[parts[0]] = ''

        # Add source to directive
        if directive in directives:
            if source not in directives[directive]:
                directives[directive] = f"{directives[directive]} {source}".strip()
        else:
            directives[directive] = source

        # Rebuild CSP
        new_csp = '; '.join(f"{k} {v}".strip() for k, v in directives.items())
        self.headers['Content-Security-Policy'] = new_csp

    def enable_cors(self, allowed_origins: List[str]):
        """
        Enable CORS with specific origins (don't use this directly, use cors_handler.py)

        Args:
            allowed_origins: List of allowed origins
        """
        # Note: This is a basic implementation
        # For production, use the cors_handler.py module
        if len(allowed_origins) == 1:
            self.headers['Access-Control-Allow-Origin'] = allowed_origins[0]
        else:
            # For multiple origins, this needs to be dynamic based on request
            # See cors_handler.py for proper implementation
            pass

        self.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        self.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        self.headers['Access-Control-Max-Age'] = '3600'

    def set_hsts(self, max_age: int = 31536000, include_subdomains: bool = True, preload: bool = False):
        """
        Configure HTTP Strict Transport Security

        Args:
            max_age: Max age in seconds (default: 1 year)
            include_subdomains: Include subdomains
            preload: Enable HSTS preload
        """
        hsts = f'max-age={max_age}'
        if include_subdomains:
            hsts += '; includeSubDomains'
        if preload:
            hsts += '; preload'

        self.headers['Strict-Transport-Security'] = hsts

    def disable_caching(self):
        """Disable all caching (for sensitive pages)"""
        self.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, private, max-age=0'
        self.headers['Pragma'] = 'no-cache'
        self.headers['Expires'] = '0'

    def enable_caching(self, max_age: int = 3600):
        """
        Enable caching (for static resources)

        Args:
            max_age: Cache max age in seconds
        """
        self.headers['Cache-Control'] = f'public, max-age={max_age}'
        if 'Pragma' in self.headers:
            del self.headers['Pragma']
        if 'Expires' in self.headers:
            del self.headers['Expires']


class SecurityHeadersMiddleware:
    """Middleware to automatically apply security headers to responses"""

    def __init__(self, preset: str = 'strict', custom_headers: Optional[Dict[str, str]] = None):
        """
        Initialize middleware

        Args:
            preset: Security preset to use
            custom_headers: Optional custom headers
        """
        self.security_headers = SecurityHeaders(preset, custom_headers)

    def process_response(self, handler: BaseHTTPRequestHandler):
        """
        Process response and add security headers

        Args:
            handler: HTTP request handler
        """
        self.security_headers.apply_to_handler(handler)


# Singleton instances for common presets
strict_headers = SecurityHeaders(preset='strict')
moderate_headers = SecurityHeaders(preset='moderate')
api_headers = SecurityHeaders(preset='api')


# Convenience functions
def apply_security_headers(
    handler: BaseHTTPRequestHandler,
    preset: str = 'strict',
    custom_headers: Optional[Dict[str, str]] = None
):
    """
    Apply security headers to an HTTP handler

    Args:
        handler: HTTP request handler
        preset: Security preset to use
        custom_headers: Optional custom headers
    """
    headers = SecurityHeaders(preset, custom_headers)
    headers.apply_to_handler(handler)


def get_security_headers(
    preset: str = 'strict',
    custom_headers: Optional[Dict[str, str]] = None
) -> Dict[str, str]:
    """
    Get security headers as dictionary

    Args:
        preset: Security preset to use
        custom_headers: Optional custom headers

    Returns:
        Dictionary of security headers
    """
    headers = SecurityHeaders(preset, custom_headers)
    return headers.get_headers()
