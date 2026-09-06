import json
from pathlib import Path

from app.core.config import BASE_DIR
from app.services.user_storage_service import get_user_registry_path


LEGACY_REGISTRY_PATH = (
    BASE_DIR / "vectorstore" / "document_registry.json"
)


def _get_registry_path(user_id: int | None = None) -> Path:
    """
    Return the document registry path.

    user_id provided:
        Isolated user registry.

    user_id omitted:
        Legacy global registry for backwards compatibility.
    """

    if user_id is None:
        return LEGACY_REGISTRY_PATH

    return get_user_registry_path(user_id)


def save_active_document(
    doc_id: str,
    filename: str,
    user_id: int | None = None,
):
    """
    Save the active document for a user.
    """

    registry_path = _get_registry_path(user_id)

    registry_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    data = {
        "active_doc_id": doc_id,
        "active_filename": filename,
    }

    with open(
        registry_path,
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            data,
            f,
            indent=4,
        )


def get_active_document(
    user_id: int | None = None,
):
    """
    Get the active document for a user.
    """

    registry_path = _get_registry_path(user_id)

    if not registry_path.exists():
        return None

    with open(
        registry_path,
        "r",
        encoding="utf-8",
    ) as f:
        return json.load(f)


def clear_active_document(
    user_id: int | None = None,
):
    """
    Clear the active document for a user.
    """

    registry_path = _get_registry_path(user_id)

    if registry_path.exists():
        registry_path.unlink()
