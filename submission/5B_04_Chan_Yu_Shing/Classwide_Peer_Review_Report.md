# Classwide Mastermind Peer-Review Report

Reviewer: **5B4 CHAN YU SHING**  
Review date: **24 August 2026**

## Review method and criteria

Each available submission was checked against these criteria:

1. **Correctness and Mastermind logic** — secret generation, Black/White feedback,
   duplicate handling, win/loss conditions, and scoring.
2. **Input and configuration validation** — invalid, empty, extreme, and conflicting
   settings must be rejected without corrupting the current configuration.
3. **Reliability and error handling** — the program should start on its stated
   platforms, avoid crashes or infinite loops, and recover from malformed saved data.
4. **Data and score integrity** — leaderboards and CSV/text records should be
   validated, ordered correctly, and remain usable if one row is damaged.
5. **Code quality and maintainability** — clear entry points, unambiguous source
   files, safe resource handling, and removal of dead or misleading code.
6. **User experience** — prompts, menu behaviour, replay/quit paths, and displayed
   rules must agree with the program's actual behaviour.
7. **User-manual and artifact quality** — the exact submitted filename and run
   command, complete instructions, representative examples, troubleshooting, and
   accessible sharing permissions.

Severity labels mean: **Critical** = the program cannot start or a core rule is
wrong; **High** = a valid user path crashes, hangs, becomes unwinnable, or produces
materially false results; **Medium** = incorrect or fragile behaviour with a
workaround; **Low** = clarity, maintainability, or documentation defect.

The report covers every issue found in the code and manual evidence that was
available in the shared class Drive. Suggested tests are included so each code
owner can confirm the fix rather than relying only on visual inspection.

---

## 5A02 CHAU SIU TUNG CEDRIC

Reviewed artifacts: `mastermind.py` and `Mastermind Game – User Manual`.

### What is working well

- The program provides a clear menu, validates guess length and colour codes, keeps
  a guess history, and explains Black and White feedback.
- The intended two-pass feedback design is the correct general approach for
  preventing one secret peg from being counted more than once.
- The manual is thorough, readable, and contains a sample session, score table,
  troubleshooting section, and quick-reference card.

### Issues and constructive fixes

1. **Critical — Yellow is incorrectly used as the internal “already matched”
   marker.** In `calculate_feedback`, matched positions in `secret_copy` are
   replaced with `"Y"`, but `Y` is also the real Yellow colour code. During the
   White-peg pass, the condition that skips `"Y"` therefore also skips unmatched
   genuine Yellow pegs. A case such as secret `YRGB` and guess `RYBK` should award
   a White peg for Yellow, but the marker collision can suppress it. Replace the
   string marker with `None`, a unique sentinel object, or parallel `matched`
   Boolean arrays. **Regression check:** test Yellow in both matched and misplaced
   positions, including repeated colours, and compare the result with a frequency-
   counter implementation.

2. **Medium — the “high score” display is not actually ranked.** Scores are
   appended to `highscore.txt` and displayed in file order, while the manual shows
   numbered ranks in descending score order. A later score of 900 can therefore
   appear below an earlier score of 100. Parse scores as integers, skip invalid
   rows, sort descending, and optionally show only the top ten. **Regression
   check:** save `100`, `900`, and `500` in that order and confirm the display is
   `900`, `500`, `100`.

3. **Medium — score-file handles are not protected by context managers.** The save
   and view functions manually open and close files. If reading, writing, or
   parsing raises after `open()`, the close call can be skipped. Use `with
   open(...) as file:` for both paths and handle `OSError` separately from bad-row
   data. **Regression check:** simulate a permission error and confirm a friendly
   message is shown without leaving the program in a broken state.

4. **Medium — malformed leaderboard rows are not validated before being treated
   as scores.** The current display can label arbitrary text as “points,” and a
   future numeric sort would crash if conversion is not done per row. Require
   exactly two fields, a non-empty name, and a non-negative integer score; skip
   only the bad row and preserve valid rows.

