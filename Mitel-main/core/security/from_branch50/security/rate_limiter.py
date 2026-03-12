#!/usr/bin/env python3
"""
Rate Limiting Framework
Prevents abuse by limiting request rates per IP, user, and endpoint.
"""

import time
import threading
from collections import defaultdict, deque
from typing import Dict, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class RateLimitConfig:
    """Rate limit configuration"""
    max_requests: int
    window_seconds: int
    description: str


@dataclass
class RateLimitBucket:
    """Token bucket for rate limiting"""
    config: RateLimitConfig
    requests: deque = field(default_factory=deque)
    lock: threading.Lock = field(default_factory=threading.Lock)

    def is_allowed(self) -> Tuple[bool, Optional[int]]:
        """
        Check if request is allowed

        Returns:
            Tuple of (allowed, retry_after_seconds)
        """
        with self.lock:
            now = time.time()
            window_start = now - self.config.window_seconds

            # Remove old requests outside the window
            while self.requests and self.requests[0] < window_start:
                self.requests.popleft()

            # Check if under limit
            if len(self.requests) < self.config.max_requests:
                self.requests.append(now)
                return True, None

            # Calculate retry after
            if self.requests:
                oldest_request = self.requests[0]
                retry_after = int(oldest_request + self.config.window_seconds - now) + 1
                return False, retry_after

            return False, self.config.window_seconds

    def reset(self):
        """Reset the bucket"""
        with self.lock:
            self.requests.clear()


