"""Agent endpoints for chat interactions."""

import json
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from src.api.dependencies import get_database_session, get_current_user
from src.models.user import User
from src.agent.orchestrator import AgentOrchestrator
from src.services.conversation_service import ConversationService
from src.core.logging import logger

router = APIRouter(prefix="/api/v1/agent", tags=["agent"])

# Global orchestrator instance
_orchestrator = None


async def get_orchestrator() -> AgentOrchestrator:
    """Get or create agent orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AgentOrchestrator()
    return _orchestrator


class ChatRequest(BaseModel):
    """Chat request model."""
    message: str
    session_id: str | None = None


class ChatResponse(BaseModel):
    """Chat response model."""
    response: str
    session_id: str
    tool_calls: list[dict] = []


@router.post("/chat/stream")
async def chat_stream(
    request: ChatRequest,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_user),
):
    """Process a chat message and stream real-time updates via Server-Sent Events."""
    user_id = str(current_user.id)

    async def event_generator():
        try:
            orchestrator = await get_orchestrator()
            async for event in orchestrator.process_message_stream(
                user_id=user_id,
                message=request.message,
                session_id=request.session_id,
                db=db,
            ):
                # Format as SSE: data: <json>\n\n
                yield f"data: {json.dumps(event)}\n\n"
        except Exception as e:
            logger.error(f"Chat stream error: {e}", exc_info=True)
            error_event = {
                "type": "error",
                "error": str(e),
            }
            yield f"data: {json.dumps(error_event)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable buffering for nginx
        }
    )


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_user),
):
    """Process a chat message and return agent response."""
    user_id = str(current_user.id)

    try:
        orchestrator = await get_orchestrator()
        result = await orchestrator.process_message(
            user_id=user_id,
            message=request.message,
            session_id=request.session_id,
            db=db,
        )

        return ChatResponse(**result)
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Error processing chat: {str(e)}")


@router.get("/conversations")
async def list_conversations(
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_user),
):
    """List recent conversations for the current user."""
    user_id = str(current_user.id)

    try:
        conversations = await ConversationService.list_conversations(
            db=db,
            user_id=user_id,
            limit=limit,
        )

        result_conversations = []
        for conv in conversations:
            # Extract title from first user message (optimized: early break)
            title = "New Conversation"
            preview = ""

            if conv.messages:
                messages_list = conv.messages if isinstance(
                    conv.messages, list) else []

                # Find first human message for title (optimized: single pass when possible)
                for msg in messages_list:
                    if not isinstance(msg, dict):
                        continue
                    msg_type = msg.get("type", "").lower()
                    if msg_type not in ["humanmessage", "human"]:
                        continue

                    content = msg.get("content", "")
                    if not content or not isinstance(content, str):
                        continue

                    clean_content = content.strip()
                    # Skip raw JSON/dict strings or empty content
                    if (len(clean_content) == 0 or
                            clean_content.startswith(("{", "'", '"'))):
                        continue

                    # Use first 60 chars for more informative title
                    title = clean_content[:60] + \
                        "..." if len(clean_content) > 60 else clean_content
                    break

                # Get last non-empty message content for preview (optimized: reverse iteration)
                for msg in reversed(messages_list):
                    if not isinstance(msg, dict):
                        continue
                    msg_type = msg.get("type", "").lower()
                    if msg_type in ["systemmessage", "system"]:
                        continue

                    content = msg.get("content", "")
                    if not content or not isinstance(content, str):
                        continue

                    clean_content = content.strip()
                    # Skip raw JSON/dict strings or empty content
                    if (len(clean_content) == 0 or
                            clean_content.startswith(("{", "'", '"'))):
                        continue

                    # Use first 120 chars for preview
                    preview = clean_content[:120] + \
                        "..." if len(clean_content) > 120 else clean_content
                    break

            result_conversations.append({
                "id": str(conv.id),
                "session_id": conv.session_id,
                "title": title,
                "preview": preview,
                "message_count": len(conv.messages) if conv.messages else 0,
                "created_at": conv.created_at.isoformat(),
                "updated_at": conv.updated_at.isoformat(),
            })

        return {
            "conversations": result_conversations
        }
    except Exception as e:
        logger.error(f"Error listing conversations: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Error listing conversations: {str(e)}")


@router.get("/conversations/{session_id}/messages")
async def get_conversation_messages(
    session_id: str,
    db: AsyncSession = Depends(get_database_session),
    current_user: User = Depends(get_current_user),
):
    """Get messages for a specific conversation by session_id."""
    user_id = str(current_user.id)

    try:
        conversation = await ConversationService.get_conversation(
            db=db,
            user_id=user_id,
            session_id=session_id,
        )

        if not conversation:
            raise HTTPException(
                status_code=404, detail="Conversation not found")

        # Convert messages to frontend format
        frontend_messages = []
        for idx, msg in enumerate(conversation.messages or []):
            if isinstance(msg, dict):
                msg_type = msg.get("type", "").lower()
                content = msg.get("content", "")

                # Convert to frontend message format
                if msg_type in ["humanmessage", "human"]:
                    frontend_messages.append({
                        "id": f"{session_id}-{idx}",
                        "role": "user",
                        "content": content if isinstance(content, str) else str(content),
                        "timestamp": conversation.updated_at.isoformat(),
                    })
                elif msg_type in ["aimessage", "ai"]:
                    # Extract tool calls if present
                    tool_calls = []
                    if "tool_calls" in msg and msg["tool_calls"]:
                        tool_calls = [
                            {
                                "tool_name": tc.get("name", ""),
                                "tool_input": tc.get("args", {}),
                                "tool_id": tc.get("id", ""),
                                "status": "success",
                            }
                            for tc in msg["tool_calls"]
                        ]

                    frontend_messages.append({
                        "id": f"{session_id}-{idx}",
                        "role": "assistant",
                        "content": content if isinstance(content, str) else str(content),
                        "tool_calls": tool_calls,
                        "timestamp": conversation.updated_at.isoformat(),
                    })

        return {
            "session_id": session_id,
            "messages": frontend_messages,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error getting conversation messages: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Error getting conversation messages: {str(e)}")
