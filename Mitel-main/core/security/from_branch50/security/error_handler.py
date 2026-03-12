#!/usr/bin/env python3
"""
Secure Error Handler Framework
Prevents information disclosure through error messages.
Never exposes stack traces, file paths, or system information to users.
"""

import sys
import traceback
import logging
from typing import Dict, Optional, Any
from http.server import BaseHTTPRequestHandler
import json


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('error_handler')


class SecurityError(Exception):
    """Base class for security-related errors"""
    def __init__(self, message: str, status_code: int = 403):
        super().__init__(message)
        self.status_code = status_code


class AuthenticationError(SecurityError):
    """Authentication failed"""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status_code=401)


class AuthorizationError(SecurityError):
    """Authorization failed"""
    def __init__(self, message: str = "Access denied"):
        super().__init__(message, status_code=403)


class ValidationError(SecurityError):
    """Input validation failed"""
    def __init__(self, message: str = "Invalid request"):
        super().__init__(message, status_code=400)


class RateLimitError(SecurityError):
    """Rate limit exceeded"""
    def __init__(self, message: str = "Too many requests", retry_after: Optional[int] = None):
        super().__init__(message, status_code=429)
        self.retry_after = retry_after


class ErrorHandler:
    """
    Secure error handler that prevents information disclosure
    - Generic error messages for users
    - Detailed logging server-side
    - Never exposes stack traces
    - Sanitizes error responses
    """

    # Generic error messages (safe to show to users)
    GENERIC_MESSAGES = {
        400: "Invalid request",
        401: "Authentication required",
        403: "Access denied",
        404: "Resource not found",
        405: "Method not allowed",
        429: "Too many requests. Please try again later",
        500: "Internal server error",
        502: "Bad gateway",
        503: "Service unavailable",
    }

    def __init__(self, debug_mode: bool = False):
        """
        Initialize error handler

        Args:
            debug_mode: If True, include more details in responses (ONLY for development)
        """
        self.debug_mode = debug_mode

    def get_generic_message(self, status_code: int) -> str:
        """
        Get generic error message for status code

        Args:
            status_code: HTTP status code

        Returns:
            Generic error message
        """
        return self.GENERIC_MESSAGES.get(status_code, "An error occurred")

    def sanitize_error_message(self, message: str) -> str:
        """
        Sanitize error message to prevent information disclosure

        Args:
            message: Original error message

        Returns:
            Sanitized error message
        """
        # Remove file paths
        if '/' in message or '\\' in message:
            return "Invalid request"

        # Remove stack trace indicators
        if 'Traceback' in message or 'File "' in message:
            return "Internal server error"

        # Remove version information
        if any(keyword in message.lower() for keyword in ['version', 'python', 'module']):
            return "Internal server error"

        # Remove SQL-related errors that might leak schema
        if any(keyword in message.lower() for keyword in ['sql', 'database', 'table', 'column']):
            return "Database error"

        # Limit message length
        if len(message) > 100:
            return "Invalid request"

        return message

    def log_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        level: str = 'error'
    ):
        """
        Log error with full details server-side

        Args:
            error: Exception that occurred
            context: Optional context information
            level: Log level ('error', 'warning', 'info')
        """
        # Build log message
        log_data = {
            'error_type': type(error).__name__,
            'error_message': str(error),
            'traceback': traceback.format_exc() if sys.exc_info()[0] else None,
        }

        if context:
            log_data['context'] = context

        # Log based on level
        log_message = json.dumps(log_data, indent=2)

        if level == 'error':
            logger.error(log_message)
        elif level == 'warning':
            logger.warning(log_message)
        else:
            logger.info(log_message)

    def create_error_response(
        self,
        status_code: int,
        error: Optional[Exception] = None,
        custom_message: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create safe error response

        Args:
            status_code: HTTP status code
            error: Optional exception that occurred
            custom_message: Optional custom message
            context: Optional context for logging

        Returns:
            Error response dictionary
        """
        # Log full error details server-side
        if error:
            self.log_error(error, context)

        # Create safe response for user
        response = {
            'error': True,
            'status': status_code,
        }

        # Add safe message
        if custom_message:
            if self.debug_mode:
                response['message'] = custom_message
            else:
                response['message'] = self.sanitize_error_message(custom_message)
        else:
            response['message'] = self.get_generic_message(status_code)

        # Add debug info ONLY in debug mode
        if self.debug_mode and error:
            response['debug'] = {
                'type': type(error).__name__,
                'message': str(error),
            }

        return response

    def send_error_response(
        self,
        handler: BaseHTTPRequestHandler,
        status_code: int,
        error: Optional[Exception] = None,
        custom_message: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        retry_after: Optional[int] = None
    ):
        """
        Send error response to client

        Args:
            handler: HTTP request handler
            status_code: HTTP status code
            error: Optional exception
            custom_message: Optional custom message
            context: Optional context for logging
            retry_after: Optional retry-after value for 429 responses
        """
        # Create response
        response = self.create_error_response(status_code, error, custom_message, context)

        # Send HTTP response
        handler.send_response(status_code)
        handler.send_header('Content-Type', 'application/json')

        # Add Retry-After header for rate limiting
        if status_code == 429 and retry_after:
            handler.send_header('Retry-After', str(retry_after))

        handler.end_headers()

        # Send JSON body
        response_json = json.dumps(response)
        handler.wfile.write(response_json.encode('utf-8'))

    def handle_exception(
        self,
        handler: BaseHTTPRequestHandler,
        error: Exception,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Handle exception and send appropriate response

        Args:
            handler: HTTP request handler
            error: Exception that occurred
            context: Optional context information
        """
        # Determine status code and message based on error type
        if isinstance(error, AuthenticationError):
            self.send_error_response(handler, 401, error, context=context)

        elif isinstance(error, AuthorizationError):
            self.send_error_response(handler, 403, error, context=context)

        elif isinstance(error, ValidationError):
            self.send_error_response(handler, 400, error, context=context)

        elif isinstance(error, RateLimitError):
            retry_after = getattr(error, 'retry_after', None)
            self.send_error_response(
                handler, 429, error,
                context=context,
                retry_after=retry_after
            )

        elif isinstance(error, SecurityError):
            self.send_error_response(handler, error.status_code, error, context=context)

        elif isinstance(error, (ValueError, TypeError, KeyError)):
            # Client errors - 400
            self.send_error_response(handler, 400, error, "Invalid request", context)

        elif isinstance(error, FileNotFoundError):
            self.send_error_response(handler, 404, error, context=context)

        elif isinstance(error, PermissionError):
            self.send_error_response(handler, 403, error, context=context)

        else:
            # Unknown error - 500
            self.send_error_response(handler, 500, error, context=context)

    def wrap_handler_method(self, method):
        """
        Decorator to wrap handler methods with error handling

        Args:
            method: Handler method to wrap

        Returns:
            Wrapped method
        """
        def wrapper(handler, *args, **kwargs):
            try:
                return method(handler, *args, **kwargs)
            except Exception as e:
                context = {
                    'method': handler.command,
                    'path': handler.path,
                    'client_address': handler.client_address[0] if handler.client_address else 'unknown',
                }
                self.handle_exception(handler, e, context)
        return wrapper


# Singleton instance
error_handler = ErrorHandler(debug_mode=False)


# Convenience functions
def send_error(
    handler: BaseHTTPRequestHandler,
    status_code: int,
    message: Optional[str] = None,
    error: Optional[Exception] = None
):
    """
    Send error response

    Args:
        handler: HTTP request handler
        status_code: HTTP status code
        message: Optional custom message
        error: Optional exception
    """
    error_handler.send_error_response(handler, status_code, error, message)


def handle_exception(
    handler: BaseHTTPRequestHandler,
    error: Exception,
    context: Optional[Dict[str, Any]] = None
):
    """
    Handle exception

    Args:
        handler: HTTP request handler
        error: Exception
        context: Optional context
    """
    error_handler.handle_exception(handler, error, context)


def safe_error_wrapper(method):
    """
    Decorator for handler methods

    Args:
        method: Method to wrap

    Returns:
        Wrapped method with error handling
    """
    return error_handler.wrap_handler_method(method)


# Custom exception classes for common scenarios
class InvalidInputError(ValidationError):
    """Invalid input provided"""
    pass


class InvalidJSONError(ValidationError):
    """Invalid JSON provided"""
    def __init__(self):
        super().__init__("Invalid JSON format")


class RequestTooLargeError(ValidationError):
    """Request payload too large"""
    def __init__(self, size: int, max_size: int):
        super().__init__(f"Request size exceeds maximum allowed")
        self.size = size
        self.max_size = max_size


class InvalidTokenError(AuthenticationError):
    """Invalid authentication token"""
    def __init__(self):
        super().__init__("Invalid authentication token")


class ExpiredTokenError(AuthenticationError):
    """Authentication token expired"""
    def __init__(self):
        super().__init__("Authentication token expired")


class InsufficientPermissionsError(AuthorizationError):
    """User lacks required permissions"""
    def __init__(self, permission: str):
        super().__init__("Insufficient permissions")
        self.permission = permission


class ResourceNotFoundError(SecurityError):
    """Resource not found"""
    def __init__(self, resource: str = "Resource"):
        super().__init__(f"{resource} not found", status_code=404)


class MethodNotAllowedError(SecurityError):
    """HTTP method not allowed"""
    def __init__(self, method: str):
        super().__init__(f"Method not allowed", status_code=405)
        self.method = method
