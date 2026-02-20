"""Markdown sanitizer. Strips dangerous content; allows safe markdown only."""
import re
from typing import NamedTuple


class SanitizeResult(NamedTuple):
    """Result of sanitization."""

    sanitized: str
    failed: bool
    reason: str | None


# Patterns to strip (dangerous)
SCRIPT_PATTERN = re.compile(r"<script[^>]*>.*?</script>", re.DOTALL | re.IGNORECASE)
IFRAME_PATTERN = re.compile(r"<iframe[^>]*>.*?</iframe>", re.DOTALL | re.IGNORECASE)
STYLE_ATTR_PATTERN = re.compile(r'\s+style\s*=\s*["\'][^"\']*["\']', re.IGNORECASE)
ONEVENT_PATTERN = re.compile(r"\s+on\w+\s*=\s*['\"][^'\"]*['\"]", re.IGNORECASE)
JAVASCRIPT_URI = re.compile(r"javascript:", re.IGNORECASE)
DATA_URI_SCRIPT = re.compile(r"data:\s*text/html", re.IGNORECASE)
# Strip any remaining raw HTML tags (leave markdown symbols)
HTML_TAG_PATTERN = re.compile(r"<[^>]+>")


def sanitize_markdown(raw: str) -> SanitizeResult:
    """
    Sanitize markdown: allow headings, bold/italic, lists, blockquotes, tables,
    code blocks, horizontal rules. Strip script, iframe, inline JS, style attrs.
    """
    if not isinstance(raw, str):
        return SanitizeResult("", True, "Input must be string")

    text = raw

    # 1. Remove script blocks
    if SCRIPT_PATTERN.search(text):
        return SanitizeResult("", True, "Script tag detected")
    text = SCRIPT_PATTERN.sub("", text)

    # 2. Remove iframes
    if IFRAME_PATTERN.search(text):
        return SanitizeResult("", True, "Iframe detected")
    text = IFRAME_PATTERN.sub("", text)

    # 3. Remove style attributes
    text = STYLE_ATTR_PATTERN.sub("", text)

    # 4. Remove on* event handlers
    text = ONEVENT_PATTERN.sub("", text)

    # 5. Remove javascript: URIs
    if JAVASCRIPT_URI.search(text):
        return SanitizeResult("", True, "javascript: URI detected")
    text = JAVASCRIPT_URI.sub("", text)

    # 6. Remove data:text/html
    if DATA_URI_SCRIPT.search(text):
        return SanitizeResult("", True, "data: text/html URI detected")
    text = DATA_URI_SCRIPT.sub("", text)

    # 7. Strip remaining raw HTML (keep content between tags for simple cases)
    text = HTML_TAG_PATTERN.sub("", text)

    return SanitizeResult(text.strip(), False, None)
