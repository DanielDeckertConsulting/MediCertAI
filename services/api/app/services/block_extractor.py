"""Extract structured blocks from markdown. Converts markdown into block schema."""
import re
from typing import Any

# Action block pattern:
# ### Recommended Action
# ACTION: open_queue_enterprise
# LABEL: Review Enterprise Leads
# CONFIDENCE: 0.91
ACTION_HEADER = re.compile(r"^#+\s*Recommended\s+Action\s*$", re.IGNORECASE)
ACTION_LINE = re.compile(r"^ACTION:\s*(.+)$", re.IGNORECASE)
LABEL_LINE = re.compile(r"^LABEL:\s*(.+)$", re.IGNORECASE)
CONFIDENCE_LINE = re.compile(r"^CONFIDENCE:\s*([0-9.]+)\s*$", re.IGNORECASE)


def _parse_action_block(lines: list[str], start: int) -> tuple[dict[str, Any] | None, int]:
    """
    Try to parse action block. Returns (block_dict, next_line_index) or (None, start).
    """
    i = start
    if i >= len(lines):
        return None, start

    # First line should be ### Recommended Action (already consumed by caller)
    command: str | None = None
    label: str | None = None
    confidence: float = 0.0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if not stripped:
            i += 1
            continue
        if stripped.startswith("#") and i > start:
            break
        if am := ACTION_LINE.match(stripped):
            command = am.group(1).strip()
        elif lb := LABEL_LINE.match(stripped):
            label = lb.group(1).strip()
        elif cf := CONFIDENCE_LINE.match(stripped):
            try:
                confidence = float(cf.group(1))
            except ValueError:
                pass
        i += 1

    if command and label:
        return {
            "type": "action",
            "label": label,
            "command": command,
            "confidence": min(1.0, max(0.0, confidence)),
        }, i
    return None, start + 1


def extract_blocks(markdown: str) -> list[dict[str, Any]]:
    """
    Convert markdown into structured blocks.
    Supports: heading, paragraph, list, table, code, divider, quote, action.
    """
    blocks: list[dict[str, Any]] = []
    lines = markdown.split("\n")
    i = 0
    buffer: list[str] = []

    def flush_paragraph():
        nonlocal buffer
        if buffer:
            text = "\n".join(buffer).strip()
            if text:
                blocks.append({"type": "paragraph", "content": text})
            buffer = []

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Empty line - flush paragraph
        if not stripped:
            flush_paragraph()
            i += 1
            continue

        # Horizontal rule
        if re.match(r"^[-*_]{3,}\s*$", stripped):
            flush_paragraph()
            blocks.append({"type": "divider", "content": ""})
            i += 1
            continue

        # Action block: ### Recommended Action (must check before generic heading)
        if ACTION_HEADER.match(stripped):
            flush_paragraph()
            action_block, next_i = _parse_action_block(lines, i + 1)
            if action_block:
                blocks.append(action_block)
                i = next_i
                continue
            i += 1
            continue

        # Heading
        if m := re.match(r"^(#{1,6})\s+(.+)$", stripped):
            flush_paragraph()
            level = len(m.group(1))
            blocks.append({"type": "heading", "content": m.group(2).strip(), "level": level})
            i += 1
            continue

        # Blockquote
        if stripped.startswith(">"):
            flush_paragraph()
            quote_lines = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                q = lines[i].strip()[1:].strip()
                if q:
                    quote_lines.append(q)
                i += 1
            if quote_lines:
                blocks.append({"type": "quote", "content": "\n".join(quote_lines)})
            continue

        # Code block
        if stripped.startswith("```"):
            flush_paragraph()
            lang = stripped[3:].strip() or ""
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            if i < len(lines):
                i += 1
            blocks.append({
                "type": "code",
                "content": "\n".join(code_lines),
                "metadata": {"language": lang} if lang else {},
            })
            continue

        # Table (simple: | a | b |)
        if "|" in stripped and stripped.startswith("|"):
            flush_paragraph()
            table_rows = []
            while i < len(lines) and "|" in lines[i]:
                row = [c.strip() for c in lines[i].split("|")[1:-1]]
                is_separator = row and all(re.match(r"^[-:]+$", c) for c in row)
                if row and not is_separator:
                    table_rows.append(row)
                i += 1
            if table_rows:
                blocks.append({"type": "table", "content": "", "items": table_rows, "metadata": {}})
            continue

        # Unordered list
        if re.match(r"^[-*+]\s+", stripped) or re.match(r"^\d+\.\s+", stripped):
            flush_paragraph()
            list_items = []
            while i < len(lines):
                li = lines[i]
                um = re.match(r"^[-*+]\s+(.+)$", li.strip())
                om = re.match(r"^(\d+)\.\s+(.+)$", li.strip())
                if um:
                    list_items.append(um.group(1))
                    i += 1
                elif om:
                    list_items.append(om.group(2))
                    i += 1
                elif li.strip() and not li.strip().startswith("#"):
                    break
                else:
                    break
            if list_items:
                blocks.append({"type": "list", "content": "", "items": list_items})
            continue

        # Regular paragraph line
        buffer.append(line)
        i += 1

    flush_paragraph()
    return blocks
