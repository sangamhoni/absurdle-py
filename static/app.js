/* Web Absurdle — app */

(function () {
  const landing = document.getElementById("landing");
  const game = document.getElementById("game");
  const playBtn = document.getElementById("play-btn");
  const grid = document.getElementById("grid");
  const keyboard = document.getElementById("keyboard");

  // Best result per letter for keyboard colors. Priority: correct (3) > present (2) > absent (1)
  const letterStatePriority = { correct: 3, present: 2, absent: 1 };
  let letterStates = {};

  function getLetterKeyEl(letter) {
    return keyboard.querySelector('.key[data-key="' + letter + '"]');
  }

  function clearKeyboardLetterStates() {
    letterStates = {};
    keyboard.querySelectorAll(".key[data-key]").forEach(function (key) {
      const dk = key.getAttribute("data-key");
      if (dk && dk.length === 1 && /[A-Z]/.test(dk)) {
        key.removeAttribute("data-state");
      }
    });
  }

  /**
   * Update keyboard key colors from a guess result.
   * guessWord: 5-letter string (e.g. "SPEED")
   * resultString: 5 chars from API, G/Y/W (e.g. "WYGWG")
   * Priority: Green > Yellow > Gray (e.g. if A is gray once and green later, show green).
   */
  function updateKeyboardFromGuess(guessWord, resultString) {
    if (!guessWord || !resultString || guessWord.length !== 5 || resultString.length !== 5) return;
    const map = { G: "correct", Y: "present", W: "absent" };
    for (let i = 0; i < 5; i++) {
      const letter = guessWord[i].toUpperCase();
      const result = map[resultString[i].toUpperCase()] || "absent";
      const prev = letterStates[letter];
      const prevP = prev ? letterStatePriority[prev] : 0;
      const currP = letterStatePriority[result];
      if (currP > prevP) letterStates[letter] = result;
    }
    keyboard.querySelectorAll(".key[data-key]").forEach(function (key) {
      const letter = key.getAttribute("data-key");
      if (letter && letter.length === 1 && /[A-Z]/.test(letter)) {
        const state = letterStates[letter];
        if (state) key.setAttribute("data-state", state);
        else key.removeAttribute("data-state");
      }
    });
  }

  function getCurrentRow() {
    const rows = grid.querySelectorAll(".game-row");
    return rows.length ? rows[rows.length - 1] : null;
  }

  function getCurrentTiles(row) {
    return row ? Array.from(row.querySelectorAll(".tile")) : [];
  }

  function getCurrentLetters(row) {
    const tiles = getCurrentTiles(row);
    return tiles.map((t) => (t.textContent || "").trim()).join("");
  }

  function setTileLetter(tile, letter) {
    tile.textContent = letter || "";
    tile.setAttribute("data-state", letter ? "filled" : "empty");
  }

  function onLetterKey(letter) {
    const row = getCurrentRow();
    if (!row) return;
    const letters = getCurrentLetters(row);
    if (letters.length >= 5) return;
    const tiles = getCurrentTiles(row);
    setTileLetter(tiles[letters.length], letter);
  }

  function onBackspace() {
    const row = getCurrentRow();
    if (!row) return;
    const tiles = getCurrentTiles(row);
    const letters = getCurrentLetters(row);
    if (letters.length === 0) return;
    setTileLetter(tiles[letters.length - 1], "");
  }

  playBtn.addEventListener("click", function () {
    clearKeyboardLetterStates();
    landing.classList.add("hidden");
    landing.setAttribute("aria-hidden", "true");
    game.classList.remove("hidden");
    game.setAttribute("aria-hidden", "false");
    game.focus();
  });

  keyboard.addEventListener("click", function (e) {
    const key = e.target.closest(".key");
    if (!key) return;
    const dataKey = key.getAttribute("data-key");
    if (!dataKey) return;
    if (dataKey === "enter" || dataKey === "giveup") {
      return;
    }
    if (dataKey === "backspace") {
      onBackspace();
      return;
    }
    if (dataKey.length === 1 && /[A-Z]/.test(dataKey)) {
      onLetterKey(dataKey);
    }
  });
})();
