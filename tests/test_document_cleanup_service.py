from pathlib import Path

from app.services.document_cleanup_service import (
    cleanup_failed_upload,
)


def test_cleanup_failed_upload_removes_user_artifacts(
    tmp_path,
    monkeypatch,
):
    user_id = 123
    doc_id = "test-doc-001"
    filename = "test_document.pdf"

    user_root = tmp_path / "users" / str(user_id)

    upload_dir = user_root / "uploads"
    page_image_dir = (
        user_root / "page_images" / doc_id
    )
    summary_dir = (
        user_root / "summaries" / "summary_source"
    )
    debug_dir = (
        user_root / "debug_output" / "test_document"
    )

    upload_dir.mkdir(parents=True)
    page_image_dir.mkdir(parents=True)
    summary_dir.mkdir(parents=True)
    debug_dir.mkdir(parents=True)

    saved_pdf = upload_dir / filename
    saved_pdf.write_text("fake pdf", encoding="utf-8")

    (page_image_dir / "page_1.png").write_text(
        "fake image",
        encoding="utf-8",
    )

    (summary_dir / f"{doc_id}.txt").write_text(
        "summary source",
        encoding="utf-8",
    )

    (debug_dir / "metadata.json").write_text(
        "{}",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "app.services.document_cleanup_service.get_user_page_image_dir",
        lambda user_id: user_root / "page_images",
    )

    monkeypatch.setattr(
        "app.services.document_cleanup_service.get_user_summary_dir",
        lambda user_id: user_root / "summaries",
    )

    monkeypatch.setattr(
        "app.services.document_cleanup_service.get_user_debug_dir",
        lambda user_id: user_root / "debug_output",
    )

    cleanup_failed_upload(
        user_id=user_id,
        doc_id=doc_id,
        saved_path=str(saved_pdf),
        filename=filename,
    )

    assert not saved_pdf.exists()
    assert not page_image_dir.exists()
    assert not (summary_dir / f"{doc_id}.txt").exists()
    assert not debug_dir.exists()


def test_cleanup_does_not_delete_vectorstore(
    tmp_path,
    monkeypatch,
):
    user_id = 123

    user_root = tmp_path / "users" / str(user_id)
    vectorstore_dir = user_root / "vectorstore"

    vectorstore_dir.mkdir(parents=True)
    marker = vectorstore_dir / "index.faiss"
    marker.write_text(
        "existing vectorstore",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "app.services.document_cleanup_service.get_user_page_image_dir",
        lambda user_id: user_root / "page_images",
    )

    monkeypatch.setattr(
        "app.services.document_cleanup_service.get_user_summary_dir",
        lambda user_id: user_root / "summaries",
    )

    monkeypatch.setattr(
        "app.services.document_cleanup_service.get_user_debug_dir",
        lambda user_id: user_root / "debug_output",
    )

    cleanup_failed_upload(
        user_id=user_id,
        doc_id="failed-doc",
    )

    assert vectorstore_dir.exists()
    assert marker.exists()
