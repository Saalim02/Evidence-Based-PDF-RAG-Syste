from typing import Any, Dict, List


def _tokenize(text: str) -> set[str]:
    """
    Converts text into a simple set of lowercase word tokens.
    """
    return {
        token.strip(".,!?;:()[]{}\"'")
        for token in text.lower().split()
        if token.strip(".,!?;:()[]{}\"'")
    }


def calculate_chunk_relevance(
    question: str,
    chunk_text: str,
) -> float:
    """
    Calculates a simple lexical relevance score between
    the question and a retrieved chunk.

    This is a deterministic heuristic, not a semantic
    relevance metric.
    """
    question_tokens = _tokenize(question)
    chunk_tokens = _tokenize(chunk_text)

    if not question_tokens or not chunk_tokens:
        return 0.0

    overlap = question_tokens.intersection(chunk_tokens)

    score = len(overlap) / len(question_tokens)

    return round(
        max(0.0, min(1.0, score)),
        4,
    )


def evaluate_source_relevance(
    question: str,
    retrieved_chunks: List[Dict[str, Any]],
) -> float:
    """
    Calculates the average lexical relevance of retrieved
    chunks against the user's question.

    Returns a value between 0.0 and 1.0.
    """
    if not question or not retrieved_chunks:
        return 0.0

    relevance_scores = []

    for chunk in retrieved_chunks:
        chunk_text = chunk.get("text")

        if not chunk_text:
            continue

        relevance_scores.append(
            calculate_chunk_relevance(
                question,
                str(chunk_text),
            )
        )

    if not relevance_scores:
        return 0.0

    average_score = (
        sum(relevance_scores)
        / len(relevance_scores)
    )

    return round(
        max(0.0, min(1.0, average_score)),
        4,
    )
