"""Robust Markdown parser for Google Docs formatting using markdown-it-py."""

from typing import List, Dict, Any, Tuple


def parse_markdown_to_docs_requests(markdown: str, start_index: int) -> Tuple[str, List[Dict[str, Any]]]:
    """Parse Markdown content and generate Google Docs API requests.

    Uses markdown-it-py to properly parse Markdown into tokens, then converts
    them to Google Docs API formatting requests.

    Args:
        markdown: Markdown content string
        start_index: Starting index in the document where content will be inserted

    Returns:
        Tuple of (plain_text, requests) where:
        - plain_text: The plain text content (without Markdown markers)
        - requests: List of Google Docs API batchUpdate requests for formatting
    """
    from markdown_it import MarkdownIt

    md = MarkdownIt("commonmark")
    tokens = md.parse(markdown)

    plain_text_parts: List[str] = []
    requests: List[Dict[str, Any]] = []

    # Track formatting ranges (for bold/italic)
    formatting_stack: List[Dict[str, Any]] = []
    # Track heading ranges
    heading_info: List[Dict[str, Any]] = []

    def get_current_text_length():
        return len("".join(plain_text_parts))

    def process_tokens(token_list: List[Any]):
        """Recursively process tokens."""
        i = 0
        while i < len(token_list):
            token = token_list[i]
            token_type = token.type

            if token_type == "heading_open":
                level = int(token.tag[1]) if hasattr(
                    token, 'tag') and token.tag else 1
                level = min(max(level, 1), 6)
                heading_info.append({
                    "level": level,
                    "start": get_current_text_length()
                })

            elif token_type == "heading_close":
                if heading_info:
                    info = heading_info[-1]
                    end = get_current_text_length()
                    if end > info["start"]:
                        requests.append({
                            "updateParagraphStyle": {
                                "range": {
                                    "startIndex": start_index + info["start"],
                                    "endIndex": start_index + end
                                },
                                "paragraphStyle": {
                                    "namedStyleType": f"HEADING_{info['level']}"
                                },
                                "fields": "namedStyleType"
                            }
                        })
                    heading_info.pop()
                plain_text_parts.append("\n")

            elif token_type == "paragraph_open":
                pass  # Just mark start if needed

            elif token_type == "paragraph_close":
                plain_text_parts.append("\n")

            elif token_type == "bullet_list_open":
                pass

            elif token_type == "bullet_list_close":
                pass

            elif token_type == "list_item_open":
                # Check if parent is bullet list
                if i > 0 and token_list[i-1].type == "bullet_list_open":
                    plain_text_parts.append("• ")

            elif token_type == "list_item_close":
                plain_text_parts.append("\n")

            elif token_type == "strong_open":
                formatting_stack.append({
                    "type": "bold",
                    "start": get_current_text_length()
                })

            elif token_type == "strong_close":
                if formatting_stack and formatting_stack[-1].get("type") == "bold":
                    fmt = formatting_stack.pop()
                    end = get_current_text_length()
                    if end > fmt["start"]:
                        requests.append({
                            "updateTextStyle": {
                                "range": {
                                    "startIndex": start_index + fmt["start"],
                                    "endIndex": start_index + end
                                },
                                "textStyle": {"bold": True},
                                "fields": "bold"
                            }
                        })

            elif token_type == "em_open":
                formatting_stack.append({
                    "type": "italic",
                    "start": get_current_text_length()
                })

            elif token_type == "em_close":
                if formatting_stack and formatting_stack[-1].get("type") == "italic":
                    fmt = formatting_stack.pop()
                    end = get_current_text_length()
                    if end > fmt["start"]:
                        requests.append({
                            "updateTextStyle": {
                                "range": {
                                    "startIndex": start_index + fmt["start"],
                                    "endIndex": start_index + end
                                },
                                "textStyle": {"italic": True},
                                "fields": "italic"
                            }
                        })

            elif token_type == "inline":
                # Process inline tokens
                if hasattr(token, 'children') and token.children:
                    process_tokens(token.children)

            elif token_type == "text":
                if hasattr(token, 'content') and token.content:
                    plain_text_parts.append(token.content)

            # Process children for block-level tokens
            if token_type not in ("inline", "text") and hasattr(token, 'children') and token.children:
                process_tokens(token.children)

            i += 1

    # Process all tokens
    process_tokens(tokens)

    plain_text = "".join(plain_text_parts)

    return plain_text, requests
