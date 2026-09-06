import os
from pathlib import Path

from dotenv import load_dotenv

# Base project directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Load environment variables from the project .env file
load_dotenv(BASE_DIR / ".env")

# Storage root
STORAGE_DIR = BASE_DIR / "storage"

# Runtime storage folders
UPLOAD_DIR = STORAGE_DIR / "uploads"
VECTORSTORE_DIR = STORAGE_DIR / "vectorstore"
PAGE_IMAGE_DIR = STORAGE_DIR / "page_images"
DEBUG_OUTPUT_DIR = STORAGE_DIR / "debug_output"
SUMMARY_DIR = STORAGE_DIR / "summaries"
EVALUATION_DIR = STORAGE_DIR / "evaluations"

# Logs folder
LOG_DIR = BASE_DIR / "logs"

# Automatically create folders if missing
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
VECTORSTORE_DIR.mkdir(parents=True, exist_ok=True)
PAGE_IMAGE_DIR.mkdir(parents=True, exist_ok=True)
DEBUG_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
SUMMARY_DIR.mkdir(parents=True, exist_ok=True)
EVALUATION_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Validation rules
ALLOWED_EXTENSIONS = [".pdf"]
ALLOWED_MIME_TYPES = ["application/pdf"]
MAX_FILE_SIZE_MB = 200
MAX_PDF_PAGES = 1400
# LLM evaluation configuration
# Can be overridden through the EVALUATION_MODEL environment variable.
EVALUATION_MODEL = os.getenv(
    "EVALUATION_MODEL",
    "gpt-4o-mini",
)


# -----------------------------------
# REQUIRED ENVIRONMENT VALIDATION
# -----------------------------------
REQUIRED_ENV_VARS = (
    "OPENAI_API_KEY",
    "RAG_ACCESS_PASSWORD",
    "JWT_SECRET_KEY",
)


def validate_required_environment() -> None:
    """
    Validate required backend secrets without exposing
    their values in logs or error messages.
    """

    missing = [
        name
        for name in REQUIRED_ENV_VARS
        if not os.getenv(name) or not os.getenv(name).strip()
    ]

    if missing:
        raise RuntimeError(
            "Required environment configuration is missing: "
            + ", ".join(missing)
        )
