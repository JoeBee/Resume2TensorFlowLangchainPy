"""
Resume website: serves abbreviated resume and RAG-based Q&A using full resume + LangChain + TensorFlow.
"""
import json
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from dotenv import load_dotenv

# Load .env from project root so it's found regardless of working directory
_project_root = Path(__file__).resolve().parent
load_dotenv(_project_root / ".env")

from rag import answer_question

app = FastAPI(title="Resume & Q&A", description="Resume display with AI Q&A over full resume data.")

DATA_DIR = Path(__file__).resolve().parent / "data"
STATIC_DIR = Path(__file__).resolve().parent / "static"
IMAGES_DIR = Path(__file__).resolve().parent / "images"
ABBREV_RESUME_PATH = DATA_DIR / "resume-abbrev.json"


class AskRequest(BaseModel):
    question: str


@app.get("/api/resume")
def get_resume():
    """Return the abbreviated resume (what the user sees on the page)."""
    if not ABBREV_RESUME_PATH.exists():
        raise HTTPException(status_code=500, detail="Resume data not found.")
    with open(ABBREV_RESUME_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@app.post("/api/ask")
def ask(req: AskRequest):
    """Answer a question using augmented full resume data (RAG: TensorFlow embeddings + LangChain + LLM)."""
    if not req.question or not req.question.strip():
        raise HTTPException(status_code=400, detail="Question is required.")
    try:
        answer = answer_question(req.question)
        return {"answer": answer}
    except ValueError as e:
        if "GOOGLE_API_KEY" in str(e) or "GEMINI_API_KEY" in str(e):
            raise HTTPException(status_code=503, detail="Q&A is not configured (missing GOOGLE_API_KEY or GEMINI_API_KEY). Add it to .env and restart.")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        err = str(e)
        if "429" in err or "RESOURCE_EXHAUSTED" in err or "quota" in err.lower():
            raise HTTPException(
                status_code=429,
                detail="Gemini API quota exceeded. Please try again in a few minutes, or check your usage at https://ai.google.dev/gemini-api/docs/rate-limits",
            )
        raise HTTPException(status_code=500, detail=f"Error answering question: {err}")


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/favicon.ico")
def favicon():
    """Serve favicon to avoid 404 when the browser requests it by default."""
    favicon_path = STATIC_DIR / "favicon.svg"
    if favicon_path.exists():
        return FileResponse(favicon_path, media_type="image/svg+xml")
    raise HTTPException(status_code=404)


# Serve static files (HTML, CSS, JS)
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Serve images
if IMAGES_DIR.exists():
    app.mount("/images", StaticFiles(directory=str(IMAGES_DIR)), name="images")


@app.get("/")
def index():
    """Serve the main resume page."""
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    raise HTTPException(status_code=404, detail="Frontend not found. Create static/index.html.")
