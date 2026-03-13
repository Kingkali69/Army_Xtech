#!/usr/bin/env python3
"""
Password Hasher
Secure password hashing using bcrypt for GhostOps authentication
"""

import os
import sys

try:
    import bcrypt
except ImportError:
    print("[!] WARNING: bcrypt module not installed. Password hashing will use fallback method.")
    print("[!] Install bcrypt with: pip install bcrypt")
    bcrypt = None


class PasswordHasher:
    """Handles secure password hashing and verification using bcrypt"""

    # bcrypt work factor (cost factor: 2^12 iterations)
    # Higher = more secure but slower
    WORK_FACTOR = 12

    @staticmethod
    def hash_password(password):
        """
        Hash a password using bcrypt

        Args:
            password: Plain text password to hash

        Returns:
            str: Hashed password (bcrypt format)
        """
        if not password:
            raise ValueError("Password cannot be empty")

        if bcrypt is None:
            # Fallback to SHA-256 if bcrypt not available (NOT RECOMMENDED)
            import hashlib
            import base64
            salt = os.urandom(32)
            key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
            return base64.b64encode(salt + key).decode('utf-8')

        # Convert password to bytes
        password_bytes = password.encode('utf-8')

        # Generate salt and hash password
        salt = bcrypt.gensalt(rounds=PasswordHasher.WORK_FACTOR)
        hashed = bcrypt.hashpw(password_bytes, salt)

        # Return as string
        return hashed.decode('utf-8')

    @staticmethod
    def verify_password(password, hashed_password):
        """
        Verify a password against a hash

        Args:
            password: Plain text password to verify
            hashed_password: Previously hashed password

        Returns:
            bool: True if password matches, False otherwise
        """
        if not password or not hashed_password:
            return False

        try:
            if bcrypt is None:
                # Fallback verification for SHA-256
                import hashlib
                import base64
                decoded = base64.b64decode(hashed_password.encode('utf-8'))
                salt = decoded[:32]
                stored_key = decoded[32:]
                key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
                return key == stored_key

            # Convert inputs to bytes
            password_bytes = password.encode('utf-8')
            hashed_bytes = hashed_password.encode('utf-8')

            # Verify password
            return bcrypt.checkpw(password_bytes, hashed_bytes)

        except Exception as e:
            print(f"[!] Password verification error: {e}")
            return False

    @staticmethod
    def needs_rehash(hashed_password):
        """
        Check if a hashed password needs to be rehashed
        (e.g., if work factor has increased)

        Args:
            hashed_password: Previously hashed password

        Returns:
            bool: True if password should be rehashed
        """
        if bcrypt is None:
            return False

        try:
            # bcrypt hashes have format: $2b$rounds$salt_and_hash
            # Extract rounds from hash
            parts = hashed_password.split('$')
            if len(parts) >= 3:
                current_rounds = int(parts[2])
                return current_rounds < PasswordHasher.WORK_FACTOR
            return False
        except:
            return False

    @staticmethod
    def is_bcrypt_available():
        """Check if bcrypt module is available"""
        return bcrypt is not None


# Testing function
if __name__ == "__main__":
    print("=== Password Hasher Test ===\n")

    if not PasswordHasher.is_bcrypt_available():
        print("[!] WARNING: Using fallback hashing (bcrypt not installed)")
        print()

    # Test password
    test_password = "GhostOps2024!Security"
    wrong_password = "WrongPassword123!"

    print(f"Test password: {test_password}")
    print()

    # Hash password
    print("[+] Hashing password...")
    hashed = PasswordHasher.hash_password(test_password)
    print(f"Hashed: {hashed[:50]}...")
    print()

    # Verify correct password
    print("[+] Verifying correct password...")
    is_valid = PasswordHasher.verify_password(test_password, hashed)
    print(f"Result: {'✓ VALID' if is_valid else '✗ INVALID'}")
    print()

    # Verify wrong password
    print("[+] Verifying wrong password...")
    is_valid = PasswordHasher.verify_password(wrong_password, hashed)
    print(f"Result: {'✓ VALID' if is_valid else '✗ INVALID'}")
    print()

    # Check if rehash needed
    needs_rehash = PasswordHasher.needs_rehash(hashed)
    print(f"[+] Needs rehash: {needs_rehash}")
