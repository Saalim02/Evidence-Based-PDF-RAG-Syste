import os

SUMMARY_SOURCE_DIR = "debug_output/summary_source"
os.makedirs(SUMMARY_SOURCE_DIR, exist_ok=True)


def save_summary_source(doc_id: str, full_text: str):
    """
    Saves full extracted PDF text for summary generation.
    """
    file_path = os.path.join(SUMMARY_SOURCE_DIR, f"{doc_id}.txt")

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(full_text)


def load_summary_source(doc_id: str):
    """
    Loads saved full extracted PDF text for the active document.
    """
    file_path = os.path.join(SUMMARY_SOURCE_DIR, f"{doc_id}.txt")

    if not os.path.exists(file_path):
        return None

    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()