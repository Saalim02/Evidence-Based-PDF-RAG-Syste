from pathlib import Path

# Base project directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Storage root
STORAGE_DIR = BASE_DIR / "storage"

# Runtime storage folders
UPLOAD_DIR = STORAGE_DIR / "uploads"
VECTORSTORE_DIR = STORAGE_DIR / "vectorstore"
PAGE_IMAGE_DIR = STORAGE_DIR / "page_images"
DEBUG_OUTPUT_DIR = STORAGE_DIR / "debug_output"
SUMMARY_DIR = STORAGE_DIR / "summaries"

# Logs folder
LOG_DIR = BASE_DIR / "logs"

# Automatically create folders if missing
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
VECTORSTORE_DIR.mkdir(parents=True, exist_ok=True)
PAGE_IMAGE_DIR.mkdir(parents=True, exist_ok=True)
DEBUG_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
SUMMARY_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Validation rules
ALLOWED_EXTENSIONS = [".pdf"]
ALLOWED_MIME_TYPES = ["application/pdf"]
MAX_FILE_SIZE_MB = 70