from pathlib import Path

from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS

from app.services.embedding_service import get_embedding_model
from app.core.config import VECTORSTORE_DIR
from app.services.user_storage_service import get_user_vectorstore_dir


def convert_chunks_to_documents(
    chunks: list,
    file_name: str
) -> list:
    """
    Converts chunk dictionaries into
    LangChain Document objects.
    """

    documents = []

    for chunk in chunks:
        doc = Document(
            page_content=chunk["text"],
            metadata={
                "page_number": chunk["page_number"],
                "chunk_id": chunk["chunk_id"],
                "doc_id": chunk["doc_id"],
                "file_name": file_name,
            },
        )

        documents.append(doc)

    return documents


def _get_vectorstore_dir(user_id: int | None = None) -> Path:
    """
    Return the vectorstore directory.

    user_id provided:
        Use isolated per-user storage.

    user_id omitted:
        Preserve legacy global storage for backwards compatibility
        with existing tests/data.
    """

    if user_id is None:
        return VECTORSTORE_DIR

    return get_user_vectorstore_dir(user_id)


def create_and_save_vectorstore(
    documents: list,
    user_id: int | None = None,
):
    """
    Creates and saves a FAISS vectorstore.

    When user_id is provided, the vectorstore is isolated
    under that user's storage directory.
    """

    embeddings = get_embedding_model()

    vectorstore = FAISS.from_documents(
        documents,
        embeddings,
    )

    vectorstore_dir = _get_vectorstore_dir(user_id)

    vectorstore_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    vectorstore.save_local(
        str(vectorstore_dir)
    )

    return vectorstore


def load_vectorstore(
    user_id: int | None = None,
):
    """
    Loads a FAISS vectorstore.

    When user_id is provided, only that user's vectorstore
    can be loaded.
    """

    embeddings = get_embedding_model()

    vectorstore_dir = _get_vectorstore_dir(user_id)

    if not vectorstore_dir.exists():
        return None

    try:
        vectorstore = FAISS.load_local(
            str(vectorstore_dir),
            embeddings,
            allow_dangerous_deserialization=True,
        )

        return vectorstore

    except Exception:
        return None
