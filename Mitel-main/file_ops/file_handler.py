#!/usr/bin/env python3
"""
GhostOps Safe File Handler Module
Provides secure file operations with path validation and access controls
"""

import os
import base64
import hashlib
from safe_path import validate_file_path, log_blocked_access


class SafeFileHandler:
    """
    Safe file handler with path validation and access logging
    """

    def __init__(self, allowed_base_dir=None):
        """
        Initialize safe file handler

        Args:
            allowed_base_dir: Optional base directory to restrict operations to
        """
        self.allowed_base_dir = allowed_base_dir

    def read_file(self, file_path, source="unknown"):
        """
        Safely read a file with path validation

        Args:
            file_path: Path to file to read
            source: Source of the request (for logging)

        Returns:
            File contents as bytes, or None if file doesn't exist

        Raises:
            ValueError: If path validation fails
        """
        try:
            # Validate path
            validated_path = validate_file_path(
                file_path,
                allowed_base_dir=self.allowed_base_dir,
                mode='read'
            )

            # Check if file exists
            if not os.path.exists(validated_path):
                print(f"[!] File not found: {validated_path}")
                return None

            # Check if it's actually a file (not a directory)
            if not os.path.isfile(validated_path):
                raise ValueError(f"Not a file: {file_path}")

            # Read file
            with open(validated_path, 'rb') as f:
                content = f.read()

            print(f"[+] File read: {validated_path} ({len(content)} bytes) [source: {source}]")
            return content

        except ValueError as e:
            # Log blocked access
            log_blocked_access(file_path, str(e), source)
            raise

        except Exception as e:
            print(f"[!] Error reading file {file_path}: {e}")
            raise

    def write_file(self, file_path, content, is_base64=False, source="unknown", verify_hash=None):
        """
        Safely write a file with path validation and verification

        Args:
            file_path: Path to file to write
            content: Content to write (bytes or string)
            is_base64: Whether content is base64 encoded
            source: Source of the request (for logging)
            verify_hash: Optional SHA256 hash to verify content integrity

        Returns:
            True if successful

        Raises:
            ValueError: If path validation fails or verification fails
        """
        try:
            # Validate path
            validated_path = validate_file_path(
                file_path,
                allowed_base_dir=self.allowed_base_dir,
                mode='write'
            )

            # Decode base64 if needed
            if is_base64:
                if isinstance(content, str):
                    content = base64.b64decode(content)
                else:
                    try:
                        content = base64.b64decode(content.decode('utf-8'))
                    except:
                        content = base64.b64decode(content)

            # Ensure content is bytes
            if isinstance(content, str):
                content = content.encode('utf-8')

            # Verify hash if provided
            if verify_hash:
                actual_hash = hashlib.sha256(content).hexdigest()
                if actual_hash != verify_hash:
                    raise ValueError(
                        f"Hash verification failed: expected {verify_hash}, got {actual_hash}"
                    )

            # Ensure parent directory exists
            parent_dir = os.path.dirname(validated_path)
            if parent_dir:
                os.makedirs(parent_dir, exist_ok=True)

            # Write file atomically (write to temp then rename)
            temp_path = validated_path + '.tmp'
            try:
                with open(temp_path, 'wb') as f:
                    f.write(content)

                # Atomic replace
                if os.path.exists(validated_path):
                    os.remove(validated_path)
                os.rename(temp_path, validated_path)
            except:
                # Fallback to direct write
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                with open(validated_path, 'wb') as f:
                    f.write(content)

            # Verify file was actually written
            if not os.path.exists(validated_path):
                raise ValueError(f"File verification failed: {validated_path} does not exist after write")

            saved_size = os.path.getsize(validated_path)
            if saved_size != len(content):
                raise ValueError(
                    f"Size verification failed: expected {len(content)}, got {saved_size}"
                )

            # Verify content by reading back
            with open(validated_path, 'rb') as f:
                read_back = f.read()
            if read_back != content:
                raise ValueError("Content verification failed: file content doesn't match")

            print(f"[+] File written: {validated_path} ({saved_size} bytes) [source: {source}]")
            return True

        except ValueError as e:
            # Log blocked access
            log_blocked_access(file_path, str(e), source)
            raise

        except PermissionError as e:
            error_msg = f"Permission denied: {e}"
            log_blocked_access(file_path, error_msg, source)
            raise ValueError(error_msg)

        except Exception as e:
            print(f"[!] Error writing file {file_path}: {e}")
            import traceback
            traceback.print_exc()
            raise

    def delete_file(self, file_path, source="unknown"):
        """
        Safely delete a file with path validation

        Args:
            file_path: Path to file to delete
            source: Source of the request (for logging)

        Returns:
            True if successful

        Raises:
            ValueError: If path validation fails
        """
        try:
            # Validate path
            validated_path = validate_file_path(
                file_path,
                allowed_base_dir=self.allowed_base_dir,
                mode='write'
            )

            # Check if file exists
            if not os.path.exists(validated_path):
                print(f"[!] File not found: {validated_path}")
                return False

            # Check if it's actually a file (not a directory)
            if not os.path.isfile(validated_path):
                raise ValueError(f"Not a file: {file_path}")

            # Delete file
            os.remove(validated_path)
            print(f"[+] File deleted: {validated_path} [source: {source}]")
            return True

        except ValueError as e:
            # Log blocked access
            log_blocked_access(file_path, str(e), source)
            raise

        except Exception as e:
            print(f"[!] Error deleting file {file_path}: {e}")
            raise

    def file_exists(self, file_path, source="unknown"):
        """
        Safely check if a file exists with path validation

        Args:
            file_path: Path to check
            source: Source of the request (for logging)

        Returns:
            True if file exists, False otherwise

        Raises:
            ValueError: If path validation fails
        """
        try:
            # Validate path
            validated_path = validate_file_path(
                file_path,
                allowed_base_dir=self.allowed_base_dir,
                mode='read'
            )

            return os.path.exists(validated_path) and os.path.isfile(validated_path)

        except ValueError as e:
            # Log blocked access
            log_blocked_access(file_path, str(e), source)
            raise

    def get_file_hash(self, file_path, source="unknown"):
        """
        Calculate SHA256 hash of file with path validation

        Args:
            file_path: Path to file
            source: Source of the request (for logging)

        Returns:
            SHA256 hash as hex string, or None if file doesn't exist

        Raises:
            ValueError: If path validation fails
        """
        try:
            # Validate path
            validated_path = validate_file_path(
                file_path,
                allowed_base_dir=self.allowed_base_dir,
                mode='read'
            )

            if not os.path.exists(validated_path):
                return None

            sha256_hash = hashlib.sha256()
            with open(validated_path, 'rb') as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)

            return sha256_hash.hexdigest()

        except ValueError as e:
            # Log blocked access
            log_blocked_access(file_path, str(e), source)
            raise

        except Exception as e:
            print(f"[!] Error calculating hash for {file_path}: {e}")
            return None

    def get_file_info(self, file_path, source="unknown"):
        """
        Get file information with path validation

        Args:
            file_path: Path to file
            source: Source of the request (for logging)

        Returns:
            Dict with file info (size, mtime, hash) or None if file doesn't exist

        Raises:
            ValueError: If path validation fails
        """
        try:
            # Validate path
            validated_path = validate_file_path(
                file_path,
                allowed_base_dir=self.allowed_base_dir,
                mode='read'
            )

            if not os.path.exists(validated_path):
                return {
                    'exists': False,
                    'size': 0,
                    'version': 0,
                    'hash': None
                }

            file_hash = self.get_file_hash(file_path, source)

            return {
                'exists': True,
                'size': os.path.getsize(validated_path),
                'version': os.path.getmtime(validated_path),
                'hash': file_hash
            }

        except ValueError as e:
            # Log blocked access
            log_blocked_access(file_path, str(e), source)
            raise

        except Exception as e:
            print(f"[!] Error getting file info for {file_path}: {e}")
            return None


