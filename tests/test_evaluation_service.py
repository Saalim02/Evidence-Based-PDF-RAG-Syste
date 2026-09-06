from unittest.mock import patch

import pytest

from app.models.evaluation_models import EvaluationDecision
from app.models.judge_models import (
    GroundingJudgeResult,
    JudgeScore,
)
from app.services.evaluation.evaluation_service import (
    _extract_claims,
    evaluate_rag_response,
)


def test_extract_claims():
    answer = (
        "Customers can request a refund within 30 days. "
        "Refund requests must be submitted online."
    )

    claims = _extract_claims(answer)

    assert claims == [
        "Customers can request a refund within 30 days",
        "Refund requests must be submitted online",
    ]


def test_extract_claims_empty_answer():
    assert _extract_claims("") == []
    assert _extract_claims("   ") == []


def test_evaluation_requires_question():
    with pytest.raises(ValueError, match="Question is required"):
        evaluate_rag_response(
            question="",
            answer="A valid answer.",
            retrieved_chunks=[
                {
                    "chunk_id": 1,
                    "file_name": "policy.pdf",
                    "page_number": 2,
                    "text": "A valid evidence chunk.",
                    "score": 0.5,
                }
            ],
            evidence=[
                {
                    "page_number": 2,
                    "snippet": "A valid evidence chunk.",
                }
            ],
            api_key="test-api-key",
            use_llm_judges=False,
        )


def test_evaluation_requires_answer():
    with pytest.raises(ValueError, match="Answer is required"):
        evaluate_rag_response(
            question="What is the policy?",
            answer="",
            retrieved_chunks=[
                {
                    "chunk_id": 1,
                    "file_name": "policy.pdf",
                    "page_number": 2,
                    "text": "A valid evidence chunk.",
                    "score": 0.5,
                }
            ],
            evidence=[
                {
                    "page_number": 2,
                    "snippet": "A valid evidence chunk.",
                }
            ],
            api_key="test-api-key",
            use_llm_judges=False,
        )


def test_evaluation_requires_retrieved_chunks():
    with pytest.raises(ValueError, match="Retrieved chunks are required"):
        evaluate_rag_response(
            question="What is the policy?",
            answer="A valid answer.",
            retrieved_chunks=[],
            evidence=[],
            api_key="test-api-key",
            use_llm_judges=False,
        )


@patch(
    "app.services.evaluation.evaluation_service."
    "evaluate_source_relevance_with_llm"
)
@patch(
    "app.services.evaluation.evaluation_service."
    "evaluate_grounding_with_llm"
)
@patch(
    "app.services.evaluation.evaluation_service."
    "evaluate_answer_correctness_with_llm"
)
def test_evaluation_orchestrates_all_llm_judges(
    mock_correctness,
    mock_grounding,
    mock_source_relevance,
):
    mock_source_relevance.return_value = JudgeScore(
        score=0.90,
        reason="Evidence is highly relevant.",
    )

    mock_grounding.return_value = GroundingJudgeResult(
        supported=True,
        score=0.95,
        reason="Answer is well grounded.",
    )

    mock_correctness.return_value = JudgeScore(
        score=0.90,
        reason="Answer is correct.",
    )

    retrieved_chunks = [
        {
            "chunk_id": 1,
            "file_name": "policy.pdf",
            "page_number": 2,
            "text": "Customers can request a refund within 30 days.",
            "score": 0.2,
        }
    ]

    evidence = [
        {
            "page_number": 2,
            "snippet": "Customers can request a refund within 30 days.",
        }
    ]

    result = evaluate_rag_response(
        question="What is the refund period?",
        answer="Customers can request a refund within 30 days.",
        retrieved_chunks=retrieved_chunks,
        evidence=evidence,
        api_key="test-api-key",
        use_llm_judges=True,
    )

    assert result.evaluation_id != "pending"
    assert result.evaluation_id.startswith("eval-")
    assert len(result.evaluation_id) == 37
    assert all(
        character in "0123456789abcdef"
        for character in result.evaluation_id[5:]
    )
    assert result.question == "What is the refund period?"
    assert result.answer == (
        "Customers can request a refund within 30 days."
    )

    assert result.retrieval_quality > 0.0
    assert result.source_relevance == 0.90
    assert result.grounding == 0.95
    assert result.answer_correctness == 0.90
    assert result.citation_quality == 1.0

    assert result.overall_confidence > 0.85
    assert result.decision == EvaluationDecision.AUTO_APPROVE

    mock_source_relevance.assert_called_once()
    mock_grounding.assert_called_once()
    mock_correctness.assert_called_once()


