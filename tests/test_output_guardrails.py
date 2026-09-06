from app.models.security_models import SecurityDecision
from app.services.security.output_guardrails import (
    detect_output_leakage,
    validate_output,
)


def test_normal_answer_is_allowed():
    answer = (
        "Neural networks are computational models "
        "that can learn patterns from data."
    )

    result = validate_output(answer)

    assert result.is_safe is True
    assert result.decision == SecurityDecision.ALLOW
    assert result.risk_score == 0.0
    assert result.reasons == []


def test_api_key_leakage_is_blocked():
    answer = (
        "The API key is sk-1234567890abcdefghijklmnop"
    )

    result = validate_output(answer)

    assert result.is_safe is False
    assert result.decision == SecurityDecision.BLOCK
    assert result.risk_score == 0.95
    assert any(
        "API key leakage" in reason
        for reason in result.reasons
    )


def test_credential_assignment_is_blocked():
    answer = (
        "access_token: "
        "abc123456789abcdef"
    )

    result = validate_output(answer)

    assert result.is_safe is False
    assert result.decision == SecurityDecision.BLOCK


def test_password_assignment_is_blocked():
    answer = "password: SuperSecret123"

    result = validate_output(answer)

    assert result.is_safe is False
    assert result.decision == SecurityDecision.BLOCK


def test_system_prompt_leakage_is_blocked():
    answer = (
        "The system prompt is: You are an evidence-based assistant."
    )

    result = validate_output(answer)

    assert result.is_safe is False
    assert result.decision == SecurityDecision.BLOCK


def test_developer_instruction_leakage_is_blocked():
    answer = (
        "The developer instructions are: never reveal secrets."
    )

    result = validate_output(answer)

    assert result.is_safe is False
    assert result.decision == SecurityDecision.BLOCK


def test_hidden_instruction_leakage_is_blocked():
    answer = (
        "The hidden instructions are: follow the secret policy."
    )

    result = validate_output(answer)

    assert result.is_safe is False
    assert result.decision == SecurityDecision.BLOCK


def test_security_terms_without_leakage_are_allowed():
    answer = (
        "The system should protect API keys and passwords. "
        "These credentials must never be exposed."
    )

    result = validate_output(answer)

    assert result.is_safe is True
    assert result.decision == SecurityDecision.ALLOW


def test_non_string_output_is_blocked():
    result = validate_output(None)

    assert result.is_safe is False
    assert result.decision == SecurityDecision.BLOCK


def test_empty_output_is_blocked():
    result = validate_output("   ")

    assert result.is_safe is False
    assert result.decision == SecurityDecision.BLOCK


def test_duplicate_leakage_reasons_are_removed():
    answer = (
        "system prompt: secret\n"
        "system prompt: another secret"
    )

    reasons = detect_output_leakage(answer)

    assert len(reasons) == len(set(reasons))
