"""
Conversation routes — CRUD for GraphRAG conversations and messages.

All endpoints require authentication.
"""

import logging
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field

from backend.dependencies import get_db
from backend.routes.auth import get_current_user
from backend.services.conversation_service import ConversationService
from eleutheria_database.services.db import DatabaseService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["conversations"])


# ---------- Models ----------

class CreateConversationRequest(BaseModel):
    title: str | None = None
    settings: dict[str, Any] | None = None


class UpdateConversationRequest(BaseModel):
    title: str | None = None
    settings: dict[str, Any] | None = None


# ---------- Dependency ----------

async def get_conversation_service(
    db: Annotated[DatabaseService, Depends(get_db)],
) -> ConversationService:
    svc = ConversationService(db)
    await svc.ensure_tables()
    return svc


# ---------- Routes ----------

@router.post("")
async def create_conversation(
    body: CreateConversationRequest,
    request: Request,
    db: Annotated[DatabaseService, Depends(get_db)],
    svc: Annotated[ConversationService, Depends(get_conversation_service)],
) -> dict[str, Any]:
    """Create a new conversation."""
    user = await get_current_user(request, db)
    conv = await svc.create(
        user_id=UUID(str(user["user_id"])),
        title=body.title,
        settings=body.settings,
    )
    return {"success": True, "conversation": conv}


@router.get("")
async def list_conversations(
    request: Request,
    db: Annotated[DatabaseService, Depends(get_db)],
    svc: Annotated[ConversationService, Depends(get_conversation_service)],
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> dict[str, Any]:
    """List conversations for the authenticated user."""
    user = await get_current_user(request, db)
    convs, count = await svc.list_for_user(
        user_id=UUID(str(user["user_id"])),
        limit=limit, offset=offset,
    )
    return {"success": True, "conversations": convs, "count": count}


@router.get("/search")
async def search_conversations(
    request: Request,
    db: Annotated[DatabaseService, Depends(get_db)],
    svc: Annotated[ConversationService, Depends(get_conversation_service)],
    q: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=100),
) -> dict[str, Any]:
    """Search conversations by message content."""
    user = await get_current_user(request, db)
    convs, count = await svc.search(
        user_id=UUID(str(user["user_id"])),
        query=q, limit=limit,
    )
    return {"success": True, "conversations": convs, "count": count}


@router.get("/{conversation_id}")
async def get_conversation(
    conversation_id: UUID,
    request: Request,
    db: Annotated[DatabaseService, Depends(get_db)],
    svc: Annotated[ConversationService, Depends(get_conversation_service)],
) -> dict[str, Any]:
    """Get a specific conversation."""
    user = await get_current_user(request, db)
    conv = await svc.get(conversation_id)
    if not conv or conv.get("user_id") != str(user["user_id"]):
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"success": True, "conversation": conv}


@router.put("/{conversation_id}")
async def update_conversation(
    conversation_id: UUID,
    body: UpdateConversationRequest,
    request: Request,
    db: Annotated[DatabaseService, Depends(get_db)],
    svc: Annotated[ConversationService, Depends(get_conversation_service)],
) -> dict[str, Any]:
    """Update conversation title and/or settings."""
    user = await get_current_user(request, db)
    existing = await svc.get(conversation_id)
    if not existing or existing.get("user_id") != str(user["user_id"]):
        raise HTTPException(status_code=404, detail="Conversation not found")

    conv = await svc.update(conversation_id, title=body.title, settings=body.settings)
    return {"success": True, "conversation": conv}


@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: UUID,
    request: Request,
    db: Annotated[DatabaseService, Depends(get_db)],
    svc: Annotated[ConversationService, Depends(get_conversation_service)],
) -> dict[str, Any]:
    """Delete a conversation and all its messages."""
    user = await get_current_user(request, db)
    existing = await svc.get(conversation_id)
    if not existing or existing.get("user_id") != str(user["user_id"]):
        raise HTTPException(status_code=404, detail="Conversation not found")

    deleted = await svc.delete(conversation_id)
    return {"success": True, "deleted": deleted}


@router.get("/{conversation_id}/messages")
async def get_messages(
    conversation_id: UUID,
    request: Request,
    db: Annotated[DatabaseService, Depends(get_db)],
    svc: Annotated[ConversationService, Depends(get_conversation_service)],
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> dict[str, Any]:
    """Get messages for a conversation in chronological order."""
    user = await get_current_user(request, db)
    existing = await svc.get(conversation_id)
    if not existing or existing.get("user_id") != str(user["user_id"]):
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages, count = await svc.get_messages(conversation_id, limit=limit, offset=offset)
    return {"success": True, "messages": messages, "count": count}
