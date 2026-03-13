#!/usr/bin/env python3
"""
Education Sandbox - Firejail/Docker Wrapper for Maximum Security
Provides containerized execution environment for education tier
"""

import os
import subprocess
import tempfile
import shutil
import time
import hashlib
from typing import Dict, Any, Optional, List
from pathlib import Path


class EducationSandbox:
    """
    Sandbox execution using firejail or Docker for maximum isolation

    Features:
    - Isolated file system (read-only /ghostops/payloads/)
    - No network access
    - CPU/memory limits
    - Timeout enforcement (5 min max)
    - No access to system files
    - All execution in temporary containers
    """

    def __init__(
        self,
        use_firejail: bool = True,
        use_docker: bool = False,
        timeout_seconds: int = 300,
        memory_limit_mb: int = 256,
        cpu_limit_percent: int = 50,
        audit_logger = None
    ):
        """
        Initialize education sandbox

        Args:
            use_firejail: Use firejail for sandboxing
            use_docker: Use Docker for sandboxing
            timeout_seconds: Maximum execution time
            memory_limit_mb: Memory limit in MB
            cpu_limit_percent: CPU usage limit
            audit_logger: Audit logger instance
        """
        self.use_firejail = use_firejail and self._check_firejail()
        self.use_docker = use_docker and self._check_docker()
        self.timeout_seconds = timeout_seconds
        self.memory_limit_mb = memory_limit_mb
        self.cpu_limit_percent = cpu_limit_percent
        self.audit_logger = audit_logger

        # Verify at least one sandbox method is available
        if not self.use_firejail and not self.use_docker:
            print("[!] Warning: No sandbox method available (firejail/docker not found)")
            print("[!] Falling back to restricted subprocess execution")

    def _check_firejail(self) -> bool:
        """Check if firejail is available"""
        try:
            result = subprocess.run(
                ['firejail', '--version'],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def _check_docker(self) -> bool:
        """Check if Docker is available"""
        try:
            result = subprocess.run(
                ['docker', '--version'],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def execute_sandboxed(
        self,
        code: str,
        user_id: str,
        language: str = 'python',
        allowed_files: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Execute code in sandboxed environment

        Args:
            code: Code to execute
            user_id: User ID for audit logging
            language: Programming language (python, bash)
            allowed_files: List of files to make available

        Returns:
            Execution result dictionary
        """
        sandbox_id = self._generate_sandbox_id(user_id)

        # Log sandbox start
        if self.audit_logger:
            self.audit_logger.log_sandbox_event(
                'start',
                user_id,
                sandbox_id,
                {
                    'language': language,
                    'code_length': len(code),
                    'timeout': self.timeout_seconds
                }
            )

        try:
            # Choose sandbox method
            if self.use_firejail:
                result = self._execute_firejail(code, user_id, sandbox_id, language, allowed_files)
            elif self.use_docker:
                result = self._execute_docker(code, user_id, sandbox_id, language, allowed_files)
            else:
                result = self._execute_restricted(code, user_id, sandbox_id, language, allowed_files)

            # Log sandbox stop
            if self.audit_logger:
                self.audit_logger.log_sandbox_event(
                    'stop',
                    user_id,
                    sandbox_id,
                    {
                        'success': result.get('success', False),
                        'runtime': result.get('runtime', 0)
                    }
                )

            return result

        except Exception as e:
            # Log sandbox error
            if self.audit_logger:
                self.audit_logger.log_sandbox_event(
                    'error',
                    user_id,
                    sandbox_id,
                    {'error': str(e)}
                )
            return {
                'success': False,
                'error': str(e),
                'sandbox_id': sandbox_id
            }

    def _execute_firejail(
        self,
        code: str,
        user_id: str,
        sandbox_id: str,
        language: str,
        allowed_files: Optional[List[str]]
    ) -> Dict[str, Any]:
        """
        Execute code using firejail sandbox

        Args:
            code: Code to execute
            user_id: User ID
            sandbox_id: Sandbox ID
            language: Programming language
            allowed_files: Allowed files

        Returns:
            Execution result
        """
        # Create temporary directory for execution
        temp_dir = tempfile.mkdtemp(prefix=f'sandbox_{sandbox_id}_')

        try:
            # Write code to temporary file
            if language == 'python':
                script_file = Path(temp_dir) / 'script.py'
                interpreter = 'python3'
            elif language == 'bash':
                script_file = Path(temp_dir) / 'script.sh'
                interpreter = 'bash'
            else:
                return {
                    'success': False,
                    'error': f'Unsupported language: {language}'
                }

            script_file.write_text(code)

            # Copy allowed files to temp directory
            if allowed_files:
                for filepath in allowed_files:
                    if os.path.exists(filepath):
                        shutil.copy2(filepath, temp_dir)

            # Build firejail command
            firejail_cmd = [
                'firejail',
                '--quiet',
                '--noprofile',
                '--net=none',  # No network access
                '--private=' + temp_dir,  # Private temporary directory
                '--read-only=/ghostops/payloads',  # Read-only payloads directory
                '--nosound',  # No sound
                '--novideo',  # No video
                '--no3d',  # No 3D acceleration
                '--nodvd',  # No DVD
                '--notv',  # No TV
                '--nou2f',  # No U2F
                '--nodbus',  # No D-Bus
                f'--rlimit-as={self.memory_limit_mb}M',  # Memory limit
                f'--rlimit-cpu={self.timeout_seconds}',  # CPU time limit
                '--caps.drop=all',  # Drop all capabilities
                '--seccomp',  # Enable seccomp
                '--nonewprivs',  # Prevent privilege escalation
                interpreter,
                str(script_file)
            ]

            # Execute with timeout
            start_time = time.time()
            result = subprocess.run(
                firejail_cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds
            )
            runtime = time.time() - start_time

            return {
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'exit_code': result.returncode,
                'runtime': runtime,
                'sandbox_id': sandbox_id,
                'sandbox_method': 'firejail'
            }

        except subprocess.TimeoutExpired:
            if self.audit_logger:
                self.audit_logger.log_sandbox_event(
                    'timeout',
                    user_id,
                    sandbox_id,
                    {'timeout': self.timeout_seconds}
                )
            return {
                'success': False,
                'error': f'Execution timeout ({self.timeout_seconds}s)',
                'sandbox_id': sandbox_id,
                'timeout': True
            }

        finally:
            # Clean up temporary directory
            try:
                shutil.rmtree(temp_dir)
            except Exception as e:
                print(f"[!] Warning: Could not remove temp dir {temp_dir}: {e}")

    def _execute_docker(
        self,
        code: str,
        user_id: str,
        sandbox_id: str,
        language: str,
        allowed_files: Optional[List[str]]
    ) -> Dict[str, Any]:
        """
        Execute code using Docker container

        Args:
            code: Code to execute
            user_id: User ID
            sandbox_id: Sandbox ID
            language: Programming language
            allowed_files: Allowed files

        Returns:
            Execution result
        """
        # Create temporary directory for execution
        temp_dir = tempfile.mkdtemp(prefix=f'docker_sandbox_{sandbox_id}_')

        try:
            # Write code to temporary file
            if language == 'python':
                script_file = Path(temp_dir) / 'script.py'
                image = 'python:3.11-alpine'
                command = ['python3', '/workspace/script.py']
            elif language == 'bash':
                script_file = Path(temp_dir) / 'script.sh'
                image = 'alpine:latest'
                command = ['sh', '/workspace/script.sh']
            else:
                return {
                    'success': False,
                    'error': f'Unsupported language: {language}'
                }

            script_file.write_text(code)

            # Copy allowed files
            if allowed_files:
                for filepath in allowed_files:
                    if os.path.exists(filepath):
                        shutil.copy2(filepath, temp_dir)

            # Build Docker command
            docker_cmd = [
                'docker', 'run',
                '--rm',  # Remove container after execution
                '--network=none',  # No network access
                '--read-only',  # Read-only root filesystem
                '--tmpfs', '/tmp:rw,noexec,nosuid,size=64m',  # Temporary filesystem
                f'--memory={self.memory_limit_mb}m',  # Memory limit
                f'--cpus={self.cpu_limit_percent / 100.0}',  # CPU limit
                '--security-opt=no-new-privileges',  # No privilege escalation
                '--cap-drop=ALL',  # Drop all capabilities
                '-v', f'{temp_dir}:/workspace:ro',  # Mount workspace read-only
                '-w', '/workspace',
                image
            ] + command

            # Execute with timeout
            start_time = time.time()
            result = subprocess.run(
                docker_cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds
            )
            runtime = time.time() - start_time

            return {
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'exit_code': result.returncode,
                'runtime': runtime,
                'sandbox_id': sandbox_id,
                'sandbox_method': 'docker'
            }

        except subprocess.TimeoutExpired:
            if self.audit_logger:
                self.audit_logger.log_sandbox_event(
                    'timeout',
                    user_id,
                    sandbox_id,
                    {'timeout': self.timeout_seconds}
                )

            # Kill the container
            try:
                subprocess.run(['docker', 'ps', '-q', '-f', f'name={sandbox_id}'], timeout=5)
                subprocess.run(['docker', 'kill', sandbox_id], timeout=5)
            except:
                pass

            return {
                'success': False,
                'error': f'Execution timeout ({self.timeout_seconds}s)',
                'sandbox_id': sandbox_id,
                'timeout': True
            }

        finally:
            # Clean up temporary directory
            try:
                shutil.rmtree(temp_dir)
            except Exception as e:
                print(f"[!] Warning: Could not remove temp dir {temp_dir}: {e}")

    def _execute_restricted(
        self,
        code: str,
        user_id: str,
        sandbox_id: str,
        language: str,
        allowed_files: Optional[List[str]]
    ) -> Dict[str, Any]:
        """
        Fallback: Execute with basic restrictions (no firejail/docker)

        Args:
            code: Code to execute
            user_id: User ID
            sandbox_id: Sandbox ID
            language: Programming language
            allowed_files: Allowed files

        Returns:
            Execution result
        """
        # Use SafeExecEnvironment for Python
        if language == 'python':
            from safe_exec_environment import execute_safe
            return execute_safe(code, user_id)

        # For bash, use basic subprocess with restrictions
        temp_dir = tempfile.mkdtemp(prefix=f'restricted_sandbox_{sandbox_id}_')

        try:
            script_file = Path(temp_dir) / 'script.sh'
            script_file.write_text(code)

            # Execute with minimal privileges
            start_time = time.time()
            result = subprocess.run(
                ['bash', str(script_file)],
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                cwd=temp_dir,
                env={'PATH': '/usr/bin:/bin'}  # Minimal PATH
            )
            runtime = time.time() - start_time

            return {
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'exit_code': result.returncode,
                'runtime': runtime,
                'sandbox_id': sandbox_id,
                'sandbox_method': 'restricted',
                'warning': 'Executed without full sandboxing (firejail/docker not available)'
            }

        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': f'Execution timeout ({self.timeout_seconds}s)',
                'sandbox_id': sandbox_id,
                'timeout': True
            }

        finally:
            try:
                shutil.rmtree(temp_dir)
            except:
                pass

    def _generate_sandbox_id(self, user_id: str) -> str:
        """Generate unique sandbox ID"""
        return hashlib.sha256(f"{user_id}_{time.time()}".encode()).hexdigest()[:16]


# Global sandbox instance
_global_sandbox = None


def get_sandbox() -> EducationSandbox:
    """Get global sandbox instance"""
    global _global_sandbox
    if _global_sandbox is None:
        from audit_logger import get_audit_logger
        _global_sandbox = EducationSandbox(audit_logger=get_audit_logger())
    return _global_sandbox


def execute_in_sandbox(
    code: str,
    user_id: str,
    language: str = 'python',
    allowed_files: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Convenience function to execute code in sandbox

    Args:
        code: Code to execute
        user_id: User ID
        language: Programming language
        allowed_files: Allowed files

    Returns:
        Execution result
    """
    return get_sandbox().execute_sandboxed(code, user_id, language, allowed_files)
