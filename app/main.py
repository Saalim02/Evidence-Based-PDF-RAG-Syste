from dotenv import load_dotenv

# -----------------------------------
# LOAD ENV VARIABLES
# -----------------------------------
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes.upload import (
    router as upload_router
)

from app.api.routes.query import (
    router as query_router
)

from app.api.routes.summary import (
    router as summary_router
)

from app.api.routes.suggested_questions import (
    router as suggested_questions_router
)

from app.core.config import (
    PAGE_IMAGE_DIR
)

# -----------------------------------
# FASTAPI APP
# -----------------------------------
app = FastAPI()

# -----------------------------------
# CORS
# -----------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8501",
        "http://127.0.0.1:8501",
        "http://localhost:8502",
        "http://127.0.0.1:8502",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------
# ROOT
# -----------------------------------
@app.get("/")
def root():

    return {
        "message":
        "Evidence-Based RAG Backend Running Successfully 🚀"
    }


# -----------------------------------
# HEALTH CHECK
# -----------------------------------
@app.get("/health")
def health_check():

    return {
        "status": "healthy"
    }


# -----------------------------------
# SERVE PAGE PREVIEW IMAGES
# -----------------------------------
app.mount(
    "/page_images",
    StaticFiles(
        directory=str(PAGE_IMAGE_DIR)
    ),
    name="page_images"
)

# -----------------------------------
# REGISTER ROUTES
# -----------------------------------
app.include_router(
    upload_router,
    prefix="/api",
    tags=["Upload"]
)

app.include_router(
    query_router,
    prefix="/api",
    tags=["Query"]
)

app.include_router(
    summary_router,
    prefix="/api",
    tags=["Summary"]
)

app.include_router(
    suggested_questions_router,
    prefix="/api",
    tags=["Suggested Questions"]
)