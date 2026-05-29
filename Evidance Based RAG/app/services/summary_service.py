from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from app.services.document_registry_service import get_active_document
from app.services.summary_storage_service import load_summary_source
import json
import re


def get_summary_config(total_pages: int, total_text_length: int):
    """
    Dynamically decides summary length and topic count
    based on PDF size and content.
    """

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
    """
    Rough fallback estimate if actual page count isn't stored separately.
    """
    approx_chars_per_page = 2500
    return max(1, len(document_text) // approx_chars_per_page)


def clean_json_response(raw_text: str):
    """
    Removes markdown code fences and cleans raw LLM JSON output.
    """
    raw_text = raw_text.strip()

    raw_text = re.sub(r"^```json", "", raw_text, flags=re.IGNORECASE).strip()
    raw_text = re.sub(r"^```", "", raw_text).strip()
    raw_text = re.sub(r"```$", "", raw_text).strip()

    return raw_text


def generate_pdf_summary():
    """
    Generates summary + key topics from the active uploaded PDF.
    """
    active_doc = get_active_document()

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

    document_text = load_summary_source(active_doc_id)

    if not document_text or len(document_text.strip()) < 100:
        return {
            "status": "error",
            "active_document": active_filename,
            "summary": "",
            "key_topics": [],
            "message": "Not enough text found to summarize."
        }

    total_text_length = len(document_text)
    estimated_pages = estimate_page_count(document_text)
    summary_config = get_summary_config(estimated_pages, total_text_length)

    # Limit input to keep token usage safe
    summary_input = document_text[:20000]

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    prompt = ChatPromptTemplate.from_template("""
You are an AI assistant that summarizes uploaded PDF documents.

The uploaded PDF has:
- Approximate Pages: {estimated_pages}
- Total Extracted Text Length: {total_text_length} characters

Your task:
1. Generate a {summary_style}
2. The summary should be around {summary_length}
3. Extract {topic_count} important key topics from the document
4. Keep the summary useful, grounded, and non-generic
5. Do NOT make up information that is not supported by the document

Return output ONLY in this JSON format:

{{
  "summary": "...",
  "key_topics": ["topic1", "topic2", "topic3"]
}}

Document Text:
{document_text}
""")

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

    try:
        parsed = json.loads(cleaned_output)
        return {
            "status": "success",
            "active_document": active_filename,
            "summary": parsed.get("summary", ""),
            "key_topics": parsed.get("key_topics", []),
            "message": "PDF summary generated successfully."
        }

    except Exception:
        return {
            "status": "success",
            "active_document": active_filename,
            "summary": raw_output,
            "key_topics": [],
            "message": "PDF summary generated successfully (fallback mode)."
        }