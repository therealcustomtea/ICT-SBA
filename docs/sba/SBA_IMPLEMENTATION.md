# Mastermind ICT SBA implementation

This document explains the school-facing Python work and how it grows into the Cipherboard market product. It is written so a Form 5 student can adapt it into an SBA report while still pointing to the real source code.

## 1. Problem definition

Mastermind is a code-breaking game. A Code Maker chooses a hidden sequence of colour identifiers. The Code Breaker submits guesses. After every valid guess the program reports:

- **black pegs**: correct colour in the correct position;
- **white pegs**: correct colour in the wrong position.

The difficult programming requirement is duplicate handling. One secret peg may produce at most one feedback peg, and an exact match must not also produce a white peg. The application must also validate input, stop at the correct time, calculate a reproducible score, and save local results.

## 2. Objectives

The SBA program must:

1. present a clear five-option menu;
2. support Easy, Normal, Hard, Expert, and Custom settings;
3. support computer and human Code Makers;
4. accept several readable input separators and a `quit` command;
5. reject invalid guesses without using an attempt;
6. show complete board history, feedback, and attempts remaining;
7. handle wins, losses, abandonment, end-of-input, and `KeyboardInterrupt`;
8. calculate `score_v1` consistently;
9. create, append, load, sort, and export UTF-8 CSV safely;
10. use the same tested rule package as the production API.

## 3. System decomposition

```text
mastermind_core
├── models.py       typed game configuration, state, attempts and feedback
├── presets.py      official settings
├── validation.py   input normalization and rule validation
├── feedback.py     duplicate-safe comparison
├── engine.py       secret generation, state and game operations
├── scoring.py      score_v1
└── daily.py        production daily derivation

mastermind_cli
├── __main__.py     python -m entry point
├── app.py          menu, game loop, and terminal output
└── storage.py      CSV file handling
```

The CLI contains input/output code. The core contains rules. This separation lets unit tests call the rules without pretending to type at a terminal.

## 4. Data representation

### Stable colour identifiers

The program stores `R`, `B`, `G`, `Y`, `W`, `K`, `O`, `P`, `C`, and `M`, not translated display names. A tuple stores the enabled palette because it has a fixed order and should not change during a game.

### Lists and tuples

- A guess begins as a list of tokens read from input.
- Validated codes become tuples so accidental mutation is less likely.
- Attempt history is a tuple of `AttemptRecord` values. Adding an attempt creates a new history rather than rewriting an old attempt.

### Dictionaries

Dictionaries represent versioned serialized settings and score breakdowns. For example:

```python
{
    'colours': ['R', 'B', 'G', 'Y', 'W', 'K'],
    'codeLength': 4,
    'maxAttempts': 10,
    'duplicatesAllowed': True,
}
```

### Dataclasses and enums

`GameConfig`, `Feedback`, `AttemptRecord`, `ScoreBreakdown`, and `GameState` are frozen dataclasses. They group related fields and validate their invariants. `GameMode`, `GameStatus`, `CodeMakerType`, and `GameVisibility` are enums, which prevent spelling variants such as `In Progress`, `in-progress`, and `active` from becoming different states.

### Database structures

The web API persists the same concepts in PostgreSQL. `game_sessions` stores one authoritative game and encrypted secret. `game_attempts` stores immutable valid guesses and feedback. A foreign key connects attempts to their game. Unique constraints on `(game_id, attempt_number)` and `(game_id, idempotency_key)` stop double submissions. The CLI does not need a database; it stores final local score rows in CSV.

## 5. Configuration validation

`GameConfig.__post_init__` enforces:

- 5–10 enabled colours;
- unique, known colour identifiers;
- code length 3–6;
- maximum attempts 1–20;
- enough colours for a no-duplicate code;
- legacy time bonus cap 0–3600 seconds (serialized for compatibility, not points).

The four official presets are constants created through this same validation, so a preset cannot bypass the normal rules.

## 6. Input normalization

The following input forms:

```text
R B G Y
r,b,g,y
R-B-G-Y
```

all normalize to:

```python
('R', 'B', 'G', 'Y')
```

### Pseudocode

```text
FUNCTION normalize_code(input)
    remove leading and trailing spaces
    IF input is empty THEN report EMPTY_GUESS
    IF lowercase input is "quit" THEN report QUIT_REQUESTED
    IF separators are malformed THEN report MALFORMED_GUESS
    split using spaces, commas, or hyphens
    convert every token to uppercase
    RETURN tuple of tokens
END FUNCTION
```

`validate_code` then checks exact length, enabled identifiers, and the duplicate rule. It returns before the engine creates an `AttemptRecord`, so invalid input cannot consume a turn or affect score.

## 7. Duplicate-safe feedback algorithm

The implementation in `packages/mastermind_core/mastermind_core/feedback.py` is a pure function:

```python
def calculate_feedback(secret, guess):
    if len(secret) != len(guess):
        raise DomainError(...)
    black = 0
    unmatched_secret = []
    unmatched_guess = []
    for secret_peg, guess_peg in zip(secret, guess, strict=True):
        if secret_peg == guess_peg:
            black += 1
        else:
            unmatched_secret.append(secret_peg)
            unmatched_guess.append(guess_peg)
    secret_counts = Counter(unmatched_secret)
    guess_counts = Counter(unmatched_guess)
    white = sum((secret_counts & guess_counts).values())
    return Feedback(black=black, white=white)
```

The `Counter` intersection keeps the smaller count for each colour. Exact matches were removed first, so they cannot be counted again.

