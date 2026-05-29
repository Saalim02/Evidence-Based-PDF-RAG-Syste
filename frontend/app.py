import streamlit as st
import requests
import os

# ---------------------------
# CONFIG
# ---------------------------
FASTAPI_BASE_URL = os.getenv(
    "FASTAPI_BASE_URL",
    "http://localhost:8000/api"
)

st.set_page_config(
    page_title="Evidence-Based PDF RAG",
    layout="wide"
)

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
# SIDEBAR - ACCESS CONTROL
# ---------------------------
st.sidebar.markdown("---")
st.sidebar.subheader("🔐 OpenAI Access")

access_password = st.sidebar.text_input(
    "Enter Access Password (optional)",
    type="password"
)

user_openai_api_key = st.sidebar.text_input(
    "Enter Your OpenAI API Key",
    type="password"
)

# ---------------------------
# NORMALIZE INPUTS
# ---------------------------
access_password = access_password.strip()
user_openai_api_key = user_openai_api_key.strip()

# ---------------------------
# ACCESS MODE DETECTION
# ---------------------------
using_backend_key = (
    access_password == "20022004"
)

using_user_key = (
    not using_backend_key
    and len(user_openai_api_key) > 20
)

# ---------------------------
# ACCESS STATUS UI
# ---------------------------
if using_backend_key:

    st.sidebar.success(
        "✅ Using backend OpenAI access"
    )

elif using_user_key:

    st.sidebar.success(
        "✅ Using your OpenAI API key"
    )

else:

    st.sidebar.warning(
        "⚠️ Enter valid password or OpenAI API key"
    )

# ---------------------------
# API HELPERS
# ---------------------------
def upload_pdf_to_backend(uploaded_file):

    files = {
        "file": (
            uploaded_file.name,
            uploaded_file,
            "application/pdf"
        )
    }

    data = {
        "access_password": access_password,
        "user_openai_api_key": user_openai_api_key
    }

    response = requests.post(
        f"{FASTAPI_BASE_URL}/upload-pdf",
        files=files,
        data=data
    )

    return response


def get_pdf_summary():

    payload = {
        "question": "summary",
        "access_password": access_password,
        "user_openai_api_key": user_openai_api_key
    }

    response = requests.post(
        f"{FASTAPI_BASE_URL}/summary",
        json=payload
    )

    return response


def get_suggested_questions():

    payload = {
        "question": "suggested questions",
        "access_password": access_password,
        "user_openai_api_key": user_openai_api_key
    }

    response = requests.post(
        f"{FASTAPI_BASE_URL}/suggested-questions",
        json=payload
    )

    return response


def ask_question_backend(question):

    payload = {
        "question": question,
        "access_password": access_password,
        "user_openai_api_key": user_openai_api_key
    }

    response = requests.post(
        f"{FASTAPI_BASE_URL}/ask",
        json=payload
    )

    return response


# ---------------------------
# MAIN TITLE
# ---------------------------
st.title("📄 Evidence-Based PDF RAG System")

st.markdown(
    "Ask grounded questions from your uploaded PDF and view supporting page evidence."
)

# ---------------------------
# SIDEBAR - PDF UPLOAD
# ---------------------------
st.sidebar.header("📤 Upload PDF")

uploaded_file = st.sidebar.file_uploader(
    "Upload a PDF",
    type=["pdf"]
)

if uploaded_file is not None:

    if st.sidebar.button("Upload PDF"):

        # ---------------------------
        # ACCESS VALIDATION
        # ---------------------------
        if (
            not using_backend_key
            and not using_user_key
        ):

            st.sidebar.error(
                "Enter correct access password or provide your own OpenAI API key."
            )

        else:

            with st.spinner(
                "Uploading and processing PDF..."
            ):

                response = upload_pdf_to_backend(
                    uploaded_file
                )

                if response.status_code == 200:

                    result = response.json()

                    st.session_state.upload_result = result

                    st.session_state.ask_result = None

                    st.sidebar.success(
                        "PDF uploaded successfully!"
                    )

                    # ---------------------------
                    # AUTO SUMMARY
                    # ---------------------------
                    summary_response = get_pdf_summary()

                    if summary_response.status_code == 200:

                        st.session_state.summary_result = (
                            summary_response.json()
                        )

                    else:

                        st.session_state.summary_result = {
                            "status": "error",
                            "summary": "",
                            "key_topics": [],
                            "message": "Failed to fetch summary."
                        }

                    # ---------------------------
                    # AUTO SUGGESTED QUESTIONS
                    # ---------------------------
                    suggested_questions_response = (
                        get_suggested_questions()
                    )

                    if (
                        suggested_questions_response.status_code
                        == 200
                    ):

                        st.session_state.suggested_questions_result = (
                            suggested_questions_response.json()
                        )

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

                    st.sidebar.error(
                        "Upload failed."
                    )

                    st.sidebar.text(
                        response.text
                    )

