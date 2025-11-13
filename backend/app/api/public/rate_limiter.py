#!/usr/bin/env python3
"""
Rate Limiter for Public API
Fixed Window Counter implementation for rate limiting
"""

import logging
import time
from typing import Dict, Tuple
from collections import defaultdict
from fastapi import HTTPException, Response

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Fixed Window Counter rate limiter
    Tracks requests per user in fixed time windows
    """
    
    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        """
        Initialize rate limiter
        
        Args:
            max_requests: Maximum number of requests allowed per window
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        # Store: {user_id: [(timestamp, count), ...]}
        # Using list of tuples for simplicity (can be optimized with Redis in production)
        self._requests: Dict[str, list] = defaultdict(list)
        logger.info(f"RateLimiter initialized: {max_requests} requests per {window_seconds} seconds")
    
    def _cleanup_old_requests(self, user_id: str, current_time: float):
        """Remove requests outside the current time window"""
        cutoff_time = current_time - self.window_seconds
        self._requests[user_id] = [
            (ts, count) for ts, count in self._requests[user_id]
            if ts > cutoff_time
        ]
    
    def check_rate_limit(self, user_id: str) -> Tuple[bool, Dict[str, int]]:
        """
        Check if user has exceeded rate limit
        
        Args:
            user_id: User identifier (from Firebase token)
            
        Returns:
            Tuple of (is_allowed, rate_limit_info)
            rate_limit_info contains: limit, remaining, reset_time
        """
        current_time = time.time()
        
        # Clean up old requests outside the window
        self._cleanup_old_requests(user_id, current_time)
        
        # Count requests in current window
        current_count = sum(count for _, count in self._requests[user_id])
        
        # Calculate reset time (end of current window)
        if self._requests[user_id]:
            oldest_request_time = min(ts for ts, _ in self._requests[user_id])
            reset_time = int(oldest_request_time + self.window_seconds)
        else:
            reset_time = int(current_time + self.window_seconds)
        
        # Check if limit exceeded
        is_allowed = current_count < self.max_requests
        remaining = max(0, self.max_requests - current_count)
        
        rate_limit_info = {
            "limit": self.max_requests,
            "remaining": remaining,
            "reset": reset_time
        }
        
        if is_allowed:
            # Record this request
            self._requests[user_id].append((current_time, 1))
            logger.debug(f"Rate limit check passed for user {user_id}: {remaining} remaining")
        else:
            logger.warning(
                f"Rate limit exceeded for user {user_id}: "
                f"{current_count}/{self.max_requests} requests in window"
            )
        
        return is_allowed, rate_limit_info
    
    def add_rate_limit_headers(self, response: Response, rate_limit_info: Dict[str, int]):
        """
        Add rate limit headers to response
        
        Args:
            response: FastAPI Response object
            rate_limit_info: Rate limit information dict
        """
        response.headers["X-RateLimit-Limit"] = str(rate_limit_info["limit"])
        response.headers["X-RateLimit-Remaining"] = str(rate_limit_info["remaining"])
        response.headers["X-RateLimit-Reset"] = str(rate_limit_info["reset"])


# Global rate limiter instance
# Configuration: 10 requests per 60 seconds (can be adjusted via environment variables)
import os
max_requests = int(os.getenv("API_RATE_LIMIT_MAX", "10"))
window_seconds = int(os.getenv("API_RATE_LIMIT_WINDOW", "60"))

rate_limiter = RateLimiter(max_requests=max_requests, window_seconds=window_seconds)

