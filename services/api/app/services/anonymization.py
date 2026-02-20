"""Basic PII anonymization via regex masking. MVP only - not perfect de-identification."""
import re

# Patterns: order matters (more specific first)
_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    # Emails
    (re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"), "[EMAIL]"),
    # German phone numbers (simplified)
    (re.compile(r"\+49[- ]?[0-9]{2,4}[- ]?[0-9]{4,10}"), "[PHONE]"),
    (re.compile(r"0[0-9]{2,4}[- ]?[0-9]{4,10}"), "[PHONE]"),
    # Date of birth patterns (DD.MM.YYYY, DD/MM/YYYY, YYYY-MM-DD)
    (re.compile(r"\b\d{1,2}\.\d{1,2}\.\d{4}\b"), "[DATE_OF_BIRTH]"),
    (re.compile(r"\b\d{1,2}/\d{1,2}/\d{4}\b"), "[DATE_OF_BIRTH]"),
    (re.compile(r"\b\d{4}-\d{2}-\d{2}\b"), "[DATE_OF_BIRTH]"),
    # ID-like (long digit sequences)
    (re.compile(r"\b\d{10,}\b"), "[ID_NUMBER]"),
    # Herr/Frau + Word -> [PERSON]
    (re.compile(r"\b(?:Herr|Frau)\s+[A-ZÄÖÜa-zäöüß]+\b"), "[PERSON]"),
    # Dr. + Word -> [PERSON]
    (re.compile(r"\bDr\.\s*[A-ZÄÖÜa-zäöüß]+\b"), "[PERSON]"),
]


def anonymize(text: str) -> str:
    """Apply deterministic regex masking. Returns masked text for LLM; original stored in DB."""
    result = text
    for pattern, replacement in _PATTERNS:
        result = pattern.sub(replacement, result)
    return result
