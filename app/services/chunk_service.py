from langchain_text_splitters import RecursiveCharacterTextSplitter


def get_page_chunk_config(text: str):
    total_chars = len(text)

    if total_chars < 800:
        chunk_size = 300
        chunk_overlap = 50
    elif total_chars < 2000:
        chunk_size = 400
        chunk_overlap = 80
    elif total_chars < 5000:
        chunk_size = 500
        chunk_overlap = 100
    else:
        chunk_size = 700
        chunk_overlap = 120

    # Safety
    if total_chars < chunk_size:
        chunk_size = max(total_chars, 50)

    if chunk_overlap >= chunk_size:
        chunk_overlap = max(chunk_size // 5, 10)

    return {
        "chunk_size": chunk_size,
        "chunk_overlap": chunk_overlap
    }


def chunk_page_text(text: str):
    cleaned_text = text.strip()

    if not cleaned_text:
        return [], {"chunk_size": 0, "chunk_overlap": 0}

    config = get_page_chunk_config(cleaned_text)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=config["chunk_size"],
        chunk_overlap=config["chunk_overlap"]
    )

    chunks = splitter.split_text(cleaned_text)

    return chunks, config