from pathlib import Path

from app.models.evaluation_models import (
    EvaluationDecision,
    EvaluationResult,
    FeedbackCategory,
    HumanReview,
)
from app.services.evaluation import evaluation_storage_service


def build_evaluation():
    return EvaluationResult(
        evaluation_id="eval-storage-test-001",
        question="What is hybrid retrieval?",
        answer="Hybrid retrieval combines multiple retrieval methods.",
        retrieval_quality=0.90,
        source_relevance=0.85,
        grounding=0.95,
        answer_correctness=0.90,
        citation_quality=1.0,
        overall_confidence=0.92,
        decision=EvaluationDecision.AUTO_APPROVE,
        reasons=[
            "All evaluation dimensions are within acceptable ranges.",
            "Evaluation decision: EvaluationDecision.AUTO_APPROVE.",
        ],
        claims=[],
    )


def build_human_review():
    return HumanReview(
        evaluation_id="eval-storage-test-001",
        decision=EvaluationDecision.HUMAN_REVIEW,
        feedback_category=FeedbackCategory.INCORRECT_ANSWER,
        feedback_text="The answer needs correction.",
        corrected_answer="The corrected answer.",
    )


def test_save_and_load_evaluation(monkeypatch, tmp_path):
    monkeypatch.setattr(
        evaluation_storage_service,
        "EVALUATION_DIR",
        tmp_path,
    )

    evaluation = build_evaluation()

    saved_id = evaluation_storage_service.save_evaluation(
        evaluation
    )

    assert saved_id == evaluation.evaluation_id

    expected_file = (
        tmp_path / f"{evaluation.evaluation_id}.json"
    )

    assert expected_file.exists()

    loaded = evaluation_storage_service.load_evaluation(
        evaluation.evaluation_id
    )

    assert loaded is not None
    assert loaded.evaluation_id == evaluation.evaluation_id
    assert loaded.question == evaluation.question
    assert loaded.answer == evaluation.answer

    assert loaded.retrieval_quality == evaluation.retrieval_quality
    assert loaded.source_relevance == evaluation.source_relevance
    assert loaded.grounding == evaluation.grounding
    assert loaded.answer_correctness == evaluation.answer_correctness
    assert loaded.citation_quality == evaluation.citation_quality
    assert loaded.overall_confidence == evaluation.overall_confidence

    assert loaded.decision == evaluation.decision
    assert loaded.reasons == evaluation.reasons


def test_load_missing_evaluation_returns_none(monkeypatch, tmp_path):
    monkeypatch.setattr(
        evaluation_storage_service,
        "EVALUATION_DIR",
        tmp_path,
    )

    result = evaluation_storage_service.load_evaluation(
        "does-not-exist"
    )

    assert result is None


def test_saved_evaluation_is_valid_json(monkeypatch, tmp_path):
    monkeypatch.setattr(
        evaluation_storage_service,
        "EVALUATION_DIR",
        tmp_path,
    )

    evaluation = build_evaluation()

    evaluation_storage_service.save_evaluation(
        evaluation
    )

    file_path = (
        tmp_path / f"{evaluation.evaluation_id}.json"
    )

    content = file_path.read_text(
        encoding="utf-8"
    )

    assert content.strip().startswith("{")
    assert content.strip().endswith("}")


def test_save_and_load_human_review(monkeypatch, tmp_path):
    monkeypatch.setattr(
        evaluation_storage_service,
        "EVALUATION_DIR",
        tmp_path,
    )

    review = build_human_review()

    saved_id = evaluation_storage_service.save_human_review(
        review
    )

    assert saved_id == review.evaluation_id

    expected_file = (
        tmp_path
        / "reviews"
        / f"{review.evaluation_id}.json"
    )

    assert expected_file.exists()

    loaded = evaluation_storage_service.load_human_review(
        review.evaluation_id
    )

    assert loaded is not None
    assert loaded.evaluation_id == review.evaluation_id
    assert loaded.decision == review.decision
    assert loaded.feedback_category == review.feedback_category
    assert loaded.feedback_text == review.feedback_text
    assert loaded.corrected_answer == review.corrected_answer


def test_load_missing_human_review_returns_none(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setattr(
        evaluation_storage_service,
        "EVALUATION_DIR",
        tmp_path,
    )

    result = evaluation_storage_service.load_human_review(
        "does-not-exist"
    )

    assert result is None


def test_saved_human_review_is_valid_json(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setattr(
        evaluation_storage_service,
        "EVALUATION_DIR",
        tmp_path,
    )

    review = build_human_review()

    evaluation_storage_service.save_human_review(
        review
    )

    file_path = (
        tmp_path
        / "reviews"
        / f"{review.evaluation_id}.json"
    )

    content = file_path.read_text(
        encoding="utf-8"
    )

    assert content.strip().startswith("{")
    assert content.strip().endswith("}")


def test_append_evaluation_dataset(tmp_path, monkeypatch):
    from app.models.evaluation_models import (
        EvaluationDecision,
        EvaluationResult,
        HumanReview,
        FeedbackCategory,
    )
    from app.services.evaluation import evaluation_storage_service as storage

    monkeypatch.setattr(
        storage,
        "EVALUATION_DIR",
        tmp_path,
    )

    evaluation = EvaluationResult(
        evaluation_id="dataset-test-001",
        question="What is RNN?",
        answer="RNN is a recurrent neural network.",
        retrieval_quality=0.9,
        source_relevance=0.9,
        grounding=0.9,
        answer_correctness=0.9,
        citation_quality=1.0,
        overall_confidence=0.92,
        decision=EvaluationDecision.AUTO_APPROVE,
        reasons=[],
        claims=[],
    )

    review = HumanReview(
        evaluation_id="dataset-test-001",
        decision=EvaluationDecision.HUMAN_REVIEW,
        feedback_category=FeedbackCategory.OTHER,
        feedback_text="Reviewer checked the answer.",
        corrected_answer="RNN stands for recurrent neural network.",
    )

    dataset_path = storage.append_evaluation_dataset(
        evaluation,
        review,
    )

    import json

    records = [
        json.loads(line)
        for line in open(
            dataset_path,
            encoding="utf-8",
        )
        if line.strip()
    ]

    assert len(records) == 1
    assert records[0]["evaluation_id"] == "dataset-test-001"
    assert records[0]["question"] == "What is RNN?"
    assert records[0]["human_decision"] == "HUMAN_REVIEW"
    assert records[0]["feedback_category"] == "other"
    assert records[0]["corrected_answer"] == (
        "RNN stands for recurrent neural network."
    )
