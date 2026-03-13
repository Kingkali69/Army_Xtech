#!/usr/bin/env python3
"""
GhostOps Safe Upload Handler Module
Handles file uploads with comprehensive security checks
"""

import os
import time
from path_sanitizer import (
    sanitize_filename,
    validate_file_extension,
    generate_random_filename,
    check_file_size,
    check_magic_number
)
from safe_path import validate_file_path, get_safe_upload_path, log_blocked_access
from file_handler import SafeFileHandler


class UploadHandler:
    """
    Secure file upload handler with multiple security layers
    """

    def __init__(self, upload_dir="~/.ghostops/uploads", max_size_mb=50,
                 allowed_extensions=None, use_random_names=False):
        """
        Initialize upload handler

        Args:
            upload_dir: Directory to store uploads (default: ~/.ghostops/uploads)
            max_size_mb: Maximum file size in MB (default: 50)
            allowed_extensions: List of allowed extensions (default: safe extensions)
            use_random_names: Whether to use random filenames (default: False)
        """
        self.upload_dir = os.path.abspath(os.path.expanduser(upload_dir))
        self.max_size_mb = max_size_mb
        self.allowed_extensions = allowed_extensions or [
            '.py', '.txt', '.sh', '.json', '.log', '.md', '.yaml', '.yml', '.conf'
        ]
        self.use_random_names = use_random_names

        # Create upload directory
        os.makedirs(self.upload_dir, exist_ok=True)

        # Initialize file handler for this directory
        self.file_handler = SafeFileHandler(allowed_base_dir=self.upload_dir)

    def handle_upload(self, file_info, source="unknown"):
        """
        Handle file upload with security validation

        Args:
            file_info: Dict with 'filename', 'data', 'content_type'
            source: Source of upload (IP, device_id, etc.)

        Returns:
            Dict with upload result (success, path, size, etc.)

        Raises:
            ValueError: If upload fails security checks
        """
        try:
            # Extract file info
            original_filename = file_info.get('filename', '')
            file_data = file_info.get('data', b'')

            if not original_filename:
                raise ValueError("No filename provided")

            if not file_data:
                raise ValueError("No file data provided")

            print(f"[UPLOAD] Processing upload: {original_filename} from {source}")

            # Security Layer 1: File size check
            check_file_size(file_data, max_size_mb=self.max_size_mb)
            print(f"[UPLOAD] ✓ Size check passed: {len(file_data)} bytes")

            # Security Layer 2: Sanitize filename
            safe_filename = sanitize_filename(original_filename)
            print(f"[UPLOAD] ✓ Filename sanitized: {original_filename} → {safe_filename}")

            # Security Layer 3: Validate extension
            validate_file_extension(safe_filename, allowed_extensions=self.allowed_extensions)
            print(f"[UPLOAD] ✓ Extension validated")

            # Security Layer 4: Magic number check (malware detection)
            check_magic_number(file_data, safe_filename)
            print(f"[UPLOAD] ✓ Magic number check passed")

            # Security Layer 5: Generate random filename if configured
            if self.use_random_names:
                final_filename = generate_random_filename(safe_filename)
                print(f"[UPLOAD] ✓ Random filename generated: {final_filename}")
            else:
                final_filename = safe_filename

            # Security Layer 6: Check for existing file and prevent overwrite
            target_path = os.path.join(self.upload_dir, final_filename)
            if os.path.exists(target_path):
                # Add timestamp to prevent overwrite
                name, ext = os.path.splitext(final_filename)
                timestamp = int(time.time())
                final_filename = f"{name}_{timestamp}{ext}"
                print(f"[UPLOAD] ✓ Conflict resolved: {final_filename}")

            # Security Layer 7: Build and validate full path
            full_path = os.path.join(self.upload_dir, final_filename)
            # Validate the path is safe
            validated_path = validate_file_path(full_path, allowed_base_dir=self.upload_dir, mode='write')
            print(f"[UPLOAD] ✓ Path validated: {validated_path}")

            # Security Layer 8: Write file using safe handler
            # Write using the full path (already validated above)
            with open(validated_path, 'wb') as f:
                f.write(file_data)
            print(f"[UPLOAD] ✓ File written successfully")

            # Verify upload
            saved_size = os.path.getsize(validated_path)
            if saved_size != len(file_data):
                raise ValueError(f"Upload verification failed: size mismatch")

            result = {
                'success': True,
                'original_name': original_filename,
                'saved_name': final_filename,
                'path': validated_path,
                'size': saved_size,
                'timestamp': time.time()
            }

            print(f"[UPLOAD] ✅ Upload successful: {final_filename} ({saved_size} bytes)")
            return result

        except ValueError as e:
            # Log blocked upload
            log_blocked_access(
                file_info.get('filename', 'unknown'),
                f"Upload blocked: {str(e)}",
                source
            )
            print(f"[UPLOAD] ❌ Upload blocked: {e}")
            raise

        except Exception as e:
            print(f"[UPLOAD] ❌ Upload error: {e}")
            import traceback
            traceback.print_exc()
            raise ValueError(f"Upload failed: {str(e)}")

    def handle_multipart_upload(self, multipart_data, source="unknown"):
        """
        Handle multipart form upload (multiple files)

        Args:
            multipart_data: Dict with 'files' and 'fields' from multipart parser
            source: Source of upload

        Returns:
            Dict with results for all uploaded files
        """
        if not multipart_data or 'files' not in multipart_data:
            raise ValueError("No files in multipart upload")

        files = multipart_data['files']
        results = {
            'success': True,
            'saved_files': [],
            'failed_files': [],
            'total_size': 0
        }

        for field_name, file_info in files.items():
            try:
                result = self.handle_upload(file_info, source=source)
                results['saved_files'].append(result)
                results['total_size'] += result['size']
            except Exception as e:
                results['failed_files'].append({
                    'filename': file_info.get('filename', 'unknown'),
                    'error': str(e)
                })
                results['success'] = False

        print(f"[UPLOAD] Multipart upload complete: "
              f"{len(results['saved_files'])} succeeded, "
              f"{len(results['failed_files'])} failed")

        return results

    def list_uploads(self):
        """
        List all uploaded files

        Returns:
            List of uploaded file info
        """
        try:
            files = []
            for filename in os.listdir(self.upload_dir):
                file_path = os.path.join(self.upload_dir, filename)
                if os.path.isfile(file_path):
                    files.append({
                        'name': filename,
                        'size': os.path.getsize(file_path),
                        'modified': os.path.getmtime(file_path)
                    })

            return sorted(files, key=lambda x: x['modified'], reverse=True)
        except Exception as e:
            print(f"[!] Error listing uploads: {e}")
            return []

    def delete_upload(self, filename, source="unknown"):
        """
        Delete an uploaded file

        Args:
            filename: Name of file to delete
            source: Source of delete request

        Returns:
            True if successful
        """
        try:
            # Sanitize filename
            safe_filename = sanitize_filename(filename)

            # Delete using safe handler
            return self.file_handler.delete_file(safe_filename, source=source)

        except Exception as e:
            print(f"[!] Error deleting upload {filename}: {e}")
            raise

    def cleanup_old_uploads(self, max_age_days=30):
        """
        Clean up old uploaded files

        Args:
            max_age_days: Maximum age in days before deletion (default: 30)

        Returns:
            Number of files deleted
        """
        try:
            current_time = time.time()
            max_age_seconds = max_age_days * 24 * 60 * 60
            deleted = 0

            for filename in os.listdir(self.upload_dir):
                file_path = os.path.join(self.upload_dir, filename)
                if os.path.isfile(file_path):
                    file_age = current_time - os.path.getmtime(file_path)
                    if file_age > max_age_seconds:
                        try:
                            self.file_handler.delete_file(filename, source="cleanup")
                            deleted += 1
                            print(f"[CLEANUP] Deleted old upload: {filename}")
                        except:
                            pass

            print(f"[CLEANUP] Deleted {deleted} old uploads (>{max_age_days} days)")
            return deleted

        except Exception as e:
            print(f"[!] Error during cleanup: {e}")
            return 0


