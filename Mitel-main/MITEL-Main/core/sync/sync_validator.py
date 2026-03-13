#!/usr/bin/env python3
"""
GhostOps Sync Validator Module
Validates file sync operations to prevent path traversal and unauthorized access
"""

import os
import re
from safe_path import validate_sync_path, log_blocked_access
from file_handler import SafeFileHandler


# Whitelist of files allowed for sync (core files only)
ALLOWED_SYNC_FILES = [
    'ghostops_core.py',
    'ghostops_adapter.py',
    'ex_api.py',
    'file_sharing.py',
    'kali.py',
    'windows.py',
    'android.py',
    'activate_tunnel.py',
    'mesh_manager.py',
    # Security modules
    'safe_path.py',
    'path_sanitizer.py',
    'file_handler.py',
    'upload_handler.py',
    'sync_validator.py'
]

# Allowed sync directories (relative paths only)
ALLOWED_SYNC_DIRS = [
    '.',  # Current directory for core files
    'tools',  # Tool outputs
    'data',  # Data files
]


class SyncValidator:
    """
    Validates file synchronization operations
    """

    def __init__(self, allowed_files=None, allowed_dirs=None, strict_mode=True):
        """
        Initialize sync validator

        Args:
            allowed_files: List of allowed filenames (default: ALLOWED_SYNC_FILES)
            allowed_dirs: List of allowed directories (default: ALLOWED_SYNC_DIRS)
            strict_mode: Whether to enforce strict validation (default: True)
        """
        self.allowed_files = allowed_files or ALLOWED_SYNC_FILES
        self.allowed_dirs = allowed_dirs or ALLOWED_SYNC_DIRS
        self.strict_mode = strict_mode
        self.file_handler = SafeFileHandler(allowed_base_dir='.')

    def validate_sync_request(self, sync_path, source="unknown"):
        """
        Validate a file sync request

        Args:
            sync_path: Path requested for sync
            source: Source of sync request

        Returns:
            Validated path if safe

        Raises:
            ValueError: If sync request is invalid or dangerous
        """
        # Convert to string if needed
        if not isinstance(sync_path, str):
            sync_path = str(sync_path)

        print(f"[SYNC] Validating sync request: {sync_path} from {source}")

        # Security Check 1: Must be relative path (not absolute)
        if os.path.isabs(sync_path):
            error = f"Absolute paths not allowed in sync: {sync_path}"
            log_blocked_access(sync_path, error, source)
            raise ValueError(error)

        # Security Check 2: Block path traversal patterns
        if ".." in sync_path or sync_path.startswith("/"):
            error = f"Path traversal blocked in sync: {sync_path}"
            log_blocked_access(sync_path, error, source)
            raise ValueError(error)

        # Security Check 3: Only allow safe characters
        if not re.match(r'^[a-zA-Z0-9_\-./]+$', sync_path):
            error = f"Invalid characters in sync path: {sync_path}"
            log_blocked_access(sync_path, error, source)
            raise ValueError(error)

        # Security Check 4: Extract filename and directory
        filename = os.path.basename(sync_path)
        dirname = os.path.dirname(sync_path) or '.'

        # Security Check 5: Validate directory is in allowlist
        if self.strict_mode:
            # In strict mode, only allow specific directories
            if dirname not in self.allowed_dirs:
                error = f"Sync directory not allowed: {dirname} (allowed: {self.allowed_dirs})"
                log_blocked_access(sync_path, error, source)
                raise ValueError(error)
        else:
            # In non-strict mode, block only known dangerous directories
            dangerous_dirs = ['/etc', '/root', '/sys', '/proc', '/dev', '/home', '/Users']
            for dangerous in dangerous_dirs:
                if dirname.startswith(dangerous):
                    error = f"Dangerous sync directory blocked: {dirname}"
                    log_blocked_access(sync_path, error, source)
                    raise ValueError(error)

        # Security Check 6: Validate filename is in allowlist (for core files)
        if dirname == '.' and self.strict_mode:
            # Root directory - only allow core files
            if filename not in self.allowed_files:
                error = f"File not in sync whitelist: {filename}"
                log_blocked_access(sync_path, error, source)
                raise ValueError(error)

        # Security Check 7: Use path validator for final check
        try:
            validated_path = validate_sync_path(sync_path)
        except ValueError as e:
            log_blocked_access(sync_path, str(e), source)
            raise

        print(f"[SYNC] ✓ Sync validated: {sync_path} → {validated_path}")
        return validated_path

    def validate_sync_batch(self, file_list, source="unknown"):
        """
        Validate a batch of files for sync

        Args:
            file_list: List of file paths to sync
            source: Source of sync request

        Returns:
            Dict with validated files and blocked files
        """
        results = {
            'validated': [],
            'blocked': [],
            'total': len(file_list)
        }

        for file_path in file_list:
            try:
                validated = self.validate_sync_request(file_path, source)
                results['validated'].append({
                    'original': file_path,
                    'validated': validated
                })
            except ValueError as e:
                results['blocked'].append({
                    'path': file_path,
                    'reason': str(e)
                })

        print(f"[SYNC] Batch validation: {len(results['validated'])} allowed, "
              f"{len(results['blocked'])} blocked")

        return results

    def validate_file_info(self, file_info, source="unknown"):
        """
        Validate file info structure for sync

        Args:
            file_info: Dict with file information from peer
            source: Source of sync request

        Returns:
            Validated and sanitized file info

        Raises:
            ValueError: If file info is invalid
        """
        if not isinstance(file_info, dict):
            raise ValueError("File info must be a dictionary")

        validated_info = {}

        for filename, info in file_info.items():
            try:
                # Validate the filename/path
                validated_path = self.validate_sync_request(filename, source)

                # Validate the info structure
                if not isinstance(info, dict):
                    print(f"[SYNC] Warning: Invalid info for {filename}")
                    continue

                # Extract and validate fields
                validated_info[validated_path] = {
                    'version': info.get('version', 0),
                    'size': info.get('size', 0),
                    'hash': info.get('hash', None)
                }

                # Only include content if it exists and is valid
                if 'content' in info and info['content']:
                    # Limit content size (prevent DoS)
                    if len(info['content']) > 10 * 1024 * 1024:  # 10MB limit
                        print(f"[SYNC] Warning: Content too large for {filename}")
                        continue
                    validated_info[validated_path]['content'] = info['content']

            except ValueError as e:
                print(f"[SYNC] Blocked file in sync: {filename} - {e}")
                log_blocked_access(filename, str(e), source)
                continue

        return validated_info

    def validate_sync_write(self, file_path, content, source="unknown"):
        """
        Validate and perform a sync write operation

        Args:
            file_path: Path to write to
            content: Content to write
            source: Source of sync request

        Returns:
            True if successful

        Raises:
            ValueError: If validation fails
        """
        # Validate the sync path
        validated_path = self.validate_sync_request(file_path, source)

        # Use safe file handler to write
        return self.file_handler.write_file(validated_path, content, source=source)

    def get_allowed_files_info(self):
        """
        Get file info for all allowed sync files

        Returns:
            Dict with file info for allowed files
        """
        files_info = {}

        for filename in self.allowed_files:
            try:
                info = self.file_handler.get_file_info(filename, source="sync")
                if info and info.get('exists'):
                    files_info[filename] = info
                else:
                    # File doesn't exist - mark with version 0
                    files_info[filename] = {
                        'exists': False,
                        'version': 0,
                        'size': 0,
                        'hash': None
                    }
            except Exception as e:
                print(f"[SYNC] Error getting info for {filename}: {e}")
                continue

        return files_info


