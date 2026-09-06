import fitz

from app.core.config import MAX_PDF_PAGES


def extract_text_from_pdf(pdf_path: str) -> dict:
    try:
        doc = fitz.open(pdf_path)

        total_pages = len(doc)

        if total_pages > MAX_PDF_PAGES:
            doc.close()
            raise ValueError(
                f"PDF exceeds the maximum allowed page count "
                f"of {MAX_PDF_PAGES} pages."
            )

        pages_data = []

        for page_number, page in enumerate(doc, start=1):
            page_text = page.get_text().strip()
            pages_data.append({
                "page_number": page_number,
                "text": page_text
            })

        doc.close()

        return {
            "pages": pages_data,
            "total_pages": total_pages
        }

    except ValueError:
        raise

    except Exception as e:
        raise ValueError(
            f"Invalid or unreadable PDF: {str(e)}"
        )
