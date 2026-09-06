import fitz  # PyMuPDF

from app.core.config import PAGE_IMAGE_DIR
from app.services.user_storage_service import get_user_page_image_dir


def generate_page_images(
    pdf_path: str,
    doc_id: str,
    user_id: int | None = None,
):
    """
    Converts PDF pages into images.

    When user_id is provided, images are stored in
    that user's isolated storage directory.
    """

    doc = fitz.open(pdf_path)

    if user_id is not None:
        base_dir = get_user_page_image_dir(user_id)
    else:
        base_dir = PAGE_IMAGE_DIR

    doc_folder = base_dir / doc_id

    doc_folder.mkdir(
        parents=True,
        exist_ok=True,
    )

    image_paths = []

    for page_num in range(len(doc)):

        page = doc.load_page(page_num)

        matrix = fitz.Matrix(2, 2)

        pix = page.get_pixmap(
            matrix=matrix
        )

        image_path = (
            doc_folder /
            f"page_{page_num + 1}.png"
        )

        pix.save(str(image_path))

        image_paths.append({
            "page_number": page_num + 1,
            "image_path": str(image_path),
        })

    doc.close()

    return image_paths
