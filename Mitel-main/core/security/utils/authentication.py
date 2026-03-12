#!/usr/bin/env python3
"""
Authentication System
Comprehensive login and authentication management for GhostOps
Integrates password validation, hashing, key management, and session tokens
"""

import os
import json
import time
from password_validator import PasswordValidator
from password_hasher import PasswordHasher
from key_manager import KeyManager
from session_manager import SessionManager, LoginRateLimiter


class AuthenticationSystem:
    """Main authentication system that coordinates all security components"""

    DEFAULT_CONFIG_DIR = os.path.expanduser("~/.ghostops")
    CREDENTIALS_FILE = "credentials.json"

    def __init__(self, config_dir=None, session_timeout=3600):
        """
        Initialize authentication system

        Args:
            config_dir: Directory for auth files (default: ~/.ghostops)
            session_timeout: Session timeout in seconds (default: 1 hour)
        """
        self.config_dir = config_dir or self.DEFAULT_CONFIG_DIR
        self.credentials_path = os.path.join(self.config_dir, self.CREDENTIALS_FILE)

        # Initialize components
        self.key_manager = KeyManager(config_dir=self.config_dir)
        self.session_manager = SessionManager(session_timeout=session_timeout)
        self.rate_limiter = LoginRateLimiter()
        self.password_validator = PasswordValidator()
        self.password_hasher = PasswordHasher()

        # Ensure config directory exists with secure permissions
        self._ensure_config_dir()

    def _ensure_config_dir(self):
        """Create config directory with secure permissions"""
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir, mode=0o700)

    def is_first_run(self):
        """
        Check if this is the first run (no admin credentials set)

        Returns:
            bool: True if first run
        """
        return not os.path.exists(self.credentials_path) or not self.key_manager.key_exists()

    def setup_admin(self, password):
        """
        Set up admin account with password (first-run setup)

        Args:
            password: Admin password

        Returns:
            tuple: (success: bool, message: str, admin_key: str or None)
        """
        # Validate password strength
        is_valid, error = self.password_validator.validate_password(password)
        if not is_valid:
            return False, error, None

        # Check for common passwords
        if self.password_validator.check_common_passwords(password):
            return False, "Password is too common. Please choose a more unique password.", None

        # Hash password
        try:
            password_hash = self.password_hasher.hash_password(password)
        except Exception as e:
            return False, f"Failed to hash password: {e}", None

        # Generate admin key
        admin_key = self.key_manager.generate_key()

        # Save admin key
        if not self.key_manager.save_key(admin_key):
            return False, "Failed to save admin key", None

        # Save credentials
        credentials = {
            "admin": {
                "password_hash": password_hash,
                "created_at": time.time(),
                "created_at_readable": time.strftime("%Y-%m-%d %H:%M:%S"),
                "last_login": None,
                "password_changed_at": time.time()
            }
        }

        try:
            # Write credentials to temp file first
            temp_path = self.credentials_path + ".tmp"
            with open(temp_path, 'w') as f:
                json.dump(credentials, f, indent=2)

            # Set secure permissions
            os.chmod(temp_path, 0o600)

            # Atomic rename
            os.rename(temp_path, self.credentials_path)

            print(f"[+] Admin account created successfully")
            print(f"[+] Admin key saved to: {self.key_manager.key_file_path}")
            print(f"[!] IMPORTANT: Save your admin key in a secure location!")
            print(f"[!] Admin Key: {admin_key}")

            return True, "Admin account created successfully", admin_key

        except Exception as e:
            # Cleanup on failure
            if os.path.exists(temp_path):
                os.remove(temp_path)
            self.key_manager.delete_key()
            return False, f"Failed to save credentials: {e}", None

    def login(self, username, password):
        """
        Authenticate user and create session

        Args:
            username: Username (currently only "admin" supported)
            password: Password

        Returns:
            tuple: (success: bool, message: str, session_token: str or None)
        """
        # Check rate limiting
        is_locked, remaining = self.rate_limiter.is_locked_out(username)
        if is_locked:
            return False, f"Account locked due to too many failed attempts. Try again in {remaining} seconds.", None

        # Load credentials
        credentials = self._load_credentials()
        if not credentials:
            return False, "Authentication system not initialized", None

        # Check if user exists
        if username not in credentials:
            self.rate_limiter.record_attempt(username, success=False)
            return False, "Invalid username or password", None

        user_data = credentials[username]

        # Verify password
        password_hash = user_data.get('password_hash')
        if not password_hash:
            return False, "User account corrupted", None

        try:
            password_valid = self.password_hasher.verify_password(password, password_hash)
        except Exception as e:
            print(f"[!] Password verification error: {e}")
            return False, "Authentication error", None

        if not password_valid:
            # Record failed attempt
            self.rate_limiter.record_attempt(username, success=False)

            # Get attempt count
            attempts = self.rate_limiter.get_attempt_count(username)
            remaining_attempts = LoginRateLimiter.MAX_ATTEMPTS - attempts

            if remaining_attempts > 0:
                return False, f"Invalid username or password. {remaining_attempts} attempts remaining.", None
            else:
                return False, "Account locked due to too many failed attempts.", None

        # Password valid - record success
        self.rate_limiter.record_attempt(username, success=True)

        # Check if password needs rehashing
        if self.password_hasher.needs_rehash(password_hash):
            print("[+] Password hash needs update (rehashing with current work factor)")
            new_hash = self.password_hasher.hash_password(password)
            user_data['password_hash'] = new_hash
            self._save_credentials(credentials)

        # Update last login
        user_data['last_login'] = time.time()
        user_data['last_login_readable'] = time.strftime("%Y-%m-%d %H:%M:%S")
        self._save_credentials(credentials)

        # Create session
        token, session = self.session_manager.create_session(
            username,
            metadata={
                'login_time': time.time(),
                'login_time_readable': time.strftime("%Y-%m-%d %H:%M:%S")
            }
        )

        print(f"[+] User '{username}' logged in successfully")
        print(f"[+] Session token: {token[:16]}... (truncated)")

        return True, "Login successful", token

    def logout(self, session_token):
        """
        Log out user (invalidate session)

        Args:
            session_token: Session token to invalidate

        Returns:
            bool: True if logout successful
        """
        success = self.session_manager.invalidate_token(session_token)
        if success:
            print("[+] User logged out successfully")
        return success

    def verify_session(self, session_token):
        """
        Verify session token is valid

        Args:
            session_token: Session token to verify

        Returns:
            dict: Session data if valid, None if invalid
        """
        return self.session_manager.validate_token(session_token)

    def change_password(self, username, old_password, new_password):
        """
        Change user password

        Args:
            username: Username
            old_password: Current password
            new_password: New password

        Returns:
            tuple: (success: bool, message: str)
        """
        # Verify old password
        success, message, _ = self.login(username, old_password)
        if not success:
            return False, "Current password is incorrect"

        # Validate new password
        is_valid, error = self.password_validator.validate_password(new_password)
        if not is_valid:
            return False, error

        # Check for common passwords
        if self.password_validator.check_common_passwords(new_password):
            return False, "New password is too common. Please choose a more unique password."

        # Hash new password
        try:
            new_hash = self.password_hasher.hash_password(new_password)
        except Exception as e:
            return False, f"Failed to hash new password: {e}"

        # Update credentials
        credentials = self._load_credentials()
        if not credentials or username not in credentials:
            return False, "User not found"

        credentials[username]['password_hash'] = new_hash
        credentials[username]['password_changed_at'] = time.time()
        credentials[username]['password_changed_at_readable'] = time.strftime("%Y-%m-%d %H:%M:%S")

        if self._save_credentials(credentials):
            # Invalidate all existing sessions
            self.session_manager.invalidate_user_sessions(username)
            print(f"[+] Password changed for user '{username}'")
            return True, "Password changed successfully. Please log in again."
        else:
            return False, "Failed to save new password"

    def rotate_admin_key(self, password):
        """
        Rotate admin key (requires password verification)

        Args:
            password: Admin password for verification

        Returns:
            tuple: (success: bool, message: str, new_key: str or None)
        """
        # Verify password
        success, message, _ = self.login("admin", password)
        if not success:
            return False, "Password verification failed", None

        # Load current key
        key_data = self.key_manager.load_key()
        if not key_data:
            return False, "No admin key found", None

        old_key = key_data.get('admin_key')

        # Rotate key
        new_key, success = self.key_manager.rotate_key(old_key)

        if success:
            print("[+] Admin key rotated successfully")
            print(f"[!] IMPORTANT: Update all systems with new admin key!")
            print(f"[!] New Admin Key: {new_key}")
            return True, "Admin key rotated successfully", new_key
        else:
            return False, "Failed to rotate admin key", None

    def get_admin_key(self):
        """
        Get current admin key

        Returns:
            str: Admin key or None if not found
        """
        key_data = self.key_manager.load_key()
        if key_data:
            return key_data.get('admin_key')
        return None

    def _load_credentials(self):
        """Load credentials from file"""
        try:
            if not os.path.exists(self.credentials_path):
                return None

            with open(self.credentials_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"[!] Failed to load credentials: {e}")
            return None

    def _save_credentials(self, credentials):
        """Save credentials to file"""
        try:
            # Write to temp file first
            temp_path = self.credentials_path + ".tmp"
            with open(temp_path, 'w') as f:
                json.dump(credentials, f, indent=2)

            # Set secure permissions
            os.chmod(temp_path, 0o600)

            # Atomic rename
            os.rename(temp_path, self.credentials_path)
            return True

        except Exception as e:
            print(f"[!] Failed to save credentials: {e}")
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return False

    def get_session_stats(self):
        """Get session statistics"""
        return self.session_manager.get_stats()

    def clear_lockout(self, username):
        """
        Clear account lockout (admin function)

        Args:
            username: Username to unlock

        Returns:
            bool: True if lockout cleared
        """
        return self.rate_limiter.clear_lockout(username)


