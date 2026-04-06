import json
from pathlib import Path

REGISTRY_PATH = Path("vectorstore/document_registry.json")


def save_active_document(doc_id: str, filename: str):
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "active_doc_id": doc_id,
        "active_filename": filename
    }

    with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def get_active_document():
    if not REGISTRY_PATH.exists():
        return None

    with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def clear_active_document():
    if REGISTRY_PATH.exists():
        REGISTRY_PATH.unlink()