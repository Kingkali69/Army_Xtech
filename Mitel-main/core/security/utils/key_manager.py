#!/usr/bin/env python3
"""
Key Manager
Handles admin key generation, storage, and rotation for GhostOps authentication
"""

import os
import json
import secrets
import time
from pathlib import Path


class KeyManager:
    """Manages admin authentication keys with secure generation and rotation"""

    # Default paths
    DEFAULT_CONFIG_DIR = os.path.expanduser("~/.ghostops")
    DEFAULT_KEY_FILE = "admin_key.json"
    KEY_LENGTH = 32  # 32 bytes = 256 bits

    def __init__(self, config_dir=None):
        """
        Initialize key manager

        Args:
            config_dir: Directory to store key files (default: ~/.ghostops)
        """
        self.config_dir = config_dir or self.DEFAULT_CONFIG_DIR
        self.key_file_path = os.path.join(self.config_dir, self.DEFAULT_KEY_FILE)

        # Ensure config directory exists with secure permissions
        self._ensure_config_dir()

    def _ensure_config_dir(self):
        """Create config directory with secure permissions if it doesn't exist"""
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir, mode=0o700)  # rwx------
            print(f"[+] Created secure config directory: {self.config_dir}")
        else:
            # Ensure existing directory has secure permissions
            try:
                os.chmod(self.config_dir, 0o700)
            except Exception as e:
                print(f"[!] Warning: Could not set directory permissions: {e}")

    def generate_key(self):
        """
        Generate a cryptographically secure random key

        Returns:
            str: URL-safe base64-encoded random key
        """
        # Use secrets module for cryptographically strong random generation
        return secrets.token_urlsafe(self.KEY_LENGTH)

    def key_exists(self):
        """
        Check if admin key file exists

        Returns:
            bool: True if key file exists
        """
        return os.path.exists(self.key_file_path)

    def save_key(self, key, metadata=None):
        """
        Save admin key to secure file

        Args:
            key: The admin key to save
            metadata: Optional dict with additional metadata (e.g., created_at, rotated_at)

        Returns:
            bool: True if save successful
        """
        try:
            # Prepare key data
            key_data = {
                "admin_key": key,
                "created_at": time.time(),
                "created_at_readable": time.strftime("%Y-%m-%d %H:%M:%S"),
                "version": 1
            }

            # Add metadata if provided
            if metadata:
                key_data.update(metadata)

            # Write to temporary file first
            temp_path = self.key_file_path + ".tmp"
            with open(temp_path, 'w') as f:
                json.dump(key_data, f, indent=2)

            # Set secure permissions on temp file (rw-------)
            os.chmod(temp_path, 0o600)

            # Atomic rename
            os.rename(temp_path, self.key_file_path)

            print(f"[+] Admin key saved securely to: {self.key_file_path}")
            print(f"[+] File permissions: 600 (read/write for owner only)")
            return True

        except Exception as e:
            print(f"[!] Failed to save admin key: {e}")
            # Clean up temp file if it exists
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except:
                    pass
            return False

    def load_key(self):
        """
        Load admin key from file

        Returns:
            dict: Key data including admin_key and metadata, or None if failed
        """
        try:
            if not self.key_exists():
                return None

            # Verify file permissions
            file_stat = os.stat(self.key_file_path)
            file_mode = file_stat.st_mode & 0o777

            # Warn if permissions are too open
            if file_mode != 0o600:
                print(f"[!] WARNING: Key file has insecure permissions: {oct(file_mode)}")
                print(f"[!] Fixing permissions to 600...")
                try:
                    os.chmod(self.key_file_path, 0o600)
                except Exception as e:
                    print(f"[!] Could not fix permissions: {e}")

            # Load key data
            with open(self.key_file_path, 'r') as f:
                key_data = json.load(f)

            return key_data

        except Exception as e:
            print(f"[!] Failed to load admin key: {e}")
            return None

    def rotate_key(self, old_key):
        """
        Rotate admin key (generate new key, archive old key)

        Args:
            old_key: The current admin key (for verification)

        Returns:
            tuple: (new_key: str, success: bool)
        """
        try:
            # Verify old key matches current key
            current_data = self.load_key()
            if not current_data:
                print("[!] No existing key found to rotate")
                return None, False

            if current_data.get("admin_key") != old_key:
                print("[!] Old key does not match current key")
                return None, False

            # Generate new key
            new_key = self.generate_key()

            # Archive old key
            archive_path = self.key_file_path + ".old"
            if os.path.exists(self.key_file_path):
                os.rename(self.key_file_path, archive_path)
                os.chmod(archive_path, 0o600)

            # Save new key with rotation metadata
            metadata = {
                "rotated_at": time.time(),
                "rotated_at_readable": time.strftime("%Y-%m-%d %H:%M:%S"),
                "previous_key_archived": True,
                "rotation_count": current_data.get("rotation_count", 0) + 1
            }

            success = self.save_key(new_key, metadata)

            if success:
                print(f"[+] Admin key rotated successfully")
                print(f"[+] Old key archived to: {archive_path}")
                self._log_rotation(old_key, new_key)
                return new_key, True
            else:
                # Restore old key if save failed
                if os.path.exists(archive_path):
                    os.rename(archive_path, self.key_file_path)
                return None, False

        except Exception as e:
            print(f"[!] Key rotation failed: {e}")
            return None, False

    def _log_rotation(self, old_key, new_key):
        """
        Log key rotation to audit log

        Args:
            old_key: Previous admin key
            new_key: New admin key
        """
        try:
            log_file = os.path.join(self.config_dir, "key_rotation.log")

            log_entry = {
                "timestamp": time.time(),
                "timestamp_readable": time.strftime("%Y-%m-%d %H:%M:%S"),
                "event": "key_rotation",
                # Store only partial keys for security (first 8 chars)
                "old_key_partial": old_key[:8] + "..." if len(old_key) > 8 else "***",
                "new_key_partial": new_key[:8] + "..." if len(new_key) > 8 else "***"
            }

            # Append to log file
            with open(log_file, 'a') as f:
                f.write(json.dumps(log_entry) + "\n")

            # Set secure permissions
            os.chmod(log_file, 0o600)

        except Exception as e:
            print(f"[!] Failed to log rotation: {e}")

    def get_rotation_history(self):
        """
        Get key rotation history from audit log

        Returns:
            list: List of rotation events
        """
        try:
            log_file = os.path.join(self.config_dir, "key_rotation.log")

            if not os.path.exists(log_file):
                return []

            history = []
            with open(log_file, 'r') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        history.append(entry)
                    except:
                        continue

            return history

        except Exception as e:
            print(f"[!] Failed to read rotation history: {e}")
            return []

    def delete_key(self):
        """
        Delete admin key file (use with caution!)

        Returns:
            bool: True if deleted successfully
        """
        try:
            if os.path.exists(self.key_file_path):
                os.remove(self.key_file_path)
                print(f"[+] Admin key deleted: {self.key_file_path}")
                return True
            return False
        except Exception as e:
            print(f"[!] Failed to delete admin key: {e}")
            return False


# Testing function
if __name__ == "__main__":
    print("=== Key Manager Test ===\n")

    # Use test directory
    test_dir = "/tmp/ghostops_test"
    km = KeyManager(config_dir=test_dir)

    # Generate and save key
    print("[+] Generating new admin key...")
    key1 = km.generate_key()
    print(f"Generated key: {key1[:16]}... (truncated)")
    print()

    print("[+] Saving admin key...")
    km.save_key(key1)
    print()

    # Load key
    print("[+] Loading admin key...")
    loaded = km.load_key()
    print(f"Loaded key: {loaded['admin_key'][:16]}... (truncated)")
    print(f"Created at: {loaded['created_at_readable']}")
    print()

    # Rotate key
    print("[+] Rotating admin key...")
    key2, success = km.rotate_key(key1)
    if success:
        print(f"New key: {key2[:16]}... (truncated)")
    print()

    # View rotation history
    print("[+] Rotation history:")
    history = km.get_rotation_history()
    for entry in history:
        print(f"  {entry['timestamp_readable']}: {entry['event']}")
    print()

    # Cleanup
    print("[+] Cleaning up test files...")
    km.delete_key()
    import shutil
    shutil.rmtree(test_dir, ignore_errors=True)
