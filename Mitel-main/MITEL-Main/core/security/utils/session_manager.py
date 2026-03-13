#!/usr/bin/env python3
"""
Session Manager
Handles session token generation, validation, and expiration for GhostOps authentication
"""

import secrets
import time
import threading
from collections import defaultdict


class SessionManager:
    """Manages authentication session tokens with expiration and rate limiting"""

    # Session configuration
    DEFAULT_SESSION_TIMEOUT = 3600  # 1 hour in seconds
    TOKEN_LENGTH = 32  # 32 bytes = 256 bits
    MAX_SESSIONS_PER_USER = 5  # Maximum concurrent sessions per user
    CLEANUP_INTERVAL = 300  # Clean up expired sessions every 5 minutes

    def __init__(self, session_timeout=None):
        """
        Initialize session manager

        Args:
            session_timeout: Session timeout in seconds (default: 1 hour)
        """
        self.session_timeout = session_timeout or self.DEFAULT_SESSION_TIMEOUT
        self.sessions = {}  # token -> session_data
        self.user_sessions = defaultdict(set)  # user -> set of tokens
        self.lock = threading.Lock()

        # Start cleanup thread
        self.cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self.cleanup_thread.start()

    def generate_token(self):
        """
        Generate a cryptographically secure session token

        Returns:
            str: URL-safe base64-encoded random token
        """
        return secrets.token_urlsafe(self.TOKEN_LENGTH)

    def create_session(self, user_id, metadata=None):
        """
        Create a new session for a user

        Args:
            user_id: User identifier (e.g., "admin")
            metadata: Optional dict with additional session metadata

        Returns:
            tuple: (token: str, session_data: dict)
        """
        with self.lock:
            # Check if user has too many sessions
            if len(self.user_sessions[user_id]) >= self.MAX_SESSIONS_PER_USER:
                # Remove oldest session
                oldest_token = min(
                    self.user_sessions[user_id],
                    key=lambda t: self.sessions.get(t, {}).get('created_at', 0)
                )
                self._remove_session(oldest_token)

            # Generate new token
            token = self.generate_token()

            # Create session data
            session_data = {
                'user_id': user_id,
                'token': token,
                'created_at': time.time(),
                'last_accessed': time.time(),
                'expires_at': time.time() + self.session_timeout,
                'metadata': metadata or {}
            }

            # Store session
            self.sessions[token] = session_data
            self.user_sessions[user_id].add(token)

            return token, session_data

    def validate_token(self, token):
        """
        Validate a session token and update last accessed time

        Args:
            token: Session token to validate

        Returns:
            dict: Session data if valid, None if invalid or expired
        """
        with self.lock:
            session = self.sessions.get(token)

            if not session:
                return None

            # Check if expired
            if time.time() > session['expires_at']:
                self._remove_session(token)
                return None

            # Update last accessed time and extend expiration
            session['last_accessed'] = time.time()
            session['expires_at'] = time.time() + self.session_timeout

            return session

    def invalidate_token(self, token):
        """
        Invalidate (remove) a session token

        Args:
            token: Session token to invalidate

        Returns:
            bool: True if token was invalidated, False if not found
        """
        with self.lock:
            return self._remove_session(token)

    def invalidate_user_sessions(self, user_id):
        """
        Invalidate all sessions for a user

        Args:
            user_id: User identifier

        Returns:
            int: Number of sessions invalidated
        """
        with self.lock:
            tokens = list(self.user_sessions.get(user_id, []))
            count = 0

            for token in tokens:
                if self._remove_session(token):
                    count += 1

            return count

    def get_user_sessions(self, user_id):
        """
        Get all active sessions for a user

        Args:
            user_id: User identifier

        Returns:
            list: List of session data dicts
        """
        with self.lock:
            tokens = self.user_sessions.get(user_id, set())
            sessions = []

            for token in list(tokens):
                session = self.sessions.get(token)
                if session and time.time() <= session['expires_at']:
                    sessions.append(session)

            return sessions

    def get_session_count(self):
        """
        Get total number of active sessions

        Returns:
            int: Number of active sessions
        """
        with self.lock:
            return len(self.sessions)

    def _remove_session(self, token):
        """
        Internal method to remove a session (must be called with lock held)

        Args:
            token: Session token to remove

        Returns:
            bool: True if removed, False if not found
        """
        session = self.sessions.get(token)
        if not session:
            return False

        user_id = session['user_id']

        # Remove from sessions dict
        del self.sessions[token]

        # Remove from user_sessions
        if user_id in self.user_sessions:
            self.user_sessions[user_id].discard(token)
            if len(self.user_sessions[user_id]) == 0:
                del self.user_sessions[user_id]

        return True

    def _cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        with self.lock:
            current_time = time.time()
            expired_tokens = []

            # Find expired sessions
            for token, session in self.sessions.items():
                if current_time > session['expires_at']:
                    expired_tokens.append(token)

            # Remove expired sessions
            for token in expired_tokens:
                self._remove_session(token)

            if expired_tokens:
                print(f"[+] Cleaned up {len(expired_tokens)} expired session(s)")

    def _cleanup_loop(self):
        """Background loop to clean up expired sessions"""
        while True:
            try:
                time.sleep(self.CLEANUP_INTERVAL)
                self._cleanup_expired_sessions()
            except Exception as e:
                print(f"[!] Session cleanup error: {e}")

    def get_stats(self):
        """
        Get session statistics

        Returns:
            dict: Statistics about active sessions
        """
        with self.lock:
            return {
                'total_sessions': len(self.sessions),
                'total_users': len(self.user_sessions),
                'sessions_by_user': {
                    user: len(tokens)
                    for user, tokens in self.user_sessions.items()
                }
            }


