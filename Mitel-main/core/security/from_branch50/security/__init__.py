#!/usr/bin/env python3
"""
GhostOps Security Framework

Comprehensive security hardening modules for input validation,
rate limiting, security headers, CORS handling, error handling,
and audit logging.

Usage:
    from security import validator, rate_limiter, audit_logger
    from security.error_handler import send_error, handle_exception
    from security.security_headers import apply_security_headers
    from security.cors_handler import validate_and_apply_cors
"""

# Import main components
from .input_validator import (
    InputValidator,
    ValidationError,
    validator,
    validate_json,
    sanitize_string,
    sanitize_path,
    sanitize_query_params,
    validate_request_size,
)

from .rate_limiter import (
    RateLimiter,
    RateLimitConfig,
    rate_limiter,
    check_rate_limit,
    record_auth_failure,
    record_tool_execution,
    record_file_sync,
)

from .security_headers import (
    SecurityHeaders,
    SecurityHeadersMiddleware,
    strict_headers,
    moderate_headers,
    api_headers,
    apply_security_headers,
    get_security_headers,
)

from .cors_handler import (
    CORSConfig,
    CORSHandler,
    cors_handler,
    configure_cors,
    add_allowed_origin,
    validate_and_apply_cors,
)

from .error_handler import (
    ErrorHandler,
    SecurityError,
    AuthenticationError,
    AuthorizationError,
    RateLimitError,
    InvalidInputError,
    InvalidJSONError,
    RequestTooLargeError,
    InvalidTokenError,
    ExpiredTokenError,
    InsufficientPermissionsError,
    ResourceNotFoundError,
    MethodNotAllowedError,
    error_handler,
    send_error,
    handle_exception,
    safe_error_wrapper,
)

from .audit_logger import (
    AuditLogger,
    EventType,
    EventSeverity,
    audit_logger,
    log_auth_success,
    log_auth_failure,
    log_file_operation,
    log_tool_execution,
    log_api_request,
    log_security_event,
)

__version__ = '1.0.0'
__all__ = [
    # Input Validator
    'InputValidator',
    'ValidationError',
    'validator',
    'validate_json',
    'sanitize_string',
    'sanitize_path',
    'sanitize_query_params',
    'validate_request_size',

    # Rate Limiter
    'RateLimiter',
    'RateLimitConfig',
    'rate_limiter',
    'check_rate_limit',
    'record_auth_failure',
    'record_tool_execution',
    'record_file_sync',

    # Security Headers
    'SecurityHeaders',
    'SecurityHeadersMiddleware',
    'strict_headers',
    'moderate_headers',
    'api_headers',
    'apply_security_headers',
    'get_security_headers',

    # CORS Handler
    'CORSConfig',
    'CORSHandler',
    'cors_handler',
    'configure_cors',
    'add_allowed_origin',
    'validate_and_apply_cors',

    # Error Handler
    'ErrorHandler',
    'SecurityError',
    'AuthenticationError',
    'AuthorizationError',
    'RateLimitError',
    'InvalidInputError',
    'InvalidJSONError',
    'RequestTooLargeError',
    'InvalidTokenError',
    'ExpiredTokenError',
    'InsufficientPermissionsError',
    'ResourceNotFoundError',
    'MethodNotAllowedError',
    'error_handler',
    'send_error',
    'handle_exception',
    'safe_error_wrapper',

    # Audit Logger
    'AuditLogger',
    'EventType',
    'EventSeverity',
    'audit_logger',
    'log_auth_success',
    'log_auth_failure',
    'log_file_operation',
    'log_tool_execution',
    'log_api_request',
    'log_security_event',
]
