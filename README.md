# ABSURDLE
Wordle's Evil Twin  
PLAY IT HERE: https://absurdle.onrender.com/

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

**“Game not found” after submitting a guess?** Hit `GET /health` — if you see `"redis": false`, the app is using in-memory store (lost on restart or if requests hit different workers). Use `--workers 1` and, on Render, add a Redis (Key Value) and set `REDIS_URL`. If it keeps happening, try **Railway** (below).

### Deploy on Railway (alternative to Render)

Railway runs one instance by default (no spin-down like Render free) and often avoids “game not found” with no Redis.

1. Go to [railway.app](https://railway.app) → **Login** with GitHub.
2. **New Project** → **Deploy from GitHub repo** → select **absurdle-py** (or your repo).
3. Railway detects Python and uses your **Procfile**. If it doesn’t, set **Start Command** to:  
   `uvicorn app:app --host 0.0.0.0 --port $PORT --workers 1`
4. In the service → **Settings** → **Networking** → **Generate Domain** to get a public URL.
5. Deploy. Your app runs on that URL; no Redis needed for a single instance.

(Optional: add **Redis** in Railway and set `REDIS_URL` for shared state across deploys.)

---

## CREDITS
Word list: [Wordle dictionary (La)](https://gist.github.com/scholtes/94f3c0303ba6a7768b47583aff36654d) by scholtes.