class LoginRateLimiter:
    """Rate limiter for login attempts to prevent brute force attacks"""

    # Rate limiting configuration
    MAX_ATTEMPTS = 5  # Maximum failed attempts before lockout
    LOCKOUT_DURATION = 900  # 15 minutes in seconds
    ATTEMPT_WINDOW = 300  # Track attempts in last 5 minutes

    def __init__(self):
        """Initialize rate limiter"""
        self.attempts = defaultdict(list)  # user_id -> list of attempt timestamps
        self.lockouts = {}  # user_id -> lockout_until timestamp
        self.lock = threading.Lock()

    def record_attempt(self, user_id, success):
        """
        Record a login attempt

        Args:
            user_id: User identifier
            success: True if login succeeded, False if failed

        Returns:
            None
        """
        with self.lock:
            current_time = time.time()

            if success:
                # Clear attempts on successful login
                if user_id in self.attempts:
                    del self.attempts[user_id]
                if user_id in self.lockouts:
                    del self.lockouts[user_id]
            else:
                # Record failed attempt
                self.attempts[user_id].append(current_time)

                # Clean up old attempts (outside window)
                cutoff = current_time - self.ATTEMPT_WINDOW
                self.attempts[user_id] = [
                    t for t in self.attempts[user_id] if t > cutoff
                ]

                # Check if should lock out
                if len(self.attempts[user_id]) >= self.MAX_ATTEMPTS:
                    self.lockouts[user_id] = current_time + self.LOCKOUT_DURATION
                    print(f"[!] Account locked: {user_id} (too many failed attempts)")

    def is_locked_out(self, user_id):
        """
        Check if a user is currently locked out

        Args:
            user_id: User identifier

        Returns:
            tuple: (is_locked: bool, remaining_seconds: int)
        """
        with self.lock:
            if user_id not in self.lockouts:
                return False, 0

            lockout_until = self.lockouts[user_id]
            current_time = time.time()

            if current_time >= lockout_until:
                # Lockout expired
                del self.lockouts[user_id]
                if user_id in self.attempts:
                    del self.attempts[user_id]
                return False, 0

            # Still locked out
            remaining = int(lockout_until - current_time)
            return True, remaining

    def get_attempt_count(self, user_id):
        """
        Get number of failed attempts for a user

        Args:
            user_id: User identifier

        Returns:
            int: Number of failed attempts in current window
        """
        with self.lock:
            if user_id not in self.attempts:
                return 0

            current_time = time.time()
            cutoff = current_time - self.ATTEMPT_WINDOW

            # Clean up old attempts
            self.attempts[user_id] = [
                t for t in self.attempts[user_id] if t > cutoff
            ]

            return len(self.attempts[user_id])

    def clear_lockout(self, user_id):
        """
        Clear lockout for a user (admin function)

        Args:
            user_id: User identifier

        Returns:
            bool: True if lockout was cleared
        """
        with self.lock:
            cleared = False

            if user_id in self.lockouts:
                del self.lockouts[user_id]
                cleared = True

            if user_id in self.attempts:
                del self.attempts[user_id]

            return cleared


# Testing function
if __name__ == "__main__":
    print("=== Session Manager Test ===\n")

    # Test session manager
    sm = SessionManager(session_timeout=10)  # 10 second timeout for testing

    print("[+] Creating session for admin...")
    token, session = sm.create_session("admin", metadata={"ip": "192.168.1.100"})
    print(f"Token: {token[:16]}... (truncated)")
    print(f"Expires at: {session['expires_at']}")
    print()

    print("[+] Validating token...")
    validated = sm.validate_token(token)
    print(f"Valid: {validated is not None}")
    print()

    print("[+] Session stats:")
    stats = sm.get_stats()
    print(f"Total sessions: {stats['total_sessions']}")
    print(f"Total users: {stats['total_users']}")
    print()

    # Test rate limiter
    print("=== Rate Limiter Test ===\n")
    limiter = LoginRateLimiter()

    print("[+] Recording failed attempts...")
    for i in range(6):
        limiter.record_attempt("admin", success=False)
        is_locked, remaining = limiter.is_locked_out("admin")
        print(f"Attempt {i+1}: Locked={is_locked}, Remaining={remaining}s")

    print()
    print("[+] Clearing lockout...")
    limiter.clear_lockout("admin")
    is_locked, remaining = limiter.is_locked_out("admin")
    print(f"Locked: {is_locked}")
