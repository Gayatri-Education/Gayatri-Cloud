"""Sanitization and Prompt Injection Defense for Ingested Documents."""

from __future__ import annotations

import html
import re

# Malicious LLM control tokens and jailbreak markers
BANNED_CONTROL_TOKENS = [
    r"<\|im_start\|>",
    r"<\|im_end\|>",
    r"<\|endoftext\|>",
    r"\[INST\]",
    r"\[/INST\]",
    r"<<SYS>>",
    r"<</SYS>>",
    r"<s>",
    r"</s>",
]

# Patterns attempting to override system behavior
INJECTION_OVERRIDE_PATTERNS = [
    (
        re.compile(r"(?i)\bignore\s+(all\s+)?(previous|prior)\s+instructions\b"),
        "[Sanitized Override Attempt]",
    ),
    (
        re.compile(r"(?i)\bdisregard\s+(all\s+)?(previous|prior)\s+rules\b"),
        "[Sanitized Override Attempt]",
    ),
    (
        re.compile(r"(?i)\byou\s+are\s+now\s+(an?\s+)?unrestricted\b"),
        "[Sanitized Jailbreak Attempt]",
    ),
    (re.compile(r"(?i)^system:\s*", re.MULTILINE), "[Document Text: System: ]"),
    (re.compile(r"(?i)^assistant:\s*", re.MULTILINE), "[Document Text: Assistant: ]"),
]


def sanitize_document_text(text: str) -> str:
    """Sanitize raw document text by neutralizing prompt injection patterns and control tokens."""
    if not text:
        return ""

    sanitized = text

    # Strip LLM control tokens
    for token_pattern in BANNED_CONTROL_TOKENS:
        sanitized = re.sub(token_pattern, " ", sanitized)

    # Neutralize instruction override attacks
    for pattern, replacement in INJECTION_OVERRIDE_PATTERNS:
        sanitized = pattern.sub(replacement, sanitized)

    return sanitized.strip()


def wrap_chunk_for_prompt(
    chunk_id: str,
    text: str,
    page_number: int | None = None,
    section_header: str | None = None,
) -> str:
    """Encapsulate retrieved chunk in secure XML enclosure with strict non-executable semantics."""
    clean_text = html.escape(text)
    attrs = [f'id="{chunk_id}"']
    if page_number is not None:
        attrs.append(f'page="{page_number}"')
    if section_header:
        attrs.append(f'section="{html.escape(section_header)}"')

    attr_str = " ".join(attrs)
    return (
        f"<document_chunk {attr_str}>\n  <content>\n{clean_text}\n  </content>\n</document_chunk>"
    )
