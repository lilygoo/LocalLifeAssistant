#!/usr/bin/env python3
"""
Authentication dependencies for public API
"""

import logging
from typing import Optional
from fastapi import HTTPException, Header, Depends, Response
from firebase_admin import auth

from ...user_manager import UserManager
from .rate_limiter import rate_limiter

logger = logging.getLogger(__name__)

# Initialize user manager for token verification
user_manager = UserManager()


async def verify_firebase_token(
    authorization: Optional[str] = Header(None)
) -> str:
    """
    Verify Firebase Auth token from Authorization header
    Returns user_id if valid, raises HTTPException if invalid
    
    Expected header format: Authorization: Bearer <token>
    """
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Authorization header required"
        )
    
    # Extract token from "Bearer <token>" format
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization header format. Expected: Bearer <token>"
        )
    
    token = parts[1]
    
    try:
        # Verify token using Firebase Admin SDK
        user_data = user_manager.authenticate_with_token(token)
        user_id = user_data.get("user_id")
        
        if not user_id:
            raise HTTPException(
                status_code=401,
                detail="User ID not found in token"
            )
        
        logger.info(f"User authenticated via Firebase token: {user_id}")
        return user_id
        
    except ValueError as e:
        logger.warning(f"Token verification failed: {e}")
        raise HTTPException(
            status_code=401,
            detail=f"Invalid authentication token: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error during token verification: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Internal server error during authentication"
        )


async def rate_limit(
    user_id: str = Depends(verify_firebase_token)
) -> tuple[str, dict]:
    """
    Rate limiting dependency
    Checks if user has exceeded rate limit
    
    Returns (user_id, rate_limit_info) if within rate limit, raises HTTPException if exceeded
    rate_limit_info can be used to add headers in the endpoint handler
    """
    is_allowed, rate_limit_info = rate_limiter.check_rate_limit(user_id)
    
    if not is_allowed:
        logger.warning(f"Rate limit exceeded for user {user_id}")
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Maximum {rate_limit_info['limit']} requests per {rate_limiter.window_seconds} seconds. Try again after {rate_limit_info['reset']}.",
            headers={
                "X-RateLimit-Limit": str(rate_limit_info["limit"]),
                "X-RateLimit-Remaining": str(rate_limit_info["remaining"]),
                "X-RateLimit-Reset": str(rate_limit_info["reset"])
            }
        )
    
    return user_id, rate_limit_info
