from app.services.evaluation.grounding_evaluator import (
    calculate_claim_support,
    evaluate_claim,
    evaluate_claims,
    calculate_grounding_score,
)


def test_fully_supported_claim():
    score = calculate_claim_support(
        "The refund period is 30 days.",
        [
            "Customers can request a refund within 30 days."
        ],
    )

    assert score >= 0.5


def test_unsupported_claim():
    score = calculate_claim_support(
        "The refund period is 90 days.",
        [
            "Customers can request a refund within 30 days."
        ],
    )

    assert score < 1.0


def test_empty_claim_returns_zero():
    assert (
        calculate_claim_support(
            "",
            ["Some evidence text."]
        )
        == 0.0
    )


def test_empty_evidence_returns_zero():
    assert (
        calculate_claim_support(
            "The refund period is 30 days.",
            []
        )
        == 0.0
    )


def test_evaluate_claim_marks_supported_claim():
    retrieved_chunks = [
        {
            "chunk_id": 1,
            "file_name": "policy.pdf",
            "page_number": 5,
            "text": "Customers can request a refund within 30 days.",
        }
    ]

    result = evaluate_claim(
        "The refund period is 30 days.",
        retrieved_chunks,
    )

    assert result.supported is True
    assert len(result.evidence) == 1
    assert result.evidence[0].page_number == 5
    assert result.evidence[0].chunk_id == 1
    assert result.evidence[0].file_name == "policy.pdf"


def test_evaluate_claim_marks_unsupported_claim():
    retrieved_chunks = [
        {
            "chunk_id": 1,
            "file_name": "policy.pdf",
            "page_number": 5,
            "text": "Customers can request a refund within 30 days.",
        }
    ]

    result = evaluate_claim(
        "The company provides refunds for five years.",
        retrieved_chunks,
    )

    assert result.supported is False
    assert result.evidence == []


def test_evaluate_multiple_claims():
    retrieved_chunks = [
        {
            "chunk_id": 1,
            "file_name": "policy.pdf",
            "page_number": 5,
            "text": "Customers can request a refund within 30 days.",
        }
    ]

    results = evaluate_claims(
        [
            "The refund period is 30 days.",
            "The company provides refunds for five years.",
        ],
        retrieved_chunks,
    )

    assert len(results) == 2
    assert results[0].supported is True
    assert results[1].supported is False


def test_grounding_score_with_all_supported_claims():
    retrieved_chunks = [
        {
            "chunk_id": 1,
            "file_name": "policy.pdf",
            "page_number": 5,
            "text": "Customers can request a refund within 30 days.",
        }
    ]

    results = evaluate_claims(
        [
            "The refund period is 30 days.",
            "Customers can request a refund.",
        ],
        retrieved_chunks,
    )

    score = calculate_grounding_score(results)

    assert score == 1.0


def test_grounding_score_with_partially_supported_claims():
    retrieved_chunks = [
        {
            "chunk_id": 1,
            "file_name": "policy.pdf",
            "page_number": 5,
            "text": "Customers can request a refund within 30 days.",
        }
    ]

    results = evaluate_claims(
        [
            "The refund period is 30 days.",
            "The company provides refunds for five years.",
        ],
        retrieved_chunks,
    )

    score = calculate_grounding_score(results)

    assert score == 0.5


def test_grounding_score_with_no_claims():
    assert calculate_grounding_score([]) == 0.0
