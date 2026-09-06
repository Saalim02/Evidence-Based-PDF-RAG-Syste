from typing import List, Dict, Any


def evaluate_citation_quality(
    retrieved_chunks: List[Dict[str, Any]],
    evidence: List[Dict[str, Any]],
) -> float:
    """
    Deterministically evaluates whether the returned evidence
    is backed by the retrieved chunks.

    Returns a score between 0.0 and 1.0.
    """

    # -----------------------------------
    # NO EVIDENCE
    # -----------------------------------

    if not evidence:
        return 0.0

    if not retrieved_chunks:
        return 0.0

    # -----------------------------------
    # BUILD LOOKUPS
    # -----------------------------------

    retrieved_pages = {
        chunk.get("page_number")
        for chunk in retrieved_chunks
        if chunk.get("page_number") is not None
    }

    retrieved_chunk_ids = {
        chunk.get("chunk_id")
        for chunk in retrieved_chunks
        if chunk.get("chunk_id") is not None
    }

    valid_evidence = 0

    # -----------------------------------
    # CHECK EACH EVIDENCE ITEM
    # -----------------------------------

    for item in evidence:

        page_number = item.get("page_number")
        chunk_id = item.get("chunk_id")

        page_valid = (
            page_number in retrieved_pages
        )

        chunk_valid = (
            chunk_id is None
            or chunk_id in retrieved_chunk_ids
        )

        if page_valid and chunk_valid:
            valid_evidence += 1

    # -----------------------------------
    # SCORE
    # -----------------------------------

    score = valid_evidence / len(evidence)

    return round(score, 4)
