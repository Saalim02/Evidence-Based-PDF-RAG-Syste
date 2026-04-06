import fitz  # PyMuPDF
from pathlib import Path


PAGE_IMAGE_DIR = Path("page_images")
PAGE_IMAGE_DIR.mkdir(exist_ok=True)


def generate_page_images(pdf_path: str, doc_id: str):
    """
    Converts each PDF page into an image and saves locally.
    """

    doc = fitz.open(pdf_path)

    doc_folder = PAGE_IMAGE_DIR / doc_id
    doc_folder.mkdir(exist_ok=True)

    image_paths = []

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)

        pix = page.get_pixmap()

        image_path = doc_folder / f"page_{page_num + 1}.png"
        pix.save(str(image_path))

        image_paths.append({
            "page_number": page_num + 1,
            "image_path": str(image_path)
        })

    return image_paths