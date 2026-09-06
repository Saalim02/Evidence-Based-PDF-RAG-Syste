from langchain_core.prompts import ChatPromptTemplate

from app.services.document_registry_service import get_active_document
from app.services.summary_storage_service import load_summary_source
from app.services.llm_service import get_llm

import json
import re


def get_summary_config(total_pages: int, total_text_length: int):

    if total_pages <= 5 or total_text_length < 5000:
        return {
            "summary_style": "detailed short-document summary",
            "summary_length": "5 to 7 lines",
            "topic_count": "4 to 6"
        }

    elif total_pages <= 30 or total_text_length < 30000:
        return {
            "summary_style": "balanced medium-document summary",
            "summary_length": "8 to 12 lines",
            "topic_count": "6 to 8"
        }

    elif total_pages <= 150 or total_text_length < 120000:
        return {
            "summary_style": "compressed but informative large-document summary",
            "summary_length": "10 to 15 lines",
            "topic_count": "8 to 10"
        }

    else:
        return {
            "summary_style": "high-level executive summary for a very large document",
            "summary_length": "8 to 12 concise lines",
            "topic_count": "8 to 12"
        }


def estimate_page_count(document_text: str):

    approx_chars_per_page = 2500

    return max(1, len(document_text) // approx_chars_per_page)


def clean_json_response(raw_text: str):

    raw_text = raw_text.strip()

    raw_text = re.sub(
        r"^```json",
        "",
        raw_text,
        flags=re.IGNORECASE
    ).strip()

    raw_text = re.sub(r"^```", "", raw_text).strip()

    raw_text = re.sub(r"```$", "", raw_text).strip()

    return raw_text


def generate_pdf_summary(api_key: str, user_id: int | None = None):

    """
    Generates summary + key topics
    from the active uploaded PDF.
    """

    # -----------------------------------
    # ACTIVE DOCUMENT CHECK
    # -----------------------------------
    active_doc = get_active_document(user_id)

    if not active_doc:

        return {
            "status": "error",
            "active_document": None,
            "summary": "",
            "key_topics": [],
            "message": "No active PDF uploaded."
        }

    active_filename = active_doc["active_filename"]
    active_doc_id = active_doc["active_doc_id"]

    # -----------------------------------
    # LOAD SUMMARY SOURCE
    # -----------------------------------
    document_text = load_summary_source(active_doc_id, user_id)

    if not document_text or len(document_text.strip()) < 100:

        return {
            "status": "error",
            "active_document": active_filename,
            "summary": "",
            "key_topics": [],
            "message": "Not enough text found to summarize."
        }

    # -----------------------------------
    # DYNAMIC SUMMARY CONFIG
    # -----------------------------------
    total_text_length = len(document_text)

    estimated_pages = estimate_page_count(document_text)

    summary_config = get_summary_config(
        estimated_pages,
        total_text_length
    )

    # -----------------------------------
    # TOKEN SAFETY LIMIT
    # -----------------------------------
    summary_input = document_text[:20000]

    # -----------------------------------
    # DYNAMIC LLM
    # -----------------------------------
    llm = get_llm(api_key)

    # -----------------------------------
    # PROMPT
    # -----------------------------------
    prompt = ChatPromptTemplate.from_template("""
You are an AI assistant that summarizes uploaded PDF documents.

STRICT RULES:
- Use ONLY the provided document text
- Do NOT hallucinate
- Do NOT add outside knowledge
- Keep the summary grounded
- Keep the summary useful and structured

The uploaded PDF has:
- Approximate Pages: {estimated_pages}
- Total Extracted Text Length: {total_text_length} characters

Your tasks:
1. Generate a {summary_style}
2. The summary should be around {summary_length}
3. Extract {topic_count} important key topics
4. Keep the summary concise but informative

Return ONLY valid JSON in this format:

{{
  "summary": "...",
  "key_topics": ["topic1", "topic2", "topic3"]
}}

Document Text:
{document_text}
""")

    # -----------------------------------
    # CHAIN
    # -----------------------------------
    chain = prompt | llm

    response = chain.invoke({
        "document_text": summary_input,
        "estimated_pages": estimated_pages,
        "total_text_length": total_text_length,
        "summary_style": summary_config["summary_style"],
        "summary_length": summary_config["summary_length"],
        "topic_count": summary_config["topic_count"]
    })

    raw_output = response.content.strip()

    cleaned_output = clean_json_response(raw_output)

    # -----------------------------------
    # JSON PARSE
    # -----------------------------------
    try:

        parsed = json.loads(cleaned_output)

        return {
            "status": "success",
            "active_document": active_filename,
            "summary": parsed.get("summary", ""),
            "key_topics": parsed.get("key_topics", []),
            "message": "PDF summary generated successfully."
        }

    # -----------------------------------
    # FALLBACK MODE
    # -----------------------------------
    except Exception:

        return {
            "status": "success",
            "active_document": active_filename,
            "summary": raw_output,
            "key_topics": [],
            "message": "PDF summary generated successfully (fallback mode)."
        }