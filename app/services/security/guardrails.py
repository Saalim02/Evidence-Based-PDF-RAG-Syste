import re
from typing import List

from app.models.security_models import (
    SecurityCheckResult,
    SecurityDecision,
)


MAX_QUESTION_LENGTH = 4000


PROMPT_INJECTION_PATTERNS = [
    (
        r"\bignore\s+(all\s+)?previous\s+instructions\b",
        "Instruction override attempt detected.",
    ),
    (
        r"\bignore\s+(all\s+)?prior\s+instructions\b",
        "Instruction override attempt detected.",
    ),
    (
        r"\bdisregard\s+(all\s+)?previous\s+instructions\b",
        "Instruction override attempt detected.",
    ),
    (
        r"\bforget\s+(all\s+)?previous\s+instructions\b",
        "Instruction override attempt detected.",
    ),
    (
        r"\breveal\s+(the\s+)?system\s+prompt\b",
        "System prompt extraction attempt detected.",
    ),
    (
        r"\bshow\s+(me\s+)?(the\s+)?system\s+prompt\b",
        "System prompt extraction attempt detected.",
    ),
    (
        r"\breveal\s+(your\s+)?(hidden|secret)\s+instructions\b",
        "Hidden instruction extraction attempt detected.",
    ),
    (
        r"\bwhat\s+are\s+your\s+(system|hidden)\s+instructions\b",
        "Hidden instruction extraction attempt detected.",
    ),
    (
        r"\bdeveloper\s+message\b",
        "Developer instruction probing detected.",
    ),
    (
        r"\bdeveloper\s+instructions\b",
        "Developer instruction probing detected.",
    ),
    (
        r"\b(print|show|display|reveal|give|provide)\s+"
        r"(the\s+)?(openai\s+)?api\s+key\b",
        "Secret/API key extraction attempt detected.",
    ),
    (
         r"\b(print|show|display|reveal|give|provide)\s+"
         r"(the\s+)?api\s+key\b",
          "Secret/API key extraction attempt detected.",
    ),
    (
        r"\bdo\s+not\s+follow\s+(the\s+)?rules\b",
        "Safety/instruction bypass attempt detected.",
    ),
    (
        r"\bbypass\s+(the\s+)?(safety|security|guardrails)\b",
        "Security bypass attempt detected.",
    ),
    (
        r"\bdisable\s+(the\s+)?(safety|security|guardrails)\b",
        "Security bypass attempt detected.",
    ),
]


def _normalize_question(question: str) -> str:
    return " ".join(question.strip().split())


def detect_prompt_injection(question: str) -> List[str]:
    normalized = _normalize_question(question)

    reasons = []

    for pattern, reason in PROMPT_INJECTION_PATTERNS:
        if re.search(pattern, normalized, flags=re.IGNORECASE):
            reasons.append(reason)

    return list(dict.fromkeys(reasons))


def validate_question(question: str) -> SecurityCheckResult:
    if not isinstance(question, str):
        return SecurityCheckResult(
            decision=SecurityDecision.BLOCK,
            is_safe=False,
            risk_score=1.0,
            reasons=["Question must be a string."],
        )

    normalized = _normalize_question(question)

    if not normalized:
        return SecurityCheckResult(
            decision=SecurityDecision.BLOCK,
            is_safe=False,
            risk_score=1.0,
            reasons=["Question cannot be empty."],
        )

    if len(normalized) > MAX_QUESTION_LENGTH:
        return SecurityCheckResult(
            decision=SecurityDecision.BLOCK,
            is_safe=False,
            risk_score=1.0,
            reasons=[
                f"Question exceeds the maximum length of "
                f"{MAX_QUESTION_LENGTH} characters."
            ],
        )

    injection_reasons = detect_prompt_injection(normalized)

    if injection_reasons:
        return SecurityCheckResult(
            decision=SecurityDecision.BLOCK,
            is_safe=False,
            risk_score=0.95,
            reasons=injection_reasons,
        )

    return SecurityCheckResult(
        decision=SecurityDecision.ALLOW,
        is_safe=True,
        risk_score=0.0,
        reasons=[],
    )
