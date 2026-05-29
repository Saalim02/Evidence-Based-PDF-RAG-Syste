from langchain_core.prompts import ChatPromptTemplate

from app.services.document_registry_service import (
    get_active_document
)

from app.services.summary_storage_service import (
    load_summary_source
)

from app.services.llm_service import get_llm

import json
import re


def clean_json_response(raw_text: str):

    raw_text = raw_text.strip()

    raw_text = re.sub(
        r"^```json",
        "",
        raw_text,
        flags=re.IGNORECASE
    ).strip()

    raw_text = re.sub(
        r"^```",
        "",
        raw_text
    ).strip()

    raw_text = re.sub(
        r"```$",
        "",
        raw_text
    ).strip()

    return raw_text


def generate_suggested_questions(api_key: str):
    """
    Generates useful suggested questions
    based on uploaded PDF content.
    """

    # -----------------------------
    # ACTIVE DOCUMENT
    # -----------------------------
    active_doc = get_active_document()

    if not active_doc:

        return {
            "status": "error",
            "active_document": None,
            "suggested_questions": [],
            "message": "No active PDF uploaded."
        }

    active_filename = active_doc["active_filename"]
    active_doc_id = active_doc["active_doc_id"]

    # -----------------------------
    # LOAD DOCUMENT TEXT
    # -----------------------------
    document_text = load_summary_source(
        active_doc_id
    )

    if (
        not document_text
        or len(document_text.strip()) < 100
    ):

        return {
            "status": "error",
            "active_document": active_filename,
            "suggested_questions": [],
            "message": (
                "Not enough text found "
                "to generate suggested questions."
            )
        }

    # -----------------------------
    # LIMIT INPUT SIZE
    # -----------------------------
    input_text = document_text[:12000]

    # -----------------------------
    # DYNAMIC LLM
    # -----------------------------
    llm = get_llm(api_key)

    # -----------------------------
    # PROMPT
    # -----------------------------
    prompt = ChatPromptTemplate.from_template("""
You are an AI assistant for uploaded PDF documents.

Your task:
Generate 6 useful, natural, grounded questions
that a user would likely ask after uploading this PDF.

STRICT RULES:
1. Questions must be based ONLY on the PDF content
2. Do NOT hallucinate
3. Do NOT use outside knowledge
4. Questions must help users explore the PDF meaningfully
5. Avoid vague or generic questions
6. Make questions practical and relevant
7. Return ONLY valid JSON

Return format:

{{
  "suggested_questions": [
    "Question 1",
    "Question 2",
    "Question 3",
    "Question 4",
    "Question 5",
    "Question 6"
  ]
}}

Document Text:
{document_text}
""")

    # -----------------------------
    # CHAIN
    # -----------------------------
    chain = prompt | llm

    response = chain.invoke({
        "document_text": input_text
    })

    raw_output = response.content.strip()

    cleaned_output = clean_json_response(
        raw_output
    )

    # -----------------------------
    # PARSE RESPONSE
    # -----------------------------
    try:

        parsed = json.loads(cleaned_output)

        questions = parsed.get(
            "suggested_questions",
            []
        )

        # -----------------------------
        # SAFETY CLEANUP
        # -----------------------------
        cleaned_questions = []

        for q in questions:

            if (
                isinstance(q, str)
                and len(q.strip()) > 5
            ):

                cleaned_questions.append(
                    q.strip()
                )

        return {
            "status": "success",
            "active_document": active_filename,
            "suggested_questions": cleaned_questions,
            "message": (
                "Suggested questions generated successfully."
            )
        }

    # -----------------------------
    # FALLBACK
    # -----------------------------
    except Exception:

        return {
            "status": "error",
            "active_document": active_filename,
            "suggested_questions": [],
            "message": (
                "Failed to parse suggested questions output."
            )
        }