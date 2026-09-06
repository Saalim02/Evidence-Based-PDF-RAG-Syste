from typing import Any, Dict, List

from langchain_core.prompts import ChatPromptTemplate

from app.models.judge_models import JudgeScore
from app.services.evaluation.judge_service import get_judge_llm


SOURCE_RELEVANCE_PROMPT = """
You are an evaluation model for an evidence-based RAG system.

Your task is to evaluate how relevant the retrieved evidence is
to answering the user's question.

Evaluate ONLY the supplied question and evidence.

Scoring:
- 1.0 = evidence is directly relevant and sufficient to answer the question
- 0.75 = evidence is strongly relevant but has minor gaps
- 0.50 = evidence is partially relevant
- 0.25 = evidence has weak relevance
- 0.0 = evidence is irrelevant

Return a score between 0.0 and 1.0.

Do not evaluate whether the final answer is correct.
Do not use outside knowledge.
Explain the reason briefly.

Question:
{question}

Retrieved Evidence:
{evidence}
"""


def _build_evidence_context(
    retrieved_chunks: List[Dict[str, Any]],
) -> str:
    """
    Converts retrieved chunks into a numbered evidence context.
    """
    evidence_parts = []

    for index, chunk in enumerate(retrieved_chunks, start=1):
        page_number = chunk.get("page_number", "unknown")
        chunk_text = chunk.get("text", "")

        if not chunk_text:
            continue

        evidence_parts.append(
            f"[Evidence {index} | Page {page_number}]\n"
            f"{chunk_text}"
        )

    return "\n\n".join(evidence_parts)


def evaluate_source_relevance_with_llm(
    question: str,
    retrieved_chunks: List[Dict[str, Any]],
    api_key: str,
) -> JudgeScore:
    """
    Uses the configurable evaluation LLM to judge the semantic
    relevance of retrieved evidence to the user's question.
    """
    if not question or not question.strip():
        raise ValueError("Question is required.")

    if not retrieved_chunks:
        raise ValueError("Retrieved evidence is required.")

    evidence = _build_evidence_context(retrieved_chunks)

    if not evidence:
        raise ValueError("Retrieved evidence contains no text.")

    prompt = ChatPromptTemplate.from_template(
        SOURCE_RELEVANCE_PROMPT
    )

    llm = get_judge_llm(api_key)

    structured_llm = llm.with_structured_output(
        JudgeScore
    )

    chain = prompt | structured_llm

    result = chain.invoke(
        {
            "question": question.strip(),
            "evidence": evidence,
        }
    )

    if isinstance(result, JudgeScore):
        return result

    return JudgeScore.model_validate(result)
