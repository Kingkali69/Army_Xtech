# GhostOps Security Framework

Comprehensive security hardening framework implementing input validation, rate limiting, security headers, CORS handling, error handling, and audit logging.

## Overview

This security framework provides six key modules that work together to harden the GhostOps platform against common attacks:

1. **Input Validator** - Sanitizes and validates all user inputs
2. **Rate Limiter** - Prevents abuse through request rate limiting
3. **Security Headers** - Adds comprehensive HTTP security headers
4. **CORS Handler** - Implements proper Cross-Origin Resource Sharing
5. **Error Handler** - Prevents information disclosure through safe error messages
6. **Audit Logger** - Comprehensive security event logging

## Installation

The security framework is already included in the GhostOps codebase. Simply import the modules you need:

```python
from security import (
    validator,
    rate_limiter,
    audit_logger,
    apply_security_headers,
    validate_and_apply_cors,
    handle_exception
)
```

## Module Documentation

### 1. Input Validator (`input_validator.py`)

Validates and sanitizes all user inputs to prevent injection attacks.

**Features:**
- JSON validation (max 1MB, schema validation)
- Query parameter sanitization
- Form input sanitization
- Request size validation (max 10MB)
- SQL injection prevention
- XSS prevention
- Path traversal prevention
- Command injection prevention

**Usage:**

```python
from security import validator, validate_json, sanitize_string, sanitize_path

# Validate JSON
try:
    data = validate_json(request_body)
except ValidationError as e:
    # Handle validation error
    pass

# Sanitize string input
clean_input = sanitize_string(user_input)

# Sanitize file path
safe_path = sanitize_path(file_path)

# Validate request size
validate_request_size(content_length)

# Validate with schema
schema = {
    'username': {'required': True, 'type': str, 'validator': validator.validate_username},
    'email': {'required': True, 'type': str, 'validator': validator.validate_email},
}
validated_data = validator.validate_schema(data, schema)
```

**Limits:**
- Max JSON size: 1MB
- Max request size: 10MB
- Max string length: 10,000 characters
- Max array length: 1,000 items
- Max object depth: 10 levels

### 2. Rate Limiter (`rate_limiter.py`)

Implements token bucket rate limiting to prevent abuse.

**Features:**
- Per-IP rate limiting (100 requests/minute)
- Failed login limiting (10 failures/minute)
- Tool execution limiting (5 executions/minute per user)
- File sync limiting (1000 requests/hour)
- Automatic cleanup of old data
- 429 Too Many Requests responses

**Usage:**

```python
from security import check_rate_limit, record_auth_failure, record_tool_execution

# Check general rate limit
allowed, retry_after, message = check_rate_limit(
    ip_address="192.168.1.100",
    user_id="user123",
    endpoint="/api/sync",
    limit_type='general'
)

if not allowed:
    # Return 429 Too Many Requests
    # Retry-After: {retry_after} seconds
    pass

# Record authentication failure
allowed, retry_after, message = record_auth_failure(ip_address)

# Record tool execution
allowed, retry_after, message = record_tool_execution(user_id)

# Record file sync
allowed, retry_after, message = record_file_sync(ip_address)
```

**Rate Limits:**
- General: 100 requests/minute per IP
- Auth failures: 10 failures/minute per IP
- Tool execution: 5 executions/minute per user
- File sync: 1000 requests/hour per IP

### 3. Security Headers (`security_headers.py`)

Adds comprehensive HTTP security headers to all responses.

**Features:**
- X-Content-Type-Options: nosniff
- X-Frame-Options: DENY
- X-XSS-Protection: 1; mode=block
- Strict-Transport-Security: max-age=31536000
- Content-Security-Policy: default-src 'self'
- Referrer-Policy: strict-origin-when-cross-origin
- Permissions-Policy (blocks dangerous APIs)
- Cache-Control (prevents sensitive data caching)

**Usage:**

```python
from security import apply_security_headers, SecurityHeaders

# Apply headers to HTTP handler
def do_GET(self):
    self.send_response(200)
    apply_security_headers(self, preset='strict')
    self.end_headers()

# Custom headers
custom = SecurityHeaders(preset='moderate')
custom.update_csp('script-src', "'self' https://cdn.example.com")
custom.apply_to_handler(handler)

# Presets: 'strict', 'moderate', 'api'
```

