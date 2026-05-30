import uuid
from pathlib import Path

from fastapi import UploadFile

from app.core.config import (
    UPLOAD_DIR
)


async def save_uploaded_file(
    file: UploadFile
) -> tuple[str, str, float]:

    """
    Saves uploaded PDF into centralized
    storage/uploads directory.
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

    file_path = (
        UPLOAD_DIR /
        unique_filename
    )

    # -----------------------------------
    # READ FILE CONTENT
    # -----------------------------------
    content = await file.read()

    # -----------------------------------
    # SAVE FILE
    # -----------------------------------
    with open(
        file_path,
        "wb"
    ) as buffer:

        buffer.write(content)

    # -----------------------------------
    # FILE SIZE
    # -----------------------------------
    file_size_mb = round(
        len(content) / (1024 * 1024),
        2
    )

    # -----------------------------------
    # RETURN
    # -----------------------------------
    return (
        original_filename,
        str(file_path),
        file_size_mb
    )