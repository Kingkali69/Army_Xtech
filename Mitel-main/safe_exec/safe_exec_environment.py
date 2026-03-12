#!/usr/bin/env python3
"""
Safe Execution Environment - Restricted Python Interpreter
Provides sandboxed Python execution with limited imports and capabilities
"""

import sys
import io
import time
import signal
import resource
import threading
from typing import Dict, Any, Optional, Set
from contextlib import redirect_stdout, redirect_stderr


class SafeExecEnvironment:
    """
    Restricted Python execution environment with security controls

    Features:
    - Limited imports (no os.system, subprocess, etc.)
    - Read-only file system
    - Memory limit (256MB max)
    - Execution timeout (300 seconds max)
    - Audit logging
    """

    # Whitelist of allowed built-in functions
    ALLOWED_BUILTINS = {
        'abs', 'all', 'any', 'ascii', 'bin', 'bool', 'bytearray', 'bytes',
        'chr', 'complex', 'dict', 'dir', 'divmod', 'enumerate', 'filter',
        'float', 'format', 'frozenset', 'hex', 'int', 'isinstance',
        'issubclass', 'iter', 'len', 'list', 'map', 'max', 'min', 'next',
        'oct', 'ord', 'pow', 'print', 'range', 'repr', 'reversed', 'round',
        'set', 'slice', 'sorted', 'str', 'sum', 'tuple', 'type', 'zip',
        '__import__', '__name__', '__doc__'
    }

    # Whitelist of allowed modules (read-only, safe modules only)
    ALLOWED_MODULES = {
        'math', 'random', 'string', 'json', 'datetime', 'time',
        'collections', 'itertools', 'functools', 're', 'hashlib'
    }

    # Blacklist of dangerous modules/functions
    BLOCKED_IMPORTS = {
        'os', 'sys', 'subprocess', 'socket', 'urllib', 'requests',
        'pickle', 'shelve', 'eval', 'exec', 'compile', '__import__',
        'open', 'file', 'input', 'raw_input', 'execfile'
    }

    def __init__(
        self,
        memory_limit_mb: int = 256,
        timeout_seconds: int = 300,
        audit_logger = None
    ):
        """
        Initialize safe execution environment

        Args:
            memory_limit_mb: Maximum memory in MB
            timeout_seconds: Maximum execution time in seconds
            audit_logger: Audit logger instance
        """
        self.memory_limit_mb = memory_limit_mb
        self.timeout_seconds = timeout_seconds
        self.audit_logger = audit_logger
        self.execution_count = 0

    def execute_code(
        self,
        code: str,
        user_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute Python code in restricted environment

        Args:
            code: Python code to execute
            user_id: User ID for audit logging
            context: Optional context variables

        Returns:
            Execution result dictionary
        """
        self.execution_count += 1
        execution_id = f"{user_id}_{int(time.time())}_{self.execution_count}"

        # Log execution attempt
        if self.audit_logger:
            self.audit_logger.log_execution_attempt(
                action='safe_exec',
                user_id=user_id,
                payload_type='python_code',
                payload_data={'code': code[:100], 'execution_id': execution_id},
                approved=True,
                blocked=False,
                reason='Safe execution environment'
            )

        # Validate code first
        validation_result = self._validate_code(code)
        if not validation_result['valid']:
            if self.audit_logger:
                self.audit_logger.log_violation(
                    'unsafe_code_detected',
                    user_id,
                    {
                        'execution_id': execution_id,
                        'violations': validation_result['violations']
                    },
                    severity='high'
                )
            return {
                'success': False,
                'error': 'Code validation failed',
                'violations': validation_result['violations'],
                'blocked': True
            }

        # Execute in restricted environment
        try:
            result = self._execute_restricted(code, context or {}, user_id, execution_id)
            return result
        except Exception as e:
            if self.audit_logger:
                self.audit_logger.log_violation(
                    'execution_exception',
                    user_id,
                    {
                        'execution_id': execution_id,
                        'error': str(e)
                    },
                    severity='medium'
                )
            return {
                'success': False,
                'error': str(e),
                'type': type(e).__name__
            }

    def _validate_code(self, code: str) -> Dict[str, Any]:
        """
        Validate code for security violations

        Args:
            code: Code to validate

        Returns:
            Validation result with 'valid' and 'violations'
        """
        violations = []

        # Check for blocked keywords
        dangerous_keywords = [
            'import os', 'import sys', 'import subprocess', '__import__',
            'eval(', 'exec(', 'compile(', 'open(', 'file(',
            'os.system', 'subprocess.', 'socket.', 'urllib.',
            'execfile', 'input(', 'raw_input('
        ]

        code_lower = code.lower()
        for keyword in dangerous_keywords:
            if keyword.lower() in code_lower:
                violations.append(f'Blocked keyword detected: {keyword}')

        # Check for potential code injection patterns
        injection_patterns = [
            '__builtins__', '__globals__', '__locals__',
            'globals()', 'locals()', 'vars()',
            '__code__', '__class__', '__bases__',
            'getattr', 'setattr', 'delattr', 'hasattr'
        ]

        for pattern in injection_patterns:
            if pattern.lower() in code_lower:
                violations.append(f'Potential injection pattern: {pattern}')

        return {
            'valid': len(violations) == 0,
            'violations': violations
        }

    def _execute_restricted(
        self,
        code: str,
        context: Dict[str, Any],
        user_id: str,
        execution_id: str
    ) -> Dict[str, Any]:
        """
        Execute code in restricted Python interpreter

        Args:
            code: Code to execute
            context: Execution context
            user_id: User ID
            execution_id: Execution ID

        Returns:
            Execution result
        """
        # Create restricted globals
        restricted_globals = self._create_restricted_globals()

        # Add context variables
        restricted_globals.update(context)

        # Capture stdout/stderr
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()

        # Set resource limits (Unix only)
        if sys.platform != 'win32':
            try:
                # Memory limit
                memory_limit_bytes = self.memory_limit_mb * 1024 * 1024
                resource.setrlimit(resource.RLIMIT_AS, (memory_limit_bytes, memory_limit_bytes))

                # CPU time limit
                resource.setrlimit(resource.RLIMIT_CPU, (self.timeout_seconds, self.timeout_seconds))
            except Exception as e:
                print(f"[!] Warning: Could not set resource limits: {e}")

        # Execute with timeout
        result = {'success': False, 'output': '', 'error': '', 'timeout': False}

        def execute_with_timeout():
            try:
                with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                    # Compile code first (safer than direct exec)
                    compiled_code = compile(code, '<string>', 'exec')

                    # Execute compiled code
                    exec(compiled_code, restricted_globals, {})

                    result['success'] = True
                    result['output'] = stdout_capture.getvalue()
                    result['error'] = stderr_capture.getvalue()
            except Exception as e:
                result['success'] = False
                result['error'] = f"{type(e).__name__}: {str(e)}"
                result['output'] = stdout_capture.getvalue()

        # Run in thread with timeout
        execution_thread = threading.Thread(target=execute_with_timeout)
        execution_thread.daemon = True
        execution_thread.start()
        execution_thread.join(timeout=self.timeout_seconds)

        if execution_thread.is_alive():
            # Timeout occurred
            result['timeout'] = True
            result['error'] = f'Execution timeout ({self.timeout_seconds}s)'

            if self.audit_logger:
                self.audit_logger.log_violation(
                    'execution_timeout',
                    user_id,
                    {'execution_id': execution_id, 'timeout': self.timeout_seconds},
                    severity='medium'
                )

        return result

    def _create_restricted_globals(self) -> Dict[str, Any]:
        """
        Create restricted global namespace with limited builtins

        Returns:
            Restricted globals dictionary
        """
        # Start with minimal builtins
        safe_builtins = {}

        import builtins
        for name in self.ALLOWED_BUILTINS:
            if hasattr(builtins, name):
                safe_builtins[name] = getattr(builtins, name)

        # Create custom __import__ that only allows safe modules
        def safe_import(name, *args, **kwargs):
            if name in self.BLOCKED_IMPORTS:
                raise ImportError(f"Import of '{name}' is not allowed")
            if name not in self.ALLOWED_MODULES:
                raise ImportError(f"Import of '{name}' is not allowed. Allowed modules: {', '.join(self.ALLOWED_MODULES)}")
            return __import__(name, *args, **kwargs)

        safe_builtins['__import__'] = safe_import

        # Return restricted globals
        return {
            '__builtins__': safe_builtins,
            '__name__': '__main__',
            '__doc__': None
        }

    def get_allowed_modules(self) -> Set[str]:
        """Get set of allowed modules"""
        return self.ALLOWED_MODULES.copy()

    def get_allowed_builtins(self) -> Set[str]:
        """Get set of allowed builtin functions"""
        return self.ALLOWED_BUILTINS.copy()


class RestrictedFile:
    """
    Read-only file wrapper for safe execution environment
    Prevents write operations
    """

    def __init__(self, filepath: str, mode: str = 'r'):
        """
        Initialize restricted file

        Args:
            filepath: Path to file
            mode: File mode (only 'r' allowed)
        """
        if 'w' in mode or 'a' in mode or '+' in mode:
            raise PermissionError("Write access not allowed in safe execution environment")

        # Only allow reading from specific safe directories
        safe_dirs = ['/tmp', '/var/log']
        import os
        abs_path = os.path.abspath(filepath)

        if not any(abs_path.startswith(safe_dir) for safe_dir in safe_dirs):
            raise PermissionError(f"File access not allowed: {filepath}")

        self.file = open(filepath, mode)

    def __enter__(self):
        return self.file

    def __exit__(self, *args):
        return self.file.__exit__(*args)

    def read(self, *args, **kwargs):
        return self.file.read(*args, **kwargs)

    def readline(self, *args, **kwargs):
        return self.file.readline(*args, **kwargs)

    def readlines(self, *args, **kwargs):
        return self.file.readlines(*args, **kwargs)

    def write(self, *args, **kwargs):
        raise PermissionError("Write access not allowed")

    def close(self):
        return self.file.close()


# Global safe execution environment
_global_safe_env = None


def get_safe_exec_env() -> SafeExecEnvironment:
    """Get global safe execution environment instance"""
    global _global_safe_env
    if _global_safe_env is None:
        from audit_logger import get_audit_logger
        _global_safe_env = SafeExecEnvironment(audit_logger=get_audit_logger())
    return _global_safe_env


def execute_safe(code: str, user_id: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Convenience function to execute code safely

    Args:
        code: Python code to execute
        user_id: User ID
        context: Optional context variables

    Returns:
        Execution result
    """
    return get_safe_exec_env().execute_code(code, user_id, context)
