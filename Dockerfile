FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project source
COPY . .

# Build the ChromaDB vector store from knowledge base files
# (Requires WATSONX_APIKEY, WATSONX_URL, WATSONX_PROJECT_ID to be set as build args or env vars)
# Comment this out if you are committing db/ to the repo via Git LFS
RUN python src/ingest.py || echo "Ingest skipped (credentials not available at build time)"

# HF Spaces uses port 7860; Render/Railway use $PORT
EXPOSE 7860

CMD ["sh", "-c", "gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --timeout 120"]
