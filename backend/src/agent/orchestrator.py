"""Agent orchestrator - main entry point for agent interactions."""

import uuid
from typing import Optional
from langchain_core.messages import HumanMessage
from sqlalchemy.ext.asyncio import AsyncSession

from src.agent.state import AgentState
from src.agent.graph.graph import create_agent_graph
from src.agent.checkpoint import get_checkpointer
from src.agent.tools.hubspot_tools import get_hubspot_tools
from src.agent.tools.gmail_tools import get_gmail_tools
from src.agent.tools.calendar_tools import get_calendar_tools
from src.agent.tools.discord_tools import get_discord_tools
from src.agent.tools.drive_tools import get_drive_tools
from src.agent.tools.meeting_tools import get_meeting_tools
from src.services.conversation_service import ConversationService
from src.services.context_service import ContextService
from src.core.logging import logger


class AgentOrchestrator:
    """Orchestrator for managing agent conversations and state."""

    def __init__(self):
        """Initialize the agent orchestrator."""
        self._checkpointer_cm = None
        self._checkpointer = None
        self._graph = None

    async def _get_checkpointer(self):
        """Get or create checkpointer."""
        if self._checkpointer is None:
            # Create context manager and enter it
            self._checkpointer_cm = get_checkpointer()
            self._checkpointer = await self._checkpointer_cm.__aenter__()
        return self._checkpointer

    async def _get_graph(self, db: AsyncSession, user_id: str):
        """Get or create graph with checkpointer and tools."""
        # Always recreate graph with latest tools (in case integrations changed)
        checkpointer = await self._get_checkpointer()

        # Get tools from all integrations
        hubspot_tools = await get_hubspot_tools(db, user_id)
        gmail_tools = await get_gmail_tools(db, user_id)
        calendar_tools = await get_calendar_tools(db, user_id)
        discord_tools = await get_discord_tools(db, user_id)
        drive_tools = await get_drive_tools(db, user_id)
        meeting_tools = await get_meeting_tools(db, user_id)
        all_tools = hubspot_tools + gmail_tools + calendar_tools + discord_tools + drive_tools + meeting_tools

        # Create graph with tools
        self._graph = create_agent_graph(
            checkpointer=checkpointer, tools=all_tools)
        return self._graph

    async def process_message_stream(
        self,
        user_id: str,
        message: str,
        session_id: Optional[str] = None,
        db: Optional[AsyncSession] = None,
    ):
        """Process a user message and stream updates via async generator."""
        if not db:
            raise ValueError("Database session is required")

        # Generate session ID if not provided
        if not session_id:
            session_id = str(uuid.uuid4())

        # Get conversation context for enhanced awareness
        context_data = await ContextService.get_conversation_context(
            db=db,
            user_id=user_id,
            session_id=session_id,
        )

        # Create config for this conversation thread
        config = {
            "configurable": {
                "thread_id": session_id,
            },
            "recursion_limit": 50,  # Increase recursion limit to allow more tool calls in complex workflows
        }

        # Create initial state (TypedDict format) with only the new user message
        initial_state: AgentState = {
            "messages": [HumanMessage(content=message)],
            "user_id": user_id,
            "session_id": session_id,
            "tool_calls": [],
            "context": context_data,
        }

        try:
            # Get graph with checkpointer and tools
            graph = await self._get_graph(db, user_id)

            # Track tool calls that have been emitted to avoid duplicates
            final_state = None

            # Stream graph execution to get real-time updates
            try:
                async for event in graph.astream(initial_state, config=config):
                    # Extract node name and state from event
                    for node_name, node_state in event.items():
                        final_state = node_state  # Keep track of latest state
                        # No tool call feedback - just stream the final response
            except Exception as checkpoint_error:
                error_str = str(checkpoint_error)
                if "tool_call_id" in error_str and "did not have response" in error_str:
                    logger.warning(
                        f"Corrupted checkpoint state detected for session {session_id}. Creating new session.")
                    session_id = str(uuid.uuid4())
                    config = {
                        "configurable": {"thread_id": session_id},
                        "recursion_limit": 50,
                    }
                    # Retry with new session - stream again
                    async for event in graph.astream(initial_state, config=config):
                        for node_name, node_state in event.items():
                            final_state = node_state
                            # No tool call feedback - just stream the final response
                else:
                    raise

            # Extract final response from last state
            if final_state:
                messages = final_state.get("messages", [])
                response_text = "No response generated"
                tool_calls_made = []

                from langchain_core.messages import AIMessage
                for msg in reversed(messages):
                    if isinstance(msg, AIMessage) and msg.content:
                        response_text = msg.content
                        if hasattr(msg, "tool_calls") and msg.tool_calls:
                            tool_calls_made = [
                                {
                                    "tool_name": getattr(tc, "name", "") if hasattr(tc, "name") else (tc.get("name") if isinstance(tc, dict) else ""),
                                    "tool_input": getattr(tc, "args", {}) if hasattr(tc, "args") else (tc.get("args", {}) if isinstance(tc, dict) else {}),
                                }
                                for tc in msg.tool_calls
                            ]
                        break

                # Persist conversation to database
                try:
                    from langchain_core.messages import SystemMessage, ToolMessage
                    serializable_messages = []
                    for msg in messages:
                        if isinstance(msg, (HumanMessage, AIMessage, SystemMessage, ToolMessage)):
                            msg_dict = {
                                "type": type(msg).__name__,
                                "content": getattr(msg, "content", ""),
                            }
                            if isinstance(msg, ToolMessage):
                                msg_dict["tool_call_id"] = getattr(
                                    msg, "tool_call_id", "")
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

                    await ConversationService.update_conversation_messages(
                        db=db,
                        user_id=user_id,
                        session_id=session_id,
                        messages=serializable_messages,
                    )
                except Exception as e:
                    logger.warning(
                        f"Failed to persist conversation: {e}", exc_info=True)

                # Emit final response
                yield {
                    "type": "response",
                    "response": response_text,
                    "session_id": session_id,
                }

        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            yield {
                "type": "error",
                "error": str(e),
                "session_id": session_id,
            }

    async def process_message(
        self,
        user_id: str,
        message: str,
        session_id: Optional[str] = None,
        db: Optional[AsyncSession] = None,
    ) -> dict:
        """Process a user message and return agent response."""
        if not db:
            raise ValueError("Database session is required")

        # Generate session ID if not provided
        if not session_id:
            session_id = str(uuid.uuid4())

        # Get conversation context for enhanced awareness
        context_data = await ContextService.get_conversation_context(
            db=db,
            user_id=user_id,
            session_id=session_id,
        )

        # Create config for this conversation thread
        config = {
            "configurable": {
                "thread_id": session_id,
            },
            "recursion_limit": 50,  # Increase recursion limit to allow more tool calls in complex workflows
        }

        # Don't manually load previous messages - let LangGraph's checkpointer handle state restoration
        # The checkpointer will automatically restore the state for this thread_id and merge it with initial_state
        # We only provide the NEW user message; the checkpointer will add it to the existing conversation

        # Create initial state (TypedDict format) with only the new user message
        initial_state: AgentState = {
            # Only the new message - checkpointer handles the rest
            "messages": [HumanMessage(content=message)],
            "user_id": user_id,
            "session_id": session_id,
            "tool_calls": [],
            "context": context_data,  # Store context data for reference
        }

        try:
            # Get graph with checkpointer and tools
            graph = await self._get_graph(db, user_id)

            # Invoke graph with checkpointing
            # result is an AgentState TypedDict (which is a dict)
            try:
                result = await graph.ainvoke(
                    initial_state,
                    config=config,
                )
            except Exception as checkpoint_error:
                # If there's a corrupted checkpoint state (e.g., tool_calls without responses),
                # create a new session_id and retry with fresh state
                error_str = str(checkpoint_error)
                if "tool_call_id" in error_str and "did not have response" in error_str:
                    logger.warning(
                        f"Corrupted checkpoint state detected for session {session_id}. Creating new session."
                    )
                    # Generate a new session ID
                    session_id = str(uuid.uuid4())
                    config = {
                        "configurable": {
                            "thread_id": session_id,
                        }
                    }
                    # Retry with new session
                    result = await graph.ainvoke(
                        initial_state,
                        config=config,
                    )
                else:
                    # Re-raise if it's a different error
                    raise

            # Log the result structure for debugging
            logger.debug(
                f"Graph result type: {type(result)}, keys: {result.keys() if isinstance(result, dict) else 'not a dict'}")

            # Extract response (get the last AI message)
            # AgentState is a TypedDict, which is a dict, so use dictionary access
            if not isinstance(result, dict):
                raise ValueError(
                    f"Expected dict from graph.ainvoke(), got {type(result)}")

            messages = result.get("messages", [])
            response_text = "No response generated"
            tool_calls_made = []

            # Find the last AI message with content
            from langchain_core.messages import AIMessage
            for msg in reversed(messages):
                # Check if it's an AIMessage with content
                if isinstance(msg, AIMessage) and msg.content:
                    response_text = msg.content
                    # Check for tool calls in this message
                    if hasattr(msg, "tool_calls") and msg.tool_calls:
                        tool_calls_made = [
                            {
                                "tool_name": getattr(tc, "name", "") if hasattr(tc, "name") else (tc.get("name") if isinstance(tc, dict) else ""),
                                "tool_input": getattr(tc, "args", {}) if hasattr(tc, "args") else (tc.get("args") if isinstance(tc, dict) else {}),
                            }
                            for tc in msg.tool_calls
                        ]
                    break
                # Fallback: if it's a dict-like object with content
                elif isinstance(msg, dict) and msg.get("content"):
                    response_text = msg["content"]
                    break
                # Fallback: if it has content attribute
                elif hasattr(msg, "content") and msg.content:
                    response_text = msg.content
                    break

            logger.info(
                f"Agent processed message for user {user_id}, session {session_id}")

            # Persist conversation to database
            try:
                # Convert messages to serializable format
                from langchain_core.messages import AIMessage, SystemMessage, ToolMessage
                serializable_messages = []
                for msg in messages:
                    if isinstance(msg, (HumanMessage, AIMessage, SystemMessage, ToolMessage)):
                        msg_dict = {
                            "type": type(msg).__name__,
                            "content": getattr(msg, "content", ""),
                        }
                        if isinstance(msg, ToolMessage):
                            msg_dict["tool_call_id"] = getattr(
                                msg, "tool_call_id", "")
                        if hasattr(msg, "tool_calls") and msg.tool_calls:
                            # Save tool_calls with id, name, and args for proper reconstruction
                            msg_dict["tool_calls"] = [
                                {
                                    "id": getattr(tc, "id", "") if hasattr(tc, "id") else (tc.get("id", "") if isinstance(tc, dict) else ""),
                                    "name": getattr(tc, "name", "") if hasattr(tc, "name") else (tc.get("name", "") if isinstance(tc, dict) else ""),
                                    "args": getattr(tc, "args", {}) if hasattr(tc, "args") else (tc.get("args", {}) if isinstance(tc, dict) else {}),
                                }
                                for tc in msg.tool_calls
                            ]
                        serializable_messages.append(msg_dict)
                    elif isinstance(msg, dict):
                        serializable_messages.append(msg)

                await ConversationService.update_conversation_messages(
                    db=db,
                    user_id=user_id,
                    session_id=session_id,
                    messages=serializable_messages,
                )
            except Exception as e:
                # Log but don't fail the request if conversation persistence fails
                logger.warning(
                    f"Failed to persist conversation: {e}", exc_info=True)

            return {
                "response": response_text,
                "session_id": session_id,
                "tool_calls": tool_calls_made,
            }
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            raise
