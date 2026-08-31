# Peer review notes

Reviewer: **5B4 CHAN YU SHING 陳御丞 M**  
Reviewer email: **s202101127@elearn.cccmkc.edu.hk**

## Incoming comments selected for Step 3

### 5C03 LAM SZE YUEN

1. `GameConfig.from_dict()` used `bool()` for `duplicatesAllowed`, so the text
   `"false"` became `True`.
2. Add regression tests covering `"false"`, `"true"`, and invalid Boolean text.
3. The Human Code Maker paragraph overlapped the footer/page number in the
   reviewed user manual.

All three were accepted and resolved.

### 5B12 LAU CHUN LOK

1. Section 7 needed a sample terminal-output diagram showing guess history and
   feedback layout. This was accepted and resolved.
2. A broad launcher-level `try/except` was reviewed but not selected because the
   actual CLI entry point already handles `EOFError` and `KeyboardInterrupt`.
3. A second packaging file was reviewed but not selected because the full
   repository already has one authoritative `pyproject.toml`.

These comments are based on the submitted source files visible in the shared
`ICT_SBA_Learning_2526` folder on 2026-08-24. They are ready to enter in the
official review form and email to each code owner after confirmation.

## 5A4 CHIU LANG WEI — `5A_04_Chiu_Lang_Wei.py`

Code owner email: `s202101030@elearn.cccmkc.edu.hk`

1. **Colour-pool validation order (lines 190–200).** The code checks the length
   of `unique_colors` before removing invalid codes. For example, `RXYZ` has
   four unique characters and can pass the first length check, but filtering at
   line 198 leaves only `R`, so line 200 stores a pool that is shorter than the
   configured code length. Filter against `color_names` first, then validate the
   filtered list before assigning it to `config['colors']`. This prevents a
   custom setting from creating a misleading or impossible game.

2. **Unbounded attempts break score scaling (lines 63 and 167–169).** The
   settings menu accepts any positive `max_attempts`. When it is greater than
   800, `800 // max_attempts` becomes zero, so every winning attempt receives
   the same 1000 points. Restrict attempts to a documented range such as 1–20
   and use a proportional score formula that cannot collapse to a zero penalty.

3. **CSV formula injection risk (line 91).** `player_name` is written directly
   into CSV. A name starting with `=`, `+`, `-`, or `@` can be interpreted as a
   formula when the file is opened in spreadsheet software. Prefix dangerous
   values with an apostrophe or validate the first character before writing.

## 5C1 ALI WAH HIN — `sba code.py`

Code owner email: `s202101001@elearn.cccmkc.edu.hk`

1. **A no-duplicate game can become unwinnable (lines 98–110).** Calling
   `random.sample(available_colors, min(length, len(available_colors)))`
   silently returns a secret shorter than `CONFIG['code_length']` when the code
   length is larger than the colour pool. The win check still expects the full
   configured length, so the player can never win. Validate
   `length <= len(available_colors)` and reject the configuration instead of
   shortening the secret.

2. **Settings are committed without cross-field validation (lines 351–403).**
   Code length, colour count, and duplicate mode are updated separately. A user
   can select length 6, five colours, then enable no-duplicate mode. Build a
   candidate configuration first, validate all relationships, and only then
   replace `CONFIG`; otherwise keep the previous valid values and explain the
   conflict.

3. **One malformed score hides the whole leaderboard (around lines 165–198).**
   Rows with three fields are accepted, but the numeric score is converted only
   inside the sort key at line 184. A non-numeric score raises `ValueError` and
   the outer handler prints a general loading error, so valid rows are not
   shown. Convert and validate each score while reading, skip only the malformed
   row, and sort already-parsed integers.

## 5D9 LEUNG CHUN FUNG — `5D_09_Charlie_Leung_main.py`

Code owner email: `s202101134@elearn.cccmkc.edu.hk`

1. **Custom settings need complete bounds (lines 61–68).** The program checks
   only whether a no-duplicate length exceeds six. Zero or negative lengths and
   attempts are accepted, and any response other than `Y` silently means no
   duplicates. Add loops enforcing code length 3–6, attempts 1–20, and an
   explicit `Y`/`N` response before calling `play_game()`.

