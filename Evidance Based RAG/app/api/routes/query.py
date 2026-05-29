from fastapi import APIRouter
from app.models.query_models import QueryRequest
from app.services.retrieval_service import retrieve_relevant_chunks
from app.services.answer_service import generate_grounded_answer
from app.services.document_registry_service import get_active_document

router = APIRouter()


@router.post("/ask")
def ask_question(request: QueryRequest):
    retrieval_output = retrieve_relevant_chunks(request.question)

    if retrieval_output["status"] == "error":
        return retrieval_output

    active_doc = get_active_document()
    active_doc_id = active_doc["active_doc_id"] if active_doc else None

    # 🚨 No-hallucination rejection logic
    if retrieval_output["confidence"] == "low":
        return {
            "status": "error",
            "active_document": retrieval_output["active_document"],
            "question": request.question,
            "answer": None,
            "confidence": retrieval_output["confidence"],
            "best_score": retrieval_output["best_score"],
            "average_score": retrieval_output["average_score"],
            "evidence": [],
            "retrieved_chunks": retrieval_output["retrieved_chunks"],
            "message": "Answer not found in uploaded PDF."
        }

    retrieved_chunks = retrieval_output["retrieved_chunks"]

    final_answer = generate_grounded_answer(
        question=request.question,
        retrieved_chunks=retrieved_chunks
    )

    # Build clean evidence section with page image path
    evidence = []
    for chunk in retrieved_chunks:
        page_number = chunk["page_number"]
        image_path = f"http://127.0.0.1:8000/page_images/{active_doc_id}/page_{page_number}.png"

        evidence.append({
            "page_number": page_number,
            "snippet": chunk["text"][:250],
            "image_path": image_path
        })

    return {
        "status": "success",
        "active_document": retrieval_output["active_document"],
        "question": request.question,
        "answer": final_answer,
        "confidence": retrieval_output["confidence"],
        "best_score": retrieval_output["best_score"],
        "average_score": retrieval_output["average_score"],
        "evidence": evidence,
        "retrieved_chunks": retrieved_chunks,
        "message": "Answer generated successfully."
    }