5. **Low — importing the file starts the interactive menu immediately.** There is
   no `if __name__ == '__main__':` guard, which makes automated unit testing and
   reuse of `calculate_feedback()` difficult. Move the menu loop into `main()` and
   guard it. **Regression check:** `python -c "import mastermind"` should return
   without asking for input.

6. **Low — the manual's high-score claim does not match the implementation.** The
   manual presents saved entries as ranked high scores, although the program only
   appends and replays them. Either implement sorting as above or rename the
   section to “Saved Scores” and remove rank language.

7. **Low — the troubleshooting explanation for `FileNotFoundError` is misleading.**
   The manual says it should only occur if `highscore.txt` is deleted while the
   game is running, but the read path already handles a missing file and append
   mode recreates it. Replace that paragraph with realistic permission, invalid-
   row, and read-only-folder troubleshooting.

**Recommended priority:** fix the Yellow sentinel collision first because it
changes the core Mastermind result even for valid guesses.

---

## 5A04 CHIU LANG WEI

Reviewed artifacts: `5A_04_Chiu_Lang_Wei.py` and the submitted 13-page manual.

### What is working well

- The feedback algorithm is duplicate-aware and separates exact matches from
  colour-only matches.
- The game includes configurable settings, score persistence, and substantial
  documentation.

### Issues and constructive fixes

1. **High — invalid colour codes are filtered only after the pool-length check.**
   The program checks the length of `unique_colors` before removing characters
   not found in `color_names`. For example, a four-character entry containing
   three valid colours and one invalid letter can pass the first check, then be
   stored as a three-colour pool for a four-peg game. Filter first, reject any
   invalid token explicitly, then validate the final pool before updating
   `config['colors']`. **Regression check:** try `RBGX` at length four and confirm
   the old valid configuration remains unchanged.

2. **Medium — the second easy-mode length condition is unreachable/redundant.**
   The earlier condition already catches the same `len(unique_colors) <
   code_length` relationship, so the easy-mode-specific branch cannot add its
   intended explanation. Consolidate the rules into one cross-field validator
   with a specific message for no-duplicate mode.

3. **Medium — settings updates should be atomic.** If several settings are changed
   sequentially and a later validation fails, earlier assignments can survive and
   create a partially changed game. Build a temporary candidate dictionary,
   validate every field and relationship, then replace `config` once. **Regression
   check:** enter a valid colour count followed by an invalid code length and
   confirm every previous setting is preserved.

4. **Medium — unbounded attempts can collapse the score penalty.** With a formula
   using `800 // max_attempts`, a sufficiently large attempt count produces a zero
   per-attempt penalty, so all wins have the same score. Enforce a documented
   attempts range or use a proportional formula that cannot truncate to zero.

5. **Medium — player names written directly to CSV can be interpreted as formulas.**
   Names beginning with `=`, `+`, `-`, or `@` may execute as formulas when opened
   in spreadsheet software. Limit name length and prefix or reject dangerous first
   characters before `writer.writerow()`.

6. **Medium — the manual promises internal-space support that the parser does not
   provide.** `validate_guess()` strips the ends and removes hyphens, but does not
   remove internal spaces; `R B G Y` is therefore rejected. Either normalise
   spaces/commas/hyphens or change the manual to say guesses must be compact.

7. **High documentation defect — the manual's run filename does not match the
   uploaded source.** It refers to `5A04SBA.py` and elsewhere uses another
   capitalization, while the submitted file is `5A_04_Chiu_Lang_Wei.py`. Replace
   every command with the exact submitted filename and test it from a clean
   folder.

8. **Low — broad score-loading exceptions hide the cause.** Catch `OSError` for
   file failures and `ValueError`/bad field counts per row so one damaged entry
   does not hide valid scores or make diagnosis impossible.

**Recommended priority:** correct colour-pool validation and the run command;
both currently create user paths that do not behave as documented.

---

## 5A07 LEE CHIN PONG (KELVIN)

