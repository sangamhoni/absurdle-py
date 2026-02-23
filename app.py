"""
Web Absurdle — FastAPI backend.
Run from repo root: uvicorn app:app --reload
"""
import json
import os
import random
import uuid
from contextlib import asynccontextmanager
from typing import Literal

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, field_validator

import absurdle

# Optional Redis for game store (shared across instances/workers). Set REDIS_URL to enable.
_redis = None
_REDIS_KEY_PREFIX = "absurdle:game:"
_REDIS_TTL_SECONDS = 86400  # 24 hours


class CreateGameResponse(BaseModel):
    game_id: str
    remaining_count: int


class GuessRequest(BaseModel):
    guess: str

    @field_validator("guess")
    @classmethod
    def guess_uppercase(cls, v: str) -> str:
        return v.strip().upper() if v else ""


class GuessResponse(BaseModel):
    result: str
    won: bool


class GiveUpResponse(BaseModel):
    answer: str

# Game state: {remaining_words: list[str], status: GameStatus}
GameStatus = Literal["active", "won", "gave_up"]
_GAME_STORE: dict[str, dict] = {}  # used when REDIS_URL is not set


def _game_store_set(game_id: str, state: dict) -> None:
    if _redis:
        key = _REDIS_KEY_PREFIX + game_id
        _redis.setex(
            key,
            _REDIS_TTL_SECONDS,
            json.dumps({"remaining_words": state["remaining_words"], "status": state["status"]}),
        )
    else:
        _GAME_STORE[game_id] = state


def _game_store_get(game_id: str) -> dict | None:
    if _redis:
        key = _REDIS_KEY_PREFIX + game_id
        raw = _redis.get(key)
        if raw is None:
            return None
        data = json.loads(raw)
        return {"remaining_words": data["remaining_words"], "status": data["status"]}
    return _GAME_STORE.get(game_id)


def create_game(answer_set_words: set[str]) -> str:
    """Create a new game, store it, return game_id."""
    game_id = str(uuid.uuid4())
    state = {
        "remaining_words": list(answer_set_words),
        "status": "active",
    }
    _game_store_set(game_id, state)
    return game_id


def get_game(game_id: str) -> dict | None:
    """Return game state or None if not found."""
    return _game_store_get(game_id)

# Paths relative to repo root (where app.py lives).
_REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
_STATIC_DIR = os.path.join(_REPO_ROOT, "static")


def _word_list_path() -> str:
    raw = os.environ.get("WORD_LIST", "wordle-La.txt")
    if os.path.isabs(raw):
        return raw
    return os.path.join(_REPO_ROOT, raw)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load word list at startup; connect to Redis if REDIS_URL set."""
    global _redis
    redis_url = os.environ.get("REDIS_URL")
    if redis_url:
        try:
            import redis as redis_lib
            _redis = redis_lib.Redis.from_url(redis_url, decode_responses=True)
            _redis.ping()
        except Exception as e:
            raise RuntimeError(f"Redis connection failed: {e}") from e
    path = _word_list_path()
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Word list not found: {path}")
    words = absurdle.load_answer_set_words(path)
    if not words:
        raise ValueError(f"Word list is empty or has no 5-letter words: {path}")
    app.state.answer_set_words = words
    yield
    if _redis:
        try:
            _redis.close()
        except Exception:
            pass
        _redis = None


app = FastAPI(title="Absurdle API", lifespan=lifespan)

# CORS: allow frontend (same-origin when served from this app; configurable for other origins).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Accept"],
)

# Serve the SPA at root; assets under /static.
@app.get("/")
def serve_app():
    """Serve the frontend (index.html)."""
    return FileResponse(os.path.join(_STATIC_DIR, "index.html"))

app.mount("/static", StaticFiles(directory=_STATIC_DIR), name="static")


@app.get("/api")
def api_info():
    """API sanity check."""
    return {"service": "absurdle-api", "status": "ok"}


@app.get("/health")
def health():
    """Health check for load balancers / hosting."""
    return {"status": "healthy"}


@app.get("/check-word")
def check_word(word: str, request: Request):
    """Check if a 5-letter word is in the word list. For pre-Enter validation."""
    w = (word or "").strip().upper()
    if not absurdle.is_valid_guess(w):
        return {"in_list": False}
    if not absurdle.is_in_wordlist(w, request.app.state.answer_set_words):
        return {"in_list": False}
    return {"in_list": True}


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


@app.post("/games/{game_id}/guess", response_model=GuessResponse)
def guess_endpoint(game_id: str, body: GuessRequest, request: Request):
    """Submit a 5-letter guess. Returns result string (G/Y/W) and won flag."""
    state = get_game(game_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Game not found")
    if state["status"] != "active":
        raise HTTPException(status_code=409, detail="Game already ended")

    guess = body.guess
    if not absurdle.is_valid_guess(guess):
        raise HTTPException(status_code=422, detail="Guess must be exactly 5 letters")
    answer_set_words = request.app.state.answer_set_words
    if not absurdle.is_in_wordlist(guess, answer_set_words):
        raise HTTPException(status_code=422, detail="Not in word list")

    result_string, new_remaining = absurdle.get_adversarial_result(
        guess, answer_set_words, state["remaining_words"]
    )
    state["remaining_words"] = new_remaining
    if result_string == "GGGGG":
        state["status"] = "won"
    _game_store_set(game_id, state)
    return GuessResponse(result=result_string, won=(result_string == "GGGGG"))


@app.post("/games/{game_id}/giveup", response_model=GiveUpResponse)
def giveup_endpoint(game_id: str):
    """Give up and reveal one of the remaining words. Game is then ended."""
    state = get_game(game_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Game not found")
    if state["status"] != "active":
        raise HTTPException(status_code=409, detail="Game already ended")

    remaining = state["remaining_words"]
    answer = random.choice(remaining) if remaining else ""
    state["status"] = "gave_up"
    _game_store_set(game_id, state)
    return GiveUpResponse(answer=answer)
