from fastapi import UploadFile, HTTPException
from pathlib import Path

from app.core.config import (
    ALLOWED_EXTENSIONS,
    ALLOWED_MIME_TYPES,
)


async def validate_pdf_file(file: UploadFile):
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Invalid filename.",
        )

    extension = Path(file.filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed.",
        )

    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Invalid file type.",
        )
