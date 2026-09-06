from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.main import app
from app.core.database import SessionLocal
from app.models.auth_models import PasswordResetToken, User
from app.services.security.auth_rate_limit import (
    PASSWORD_RESET_CONFIRM_RATE_LIMITER,
)
from app.services.security.auth_service import (
    create_access_token,
    create_password_reset_token,
    create_user,
)


client = TestClient(app)


TEST_EMAIL = "password_reset_test@example.com"
TEST_PASSWORD = "OldPassword123!"


def get_or_create_local_user(
    email: str = TEST_EMAIL,
    password: str = TEST_PASSWORD,
):
    db = SessionLocal()

    try:
        user = (
            db.query(User)
            .filter(User.email == email)
            .first()
        )

        if user is None:
            user = create_user(
                db=db,
                email=email,
                password=password,
            )

        return user.id

    finally:
        db.close()


def test_forgot_password_returns_same_response_for_existing_and_missing_email():
    existing_user_id = get_or_create_local_user()

    existing_response = client.post(
        "/api/auth/forgot-password",
        json={
            "email": TEST_EMAIL,
        },
    )

    missing_response = client.post(
        "/api/auth/forgot-password",
        json={
            "email": "does-not-exist@example.com",
        },
    )

    assert existing_user_id is not None

    assert existing_response.status_code == 200
    assert missing_response.status_code == 200

    assert existing_response.json() == missing_response.json()

    assert "reset" in existing_response.json()["message"].lower()


def test_password_reset_token_is_stored_as_hash():
    user_id = get_or_create_local_user(
        email="password_hash_storage_test@example.com",
    )

    db = SessionLocal()

    try:
        user = db.query(User).filter(User.id == user_id).first()

        raw_token = create_password_reset_token(
            db=db,
            user=user,
        )

        stored = (
            db.query(PasswordResetToken)
            .filter(
                PasswordResetToken.user_id == user.id
            )
            .order_by(PasswordResetToken.id.desc())
            .first()
        )

        assert stored is not None
        assert stored.token_hash != raw_token
        assert len(stored.token_hash) == 64

    finally:
        db.close()


def test_valid_password_reset_token_changes_password():
    user_id = get_or_create_local_user(
        email="password_change_test@example.com",
    )

    db = SessionLocal()

    try:
        user = db.query(User).filter(User.id == user_id).first()

        raw_token = create_password_reset_token(
            db=db,
            user=user,
        )

    finally:
        db.close()

    response = client.post(
        "/api/auth/reset-password",
        json={
            "token": raw_token,
            "new_password": "NewPassword456!",
        },
    )

    assert response.status_code == 200
    assert response.json()["message"] == (
        "Password has been reset successfully."
    )

    db = SessionLocal()

    try:
        user = db.query(User).filter(User.id == user_id).first()

        assert user is not None
        assert user.password_hash is not None

        from app.services.security.auth_service import (
            verify_password,
        )

        assert verify_password(
            "NewPassword456!",
            user.password_hash,
        )

    finally:
        db.close()


