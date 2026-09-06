from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def get_test_token():
    """Create/reuse a dedicated test user without hitting auth rate limits."""
    from app.core.database import SessionLocal
    from app.models.auth_models import User
    from app.services.security.auth_service import (
        create_access_token,
        create_user,
    )

    email = "upload_guardrail_test@example.com"
    password = "TestPass123!"

    db = SessionLocal()

    try:
        user = db.query(User).filter(User.email == email).first()

        if user is None:
            user = create_user(
                db,
                email=email,
                password=password,
            )

        return create_access_token(user.id)
    finally:
        db.close()

def auth_headers():
    return {
        "Authorization": f"Bearer {get_test_token()}",
    }


def auth_form_data():
    return {
        "access_password": "20022004",
    }


def test_upload_pdf_exceeding_page_limit_is_blocked(monkeypatch):
    class FakeDocument:
        def __len__(self):
            return 1401

        def close(self):
            pass

    monkeypatch.setattr(
        "app.services.pdf_service.fitz.open",
        lambda _: FakeDocument(),
    )

    response = client.post(
        "/api/upload-pdf",
        headers=auth_headers(),
        data=auth_form_data(),
        files={
            "file": (
                "large.pdf",
                b"fake-pdf-content",
                "application/pdf",
            )
        },
    )

    assert response.status_code == 400
    assert (
        "maximum allowed page count of 1400 pages"
        in response.json()["detail"]
    )


def test_upload_malformed_pdf_is_rejected_and_cleaned_up(
    tmp_path,
    monkeypatch,
):
    async def fake_save_uploaded_file(
        file,
        user_id=None,
    ):
        return (
            "malformed.pdf",
            str(tmp_path / "malformed.pdf"),
            0.01,
        )

    monkeypatch.setattr(
        "app.api.routes.upload.save_uploaded_file",
        fake_save_uploaded_file,
    )

    saved_path = tmp_path / "malformed.pdf"
    saved_path.write_bytes(b"not a real pdf")

    monkeypatch.setattr(
        "app.api.routes.upload.extract_text_from_pdf",
        lambda _: (_ for _ in ()).throw(
            ValueError(
                "Invalid or unreadable PDF: cannot open malformed PDF"
            )
        ),
    )

    response = client.post(
        "/api/upload-pdf",
        headers=auth_headers(),
        data=auth_form_data(),
        files={
            "file": (
                "malformed.pdf",
                b"not a real pdf",
                "application/pdf",
            )
        },
    )

    assert response.status_code == 400
    assert "Invalid or unreadable PDF" in response.json()["detail"]
    assert not saved_path.exists()
