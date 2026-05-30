from pathlib import Path

from app.core.config import (
    SUMMARY_DIR
)


# -----------------------------------
# SUMMARY SOURCE DIRECTORY
# -----------------------------------
SUMMARY_SOURCE_DIR = (
    SUMMARY_DIR / "summary_source"
)

# -----------------------------------
# CREATE DIRECTORY
# -----------------------------------
SUMMARY_SOURCE_DIR.mkdir(
    parents=True,
    exist_ok=True
)


def save_summary_source(
    doc_id: str,
    full_text: str
):
    """
    Saves full extracted PDF text
    for summary generation.
    """

    # -----------------------------------
    # FILE PATH
    # -----------------------------------
    file_path = (
        SUMMARY_SOURCE_DIR /
        f"{doc_id}.txt"
    )

    # -----------------------------------
    # SAVE TEXT
    # -----------------------------------
    with open(
        file_path,
        "w",
        encoding="utf-8"
    ) as f:

        f.write(full_text)


def load_summary_source(
    doc_id: str
):
    """
    Loads saved extracted PDF text
    for summary generation.
    """

    # -----------------------------------
    # FILE PATH
    # -----------------------------------
    file_path = (
        SUMMARY_SOURCE_DIR /
        f"{doc_id}.txt"
    )

    # -----------------------------------
    # FILE NOT FOUND
    # -----------------------------------
    if not file_path.exists():

        return None

    # -----------------------------------
    # READ FILE
    # -----------------------------------
    with open(
        file_path,
        "r",
        encoding="utf-8"
    ) as f:

        return f.read()