class RateLimiter:
    """
    Comprehensive rate limiting system
    - Per-IP rate limiting
    - Per-user rate limiting
    - Per-endpoint rate limiting
    - Automatic cleanup of old entries
    """

    # Default rate limit configurations
    DEFAULT_LIMITS = {
        'general': RateLimitConfig(
            max_requests=100,
            window_seconds=60,
            description="100 requests per minute per IP"
        ),
        'auth_failure': RateLimitConfig(
            max_requests=10,
            window_seconds=60,
            description="10 failed logins per minute per IP"
        ),
        'tool_execution': RateLimitConfig(
            max_requests=5,
            window_seconds=60,
            description="5 tool executions per minute per user"
        ),
        'file_sync': RateLimitConfig(
            max_requests=1000,
            window_seconds=3600,
            description="1000 file sync requests per hour"
        ),
        'api_endpoint': RateLimitConfig(
            max_requests=60,
            window_seconds=60,
            description="60 requests per minute per endpoint"
        ),
    }

    def __init__(self):
        """Initialize rate limiter"""
        self.ip_buckets: Dict[str, Dict[str, RateLimitBucket]] = defaultdict(dict)
        self.user_buckets: Dict[str, Dict[str, RateLimitBucket]] = defaultdict(dict)
        self.endpoint_buckets: Dict[str, RateLimitBucket] = {}
        self.global_lock = threading.Lock()

        # Start cleanup thread
        self.cleanup_interval = 300  # 5 minutes
        self.cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self.cleanup_thread.start()

    def _get_or_create_bucket(
        self,
        buckets_dict: Dict,
        key: str,
        limit_type: str
    ) -> RateLimitBucket:
        """Get or create a rate limit bucket"""
        if limit_type not in buckets_dict.get(key, {}):
            with self.global_lock:
                if key not in buckets_dict:
                    buckets_dict[key] = {}
                if limit_type not in buckets_dict[key]:
                    config = self.DEFAULT_LIMITS.get(
                        limit_type,
                        self.DEFAULT_LIMITS['general']
                    )
                    buckets_dict[key][limit_type] = RateLimitBucket(config=config)

        return buckets_dict[key][limit_type]

    def check_rate_limit_ip(
        self,
        ip_address: str,
        limit_type: str = 'general'
    ) -> Tuple[bool, Optional[int], str]:
        """
        Check rate limit for an IP address

        Args:
            ip_address: IP address to check
            limit_type: Type of limit to apply

        Returns:
            Tuple of (allowed, retry_after_seconds, message)
        """
        bucket = self._get_or_create_bucket(self.ip_buckets, ip_address, limit_type)
        allowed, retry_after = bucket.is_allowed()

        if not allowed:
            message = f"Rate limit exceeded: {bucket.config.description}. Retry after {retry_after} seconds."
            return False, retry_after, message

        return True, None, "OK"

    def check_rate_limit_user(
        self,
        user_id: str,
        limit_type: str = 'general'
    ) -> Tuple[bool, Optional[int], str]:
        """
        Check rate limit for a user

        Args:
            user_id: User identifier to check
            limit_type: Type of limit to apply

        Returns:
            Tuple of (allowed, retry_after_seconds, message)
        """
        bucket = self._get_or_create_bucket(self.user_buckets, user_id, limit_type)
        allowed, retry_after = bucket.is_allowed()

        if not allowed:
            message = f"Rate limit exceeded: {bucket.config.description}. Retry after {retry_after} seconds."
            return False, retry_after, message

        return True, None, "OK"

    def check_rate_limit_endpoint(
        self,
        endpoint: str,
        limit_type: str = 'api_endpoint'
    ) -> Tuple[bool, Optional[int], str]:
        """
        Check rate limit for an endpoint

        Args:
            endpoint: Endpoint path to check
            limit_type: Type of limit to apply

        Returns:
            Tuple of (allowed, retry_after_seconds, message)
        """
        if endpoint not in self.endpoint_buckets:
            with self.global_lock:
                if endpoint not in self.endpoint_buckets:
                    config = self.DEFAULT_LIMITS.get(
                        limit_type,
                        self.DEFAULT_LIMITS['api_endpoint']
                    )
                    self.endpoint_buckets[endpoint] = RateLimitBucket(config=config)

        bucket = self.endpoint_buckets[endpoint]
        allowed, retry_after = bucket.is_allowed()

        if not allowed:
            message = f"Endpoint rate limit exceeded: {bucket.config.description}. Retry after {retry_after} seconds."
            return False, retry_after, message

        return True, None, "OK"

    def check_combined_rate_limit(
        self,
        ip_address: str,
        user_id: Optional[str] = None,
        endpoint: Optional[str] = None,
        limit_type: str = 'general'
    ) -> Tuple[bool, Optional[int], str]:
        """
        Check multiple rate limits in sequence

        Args:
            ip_address: IP address to check
            user_id: Optional user identifier
            endpoint: Optional endpoint path
            limit_type: Type of limit to apply

        Returns:
            Tuple of (allowed, retry_after_seconds, message)
        """
        # Check IP rate limit
        allowed, retry_after, message = self.check_rate_limit_ip(ip_address, limit_type)
        if not allowed:
            return False, retry_after, message

        # Check user rate limit if user_id provided
        if user_id:
            allowed, retry_after, message = self.check_rate_limit_user(user_id, limit_type)
            if not allowed:
                return False, retry_after, message

        # Check endpoint rate limit if endpoint provided
        if endpoint:
            allowed, retry_after, message = self.check_rate_limit_endpoint(endpoint, limit_type)
            if not allowed:
                return False, retry_after, message

        return True, None, "OK"

    def record_auth_failure(self, ip_address: str) -> Tuple[bool, Optional[int], str]:
        """
        Record an authentication failure

        Args:
            ip_address: IP address of failed attempt

        Returns:
            Tuple of (allowed, retry_after_seconds, message)
        """
        return self.check_rate_limit_ip(ip_address, 'auth_failure')

    def record_tool_execution(self, user_id: str) -> Tuple[bool, Optional[int], str]:
        """
        Record a tool execution

        Args:
            user_id: User executing the tool

        Returns:
            Tuple of (allowed, retry_after_seconds, message)
        """
        return self.check_rate_limit_user(user_id, 'tool_execution')

    def record_file_sync(self, ip_address: str) -> Tuple[bool, Optional[int], str]:
        """
        Record a file sync request

        Args:
            ip_address: IP address making the request

        Returns:
            Tuple of (allowed, retry_after_seconds, message)
        """
        return self.check_rate_limit_ip(ip_address, 'file_sync')

    def reset_ip_limits(self, ip_address: str, limit_type: Optional[str] = None):
        """
        Reset rate limits for an IP address

        Args:
            ip_address: IP address to reset
            limit_type: Optional specific limit type to reset (None = all)
        """
        with self.global_lock:
            if ip_address in self.ip_buckets:
                if limit_type:
                    if limit_type in self.ip_buckets[ip_address]:
                        self.ip_buckets[ip_address][limit_type].reset()
                else:
                    for bucket in self.ip_buckets[ip_address].values():
                        bucket.reset()

    def reset_user_limits(self, user_id: str, limit_type: Optional[str] = None):
        """
        Reset rate limits for a user

        Args:
            user_id: User identifier to reset
            limit_type: Optional specific limit type to reset (None = all)
        """
        with self.global_lock:
            if user_id in self.user_buckets:
                if limit_type:
                    if limit_type in self.user_buckets[user_id]:
                        self.user_buckets[user_id][limit_type].reset()
                else:
                    for bucket in self.user_buckets[user_id].values():
                        bucket.reset()

    def get_rate_limit_status(self, ip_address: str) -> Dict[str, Dict]:
        """
        Get current rate limit status for an IP

        Args:
            ip_address: IP address to check

        Returns:
            Dictionary with status for each limit type
        """
        status = {}
        if ip_address in self.ip_buckets:
            for limit_type, bucket in self.ip_buckets[ip_address].items():
                with bucket.lock:
                    now = time.time()
                    window_start = now - bucket.config.window_seconds

                    # Count active requests
                    active_requests = sum(
                        1 for req_time in bucket.requests
                        if req_time >= window_start
                    )

                    status[limit_type] = {
                        'current': active_requests,
                        'limit': bucket.config.max_requests,
                        'window': bucket.config.window_seconds,
                        'description': bucket.config.description,
                    }

        return status

    def _cleanup_loop(self):
        """Background thread to cleanup old buckets"""
        while True:
            time.sleep(self.cleanup_interval)
            self._cleanup_old_buckets()

    def _cleanup_old_buckets(self):
        """Remove buckets with no recent activity"""
        with self.global_lock:
            now = time.time()

            # Cleanup IP buckets
            ips_to_remove = []
            for ip, buckets in self.ip_buckets.items():
                # Check if all buckets are empty or old
                all_empty = True
                for bucket in buckets.values():
                    with bucket.lock:
                        if bucket.requests:
                            # Check if newest request is old
                            newest = bucket.requests[-1]
                            if now - newest < bucket.config.window_seconds * 2:
                                all_empty = False
                                break

                if all_empty:
                    ips_to_remove.append(ip)

            for ip in ips_to_remove:
                del self.ip_buckets[ip]

            # Cleanup user buckets
            users_to_remove = []
            for user, buckets in self.user_buckets.items():
                all_empty = True
                for bucket in buckets.values():
                    with bucket.lock:
                        if bucket.requests:
                            newest = bucket.requests[-1]
                            if now - newest < bucket.config.window_seconds * 2:
                                all_empty = False
                                break

                if all_empty:
                    users_to_remove.append(user)

            for user in users_to_remove:
                del self.user_buckets[user]


# Singleton instance
rate_limiter = RateLimiter()


# Convenience functions
def check_rate_limit(
    ip_address: str,
    user_id: Optional[str] = None,
    endpoint: Optional[str] = None,
    limit_type: str = 'general'
) -> Tuple[bool, Optional[int], str]:
    """Check combined rate limits"""
    return rate_limiter.check_combined_rate_limit(ip_address, user_id, endpoint, limit_type)


def record_auth_failure(ip_address: str) -> Tuple[bool, Optional[int], str]:
    """Record authentication failure"""
    return rate_limiter.record_auth_failure(ip_address)


def record_tool_execution(user_id: str) -> Tuple[bool, Optional[int], str]:
    """Record tool execution"""
    return rate_limiter.record_tool_execution(user_id)


def record_file_sync(ip_address: str) -> Tuple[bool, Optional[int], str]:
    """Record file sync request"""
    return rate_limiter.record_file_sync(ip_address)