### Worked example

Secret: `R B R G`
Guess: `R R B Y`

1. Position 1 is exact: 1 black.
2. Unmatched secret: `B R G`.
3. Unmatched guess: `R B Y`.
4. Both contain one `R` and one `B`: 2 white.
5. Result: **1 black, 2 white**.

### Complexity

Let `n` be code length.

- The position loop is `O(n)`.
- Building both counters is `O(n)`.
- Counter intersection visits at most the enabled colour count, which is bounded by `n` for the compared values.
- Overall time is `O(n)` and additional space is `O(n)`.

A double nested scan would be `O(n²)` and would make duplicate bookkeeping more error-prone.

## 8. Game state and loop

Only these transitions are accepted:

```text
created → active
active → won
active → lost
active → abandoned
active → expired
```

Terminal states have no outgoing transition. `submit_guess` first checks that the state is active, validates both codes, calculates feedback, appends one immutable record, and determines whether the result is won, lost, or still active.

### CLI loop pseudocode

```text
display main menu
WHILE choice is not Exit
    IF Start game
        ask for preset or custom settings
        obtain or generate secret
        create active state
        WHILE state is active
            read guess
            IF quit THEN abandon and stop loop
            validate guess
            IF invalid THEN show precise error and continue
            submit valid guess through core engine
            display complete history and attempts remaining
        END WHILE
        display result and permitted secret
        calculate and append terminal result row
    ELSE IF View scores THEN load and sort CSV
    ELSE IF View rules THEN explain black/white feedback
    ELSE IF Export scores THEN write/copy the CSV export
    ELSE show invalid-menu error
END WHILE
```

## 9. Secret generation

Production calls `secrets.SystemRandom`. With duplicates enabled it chooses one enabled colour for each position. Without duplicates it samples distinct colours. Tests can inject `random.Random(seed)` so expected sequences are repeatable. Seeded generation is not used for ordinary production games.

Human Code Maker input follows the same validator. The CLI reads it through an obscured `getpass` prompt, then clears/separates the hand-off view before the Code Breaker begins. The production API encrypts it immediately and never returns it while active.

## 10. Scoring

`score_v1` awards zero for loss, abandonment, or expiry. A win receives:

```text
(maximum attempts - attempts used + 1) × 100
+ code length × 50
+ enabled colours × 20
+ 100 if duplicates are allowed
```

The result is clamped to zero. Under the same settings, one fewer attempt always adds 100 points. Elapsed time never awards points; the server uses it only after score and attempts to break leaderboard ties. The score still stores attempt, difficulty, time, total, and version fields separately, with `time` fixed at zero for serialized-record compatibility.

## 11. CSV file handling

The default CLI path is `data/high_scores.csv`. The header is:

```text
timestamp,player_name,mode,difficulty,code_maker,number_of_colours,code_length,duplicates_allowed,attempts_used,maximum_attempts,score,scoring_version,result
```

The file module:

- opens files with UTF-8 and `newline=''` for Python CSV correctness;
- creates the directory and header on first append;
- warns about and skips malformed legacy rows instead of crashing the menu;
- warns and returns to the menu when a score cannot be saved or exported;
- sorts deterministically by score descending, attempts ascending, then timestamp;
- neutralizes player values beginning with `=`, `+`, `-`, `@`, tab, or carriage return to prevent spreadsheet formula injection;
- never stores a secret code.

## 12. Sample interaction

```text
Mastermind
1. Start game
2. View local high scores
3. View rules
4. Export scores
5. Exit
Choice: 1

Difficulty: Normal
Available colours: R B G Y W K
Enter 4 pegs, or type quit.
Guess: R,R,R,R
Attempt  Guess               Black  White
      1  R R R R                 1      0
9 attempts remaining.
Guess: R G B W
Attempt  Guess               Black  White
      1  R R R R                 1      0
      2  R G B W                 1      2
8 attempts remaining.
```

Exact wording can be localized later; the data and state behavior remain the same.

## 13. Testing

Unit tests cover all mandatory examples, invalid lengths, unknown colours, duplicates disabled, preset/custom boundaries, deterministic RNG, legal and illegal transitions, exhaustion, final-attempt win, abandonment, attempt-based score ordering, elapsed-time score invariance, and score stability. Hypothesis generates valid duplicate combinations and verifies:

```text
0 ≤ black ≤ length
0 ≤ white ≤ length
black + white ≤ length
equal codes produce all black
same inputs always produce the same feedback
```

The pure core has a 95% branch-coverage gate. CLI tests cover normalization, menu input, obscured human-secret input, complete board rendering, EOF/interrupt handling, CSV creation, malformed-row warnings, save/export failures, sorting, and formula protection. API integration tests add authentication, encryption, idempotency, authorization, and transaction races around the same core.

## 14. Relationship to the complete product

The SBA CLI is not thrown away when the web product is built:

- both CLI and API import `mastermind_core`;
- the CLI demonstrates selection, iteration, functions, validation, dataclasses, file handling, and testing in an understandable form;
- the API adds managed authentication, PostgreSQL transactions, AES-GCM secret storage, daily HMAC derivation, real-time rooms, rate limits, and administration;
- the web adds touch/keyboard controls, localization, accessibility, PWA resilience, profiles, statistics, and social modes;
- the same `rules_v1` and `score_v1` identifiers connect all results.

This architecture demonstrates that the original computational solution is the foundation of a maintainable consumer product rather than a disconnected school mock-up.
