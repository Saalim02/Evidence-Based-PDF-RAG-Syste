import fitz


def extract_text_from_pdf(pdf_path: str) -> dict:
    try:
        doc = fitz.open(pdf_path)

        pages_data = []

        for page_number, page in enumerate(doc, start=1):
            page_text = page.get_text().strip()
            pages_data.append({
                "page_number": page_number,
                "text": page_text
            })

        total_pages = len(doc)
        doc.close()

        return {
            "pages": pages_data,
            "total_pages": total_pages
        }

    except Exception as e:
        raise Exception(f"PDF read error: {str(e)}")