Reviewed artifact: `5A7 python mastermind.py`. The manual shortcut reports that
the reviewer needs permission, so its contents could not be verified.

### What is working well

- `evaluate_guess()` uses counters and handles duplicate colours correctly.
- Difficulty choices, guess validation, and the no-duplicate generator are
  generally clear.

### Issues and constructive fixes

1. **High — a player receives a positive final score after losing.** The program
   calculates and displays `final_score` after the game loop even when `won` is
   false. Exhausting every attempt therefore still earns points. Calculate/save a
   score only inside the win branch and set a loss to zero. **Regression check:**
   force a known secret, use all attempts without matching it, and verify that no
   score is awarded or saved.

2. **Medium — the start prompt accepts only one narrow path and lacks a clean exit.**
   A response other than the expected `y` does not provide a well-defined quit or
   retry flow, and EOF/Ctrl+C can expose a traceback. Accept explicit `y`/`n`,
   reprompt invalid responses, and handle `EOFError`/`KeyboardInterrupt` at the
   entry point.

3. **Medium — scoring policy for duplicate mode is counter-intuitive and
   undocumented.** The 1.5 multiplier rewards enabling duplicates even though that
   may make the puzzle harder, and the multiplier's rationale is not visible to
   the player. Define a consistent difficulty model, display it before play, and
   document an example calculation.

4. **Low — the code should expose an import-safe entry point.** Put interactive
   startup in `main()` behind an `if __name__ == '__main__':` guard so the feedback
   function can be unit tested independently.

5. **High artifact-access issue — the manual is not shared with reviewers.** The
   Drive shortcut requires extra permission, preventing verification of run
   instructions, rules, input format, scoring, and troubleshooting. Change the
   target document permission to the class group and test the link using another
   student account or an incognito session.

6. **Documentation follow-up required.** Because the manual is inaccessible, the
   exact filename, commands, screenshots, dependency statements, and behaviour
   claims could not be checked. After fixing sharing, compare every instruction
   against a fresh run and include the loss-score rule explicitly.

**Recommended priority:** stop awarding scores on defeat, then repair the manual's
sharing permission.

---

## 5B01 CHAN CHUN LAM

Reviewed artifact: `5b01 sba .py`. No user manual was present in the folder.

### What is working well

- The Tkinter interface clearly separates setup, colour selection, history, and
  result dialogs.
- The program prevents repeated guesses and rejects a colour pool smaller than the
  code length. Because both the secret and guesses are unique, its simple White-
  peg count is valid for the stated no-repeat rule.

### Issues and constructive fixes

1. **Critical portability defect — `winsound` prevents startup outside Windows.**
   `import winsound` raises `ModuleNotFoundError` on macOS and Linux before the GUI
   opens, even though Mastermind itself uses only standard cross-platform Tkinter
   features. Make sound optional with a guarded import and silent fallback, or use
   Tk's bell. **Regression check:** start the program on Windows and macOS/Linux;
   both must reach the setup screen.

2. **High artifact defect — the required user manual is missing.** The folder
   contains only source code. Add a manual covering the exact filename, Python and
   Tkinter requirements, platform limitations, setup choices, no-repeat rule,
   feedback meaning, controls, screenshots/sample round, replay behaviour, and
   troubleshooting.

3. **Medium — the source filename is difficult to run reliably.** `5b01 sba .py`
   contains spaces and an extra space before `.py`, making typed commands easy to
   get wrong. Rename it to a conventional exact name such as
   `5B_01_Chan_Chun_Lam_main.py`, then use that filename consistently in the
   manual.

4. **Medium — there is no displayed scoring or persistent result record.** If the
   assessment expects scoring/high scores, a correct win currently records only
   the attempt count in a temporary dialog. Add a documented formula, save only
   validated results, and provide a leaderboard or clearly state that scoring is
   outside the selected feature scope.

