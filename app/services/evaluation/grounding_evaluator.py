from typing import Any, Dict, List

from app.models.evaluation_models import ClaimEvaluation, EvidenceReference


def _tokenize(text: str) -> set[str]:
    """
    Converts text into a simple set of lowercase word tokens.
    """
    return {
        token.strip(".,!?;:()[]{}\"'")
        for token in text.lower().split()
        if token.strip(".,!?;:()[]{}\"'")
    }


def calculate_claim_support(
    claim: str,
    evidence_texts: List[str],
) -> float:
    """
    Calculates a deterministic lexical support score for a claim.

    The score represents the proportion of claim tokens that
    appear in the supplied evidence.

    This is a heuristic signal, not semantic entailment.
    """
    claim_tokens = _tokenize(claim)

    if not claim_tokens or not evidence_texts:
        return 0.0

    evidence_tokens = set()

    for evidence_text in evidence_texts:
        evidence_tokens.update(_tokenize(evidence_text))

    overlap = claim_tokens.intersection(evidence_tokens)

    score = len(overlap) / len(claim_tokens)

    return round(
        max(0.0, min(1.0, score)),
        4,
    )


def evaluate_claim(
    claim: str,
    retrieved_chunks: List[Dict[str, Any]],
    support_threshold: float = 0.50,
) -> ClaimEvaluation:
    """
    Evaluates whether a single answer claim is supported
    by the retrieved evidence.
    """
    evidence_texts = []
    evidence_references = []

    for chunk in retrieved_chunks:
        chunk_text = chunk.get("text")

        if not chunk_text:
            continue

        evidence_texts.append(str(chunk_text))

        evidence_references.append(
            EvidenceReference(
                page_number=int(chunk.get("page_number", 0)),
                snippet=str(chunk_text)[:500],
                chunk_id=chunk.get("chunk_id"),
                file_name=chunk.get("file_name"),
            )
        )

    support_score = calculate_claim_support(
        claim,
        evidence_texts,
    )

    supported = support_score >= support_threshold

    reason = (
        "Claim has sufficient lexical overlap with retrieved evidence."
        if supported
        else "Claim has insufficient lexical overlap with retrieved evidence."
    )

    return ClaimEvaluation(
        claim=claim,
        supported=supported,
        evidence=evidence_references if supported else [],
        reason=reason,
    )


def evaluate_claims(
    claims: List[str],
    retrieved_chunks: List[Dict[str, Any]],
    support_threshold: float = 0.50,
) -> List[ClaimEvaluation]:
    """
    Evaluates multiple answer claims against retrieved evidence.
    """
    return [
        evaluate_claim(
            claim=claim,
            retrieved_chunks=retrieved_chunks,
            support_threshold=support_threshold,
        )
        for claim in claims
        if claim.strip()
    ]


def calculate_grounding_score(
    claim_evaluations: List[ClaimEvaluation],
) -> float:
    """
    Calculates the proportion of supported claims.

    Returns a value between 0.0 and 1.0.
    """
    if not claim_evaluations:
        return 0.0

    supported_claims = sum(
        1
        for evaluation in claim_evaluations
        if evaluation.supported
    )

    score = supported_claims / len(claim_evaluations)

    return round(
        max(0.0, min(1.0, score)),
        4,
    )
