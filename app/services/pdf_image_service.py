import fitz  # PyMuPDF

from app.core.config import (
    PAGE_IMAGE_DIR
)


def generate_page_images(
    pdf_path: str,
    doc_id: str
):

    """
    Converts PDF pages into images
    and saves them into centralized
    storage/page_images directory.
    """

    # -----------------------------------
    # OPEN PDF
    # -----------------------------------
    doc = fitz.open(pdf_path)

    # -----------------------------------
    # DOCUMENT IMAGE FOLDER
    # -----------------------------------
    doc_folder = (
        PAGE_IMAGE_DIR / doc_id
    )

    doc_folder.mkdir(
        parents=True,
        exist_ok=True
    )

    image_paths = []

    # -----------------------------------
    # GENERATE PAGE IMAGES
    # -----------------------------------
    for page_num in range(len(doc)):

        page = doc.load_page(page_num)

        # -----------------------------------
        # HIGHER QUALITY RENDER
        # -----------------------------------
        matrix = fitz.Matrix(
            2,
            2
        )

        pix = page.get_pixmap(
            matrix=matrix
        )

        image_path = (
            doc_folder /
            f"page_{page_num + 1}.png"
        )

        pix.save(
            str(image_path)
        )

        image_paths.append({

            "page_number":
            page_num + 1,

            "image_path":
            str(image_path)
        })

    # -----------------------------------
    # CLOSE PDF
    # -----------------------------------
    doc.close()

    return image_paths