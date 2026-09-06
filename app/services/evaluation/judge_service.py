from langchain_openai import ChatOpenAI

from app.core.config import EVALUATION_MODEL


def get_judge_llm(openai_api_key: str):
    """
    Returns the configurable LLM used for evaluation.

    The evaluation model is intentionally separate from
    the generation LLM configuration.
    """
    if (
        openai_api_key is None
        or not str(openai_api_key).strip()
    ):
        raise ValueError(
            "OpenAI API key is missing."
        )

    openai_api_key = str(
        openai_api_key
    ).strip()

    if not EVALUATION_MODEL.strip():
        raise ValueError(
            "Evaluation model is not configured."
        )

    return ChatOpenAI(
        model=EVALUATION_MODEL,
        temperature=0,
        api_key=openai_api_key,
    )