def test_password_reset_token_can_only_be_used_once():
    user_id = get_or_create_local_user(
        email="single_use_reset_test@example.com",
    )

    db = SessionLocal()

    try:
        user = db.query(User).filter(User.id == user_id).first()

        raw_token = create_password_reset_token(
            db=db,
            user=user,
        )

    finally:
        db.close()

    first_response = client.post(
        "/api/auth/reset-password",
        json={
            "token": raw_token,
            "new_password": "FirstNewPassword123!",
        },
    )

    second_response = client.post(
        "/api/auth/reset-password",
        json={
            "token": raw_token,
            "new_password": "SecondNewPassword123!",
        },
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 400
    assert second_response.json()["detail"] == (
        "Invalid or expired password reset token."
    )


def test_invalid_password_reset_token_is_rejected():
    response = client.post(
        "/api/auth/reset-password",
        json={
            "token": "this-is-an-invalid-reset-token-123456",
            "new_password": "NewPassword789!",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Invalid or expired password reset token."
    )


def test_expired_password_reset_token_is_rejected():
    user_id = get_or_create_local_user(
        email="expired_reset_test@example.com",
    )

    db = SessionLocal()

    try:
        user = db.query(User).filter(User.id == user_id).first()

        raw_token = create_password_reset_token(
            db=db,
            user=user,
            expires_minutes=1,
        )

        reset_record = (
            db.query(PasswordResetToken)
            .filter(
                PasswordResetToken.user_id == user.id
            )
            .order_by(PasswordResetToken.id.desc())
            .first()
        )

        reset_record.expires_at = (
            datetime.now(timezone.utc)
            - timedelta(minutes=1)
        )

        db.commit()

    finally:
        db.close()

    response = client.post(
        "/api/auth/reset-password",
        json={
            "token": raw_token,
            "new_password": "ExpiredPassword123!",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Invalid or expired password reset token."
    )


def test_weak_password_is_rejected():
    user_id = get_or_create_local_user(
        email="weak_password_reset_test@example.com",
    )

    db = SessionLocal()

    try:
        user = db.query(User).filter(User.id == user_id).first()

        raw_token = create_password_reset_token(
            db=db,
            user=user,
        )

    finally:
        db.close()

    response = client.post(
        "/api/auth/reset-password",
        json={
            "token": raw_token,
            "new_password": "short",
        },
    )

    assert response.status_code == 422


def test_google_only_account_does_not_create_password_reset_token():
    email = "google_only_reset_test@example.com"

    db = SessionLocal()

    try:
        user = (
            db.query(User)
            .filter(User.email == email)
            .first()
        )

        if user is None:
            user = User(
                email=email,
                password_hash=None,
                auth_provider="google",
                google_sub="google-reset-test-sub",
                is_active=True,
            )
            db.add(user)
            db.commit()
            db.refresh(user)

    finally:
        db.close()

    response = client.post(
        "/api/auth/forgot-password",
        json={
            "email": email,
        },
    )

    assert response.status_code == 200

    db = SessionLocal()

    try:
        token_count = (
            db.query(PasswordResetToken)
            .filter(
                PasswordResetToken.user_id == user.id
            )
            .count()
        )

        assert token_count == 0

    finally:
        db.close()


def test_password_reset_revokes_existing_access_token():
    email = "jwt_revocation_reset_test@example.com"
    user_id = get_or_create_local_user(
        email=email,
        password="OldPassword123!",
    )

    db = SessionLocal()

    try:
        user = db.query(User).filter(User.id == user_id).first()

        assert user is not None

        old_token_version = user.token_version

        access_token = create_access_token(
            user.id,
            token_version=user.token_version,
        )

        raw_reset_token = create_password_reset_token(
            db=db,
            user=user,
        )

    finally:
        db.close()

    PASSWORD_RESET_CONFIRM_RATE_LIMITER.reset()

    reset_response = client.post(
        "/api/auth/reset-password",
        json={
            "token": raw_reset_token,
            "new_password": "RevokedPassword456!",
        },
    )

    assert reset_response.status_code == 200

    db = SessionLocal()

    try:
        user = db.query(User).filter(User.id == user_id).first()

        assert user is not None
        assert user.token_version == old_token_version + 1

    finally:
        db.close()

    protected_response = client.get(
        "/api/auth/me",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )

    assert protected_response.status_code == 401
    assert protected_response.json()["detail"] == (
        "Authentication token has been revoked."
    )


def test_weak_password_does_not_consume_reset_token():
    email = "weak_password_reset_test@example.com"

    user_id = get_or_create_local_user(
        email=email,
        password="OldPassword123!",
    )

    db = SessionLocal()

    try:
        user = db.query(User).filter(User.id == user_id).first()

        assert user is not None

        raw_reset_token = create_password_reset_token(
            db=db,
            user=user,
        )

    finally:
        db.close()

    weak_response = client.post(
        "/api/auth/reset-password",
        json={
            "token": raw_reset_token,
            "new_password": "short",
        },
    )

    assert weak_response.status_code == 422
    assert "at least 8 characters" in (
        weak_response.json()["detail"][0]["msg"]
    )

    # Reset the test limiter so we can prove that the same
    # reset token is still usable after the rejected password.
    PASSWORD_RESET_CONFIRM_RATE_LIMITER.reset()

    # The token should still be usable because password
    # validation happens before token consumption.
    valid_response = client.post(
        "/api/auth/reset-password",
        json={
            "token": raw_reset_token,
            "new_password": "ValidPassword456!",
        },
    )

    assert valid_response.status_code == 200
    assert valid_response.json()["message"] == (
        "Password has been reset successfully."
    )
