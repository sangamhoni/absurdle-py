"""
Web Absurdle — FastAPI backend.
Run from repo root: uvicorn app:app --reload
"""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

import absurdle

# Resolve word list path from env (default: short_list.txt) relative to repo root.
_REPO_ROOT = os.path.dirname(os.path.abspath(__file__))


def _word_list_path() -> str:
    raw = os.environ.get("WORD_LIST", "short_list.txt")
    if os.path.isabs(raw):
        return raw
    return os.path.join(_REPO_ROOT, raw)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load word list at startup; fail fast if missing or empty."""
    path = _word_list_path()
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Word list not found: {path}")
    words = absurdle.load_answer_set_words(path)
    if not words:
        raise ValueError(f"Word list is empty or has no 5-letter words: {path}")
    app.state.answer_set_words = words
    yield
    # shutdown: nothing to do


app = FastAPI(title="Absurdle API", lifespan=lifespan)


@app.get("/")
def root():
    """Minimal sanity check."""
    return {"service": "absurdle-api", "status": "ok"}


@app.get("/api")
def api_info():
    """API info (alias for root)."""
    return {"service": "absurdle-api", "status": "ok"}


@app.get("/health")
def health():
    """Health check for load balancers / hosting."""
    return {"status": "healthy"}