# ---------------------------
# SIDEBAR - UPLOAD INFO
# ---------------------------
if st.session_state.upload_result:

    upload_result = (
        st.session_state.upload_result
    )

    st.sidebar.markdown("---")

    st.sidebar.subheader(
        "📄 Uploaded PDF Info"
    )

    st.sidebar.write(
        f"**Filename:** {upload_result.get('filename', 'N/A')}"
    )

    st.sidebar.write(
        f"**Pages:** {upload_result.get('total_pages', 'N/A')}"
    )

    st.sidebar.write(
        f"**Chunks:** {upload_result.get('num_chunks', 'N/A')}"
    )

    st.sidebar.write(
        f"**Chunk Size:** {upload_result.get('selected_chunk_size', 'N/A')}"
    )

    st.sidebar.write(
        f"**Chunk Overlap:** {upload_result.get('selected_chunk_overlap', 'N/A')}"
    )

# ---------------------------
# MAIN - SUMMARY SECTION
# ---------------------------
if st.session_state.summary_result:

    summary_result = (
        st.session_state.summary_result
    )

    col1, col2 = st.columns([5, 1])

    with col1:

        st.subheader(
            "📄 Document Summary"
        )

    with col2:

        if st.button(
            "🔄 Refresh Summary"
        ):

            summary_response = (
                get_pdf_summary()
            )

            if summary_response.status_code == 200:

                st.session_state.summary_result = (
                    summary_response.json()
                )

                summary_result = (
                    st.session_state.summary_result
                )

    if summary_result.get("status") == "success":

        st.info(
            summary_result.get(
                "summary",
                "No summary available."
            )
        )

        key_topics = summary_result.get(
            "key_topics",
            []
        )

        if key_topics:

            st.subheader(
                "🧠 Key Topics"
            )

            for topic in key_topics:

                st.markdown(
                    f"- {topic}"
                )

    else:

        st.warning(
            summary_result.get(
                "message",
                "Summary not available."
            )
        )

# ---------------------------
# MAIN - SUGGESTED QUESTIONS
# ---------------------------
if st.session_state.suggested_questions_result:

    suggested_result = (
        st.session_state
        .suggested_questions_result
    )

    if suggested_result.get("status") == "success":

        st.subheader(
            "💡 Suggested Questions"
        )

        for q in suggested_result.get(
            "suggested_questions",
            []
        ):

            st.markdown(
                f"- {q}"
            )

    else:

        st.warning(
            suggested_result.get(
                "message",
                "Suggested questions not available."
            )
        )

# ---------------------------
# MAIN - QUESTION INPUT
# ---------------------------
st.subheader("❓ Ask a Question")

question = st.text_input(
    "Enter your question about the uploaded PDF"
)

ask_disabled = (
    st.session_state.upload_result
    is None
)

if st.button(
    "Ask",
    disabled=ask_disabled
):

    if not question.strip():

        st.warning(
            "Please enter a question."
        )

    else:

        if (
            not using_backend_key
            and not using_user_key
        ):

            st.error(
                "Enter correct access password or provide your own OpenAI API key."
            )

        else:

            with st.spinner(
                "Generating answer..."
            ):

                response = ask_question_backend(
                    question
                )

                if response.status_code == 200:

                    st.session_state.ask_result = (
                        response.json()
                    )

                else:

                    st.session_state.ask_result = None

                    st.error(
                        "Failed to get answer."
                    )

                    st.text(
                        response.text
                    )

if ask_disabled:

    st.info(
        "Upload a PDF first to ask questions."
    )

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

        st.success(
            result["answer"]
        )

    else:

        st.error(
            result.get(
                "message",
                "No answer found."
            )
        )

    # ---------------------------
    # QUESTION TYPE
    # ---------------------------
    if result.get("question_type"):

        st.subheader(
            "🧠 Question Type"
        )

        st.write(
            result.get(
                "question_type"
            )
        )

    # ---------------------------
    # CONFIDENCE
    # ---------------------------
    st.subheader("📊 Confidence")

    st.write(
        f"**Confidence:** {result.get('confidence', 'N/A')}"
    )

    st.write(
        f"**Best Score:** {result.get('best_score', 'N/A')}"
    )

    st.write(
        f"**Average Score:** {result.get('average_score', 'N/A')}"
    )

    # ---------------------------
    # EVIDENCE
    # ---------------------------
    st.subheader(
        "📌 Supporting Evidence"
    )

    evidence_list = result.get(
        "evidence",
        []
    )

    if evidence_list:

        for i, evidence in enumerate(
            evidence_list,
            start=1
        ):

            with st.expander(
                f"Evidence {i} — Page {evidence['page_number']}"
            ):

                st.code(
                    evidence["snippet"],
                    language="text"
                )

                image_url = evidence.get(
                    "image_path"
                )

                if image_url:

                    st.image(
                        image_url,
                        caption=(
                            f"Page "
                            f"{evidence['page_number']} "
                            f"Preview"
                        ),
                        use_container_width=True
                    )

    else:

        st.info(
            "No evidence available."
        )