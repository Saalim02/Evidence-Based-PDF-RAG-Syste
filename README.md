# 📄 Evidence-Based PDF RAG System

An end-to-end **production-minded Retrieval-Augmented Generation (RAG) system** that allows users to upload PDFs and get **grounded, explainable, and evidence-backed answers** with page-level references and visual previews.

---

## 🚀 Project Overview

This project is designed to simulate a **real-world AI/ML system** rather than a basic chatbot.

It focuses on:

* **Grounded Answer Generation**
* **Semantic Retrieval with Similarity Scoring**
* **Explainability (Evidence + Page Preview)**
* **Hallucination Control**
* **Dynamic Intelligence Features**

---

## 🧠 Key Features

### 📤 PDF Upload & Processing

* Upload PDFs up to **70 MB**
* Supports documents up to **~1200 pages**
* Page-wise text extraction
* Scanned PDF detection:

  > `"This PDF appears to be scanned or image-based..."`

---

### 🔍 Hybrid Retrieval (Semantic + Similarity)

* Uses **Hugging Face embeddings**
* **FAISS vector store**
* Dynamic:

  * chunk size
  * overlap
  * top-k retrieval
* Active-document-safe retrieval:

  * Only latest uploaded PDF is used

---

### ✂️ Smart Chunking System

* Page-level + chunk-level storage
* ~500 character chunks with overlap
* Metadata preserved:

  * page number
  * chunk id
  * document id

---

### 🧠 Grounded Answer Generation

* Built with:

  * LangChain
  * OpenAI (user-provided API key)
* Strict grounding rules:

  * Only uses retrieved chunks
  * No external knowledge

---

### ❌ Hallucination Control

If answer is not supported:

> **"Answer not found in uploaded PDF."**

---

### 📊 Confidence & Scoring

Each response includes:

* Confidence level (high / low)
* Best similarity score
* Average similarity score

---

### 📌 Evidence-Based Responses

Every answer returns:

* Supporting text snippets
* Exact page numbers
* Multiple supporting sources

---

### 🖼️ Page Preview (Multimodal Support)

* Every PDF page is converted to an image
* Response includes:

  * Direct page preview link
* Works for:

  * text
  * tables
  * diagrams
  * charts

---

### 📘 Dynamic PDF Summary

* Auto-generated after upload
* Adaptive based on PDF size:

  * Small PDF → detailed summary
  * Large PDF → compressed summary
* Also extracts:

  * Key topics

---

### 💡 Suggested Questions (AI-Generated)

* Context-aware question suggestions
* Generated from document content
* Helps users explore the document faster

---

### 🧠 Question Type Detection (Advanced Feature)

System automatically detects intent:

* definition
* explanation
* summary
* comparison
* how-to
* fact lookup

Then adapts answer style accordingly.

---

### 🎯 Clean UI (Streamlit)

* Upload PDF
* View summary + key topics
* Suggested questions
* Ask questions
* See:

  * Answer
  * Confidence
  * Evidence
  * Page preview images

---

## 🏗️ Tech Stack

### Backend

* FastAPI
* LangChain
* Hugging Face Transformers
* FAISS

### LLM

* OpenAI (user-provided API key)

### Frontend

* Streamlit

### Storage

* Local file system
* FAISS vector index

---

## 📂 Project Structure

```
project root/
├── app/
│   ├── api/routes/
│   ├── services/
│   ├── models/
│   ├── utils/
│   └── main.py
├── uploads/
├── vectorstore/
├── debug_output/
├── page_images/
├── streamlit_app.py
├── requirements.txt
└── README.md
```

---

## ⚙️ Setup Instructions

### 1. Clone Repository

```bash
git clone <your-repo-link>
cd project-root
```

### 2. Create Environment

```bash
conda create -n rag_env python=3.10
conda activate rag_env
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Add OpenAI API Key

Create `.env` file:

```
OPENAI_API_KEY=your_api_key_here
```

---

### 5. Run Backend

```bash
uvicorn app.main:app --reload
```

---

### 6. Run Frontend

```bash
streamlit run streamlit_app.py
```

---

## 🔥 Example Workflow

1. Upload PDF

2. System:

   * extracts text
   * creates embeddings
   * builds vector store
   * generates summary
   * suggests questions

3. Ask a question:

   * retrieval happens
   * answer is generated
   * evidence + page preview shown

---

## ⚠️ Challenges Faced & Solutions

### 1. ❌ Hallucination Issues

**Problem:**
Model generated answers not present in PDF.

**Solution:**

* Strict grounding prompt
* Threshold-based filtering
* Hard fallback:

  > "Answer not found in uploaded PDF."

---

### 2. ❌ Irrelevant Retrieval

**Problem:**
Wrong chunks retrieved.

**Solution:**

* Semantic + similarity hybrid
* Dynamic top-k tuning
* Active document filtering

---

### 3. ❌ Poor Summary Generation

**Problem:**
Generic or broken summaries.

**Solution:**

* Dynamic summary length
* Context truncation
* JSON output cleaning

---

### 4. ❌ JSON Parsing Failures (LLM Output)

**Problem:**
Invalid JSON from model.

**Solution:**

* Regex cleaning
* Fallback handling

---

### 5. ❌ Page Preview Not Showing

**Problem:**
Only file path returned.

**Solution:**

* Static file mounting in FastAPI
* URL-based image serving

---

### 6. ❌ Weak UX (User Doesn’t Know What to Ask)

**Problem:**
Users stuck after upload.

**Solution:**

* Suggested Questions feature

---

### 7. ❌ One-Style Answers (Poor Quality)

**Problem:**
Same answer style for all questions.

**Solution:**

* Question Type Detection
* Adaptive prompting

---

## 📈 Future Improvements

* Clickable suggested questions
* Answer highlighting on page preview
* Better evidence ranking
* Multi-document support

---

## ⭐ If you like this project

❤️Give it a star⭐

