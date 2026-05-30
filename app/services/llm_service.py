from langchain_openai import ChatOpenAI


def get_llm(openai_api_key: str):
    """
    Returns OpenAI LLM using
    resolved API key.
    """

    # -----------------------------------
    # SAFETY VALIDATION
    # -----------------------------------
    if (
        openai_api_key is None
        or not str(openai_api_key).strip()
    ):

        raise ValueError(
            "OpenAI API key is missing."
        )

    # -----------------------------------
    # CLEAN KEY
    # -----------------------------------
    openai_api_key = str(
        openai_api_key
    ).strip()

    # -----------------------------------
    # CREATE LLM
    # -----------------------------------
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
        api_key=openai_api_key
    )

    return llm