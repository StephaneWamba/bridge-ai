"""Meeting analysis tools for summarizing transcripts and extracting action items."""

from typing import Optional, Type, List
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
from pydantic_core import ValidationError

from src.core.config import settings
from src.core.logging import logger
from langchain_openai import ChatOpenAI


class SummarizeMeetingInput(BaseModel):
    """Input for summarizing a meeting transcript."""

    transcript: str = Field(description="Meeting transcript text to summarize")
    format: Optional[str] = Field(
        default="markdown",
        description="Output format: 'markdown' (default) or 'plain'",
    )


class SummarizeMeetingTool(BaseTool):
    """Tool for summarizing meeting transcripts using LLM."""

    name: str = "summarize_meeting"
    description: str = (
        "Generate a comprehensive summary of a meeting transcript. "
        "Returns key points, decisions, topics discussed, and main takeaways. "
        "Provide the full transcript text as input."
    )
    args_schema: Type[BaseModel] = SummarizeMeetingInput
    model_config = {"extra": "allow"}

    def __init__(self, **kwargs):
        """Initialize the summarization tool."""
        super().__init__(**kwargs)

    def _run(self, transcript: str, format: str = "markdown") -> str:
        """Synchronous version - not used, but required by BaseTool."""
        raise NotImplementedError("This tool is async-only. Use _arun instead.")

    async def _arun(self, transcript: str, format: str = "markdown") -> str:
        """Summarize meeting transcript using LLM."""
        try:
            if not settings.OPENAI_API_KEY:
                return "Error: OPENAI_API_KEY not configured"

            # Truncate transcript if too long (to avoid token limits)
            # GPT-4o-mini can handle ~128k tokens, but we'll limit to reasonable size
            max_length = 100000  # ~25k words
            if len(transcript) > max_length:
                transcript = transcript[:max_length] + "\n\n[... transcript truncated ...]"

            llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.3,  # Lower temperature for more factual summaries
                api_key=settings.OPENAI_API_KEY,
            )

            prompt = f"""Analyze the following meeting transcript and provide a comprehensive summary.

Include the following sections:
1. **Meeting Overview**: Brief summary of the meeting purpose and key participants
2. **Key Topics Discussed**: Main topics and themes covered
3. **Decisions Made**: Important decisions and outcomes
4. **Key Points**: Significant points, insights, or information shared
5. **Next Steps** (if mentioned): Any follow-up items or planned actions

Transcript:
{transcript}

Provide the summary in {"Markdown format" if format == "markdown" else "plain text format"}.
Be concise but comprehensive, focusing on the most important information."""

            response = await llm.ainvoke(prompt)
            summary = response.content if hasattr(response, "content") else str(response)

            return summary

        except Exception as e:
            logger.error(f"Error summarizing meeting: {e}", exc_info=True)
            return f"Error generating meeting summary: {str(e)}"


class ActionItem(BaseModel):
    """Action item structure."""

    description: str = Field(description="Action item description/task")
    assignee: Optional[str] = Field(default=None, description="Person assigned (if mentioned)")
    due_date: Optional[str] = Field(default=None, description="Due date or deadline (if mentioned)")
    priority: Optional[str] = Field(default=None, description="Priority level (if mentioned)")
    context: Optional[str] = Field(default=None, description="Additional context or notes")


class ExtractActionItemsInput(BaseModel):
    """Input for extracting action items from a transcript."""

    transcript: str = Field(description="Meeting transcript text to analyze")


class ExtractActionItemsTool(BaseTool):
    """Tool for extracting action items from meeting transcripts using structured output."""

    name: str = "extract_action_items"
    description: str = (
        "Extract action items from a meeting transcript. "
        "Returns a structured list of action items with descriptions, assignees, due dates, and priority. "
        "Provide the full transcript text as input."
    )
    args_schema: Type[BaseModel] = ExtractActionItemsInput
    model_config = {"extra": "allow"}

    def __init__(self, **kwargs):
        """Initialize the action item extraction tool."""
        super().__init__(**kwargs)

    def _run(self, transcript: str) -> str:
        """Synchronous version - not used, but required by BaseTool."""
        raise NotImplementedError("This tool is async-only. Use _arun instead.")

    async def _arun(self, transcript: str) -> str:
        """Extract action items from meeting transcript using structured output."""
        try:
            if not settings.OPENAI_API_KEY:
                return "Error: OPENAI_API_KEY not configured"

            # Truncate transcript if too long
            max_length = 100000
            if len(transcript) > max_length:
                transcript = transcript[:max_length] + "\n\n[... transcript truncated ...]"

            # Use instructor for structured output
            try:
                from instructor import patch
                from openai import AsyncOpenAI

                client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
                client = patch(client)

                class ActionItemsResponse(BaseModel):
                    """Response containing list of action items."""

                    action_items: List[ActionItem] = Field(
                        description="List of action items extracted from the transcript"
                    )

                prompt = f"""Analyze the following meeting transcript and extract all action items.

An action item is a task, to-do, or follow-up item that was mentioned during the meeting. 
Look for:
- Tasks assigned to specific people
- Follow-up items mentioned
- Decisions that require action
- Next steps or deliverables

For each action item, extract:
- Description: Clear description of what needs to be done
- Assignee: Person's name if mentioned (e.g., "John will...", "Sarah should...")
- Due date: Any deadline or timeframe mentioned
- Priority: If priority was explicitly mentioned (high, medium, low, urgent, etc.)
- Context: Additional relevant context or notes

Only extract action items that are clearly actionable tasks. Do not include general discussion points or information sharing.

Transcript:
{transcript}"""

                response: ActionItemsResponse = await client.chat.completions.create(
                    model="gpt-4o-mini",
                    response_model=ActionItemsResponse,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                )

                if not response.action_items:
                    return "No action items found in the transcript."

                # Format action items for display
                formatted_items = []
                for idx, item in enumerate(response.action_items, 1):
                    item_str = f"{idx}. **{item.description}**"
                    if item.assignee:
                        item_str += f"\n   - Assignee: {item.assignee}"
                    if item.due_date:
                        item_str += f"\n   - Due: {item.due_date}"
                    if item.priority:
                        item_str += f"\n   - Priority: {item.priority}"
                    if item.context:
                        item_str += f"\n   - Context: {item.context}"
                    formatted_items.append(item_str)

                return f"Found {len(response.action_items)} action item(s):\n\n" + "\n\n".join(
                    formatted_items
                )

            except ImportError:
                # Fallback to regular LLM if instructor not available
                llm = ChatOpenAI(
                    model="gpt-4o-mini",
                    temperature=0.3,
                    api_key=settings.OPENAI_API_KEY,
                )

                prompt = f"""Analyze the following meeting transcript and extract all action items.

An action item is a task, to-do, or follow-up item that was mentioned during the meeting.

For each action item, provide:
- Description: Clear description of what needs to be done
- Assignee: Person's name if mentioned
- Due date: Any deadline or timeframe mentioned
- Priority: If priority was mentioned

Format the output as a numbered list with clear sections.

Transcript:
{transcript}"""

                response = await llm.ainvoke(prompt)
                return response.content if hasattr(response, "content") else str(response)

        except Exception as e:
            logger.error(f"Error extracting action items: {e}", exc_info=True)
            return f"Error extracting action items: {str(e)}"


async def get_meeting_tools(db, user_id: str) -> list[BaseTool]:
    """Get all meeting analysis tools."""
    # These tools don't require any integration client, they use LLM directly
    return [
        SummarizeMeetingTool(),
        ExtractActionItemsTool(),
    ]