**Presets:**
- **strict**: Maximum security, blocks most external resources
- **moderate**: Balanced security, allows inline styles
- **api**: API-focused, minimal CSP

### 4. CORS Handler (`cors_handler.py`)

Implements proper CORS with origin whitelisting (NO wildcards).

**Features:**
- Whitelist specific origins only
- Preflight request handling
- CSRF token validation for state-changing operations
- Sensitive endpoint protection
- Per-request origin validation

**Usage:**

```python
from security import cors_handler, add_allowed_origin, configure_cors

# Add allowed origins
add_allowed_origin('https://app.example.com')
add_allowed_origin('https://admin.example.com')

# Handle CORS in HTTP handler
def do_OPTIONS(self):
    # Handle preflight
    if cors_handler.is_preflight_request(self):
        cors_handler.handle_preflight_request(self)
        return

def do_POST(self):
    # Validate CORS
    validation = cors_handler.validate_cors_request(self)
    if not validation['allowed']:
        send_error(self, 403, validation['error'])
        return

    # Apply CORS headers
    self.send_response(200)
    cors_handler.apply_cors_headers(self)
    self.end_headers()

# Custom CORS configuration
from security import CORSConfig, CORSHandler

config = CORSConfig(
    allowed_origins=['https://app.example.com'],
    allowed_methods=['GET', 'POST'],
    require_csrf_token=True
)
custom_cors = CORSHandler(config)
```

**BEFORE:**
```python
# DANGEROUS - allows any origin
headers['Access-Control-Allow-Origin'] = '*'
```

**AFTER:**
```python
# SECURE - only whitelisted origins
add_allowed_origin('https://trusted-app.com')
cors_handler.apply_cors_headers(handler)
```

### 5. Error Handler (`error_handler.py`)

Prevents information disclosure through safe error messages.

**Features:**
- Generic error messages for users
- Detailed logging server-side only
- Never exposes stack traces to users
- Never reveals file paths, versions, or system info
- Custom exception classes
- Automatic exception handling

**Usage:**

```python
from security import send_error, handle_exception, safe_error_wrapper
from security import AuthenticationError, ValidationError, RateLimitError

# Send safe error response
send_error(handler, 400, "Invalid request")

# Handle exception automatically
try:
    # Your code here
    pass
except Exception as e:
    handle_exception(handler, e, context={'endpoint': '/api/sync'})

# Raise custom exceptions
raise AuthenticationError("Invalid token")
raise ValidationError("Invalid input")
raise RateLimitError("Too many requests", retry_after=60)

# Decorator for automatic error handling
@safe_error_wrapper
def do_POST(self):
    # Any exception raised here will be handled safely
    data = validate_json(self.rfile.read())
```

**Error Messages (User vs Server):**
- **User sees**: "Invalid request"
- **Server logs**: Full stack trace, file paths, detailed error info

### 6. Audit Logger (`audit_logger.py`)

Comprehensive security event logging with daily rotation.

**Features:**
- Logs all authentication attempts
- Logs all file operations
- Logs all tool executions
- Logs all API errors
- Daily log rotation
- 30-day retention
- Thread-safe logging

**Usage:**

```python
from security import audit_logger, log_auth_success, log_auth_failure

# Log authentication
log_auth_success(user_id="user123", ip_address="192.168.1.100")
log_auth_failure(user_id="user123", ip_address="192.168.1.100", reason="Invalid password")

# Log file operations
audit_logger.log_file_read(user_id="user123", file_path="/data/file.txt", ip_address="192.168.1.100")
audit_logger.log_file_write(user_id="user123", file_path="/data/file.txt", ip_address="192.168.1.100", size=1024)
audit_logger.log_file_delete(user_id="user123", file_path="/data/file.txt", ip_address="192.168.1.100")

# Log tool execution
audit_logger.log_tool_execution(user_id="user123", tool_name="nmap", ip_address="192.168.1.100")

# Log API requests
audit_logger.log_api_request(
    endpoint="/api/sync",
    method="POST",
    ip_address="192.168.1.100",
    status_code=200,
    response_time_ms=45.2
)

# Log security events
audit_logger.log_injection_attempt(
    injection_type="SQL",
    ip_address="192.168.1.100",
    payload="' OR 1=1--"
)

audit_logger.log_path_traversal_attempt(
    ip_address="192.168.1.100",
    attempted_path="../../../etc/passwd"
)
```

