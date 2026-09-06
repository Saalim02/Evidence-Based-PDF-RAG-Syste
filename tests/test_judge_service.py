import pytest

from app.services.evaluation.judge_service import get_judge_llm


def test_missing_api_key_raises_error():
    with pytest.raises(ValueError, match="OpenAI API key is missing"):
        get_judge_llm("")


def test_whitespace_api_key_raises_error():
    with pytest.raises(ValueError, match="OpenAI API key is missing"):
        get_judge_llm("   ")


def test_judge_llm_uses_configured_model():
    llm = get_judge_llm("test-api-key")

    assert llm.model_name == "gpt-4o-mini"
    assert llm.temperature == 0
