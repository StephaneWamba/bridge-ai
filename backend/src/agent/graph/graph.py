"""LangGraph graph definition."""

from typing import Literal, Optional
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
# Import parent modules first to ensure namespace package is initialized
import langgraph.checkpoint.postgres  # noqa: F401
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langchain_core.tools import BaseTool

from src.agent.state import AgentState
from src.agent.graph.nodes import agent_node
from src.core.logging import logger


def create_agent_graph(
    checkpointer: Optional[AsyncPostgresSaver] = None,
    tools: Optional[list[BaseTool]] = None,
):
    """Create the LangGraph agent graph."""
    # Create graph
    graph = StateGraph(AgentState)

    # Add agent node with tools
    if tools:
        # Create a partial function that includes tools
        from functools import partial
        agent_node_with_tools = partial(agent_node, tools=tools)
        graph.add_node("agent", agent_node_with_tools)

        # Add tool node for executing tools
        tool_node = ToolNode(tools)
        graph.add_node("tools", tool_node)
    else:
        graph.add_node("agent", agent_node)

    # Set entry point
    graph.set_entry_point("agent")

    # Add conditional edges
    if tools:
        # Route to tools if tool calls are made, otherwise end
        def should_continue(state: AgentState) -> Literal["tools", END]:
            """Determine whether to continue to tools or end."""
            messages = state["messages"]
            last_message = messages[-1]

            # Check if the last message has tool calls
            if hasattr(last_message, "tool_calls") and last_message.tool_calls:
                return "tools"
            return END

        graph.add_conditional_edges(
            "agent",
            should_continue,
            {
                "tools": "tools",
                END: END,
            },
        )

        # After tools execute, return to agent
        graph.add_edge("tools", "agent")
    else:
        # Simple flow: agent -> END
        graph.add_edge("agent", END)

    # Compile graph with checkpointer if provided
    if checkpointer:
        compiled_graph = graph.compile(checkpointer=checkpointer)
    else:
        compiled_graph = graph.compile()

    logger.info(
        f"LangGraph agent graph created with {len(tools) if tools else 0} tool(s)")

    return compiled_graph
