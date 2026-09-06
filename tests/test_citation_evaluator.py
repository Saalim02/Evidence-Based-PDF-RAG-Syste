from app.services.evaluation.citation_evaluator import (
    evaluate_citation_quality,
)


def test_valid_page_evidence():
    retrieved_chunks = [
        {
            "chunk_id": 1,
            "page_number": 4,
            "text": "Employees receive annual leave.",
        },
        {
            "chunk_id": 2,
            "page_number": 7,
            "text": "Leave requests require approval.",
        },
    ]

    evidence = [
        {
            "page_number": 4,
            "snippet": "Employees receive annual leave.",
        },
        {
            "page_number": 7,
            "snippet": "Leave requests require approval.",
        },
    ]

    score = evaluate_citation_quality(
        retrieved_chunks,
        evidence,
    )

    assert score == 1.0


def test_invalid_page_evidence():
    retrieved_chunks = [
        {
            "chunk_id": 1,
            "page_number": 4,
            "text": "Employees receive annual leave.",
        }
    ]

    evidence = [
        {
            "page_number": 8,
            "snippet": "Unrelated content.",
        }
    ]

    score = evaluate_citation_quality(
        retrieved_chunks,
        evidence,
    )

    assert score == 0.0


def test_mixed_valid_and_invalid_evidence():
    retrieved_chunks = [
        {
            "chunk_id": 1,
            "page_number": 4,
            "text": "Annual leave policy.",
        },
        {
            "chunk_id": 2,
            "page_number": 7,
            "text": "Leave approval process.",
        },
    ]

    evidence = [
        {
            "page_number": 4,
            "snippet": "Annual leave policy.",
        },
        {
            "page_number": 99,
            "snippet": "Unsupported page.",
        },
    ]

    score = evaluate_citation_quality(
        retrieved_chunks,
        evidence,
    )

    assert score == 0.5


def test_empty_evidence():
    retrieved_chunks = [
        {
            "chunk_id": 1,
            "page_number": 4,
            "text": "Annual leave policy.",
        }
    ]

    score = evaluate_citation_quality(
        retrieved_chunks,
        [],
    )

    assert score == 0.0