def test_deterministic_evaluation_without_llm_judges():
    retrieved_chunks = [
        {
            "chunk_id": 1,
            "file_name": "policy.pdf",
            "page_number": 2,
            "text": "Customers can request a refund within 30 days.",
            "score": 0.2,
        }
    ]

    evidence = [
        {
            "page_number": 2,
            "snippet": "Customers can request a refund within 30 days.",
        }
    ]

    result = evaluate_rag_response(
        question="What is the refund period?",
        answer="Customers can request a refund within 30 days.",
        retrieved_chunks=retrieved_chunks,
        evidence=evidence,
        api_key="test-api-key",
        use_llm_judges=False,
    )

    assert result.retrieval_quality > 0.0
    assert result.source_relevance > 0.0
    assert result.grounding == 1.0
    assert result.answer_correctness == result.grounding
    assert result.citation_quality == 1.0
    assert 0.0 <= result.overall_confidence <= 1.0


@patch(
    "app.services.evaluation.evaluation_service."
    "evaluate_source_relevance_with_llm"
)
@patch(
    "app.services.evaluation.evaluation_service."
    "evaluate_grounding_with_llm"
)
@patch(
    "app.services.evaluation.evaluation_service."
    "evaluate_answer_correctness_with_llm"
)
def test_low_grounding_forces_human_review(
    mock_correctness,
    mock_grounding,
    mock_source_relevance,
):
    mock_source_relevance.return_value = JudgeScore(
        score=1.0,
        reason="Evidence is relevant.",
    )

    mock_grounding.return_value = GroundingJudgeResult(
        supported=False,
        score=0.20,
        reason="Answer is not sufficiently grounded.",
    )

    mock_correctness.return_value = JudgeScore(
        score=1.0,
        reason="Answer appears correct.",
    )

    result = evaluate_rag_response(
        question="What is the refund period?",
        answer="Customers can request a refund within 90 days.",
        retrieved_chunks=[
            {
                "chunk_id": 1,
                "file_name": "policy.pdf",
                "page_number": 2,
                "text": "Customers can request a refund within 30 days.",
                "score": 0.2,
            }
        ],
        evidence=[
            {
                "page_number": 2,
                "snippet": "Customers can request a refund within 30 days.",
            }
        ],
        api_key="test-api-key",
        use_llm_judges=True,
    )

    assert result.grounding == 0.20
    assert result.decision == EvaluationDecision.HUMAN_REVIEW
    assert any(
        "critically low" in reason.lower()
        for reason in result.reasons
    )


def test_confidence_and_decision_are_bounded():
    retrieved_chunks = [
        {
            "chunk_id": 1,
            "file_name": "policy.pdf",
            "page_number": 1,
            "text": "Refunds are available.",
            "score": 0.1,
        }
    ]

    result = evaluate_rag_response(
        question="Are refunds available?",
        answer="Refunds are available.",
        retrieved_chunks=retrieved_chunks,
        evidence=[
            {
                "page_number": 1,
                "snippet": "Refunds are available.",
            }
        ],
        api_key="test-api-key",
        use_llm_judges=False,
    )

    assert 0.0 <= result.overall_confidence <= 1.0


def test_evaluation_ids_are_unique():
    retrieved_chunks = [
        {
            "chunk_id": 1,
            "file_name": "policy.pdf",
            "page_number": 2,
            "text": "Customers can request a refund within 30 days.",
            "score": 0.2,
        }
    ]

    evidence = [
        {
            "page_number": 2,
            "snippet": "Customers can request a refund within 30 days.",
        }
    ]

    first = evaluate_rag_response(
        question="What is the refund period?",
        answer="Customers can request a refund within 30 days.",
        retrieved_chunks=retrieved_chunks,
        evidence=evidence,
        api_key="test-api-key",
        use_llm_judges=False,
    )

    second = evaluate_rag_response(
        question="What is the refund period?",
        answer="Customers can request a refund within 30 days.",
        retrieved_chunks=retrieved_chunks,
        evidence=evidence,
        api_key="test-api-key",
        use_llm_judges=False,
    )

    assert first.evaluation_id != second.evaluation_id
    assert first.evaluation_id.startswith("eval-")
    assert second.evaluation_id.startswith("eval-")
