#!/usr/bin/env python3
"""
Authentication Service
Handles JWT token creation, verification, and user management
"""

import os
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Simple user store (in production, use a database)
# Format: {username: {"username": str, "email": str, "hashed_password": str, "role": str}}
USERS_DB = {
    "admin": {
        "username": "admin",
        "email": "admin@example.com",
        "hashed_password": pwd_context.hash("admin123"),  # Change this!
        "role": "admin"
    },
    "researcher": {
        "username": "researcher", 
        "email": "researcher@example.com",
        "hashed_password": pwd_context.hash("research123"),  # Change this!
        "role": "researcher"
    }
}


class User(BaseModel):
    username: str
    email: str
    role: str


class UserInDB(User):
    hashed_password: str


class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int


class TokenData(BaseModel):
    username: Optional[str] = None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def get_user(username: str) -> Optional[UserInDB]:
    """Get user from database"""
    if username in USERS_DB:
        user_dict = USERS_DB[username]
        return UserInDB(**user_dict)
    return None


def authenticate_user(username: str, password: str) -> Optional[UserInDB]:
    """Authenticate a user"""
    user = get_user(username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[TokenData]:
    """Verify and decode a JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        token_data = TokenData(username=username)
        return token_data
    except JWTError:
        return None


def get_current_user(token: str) -> Optional[User]:
    """Get current user from token"""
    token_data = verify_token(token)
    if token_data is None:
        return None
    
    user = get_user(username=token_data.username)
    if user is None:
        return None
    
    return User(username=user.username, email=user.email, role=user.role)


# Rate limiting storage (in production, use Redis)
rate_limit_storage: Dict[str, Dict[str, Any]] = {}


def check_rate_limit(identifier: str, limit: int = 30, window_minutes: int = 15) -> bool:
    """
    Check if user/IP has exceeded rate limit
    Args:
        identifier: user/IP identifier
        limit: max requests per window
        window_minutes: time window in minutes
    Returns:
        True if within limit, False if exceeded
    """
    now = time.time()
    window_seconds = window_minutes * 60
    
    if identifier not in rate_limit_storage:
        rate_limit_storage[identifier] = {
            "requests": [],
            "last_cleanup": now
        }
    
    user_data = rate_limit_storage[identifier]
    requests = user_data["requests"]
    
    # Clean old requests outside the window
    cutoff_time = now - window_seconds
    requests[:] = [req_time for req_time in requests if req_time > cutoff_time]
    
    # Check if limit exceeded
    if len(requests) >= limit:
        return False
    
    # Add current request
    requests.append(now)
    user_data["last_cleanup"] = now
    
    return True


def get_rate_limit_info(identifier: str, limit: int = 30, window_minutes: int = 15) -> Dict[str, Any]:
    """Get rate limit information for an identifier"""
    now = time.time()
    window_seconds = window_minutes * 60
    
    if identifier not in rate_limit_storage:
        return {
            "remaining": limit,
            "reset_time": now + window_seconds,
            "limit": limit
        }
    
    user_data = rate_limit_storage[identifier]
    requests = user_data["requests"]
    
    # Clean old requests
    cutoff_time = now - window_seconds
    requests[:] = [req_time for req_time in requests if req_time > cutoff_time]
    
    remaining = max(0, limit - len(requests))
    reset_time = now + window_seconds if requests else now + window_seconds
    
    return {
        "remaining": remaining,
        "reset_time": reset_time,
        "limit": limit
    }
