from app.services.evaluation.retrieval_evaluator import (
    normalize_retrieval_score,
    evaluate_retrieval_quality,
)


def test_zero_distance_is_perfect_signal():
    assert normalize_retrieval_score(0.0) == 1.0


def test_distance_signal_decreases():
    excellent = normalize_retrieval_score(0.5)
    poor = normalize_retrieval_score(2.0)

    assert excellent > poor


def test_retrieval_quality_with_good_chunks():
    retrieved_chunks = [
        {"score": 0.2},
        {"score": 0.3},
        {"score": 0.4},
    ]

    score = evaluate_retrieval_quality(retrieved_chunks)

    assert 0.0 < score <= 1.0


def test_retrieval_quality_with_poor_chunks():
    retrieved_chunks = [
        {"score": 3.0},
        {"score": 4.0},
        {"score": 5.0},
    ]

    score = evaluate_retrieval_quality(retrieved_chunks)

    assert 0.0 <= score < 0.5


def test_empty_retrieval():
    assert evaluate_retrieval_quality([]) == 0.0


def test_missing_scores():
    retrieved_chunks = [
        {"page_number": 1},
        {"page_number": 2},
    ]

    assert evaluate_retrieval_quality(retrieved_chunks) == 0.0
