from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from app.services.document_registry_service import get_active_document
from app.services.summary_storage_service import load_summary_source
import json
import re


def clean_json_response(raw_text: str):
    raw_text = raw_text.strip()
    raw_text = re.sub(r"^```json", "", raw_text, flags=re.IGNORECASE).strip()
    raw_text = re.sub(r"^```", "", raw_text).strip()
    raw_text = re.sub(r"```$", "", raw_text).strip()
    return raw_text


def generate_suggested_questions():
    """
    Generates useful suggested questions based on the uploaded PDF.
    """
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

    document_text = load_summary_source(active_doc_id)

    if not document_text or len(document_text.strip()) < 100:
        return {
            "status": "error",
            "active_document": active_filename,
            "suggested_questions": [],
            "message": "Not enough text found to generate suggested questions."
        }

    input_text = document_text[:12000]

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    prompt = ChatPromptTemplate.from_template("""
You are an AI assistant for uploaded PDF documents.

Your task:
Generate 6 useful, natural, grounded questions that a user would likely ask
after uploading this PDF.

Rules:
1. Questions must be based ONLY on the PDF content
2. Questions must be useful for understanding, exploring, or analyzing the PDF
3. Avoid generic boring questions like "Can you summarize this?"
4. Make the questions sound natural and relevant
5. Return ONLY valid JSON in this format:

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

    chain = prompt | llm

    response = chain.invoke({
        "document_text": input_text
    })

    raw_output = response.content.strip()
    cleaned_output = clean_json_response(raw_output)

    try:
        parsed = json.loads(cleaned_output)
        return {
            "status": "success",
            "active_document": active_filename,
            "suggested_questions": parsed.get("suggested_questions", []),
            "message": "Suggested questions generated successfully."
        }

    except Exception:
        return {
            "status": "error",
            "active_document": active_filename,
            "suggested_questions": [],
            "message": "Failed to parse suggested questions output."
        }