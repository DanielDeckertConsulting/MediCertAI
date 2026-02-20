"""Block extractor unit tests."""
import pytest

from app.services.block_extractor import extract_blocks


def test_extract_heading():
    blocks = extract_blocks("## Hello World")
    assert len(blocks) == 1
    assert blocks[0]["type"] == "heading"
    assert blocks[0]["content"] == "Hello World"
    assert blocks[0]["level"] == 2


def test_extract_paragraph():
    blocks = extract_blocks("Some text here.")
    assert len(blocks) == 1
    assert blocks[0]["type"] == "paragraph"
    assert blocks[0]["content"] == "Some text here."


def test_extract_list():
    blocks = extract_blocks("- item 1\n- item 2")
    assert len(blocks) == 1
    assert blocks[0]["type"] == "list"
    assert blocks[0]["items"] == ["item 1", "item 2"]


def test_extract_action_block():
    md = """### Recommended Action
ACTION: open_queue_enterprise
LABEL: Review Enterprise Leads
CONFIDENCE: 0.91"""
    blocks = extract_blocks(md)
    assert len(blocks) == 1
    assert blocks[0]["type"] == "action"
    assert blocks[0]["command"] == "open_queue_enterprise"
    assert blocks[0]["label"] == "Review Enterprise Leads"
    assert blocks[0]["confidence"] == 0.91


def test_extract_code_block():
    blocks = extract_blocks("```python\nx = 1\n```")
    assert len(blocks) == 1
    assert blocks[0]["type"] == "code"
    assert "x = 1" in blocks[0]["content"]
    assert blocks[0].get("metadata", {}).get("language") == "python"


def test_extract_divider():
    blocks = extract_blocks("---")
    assert len(blocks) == 1
    assert blocks[0]["type"] == "divider"


def test_extract_quote():
    blocks = extract_blocks("> Quote text here")
    assert len(blocks) == 1
    assert blocks[0]["type"] == "quote"
    assert "Quote text" in blocks[0]["content"]


def test_extract_table():
    md = """| A | B |
| --- | --- |
| 1 | 2 |"""
    blocks = extract_blocks(md)
    assert len(blocks) == 1
    assert blocks[0]["type"] == "table"
    # Header row + data row
    assert blocks[0]["items"] == [["A", "B"], ["1", "2"]]


def test_extract_full_weekly_report():
    md = """## Weekly Report Summary

This week showed **positive** trends.

### Key Points
- Session attendance improved
- Documentation at 94%

### Recommended Action
ACTION: open_queue_enterprise
LABEL: Review Enterprise Leads
CONFIDENCE: 0.91"""
    blocks = extract_blocks(md)
    types = [b["type"] for b in blocks]
    assert "heading" in types
    assert "paragraph" in types
    assert "list" in types
    assert "action" in types
