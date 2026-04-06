from langchain_core.prompts import ChatPromptTemplate
from app.services.llm_service import get_llm


def generate_grounded_answer(question: str, retrieved_chunks: list) -> str:
    """
    Generates a grounded answer using only the retrieved PDF chunks.
    """

    if not retrieved_chunks:
        return "Answer not found in uploaded PDF."

    context = "\n\n".join(
        [chunk["text"] for chunk in retrieved_chunks]
    )

    prompt = ChatPromptTemplate.from_template("""
You are an evidence-based PDF question answering assistant.

Your job is to answer the question using ONLY the provided context.

Rules:
- Use ONLY the given context.
- You are allowed to REASON and SUMMARIZE from the context.
- The answer does NOT need to be an exact sentence match.
- If the context contains enough information to answer logically, answer clearly.
- If the context is completely unrelated, respond:
  "Answer not found in uploaded PDF."

Question:
{question}

Context:
{context}

Answer:
""")

    llm = get_llm()

    chain = prompt | llm

    response = chain.invoke({
        "question": question,
        "context": context
    })

    return response.content.strip()