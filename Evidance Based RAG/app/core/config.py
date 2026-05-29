from pathlib import Path

# Upload folder
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Debug output folder
DEBUG_OUTPUT_DIR = Path("debug_output")
DEBUG_OUTPUT_DIR.mkdir(exist_ok=True)

# Validation rules
ALLOWED_EXTENSIONS = [".pdf"]
ALLOWED_MIME_TYPES = ["application/pdf"]
MAX_FILE_SIZE_MB = 70