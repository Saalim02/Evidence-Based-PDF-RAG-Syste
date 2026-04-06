import uuid
from pathlib import Path
from fastapi import UploadFile
from app.core.config import UPLOAD_DIR


async def save_uploaded_file(file: UploadFile) -> tuple[str, str, float]:
    original_filename = file.filename
    extension = Path(original_filename).suffix
    unique_filename = f"{uuid.uuid4().hex}{extension}"
    file_path = UPLOAD_DIR / unique_filename

    content = await file.read()

    with open(file_path, "wb") as buffer:
        buffer.write(content)

    file_size_mb = round(len(content) / (1024 * 1024), 2)

    return original_filename, str(file_path), file_size_mb