"""
Web Absurdle — FastAPI backend.
Run from repo root: uvicorn app:app --reload
"""
import os
import uuid
from contextlib import asynccontextmanager
from typing import Literal

from fastapi import FastAPI, Request
from pydantic import BaseModel

import absurdle


class CreateGameResponse(BaseModel):
    game_id: str
    remaining_count: int

# In-memory game store: game_id -> {remaining_words: list[str], status: GameStatus}
GameStatus = Literal["active", "won", "gave_up"]
GAME_STORE: dict[str, dict] = {}


def create_game(answer_set_words: set[str]) -> str:
    """Create a new game, store it, return game_id."""
    game_id = str(uuid.uuid4())
    GAME_STORE[game_id] = {
        "remaining_words": list(answer_set_words),
        "status": "active",
    }
    return game_id


def get_game(game_id: str) -> dict | None:
    """Return game state or None if not found."""
    return GAME_STORE.get(game_id)

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


@app.post("/games", response_model=CreateGameResponse, status_code=201)
def create_game_endpoint(request: Request):
    """Create a new game. No request body. Returns game_id and remaining_count."""
    answer_set_words = request.app.state.answer_set_words
    game_id = create_game(answer_set_words)
    state = get_game(game_id)
    return CreateGameResponse(
        game_id=game_id,
        remaining_count=len(state["remaining_words"]),
    )
