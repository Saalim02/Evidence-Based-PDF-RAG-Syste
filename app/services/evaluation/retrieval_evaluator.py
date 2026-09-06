from typing import Any, Dict, List


def normalize_retrieval_score(score: float) -> float:
    """
    Converts a FAISS-style distance into a normalized
    retrieval-quality signal.

    Lower distance = better retrieval.

    This is a heuristic signal, not a ground-truth
    retrieval metric.
    """

    if score < 0:
        score = 0.0

    normalized = 1.0 / (1.0 + score)

    return round(
        max(0.0, min(1.0, normalized)),
        4,
    )


def evaluate_retrieval_quality(
    retrieved_chunks: List[Dict[str, Any]],
) -> float:
    """
    Calculates a deterministic retrieval-quality signal
    from the distances of retrieved chunks.

    Returns a value between 0.0 and 1.0.
    """

    if not retrieved_chunks:
        return 0.0

    normalized_scores = []

    for chunk in retrieved_chunks:

        score = chunk.get("score")

        if score is None:
            continue

        try:
            score = float(score)
        except (TypeError, ValueError):
            continue

        normalized_scores.append(
            normalize_retrieval_score(score)
        )

    if not normalized_scores:
        return 0.0

    average_score = (
        sum(normalized_scores)
        / len(normalized_scores)
    )

    return round(
        max(0.0, min(1.0, average_score)),
        4,
    )
