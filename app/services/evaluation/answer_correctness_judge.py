from typing import Any, Dict, List

from langchain_core.prompts import ChatPromptTemplate

from app.models.judge_models import JudgeScore
from app.services.evaluation.judge_service import get_judge_llm


ANSWER_CORRECTNESS_PROMPT = """
You are an evaluation model for an evidence-based RAG system.

Your task is to evaluate whether the supplied answer correctly answers
the user's question using the supplied retrieved evidence.

Evaluate ONLY the supplied question, answer, and evidence.

Rules:
- Do not use outside knowledge.
- The answer must directly address the user's question.
- The answer must be factually consistent with the supplied evidence.
- Do not reward an answer merely because it contains information
  related to the question.
- Penalize answers that omit important information needed to answer
  the question.
- Penalize answers that contain contradictions or unsupported conclusions.

Scoring:
- 1.0 = fully correct and directly answers the question
- 0.75 = mostly correct with minor omissions
- 0.50 = partially correct
- 0.25 = mostly incorrect
- 0.0 = completely incorrect or does not answer the question

Return a score between 0.0 and 1.0.

Explain the reason briefly.

Question:
{question}

Answer:
{answer}

Retrieved Evidence:
{evidence}
"""


def _build_correctness_evidence_context(
    retrieved_chunks: List[Dict[str, Any]],
) -> str:
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


def evaluate_answer_correctness_with_llm(
    question: str,
    answer: str,
    retrieved_chunks: List[Dict[str, Any]],
    api_key: str,
) -> JudgeScore:
    if not question or not question.strip():
        raise ValueError("Question is required.")

    if not answer or not answer.strip():
        raise ValueError("Answer is required.")

    if not retrieved_chunks:
        raise ValueError("Retrieved evidence is required.")

    evidence = _build_correctness_evidence_context(retrieved_chunks)

    if not evidence:
        raise ValueError("Retrieved evidence contains no text.")

    prompt = ChatPromptTemplate.from_template(
        ANSWER_CORRECTNESS_PROMPT
    )

    llm = get_judge_llm(api_key)

    structured_llm = llm.with_structured_output(
        JudgeScore
    )

    chain = prompt | structured_llm

    result = chain.invoke(
        {
            "question": question.strip(),
            "answer": answer.strip(),
            "evidence": evidence,
        }
    )

    if isinstance(result, JudgeScore):
        return result

    return JudgeScore.model_validate(result)
