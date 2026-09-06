import re
from typing import List


DOCUMENT_INJECTION_PATTERNS = [
    (
        r"\bignore\s+(all\s+)?(previous|prior)\s+instructions\b",
        "Document contains an instruction override attempt.",
    ),
    (
        r"\bdisregard\s+(all\s+)?(previous|prior)\s+instructions\b",
        "Document contains an instruction override attempt.",
    ),
    (
        r"\breveal\s+(the\s+)?system\s+prompt\b",
        "Document attempts to extract the system prompt.",
    ),
    (
        r"\bshow\s+(me\s+)?(the\s+)?system\s+prompt\b",
        "Document attempts to extract the system prompt.",
    ),
    (
        r"\breveal\s+(the\s+)?(openai\s+)?api\s+key\b",
        "Document attempts to extract an API key.",
    ),
    (
        r"\breveal\s+(your\s+)?(hidden|secret)\s+instructions\b",
        "Document attempts to extract hidden instructions.",
    ),
    (
        r"\b(system|developer)\s+(message|instruction)s?\s*:",
        "Document contains instruction-like system/developer content.",
    ),
    (
        r"\bdo\s+not\s+follow\s+(the\s+)?rules\b",
        "Document contains a safety bypass instruction.",
    ),
    (
        r"\bbypass\s+(the\s+)?(safety|security|guardrails)\b",
        "Document contains a security bypass instruction.",
    ),
]


def detect_document_injection(text: str) -> List[str]:
    """
    Detect instruction-like content embedded inside
    retrieved document text.
    """

    if not isinstance(text, str):
        return ["Document content is not valid text."]

    reasons = []

    for pattern, reason in DOCUMENT_INJECTION_PATTERNS:
        if re.search(pattern, text, flags=re.IGNORECASE):
            reasons.append(reason)

    return list(dict.fromkeys(reasons))


def inspect_retrieved_chunks(retrieved_chunks: list) -> dict:
    """
    Inspect retrieved chunks for indirect prompt injection.

    The original chunks are not modified.
    Security metadata is returned separately.
    """

    suspicious_chunks = []
    clean_chunks = []

    for chunk in retrieved_chunks:
        reasons = detect_document_injection(
            chunk.get("text", "")
        )

        if reasons:
            suspicious_chunks.append(
                {
                    "chunk_id": chunk.get("chunk_id"),
                    "page_number": chunk.get("page_number"),
                    "reasons": reasons,
                }
            )
        else:
            clean_chunks.append(chunk)

    return {
        "is_suspicious": bool(suspicious_chunks),
        "suspicious_chunks": suspicious_chunks,
        "clean_chunks": clean_chunks,
    }
