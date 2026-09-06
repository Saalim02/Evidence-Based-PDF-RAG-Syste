import re
from typing import List

from app.models.security_models import (
    SecurityCheckResult,
    SecurityDecision,
)


OUTPUT_SECRET_PATTERNS = [
    (
        r"\bsk-[A-Za-z0-9_-]{20,}\b",
        "Potential API key leakage detected.",
    ),
    (
        r"\b(api[_ -]?key|access[_ -]?token|secret[_ -]?key)"
        r"\s*[:=]\s*[A-Za-z0-9_\-./+=]{12,}",
        "Potential credential/token leakage detected.",
    ),
    (
        r"\b(password|passwd|credential)"
        r"\s*[:=]\s*\S{8,}",
        "Potential password/credential leakage detected.",
    ),
]


OUTPUT_PROMPT_LEAK_PATTERNS = [
    (
        r"\b(system prompt|system message)\b"
        r"\s*(is|was|:)\s*",
        "Potential system prompt leakage detected.",
    ),
    (
        r"\b(developer instructions|developer message)\b"
        r"\s*(is|are|was|were|:)\s*",
        "Potential developer instruction leakage detected.",
    ),
    (
        r"\b(hidden instructions|secret instructions)\b"
        r"\s*(is|are|was|were|:)\s*",
        "Potential hidden instruction leakage detected.",
    ),
]


def detect_output_leakage(answer: str) -> List[str]:
    """
    Detects obvious secret or instruction leakage
    in an LLM-generated answer.
    """

    if not isinstance(answer, str):
        return ["LLM output is not valid text."]

    reasons = []

    for pattern, reason in (
        OUTPUT_SECRET_PATTERNS
        + OUTPUT_PROMPT_LEAK_PATTERNS
    ):
        if re.search(pattern, answer, flags=re.IGNORECASE):
            reasons.append(reason)

    return list(dict.fromkeys(reasons))


def validate_output(answer: str) -> SecurityCheckResult:
    """
    Validates an LLM-generated answer before returning it
    to the user.
    """

    if not isinstance(answer, str):
        return SecurityCheckResult(
            decision=SecurityDecision.BLOCK,
            is_safe=False,
            risk_score=1.0,
            reasons=["LLM output must be a string."],
        )

    if not answer.strip():
        return SecurityCheckResult(
            decision=SecurityDecision.BLOCK,
            is_safe=False,
            risk_score=1.0,
            reasons=["LLM output cannot be empty."],
        )

    leakage_reasons = detect_output_leakage(answer)

    if leakage_reasons:
        return SecurityCheckResult(
            decision=SecurityDecision.BLOCK,
            is_safe=False,
            risk_score=0.95,
            reasons=leakage_reasons,
        )

    return SecurityCheckResult(
        decision=SecurityDecision.ALLOW,
        is_safe=True,
        risk_score=0.0,
        reasons=[],
    )
