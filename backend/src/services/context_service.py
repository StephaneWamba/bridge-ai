"""Service for managing conversation context and tool execution results."""

from typing import Any, Optional, List, Dict
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.conversation_service import ConversationService
from src.core.logging import logger


class ContextService:
    """Service for managing conversation context."""

    @staticmethod
    async def get_conversation_context(
        db: AsyncSession,
        user_id: str,
        session_id: str,
        limit: int = 10,
    ) -> Dict[str, Any]:
        """Get conversation context including recent messages and tool results."""
        try:
            conversation = await ConversationService.get_conversation(
                db=db,
                user_id=user_id,
                session_id=session_id,
            )

            if not conversation or not conversation.messages:
                return {
                    "recent_messages": [],
                    "tool_results": [],
                    "summary": "",
                }

            # Extract recent messages and tool results
            recent_messages = conversation.messages[-limit:] if conversation.messages else []
            tool_results = []

            # Extract tool execution results from messages
            for msg in recent_messages:
                if isinstance(msg, dict):
                    msg_type = msg.get("type", "")
                    if msg_type == "tool":
                        tool_results.append({
                            "tool_name": msg.get("name", "unknown"),
                            "input": msg.get("tool_input", {}),
                            "output": msg.get("content", ""),
                            "success": "error" not in str(msg.get("content", "")).lower(),
                        })

            # Build summary
            summary = ContextService._build_summary(tool_results, recent_messages)

            return {
                "recent_messages": recent_messages,
                "tool_results": tool_results[-5:],  # Last 5 tool results
                "summary": summary,
            }
        except Exception as e:
            logger.warning(f"Failed to get conversation context: {e}", exc_info=True)
            return {
                "recent_messages": [],
                "tool_results": [],
                "summary": "",
            }

    @staticmethod
    def _build_summary(
        tool_results: List[Dict[str, Any]],
        recent_messages: List[Dict[str, Any]],
    ) -> str:
        """Build a context summary from tool results and messages."""
        if not tool_results and not recent_messages:
            return ""

        summary_parts = []

        if tool_results:
            summary_parts.append("Recent tool executions:")
            for result in tool_results[-3:]:  # Last 3 tool results
                tool_name = result.get("tool_name", "unknown")
                success = result.get("success", True)
                status = "✓" if success else "✗"
                summary_parts.append(f"  {status} {tool_name}")

        if recent_messages:
            # Count user queries
            user_queries = [
                msg.get("content", "")
                for msg in recent_messages
                if isinstance(msg, dict) and msg.get("type") == "human"
            ]
            if user_queries:
                summary_parts.append(f"\nRecent user queries: {len(user_queries)}")

        return "\n".join(summary_parts) if summary_parts else ""

