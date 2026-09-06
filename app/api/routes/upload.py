import uuid
from pathlib import Path

from fastapi import (
    APIRouter,
    UploadFile,
    File,
    HTTPException,
    Form,
    Depends,
)

from app.services.validation_service import validate_pdf_file

from app.models.auth_models import User
from app.services.security.auth_dependencies import get_current_user
from app.services.security.rag_authorization import resolve_authorized_api_key

from app.utils.file_handler import save_uploaded_file

from app.services.pdf_service import extract_text_from_pdf

from app.models.response_models import UploadPDFResponse

from app.utils.metadata_builder import build_chunk_metadata

from app.utils.debug_exporter import export_debug_files

from app.services.document_registry_service import (
    save_active_document
)

from app.services.pdf_image_service import (
    generate_page_images
)

from app.services.summary_storage_service import (
    save_summary_source
)

from app.services.vector_store_service import (
    convert_chunks_to_documents,
    create_and_save_vectorstore
)

router = APIRouter()


@router.post(
    "/upload-pdf",
    response_model=UploadPDFResponse
)
async def upload_pdf(

    file: UploadFile = File(...),

    access_password: str = Form(""),

    user_openai_api_key: str = Form(""),

    current_user: User = Depends(get_current_user),
):
    saved_path = None
    try:

        # -----------------------------------
        # AUTHORIZATION
        # -----------------------------------
        api_key = resolve_authorized_api_key(
            user=current_user,
            access_password=access_password,
            user_openai_api_key=user_openai_api_key,
        )

        # -----------------------------------
        # VALIDATE PDF
        # -----------------------------------
        await validate_pdf_file(file)

        # -----------------------------------
        # SAVE PDF
        # -----------------------------------
        (
            original_filename,
            saved_path,
            file_size_mb
        ) = await save_uploaded_file(
            file,
            user_id=current_user.id,
        )

        # -----------------------------------
        # EXTRACT PDF TEXT
        # -----------------------------------
        try:
            pdf_data = extract_text_from_pdf(saved_path)
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=str(e),
            )

        pages_data = pdf_data["pages"]

        total_pages = pdf_data["total_pages"]

        extracted_text = "\n".join(
            [
                page["text"]
                for page in pages_data
            ]
        )

        # -----------------------------------
        # LOW TEXT / SCANNED CHECK
        # -----------------------------------
        if (
            not extracted_text.strip()
            or len(extracted_text.strip()) < 50
        ):

            return UploadPDFResponse(

                status="error",

                filename=original_filename,

                saved_filename=saved_path.split("\\")[-1]
                .split("/")[-1],

                file_size_mb=file_size_mb,

                total_pages=total_pages,

                extracted_characters=len(extracted_text),

                num_chunks=0,

                selected_chunk_size=0,

                selected_chunk_overlap=0,

                preview_chunk=None,

                message=(
                    "This PDF appears to be scanned "
                    "or image-based. For best results, "
                    "please upload a text-selectable PDF."
                )
            )

        # -----------------------------------
        # DOCUMENT ID
        # -----------------------------------
        doc_id = str(uuid.uuid4())

        # -----------------------------------
        # GENERATE PAGE IMAGES
        # -----------------------------------
        generate_page_images(
            saved_path,
            doc_id,
            user_id=current_user.id,
        )

        # -----------------------------------
        # SAVE SUMMARY SOURCE
        # -----------------------------------
        save_summary_source(
            doc_id,
            extracted_text,
            user_id=current_user.id,
        )

        # -----------------------------------
        # BUILD CHUNK METADATA
        # -----------------------------------
        metadata, chunk_configs = (
            build_chunk_metadata(
                pages_data,
                original_filename,
                doc_id
            )
        )

        # -----------------------------------
        # CONVERT TO LANGCHAIN DOCS
        # -----------------------------------
        documents = convert_chunks_to_documents(
            metadata,
            original_filename
        )

        # -----------------------------------
        # CREATE VECTORSTORE
        # -----------------------------------
        create_and_save_vectorstore(
            documents,
            user_id=current_user.id,
        )

        # -----------------------------------
        # EXPORT DEBUG FILES
        # -----------------------------------
        export_debug_files(
            original_filename,
            pages_data,
            metadata,
            user_id=current_user.id,
        )

        # -----------------------------------
        # ACTIVE DOCUMENT REGISTRY
        # -----------------------------------
        save_active_document(
            doc_id,
            original_filename,
            user_id=current_user.id,
        )

        # -----------------------------------
        # DYNAMIC CHUNK STATS
        # -----------------------------------
        avg_chunk_size = (

            sum(
                config["chunk_size"]
                for config in chunk_configs
            ) // len(chunk_configs)

            if chunk_configs else 0
        )

        avg_chunk_overlap = (

            sum(
                config["chunk_overlap"]
                for config in chunk_configs
            ) // len(chunk_configs)

            if chunk_configs else 0
        )

        # -----------------------------------
        # SUCCESS RESPONSE
        # -----------------------------------
        return UploadPDFResponse(

            status="success",

            filename=original_filename,

            saved_filename=saved_path.split("\\")[-1]
            .split("/")[-1],

            file_size_mb=file_size_mb,

            total_pages=total_pages,

            extracted_characters=len(extracted_text),

            num_chunks=len(metadata),

            selected_chunk_size=avg_chunk_size,

            selected_chunk_overlap=avg_chunk_overlap,

            preview_chunk=(
                metadata[0]["text"]
                if metadata else None
            ),

            message=(
                "PDF uploaded, active document set, "
                "chunked, embedded, stored, exported, "
                "summary source saved, and page images "
                "generated successfully."
            )
        )
    except HTTPException as e:

        if saved_path:
            saved_file = Path(saved_path)

            if saved_file.exists():
                saved_file.unlink()

        raise e

    except Exception as e:

        if saved_path:
            saved_file = Path(saved_path)

            if saved_file.exists():
                saved_file.unlink()

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
