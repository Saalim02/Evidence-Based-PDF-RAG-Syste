from unittest.mock import MagicMock, patch

import pytest

from app.models.judge_models import GroundingJudgeResult
from app.services.evaluation.grounding_judge import (
    _build_grounding_evidence_context,
    evaluate_grounding_with_llm,
)


def test_build_grounding_evidence_context():
    chunks = [
        {
            "page_number": 2,
            "text": "Customers can request a refund within 30 days.",
        },
        {
            "page_number": 5,
            "text": "Refund requests must be submitted online.",
        },
    ]

    context = _build_grounding_evidence_context(chunks)

    assert "[Evidence 1 | Page 2]" in context
    assert "Customers can request a refund within 30 days." in context
    assert "[Evidence 2 | Page 5]" in context
    assert "Refund requests must be submitted online." in context


def test_empty_question_raises_error():
    with pytest.raises(ValueError, match="Question is required"):
        evaluate_grounding_with_llm(
            "",
            "Customers can request a refund within 30 days.",
            [{"page_number": 1, "text": "Refunds are allowed within 30 days."}],
            "test-api-key",
        )


def test_empty_answer_raises_error():
    with pytest.raises(ValueError, match="Answer is required"):
        evaluate_grounding_with_llm(
            "What is the refund policy?",
            "",
            [{"page_number": 1, "text": "Refunds are allowed within 30 days."}],
            "test-api-key",
        )


def test_empty_retrieval_raises_error():
    with pytest.raises(
        ValueError,
        match="Retrieved evidence is required",
    ):
        evaluate_grounding_with_llm(
            "What is the refund policy?",
            "Customers can request a refund within 30 days.",
            [],
            "test-api-key",
        )


def test_empty_evidence_text_raises_error():
    with pytest.raises(
        ValueError,
        match="Retrieved evidence contains no text",
    ):
        evaluate_grounding_with_llm(
            "What is the refund policy?",
            "Customers can request a refund within 30 days.",
            [{"page_number": 1, "text": ""}],
            "test-api-key",
        )


@patch(
    "app.services.evaluation.grounding_judge.ChatPromptTemplate.from_template"
)
@patch(
    "app.services.evaluation.grounding_judge.get_judge_llm"
)
def test_llm_grounding_judge_returns_result(
    mock_get_judge_llm,
    mock_from_template,
):
    mock_llm = MagicMock()
    mock_structured_llm = MagicMock()
    mock_prompt = MagicMock()
    mock_chain = MagicMock()

    expected_result = GroundingJudgeResult(
        supported=True,
        score=0.95,
        reason="The answer is fully supported by the retrieved evidence.",
    )

    mock_chain.invoke.return_value = expected_result

    mock_prompt.__or__.return_value = mock_chain
    mock_from_template.return_value = mock_prompt

    mock_llm.with_structured_output.return_value = mock_structured_llm
    mock_get_judge_llm.return_value = mock_llm

    result = evaluate_grounding_with_llm(
        "What is the refund policy?",
        "Customers can request a refund within 30 days.",
        [
            {
                "page_number": 2,
                "text": "Customers can request a refund within 30 days.",
            }
        ],
        "test-api-key",
    )

    assert isinstance(result, GroundingJudgeResult)
    assert result.supported is True
    assert result.score == 0.95
    assert (
        result.reason
        == "The answer is fully supported by the retrieved evidence."
    )

    mock_get_judge_llm.assert_called_once_with("test-api-key")

    mock_llm.with_structured_output.assert_called_once_with(
        GroundingJudgeResult
    )

    mock_prompt.__or__.assert_called_once_with(
        mock_structured_llm
    )

    mock_chain.invoke.assert_called_once()


@patch(
    "app.services.evaluation.grounding_judge.ChatPromptTemplate.from_template"
)
@patch(
    "app.services.evaluation.grounding_judge.get_judge_llm"
)
def test_dictionary_result_is_validated_into_grounding_result(
    mock_get_judge_llm,
    mock_from_template,
):
    mock_llm = MagicMock()
    mock_structured_llm = MagicMock()
    mock_prompt = MagicMock()
    mock_chain = MagicMock()

    mock_chain.invoke.return_value = {
        "supported": False,
        "score": 0.25,
        "reason": "The answer contains unsupported information.",
    }

    mock_prompt.__or__.return_value = mock_chain
    mock_from_template.return_value = mock_prompt

    mock_llm.with_structured_output.return_value = mock_structured_llm
    mock_get_judge_llm.return_value = mock_llm

    result = evaluate_grounding_with_llm(
        "What is the refund policy?",
        "Customers receive refunds within 90 days.",
        [
            {
                "page_number": 2,
                "text": "Customers can request a refund within 30 days.",
            }
        ],
        "test-api-key",
    )

    assert isinstance(result, GroundingJudgeResult)
    assert result.supported is False
    assert result.score == 0.25
    assert result.reason == "The answer contains unsupported information."


@patch(
    "app.services.evaluation.grounding_judge.ChatPromptTemplate.from_template"
)
@patch(
    "app.services.evaluation.grounding_judge.get_judge_llm"
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
        "supported": True,
        "score": 1.5,
        "reason": "Invalid score.",
    }

    mock_prompt.__or__.return_value = mock_chain
    mock_from_template.return_value = mock_prompt

    mock_llm.with_structured_output.return_value = mock_structured_llm
    mock_get_judge_llm.return_value = mock_llm

    with pytest.raises(Exception):
        evaluate_grounding_with_llm(
            "What is the refund policy?",
            "Customers can request a refund within 30 days.",
            [
                {
                    "page_number": 2,
                    "text": "Customers can request a refund within 30 days.",
                }
            ],
            "test-api-key",
        )