def create_upload_handler(upload_dir="~/.ghostops/uploads", max_size_mb=50,
                          allowed_extensions=None, use_random_names=False):
    """
    Factory function to create an UploadHandler

    Args:
        upload_dir: Directory to store uploads
        max_size_mb: Maximum file size in MB
        allowed_extensions: List of allowed extensions
        use_random_names: Whether to use random filenames

    Returns:
        UploadHandler instance
    """
    return UploadHandler(
        upload_dir=upload_dir,
        max_size_mb=max_size_mb,
        allowed_extensions=allowed_extensions,
        use_random_names=use_random_names
    )


if __name__ == "__main__":
    # Test cases
    print("=== Upload Handler Test Cases ===\n")

    handler = UploadHandler(upload_dir="/tmp/ghostops/uploads", use_random_names=False)

    print("Test 1: Normal file upload")
    try:
        result = handler.handle_upload({
            'filename': 'test.txt',
            'data': b'Hello, World!',
            'content_type': 'text/plain'
        }, source="test")
        print(f"✓ Upload successful: {result}\n")
    except Exception as e:
        print(f"✗ Upload failed: {e}\n")

    print("Test 2: Path traversal attempt (should block)")
    try:
        result = handler.handle_upload({
            'filename': '../../../etc/passwd',
            'data': b'malicious',
            'content_type': 'text/plain'
        }, source="test")
        print(f"✗ FAILED: Path traversal was not blocked!\n")
    except ValueError as e:
        print(f"✓ Blocked: {e}\n")

    print("Test 3: Executable file upload (should block)")
    try:
        result = handler.handle_upload({
            'filename': 'malware.exe',
            'data': b'MZ\x90\x00' + b'A' * 100,  # Windows EXE signature
            'content_type': 'application/octet-stream'
        }, source="test")
        print(f"✗ FAILED: Executable was not blocked!\n")
    except ValueError as e:
        print(f"✓ Blocked: {e}\n")

    print("Test 4: File too large (should block)")
    try:
        large_data = b'A' * (51 * 1024 * 1024)  # 51MB
        result = handler.handle_upload({
            'filename': 'large.txt',
            'data': large_data,
            'content_type': 'text/plain'
        }, source="test")
        print(f"✗ FAILED: Large file was not blocked!\n")
    except ValueError as e:
        print(f"✓ Blocked: {e}\n")

    print("Test 5: List uploads")
    try:
        uploads = handler.list_uploads()
        print(f"✓ Found {len(uploads)} uploads")
        for upload in uploads:
            print(f"  - {upload['name']} ({upload['size']} bytes)")
        print()
    except Exception as e:
        print(f"✗ List failed: {e}\n")

    print("Test 6: Cleanup old uploads")
    try:
        deleted = handler.cleanup_old_uploads(max_age_days=0)  # Delete all
        print(f"✓ Cleaned up {deleted} files\n")
    except Exception as e:
        print(f"✗ Cleanup failed: {e}\n")
