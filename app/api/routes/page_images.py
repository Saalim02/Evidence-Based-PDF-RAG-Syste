from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from app.models.auth_models import User
from app.services.security.auth_dependencies import get_current_user
from app.services.user_storage_service import get_user_page_image_dir

router = APIRouter()


@router.get("/page-images/{doc_id}/{page_filename}")
def get_page_image(
    doc_id: str,
    page_filename: str,
    current_user: User = Depends(get_current_user),
):
    """
    Serve a page preview image only from the authenticated
    user's isolated page-image directory.
    """

    # Reject path separators and traversal attempts.
    if (
        not doc_id
        or not page_filename
        or Path(doc_id).name != doc_id
        or Path(page_filename).name != page_filename
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid page image path.",
        )

    # Restrict access to generated PNG page images.
    if not (
        page_filename.startswith("page_")
        and page_filename.endswith(".png")
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid page image filename.",
        )

    user_page_dir = get_user_page_image_dir(current_user.id)

    user_root = user_page_dir.resolve()
    image_path = (
        user_page_dir / doc_id / page_filename
    ).resolve()

    # Defense in depth: resolved path must remain
    # inside the authenticated user's page-image directory.
    try:
        image_path.relative_to(user_root)
    except ValueError:
        raise HTTPException(
            status_code=403,
            detail="Access to this page image is not allowed.",
        )

    if not image_path.is_file():
        raise HTTPException(
            status_code=404,
            detail="Page image not found.",
        )

    return FileResponse(
        path=image_path,
        media_type="image/png",
    )
