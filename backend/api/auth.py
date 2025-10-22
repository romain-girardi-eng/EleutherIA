#!/usr/bin/env python3
"""
Authentication API Routes
Handles JWT authentication and Semativerse permission checking
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import logging
import os
from typing import Optional

from services.auth_service import (
    authenticate_user, 
    create_access_token, 
    get_current_user,
    check_rate_limit,
    get_rate_limit_info,
    User,
    Token
)

logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer()

# Semativerse access key (from environment)
SEMATIVERSE_ACCESS_KEY = os.getenv('SEMATIVERSE_ACCESS_KEY', 'demo-key-change-in-production')


class LoginRequest(BaseModel):
    """Request model for user login"""
    username: str
    password: str


class SemativersePermissionRequest(BaseModel):
    """Request model for checking Semativerse permission"""
    access_key: str


# Authentication dependency
def get_current_user_dependency(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """Dependency to get current authenticated user"""
    token = credentials.credentials
    user = get_current_user(token)
    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


@router.post("/login", response_model=Token)
async def login(login_request: LoginRequest):
    """Authenticate user and return JWT token"""
    try:
        user = authenticate_user(login_request.username, login_request.password)
        if not user:
            raise HTTPException(
                status_code=401,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        access_token = create_access_token(data={"sub": user.username})
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=60 * 24 * 7  # 7 days in seconds
        )
        
    except Exception as e:
        logger.error(f"Error during login: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_user_dependency)):
    """Get current user information"""
    return current_user


@router.get("/rate-limit")
async def get_rate_limit_status(request: Request, current_user: User = Depends(get_current_user_dependency)):
    """Get rate limit status for current user"""
    client_ip = request.client.host
    identifier = f"{current_user.username}:{client_ip}"
    
    rate_info = get_rate_limit_info(identifier)
    return {
        "user": current_user.username,
        "ip": client_ip,
        "rate_limit": rate_info
    }


@router.post("/semativerse/check")
async def check_semativerse_permission(request: SemativersePermissionRequest):
    """
    Check if user has permission to access Semativerse visualization
    🔒 CRITICAL: Semativerse code is private and requires explicit permission
    """
    try:
        # Validate access key
        has_permission = request.access_key == SEMATIVERSE_ACCESS_KEY

        return {
            'has_permission': has_permission,
            'message': 'Access granted' if has_permission else 'Access denied - invalid key'
        }

    except Exception as e:
        logger.error(f"Error checking Semativerse permission: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/semativerse/status")
async def semativerse_status():
    """Get Semativerse service status"""
    return {
        'status': 'available',
        'requires_permission': True,
        'features': [
            '3D/2D visualization',
            'WebGL2 + Three.js + UnrealBloomPass',
            '60 FPS with 5,000+ nodes',
            'Category suns, domain colors',
            'Recording and screenshots',
            'Semantic search integration'
        ]
    }


def verify_semativerse_access(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Dependency for protecting Semativerse endpoints
    Use in routes that require Semativerse access
    """
    token = credentials.credentials
    if token != SEMATIVERSE_ACCESS_KEY:
        raise HTTPException(
            status_code=403,
            detail="Access denied - Semativerse requires permission"
        )
    return token