# Testing function
if __name__ == "__main__":
    print("=== Authentication System Test ===\n")

    # Use test directory
    test_dir = "/tmp/ghostops_auth_test"
    auth = AuthenticationSystem(config_dir=test_dir)

    # Check first run
    print(f"[+] First run: {auth.is_first_run()}")
    print()

    # Setup admin
    print("[+] Setting up admin account...")
    success, message, admin_key = auth.setup_admin("StrongPassword123!")
    print(f"Success: {success}")
    print(f"Message: {message}")
    if admin_key:
        print(f"Admin key: {admin_key[:16]}... (truncated)")
    print()

    # Login
    print("[+] Logging in as admin...")
    success, message, token = auth.login("admin", "StrongPassword123!")
    print(f"Success: {success}")
    print(f"Message: {message}")
    if token:
        print(f"Token: {token[:16]}... (truncated)")
    print()

    # Verify session
    print("[+] Verifying session...")
    session = auth.verify_session(token)
    print(f"Valid: {session is not None}")
    print()

    # Session stats
    print("[+] Session stats:")
    stats = auth.get_session_stats()
    print(f"Total sessions: {stats['total_sessions']}")
    print()

    # Logout
    print("[+] Logging out...")
    auth.logout(token)
    print()

    # Cleanup
    print("[+] Cleaning up test files...")
    import shutil
    shutil.rmtree(test_dir, ignore_errors=True)
