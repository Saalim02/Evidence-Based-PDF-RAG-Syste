from app.services.chunk_service import chunk_page_text


def build_chunk_metadata(pages_data, source_filename, doc_id):
    metadata = []
    chunk_counter = 1
    chunk_configs = []

    for page in pages_data:
        page_number = page["page_number"]
        page_text = page["text"]

        if not page_text.strip():
            continue

        page_chunks, config = chunk_page_text(page_text)
        chunk_configs.append(config)

        for idx, chunk in enumerate(page_chunks, start=1):
            metadata.append({
                "chunk_id": chunk_counter,
                "page_chunk_id": idx,
                "doc_id": doc_id,
                "text": chunk,
                "page_number": page_number,
                "source": source_filename
            })
            chunk_counter += 1

    return metadata, chunk_configs