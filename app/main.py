from dotenv import load_dotenv

# -----------------------------------
# LOAD ENV VARIABLES
# -----------------------------------
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Request
from fastapi.responses import JSONResponse

from app.services.security.rate_limiter import RateLimiter

from app.services.security.audit_logger import (
    log_security_event,
)

from app.api.routes.auth import router as auth_router

from app.core.database import init_db

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

from app.api.routes.page_images import (
    router as page_images_router
)

from app.core.config import (
    validate_required_environment,
)

# -----------------------------------
# ENVIRONMENT VALIDATION
# -----------------------------------
validate_required_environment()

# -----------------------------------
# DATABASE INITIALIZATION
# -----------------------------------
init_db()

# -----------------------------------
# FASTAPI APP
# -----------------------------------
app = FastAPI()

# -----------------------------------
# RATE LIMITING
# -----------------------------------
RATE_LIMIT_RULES = {
    "/api/ask": (10, 60),
    "/api/upload-pdf": (5, 60),
    "/api/summary": (5, 60),
    "/api/suggested-questions": (10, 60),
}

_rate_limiters = {
    path: RateLimiter(
        max_requests=max_requests,
        window_seconds=window_seconds,
    )
    for path, (max_requests, window_seconds)
    in RATE_LIMIT_RULES.items()
}


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    path = request.url.path

    limiter = _rate_limiters.get(path)

    if limiter is not None:
        client_host = (
            request.client.host
            if request.client
            else "unknown"
        )

        client_id = f"{client_host}:{path}"

        if not limiter.is_allowed(client_id):
            window_seconds = RATE_LIMIT_RULES[path][1]

            log_security_event(
                "rate_limit_blocked",
                endpoint=path,
                client_id=client_host,
                decision="BLOCK",
                reasons=["Request rate limit exceeded."],
            )

            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Too many requests. Please try again later."
                },
                headers={
                    "Retry-After": str(window_seconds)
                },
            )

    return await call_next(request)


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

app.include_router(
    page_images_router,
    prefix="/api",
    tags=["Page Images"]
)
app.include_router(
    auth_router,
    prefix="/api",
)
