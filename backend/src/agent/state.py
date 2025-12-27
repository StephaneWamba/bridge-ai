"""Agent state schema for LangGraph."""

from typing import Annotated, TypedDict, Sequence
from langgraph.graph.message import AnyMessage, add_messages


class AgentState(TypedDict):
    """State schema for the agent graph."""

    messages: Annotated[Sequence[AnyMessage], add_messages]
    user_id: str
    session_id: str
    tool_calls: list[dict]
    context: dict  # Used for storing workflow context and intermediate results

