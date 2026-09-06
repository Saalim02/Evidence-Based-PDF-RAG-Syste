from unittest.mock import MagicMock, patch

import pytest

from app.models.judge_models import JudgeScore
from app.services.evaluation.source_relevance_judge import (
    _build_evidence_context,
    evaluate_source_relevance_with_llm,
)


def test_build_evidence_context():
    chunks = [
        {
            "page_number": 3,
            "text": "The refund period is 30 days.",
        },
        {
            "page_number": 7,
            "text": "Refund requests must be submitted online.",
        },
    ]

    context = _build_evidence_context(chunks)

    assert "[Evidence 1 | Page 3]" in context
    assert "The refund period is 30 days." in context
    assert "[Evidence 2 | Page 7]" in context
    assert "Refund requests must be submitted online." in context


def test_empty_question_raises_error():
    with pytest.raises(ValueError, match="Question is required"):
        evaluate_source_relevance_with_llm(
            "",
            [{"page_number": 1, "text": "Some evidence."}],
            "test-api-key",
        )


def test_empty_retrieval_raises_error():
    with pytest.raises(
        ValueError,
        match="Retrieved evidence is required",
    ):
        evaluate_source_relevance_with_llm(
            "What is the refund policy?",
            [],
            "test-api-key",
        )


def test_empty_evidence_text_raises_error():
    with pytest.raises(
        ValueError,
        match="Retrieved evidence contains no text",
    ):
        evaluate_source_relevance_with_llm(
            "What is the refund policy?",
            [{"page_number": 1, "text": ""}],
            "test-api-key",
        )


@patch(
    "app.services.evaluation.source_relevance_judge.ChatPromptTemplate.from_template"
)
@patch(
    "app.services.evaluation.source_relevance_judge.get_judge_llm"
)
def test_llm_judge_returns_judge_score(
    mock_get_judge_llm,
    mock_from_template,
):
    mock_llm = MagicMock()
    mock_structured_llm = MagicMock()
    mock_prompt = MagicMock()
    mock_chain = MagicMock()

    expected_result = JudgeScore(
        score=0.90,
        reason="The evidence directly addresses the question.",
    )

    mock_chain.invoke.return_value = expected_result

    mock_prompt.__or__.return_value = mock_chain

    mock_from_template.return_value = mock_prompt

    mock_llm.with_structured_output.return_value = (
        mock_structured_llm
    )

    mock_get_judge_llm.return_value = mock_llm

    result = evaluate_source_relevance_with_llm(
        "What is the refund policy?",
        [
            {
                "page_number": 3,
                "text": "Customers can request a refund within 30 days.",
            }
        ],
        "test-api-key",
    )

    assert isinstance(result, JudgeScore)
    assert result.score == 0.90
    assert (
        result.reason
        == "The evidence directly addresses the question."
    )

    mock_get_judge_llm.assert_called_once_with(
        "test-api-key"
    )

    mock_llm.with_structured_output.assert_called_once_with(
        JudgeScore
    )

    mock_prompt.__or__.assert_called_once_with(
        mock_structured_llm
    )

    mock_chain.invoke.assert_called_once()


@patch(
    "app.services.evaluation.source_relevance_judge.ChatPromptTemplate.from_template"
)
@patch(
    "app.services.evaluation.source_relevance_judge.get_judge_llm"
)
def test_dictionary_result_is_validated_into_judge_score(
    mock_get_judge_llm,
    mock_from_template,
):
    mock_llm = MagicMock()
    mock_structured_llm = MagicMock()
    mock_prompt = MagicMock()
    mock_chain = MagicMock()

    mock_chain.invoke.return_value = {
        "score": 0.75,
        "reason": "The evidence is strongly relevant.",
    }

    mock_prompt.__or__.return_value = mock_chain

    mock_from_template.return_value = mock_prompt

    mock_llm.with_structured_output.return_value = (
        mock_structured_llm
    )

    mock_get_judge_llm.return_value = mock_llm

    result = evaluate_source_relevance_with_llm(
        "What is the refund policy?",
        [
            {
                "page_number": 3,
                "text": "Customers can request a refund within 30 days.",
            }
        ],
        "test-api-key",
    )

    assert isinstance(result, JudgeScore)
    assert result.score == 0.75
    assert result.reason == "The evidence is strongly relevant."


@patch(
    "app.services.evaluation.source_relevance_judge.ChatPromptTemplate.from_template"
)
@patch(
    "app.services.evaluation.source_relevance_judge.get_judge_llm"
)
def test_invalid_dictionary_result_is_rejected(
    mock_get_judge_llm,
    mock_from_template,
):
    mock_llm = MagicMock()
    mock_structured_llm = MagicMock()
    mock_prompt = MagicMock()
    mock_chain = MagicMock()

    mock_chain.invoke.return_value = {
        "score": 1.5,
        "reason": "Invalid score.",
    }

    mock_prompt.__or__.return_value = mock_chain

    mock_from_template.return_value = mock_prompt

    mock_llm.with_structured_output.return_value = (
        mock_structured_llm
    )

    mock_get_judge_llm.return_value = mock_llm

    with pytest.raises(Exception):
        evaluate_source_relevance_with_llm(
            "What is the refund policy?",
            [
                {
                    "page_number": 3,
                    "text": "Customers can request a refund within 30 days.",
                }
            ],
            "test-api-key",
        )