5. **Low — the fixed `550x700` window has no responsive sizing policy.** Large text
   scaling or smaller screens may clip the bottom controls. Set a sensible minimum
   size, allow resizing, and ensure the history and controls remain reachable.

6. **Low — navigation is abrupt after a result.** Closing the victory/defeat dialog
   immediately rebuilds the menu, so the completed board cannot be reviewed. Offer
   “Play again,” “View final board,” and “Return to menu,” or retain a summary.

7. **Low — important rules are visible only after the game starts.** Display the
   no-repeat rule and feedback explanation on the setup screen or in a Help dialog
   so users understand the constraint before selecting settings.

**Recommended priority:** make startup cross-platform and provide the missing user
manual before refining the GUI.

---

## 5B10 FUNG YAT KIU

Reviewed artifacts: `5B_10_Fung_Yat_Kiu_main.py`, the submitted manual, and the
separate untitled peer-feedback document.

### What is working well

- The intended feedback algorithm prevents a secret peg from producing multiple
  White pegs.
- The program attempts to offer code length, colour-count, attempt-count, and
  duplicate configuration.

### Issues and constructive fixes

1. **Critical — the submitted Python file contains invalid f-string syntax and
   cannot start.** The Black/White explanation lines contain an unmatched `}` in
   f-strings, for example `print(f"...place}")`. Python reports `SyntaxError:
   f-string: single '}' is not allowed` before any game code runs. Remove the `f`
   prefix because no interpolation is needed, or remove the extra brace. **Regression
   check:** run `python -m py_compile 5B_10_Fung_Yat_Kiu_main.py` and then start a
   complete game.

2. **Medium — invalid duplicate answers silently enable duplicates.** The rule is
   calculated as `duplicates_input != 'n'`, so `x`, `no`, or `yes` all become true.
   Accept only `y`, `n`, or an explicitly documented blank default and reprompt
   everything else.

3. **Medium — maximum attempts has no upper bound.** A value such as one million
   creates an unreasonable game and makes a first-attempt score enormous and
   incomparable. Enforce a range such as 1–20 and derive score from a fixed,
   documented scale.

4. **Low/UX — the colour-count prompt contradicts its error message.** The prompt
   and validator use 4–10, but the error says 5–10. Choose one rule and use the same
   value in code, messages, and manual.

5. **Medium/UX — the program ends after one game.** Add a main menu or replay/quit
   prompt so the player can change settings or play again without restarting
   Python.

6. **High documentation defect — the manual is an unfinished template.** It still
   contains placeholders such as `[Name of Feature]`, example text, and a generic
   bugs section. Replace every placeholder with actual rules, configuration,
   feedback, scoring, sample output, replay/exit behaviour, and troubleshooting.

7. **High documentation defect — the run command and dependency list are wrong.**
   The manual says `python main.py`, although the uploaded file has a different
   name, and lists `sys`/`os` while the code uses `random`. Use the exact submitted
   filename and list only real requirements.

8. **Low artifact organisation — the received-feedback document is untitled.**
   Rename it with class number, owner, reviewer, and purpose, and distinguish it
   from the user manual and final response document.

**Recommended priority:** correct the syntax error first; no other feature can be
tested until the file compiles.

---

## 5B12 LAU CHUN LOK

Reviewed artifacts: `5B_12_Lau_Chun_Lok_main.py` and the two-page Google Docs
manual.

### What is working well

- The code is separated into configuration, feedback, storage, and interface
  sections.
- The Counter-based feedback logic handles duplicate colours correctly.

### Issues and constructive fixes

1. **Medium — invalid difficulty input silently starts Medium.** A typo such as `4`
   produces a different game instead of an error. Loop until the user selects 1,
   2, or 3, then display the confirmed preset before generating the secret.

2. **Medium — one malformed CSV row can hide the complete leaderboard.** An empty
   file makes `next(reader)` fail, and converting a bad score during sorting can
   send the entire operation to a general error handler. Validate each row while
   reading, handle an empty file as “No scores yet,” skip only invalid rows, and
   sort parsed integers.

