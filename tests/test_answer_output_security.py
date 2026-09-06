from app.services.answer_service import generate_grounded_answer


class FakeResponse:
    content = "The API key is sk-1234567890abcdefghijklmnop"


class FakeChain:
    def invoke(self, values):
        return FakeResponse()


class FakePrompt:
    def __or__(self, llm):
        return FakeChain()


class FakeLLM:
    pass


def test_leaked_secret_is_not_returned_to_user(monkeypatch):
    def fake_get_llm(api_key):
        return FakeLLM()

    monkeypatch.setattr(
        "app.services.answer_service.get_llm",
        fake_get_llm,
    )

    from app.services.answer_service import ChatPromptTemplate

    class FakeChatPromptTemplate:
        @classmethod
        def from_template(cls, template):
            return FakePrompt()

    monkeypatch.setattr(
        "app.services.answer_service.ChatPromptTemplate",
        FakeChatPromptTemplate,
    )

    retrieved_chunks = [
        {
            "chunk_id": 1,
            "page_number": 1,
            "text": "Neural networks are computational models.",
            "score": 0.5,
        }
    ]

    result = generate_grounded_answer(
        question="What are neural networks?",
        retrieved_chunks=retrieved_chunks,
        api_key="test-key",
    )

    assert result == "Answer not found in uploaded PDF."
    assert "sk-1234567890abcdefghijklmnop" not in result
