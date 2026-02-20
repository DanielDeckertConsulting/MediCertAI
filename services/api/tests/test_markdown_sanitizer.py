"""Markdown sanitizer unit tests."""
import pytest

from app.services.markdown_sanitizer import sanitize_markdown


def test_sanitize_safe_markdown():
    r = sanitize_markdown("## Hello\n**bold** and *italic*")
    assert not r.failed
    assert "Hello" in r.sanitized
    assert "bold" in r.sanitized


def test_sanitize_rejects_script():
    r = sanitize_markdown("Hello <script>alert(1)</script> world")
    assert r.failed
    assert "Script tag detected" in (r.reason or "")


def test_sanitize_rejects_iframe():
    r = sanitize_markdown("Hello <iframe src='x'></iframe> world")
    assert r.failed
    assert "Iframe" in (r.reason or "")


def test_sanitize_strips_style_attr():
    r = sanitize_markdown('Hello <span style="color:red">x</span>')
    assert not r.failed
    assert "style" not in r.sanitized


def test_sanitize_rejects_javascript_uri():
    r = sanitize_markdown('Link [x](javascript:alert(1))')
    assert r.failed
    assert "javascript" in (r.reason or "").lower()


def test_sanitize_rejects_non_string():
    r = sanitize_markdown(123)  # type: ignore
    assert r.failed
    assert "string" in (r.reason or "").lower()
