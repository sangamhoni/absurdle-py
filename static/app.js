/* Web Absurdle — app (Milestone 7: API integration + game flow) */

(function () {
  const landing = document.getElementById("landing");
  const game = document.getElementById("game");
  const playBtn = document.getElementById("play-btn");
  const grid = document.getElementById("grid");
  const gridScroll = document.querySelector(".game-grid-scroll");
  const keyboard = document.getElementById("keyboard");
  const gameMessage = document.getElementById("game-message");
  const gameStatus = document.getElementById("game-status");
  const giveupDialog = document.getElementById("giveup-dialog");
  const giveupDialogNo = document.getElementById("giveup-dialog-no");
  const giveupDialogYes = document.getElementById("giveup-dialog-yes");

  let gameId = null;
  let gameEnded = false;
  let submitting = false;
  let invalidWord = false;
  let checkWordAbort = null;

  // Best result per letter for keyboard colors. Priority: correct (3) > present (2) > absent (1)
  const letterStatePriority = { correct: 3, present: 2, absent: 1 };
  let letterStates = {};

  function showMessage(text, isError) {
    if (!gameMessage) return;
    gameMessage.classList.remove("fade-in");
    gameMessage.textContent = text || "";
    gameMessage.classList.toggle("error", !!isError);
    if (text) {
      void gameMessage.offsetWidth;
      gameMessage.classList.add("fade-in");
    }
  }

  function showStatusMessage(text) {
    if (gameStatus) {
      gameStatus.classList.remove("fade-in");
      gameStatus.textContent = text || "";
      if (text) {
        void gameStatus.offsetWidth;
        gameStatus.classList.add("fade-in");
      }
    }
    if (gameMessage) gameMessage.textContent = "";
  }

  function clearStatusMessage() {
    if (gameStatus) gameStatus.textContent = "";
  }

  function setInvalidWord(flag) {
    invalidWord = flag;
    keyboard.classList.toggle("keyboard-invalid", flag);
    const row = getCurrentRow();
    const rowMsg = row ? row.querySelector(".row-message") : null;
    if (rowMsg) rowMsg.textContent = flag ? "Not in word list" : "";
    if (!flag) showMessage("");
  }

  function checkWordThen(word) {
    if (checkWordAbort) checkWordAbort.abort();
    if (!word || word.length !== 5) {
      setInvalidWord(false);
      return;
    }
    checkWordAbort = new AbortController();
    fetch("/check-word?word=" + encodeURIComponent(word.toUpperCase()), { signal: checkWordAbort.signal })
      .then(function (res) { return res.json(); })
      .then(function (data) {
        setInvalidWord(!data.in_list);
      })
      .catch(function () {
        setInvalidWord(false);
      })
      .finally(function () {
        checkWordAbort = null;
      });
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

  var FLIP_DURATION_MS = 650;
  var FLIP_STAGGER_MS = 75;
  var FLIP_MID_MS = 325;

  function setTileLetter(tile, letter) {
    tile.textContent = letter || "";
    tile.setAttribute("data-state", letter ? "filled" : "empty");
    if (letter) {
      tile.classList.add("tile-pop");
      setTimeout(function () {
        tile.classList.remove("tile-pop");
      }, 120);
    }
  }

  function countSubmittedRows() {
    let count = 0;
    grid.querySelectorAll(".game-row").forEach(function (row) {
      const tiles = row.querySelectorAll(".tile");
      const first = tiles[0];
      if (first && ["correct", "present", "absent", "revealed"].indexOf(first.getAttribute("data-state")) !== -1) count++;
    });
    return count;
  }

  function scrollCurrentRowIntoView() {
    const row = getCurrentRow();
    if (!row || !gridScroll) return;
    var grid = row.parentElement;
    if (!grid) return;
    var rowBottom = row.offsetTop + row.offsetHeight + (grid.offsetTop || 0);
    var extraSpace = 2.75 * 16;
    var targetTop = rowBottom + extraSpace - gridScroll.clientHeight;
    var maxScroll = gridScroll.scrollHeight - gridScroll.clientHeight;
    targetTop = Math.min(maxScroll, Math.max(0, targetTop));
    gridScroll.scrollTo({ top: targetTop, behavior: "smooth" });
  }

  function addNewRow() {
    const rowIndex = grid.querySelectorAll(".game-row").length;
    const row = document.createElement("div");
    row.className = "game-row";
    row.setAttribute("data-row", String(rowIndex));
    const rowTiles = document.createElement("div");
    rowTiles.className = "row-tiles";
    for (let i = 0; i < 5; i++) {
      const tile = document.createElement("div");
      tile.className = "tile";
      tile.setAttribute("data-state", "empty");
      tile.setAttribute("data-index", String(i));
      rowTiles.appendChild(tile);
    }
    row.appendChild(rowTiles);
    const rowMsg = document.createElement("span");
    rowMsg.className = "row-message";
    rowMsg.setAttribute("aria-live", "polite");
    row.appendChild(rowMsg);
    grid.appendChild(row);
    scrollCurrentRowIntoView();
  }

  function revealRowWithFlip(row, word, resultStates, onComplete) {
    var tiles = getCurrentTiles(row);
    var upper = (word || "").toUpperCase();
    var i;
    for (i = 0; i < 5; i++) {
      tiles[i].textContent = upper[i] || "";
      tiles[i].setAttribute("data-state", "filled");
    }
    row.classList.add("row-revealing");
    for (i = 0; i < 5; i++) {
      (function (idx) {
        setTimeout(function () {
          tiles[idx].setAttribute("data-state", resultStates[idx] || "absent");
        }, FLIP_MID_MS + idx * FLIP_STAGGER_MS);
      })(i);
    }
    setTimeout(function () {
      row.classList.remove("row-revealing");
      if (typeof onComplete === "function") onComplete();
    }, FLIP_DURATION_MS + 4 * FLIP_STAGGER_MS);
  }

  function setRowResult(row, word, resultString) {
    var map = { G: "correct", Y: "present", W: "absent" };
    var result = (resultString || "").toUpperCase();
    var states = [];
    for (var i = 0; i < 5; i++) states.push(map[result[i]] || "absent");
    revealRowWithFlip(row, word, states);
  }

  function setRowAnswerCorrect(row, word) {
    var states = ["correct", "correct", "correct", "correct", "correct"];
    revealRowWithFlip(row, word, states);
  }

  function disableInput() {
    gameEnded = true;
    keyboard.classList.add("disabled");
  }

  function onLetterKey(letter) {
    if (gameEnded || submitting) return;
    const row = getCurrentRow();
    if (!row) return;
    const letters = getCurrentLetters(row);
    if (letters.length >= 5) return;
    const tiles = getCurrentTiles(row);
    setTileLetter(tiles[letters.length], letter);
    const nextWord = getCurrentLetters(row);
    if (nextWord.length === 5) checkWordThen(nextWord);
    else setInvalidWord(false);
  }

  function onBackspace() {
    if (gameEnded || submitting) return;
    const row = getCurrentRow();
    if (!row) return;
    const tiles = getCurrentTiles(row);
    const letters = getCurrentLetters(row);
    if (letters.length === 0) return;
    setTileLetter(tiles[letters.length - 1], "");
    setInvalidWord(false);
  }

  function submitGuess() {
    if (gameEnded || submitting || !gameId || invalidWord) return;
    const row = getCurrentRow();
    if (!row) return;
    const word = getCurrentLetters(row);
    if (word.length !== 5) return;

    submitting = true;
    showMessage("");

    fetch("/games/" + encodeURIComponent(gameId) + "/guess", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ guess: word }),
    })
      .then(function (res) {
        return res.json().then(function (data) {
          if (!res.ok) throw { status: res.status, data: data };
          return data;
        });
      })
      .then(function (data) {
        var map = { G: "correct", Y: "present", W: "absent" };
        var result = (data.result || "").toUpperCase();
        var states = [];
        for (var r = 0; r < 5; r++) states.push(map[result[r]] || "absent");
        revealRowWithFlip(row, word, states, function () {
          updateKeyboardFromGuess(word, data.result);
          if (data.won) {
            var x = countSubmittedRows();
            showStatusMessage("You guessed successfully in " + x + " guesses!");
            disableInput();
          } else {
            addNewRow();
          }
        });
      })
      .catch(function (err) {
        if (err && err.status === 422) {
          const msg = (err.data && err.data.detail) || "Invalid guess.";
          showMessage(typeof msg === "string" ? msg : "Not in word list.", true);
        } else if (err && err.status === 404) {
          showMessage("Game not found.", true);
        } else {
          showMessage("Something went wrong. Try again.", true);
        }
      })
      .finally(function () {
        submitting = false;
      });
  }

  function closeGiveupDialog() {
    if (giveupDialog) giveupDialog.hidden = true;
  }

  function openGiveupDialog() {
    if (giveupDialog) giveupDialog.hidden = false;
  }

  function giveUpFlow() {
    if (gameEnded || submitting) return;
    if (!gameId) {
      showMessage("Game not found.", true);
      return;
    }
    openGiveupDialog();
  }

  function confirmGiveUp() {
    closeGiveupDialog();
    if (!gameId) return;
    submitting = true;
    showMessage("");
    clearStatusMessage();

    fetch("/games/" + encodeURIComponent(gameId) + "/giveup", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    })
      .then(function (res) {
        return res.json().then(function (data) {
          if (!res.ok) throw { status: res.status, data: data };
          return data;
        });
      })
      .then(function (data) {
        var x = countSubmittedRows();
        var answerRow = getCurrentRow();
        if (answerRow) {
          setRowAnswerCorrect(answerRow, data.answer);
          scrollCurrentRowIntoView();
        }
        showStatusMessage("You gave up after " + x + " guesses!");
        disableInput();
      })
      .catch(function (err) {
        if (err && err.status === 404) showMessage("Game not found.", true);
        else if (err && err.status === 409) showMessage("Game already ended.", true);
        else showMessage("Something went wrong. Try again.", true);
      })
      .finally(function () {
        submitting = false;
      });
  }

  if (giveupDialogNo) giveupDialogNo.addEventListener("click", closeGiveupDialog);
  if (giveupDialogYes) giveupDialogYes.addEventListener("click", confirmGiveUp);
  if (giveupDialog) {
    giveupDialog.addEventListener("click", function (e) {
      if (e.target === giveupDialog) closeGiveupDialog();
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && giveupDialog && !giveupDialog.hidden) {
        closeGiveupDialog();
      }
    });
  }

  function resetGridToSingleRow() {
    while (grid.firstChild) grid.removeChild(grid.firstChild);
    addNewRow();
  }

  playBtn.addEventListener("click", function () {
    showMessage("");
    clearStatusMessage();
    gameId = null;
    gameEnded = false;
    submitting = false;
    invalidWord = false;
    if (checkWordAbort) checkWordAbort.abort();
    clearKeyboardLetterStates();
    keyboard.classList.remove("disabled");
    keyboard.classList.remove("keyboard-invalid");
    resetGridToSingleRow();

    fetch("/games", { method: "POST", headers: { "Content-Type": "application/json" } })
      .then(function (res) {
        if (!res.ok) throw new Error("Create failed");
        return res.json();
      })
      .then(function (data) {
        gameId = data.game_id;
        landing.classList.add("hidden");
        landing.setAttribute("aria-hidden", "true");
        game.classList.remove("hidden");
        game.setAttribute("aria-hidden", "false");
        game.focus();
        requestAnimationFrame(function () {
          scrollCurrentRowIntoView();
        });
      })
      .catch(function () {
        window.alert("Could not start game. Try again.");
      });
  });

  keyboard.addEventListener("click", function (e) {
    const key = e.target.closest(".key");
    if (!key) return;
    const dataKey = key.getAttribute("data-key");
    if (!dataKey) return;
    if (dataKey === "enter") {
      submitGuess();
      return;
    }
    if (dataKey === "giveup") {
      giveUpFlow();
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

  document.addEventListener("keydown", function (e) {
    if (game.classList.contains("hidden") || gameEnded) return;
    if (e.ctrlKey || e.metaKey || e.altKey) return;

    if (e.key === "Backspace") {
      e.preventDefault();
      onBackspace();
      return;
    }
    if (e.key === "Enter") {
      e.preventDefault();
      submitGuess();
      return;
    }
    if (e.key.length === 1 && /^[a-zA-Z]$/.test(e.key)) {
      e.preventDefault();
      onLetterKey(e.key.toUpperCase());
    }
  });
})();
