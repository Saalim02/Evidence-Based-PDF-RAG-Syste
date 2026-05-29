from fastapi import APIRouter, HTTPException
import os

from app.models.query_models import QueryRequest
from app.services.retrieval_service import retrieve_relevant_chunks
from app.services.answer_service import generate_grounded_answer
from app.services.document_registry_service import get_active_document

router = APIRouter()


# -----------------------------------
# API KEY RESOLUTION
# -----------------------------------
def resolve_api_key(
    access_password: str,
    user_openai_api_key: str
):

    # -----------------------------------
    # BACKEND ACCESS MODE
    # -----------------------------------
    if access_password == "20022004":

        backend_key = os.getenv("OPENAI_API_KEY")

        if not backend_key:

            raise HTTPException(
                status_code=500,
                detail="Backend OpenAI API key not configured."
            )

        return backend_key

    # -----------------------------------
    # USER API KEY MODE
    # -----------------------------------
    if not user_openai_api_key:

        raise HTTPException(
            status_code=400,
            detail=(
                "Provide valid access password "
                "or your own OpenAI API key."
            )
        )

    return user_openai_api_key


@router.post("/ask")
def ask_question(request: QueryRequest):

    # -----------------------------------
    # RESOLVE API KEY
    # -----------------------------------
    api_key = resolve_api_key(
        request.access_password,
        request.user_openai_api_key
    )

    # -----------------------------------
    # RETRIEVE RELEVANT CHUNKS
    # -----------------------------------
    retrieval_output = retrieve_relevant_chunks(
        request.question
    )

    if retrieval_output["status"] == "error":
        return retrieval_output

    active_doc = get_active_document()

    active_doc_id = (
        active_doc["active_doc_id"]
        if active_doc else None
    )

    # -----------------------------------
    # NO-HALLUCINATION LOGIC
    # -----------------------------------
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

    # -----------------------------------
    # RETRIEVED CHUNKS
    # -----------------------------------
    retrieved_chunks = retrieval_output["retrieved_chunks"]

    # -----------------------------------
    # GENERATE FINAL ANSWER
    # -----------------------------------
    final_answer = generate_grounded_answer(
        question=request.question,
        retrieved_chunks=retrieved_chunks,
        api_key=api_key
    )

    # -----------------------------------
    # BUILD EVIDENCE
    # -----------------------------------
    evidence = []

    seen_pages = set()

    for chunk in retrieved_chunks:

        page_number = chunk["page_number"]

        # -----------------------------------
        # AVOID DUPLICATE PAGE EVIDENCE
        # -----------------------------------
        if page_number in seen_pages:
            continue

        seen_pages.add(page_number)

        image_path = (
            f"http://127.0.0.1:8000/page_images/"
            f"{active_doc_id}/page_{page_number}.png"
        )

        evidence.append({
            "page_number": page_number,
            "snippet": chunk["text"][:250],
            "image_path": image_path
        })

    # -----------------------------------
    # FINAL RESPONSE
    # -----------------------------------
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