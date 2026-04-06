import streamlit as st
import requests

# ---------------------------
# CONFIG
# ---------------------------
FASTAPI_BASE_URL = "http://127.0.0.1:8000/api"

st.set_page_config(page_title="Evidence-Based PDF RAG", layout="wide")

# ---------------------------
# SESSION STATE INIT
# ---------------------------
if "upload_result" not in st.session_state:
    st.session_state.upload_result = None

if "summary_result" not in st.session_state:
    st.session_state.summary_result = None

if "suggested_questions_result" not in st.session_state:
    st.session_state.suggested_questions_result = None

if "ask_result" not in st.session_state:
    st.session_state.ask_result = None

# ---------------------------
# API HELPERS
# ---------------------------
def upload_pdf_to_backend(uploaded_file):
    files = {"file": (uploaded_file.name, uploaded_file, "application/pdf")}
    response = requests.post(f"{FASTAPI_BASE_URL}/upload-pdf", files=files)
    return response


def get_pdf_summary():
    response = requests.get(f"{FASTAPI_BASE_URL}/summary")
    return response


def get_suggested_questions():
    response = requests.get(f"{FASTAPI_BASE_URL}/suggested-questions")
    return response


def ask_question_backend(question):
    payload = {"question": question}
    response = requests.post(f"{FASTAPI_BASE_URL}/ask", json=payload)
    return response


# ---------------------------
# MAIN TITLE
# ---------------------------
st.title("📄 Evidence-Based PDF RAG System")
st.markdown("Ask grounded questions from your uploaded PDF and view supporting page evidence.")

# ---------------------------
# SIDEBAR - PDF UPLOAD
# ---------------------------
st.sidebar.header("📤 Upload PDF")

uploaded_file = st.sidebar.file_uploader("Upload a PDF", type=["pdf"])

if uploaded_file is not None:
    if st.sidebar.button("Upload PDF"):
        with st.spinner("Uploading and processing PDF..."):
            response = upload_pdf_to_backend(uploaded_file)

            if response.status_code == 200:
                result = response.json()
                st.session_state.upload_result = result
                st.session_state.ask_result = None  # reset old answer

                st.sidebar.success("PDF uploaded successfully!")

                # Auto-fetch summary after upload
                summary_response = get_pdf_summary()
                if summary_response.status_code == 200:
                    st.session_state.summary_result = summary_response.json()
                else:
                    st.session_state.summary_result = {
                        "status": "error",
                        "summary": "",
                        "key_topics": [],
                        "message": "Failed to fetch summary."
                    }

                # Auto-fetch suggested questions after upload
                suggested_questions_response = get_suggested_questions()
                if suggested_questions_response.status_code == 200:
                    st.session_state.suggested_questions_result = suggested_questions_response.json()
                else:
                    st.session_state.suggested_questions_result = {
                        "status": "error",
                        "suggested_questions": [],
                        "message": "Failed to fetch suggested questions."
                    }

            else:
                st.session_state.upload_result = None
                st.session_state.summary_result = None
                st.session_state.suggested_questions_result = None
                st.session_state.ask_result = None

                st.sidebar.error("Upload failed.")
                st.sidebar.text(response.text)

# ---------------------------
# SIDEBAR - UPLOAD INFO
# ---------------------------
if st.session_state.upload_result:
    upload_result = st.session_state.upload_result

    st.sidebar.markdown("---")
    st.sidebar.subheader("📄 Uploaded PDF Info")
    st.sidebar.write(f"**Filename:** {upload_result.get('filename', 'N/A')}")
    st.sidebar.write(f"**Pages:** {upload_result.get('total_pages', 'N/A')}")
    st.sidebar.write(f"**Chunks:** {upload_result.get('num_chunks', 'N/A')}")
    st.sidebar.write(f"**Chunk Size:** {upload_result.get('selected_chunk_size', 'N/A')}")
    st.sidebar.write(f"**Chunk Overlap:** {upload_result.get('selected_chunk_overlap', 'N/A')}")

# ---------------------------
# MAIN - SUMMARY SECTION
# ---------------------------
if st.session_state.summary_result:
    summary_result = st.session_state.summary_result

    col1, col2 = st.columns([5, 1])

    with col1:
        st.subheader("📄 Document Summary")

    with col2:
        if st.button("🔄 Refresh Summary"):
            summary_response = get_pdf_summary()
            if summary_response.status_code == 200:
                st.session_state.summary_result = summary_response.json()
                summary_result = st.session_state.summary_result

    if summary_result.get("status") == "success":
        st.info(summary_result.get("summary", "No summary available."))

        key_topics = summary_result.get("key_topics", [])
        if key_topics:
            st.subheader("🧠 Key Topics")
            for topic in key_topics:
                st.markdown(f"- {topic}")

    else:
        st.warning(summary_result.get("message", "Summary not available."))

# ---------------------------
# MAIN - SUGGESTED QUESTIONS
# ---------------------------
if st.session_state.suggested_questions_result:
    suggested_result = st.session_state.suggested_questions_result

    if suggested_result.get("status") == "success":
        st.subheader("💡 Suggested Questions")

        for q in suggested_result.get("suggested_questions", []):
            st.markdown(f"- {q}")

    else:
        st.warning(suggested_result.get("message", "Suggested questions not available."))

# ---------------------------
# MAIN - QUESTION INPUT
# ---------------------------
st.subheader("❓ Ask a Question")

question = st.text_input("Enter your question about the uploaded PDF")

ask_disabled = st.session_state.upload_result is None

if st.button("Ask", disabled=ask_disabled):
    if not question.strip():
        st.warning("Please enter a question.")
    else:
        with st.spinner("Generating answer..."):
            response = ask_question_backend(question)

            if response.status_code == 200:
                st.session_state.ask_result = response.json()
            else:
                st.session_state.ask_result = None
                st.error("Failed to get answer.")
                st.text(response.text)

if ask_disabled:
    st.info("Upload a PDF first to ask questions.")

# ---------------------------
# MAIN - ANSWER DISPLAY
# ---------------------------
if st.session_state.ask_result:
    result = st.session_state.ask_result

    # ---------------------------
    # MAIN ANSWER
    # ---------------------------
    st.subheader("🧠 Answer")
    if result.get("answer"):
        st.success(result["answer"])
    else:
        st.error(result.get("message", "No answer found."))

    # ---------------------------
    # CONFIDENCE
    # ---------------------------
    st.subheader("📊 Confidence")
    st.write(f"**Confidence:** {result.get('confidence', 'N/A')}")
    st.write(f"**Best Score:** {result.get('best_score', 'N/A')}")
    st.write(f"**Average Score:** {result.get('average_score', 'N/A')}")

    # ---------------------------
    # EVIDENCE
    # ---------------------------
    st.subheader("📌 Supporting Evidence")

    evidence_list = result.get("evidence", [])

    if evidence_list:
        for i, evidence in enumerate(evidence_list, start=1):
            with st.expander(f"Evidence {i} — Page {evidence['page_number']}"):
                st.code(evidence["snippet"], language="text")

                image_url = evidence.get("image_path")
                if image_url:
                    st.image(
                        image_url,
                        caption=f"Page {evidence['page_number']} Preview",
                        use_container_width=True
                    )
    else:
        st.info("No evidence available.")