def get_safe_file_handler(allowed_base_dir=None):
    """
    Factory function to create a SafeFileHandler instance

    Args:
        allowed_base_dir: Optional base directory to restrict operations to

    Returns:
        SafeFileHandler instance
    """
    return SafeFileHandler(allowed_base_dir)


if __name__ == "__main__":
    # Test cases
    print("=== Safe File Handler Test Cases ===\n")

    # Create test directory
    test_dir = "/tmp/ghostops/test"
    os.makedirs(test_dir, exist_ok=True)

    handler = SafeFileHandler(allowed_base_dir="/tmp/ghostops")

    print("Write File Test:")
    try:
        handler.write_file("test/hello.txt", "Hello, World!", source="test")
        print("✓ Write successful\n")
    except Exception as e:
        print(f"✗ Write failed: {e}\n")

    print("Read File Test:")
    try:
        content = handler.read_file("test/hello.txt", source="test")
        print(f"✓ Read successful: {content}\n")
    except Exception as e:
        print(f"✗ Read failed: {e}\n")

    print("Path Traversal Test (should block):")
    try:
        handler.read_file("../../../etc/passwd", source="test")
        print("✗ FAILED: Path traversal was not blocked!\n")
    except ValueError as e:
        print(f"✓ Blocked: {e}\n")

    print("File Hash Test:")
    try:
        file_hash = handler.get_file_hash("test/hello.txt", source="test")
        print(f"✓ Hash calculated: {file_hash}\n")
    except Exception as e:
        print(f"✗ Hash failed: {e}\n")

    print("File Info Test:")
    try:
        info = handler.get_file_info("test/hello.txt", source="test")
        print(f"✓ File info: {info}\n")
    except Exception as e:
        print(f"✗ Info failed: {e}\n")

    print("Delete File Test:")
    try:
        handler.delete_file("test/hello.txt", source="test")
        print("✓ Delete successful\n")
    except Exception as e:
        print(f"✗ Delete failed: {e}\n")
