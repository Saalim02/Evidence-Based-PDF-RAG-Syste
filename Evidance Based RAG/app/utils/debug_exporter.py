import json
from pathlib import Path
from app.core.config import DEBUG_OUTPUT_DIR


def export_debug_files(source_filename, pages_data, metadata):
    safe_name = Path(source_filename).stem
    base_dir = DEBUG_OUTPUT_DIR / safe_name

    clean_pages_dir = base_dir / "clean_pages"
    chunks_dir = base_dir / "chunks"

    clean_pages_dir.mkdir(parents=True, exist_ok=True)
    chunks_dir.mkdir(parents=True, exist_ok=True)

    # Save clean extracted pages
    for page in pages_data:
        page_num = page["page_number"]
        page_text = page["text"]

        page_file = clean_pages_dir / f"page_{page_num:03}.txt"
        with open(page_file, "w", encoding="utf-8") as f:
            f.write(page_text)

    # Save chunks separately
    for item in metadata:
        page_num = item["page_number"]
        page_chunk_id = item["page_chunk_id"]
        chunk_text = item["text"]

        chunk_file = chunks_dir / f"page_{page_num:03}_chunk_{page_chunk_id:02}.txt"
        with open(chunk_file, "w", encoding="utf-8") as f:
            f.write(chunk_text)

    # Save metadata.json
    metadata_file = base_dir / "metadata.json"
    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=4, ensure_ascii=False)