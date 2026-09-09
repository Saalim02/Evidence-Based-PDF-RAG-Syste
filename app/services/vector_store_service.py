import shutil
import tempfile
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
    Creates and saves a FAISS vectorstore safely.

    The new vectorstore is first written to a temporary directory.
    Only after the temporary save succeeds is it moved into the
    user's vectorstore directory.

    This prevents a failed FAISS save from partially overwriting
    an existing working vectorstore.
    """

    embeddings = get_embedding_model()

    vectorstore = FAISS.from_documents(
        documents,
        embeddings,
    )

    vectorstore_dir = _get_vectorstore_dir(user_id)

    vectorstore_dir.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temp_dir = Path(
        tempfile.mkdtemp(
            prefix=".vectorstore_tmp_",
            dir=str(vectorstore_dir.parent),
        )
    )

    try:
        # -----------------------------------
        # SAVE NEW VECTORSTORE TO TEMP DIR
        # -----------------------------------
        vectorstore.save_local(
            str(temp_dir)
        )

        # -----------------------------------
        # REPLACE EXISTING VECTORSTORE
        # -----------------------------------
        if vectorstore_dir.exists():
            shutil.rmtree(vectorstore_dir)

        temp_dir.rename(vectorstore_dir)

        return vectorstore

    except Exception:
        # -----------------------------------
        # CLEAN UP FAILED TEMP SAVE
        # -----------------------------------
        if temp_dir.exists():
            shutil.rmtree(temp_dir)

        raise


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
