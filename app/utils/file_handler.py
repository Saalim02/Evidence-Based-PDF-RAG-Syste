import uuid
from pathlib import Path

from fastapi import UploadFile, HTTPException

from app.core.config import (
    MAX_FILE_SIZE_MB,
    UPLOAD_DIR,
)

from app.services.user_storage_service import (
    get_user_upload_dir,
)


async def save_uploaded_file(
    file: UploadFile,
    user_id: int | None = None,
) -> tuple[str, str, float]:
    """
    Streams the uploaded PDF to disk while enforcing
    the configured maximum file size.

    user_id provided:
        Store the upload in the user's isolated directory.

    user_id omitted:
        Preserve the legacy UPLOAD_DIR behavior for
        backwards compatibility and existing tests.
    """

    # -----------------------------------
    # ORIGINAL FILE INFO
    # -----------------------------------
    original_filename = file.filename

    extension = Path(
        original_filename
    ).suffix.lower()

    # -----------------------------------
    # UNIQUE FILE NAME
    # -----------------------------------
    unique_filename = (
        f"{uuid.uuid4().hex}"
        f"{extension}"
    )

    # -----------------------------------
    # SELECT STORAGE DIRECTORY
    # -----------------------------------
    if user_id is not None:
        upload_dir = get_user_upload_dir(user_id)
    else:
        upload_dir = UPLOAD_DIR

    upload_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    file_path = (
        upload_dir /
        unique_filename
    )

    # -----------------------------------
    # STREAMING SIZE LIMIT
    # -----------------------------------
    max_file_size_bytes = (
        MAX_FILE_SIZE_MB * 1024 * 1024
    )

    total_bytes = 0
    chunk_size = 1024 * 1024  # 1 MB

    # -----------------------------------
    # STREAM FILE TO DISK
    # -----------------------------------
    try:
        with open(
            file_path,
            "wb",
        ) as buffer:

            while True:
                chunk = await file.read(chunk_size)

                if not chunk:
                    break

                total_bytes += len(chunk)

                if total_bytes > max_file_size_bytes:
                    raise HTTPException(
                        status_code=400,
                        detail=(
                            f"File exceeds "
                            f"{MAX_FILE_SIZE_MB} MB limit."
                        ),
                    )

                buffer.write(chunk)

    # -----------------------------------
    # CLEAN UP FAILED UPLOAD
    # -----------------------------------
    except HTTPException:
        if file_path.exists():
            file_path.unlink()
        raise

    except Exception:
        if file_path.exists():
            file_path.unlink()
        raise

    # -----------------------------------
    # FILE SIZE
    # -----------------------------------
    file_size_mb = round(
        total_bytes / (1024 * 1024),
        2,
    )

    # -----------------------------------
    # RETURN
    # -----------------------------------
    return (
        original_filename,
        str(file_path),
        file_size_mb,
    )
