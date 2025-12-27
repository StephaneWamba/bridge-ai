"""Service for managing conversations and chat history."""

from typing import Optional, List
from datetime import datetime
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.conversation import Conversation
from src.core.logging import logger


class ConversationService:
    """Service for managing conversations."""
    
    @staticmethod
    async def get_or_create_conversation(
        db: AsyncSession,
        user_id: str,
        session_id: str,
    ) -> Conversation:
        """Get existing conversation or create a new one."""
        # Try to find existing conversation
        stmt = select(Conversation).where(
            Conversation.user_id == user_id,
            Conversation.session_id == session_id,
        )
        result = await db.execute(stmt)
        conversation = result.scalar_one_or_none()
        
        if conversation:
            return conversation
        
        # Create new conversation
        conversation = Conversation(
            user_id=user_id,
            session_id=session_id,
            messages=[],  # Start with empty messages array
        )
        db.add(conversation)
        await db.commit()
        await db.refresh(conversation)
        
        logger.info(f"Created new conversation {conversation.id} for user {user_id}, session {session_id}")
        return conversation
    
    @staticmethod
    async def update_conversation_messages(
        db: AsyncSession,
        user_id: str,
        session_id: str,
        messages: List[dict],
    ) -> Conversation:
        """Update conversation with latest messages from LangGraph state."""
        stmt = select(Conversation).where(
            Conversation.user_id == user_id,
            Conversation.session_id == session_id,
        )
        result = await db.execute(stmt)
        conversation = result.scalar_one_or_none()
        
        if not conversation:
            # Create if doesn't exist
            conversation = await ConversationService.get_or_create_conversation(
                db, user_id, session_id
            )
        
        # Convert LangGraph messages to serializable format
        serializable_messages = []
        for msg in messages:
            msg_dict = {
                "type": type(msg).__name__,
                "content": getattr(msg, "content", str(msg)),
            }
            # Add tool calls if present (with id for proper reconstruction)
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                msg_dict["tool_calls"] = [
                    {
                        "id": getattr(tc, "id", "") if hasattr(tc, "id") else (tc.get("id", "") if isinstance(tc, dict) else ""),
                        "name": getattr(tc, "name", "") if hasattr(tc, "name") else (tc.get("name", "") if isinstance(tc, dict) else ""),
                        "args": getattr(tc, "args", {}) if hasattr(tc, "args") else (tc.get("args", {}) if isinstance(tc, dict) else {}),
                    }
                    for tc in msg.tool_calls
                ]
            serializable_messages.append(msg_dict)
        
        # Update conversation
        conversation.messages = serializable_messages
        conversation.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(conversation)
        
        logger.debug(f"Updated conversation {conversation.id} with {len(serializable_messages)} messages")
        return conversation
    
    @staticmethod
    async def get_conversation(
        db: AsyncSession,
        user_id: str,
        session_id: str,
    ) -> Optional[Conversation]:
        """Get a conversation by user_id and session_id."""
        stmt = select(Conversation).where(
            Conversation.user_id == user_id,
            Conversation.session_id == session_id,
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def list_conversations(
        db: AsyncSession,
        user_id: str,
        limit: int = 20,
    ) -> List[Conversation]:
        """List recent conversations for a user."""
        stmt = (
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.updated_at.desc())
            .limit(limit)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())
    
    @staticmethod
    async def delete_conversation(
        db: AsyncSession,
        user_id: str,
        session_id: str,
    ) -> bool:
        """Delete a conversation."""
        stmt = select(Conversation).where(
            Conversation.user_id == user_id,
            Conversation.session_id == session_id,
        )
        result = await db.execute(stmt)
        conversation = result.scalar_one_or_none()
        
        if not conversation:
            return False
        
        await db.delete(conversation)
        await db.commit()
        
        logger.info(f"Deleted conversation {conversation.id} for user {user_id}")
        return True

