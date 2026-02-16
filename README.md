# Resume2TensorFlowLangchainPy

Resume site with RAG Q&A (LangChain + TensorFlow). This project serves your **abbreviated resume** on a single page and lets visitors **ask questions** that are answered using your **full resume** as augmented data, plus an LLM (Google Gemini).

- **Display:** Abbreviated resume from `data/resume-abbrev.json`.
- **Q&A:** Full resume in `data/resume-full.json` is embedded with **TensorFlow** (Universal Sentence Encoder), stored in **Chroma**, and used by **LangChain** for retrieval and answer generation (RAG).

## Setup

1. **Python 3.10+** and a terminal in the project folder.

2. **Create a virtual environment (recommended):**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Gemini (required for Q&A):**
   - Copy `.env.example` to `.env`.
   - Add your Gemini API key: `GOOGLE_API_KEY=...` (get one at [Google AI Studio](https://ai.google.dev/gemini-api/docs/api-key)).
   - Without this, the site still loads the resume, but "Ask a question" will return an error.

## Run

```bash
uvicorn main:app --reload
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000). You’ll see the abbreviated resume and an “Ask a question” section. The first question may take a bit longer (TensorFlow model and Chroma index are built once).

## Project layout

- `data/resume-full.json` – Full resume (RAG source).
- `data/resume-abbrev.json` – Abbreviated resume (displayed on the page).
- `data/chroma_db/` – Vector store (created on first Q&A).
- `rag.py` – TensorFlow embeddings + LangChain RAG chain.
- `main.py` – FastAPI app: `/`, `/api/resume`, `/api/ask`, `/api/health`.
- `static/index.html` – Resume UI and Q&A widget.

## Tech stack

- **TensorFlow** (TensorFlow Hub Universal Sentence Encoder) for embeddings.
- **LangChain** (retriever, prompt, LLM chain) for RAG.
- **Chroma** for the vector store.
- **FastAPI** for the API and static file serving.
