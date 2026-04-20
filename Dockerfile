# =============================================================================
# Stage 1: build the Vite/React frontend into static assets
# =============================================================================
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

# Install deps first (cached layer) — copy only lockfile + package.json
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm ci --no-audit --no-fund || npm install --no-audit --no-fund

# Build
COPY frontend/ ./
RUN npm run build

# =============================================================================
# Stage 2: Python runtime that serves API + static frontend on a single port
# =============================================================================
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# No extra apt packages needed — chromadb + numpy ship manylinux wheels for
# python:3.11-slim, and the HEALTHCHECK uses python's urllib (below) to
# avoid a curl dependency.

# Install Python deps first (cached layer)
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install -r backend/requirements.txt

# Copy backend code + scripts + knowledge base (cases for RAG indexing)
COPY backend/ ./backend/
COPY scripts/ ./scripts/

# Copy the built frontend from stage 1 — backend/main.py auto-detects this
# path and registers the SPA catch-all route
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Entrypoint does first-run seed + RAG index build if data/ is empty
COPY scripts/docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/api/health',timeout=3).status==200 else 1)" || exit 1

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
