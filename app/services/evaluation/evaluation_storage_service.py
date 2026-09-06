import json
from pathlib import Path

from app.core.config import EVALUATION_DIR
from app.models.evaluation_models import (
    EvaluationResult,
    HumanReview,
)
from app.services.user_storage_service import get_user_evaluation_dir


def _get_evaluation_dir(user_id: int | None = None) -> Path:
    """
    Return the evaluation directory.

    When user_id is provided, evaluations are isolated per user.
    When omitted, the legacy global directory is used for
    backwards compatibility with older data/tests.
    """
    if user_id is not None:
        return get_user_evaluation_dir(user_id)

    return EVALUATION_DIR


def save_evaluation(
    evaluation: EvaluationResult,
    user_id: int | None = None,
) -> str:
    """
    Save an evaluation result.

    Authenticated production callers should provide user_id.
    """

    evaluation_dir = _get_evaluation_dir(user_id)
    evaluation_dir.mkdir(parents=True, exist_ok=True)

    file_path = (
        evaluation_dir
        / f"{evaluation.evaluation_id}.json"
    )

    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(
            evaluation.model_dump(mode="json"),
            file,
            indent=2,
        )

    return evaluation.evaluation_id


def load_evaluation(
    evaluation_id: str,
    user_id: int | None = None,
) -> EvaluationResult | None:
    """
    Load an evaluation.

    With user_id, only that user's evaluation directory
    is searched.
    """

    evaluation_dir = _get_evaluation_dir(user_id)

    file_path = (
        evaluation_dir
        / f"{evaluation_id}.json"
    )

    if not file_path.exists():
        return None

    with open(
        file_path,
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    return EvaluationResult.model_validate(data)


def save_human_review(
    review: HumanReview,
    user_id: int | None = None,
) -> str:
    """
    Save a human review in the owner's evaluation directory.
    """

    evaluation_dir = _get_evaluation_dir(user_id)
    review_dir = evaluation_dir / "reviews"

    review_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    file_path = (
        review_dir
        / f"{review.evaluation_id}.json"
    )

    with open(
        file_path,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            review.model_dump(mode="json"),
            file,
            indent=2,
        )

    return review.evaluation_id


def load_human_review(
    evaluation_id: str,
    user_id: int | None = None,
) -> HumanReview | None:
    """
    Load a human review from the owner's evaluation directory.
    """

    evaluation_dir = _get_evaluation_dir(user_id)

    file_path = (
        evaluation_dir
        / "reviews"
        / f"{evaluation_id}.json"
    )

    if not file_path.exists():
        return None

    with open(
        file_path,
        "r",
        encoding="utf-8",
    ) as file:
        data = json.load(file)

    return HumanReview.model_validate(data)


def append_evaluation_dataset(
    evaluation: EvaluationResult,
    review: HumanReview,
    user_id: int | None = None,
) -> str:
    """
    Append a human-reviewed example to the owner's
    evaluation dataset.

    Secrets such as API keys and passwords are never stored.
    """

    evaluation_dir = _get_evaluation_dir(user_id)

    dataset_path = (
        evaluation_dir
        / "evaluation_dataset.jsonl"
    )

    record = {
        "evaluation_id": evaluation.evaluation_id,
        "user_id": evaluation.user_id,
        "question": evaluation.question,
        "generated_answer": evaluation.answer,
        "retrieval_quality": evaluation.retrieval_quality,
        "source_relevance": evaluation.source_relevance,
        "grounding": evaluation.grounding,
        "answer_correctness": evaluation.answer_correctness,
        "citation_quality": evaluation.citation_quality,
        "overall_confidence": evaluation.overall_confidence,
        "original_decision": evaluation.decision.value,
        "reasons": evaluation.reasons,
        "claims": [
            claim.model_dump(mode="json")
            for claim in evaluation.claims
        ],
        "human_decision": review.decision.value,
        "feedback_category": (
            review.feedback_category.value
            if review.feedback_category
            else None
        ),
        "feedback_text": review.feedback_text,
        "corrected_answer": review.corrected_answer,
    }

    evaluation_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        dataset_path,
        "a",
        encoding="utf-8",
    ) as file:
        file.write(
            json.dumps(record, ensure_ascii=False)
            + "\n"
        )

    return str(dataset_path)
