from pathlib import Path
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS

from app.services.embedding_service import get_embedding_model


VECTOR_DIR = Path("vectorstore")
VECTOR_DIR.mkdir(exist_ok=True)


def convert_chunks_to_documents(chunks: list, file_name: str) -> list:
    """
    Converts chunk dictionaries into LangChain Document objects.
    """

    documents = []

    for chunk in chunks:
        doc = Document(
            page_content=chunk["text"],
            metadata={
                "page_number": chunk["page_number"],
                "chunk_id": chunk["chunk_id"],
                "doc_id": chunk["doc_id"],
                "file_name": file_name
            }
        )
        documents.append(doc)

    return documents


def create_and_save_vectorstore(documents: list):
    """
    Creates a LangChain FAISS vector store from documents
    and saves it locally.
    """

    embeddings = get_embedding_model()

    vectorstore = FAISS.from_documents(documents, embeddings)
    vectorstore.save_local(str(VECTOR_DIR))

    return vectorstore


def load_vectorstore():
    """
    Loads the saved LangChain FAISS vector store.
    """

    embeddings = get_embedding_model()

    if not VECTOR_DIR.exists():
        return None

    try:
        vectorstore = FAISS.load_local(
            str(VECTOR_DIR),
            embeddings,
            allow_dangerous_deserialization=True
        )
        return vectorstore
    except Exception:
        return None