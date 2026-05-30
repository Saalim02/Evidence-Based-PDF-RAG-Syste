from langchain_core.prompts import ChatPromptTemplate

from app.services.llm_service import get_llm


def generate_grounded_answer(
    question: str,
    retrieved_chunks: list,
    api_key: str
) -> str:
    """
    Generates grounded answer
    using retrieved PDF chunks only.
    """

    # -----------------------------
    # NO CHUNKS
    # -----------------------------
    if not retrieved_chunks:

        return "Answer not found in uploaded PDF."

    # -----------------------------
    # BUILD CONTEXT
    # -----------------------------
    context = "\n\n".join(
        [
            f"[Page {chunk['page_number']}]\n{chunk['text']}"
            for chunk in retrieved_chunks
        ]
    )

    # -----------------------------
    # PROMPT
    # -----------------------------
    prompt = ChatPromptTemplate.from_template("""
You are an evidence-based PDF question answering assistant.

Your job is to answer the question
using ONLY the provided context.

STRICT RULES:
- Use ONLY the given context
- You are allowed to REASON and SUMMARIZE
- Do NOT hallucinate
- Do NOT use outside knowledge
- Keep the answer grounded
- If context is unrelated or insufficient, respond EXACTLY:
  "Answer not found in uploaded PDF."

Question:
{question}

Retrieved PDF Context:
{context}

Answer:
""")

    # -----------------------------
    # DYNAMIC LLM
    # -----------------------------
    llm = get_llm(api_key)

    # -----------------------------
    # CHAIN
    # -----------------------------
    chain = prompt | llm

    response = chain.invoke({
        "question": question,
        "context": context
    })

    final_answer = response.content.strip()

    # -----------------------------
    # EMPTY SAFETY
    # -----------------------------
    if not final_answer:
        return "Answer not found in uploaded PDF."

    return final_answer