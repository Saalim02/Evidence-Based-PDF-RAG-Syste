from fastapi import APIRouter, HTTPException, Depends
import os

from app.models.evaluation_models import HumanReview
from app.models.query_models import (
    QueryRequest,
    HumanReviewRequest,
)
from app.services.retrieval_service import retrieve_relevant_chunks
from app.services.answer_service import generate_grounded_answer
from app.services.document_registry_service import get_active_document
from app.services.evaluation.evaluation_service import evaluate_rag_response
from app.services.evaluation.evaluation_storage_service import (
    save_evaluation,
    load_evaluation,
    save_human_review,
    append_evaluation_dataset,
)
from app.services.security.guardrails import validate_question
from app.services.security.audit_logger import log_security_event
from app.models.auth_models import User
from app.services.security.auth_dependencies import get_current_user
from app.services.security.rag_authorization import (
    resolve_authorized_api_key,
)

router = APIRouter()



@router.post("/ask")
def ask_question(
    request: QueryRequest,
    current_user: User = Depends(get_current_user),
):

    # -----------------------------------
    # INPUT SECURITY GUARDRAIL
    # -----------------------------------
    security_result = validate_question(request.question)

    if not security_result.is_safe:
        log_security_event(
            "input_guardrail_blocked",
            endpoint="/api/ask",
            client_id=str(current_user.id),
            decision=security_result.decision.value,
            risk_score=security_result.risk_score,
            reasons=security_result.reasons,
        )

        raise HTTPException(
            status_code=400,
            detail={
                "message": "Request blocked by security guardrail.",
                "security": security_result.model_dump(),
            },
         )

    # -----------------------------------
    # RESOLVE API KEY
    # -----------------------------------
    api_key = resolve_authorized_api_key(
        user=current_user,
        access_password=request.access_password,
        user_openai_api_key=request.user_openai_api_key,
    )

    # -----------------------------------
    # RETRIEVE RELEVANT CHUNKS
    # -----------------------------------
    retrieval_output = retrieve_relevant_chunks(
        request.question,
        user_id=current_user.id,
    )

    if retrieval_output["status"] == "error":
        return retrieval_output

    active_doc = get_active_document(current_user.id)

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

        backend_url = os.getenv(
            "PUBLIC_BACKEND_URL",
            "http://localhost:8000"
        ).rstrip("/")
        
        image_path = (
            f"{backend_url}/api/page-images/"
            f"{active_doc_id}/page_{page_number}.png"
        )

        evidence.append({
            "page_number": page_number,
            "snippet": chunk["text"][:250],
            "image_path": image_path
        })

    # -----------------------------------
    # EVALUATE RAG RESPONSE
    # -----------------------------------
    evaluation = evaluate_rag_response(
        question=request.question,
        answer=final_answer,
        retrieved_chunks=retrieved_chunks,
        evidence=evidence,
        api_key=api_key,
        use_llm_judges=True,
    )

    # -----------------------------------
    # SAVE EVALUATION
    # -----------------------------------
    evaluation.user_id = current_user.id

    save_evaluation(
        evaluation,
        user_id=current_user.id,
    )

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
        "evaluation": evaluation.model_dump(),
        "message": "Answer generated successfully."
    }
# -----------------------------------
# GET EVALUATION
# -----------------------------------
@router.get("/evaluation/{evaluation_id}")
def get_evaluation(
    evaluation_id: str,
    current_user: User = Depends(get_current_user),
):

    evaluation = load_evaluation(
        evaluation_id,
        user_id=current_user.id,
    )

    if evaluation is None:
        raise HTTPException(
            status_code=404,
            detail="Evaluation not found."
        )

    return evaluation.model_dump()


# -----------------------------------
# SUBMIT HUMAN REVIEW
# -----------------------------------
@router.post("/evaluation/{evaluation_id}/review")
def submit_human_review(
    evaluation_id: str,
    request: HumanReviewRequest,
    current_user: User = Depends(get_current_user),
):

    # -----------------------------------
    # VERIFY EVALUATION EXISTS
    # -----------------------------------
    evaluation = load_evaluation(
        evaluation_id,
        user_id=current_user.id,
    )

    if evaluation is None:
        raise HTTPException(
            status_code=404,
            detail="Evaluation not found.",
        )

    # -----------------------------------
    # BUILD HUMAN REVIEW
    # -----------------------------------
    review = HumanReview(
        evaluation_id=evaluation_id,
        decision=request.decision,
        feedback_category=request.feedback_category,
        feedback_text=request.feedback_text,
        corrected_answer=request.corrected_answer,
    )

    # -----------------------------------
    # SAVE HUMAN REVIEW
    # -----------------------------------
    save_human_review(
        review,
        user_id=current_user.id,
    )

    # -----------------------------------
    # APPEND TO EVALUATION DATASET
    # -----------------------------------
    append_evaluation_dataset(
        evaluation=evaluation,
        review=review,
        user_id=current_user.id,
    )
    # -----------------------------------
    # SECURITY AUDIT
    # -----------------------------------
    log_security_event(
        "human_review_submitted",
        endpoint="/api/evaluation/{evaluation_id}/review",
        client_id=str(current_user.id),
        decision=review.decision.value,
        reasons=[
            (
                f"Human review submitted with category: "
                f"{review.feedback_category.value}"
                if review.feedback_category
                else "Human review submitted without a feedback category."
            )
        ],
    )

    # -----------------------------------
    # FINAL RESPONSE
    # -----------------------------------
    return {
        "status": "success",
        "evaluation_id": evaluation_id,
        "review": review.model_dump(),
        "message": "Human review saved successfully.",
    }