3. **Medium — player names can become spreadsheet formulas.** Limit name length
   and neutralise a leading `=`, `+`, `-`, or `@` before saving CSV.

4. **Low/UX — only space-separated guesses are accepted.** A compact input such as
   `RBGY` is rejected even though it is common for Mastermind. Support compact,
   spaced, comma-separated, and hyphenated forms through one normaliser, or make
   the limitation especially prominent in every prompt.

5. **Low — difficulty semantics need explanation.** Hard mode allows more attempts
   than Medium, so the label may appear contradictory unless its longer code,
   colour pool, and score multiplier are explained together. Show a preset table
   before selection.

6. **High documentation defect — the manual's run command does not match the
   source.** It says `main.py`; the uploaded file is
   `5B_12_Lau_Chun_Lok_main.py`. Use the exact command and test it from a clean
   folder.

7. **Low documentation defects — class and dependency details are inaccurate.**
   The author line says `6B12` instead of `5B12`, and `sys` is listed although it
   is not imported. Correct the identity and list only actual modules.

**Recommended priority:** validate difficulty and leaderboard rows, then correct
the manual's identity and run command.

---

## 5B26 LI YUE

Reviewed artifacts: `config.py`, `core.py`, `game_loop.py`, `highscore.py`,
`main.py`, `sort_search.py`, `stack.py`, `ui.py`, three duplicate `Copy of ...`
files, and `Mastermind User Manual - 5B26 Li Yue.docx`.

### What is working well

- The modular separation is strong, and the feedback logic correctly handles
  exact matches before colour-only matches.
- The project includes undo, multiple input separators, sorting/search helpers,
  high scores, and a dedicated manual.

### Issues and constructive fixes

1. **High — empty numeric input crashes custom configuration.** `is_digit_str("")`
   returns true because its loop performs zero iterations. The next condition then
   evaluates `int("")`, raising `ValueError`. Begin the helper with `if not s:
   return False` and strip input once. **Regression check:** press Enter at every
   numeric prompt and confirm the program reprompts without changing settings.

2. **High — settings are applied partially before full validation.** In difficult
   mode, colours can be updated before an invalid code length is detected; in
   custom mode, colours and length can change before invalid attempts are found.
   Build a candidate configuration copy, validate all values and relationships,
   then commit once. **Regression check:** fail the final prompt and confirm every
   prior setting remains unchanged.

3. **Medium — “Customised Mode” does not customise duplicate rules.** The interface
   says all parameters can be adjusted, but the branch always sets `easy_mode =
   False`, which enables duplicates without asking. Add a strict Yes/No duplicate
   prompt or change the description so it does not promise full customisation.

4. **High defensive-programming issue — secret generation can loop forever.** If
   called with duplicates disabled and `code_length > num_colours`, repeatedly
   drawing unused colours can never complete. UI bounds reduce but do not remove
   the risk for direct calls or future changes. Reject the relationship before the
   loop or use `random.sample()` after validation.

5. **Medium — one malformed high-score row can crash save/load.** Integer
   conversion is not protected per record. Parse field counts and scores row by
   row, skip a damaged row with a clear warning, and preserve every valid entry.

6. **Medium artifact defect — duplicate source files create two sources of truth.**
   `Copy of sort_search.py`, `Copy of stack.py`, and `Copy of ui.py` make it unclear
   which files are authoritative and can lead to fixing one copy while packaging
   another. Remove the duplicates after confirming the canonical versions and add
   a manifest or README.

7. **Low — direct secret-generation boundaries are not documented or tested.** Add
   unit tests for minimum/maximum colours, code length, duplicates on/off, and the
   impossible no-duplicate relationship.

8. **Manual verification item — commands must reflect a multi-file project.** The
   manual should instruct users to keep all canonical modules in one folder and
   run `main.py`, explain which duplicate copies must not be used, and include a
   missing-input troubleshooting case. This becomes especially important because
   the project is not a single-file submission.

