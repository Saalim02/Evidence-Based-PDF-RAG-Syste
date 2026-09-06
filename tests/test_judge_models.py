import pytest
from pydantic import ValidationError

from app.models.judge_models import (
    JudgeScore,
    GroundingJudgeResult,
)


def test_judge_score_accepts_valid_score():
    result = JudgeScore(
        score=0.85,
        reason="The evidence is relevant.",
    )

    assert result.score == 0.85
    assert result.reason == "The evidence is relevant."


def test_judge_score_accepts_boundary_values():
    assert JudgeScore(
        score=0.0,
        reason="No support.",
    ).score == 0.0

    assert JudgeScore(
        score=1.0,
        reason="Full support.",
    ).score == 1.0


def test_judge_score_rejects_score_below_zero():
    with pytest.raises(ValidationError):
        JudgeScore(
            score=-0.1,
            reason="Invalid score.",
        )


def test_judge_score_rejects_score_above_one():
    with pytest.raises(ValidationError):
        JudgeScore(
            score=1.1,
            reason="Invalid score.",
        )


def test_grounding_judge_accepts_valid_result():
    result = GroundingJudgeResult(
        supported=True,
        score=0.95,
        reason="The evidence directly supports the claim.",
    )

    assert result.supported is True
    assert result.score == 0.95


def test_grounding_judge_rejects_invalid_score():
    with pytest.raises(ValidationError):
        GroundingJudgeResult(
            supported=False,
            score=1.5,
            reason="Invalid score.",
        )


def test_grounding_judge_requires_supported_field():
    with pytest.raises(ValidationError):
        GroundingJudgeResult(
            score=0.5,
            reason="Missing supported field.",
        )
