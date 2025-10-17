#!/usr/bin/env python3
"""
Authentication API Routes
Handles Semativerse permission checking
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import logging
import os

logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer()

# Semativerse access key (from environment)
SEMATIVERSE_ACCESS_KEY = os.getenv('SEMATIVERSE_ACCESS_KEY', 'demo-key-change-in-production')


class SemativersePermissionRequest(BaseModel):
    """Request model for checking Semativerse permission"""
    access_key: str


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
