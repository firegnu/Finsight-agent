#!/bin/sh
# First-run initializer for the containerized app.
#
# Data bootstrap strategy:
#   - data/ is mounted as a volume (persistent across container restarts)
#   - On first start the volume is empty → seed the SQLite DB and build the
#     Chroma RAG index
#   - On subsequent starts the volume already has state → skip both steps
#
# Required env vars for first-run RAG indexing:
#   - LLM_EMBEDDING_BASE_URL, LLM_EMBEDDING_API_KEY, LLM_EMBEDDING_MODEL
# If these are missing the container will fail fast with a clear message.

set -e

DB_PATH="${DB_PATH:-./data/finsight.db}"
CHROMA_DB_PATH="${CHROMA_DB_PATH:-./data/chroma}"

mkdir -p "$(dirname "$DB_PATH")" "$CHROMA_DB_PATH"

if [ ! -f "$DB_PATH" ]; then
    echo "[entrypoint] $DB_PATH missing — seeding mock data"
    python scripts/seed_data.py --db-path "$DB_PATH"
else
    echo "[entrypoint] $DB_PATH exists — skip seed"
fi

# Chroma is considered initialized when its metadata sqlite exists AND has
# at least one segment. An empty dir (just-created by mkdir above) fails
# this check, which is what we want.
if [ ! -f "$CHROMA_DB_PATH/chroma.sqlite3" ]; then
    if [ -z "$LLM_EMBEDDING_API_KEY" ]; then
        echo "[entrypoint] ERROR: LLM_EMBEDDING_API_KEY is required for first-run index build" >&2
        exit 1
    fi
    echo "[entrypoint] building RAG index (first run)"
    python scripts/index_cases.py
else
    echo "[entrypoint] Chroma index present — skip index build"
fi

echo "[entrypoint] launching: $*"
exec "$@"
