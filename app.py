"""
Web Absurdle — FastAPI backend.
Run from repo root: uvicorn app:app --reload
"""
import os
import random
import uuid
from contextlib import asynccontextmanager
from typing import Literal

from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel, field_validator

import absurdle


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
    return GiveUpResponse(answer=answer)
