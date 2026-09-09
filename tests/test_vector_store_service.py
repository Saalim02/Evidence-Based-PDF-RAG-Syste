from pathlib import Path

from app.services import vector_store_service


def test_vectorstore_directory_is_user_scoped(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(
        vector_store_service,
        "get_user_vectorstore_dir",
        lambda user_id: tmp_path / "users" / str(user_id) / "vectorstore",
    )

    user_dir = vector_store_service._get_vectorstore_dir(123)

    assert user_dir == (
        tmp_path / "users" / "123" / "vectorstore"
    )


def test_vectorstore_directory_uses_legacy_path_without_user(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(
        vector_store_service,
        "VECTORSTORE_DIR",
        tmp_path / "legacy-vectorstore",
    )

    result = vector_store_service._get_vectorstore_dir()

    assert result == tmp_path / "legacy-vectorstore"


def test_convert_chunks_to_documents_preserves_doc_metadata():
    chunks = [
        {
            "text": "First chunk",
            "page_number": 2,
            "chunk_id": 7,
            "doc_id": "doc-123",
        }
    ]

    documents = (
        vector_store_service.convert_chunks_to_documents(
            chunks,
            "example.pdf",
        )
    )

    assert len(documents) == 1

    document = documents[0]

    assert document.page_content == "First chunk"
    assert document.metadata["page_number"] == 2
    assert document.metadata["chunk_id"] == 7
    assert document.metadata["doc_id"] == "doc-123"
    assert document.metadata["file_name"] == "example.pdf"


def test_create_and_save_vectorstore_writes_to_user_directory(
    tmp_path,
    monkeypatch,
):
    class FakeEmbeddings:
        pass

    class FakeVectorStore:
        def __init__(self):
            self.saved_to = None

        def save_local(self, path):
            self.saved_to = Path(path)
            self.saved_to.mkdir(parents=True, exist_ok=True)
            (self.saved_to / "index.faiss").write_text("faiss")
            (self.saved_to / "index.pkl").write_text("pickle")

    fake_vectorstore = FakeVectorStore()

    monkeypatch.setattr(
        vector_store_service,
        "get_embedding_model",
        lambda: FakeEmbeddings(),
    )

    monkeypatch.setattr(
        vector_store_service.FAISS,
        "from_documents",
        lambda documents, embeddings: fake_vectorstore,
    )

    monkeypatch.setattr(
        vector_store_service,
        "get_user_vectorstore_dir",
        lambda user_id: tmp_path / "users" / str(user_id) / "vectorstore",
    )

    result = vector_store_service.create_and_save_vectorstore(
        [{"page_content": "test"}],
        user_id=123,
    )

    expected_dir = (
        tmp_path / "users" / "123" / "vectorstore"
    )

    assert result is fake_vectorstore

    assert fake_vectorstore.saved_to != expected_dir

    assert (expected_dir / "index.faiss").exists()
    assert (expected_dir / "index.pkl").exists()

    assert (
        (expected_dir / "index.faiss").read_text()
        == "faiss"
    )

    assert (
        (expected_dir / "index.pkl").read_text()
        == "pickle"
    )


def test_create_and_save_vectorstore_preserves_existing_store_on_failure(
    tmp_path,
    monkeypatch,
):
    class FakeEmbeddings:
        pass

    class FakeVectorStore:
        def save_local(self, path):
            path = Path(path)
            path.mkdir(parents=True, exist_ok=True)

            # Simulate a partial write followed by a failure.
            (path / "index.faiss").write_text("partial-new-faiss")

            raise RuntimeError("simulated save failure")

    vectorstore_dir = (
        tmp_path / "users" / "123" / "vectorstore"
    )

    vectorstore_dir.mkdir(parents=True)

    # Existing working vectorstore.
    (vectorstore_dir / "index.faiss").write_text("old-faiss")
    (vectorstore_dir / "index.pkl").write_text("old-pickle")

    monkeypatch.setattr(
        vector_store_service,
        "get_embedding_model",
        lambda: FakeEmbeddings(),
    )

    monkeypatch.setattr(
        vector_store_service.FAISS,
        "from_documents",
        lambda documents, embeddings: FakeVectorStore(),
    )

    monkeypatch.setattr(
        vector_store_service,
        "get_user_vectorstore_dir",
        lambda user_id: vectorstore_dir,
    )

    try:
        vector_store_service.create_and_save_vectorstore(
            [{"page_content": "test"}],
            user_id=123,
        )
    except RuntimeError:
        pass

    assert (
        vectorstore_dir / "index.faiss"
    ).read_text() == "old-faiss"

    assert (
        vectorstore_dir / "index.pkl"
    ).read_text() == "old-pickle"
