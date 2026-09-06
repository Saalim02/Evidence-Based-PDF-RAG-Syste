from app.core.config import SUMMARY_DIR
from app.services.user_storage_service import get_user_summary_dir


def _get_summary_source_dir(
    user_id: int | None = None,
):
    if user_id is not None:
        path = get_user_summary_dir(user_id) / "summary_source"
    else:
        path = SUMMARY_DIR / "summary_source"

    path.mkdir(
        parents=True,
        exist_ok=True,
    )

    return path


def save_summary_source(
    doc_id: str,
    full_text: str,
    user_id: int | None = None,
):
    """
    Saves extracted PDF text for summary generation.
    """

    file_path = (
        _get_summary_source_dir(user_id)
        / f"{doc_id}.txt"
    )

    with open(
        file_path,
        "w",
        encoding="utf-8",
    ) as f:
        f.write(full_text)


def load_summary_source(
    doc_id: str,
    user_id: int | None = None,
):
    """
    Loads extracted PDF text for summary generation.
    """

    file_path = (
        _get_summary_source_dir(user_id)
        / f"{doc_id}.txt"
    )

    if not file_path.exists():
        return None

    with open(
        file_path,
        "r",
        encoding="utf-8",
    ) as f:
        return f.read()