**Log Format:**
```json
{
  "timestamp": "2025-11-19T10:30:45.123456",
  "event_type": "auth_failure",
  "severity": "warning",
  "success": false,
  "user_id": "user123",
  "ip_address": "192.168.1.100",
  "details": {
    "reason": "Invalid password"
  }
}
```

## Integration Example

Here's a complete example integrating all security modules:

```python
from security import (
    validate_json,
    validate_request_size,
    check_rate_limit,
    apply_security_headers,
    cors_handler,
    handle_exception,
    audit_logger,
)

class SecureHTTPHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        start_time = time.time()

        try:
            # 1. Validate request size
            content_length = int(self.headers.get('Content-Length', 0))
            validate_request_size(content_length)

            # 2. Check rate limit
            ip_address = self.client_address[0]
            allowed, retry_after, message = check_rate_limit(
                ip_address=ip_address,
                endpoint=self.path
            )
            if not allowed:
                self.send_response(429)
                apply_security_headers(self)
                self.send_header('Retry-After', str(retry_after))
                self.end_headers()
                self.wfile.write(json.dumps({'error': message}).encode())
                audit_logger.log_rate_limit_exceeded(ip_address, 'general')
                return

            # 3. Validate CORS
            validation = cors_handler.validate_cors_request(self)
            if not validation['allowed']:
                self.send_response(403)
                apply_security_headers(self)
                self.end_headers()
                self.wfile.write(json.dumps({'error': validation['error']}).encode())
                return

            # 4. Validate JSON input
            body = self.rfile.read(content_length)
            data = validate_json(body.decode('utf-8'))

            # 5. Process request
            result = self.process_request(data)

            # 6. Send response with security headers
            self.send_response(200)
            apply_security_headers(self, preset='strict')
            cors_handler.apply_cors_headers(self)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())

            # 7. Log successful request
            response_time = (time.time() - start_time) * 1000
            audit_logger.log_api_request(
                endpoint=self.path,
                method='POST',
                ip_address=ip_address,
                status_code=200,
                response_time_ms=response_time
            )

        except Exception as e:
            # 8. Handle errors securely
            handle_exception(self, e, context={
                'endpoint': self.path,
                'method': 'POST'
            })
```

## Configuration

### Environment Variables

```bash
# Audit Logger
export GHOSTOPS_LOG_DIR="/var/log/ghostops/security"
export GHOSTOPS_LOG_RETENTION_DAYS=30

# Rate Limiter
export GHOSTOPS_RATE_LIMIT_GENERAL=100  # requests per minute
export GHOSTOPS_RATE_LIMIT_AUTH=10      # failed logins per minute

# Error Handler
export GHOSTOPS_DEBUG_MODE=false  # NEVER set to true in production
```

### CORS Whitelist

Add your allowed origins in the application startup:

```python
from security import add_allowed_origin

# Add trusted origins
add_allowed_origin('https://app.example.com')
add_allowed_origin('https://admin.example.com')
add_allowed_origin('https://*.trusted-domain.com')  # Wildcard subdomain
```

## Security Best Practices

1. **Never disable security in production**
   - Always use `debug_mode=False` for ErrorHandler
   - Never use CORS wildcard (`*`)
   - Always validate and sanitize inputs

2. **Rate limiting**
   - Adjust limits based on your use case
   - Monitor rate limit logs for abuse patterns
   - Consider IP-based blocking for persistent attackers

3. **Audit logging**
   - Review logs regularly for suspicious activity
   - Set up alerts for critical events (injection attempts, path traversal)
   - Ensure logs are stored securely and backed up

4. **CORS configuration**
   - Only whitelist origins you trust
   - Require CSRF tokens for state-changing operations
   - Block cross-origin requests to sensitive endpoints

5. **Error handling**
   - Never expose internal details to users
   - Log all errors server-side for debugging
   - Use custom exception classes for better error categorization

## Testing

Test the security framework:

```bash
# Run security tests
python3 -m pytest tests/security/

# Test input validation
python3 -c "from security import validate_json; validate_json('{\"test\": \"data\"}')"

# Test rate limiting
python3 -c "from security import check_rate_limit; print(check_rate_limit('127.0.0.1'))"
```

## License

Part of the GhostOps platform. See main project LICENSE.

## Support

For security issues, please report to the GhostOps security team.
