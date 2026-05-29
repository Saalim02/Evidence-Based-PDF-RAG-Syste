from langchain_core.documents import (
    Document
)

from langchain_community.vectorstores import (
    FAISS
)

from app.services.embedding_service import (
    get_embedding_model
)

from app.core.config import (
    VECTORSTORE_DIR
)


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

                "page_number":
                chunk["page_number"],

                "chunk_id":
                chunk["chunk_id"],

                "doc_id":
                chunk["doc_id"],

                "file_name":
                file_name
            }
        )

        documents.append(doc)

    return documents


def create_and_save_vectorstore(
    documents: list
):

    """
    Creates LangChain FAISS vectorstore
    and saves it into centralized
    storage/vectorstore directory.
    """

    # -----------------------------------
    # EMBEDDING MODEL
    # -----------------------------------
    embeddings = get_embedding_model()

    # -----------------------------------
    # CREATE VECTORSTORE
    # -----------------------------------
    vectorstore = FAISS.from_documents(
        documents,
        embeddings
    )

    # -----------------------------------
    # SAVE VECTORSTORE
    # -----------------------------------
    vectorstore.save_local(
        str(VECTORSTORE_DIR)
    )

    return vectorstore


def load_vectorstore():

    """
    Loads saved LangChain FAISS
    vectorstore from centralized
    storage/vectorstore directory.
    """

    # -----------------------------------
    # EMBEDDING MODEL
    # -----------------------------------
    embeddings = get_embedding_model()

    # -----------------------------------
    # VECTORSTORE EXISTS?
    # -----------------------------------
    if not VECTORSTORE_DIR.exists():

        return None

    # -----------------------------------
    # LOAD VECTORSTORE
    # -----------------------------------
    try:

        vectorstore = FAISS.load_local(

            str(VECTORSTORE_DIR),

            embeddings,

            allow_dangerous_deserialization=True
        )

        return vectorstore

    except Exception:

        return None