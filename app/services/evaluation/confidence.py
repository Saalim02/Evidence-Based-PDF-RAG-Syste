from app.models.evaluation_models import EvaluationDecision


# -----------------------------------
# CONFIGURABLE WEIGHTS
# -----------------------------------

RETRIEVAL_WEIGHT = 0.20
SOURCE_RELEVANCE_WEIGHT = 0.20
GROUNDING_WEIGHT = 0.30
CORRECTNESS_WEIGHT = 0.20
CITATION_WEIGHT = 0.10


# -----------------------------------
# CONFIGURABLE THRESHOLDS
# -----------------------------------

AUTO_APPROVE_THRESHOLD = 0.85
REVIEW_RECOMMENDED_THRESHOLD = 0.65

CRITICAL_GROUNDING_THRESHOLD = 0.50


def calculate_overall_confidence(
    retrieval_quality: float,
    source_relevance: float,
    grounding: float,
    answer_correctness: float,
    citation_quality: float,
) -> float:
    """
    Calculates weighted confidence from
    independent evaluation dimensions.
    """

    confidence = (
        retrieval_quality * RETRIEVAL_WEIGHT
        + source_relevance * SOURCE_RELEVANCE_WEIGHT
        + grounding * GROUNDING_WEIGHT
        + answer_correctness * CORRECTNESS_WEIGHT
        + citation_quality * CITATION_WEIGHT
    )

    return round(
        max(0.0, min(1.0, confidence)),
        4
    )


def make_decision(
    overall_confidence: float,
    grounding: float,
) -> EvaluationDecision:
    """
    Converts evaluation scores into a
    production decision.

    Grounding acts as a hard safety gate.
    """

    # -----------------------------------
    # HARD GROUNDING GATE
    # -----------------------------------

    if grounding < CRITICAL_GROUNDING_THRESHOLD:
        return EvaluationDecision.HUMAN_REVIEW

    # -----------------------------------
    # OVERALL CONFIDENCE
    # -----------------------------------

    if overall_confidence >= AUTO_APPROVE_THRESHOLD:
        return EvaluationDecision.AUTO_APPROVE

    if overall_confidence >= REVIEW_RECOMMENDED_THRESHOLD:
        return EvaluationDecision.REVIEW_RECOMMENDED

    return EvaluationDecision.HUMAN_REVIEW
