#!/usr/bin/env python3
"""
Safe Subprocess Wrapper - Secure subprocess execution without shell=True
All subprocess calls MUST use shell=False and proper argument lists
"""

import subprocess
from typing import List, Dict, Any, Optional, Union
from parameter_sanitizer import ParameterSanitizer, ValidationError


class SafeSubprocess:
    """Wrapper for safe subprocess execution"""

    @staticmethod
    def run(
        command: List[str],
        timeout: int = 30,
        capture_output: bool = True,
        check: bool = False,
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Safely execute a command using subprocess.run with shell=False

        Args:
            command: List of command arguments (NOT a string)
            timeout: Command timeout in seconds
            capture_output: Whether to capture stdout/stderr
            check: Whether to raise exception on non-zero exit
            cwd: Working directory
            env: Environment variables

        Returns:
            Dict with stdout, stderr, exit_status, command

        Raises:
            ValidationError: If command validation fails
            subprocess.TimeoutExpired: If command times out
        """
        # Validate command is a list
        if not isinstance(command, list):
            raise ValidationError(f"Command must be a list, got {type(command).__name__}")

        if len(command) == 0:
            raise ValidationError("Command list cannot be empty")

        # Validate each argument is a string
        for i, arg in enumerate(command):
            if not isinstance(arg, str):
                raise ValidationError(f"Command argument {i} must be string, got {type(arg).__name__}")

        # Validate first argument (the executable) exists or is a known command
        executable = command[0]
        if not SafeSubprocess._is_safe_executable(executable):
            raise ValidationError(f"Executable not allowed or not found: {executable}")

        # Validate working directory if provided
        if cwd:
            cwd = ParameterSanitizer.validate_file_path(cwd, must_exist=True)

        # Validate environment variables if provided
        if env:
            if not isinstance(env, dict):
                raise ValidationError("Environment must be a dictionary")
            for key, value in env.items():
                if not isinstance(key, str) or not isinstance(value, str):
                    raise ValidationError("Environment variables must be strings")

        try:
            # Execute with shell=False (CRITICAL!)
            result = subprocess.run(
                command,
                shell=False,  # NEVER use shell=True
                capture_output=capture_output,
                text=True,
                timeout=timeout,
                check=check,
                cwd=cwd,
                env=env
            )

            return {
                'command': command,
                'stdout': result.stdout if capture_output else '',
                'stderr': result.stderr if capture_output else '',
                'exit_status': result.returncode,
                'success': result.returncode == 0
            }

        except subprocess.TimeoutExpired as e:
            return {
                'command': command,
                'error': 'Command timed out',
                'timeout': timeout,
                'stdout': e.stdout.decode() if e.stdout else '',
                'stderr': e.stderr.decode() if e.stderr else '',
                'exit_status': -1,
                'success': False
            }

        except subprocess.CalledProcessError as e:
            return {
                'command': command,
                'error': f'Command failed with exit code {e.returncode}',
                'stdout': e.stdout if capture_output else '',
                'stderr': e.stderr if capture_output else '',
                'exit_status': e.returncode,
                'success': False
            }

        except FileNotFoundError as e:
            return {
                'command': command,
                'error': f'Executable not found: {executable}',
                'exit_status': -1,
                'success': False
            }

        except Exception as e:
            return {
                'command': command,
                'error': f'Unexpected error: {str(e)}',
                'exit_status': -1,
                'success': False
            }

    @staticmethod
    def _is_safe_executable(executable: str) -> bool:
        """
        Check if executable is safe to run
        Validates against whitelist of known security tools
        """
        # Whitelist of allowed executables
        safe_executables = [
            # Network tools
            'nmap', 'netcat', 'nc', 'ncat', 'netstat', 'ping', 'traceroute',
            'dig', 'nslookup', 'host', 'whois', 'tcpdump', 'wireshark',

            # Security tools
            'sqlmap', 'hashcat', 'john', 'hydra', 'nikto', 'dirb', 'gobuster',
            'wpscan', 'metasploit', 'msfconsole', 'burpsuite',

            # System tools
            'ps', 'tasklist', 'systemctl', 'service', 'netsh',
            'wevtutil', 'ipconfig', 'ifconfig', 'ip', 'route',
            'ls', 'dir', 'cat', 'grep', 'find', 'which', 'whereis',
            'echo', 'printf', 'date', 'uname', 'hostname',

            # Tunneling
            'ssh', 'scp', 'sftp', 'openvpn', 'wireguard', 'wg',

            # Other
            'python', 'python3', 'bash', 'sh', 'powershell', 'cmd',
        ]

        # Check if executable is in whitelist
        executable_name = executable.split('/')[-1].split('\\')[-1]

        # Remove .exe extension on Windows
        if executable_name.endswith('.exe'):
            executable_name = executable_name[:-4]

        return executable_name.lower() in safe_executables

    @staticmethod
    def run_with_input(
        command: List[str],
        input_data: str,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Safely execute a command with stdin input

        Args:
            command: List of command arguments
            input_data: Data to send to stdin
            timeout: Command timeout in seconds

        Returns:
            Dict with stdout, stderr, exit_status, command
        """
        if not isinstance(command, list):
            raise ValidationError(f"Command must be a list, got {type(command).__name__}")

        if not isinstance(input_data, str):
            raise ValidationError(f"Input data must be string, got {type(input_data).__name__}")

        try:
            result = subprocess.run(
                command,
                shell=False,  # NEVER use shell=True
                input=input_data,
                capture_output=True,
                text=True,
                timeout=timeout
            )

            return {
                'command': command,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'exit_status': result.returncode,
                'success': result.returncode == 0
            }

        except subprocess.TimeoutExpired:
            return {
                'command': command,
                'error': 'Command timed out',
                'timeout': timeout,
                'exit_status': -1,
                'success': False
            }

        except Exception as e:
            return {
                'command': command,
                'error': str(e),
                'exit_status': -1,
                'success': False
            }

    @staticmethod
    def check_tool_available(tool_name: str) -> bool:
        """
        Check if a security tool is available on the system

        Args:
            tool_name: Name of the tool to check

        Returns:
            True if tool is available, False otherwise
        """
        import shutil
        return shutil.which(tool_name) is not None

    @staticmethod
    def get_tool_version(tool_name: str) -> Optional[str]:
        """
        Get version of a security tool

        Args:
            tool_name: Name of the tool

        Returns:
            Version string or None if not available
        """
        if not SafeSubprocess.check_tool_available(tool_name):
            return None

        # Try common version flags
        version_flags = ['--version', '-version', '-v', '-V']

        for flag in version_flags:
            try:
                result = SafeSubprocess.run([tool_name, flag], timeout=5)
                if result.get('success'):
                    return result.get('stdout', '').strip()
            except:
                continue

        return None


class CommandBuilder:
    """Helper class to build safe command lists"""

    def __init__(self, executable: str):
        """
        Initialize command builder

        Args:
            executable: The executable to run
        """
        self.command = [executable]

    def add_arg(self, arg: str, value: Optional[str] = None) -> 'CommandBuilder':
        """
        Add an argument to the command

        Args:
            arg: The argument flag (e.g., '-p')
            value: Optional value for the argument

        Returns:
            Self for chaining
        """
        if not isinstance(arg, str):
            raise ValidationError(f"Argument must be string, got {type(arg).__name__}")

        self.command.append(arg)

        if value is not None:
            if not isinstance(value, str):
                raise ValidationError(f"Value must be string, got {type(value).__name__}")
            self.command.append(value)

        return self

    def add_args(self, *args: str) -> 'CommandBuilder':
        """
        Add multiple arguments to the command

        Args:
            *args: Arguments to add

        Returns:
            Self for chaining
        """
        for arg in args:
            if not isinstance(arg, str):
                raise ValidationError(f"Argument must be string, got {type(arg).__name__}")
            self.command.append(arg)

        return self

    def add_target(self, target: str) -> 'CommandBuilder':
        """
        Add target (IP/hostname) to the command

        Args:
            target: Target IP or hostname

        Returns:
            Self for chaining
        """
        # Validate target
        try:
            target = ParameterSanitizer.validate_ip(target)
        except ValidationError:
            target = ParameterSanitizer.validate_hostname(target)

        self.command.append(target)
        return self

    def add_port(self, port: Union[int, str]) -> 'CommandBuilder':
        """
        Add port to the command

        Args:
            port: Port number

        Returns:
            Self for chaining
        """
        port = ParameterSanitizer.validate_port(port)
        self.command.append(str(port))
        return self

    def add_port_range(self, port_range: str) -> 'CommandBuilder':
        """
        Add port range to the command

        Args:
            port_range: Port range (e.g., "80,443,8000-9000")

        Returns:
            Self for chaining
        """
        port_range = ParameterSanitizer.validate_port_range(port_range)
        self.command.append(port_range)
        return self

    def add_file_path(self, file_path: str, must_exist: bool = False) -> 'CommandBuilder':
        """
        Add file path to the command

        Args:
            file_path: Path to file
            must_exist: Whether file must exist

        Returns:
            Self for chaining
        """
        file_path = ParameterSanitizer.validate_file_path(file_path, must_exist=must_exist)
        self.command.append(file_path)
        return self

    def build(self) -> List[str]:
        """
        Build the command list

        Returns:
            Complete command as list
        """
        return self.command.copy()

    def execute(self, timeout: int = 30) -> Dict[str, Any]:
        """
        Build and execute the command

        Args:
            timeout: Command timeout in seconds

        Returns:
            Result dictionary
        """
        return SafeSubprocess.run(self.command, timeout=timeout)
