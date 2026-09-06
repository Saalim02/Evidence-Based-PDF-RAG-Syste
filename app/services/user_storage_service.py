from pathlib import Path

from app.core.config import STORAGE_DIR


USER_STORAGE_DIR = STORAGE_DIR / "users"


def get_user_storage_dir(user_id: int) -> Path:
    """
    Return the isolated storage directory for one authenticated user.
    """
    user_dir = USER_STORAGE_DIR / str(int(user_id))
    user_dir.mkdir(parents=True, exist_ok=True)
    return user_dir


def get_user_upload_dir(user_id: int) -> Path:
    path = get_user_storage_dir(user_id) / "uploads"
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_user_vectorstore_dir(user_id: int) -> Path:
    path = get_user_storage_dir(user_id) / "vectorstore"
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_user_page_image_dir(user_id: int) -> Path:
    path = get_user_storage_dir(user_id) / "page_images"
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_user_summary_dir(user_id: int) -> Path:
    path = get_user_storage_dir(user_id) / "summaries"
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_user_debug_dir(user_id: int) -> Path:
    path = get_user_storage_dir(user_id) / "debug_output"
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_user_registry_path(user_id: int) -> Path:
    return get_user_storage_dir(user_id) / "document_registry.json"


def get_user_evaluation_dir(user_id: int) -> Path:
    path = get_user_storage_dir(user_id) / "evaluations"
    path.mkdir(parents=True, exist_ok=True)
    return path