**Recommended priority:** fix the empty-input crash and atomic configuration update,
then remove duplicate files.

---

## 5C01 ALI WAH HIN

Reviewed artifacts: `sba code.py` and the submitted 31-page document.

### What is working well

- The feedback algorithm is duplicate-aware, and the project includes substantial
  analysis/design material and several gameplay features.

### Issues and constructive fixes

1. **High — a no-duplicate game can be generated with a secret shorter than the
   configured length.** `random.sample(..., min(length, len(colors)))` silently
   truncates the secret when code length exceeds the colour pool. The win check
   still expects the configured length, so the game is unwinnable. Reject
   `length > len(colors)` in no-duplicate mode; never shorten the secret. **Regression
   check:** length six, five colours, no duplicates must be rejected before play.

2. **High — settings are not committed atomically.** Several global configuration
   values are changed before later input conversion or cross-field validation can
   fail. The message says options are reset, but the previous valid state is not
   actually restored. Validate a temporary copy, then replace the global config
   once.

3. **Medium — invalid duplicate-mode input is accepted as a successful update.** A
   response outside the expected Yes/No choices can leave an unintended value or
   still display success. Reprompt until a valid answer is received and echo the
   final rule.

4. **Medium — one malformed leaderboard row hides all valid scores.** Numeric
   conversion inside the sort path allows a single bad row to raise and trigger a
   general loading error. Validate and parse each row independently, then sort
   only valid integer scores.

5. **Medium — CSV names require spreadsheet-safe handling.** Neutralise a leading
   `=`, `+`, `-`, or `@`, limit length, and remove embedded newlines before saving.

6. **High documentation mismatch — the 31-page file is a design report, not a
   focused operational user manual.** Preserve the SBA analysis separately, but
   add a concise user manual with the exact uploaded filename, run command,
   requirements, modes, input examples, feedback/scoring, data-file location,
   troubleshooting, and screenshots/sample session.

7. **Low — the source filename contains a space and is generic.** Rename it to an
   unambiguous class/name filename and update every command in the new manual.

**Recommended priority:** reject impossible no-duplicate settings, then create a
proper user-facing manual.

---

## 5C03 LAM SZE YUEN (THOMAS)

Reviewed artifacts: `5C_3_Thomas_main_v1.py` and the text manual.

### What is working well

- The program has strong modular organisation, duplicate-aware feedback,
  statistics, and a computer-solver/benchmark mode.
- The manual honestly warns that some solver settings may be slow.

### Issues and constructive fixes

1. **High — custom no-duplicate settings can crash both game modes.** The UI allows
   five colours, a code length of six, and no duplicates. Human breaker reaches
   `random.sample(colors, 6)` and raises `ValueError`; computer breaker can index
   beyond the colour list. Enforce `code_length <= number_of_colors` whenever
   duplicates are off. **Regression check:** test the invalid relationship in both
   modes and confirm it is rejected before generation.

2. **High performance risk — the solver can make the program appear hung.** Large
   custom settings create up to `10^6` candidate codes, and each turn recomputes
   feedback against every history row; benchmark mode multiplies that work across
   games. Cap the candidate space, filter and retain candidates incrementally, and
   show an estimate/warning before a large benchmark.

3. **Medium — configuration should be validated as one object.** Validate numeric
   ranges, duplicate relationship, and estimated search-space size before starting
   either human or computer mode, rather than relying on each downstream function
   to fail.

4. **Medium — CSV text cleaning does not prevent spreadsheet formulas.** Removing
   commas/newlines is not enough; neutralise a leading `=`, `+`, `-`, or `@` before
   storage.

5. **High documentation defect — both source docstring and manual use filenames
   that were not submitted.** The code mentions `mastermind_game.py`; the manual
   says `5C_3_LAM SZE YUEN_main.py`; the actual file is
   `5C_3_Thomas_main_v1.py`. Choose one final filename and update every command.

