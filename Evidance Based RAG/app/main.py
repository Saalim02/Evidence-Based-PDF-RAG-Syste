from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes.upload import router as upload_router
from app.api.routes.query import router as query_router
from app.api.routes.summary import router as summary_router
from app.api.routes.suggested_questions import router as suggested_questions_router

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Evidence-Based RAG Backend Running Successfully 🚀"}

# Serve page preview images
app.mount("/page_images", StaticFiles(directory="page_images"), name="page_images")

# Register API routes
app.include_router(upload_router, prefix="/api", tags=["Upload"])
app.include_router(query_router, prefix="/api", tags=["Query"])
app.include_router(summary_router, prefix="/api", tags=["Summary"])
app.include_router(suggested_questions_router, prefix="/api", tags=["Suggested Questions"])