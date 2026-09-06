from app.models.evaluation_models import EvaluationDecision
from app.services.evaluation.confidence import (
    calculate_overall_confidence,
    make_decision,
)


def test_high_confidence_auto_approve():
    confidence = calculate_overall_confidence(
        retrieval_quality=0.95,
        source_relevance=0.95,
        grounding=0.95,
        answer_correctness=0.95,
        citation_quality=0.95,
    )

    assert confidence == 0.95

    decision = make_decision(
        overall_confidence=confidence,
        grounding=0.95,
    )

    assert decision == EvaluationDecision.AUTO_APPROVE


def test_medium_confidence_review_recommended():
    confidence = calculate_overall_confidence(
        retrieval_quality=0.80,
        source_relevance=0.80,
        grounding=0.70,
        answer_correctness=0.70,
        citation_quality=0.80,
    )

    decision = make_decision(
        overall_confidence=confidence,
        grounding=0.70,
    )

    assert decision == EvaluationDecision.REVIEW_RECOMMENDED


def test_low_confidence_human_review():
    confidence = calculate_overall_confidence(
        retrieval_quality=0.50,
        source_relevance=0.50,
        grounding=0.40,
        answer_correctness=0.50,
        citation_quality=0.50,
    )

    decision = make_decision(
        overall_confidence=confidence,
        grounding=0.40,
    )

    assert decision == EvaluationDecision.HUMAN_REVIEW


def test_grounding_gate_overrides_high_confidence():
    decision = make_decision(
        overall_confidence=0.95,
        grounding=0.40,
    )

    assert decision == EvaluationDecision.HUMAN_REVIEW
