import shutil
from pathlib import Path

from app.services.user_storage_service import (
    get_user_page_image_dir,
    get_user_summary_dir,
    get_user_debug_dir,
)


def cleanup_failed_upload(
    *,
    user_id: int,
    doc_id: str | None = None,
    saved_path: str | None = None,
    filename: str | None = None,
) -> None:
    """
    Remove artifacts created during a failed PDF upload.

    Intentionally does NOT delete the user's vectorstore
    or active-document registry because those may belong to
    the user's previously successful document.
    """

    # -----------------------------------
    # Uploaded PDF
    # -----------------------------------
    if saved_path:
        saved_file = Path(saved_path)

        if saved_file.exists():
            saved_file.unlink()

    # -----------------------------------
    # Page images
    # -----------------------------------
    if doc_id:
        page_image_dir = (
            get_user_page_image_dir(user_id) / doc_id
        )

        if page_image_dir.exists():
            shutil.rmtree(page_image_dir)

    # -----------------------------------
    # Summary source
    # -----------------------------------
    if doc_id:
        summary_file = (
            get_user_summary_dir(user_id)
            / "summary_source"
            / f"{doc_id}.txt"
        )

        if summary_file.exists():
            summary_file.unlink()

    # -----------------------------------
    # Debug output
    # -----------------------------------
    if filename:
        safe_name = Path(filename).stem

        debug_dir = (
            get_user_debug_dir(user_id) / safe_name
        )

        if debug_dir.exists():
            shutil.rmtree(debug_dir)
