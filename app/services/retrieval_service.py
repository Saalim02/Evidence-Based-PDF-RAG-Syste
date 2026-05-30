from app.services.vector_store_service import load_vectorstore
from app.services.document_registry_service import get_active_document


def get_dynamic_top_k(total_chunks: int) -> int:
    """
    Dynamically decides top-k retrieval value
    based on total chunk count.
    """
    if total_chunks < 50:
        return 3
    elif total_chunks < 200:
        return 4
    elif total_chunks < 500:
        return 5
    else:
        return 6


def get_confidence_label(best_score: float) -> str:
    """
    Converts best retrieval score into confidence label.
    Lower FAISS distance = better match.
    """

    if best_score < 1.6:
        return "high"
    elif best_score < 2.2:
        return "medium"
    else:
        return "low"


def retrieve_relevant_chunks(query: str):
    """
    Retrieves top relevant chunks only from the active uploaded document.
    Also returns confidence info for hallucination control.
    """

    active_doc = get_active_document()

    if not active_doc:
        return {
            "status": "error",
            "active_document": None,
            "retrieved_chunks": [],
            "confidence": "low",
            "best_score": None,
            "average_score": None,
            "message": "No active PDF uploaded."
        }

    active_filename = active_doc["active_filename"]

    vectorstore = load_vectorstore()

    if vectorstore is None:
        return {
            "status": "error",
            "active_document": active_filename,
            "retrieved_chunks": [],
            "confidence": "low",
            "best_score": None,
            "average_score": None,
            "message": "Vector store is empty."
        }

    total_chunks = len(vectorstore.docstore._dict)
    top_k = get_dynamic_top_k(total_chunks)

    docs_with_scores = vectorstore.similarity_search_with_score(query, k=top_k)

    retrieved_chunks = []
    scores = []

    for doc, score in docs_with_scores:
        retrieved_chunks.append({
            "chunk_id": doc.metadata.get("chunk_id"),
            "file_name": doc.metadata.get("file_name"),
            "page_number": doc.metadata.get("page_number"),
            "text": doc.page_content,
            "score": float(score)
        })
        scores.append(float(score))

    if not retrieved_chunks:
        return {
            "status": "error",
            "active_document": active_filename,
            "retrieved_chunks": [],
            "confidence": "low",
            "best_score": None,
            "average_score": None,
            "message": "Answer not found in uploaded PDF."
        }

    best_score = min(scores)
    avg_score = sum(scores) / len(scores)
    confidence = get_confidence_label(best_score)

    return {
        "status": "success",
        "active_document": active_filename,
        "top_k_used": top_k,
        "retrieved_chunks": retrieved_chunks,
        "confidence": confidence,
        "best_score": round(best_score, 4),
        "average_score": round(avg_score, 4),
        "message": "Relevant chunks retrieved successfully."
    }