6. **Medium — manual “safe custom rules” wording is too strong.** The invalid
   no-duplicate relationship currently crashes, and large solver spaces can be
   impractical. After adding validation, document the exact allowed ranges and
   benchmark limit.

7. **Low — file operations use manual open/close.** Use context managers and
   handle file errors separately from bad-row parsing.

8. **Low documentation improvement — add a representative solver example.** Show
   one feedback-driven elimination round and explain why the candidate count falls;
   this helps users understand the advanced feature and its performance cost.

**Recommended priority:** enforce the no-duplicate relationship and solver-space
limit before improving the manual.

---

## 5C23 LI MEI YI (ELISE LI)

Reviewed artifacts: `5C_23_elise li_main.py` and the six-page manual.

### What is working well

- The game supports both breaker and maker roles, session statistics, custom
  settings, feedback explanations, and a polished six-page manual.
- The manual openly identifies the current no-score behaviour for a successful
  human Code Maker defence.

### Issues and constructive fixes

1. **High — the computer solver ignores almost all feedback.** It removes guessed
   colours only when Black and White are both zero; for every other result it does
   not constrain positions, counts, or candidates. This makes “smarter guesses” in
   the manual inaccurate and leaves the solver mostly random. Precompute candidate
   codes and retain only candidates whose simulated feedback against each guess
   exactly matches the supplied `(black, white)` pair. **Regression check:** after
   known feedback, assert every remaining candidate reproduces it.

2. **High — Code Maker mode can enter an infinite guess-generation loop.** The
   program repeatedly generates until it finds a guess not in `past_guesses`. In a
   small custom space, all possible codes can be exhausted while attempts remain,
   so the loop never exits. Maintain a finite candidate list, remove each chosen
   guess, and stop with a clear result when it becomes empty.

3. **High — feedback validation accepts combinations inconsistent with every
   possible secret.** Checking only `black + white <= length` is insufficient.
   Apply the feedback to the candidate set and reject it if zero candidates remain,
   explaining that the entered pegs contradict earlier feedback.

4. **Medium — session summary repeats the last game's values for every row.** The
   loop iterates through `record` but prints `session_scores[-1]`, so all displayed
   rows show the last game. Print the current `record`. **Regression check:** store
   two games with different modes/scores and confirm two different rows.

5. **Medium — “winning streak” is not a real consecutive-win calculation.** Only
   scored results are loaded and losses are not saved, so counting saved results
   cannot detect a loss that breaks a streak. Persist every game with a win/loss
   field and compute consecutive wins in chronological order.

6. **Medium — username matching can mix different users.** Substring matching with
   `if f"User: {username}" in line` lets `Ann` match `Anna`. Parse the structured
   field and compare the full username exactly.

7. **Medium — successful Code Maker defence is neither scored nor saved.** This
   means session counts and statistics exclude a valid success path. Define a
   defence score or save a zero/non-scored win record with an explicit result type.

8. **Medium — broad `except Exception: pass` hides damaged data and real I/O
   failures.** Validate each row, report skipped records, and separately handle
   `OSError`. Silent failure makes incorrect statistics difficult to diagnose.

9. **Medium — custom pegs and attempts have no practical upper bounds.** Very large
   values create enormous candidate spaces and unusable sessions. Set documented
   limits based on solver complexity and refuse settings above them.

10. **Documentation mismatch — session summary claims to show all games.** Losses
    and unscored defences are not persisted, so the game count covers only saved
    scored results. Fix persistence or narrow the wording.

11. **Documentation mismatch — the saved “settings” are incomplete.** Records
    include mode, score, code length, and colour count, but not the duplicate rule.
    Save that rule or list exactly which settings are retained.

12. **Documentation mismatch — “no valid combinations” is not fully implemented.**
    The code checks only basic colour availability, not consistency across all
    previous feedback. Implement candidate filtering before claiming this state.

**Recommended priority:** replace random non-repeating generation with a finite,
feedback-filtered candidate set; it resolves the solver-quality, inconsistency,
and infinite-loop defects together.