2. **Whitespace makes an otherwise valid guess fail (line 134).** The input is
   converted to uppercase but not stripped or tokenised. Typing `RBGY ` produces
   the wrong length, while `R B G Y` is also rejected even though spaced input
   is easier to read. Apply `.strip()` and normalise spaces, commas, and hyphens
   into one list of colour codes before length and colour validation.

3. **No in-game quit path or interruption handling (game loop beginning at
   line 132).** Once a game begins, the player cannot return to the menu without
   finishing every attempt, and Ctrl+C displays a traceback. Recognise `quit`
   before guess validation and catch `KeyboardInterrupt`/`EOFError` in the main
   entry point so the program exits cleanly without writing an incomplete CSV.

## 5C3 LAM SZE YUEN — `5C_3_Thomas_main_v1.py`

Code owner email: `s202101055@elearn.cccmkc.edu.hk`

1. **Invalid custom settings can crash the game (lines 159–166 and 96–103).**
   Custom mode allows five colours, a code length of six, and no duplicates.
   That configuration reaches `random.sample(colors, 6)` with only five
   colours and raises `ValueError` before play starts. When duplicates are
   disabled, validate that `code_length <= number_of_colors` and reprompt
   instead of returning the configuration.

2. **CSV text cleaning is incomplete (lines 215–230).** `clean_csv_text()`
   removes commas and newlines, but a player name beginning with `=`, `+`, `-`,
   or `@` may be interpreted as a formula when the CSV is opened in spreadsheet
   software. Reject these leading characters or prefix the stored value with an
   apostrophe.

3. **The manual run command does not match the uploaded file.** Section 4 tells
   the user to run `5C_3_LAM SZE YUEN_main.py`, but the shared file is named
   `5C_3_Thomas_main_v1.py`. Update the command and folder name to exactly match
   the submitted files, and add a short sample session or screenshot.

## 5B12 LAU CHUN LOK — `5B_12_Lau_Chun_Lok_main.py`

1. **One malformed CSV row hides the whole leaderboard (lines 145–163).**
   `view_leaderboard()` converts `row[2]` to `int` inside the sort key. If one
   row is incomplete or contains a non-numeric score, the broad exception
   handler displays only a loading error, so all valid scores disappear too.
   Validate each row while reading, skip only invalid rows, and sort already
   parsed integer scores.

2. **The player name is written directly to CSV (lines 107–121 and 272).** A
   name beginning with `=`, `+`, `-`, or `@` may be interpreted as a spreadsheet
   formula. Limit the name length and neutralise these leading characters before
   calling `writer.writerow()`.

3. **An invalid difficulty silently becomes Medium (lines 284–288).** A typo
   such as `4` gives no error and starts a different game. Reprompt until the
   user chooses 1, 2, or 3, display the confirmed preset, and rename the generic
   `User Manual Draft` file to the required class-number/name format.

## 5B10 FUNG YAT KIU — `5B_10_Fung_Yat_Kiu_main.py`

Code owner email: `s202101040@elearn.cccmkc.edu.hk`

1. **Invalid duplicate answers silently enable duplicates (lines 52–55).**
   `allow_duplicates` is calculated as `duplicates_input != 'n'`, so typos such
   as `no`, `x`, or `yes` become `True` without warning. Accept only `y`, `n`,
   or blank and reprompt for every other value.

2. **Maximum attempts has no upper bound (lines 42–48 and 169–170).** Any
   positive integer is accepted. A value such as 1,000,000 creates an extremely
   long game and permits a first-attempt score of 100,000,000. Enforce a
   documented range such as 1–20 or calculate scoring from a fixed difficulty
   scale.

3. **Prompts and manual packaging are inconsistent.** The colour prompt says
   4–10, while its error message says 5–10 (lines 24–27). Make both use the same
   range and add a replay/main-menu prompt after one game. Rename the manual so
   its extension matches its actual Microsoft Word format instead of ending in
   `.txt`, and include the exact run command and one example round.
