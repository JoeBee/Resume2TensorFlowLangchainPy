# LinkedIn Post Summary – Resume Codebase

## Bullet Summary (for your post)

- **Interactive resume** – Single-page resume with modern dark theme, tech pill chips, and responsive layout
- **AI-powered Q&A** – Visitors can ask questions about your experience; answers use RAG (Retrieval-Augmented Generation) over your full resume
- **RAG stack** – TensorFlow Universal Sentence Encoder for embeddings, Chroma vector store, LangChain orchestration, Google Gemini LLM
- **FastAPI backend** – REST API serving resume data, static assets, and the Q&A endpoint
- **Cloud Run deployment** – Dockerized, deployed on Google Cloud Run; supports configurable memory for TensorFlow

---

## What's Different From My Previous Resume

*My earlier resume site was static—HTML/JS served from Firebase Hosting. This version adds an AI Q&A layer: visitors can ask natural-language questions (e.g., "What government projects has he worked on?") and get answers grounded in my full resume via RAG. It's a practical demo of TensorFlow embeddings + LangChain + LLMs that I built and use in production.*

---

## Short Version (if you need fewer characters)

- Interactive resume with AI Q&A (RAG: TensorFlow + LangChain + Gemini)
- FastAPI backend, Cloud Run deployment
- **New:** Replaced static resume with RAG-powered Q&A so visitors can ask questions and get answers from my full resume
