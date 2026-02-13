"""
Conversation persistence service.

Stores GraphRAG conversations and messages in PostgreSQL.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from eleutheria_database.services.db import DatabaseService

logger = logging.getLogger(__name__)

# Default settings for new conversations
DEFAULT_SETTINGS = {
    "semantic_k": 5,
    "graph_depth": 1,
    "max_context": 30,
    "use_thinking": False,
    "academic_mode": False,
    "rigor_level": "standard",
    "citation_style": "inline",
}


class ConversationService:
    """CRUD operations for conversations and messages."""

    def __init__(self, db: DatabaseService) -> None:
        self.db = db

    async def ensure_tables(self) -> None:
        """Create conversation tables if they don't exist."""
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS free_will.conversations (
                conversation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID REFERENCES free_will.users(user_id) ON DELETE CASCADE,
                title TEXT NOT NULL DEFAULT 'New conversation',
                settings JSONB NOT NULL DEFAULT '{}',
                message_count INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
        """)
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS free_will.conversation_messages (
                message_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                conversation_id UUID NOT NULL
                    REFERENCES free_will.conversations(conversation_id) ON DELETE CASCADE,
                role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
                content TEXT NOT NULL,
                metadata JSONB DEFAULT '{}',
                created_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
        """)
        await self.db.execute("""
            CREATE INDEX IF NOT EXISTS idx_conversations_user
            ON free_will.conversations(user_id)
        """)
        await self.db.execute("""
            CREATE INDEX IF NOT EXISTS idx_conv_messages_conv
            ON free_will.conversation_messages(conversation_id)
        """)

    async def create(
        self,
        user_id: UUID,
        title: str | None = None,
        settings: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a new conversation."""
        conv_id = uuid4()
        merged_settings = {**DEFAULT_SETTINGS, **(settings or {})}

        await self.db.execute(
            """
            INSERT INTO free_will.conversations
                (conversation_id, user_id, title, settings)
            VALUES ($1, $2, $3, $4)
            """,
            conv_id, user_id,
            title or "New conversation",
            json.dumps(merged_settings),
        )

        return await self.get(conv_id)

    async def get(self, conversation_id: UUID) -> dict[str, Any] | None:
        """Get a single conversation by ID."""
        row = await self.db.fetchrow(
            """
            SELECT conversation_id, user_id, title, settings,
                   message_count, created_at, updated_at
            FROM free_will.conversations
            WHERE conversation_id = $1
            """,
            conversation_id,
        )
        if not row:
            return None
        return _serialize_conversation(row)

    async def list_for_user(
        self, user_id: UUID, limit: int = 50, offset: int = 0
    ) -> tuple[list[dict[str, Any]], int]:
        """List conversations for a user, newest first."""
        rows = await self.db.fetch(
            """
            SELECT conversation_id, user_id, title, settings,
                   message_count, created_at, updated_at
            FROM free_will.conversations
            WHERE user_id = $1
            ORDER BY updated_at DESC
            LIMIT $2 OFFSET $3
            """,
            user_id, limit, offset,
        )
        count_row = await self.db.fetchval(
            "SELECT COUNT(*) FROM free_will.conversations WHERE user_id = $1",
            user_id,
        )
        return [_serialize_conversation(r) for r in rows], int(count_row or 0)

    async def update(
        self,
        conversation_id: UUID,
        title: str | None = None,
        settings: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Update conversation title and/or settings."""
        existing = await self.get(conversation_id)
        if not existing:
            return None

        new_title = title or existing["title"]
        new_settings = {**existing["settings"], **(settings or {})}

        await self.db.execute(
            """
            UPDATE free_will.conversations
            SET title = $1, settings = $2, updated_at = now()
            WHERE conversation_id = $3
            """,
            new_title, json.dumps(new_settings), conversation_id,
        )
        return await self.get(conversation_id)

    async def delete(self, conversation_id: UUID) -> bool:
        """Delete a conversation and its messages."""
        result = await self.db.execute(
            "DELETE FROM free_will.conversations WHERE conversation_id = $1",
            conversation_id,
        )
        return "DELETE 1" in result

    async def add_message(
        self,
        conversation_id: UUID,
        role: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Add a message to a conversation."""
        msg_id = uuid4()
        await self.db.execute(
            """
            INSERT INTO free_will.conversation_messages
                (message_id, conversation_id, role, content, metadata)
            VALUES ($1, $2, $3, $4, $5)
            """,
            msg_id, conversation_id, role, content,
            json.dumps(metadata or {}),
        )
        # Update message count + timestamp
        await self.db.execute(
            """
            UPDATE free_will.conversations
            SET message_count = message_count + 1, updated_at = now()
            WHERE conversation_id = $1
            """,
            conversation_id,
        )
        return {
            "message_id": str(msg_id),
            "conversation_id": str(conversation_id),
            "role": role,
            "content": content,
            "metadata": metadata or {},
        }

    async def get_messages(
        self, conversation_id: UUID, limit: int = 100, offset: int = 0
    ) -> tuple[list[dict[str, Any]], int]:
        """Get messages for a conversation in chronological order."""
        rows = await self.db.fetch(
            """
            SELECT message_id, conversation_id, role, content, metadata, created_at
            FROM free_will.conversation_messages
            WHERE conversation_id = $1
            ORDER BY created_at ASC
            LIMIT $2 OFFSET $3
            """,
            conversation_id, limit, offset,
        )
        count = await self.db.fetchval(
            "SELECT COUNT(*) FROM free_will.conversation_messages WHERE conversation_id = $1",
            conversation_id,
        )
        messages = []
        for r in rows:
            meta = r.get("metadata")
            if isinstance(meta, str):
                meta = json.loads(meta)
            messages.append({
                "message_id": str(r["message_id"]),
                "conversation_id": str(r["conversation_id"]),
                "role": r["role"],
                "content": r["content"],
                "metadata": meta or {},
                "created_at": r["created_at"].isoformat() if isinstance(r["created_at"], datetime) else str(r.get("created_at", "")),
            })
        return messages, int(count or 0)

    async def search(
        self, user_id: UUID, query: str, limit: int = 20
    ) -> tuple[list[dict[str, Any]], int]:
        """Search conversations by message content."""
        rows = await self.db.fetch(
            """
            SELECT DISTINCT c.conversation_id, c.user_id, c.title,
                   c.settings, c.message_count, c.created_at, c.updated_at
            FROM free_will.conversations c
            JOIN free_will.conversation_messages m
                ON c.conversation_id = m.conversation_id
            WHERE c.user_id = $1
              AND m.content ILIKE '%' || $2 || '%'
            ORDER BY c.updated_at DESC
            LIMIT $3
            """,
            user_id, query, limit,
        )
        return [_serialize_conversation(r) for r in rows], len(rows)


def _serialize_conversation(row: dict[str, Any]) -> dict[str, Any]:
    """Convert a DB row to a JSON-friendly dict."""
    settings = row.get("settings")
    if isinstance(settings, str):
        settings = json.loads(settings)

    created = row.get("created_at")
    updated = row.get("updated_at")

    return {
        "conversation_id": str(row["conversation_id"]),
        "user_id": str(row["user_id"]) if row.get("user_id") else None,
        "title": row.get("title", ""),
        "settings": settings or {},
        "message_count": row.get("message_count", 0),
        "created_at": created.isoformat() if isinstance(created, datetime) else str(created or ""),
        "updated_at": updated.isoformat() if isinstance(updated, datetime) else str(updated or ""),
    }
