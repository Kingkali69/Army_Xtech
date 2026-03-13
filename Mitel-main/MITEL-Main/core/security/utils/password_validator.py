#!/usr/bin/env python3
"""
Password Strength Validator
Validates password complexity requirements for GhostOps authentication
"""

import re


class PasswordValidator:
    """Validates password strength according to security requirements"""

    # Password requirements
    MIN_LENGTH = 12
    REQUIRED_UPPERCASE = 1
    REQUIRED_LOWERCASE = 1
    REQUIRED_NUMBERS = 1
    REQUIRED_SPECIAL = 1
    SPECIAL_CHARS = "!@#$%^&*"

    @staticmethod
    def validate_password(password):
        """
        Validate password strength

        Requirements:
        - Minimum 12 characters
        - At least 1 uppercase letter
        - At least 1 lowercase letter
        - At least 1 number
        - At least 1 special character (!@#$%^&*)

        Args:
            password: The password to validate

        Returns:
            tuple: (is_valid: bool, error_message: str or None)
        """
        if not password:
            return False, "Password cannot be empty"

        # Check minimum length
        if len(password) < PasswordValidator.MIN_LENGTH:
            return False, f"Password must be at least {PasswordValidator.MIN_LENGTH} characters long"

        # Check for uppercase letters
        uppercase_count = sum(1 for c in password if c.isupper())
        if uppercase_count < PasswordValidator.REQUIRED_UPPERCASE:
            return False, f"Password must contain at least {PasswordValidator.REQUIRED_UPPERCASE} uppercase letter(s)"

        # Check for lowercase letters
        lowercase_count = sum(1 for c in password if c.islower())
        if lowercase_count < PasswordValidator.REQUIRED_LOWERCASE:
            return False, f"Password must contain at least {PasswordValidator.REQUIRED_LOWERCASE} lowercase letter(s)"

        # Check for numbers
        number_count = sum(1 for c in password if c.isdigit())
        if number_count < PasswordValidator.REQUIRED_NUMBERS:
            return False, f"Password must contain at least {PasswordValidator.REQUIRED_NUMBERS} number(s)"

        # Check for special characters
        special_count = sum(1 for c in password if c in PasswordValidator.SPECIAL_CHARS)
        if special_count < PasswordValidator.REQUIRED_SPECIAL:
            return False, f"Password must contain at least {PasswordValidator.REQUIRED_SPECIAL} special character(s) from: {PasswordValidator.SPECIAL_CHARS}"

        # All checks passed
        return True, None

    @staticmethod
    def get_password_requirements():
        """Get a formatted string describing password requirements"""
        return f"""Password Requirements:
- Minimum {PasswordValidator.MIN_LENGTH} characters
- At least {PasswordValidator.REQUIRED_UPPERCASE} uppercase letter
- At least {PasswordValidator.REQUIRED_LOWERCASE} lowercase letter
- At least {PasswordValidator.REQUIRED_NUMBERS} number
- At least {PasswordValidator.REQUIRED_SPECIAL} special character from: {PasswordValidator.SPECIAL_CHARS}"""

    @staticmethod
    def check_common_passwords(password):
        """
        Check if password is a commonly used weak password

        Args:
            password: The password to check

        Returns:
            bool: True if password is common (weak), False otherwise
        """
        # Common weak passwords list
        common_passwords = [
            "password", "123456", "12345678", "qwerty", "abc123",
            "monkey", "1234567", "letmein", "trustno1", "dragon",
            "baseball", "iloveyou", "master", "sunshine", "ashley",
            "bailey", "passw0rd", "shadow", "123123", "654321",
            "superman", "qazwsx", "michael", "football", "admin",
            "administrator", "root", "toor", "ghostops", "ghost"
        ]

        # Check if password (lowercase) is in common passwords
        if password.lower() in common_passwords:
            return True

        # Check if password contains common patterns
        common_patterns = [
            r'^\d+$',  # Only digits
            r'^[a-zA-Z]+$',  # Only letters
            r'^(.)\1+$',  # Repeated character (aaaa, 1111, etc.)
            r'^(012|123|234|345|456|567|678|789|890)+',  # Sequential numbers
            r'^(abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz)+',  # Sequential letters
        ]

        for pattern in common_patterns:
            if re.match(pattern, password, re.IGNORECASE):
                return True

        return False

    @staticmethod
    def get_password_strength_score(password):
        """
        Calculate password strength score (0-100)

        Args:
            password: The password to score

        Returns:
            int: Strength score from 0 (very weak) to 100 (very strong)
        """
        score = 0

        # Length score (up to 30 points)
        if len(password) >= 12:
            score += 10
        if len(password) >= 16:
            score += 10
        if len(password) >= 20:
            score += 10

        # Character diversity (up to 40 points)
        if any(c.isupper() for c in password):
            score += 10
        if any(c.islower() for c in password):
            score += 10
        if any(c.isdigit() for c in password):
            score += 10
        if any(c in PasswordValidator.SPECIAL_CHARS for c in password):
            score += 10

        # Complexity bonus (up to 30 points)
        unique_chars = len(set(password))
        if unique_chars >= 8:
            score += 10
        if unique_chars >= 12:
            score += 10
        if unique_chars >= 16:
            score += 10

        # Penalty for common passwords
        if PasswordValidator.check_common_passwords(password):
            score = max(0, score - 50)

        return min(100, score)

    @staticmethod
    def get_strength_label(score):
        """
        Get human-readable strength label

        Args:
            score: Password strength score (0-100)

        Returns:
            str: Strength label
        """
        if score >= 80:
            return "Very Strong"
        elif score >= 60:
            return "Strong"
        elif score >= 40:
            return "Moderate"
        elif score >= 20:
            return "Weak"
        else:
            return "Very Weak"


# Testing function
if __name__ == "__main__":
    print("=== Password Validator Test ===\n")

    # Test passwords
    test_passwords = [
        "weak",
        "Password1!",
        "StrongPass123!@#",
        "password",
        "12345678",
        "GhostOps2024!Security",
    ]

    for pwd in test_passwords:
        is_valid, error = PasswordValidator.validate_password(pwd)
        score = PasswordValidator.get_password_strength_score(pwd)
        strength = PasswordValidator.get_strength_label(score)

        print(f"Password: {pwd}")
        print(f"  Valid: {is_valid}")
        if error:
            print(f"  Error: {error}")
        print(f"  Score: {score}/100 ({strength})")
        print()