---

## 5D09 LEUNG CHUN FUNG (CHARLIE LEUNG)

Reviewed artifacts: `5D_09_Charlie_Leung_main.py` and the nine-page manual.

### What is working well

- Feedback correctly handles duplicates, the game has configurable modes and score
  saving, and the manual includes substantial gameplay guidance.

### Issues and constructive fixes

1. **High — custom settings accept zero or negative values.** Code length zero
   produces an empty secret; pressing Enter can then satisfy `black == code_length`
   and award an instant win. Non-positive attempts can skip the game loop and show
   an invalid defeat. Enforce bounded positive ranges before play. **Regression
   check:** test `0`, `-1`, blank, non-numeric, and values above the maximum for
   both fields.

2. **Medium — any duplicate response other than `Y` becomes false.** A typo changes
   the game rules silently. Reprompt until explicit `Y` or `N` and display the
   confirmed rule.

3. **Medium — otherwise valid guesses fail because whitespace is not normalised.**
   Apply `.strip()` and optionally accept spaces, commas, and hyphens before length
   and colour validation.

4. **Medium/UX — there is no in-game quit path or clean interruption handling.**
   Recognise `quit` before guess validation and catch `EOFError`/`KeyboardInterrupt`
   at the entry point so users can return to the menu without a traceback.

5. **Low — module-level history contains fake sample rows and is shadowed by a
   local variable.** This dead data is misleading during maintenance. Remove it or
   move it into a documented test fixture.

6. **Low/portability — `os.system('')` runs at import without a clear need.** Remove
   the side effect or document the terminal feature that requires it and guard by
   platform.

7. **Medium — broad CSV exceptions hide the failure source.** Validate rows per
   record and handle `OSError` separately so valid results remain visible.

8. **High documentation defect — the manual run filename is reversed.** It says
   `5D_09_Leung_Charlie_main.py`, but the uploaded file is
   `5D_09_Charlie_Leung_main.py`. Correct and test the exact command.

9. **Low documentation defect — the dependency list is incomplete.** It mentions
   only `random`, while the source also imports `os` and `csv` (all built-in).
   Explain that no third-party packages are required and list actual imports only.

10. **Documentation claim is too strong.** The manual says strict validation
    prevents crashes, but zero/negative settings create invalid games. Narrow the
    claim until boundary validation is implemented.

**Recommended priority:** enforce custom-setting bounds and strict Yes/No input,
then correct the run command.

---

## 5B02 CHAN CHUNG MAN — evidence limitation

The shared folder was present but empty when reviewed. There was no source file or
manual to execute, inspect, or compare against the criteria. A technical review
would be fabricated without evidence, so no code-specific bugs are claimed.

Constructive required action:

1. Upload the final Python source and user manual to the designated folder.
2. Use clear class/name filenames and verify class-group view permission.
3. Confirm the source starts from a clean folder and that the manual's command uses
   the exact uploaded filename.
4. Request a new review after upload; only then can correctness, validation,
   scoring, UX, and documentation be evaluated.

---

## Class folders not available for review

The Classroom reviewer list also contains students for whom no corresponding
submission folder was visible in the shared Drive: **5A08 LEE TSUN, 5A10 LIU LEO,
5A11 MOK TIK LUN, and 5D18 CHOW FONG TING**. No review or Form response should be
invented for those students. They need to upload/share artifacts before an
evidence-based review can be completed.

## Submission plan

- Existing Google Form records appear to cover 5A04, 5C01, and 5D09.
- New detailed Form responses should be submitted for the remaining reviewable
  owners: 5A02, 5A07, 5B01, 5B10, 5B12, 5B26, 5C03, and 5C23.
- 5B02 should receive an evidence-limit notice rather than invented code feedback.
- The four students without visible folders cannot receive a technical review until
  their artifacts exist and are accessible.
- Every review email should preserve the positive findings, all identified issues,
  recommended priority, and concrete fixes from this report.
