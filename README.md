# ABSURDLE
Wordle's Evil Twin
***

## ABOUT
An adversarial Wordle variant powered by a greedy algorithm that constantly changes the secret word to evade your guesses, actively fighting to prolong the game for as long as possible. Instead of guessing a predetermined answer, your goal is to mathematically corner the AI until it has absolutely nowhere left to hide.  

**uses greedy algorithm for state space maximization**

## Web app (development)

- **Virtual environment:** `source .venv/bin/activate` (macOS/Linux).
- **Backend entrypoint:** `app.py` (FastAPI app; created in later milestone).
- **Install deps:** `pip install -r requirements.txt`
- **Run server:** `uvicorn app:app --reload` (from repo root when app exists).

## CREDITS
Word list source: https://github.com/dwyl/english-words/blob/master/words_alpha.txt
