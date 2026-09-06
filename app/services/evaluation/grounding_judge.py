from typing import Any, Dict, List

from langchain_core.prompts import ChatPromptTemplate

from app.models.judge_models import GroundingJudgeResult
from app.services.evaluation.judge_service import get_judge_llm


GROUNDING_JUDGE_PROMPT = """
You are an evaluation model for an evidence-based RAG system.

Your task is to determine whether the supplied answer is supported
by the supplied retrieved evidence.

Evaluate ONLY the answer against the supplied evidence.

Rules:
- Do not use outside knowledge.
- Every factual claim in the answer must be supported by the evidence.
- If the answer contains multiple claims, evaluate the overall support.
- A fully supported answer should receive a high score.
- An answer containing unsupported or contradictory claims should receive
  a low score.

Scoring:
- 1.0 = fully supported by the evidence
- 0.75 = mostly supported, with minor unsupported content
- 0.50 = partially supported
- 0.25 = mostly unsupported
- 0.0 = completely unsupported

Set "supported" to true only when the answer is sufficiently grounded
in the supplied evidence.

Return a score between 0.0 and 1.0.

Explain the reason briefly.

Question:
{question}

Answer:
{answer}

Retrieved Evidence:
{evidence}
"""


def _build_grounding_evidence_context(
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


def evaluate_grounding_with_llm(
    question: str,
    answer: str,
    retrieved_chunks: List[Dict[str, Any]],
    api_key: str,
) -> GroundingJudgeResult:
    if not question or not question.strip():
        raise ValueError("Question is required.")

    if not answer or not answer.strip():
        raise ValueError("Answer is required.")

    if not retrieved_chunks:
        raise ValueError("Retrieved evidence is required.")

    evidence = _build_grounding_evidence_context(retrieved_chunks)

    if not evidence:
        raise ValueError("Retrieved evidence contains no text.")

    prompt = ChatPromptTemplate.from_template(GROUNDING_JUDGE_PROMPT)

    llm = get_judge_llm(api_key)

    structured_llm = llm.with_structured_output(
        GroundingJudgeResult
    )

    chain = prompt | structured_llm

    result = chain.invoke(
        {
            "question": question.strip(),
            "answer": answer.strip(),
            "evidence": evidence,
        }
    )

    if isinstance(result, GroundingJudgeResult):
        return result

    return GroundingJudgeResult.model_validate(result)
