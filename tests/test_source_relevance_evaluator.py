from app.services.evaluation.source_relevance_evaluator import (
    calculate_chunk_relevance,
    evaluate_source_relevance,
)


def test_identical_question_and_chunk_terms_are_relevant():
    score = calculate_chunk_relevance(
        "What is the refund policy?",
        "The refund policy allows customers to request a refund.",
    )

    assert score > 0.5


def test_unrelated_chunk_has_low_relevance():
    score = calculate_chunk_relevance(
        "What is the refund policy?",
        "The weather forecast predicts heavy rainfall tomorrow.",
    )

    assert score < 0.5


def test_relevance_is_case_insensitive():
    lower = calculate_chunk_relevance(
        "refund policy",
        "The Refund Policy is described here.",
    )

    upper = calculate_chunk_relevance(
        "REFUND POLICY",
        "The refund policy is described here.",
    )

    assert lower == upper


def test_empty_question_returns_zero():
    assert (
        calculate_chunk_relevance(
            "",
            "This chunk contains some information.",
        )
        == 0.0
    )


def test_empty_chunk_returns_zero():
    assert (
        calculate_chunk_relevance(
            "What is the refund policy?",
            "",
        )
        == 0.0
    )


def test_source_relevance_averages_chunk_scores():
    retrieved_chunks = [
        {
            "text": "The refund policy allows customers to request a refund."
        },
        {
            "text": "The weather forecast predicts heavy rainfall tomorrow."
        },
    ]

    score = evaluate_source_relevance(
        "What is the refund policy?",
        retrieved_chunks,
    )

    assert 0.0 < score < 1.0


def test_empty_retrieval_returns_zero():
    assert (
        evaluate_source_relevance(
            "What is the refund policy?",
            [],
        )
        == 0.0
    )


def test_chunks_without_text_return_zero():
    retrieved_chunks = [
        {"page_number": 1},
        {"page_number": 2},
    ]

    assert (
        evaluate_source_relevance(
            "What is the refund policy?",
            retrieved_chunks,
        )
        == 0.0
    )
