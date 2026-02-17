# Resume + RAG app (FastAPI, TensorFlow, LangChain). Cloud Run: use 1-2Gi memory.
FROM python:3.11-slim

WORKDIR /app

# Install system deps if needed (TensorFlow may need minimal libs)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py rag.py ./
COPY data/ data/
COPY static/ static/
COPY images/ images/

# Cloud Run sets PORT (default 8080). Listen on all interfaces.
ENV PORT=8080
EXPOSE 8080
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT}
