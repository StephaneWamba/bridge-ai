"""Base tool utilities."""

from typing import Any, Optional
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from src.core.logging import logger


class ToolError(Exception):
    """Base exception for tool errors."""

    pass


def handle_tool_error(error: Exception, tool_name: str) -> str:
    """Handle tool errors and return user-friendly messages."""
    logger.error(f"Tool {tool_name} error: {error}", exc_info=True)

    error_msg = str(error)

    # Check for specific error patterns
    if "401" in error_msg or "Unauthorized" in error_msg:
        return f"Authentication failed. Please reconnect your {tool_name} integration."
    elif "429" in error_msg or "rate limit" in error_msg.lower():
        return f"Rate limit exceeded. Please try again in a moment."
    elif "quota" in error_msg.lower():
        return f"API quota exceeded. Please try again later."
    elif "404" in error_msg or "not found" in error_msg.lower() or "does not exist" in error_msg.lower():
        # Extract ID if possible for more helpful message
        if "contact" in error_msg.lower() and "id" in error_msg.lower():
            return f"The contact you're trying to update doesn't exist in HubSpot. Please check the contact ID and try again, or search for contacts to find the correct ID."
        elif "company" in error_msg.lower() and "id" in error_msg.lower():
            return f"The company you're trying to access doesn't exist in HubSpot. Please check the company ID and try again, or search for companies to find the correct ID."
        else:
            return f"The requested resource was not found. Please verify the ID and try again."
    elif "400" in error_msg or "bad request" in error_msg.lower():
        if "invalid" in error_msg.lower() or "validation" in error_msg.lower():
            return f"Invalid request. Please check the provided information (e.g., email format, required fields) and try again."
        return f"Invalid request. Please check your input and try again."
    else:
        return f"Error using {tool_name}: {error_msg}"
