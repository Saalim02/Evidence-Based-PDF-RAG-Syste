from typing import Any, Dict, List, Optional
from uuid import uuid4

from app.models.evaluation_models import (
    ClaimEvaluation,
    EvaluationDecision,
    EvaluationResult,
)
from app.services.evaluation.answer_correctness_judge import (
    evaluate_answer_correctness_with_llm,
)
from app.services.evaluation.citation_evaluator import (
    evaluate_citation_quality,
)
from app.services.evaluation.confidence import (
    calculate_overall_confidence,
    make_decision,
)
from app.services.evaluation.grounding_evaluator import (
    evaluate_claims,
    calculate_grounding_score,
)
from app.services.evaluation.grounding_judge import (
    evaluate_grounding_with_llm,
)
from app.services.evaluation.retrieval_evaluator import (
    evaluate_retrieval_quality,
)
from app.services.evaluation.source_relevance_evaluator import (
    evaluate_source_relevance,
)
from app.services.evaluation.source_relevance_judge import (
    evaluate_source_relevance_with_llm,
)
from app.services.security.document_guardrails import (
    inspect_retrieved_chunks,
)
from app.services.security.audit_logger import (
    log_security_event,
)

def _extract_claims(answer: str) -> List[str]:
    """
    Splits the generated answer into simple sentence-level claims.

    This is the MVP claim extraction strategy.
    A more advanced claim decomposition model can be added later.
    """
    if not answer or not answer.strip():
        return []

    normalized_answer = answer.replace("\n", " ")

    claims = [
        claim.strip()
        for claim in normalized_answer.split(".")
        if claim.strip()
    ]

    return claims


def _build_reasons(
    retrieval_quality: float,
    source_relevance: float,
    grounding: float,
    answer_correctness: float,
    citation_quality: float,
    decision: str,
) -> List[str]:
    reasons = []

    if retrieval_quality < 0.65:
        reasons.append("Retrieval quality is below the recommended level.")

    if source_relevance < 0.65:
        reasons.append("Retrieved evidence has limited source relevance.")

    if grounding < 0.50:
        reasons.append("Grounding is critically low.")

    elif grounding < 0.65:
        reasons.append("Some answer claims are insufficiently grounded.")

    if answer_correctness < 0.65:
        reasons.append("Answer correctness is below the recommended level.")

    if citation_quality < 0.65:
        reasons.append("Citation quality is below the recommended level.")

    if not reasons:
        reasons.append("All evaluation dimensions are within acceptable ranges.")

    reasons.append(f"Evaluation decision: {decision}.")

    return reasons


def evaluate_rag_response(
    question: str,
    answer: str,
    retrieved_chunks: List[Dict[str, Any]],
    evidence: List[Dict[str, Any]],
    api_key: str,
    use_llm_judges: bool = True,
) -> EvaluationResult:
    """
    Evaluates one complete RAG response.

    Input:
        question
        generated answer
        retrieved PDF chunks
        page-based evidence
        evaluator API key

    Output:
        EvaluationResult containing all evaluation scores,
        overall confidence, decision, reasons, and claims.
    """

    if not question or not question.strip():
        raise ValueError("Question is required.")

    if not answer or not answer.strip():
        raise ValueError("Answer is required.")

    if not retrieved_chunks:
        raise ValueError("Retrieved chunks are required.")

    # -----------------------------------
    # DOCUMENT SECURITY
    # -----------------------------------
    document_security = inspect_retrieved_chunks(
        retrieved_chunks
    )
    if document_security["is_suspicious"]:
        log_security_event(
            "document_guardrail_detected",
            endpoint="/api/ask",
            decision="REVIEW",
            reasons=[
                "Suspicious instructions detected in retrieved document content."
            ],
        )

    # -----------------------------------
    # RETRIEVAL QUALITY
    # -----------------------------------
    retrieval_quality = evaluate_retrieval_quality(
        retrieved_chunks
    )

    # -----------------------------------
    # SOURCE RELEVANCE
    # -----------------------------------
    source_relevance = evaluate_source_relevance(
        question,
        retrieved_chunks,
    )

    # -----------------------------------
    # CLAIM EXTRACTION
    # -----------------------------------
    claims = _extract_claims(answer)

    claim_evaluations: List[ClaimEvaluation] = []

    if claims:
        claim_evaluations = evaluate_claims(
            claims,
            retrieved_chunks,
        )

    # -----------------------------------
    # DETERMINISTIC GROUNDING
    # -----------------------------------
    grounding = calculate_grounding_score(
        claim_evaluations
    )

    # -----------------------------------
    # CITATION QUALITY
    # -----------------------------------
    citation_quality = evaluate_citation_quality(
        retrieved_chunks,
        evidence,
    )

    # -----------------------------------
    # LLM JUDGES
    # -----------------------------------
    if use_llm_judges:
        source_relevance_judge = (
            evaluate_source_relevance_with_llm(
                question=question,
                retrieved_chunks=retrieved_chunks,
                api_key=api_key,
            )
        )

        grounding_judge = evaluate_grounding_with_llm(
            question=question,
            answer=answer,
            retrieved_chunks=retrieved_chunks,
            api_key=api_key,
        )

        correctness_judge = (
            evaluate_answer_correctness_with_llm(
                question=question,
                answer=answer,
                retrieved_chunks=retrieved_chunks,
                api_key=api_key,
            )
        )

        # Use LLM judges as the final semantic signals.
        source_relevance = source_relevance_judge.score
        grounding = grounding_judge.score
        answer_correctness = correctness_judge.score

    else:
        # Deterministic fallback when LLM evaluation is disabled.
        answer_correctness = grounding

    # -----------------------------------
    # OVERALL CONFIDENCE
    # -----------------------------------
    overall_confidence = calculate_overall_confidence(
        retrieval_quality=retrieval_quality,
        source_relevance=source_relevance,
        grounding=grounding,
        answer_correctness=answer_correctness,
        citation_quality=citation_quality,
    )

    # -----------------------------------
    # DECISION
    # -----------------------------------
    decision = make_decision(
        overall_confidence=overall_confidence,
        grounding=grounding,
    )

    # -----------------------------------
    # SECURITY HARD GATE
    # -----------------------------------
    if document_security["is_suspicious"]:
        decision = EvaluationDecision.HUMAN_REVIEW

    # -----------------------------------
    # REASONS
    # -----------------------------------
    reasons = _build_reasons(
        retrieval_quality=retrieval_quality,
        source_relevance=source_relevance,
        grounding=grounding,
        answer_correctness=answer_correctness,
        citation_quality=citation_quality,
        decision=decision.value,
    )

    if document_security["is_suspicious"]:
        reasons.insert(
            0,
            "Security guardrail detected suspicious instructions "
            "in retrieved document content.",
        )
        reasons.insert(
            1,
            "AUTO_APPROVE is blocked because retrieved document "
            "content is untrusted.",
        )

    return EvaluationResult(
        evaluation_id=f"eval-{uuid4().hex}",
        question=question,
        answer=answer,
        retrieval_quality=retrieval_quality,
        source_relevance=source_relevance,
        grounding=grounding,
        answer_correctness=answer_correctness,
        citation_quality=citation_quality,
        overall_confidence=overall_confidence,
        decision=decision,
        reasons=reasons,
        claims=claim_evaluations,
    )