def create_sync_validator(allowed_files=None, allowed_dirs=None, strict_mode=True):
    """
    Factory function to create a SyncValidator

    Args:
        allowed_files: List of allowed filenames
        allowed_dirs: List of allowed directories
        strict_mode: Whether to enforce strict validation

    Returns:
        SyncValidator instance
    """
    return SyncValidator(
        allowed_files=allowed_files,
        allowed_dirs=allowed_dirs,
        strict_mode=strict_mode
    )


if __name__ == "__main__":
    # Test cases
    print("=== Sync Validator Test Cases ===\n")

    validator = SyncValidator(strict_mode=True)

    test_cases = [
        # Should BLOCK
        ("../../../etc/passwd", False, "Path traversal with ../"),
        ("/etc/passwd", False, "Absolute path"),
        ("../../malware.py", False, "Multiple path traversal"),
        ("~/.ssh/id_rsa", False, "User directory access"),
        ("/root/.bashrc", False, "Root directory access"),
        ("malicious<script>.py", False, "Invalid characters"),
        ("unknown_file.py", False, "Not in whitelist"),

        # Should ALLOW
        ("ghostops_core.py", True, "Core file in whitelist"),
        ("kali.py", True, "Platform file in whitelist"),
        ("safe_path.py", True, "Security module in whitelist"),
        ("tools/nmap.txt", True, "Tool output in allowed dir"),
        ("data/results.json", True, "Data file in allowed dir"),
    ]

    print("Sync Path Validation Tests:")
    for path, should_pass, description in test_cases:
        try:
            result = validator.validate_sync_request(path, source="test")
            status = "✓ ALLOWED" if should_pass else "✗ FAILED (should block)"
            print(f"{status}: {description}")
            print(f"  Path: {path}")
            print(f"  Validated: {result}")
        except ValueError as e:
            status = "✓ BLOCKED" if not should_pass else "✗ FAILED (should allow)"
            print(f"{status}: {description}")
            print(f"  Path: {path}")
            print(f"  Reason: {e}")
        print()

    print("\nBatch Validation Test:")
    batch = [
        "ghostops_core.py",
        "kali.py",
        "../../../etc/passwd",  # Should block
        "tools/scan.txt",
        "/etc/shadow"  # Should block
    ]
    results = validator.validate_sync_batch(batch, source="test")
    print(f"Validated: {len(results['validated'])}")
    print(f"Blocked: {len(results['blocked'])}")
    for blocked in results['blocked']:
        print(f"  - {blocked['path']}: {blocked['reason']}")

    print("\nAllowed Files Info:")
    info = validator.get_allowed_files_info()
    print(f"Found info for {len(info)} files")
    for filename, file_info in list(info.items())[:3]:
        print(f"  {filename}: {file_info}")
