"""
RAG pipeline: TensorFlow Universal Sentence Encoder for embeddings,
LangChain for retrieval + LLM-based answering. Uses full resume as augmented data.
"""
import json
import os
from pathlib import Path

from langchain_core.embeddings import Embeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_chroma import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document


DATA_DIR = Path(__file__).resolve().parent / "data"
FULL_RESUME_PATH = DATA_DIR / "resume-full.json"
RAG_FAQ_PATH = DATA_DIR / "rag-faq.json"


def _faq_to_chunks(data: dict) -> list[Document]:
    """Convert FAQ Q&A JSON into RAG document chunks. Each chunk is 'Question: ... Answer: ...'."""
    chunks = []
    for item in data.get("qa", []):
        q = item.get("question", "").strip()
        a = item.get("answer", "").strip()
        if q and a:
            chunks.append(Document(
                page_content=f"Question: {q}\nAnswer: {a}",
                metadata={"section": "faq"}
            ))
    return chunks


def _resume_to_chunks(data: dict) -> list[Document]:
    """Flatten full resume JSON into text chunks for RAG."""
    chunks = []
    # Profile
    p = data.get("profile", {})
    if p:
        chunks.append(Document(
            page_content=f"Profile: {p.get('name', '')}. Address: {p.get('address', '')}. Email: {p.get('email', '')}. Phone: {p.get('phone', '')}. LinkedIn: {p.get('linkedin', '')}.",
            metadata={"section": "profile"}
        ))
    # Summary
    s = data.get("summary", {})
    for key in ("technical_skills_experience", "key_strengths", "hobbies"):
        if key in s and s[key]:
            items = s[key] if isinstance(s[key], list) else [s[key]]
            chunks.append(Document(page_content=f"Summary {key}: " + " ".join(items), metadata={"section": "summary"}))
    if s.get("next_great_challenge"):
        chunks.append(Document(page_content="Next great challenge: " + s["next_great_challenge"], metadata={"section": "summary"}))
    # Technical summary
    ts = data.get("technical_summary", {})
    for category, items in ts.items():
        if items:
            text = " ".join(items) if isinstance(items, list) else str(items)
            chunks.append(Document(page_content=f"Technical {category}: {text}", metadata={"section": "technical"}))
    # Education
    for ed in data.get("education", []):
        chunks.append(Document(
            page_content=f"Education: {ed.get('degree', '')} at {ed.get('school', '')}, {ed.get('date', '')}. {ed.get('gpa', '') or ed.get('notes', '')}.",
            metadata={"section": "education"}
        ))
    # Professional experience
    for job in data.get("professional_experience", []):
        parts = [f"Company: {job.get('company', '')}. Role: {job.get('role', job.get('title', ''))}. Date: {job.get('date', '')}."]
        if job.get("tech"):
            parts.append("Tech: " + ", ".join(job["tech"]))
        if job.get("tasks"):
            parts.append("Tasks: " + " ".join(job["tasks"]))
        if job.get("projects"):
            for proj in job["projects"]:
                parts.append(f"Project {proj.get('name', '')}: {proj.get('description', '')}")
        chunks.append(Document(page_content=" ".join(parts), metadata={"section": "experience", "company": job.get("company", "")}))
    # Training
    training = data.get("additional_training_education", [])
    if training:
        chunks.append(Document(page_content="Additional training: " + "; ".join(training), metadata={"section": "training"}))
    return chunks


def get_rag_chain():
    """Build and return the RAG chain. Uses GOOGLE_API_KEY or GEMINI_API_KEY from env."""
    # Lazy import so the app starts without loading TensorFlow (avoids pkg_resources at startup)
    import tensorflow_hub as hub

    class TensorFlowHubEmbeddings(Embeddings):
        """LangChain Embeddings using TensorFlow Hub Universal Sentence Encoder."""

        def __init__(self, model_url: str = "https://tfhub.dev/google/universal-sentence-encoder/4"):
            self._model = hub.load(model_url)

        def embed_documents(self, texts: list[str]) -> list[list[float]]:
            embeddings = self._model(texts).numpy()
            return embeddings.tolist()

        def embed_query(self, text: str) -> list[float]:
            embedding = self._model([text]).numpy()[0]
            return embedding.tolist()

    with open(FULL_RESUME_PATH, "r", encoding="utf-8") as f:
        full_resume = json.load(f)
    chunks = _resume_to_chunks(full_resume)
    if not chunks:
        raise ValueError("No resume chunks loaded.")

    if RAG_FAQ_PATH.exists():
        with open(RAG_FAQ_PATH, "r", encoding="utf-8") as f:
            faq_data = json.load(f)
        faq_chunks = _faq_to_chunks(faq_data)
        chunks = chunks + faq_chunks

    embeddings = TensorFlowHubEmbeddings()
    # Use fresh path to avoid "default_tenant" errors from old ChromaDB 1.x data
    import chromadb
    chroma_path = str(DATA_DIR / "chroma_db_v2")
    client = chromadb.PersistentClient(path=chroma_path)
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name="resume_rag",
        client=client,
    )
    retriever = vectorstore.as_retriever(search_k=4)

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a helpful assistant answering questions about Joseph Beyer's resume and career.
Use ONLY the following retrieved context (from his full resume and/or FAQ Q&A) to answer.
When the context includes a "Question: ... Answer: ..." block that matches the user's question, prefer that answer.
If the context does not contain enough information, say so briefly and answer from common sense where reasonable.
Keep answers concise and professional. If the question is off-topic or inappropriate, politely redirect to resume-related topics."""),
        ("human", "Context from resume and FAQ:\n{context}\n\nQuestion: {question}")
    ])

    api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    # Use gemini-2.5-flash (gemini-1.5-flash is deprecated / 404)
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.2, api_key=api_key)
    if not api_key:
        raise ValueError("GOOGLE_API_KEY or GEMINI_API_KEY environment variable is not set. Add it to .env or your environment.")

    def format_docs(docs):
        return "\n\n".join(d.page_content for d in docs)

    chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    return chain


_chain = None


def answer_question(question: str) -> str:
    """Answer a question using the RAG chain (full resume + LLM)."""
    global _chain
    if _chain is None:
        _chain = get_rag_chain()
    return _chain.invoke(question.strip())
