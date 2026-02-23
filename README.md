# ABSURDLE
Wordle's Evil Twin
***

## ABOUT
An adversarial Wordle variant powered by a greedy algorithm that constantly changes the secret word to evade your guesses, actively fighting to prolong the game for as long as possible. Instead of guessing a predetermined answer, your goal is to mathematically corner the AI until it has absolutely nowhere left to hide.  

**uses greedy algorithm for state space maximization**

---

## Word list

- **Default list:** `wordle-La.txt` in the repo root (2,315 five-letter words).
- **Source:** [Wordle dictionary (La) – scholtes](https://gist.github.com/scholtes/94f3c0303ba6a7768b47583aff36654d#file-wordle-la-txt) (Wordle’s “La” list: guessable words that can be the word of the day).
- At startup the backend reads the word list (one word per line), keeps only 5-letter words; that set is both the **answer pool** and **allowed guesses**. Override with **`WORD_LIST`** if you want a different file.

---

## Local development

- **Virtual environment:** `source .venv/bin/activate` (macOS/Linux).
- **Install:** `pip install -r requirements.txt`
- **Run:** `uvicorn app:app --reload` (from repo root).
- **Open:** http://localhost:8000

Optional: `WORD_LIST=path/to/words.txt` to use another list (default: `wordle-La.txt`).

---

## Hosting

- **Build:** `pip install -r requirements.txt`
- **Start:** `uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1`
- **Health:** `GET /health` → `{"status":"healthy"}`

The app serves the frontend from the same server; one URL is enough. Share that URL to play.

**“Game not found” after submitting a guess?** Game state is in memory (or in Redis if configured). On Render’s free tier the app can spin down; when it wakes, memory is empty so old game IDs are gone. Fixes: (1) Use **one worker** (`--workers 1`) so one process handles all requests. (2) Optional: add a **Redis** (Key Value) instance on Render, link it to your web service so `REDIS_URL` is set—then game state is shared and survives restarts better.

---

## CREDITS
Word list: [Wordle dictionary (La)](https://gist.github.com/scholtes/94f3c0303ba6a7768b47583aff36654d) by scholtes.
