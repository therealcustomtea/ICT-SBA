# 1: Problem Definition

Mastermind is a deductive code-breaking game. A Code Maker selects a hidden ordered sequence of colour identifiers and a Code Breaker submits guesses. After each valid guess, the system returns black feedback pegs for correct colours in correct positions and white feedback pegs for correct colours in wrong positions. The computational challenge is not simply comparing two lists: duplicate colours must be counted once, invalid data must never alter the game, terminal states must stop accepting guesses, and the final result must be saved reliably.

Release 1.1.0 delivers this solution through a Python command-line interface (CLI) with offline play and the account-backed workflows available in the graphical product. The terminal application is intentionally understandable as an SBA program, but it is not a disposable prototype. It imports the same `mastermind_core` package as the production web API. This makes the CLI a compact demonstration of decomposition, selection, iteration, validation, structured data, file handling, testing, and defensive programming.

[[FIGURE:architecture.png|Figure 1. CLI-centred system architecture and shared canonical engine.]]

## 1.1: Background

The physical Mastermind board uses coloured pegs and small feedback pegs. Converting it into a CLI requires a stable text representation. The program uses the identifiers `R`, `B`, `G`, `Y`, `W`, `K`, `O`, `P`, `C`, and `M`. Interactive terminals style each letter in its matching colour, while the letter remains the authoritative value. A user may enter a compact code such as `RBGY` or a separated form such as `R B G Y`, `R,B,G,Y`, or `R-B-G-Y`; all valid forms become the same immutable tuple.

The first implementation boundary is between interaction and rules. `mastermind_cli.app` owns prompts, menus, and display. `mastermind_core` owns configuration invariants, code validation, feedback, state transitions, secret generation, and scoring. `mastermind_cli.storage` owns local CSV persistence. This separation reduces coupling: a change in terminal wording does not change the scoring formula, while a correction to feedback automatically benefits both the CLI and API.

The project is also designed for realistic failure. A user can mistype a menu option, submit a malformed guess, interrupt the program, provide a damaged CSV file, or export to an unavailable location. The CLI converts these conditions into clear messages and returns to a safe state rather than presenting an unhandled traceback.

## 1.2: Objective

The primary objective is to create a reliable, testable Mastermind system that can be operated entirely from a terminal. The completed CLI must:

- preserve the five original choices for local play, scores, rules, export, and exit, with option 6 opening online features;
- support Easy, Normal, Hard, Expert, and Custom configurations;
- support both computer and human Code Makers, hiding human secret input;
- normalize readable input formats and reject invalid guesses without consuming an attempt;
- calculate duplicate-safe black and white feedback;
- display a colour-assisted, letter-labelled attempt history and attempts remaining after every accepted guess;
- handle win, loss, abandonment, end-of-input, and keyboard interruption safely;
- calculate a reproducible, versioned score;
- create, append, validate, sort, and export UTF-8 CSV records; and
- reuse the canonical rule engine shared by the wider Cipherboard product;
- support account-backed games and history, daily puzzles, friend challenges, live duels, profiles, rankings, support, and authorized administration through the same API as the GUI; and
- protect sessions, preserve pending guesses across uncertain network responses, and expose language and accessibility preferences in the terminal.

Success is judged by observable behaviour and repeatable verification, not by the amount of code written. Each objective is traced to implementation and tests later in this report.

## 1.3: Minimum Expectations

The minimum viable system is a menu-driven Python program that generates a legal secret, accepts guesses, returns correct feedback, ends at the right time, and stores results. The delivered system exceeds this baseline through custom constraints, pass-and-play, hidden secret entry, immutable domain objects, versioned scoring, formula-injection protection, atomic exports, malformed-row recovery, a complete automated test suite, and cross-platform installers.

| Requirement | Minimum expectation | Delivered evidence |
|---|---|---|
| Gameplay | One working game loop | Presets, Custom, computer/human Code Maker |
| Validation | Reject wrong length | Empty, separator, palette, duplicate, and boundary checks |
| Feedback | Black and white counts | Linear duplicate-safe `Counter` algorithm |
| Persistence | Save a score | UTF-8 append, sorted read, safe atomic export |
| Reliability | Normal exit | `quit`, EOF, interrupt, disk and malformed-file handling |
| Online workflows | Account and multiplayer access | Shared API sessions, daily/friend challenges, duels, profile, support and admin menus |
| Quality | Automated checks | 142 Python tests passed; core coverage 99.72%; combined core/CLI coverage 75.87% |

## 1.4: System Development Cycle

Development followed an iterative cycle: define requirements, analyse constraints, design boundaries, implement, test, and evaluate. Rule and network failures prompted corrections. Section 7 records the safeguards; Appendix 9.2 shows the planned sequence.

# 2: System Analysis

System analysis identifies the technologies, interaction model, operating assumptions, and boundaries that shape the solution. The offline CLI requires no network or database. Online mode requires the existing FastAPI service, MongoDB replica set, and Redis; published privacy and terms text also requires the web service. The terminal is a second client of those services, so account records and server permissions remain consistent with the GUI. Browser installation, touch gestures, and page animation are presentation features; terminal interaction uses keyboard menus and static text.

## 2.1: Programming Language

Python 3.13.14 is the pinned project runtime. Python suits the task because its sequence operations, dataclasses, enums, standard-library CSV support, `Counter`, and testing ecosystem express the problem directly. Type annotations improve readability and allow mypy to detect mismatched values before execution. The project uses modern syntax such as `StrEnum`, `slots=True`, union types, and `zip(..., strict=True)`.

The language choice also supports safe standard-library components. `secrets.SystemRandom` supplies operating-system randomness for normal secret generation; `getpass` hides a human Code Maker's input; `csv.DictReader` and `DictWriter` preserve an explicit schema; `tempfile.mkstemp` and `os.replace` support atomic export. The program does not use `eval`, shell interpolation, or a custom CSV parser.

| Language feature | Application in this system | Benefit |
|---|---|---|
| Frozen dataclasses | Game configuration, state, attempts, score | Prevent accidental mutation |
| Enums | Mode, status, Code Maker, visibility | Prevent spelling-dependent states |
| Tuples | Palette, secret, guess, attempt history | Stable ordered values |
| Exceptions | Stable `DomainError` codes and messages | Separates invalid data from control flow |
| Protocol | Injectable random source | Secure production behaviour and deterministic tests |

## 2.2: User Interface

The user interface is a conversational terminal menu. This matches the CLI focus and permits complete keyboard operation. The opening menu preserves choices 1–5 and adds option 6 for online features. The online menu provides 13 workflows, including a return to local play; option 0 goes back or exits. Prompts state valid ranges, and recovery messages explain the correction needed. During a game, a fixed-width attempt table exposes number, guess, black feedback, white feedback, and attempts remaining.

The terminal interface does not rely on colour alone. Pegs retain stable letters, while ANSI styling lets many players scan the palette and history more quickly. White and black identifiers use contrasting backgrounds. Redirected output, `TERM=dumb`, and `NO_COLOR` remain plain text, and `FORCE_COLOR` provides an explicit override. Human secret input uses `getpass`, and forty blank lines separate the Code Maker hand-off from the Code Breaker view. Although this is not as strong as a separate device, it is appropriate for local pass-and-play.

[[FIGURE:terminal_menu.png|Figure 2. Menu, invalid-choice recovery, and rules output.]]

## 2.3: Integrated Development Environment (IDE)

The program is editor-independent. Development can be completed in Visual Studio Code, PyCharm, or another Python-capable IDE because the repository defines its environment in `pyproject.toml`, `.python-version`, and `uv.lock`. `uv sync --frozen --all-extras` installs the exact development dependencies; `uv run` executes commands inside the project environment.

Useful IDE features include type-aware navigation, test discovery, breakpoint debugging, and integrated terminals. However, the authoritative checks are command-line commands that also run in GitHub Actions: Ruff formatting and linting, mypy strict type checking, pytest, and branch coverage. This prevents a local IDE setting from becoming an undocumented requirement.

# 3: Problem Analysis

The original example structure uses timetable terminology. To retain every required heading without misrepresenting this project, this section maps each timetable term to its Mastermind equivalent. A timetable row becomes an attempt row; teacher assignment becomes role assignment; subject selection becomes difficulty selection; classroom generation becomes game-session generation; and timetable regeneration becomes replay with a new secret.

## 3.1: Timetable Composition

In this Mastermind adaptation, “timetable composition” means the composition of one complete game board over time. Each row contains an attempt number, ordered guess, black count, white count, and submission time. Rows are append-only and retain chronological order. The configuration determines the number of columns in the logical code and the maximum number of attempt rows.

The CLI reconstructs the visible board from `GameState.attempts` after every accepted guess. It does not maintain a second display-specific history that could disagree with the engine. This is a useful invariant: the same tuple that is scored and tested is the tuple printed to the player.

## 3.2: General Parameters

General parameters define the legal game space. The palette contains 5–10 unique identifiers; code length is 3–6; maximum attempts is 1–20; duplicates may be allowed or forbidden; and the Code Maker may be a computer or human. Offline scores stay in CSV and do not enter the server leaderboard. Online mode submits difficulty, visibility, and configuration to the API, which decides ranking eligibility; the terminal cannot award itself a ranked result.

| Parameter | Type | Valid values | CLI source |
|---|---|---|---|
| Enabled colours | tuple of strings | 5–10 unique known IDs | preset or custom prompt |
| Code length | integer | 3–6 | preset or custom prompt |
| Maximum attempts | integer | 1–20 | preset or custom prompt |
| Duplicates | Boolean | yes/no | preset or custom prompt |
| Code Maker | enum | computer/human | preset defaults or custom prompt |
| Difficulty label | string | easy/normal/hard/expert/custom | menu selection |

## 3.3: Teacher Parameters

“Teacher parameters” are mapped to role and authority parameters. The Code Maker owns the secret; the Code Breaker owns guesses. When the computer is Code Maker, the engine generates the secret through `SystemRandom`. When a human is Code Maker, the same `validate_code` function checks the hidden entry before the device is handed over.

The separation prevents authority leakage. The Code Breaker never receives the secret through normal output while the game is active. Online authority additionally belongs to the API: access tokens identify the player, ownership checks isolate games and challenges, and administrator grants and MFA protect moderation. Duel snapshots expose only the permitted opponent progress. The CSV record intentionally excludes the secret. Only a lost game reveals the code, because no further competitive attempt can occur. A won game does not need to reveal it because the successful final guess already shows the sequence.

## 3.4: Timetable Illustration

The terminal attempt table is the timetable illustration for this project. A valid guess creates exactly one new row. An invalid guess creates no row and does not reduce `attempts_remaining`. The full history is printed rather than only the newest attempt, so the player can compare patterns and reason deductively.

[[FIGURE:terminal_game.png|Figure 3. Example attempt history and completed game.]]

## 3.5: Constraints

Constraints protect both the rules and data integrity. Configuration constraints are enforced when `GameConfig` is constructed, so invalid presets cannot exist. Guess constraints are enforced before an `AttemptRecord` is created. State constraints reject attempts after a terminal result. Persistence constraints require the full CSV header and parse each row defensively.

The most important gameplay constraint is single-use feedback: one secret peg can contribute to at most one black or white peg. Exact matches must be removed before colour-only matches are counted. Other important constraints include no duplicate palette identifiers, enough colours when repetition is forbidden, a stable score version, and no secret in local score data.

## 3.5.1: Constraint Simplification

Complex rules are simplified into layered checks. `normalize_code` handles representation; `validate_code` handles game-specific legality; `submit_guess` handles state and transition; `calculate_feedback` handles comparison; and `calculate_score` handles terminal points. Each function has one clear reason to reject data.

This layering makes proofs and tests smaller. For example, `calculate_feedback` can assume two equal-length sequences because the engine validates them first, yet it still contains its own length guard for direct callers. The overall behaviour becomes a composition of simple invariants rather than one long function with nested conditions.

[[FIGURE:validation_flow.png|Figure 4. Layered validation flow; rejected guesses consume no attempt.]]

## 3.6: IPO Cycle

The Input-Process-Output cycle describes the program independently of implementation details. Inputs include menu choices, player name, configuration values, secret entry, guesses, and export path. Processing includes normalization, constraint checking, secure generation, feedback, state transition, scoring, sorting, and file writing. Outputs include rules, validation messages, attempt history, terminal result, high-score table, and CSV export confirmation.

[[FIGURE:ipo_cycle.png|Figure 5. Input-Process-Output cycle for one accepted attempt.]]

## 3.6.1: Command Inputs

Command inputs are line-oriented strings. `.strip()` removes accidental surrounding spaces, `.casefold()` supports case-insensitive commands, and numeric prompts convert with `int` inside a retry loop. Guess input accepts letters without separators or tokens separated by whitespace, commas, or hyphens. A case-insensitive `quit` command abandons the active game.

Input functions are injected into `MastermindCLI`, which is significant for testability. Production uses `input` and `getpass`; tests supply deterministic callables. This avoids patching the entire terminal and makes every prompt path reproducible.

## 3.6.2: Terminal Outputs

Output is also injected. Production uses `print`; tests append each message to a list. The CLI uses safe user-facing `DomainError.message` values rather than tracebacks or internal object representations. Tabular rows calculate padding from the unstyled guess, so invisible ANSI control sequences cannot shift the Black and White columns.

`terminal.py` maps all ten identifiers to readable ANSI styles and resets formatting after every letter. Capability detection enables styling only for an interactive stream, unless `FORCE_COLOR` is set. `NO_COLOR` and `TERM=dumb` take priority. This keeps saved logs, pipes, automated tests, and assistive text workflows free of control sequences.

Output follows progressive disclosure: the main menu is short, rules are shown on request, game parameters appear once a session begins, history appears after accepted attempts, and a warning appears only when persistence fails. This keeps routine play readable while retaining diagnostic information.

## 3.6.3: CSV Export

CSV export reads the validated local records, writes them to a temporary file in the destination directory, flushes and synchronizes the file, and then atomically replaces the requested target. If writing fails, the temporary file is removed and the old destination remains intact. Values beginning with spreadsheet formula markers are prefixed with an apostrophe.

The export always writes the canonical 13-column header even when there are no records. This produces a useful empty dataset and simplifies downstream processing. The default path is `mastermind_scores.csv`, but the user may enter another path.

[[FIGURE:csv_pipeline.png|Figure 6. Defensive local persistence and atomic export pipeline.]]

## 3.6.4: Report Output

The principal operational report is the local high-score view. Records are sorted by score descending, attempts ascending, then timestamp ascending. The first twenty are printed with rank, player, difficulty, score, and attempt usage. CSV export provides the detailed machine-readable report with configuration and scoring version.

This SBA document is a second report output: it connects requirements, design, source evidence, tests, and evaluation. Terminal examples, source excerpts, and charts are generated from repository code or measured verification results. Source figures retain line numbers and omit full-line comments for readability; terminal examples illustrate deterministic test scenarios. The figures can be reproduced from the accompanying generator.

## 3.7: Modularization

The solution is modularized around dependency direction. `mastermind_cli.app` depends on the public exports of `mastermind_core` and on `CSVScoreStore`. The core never imports the CLI or file system. Within the core, `engine.py` coordinates models, validation, feedback, and scoring; it does not duplicate their logic.

Online interaction is separated into `online.py` and `online_client.py`. The first owns terminal workflows; the second owns HTTP sessions, private state, exports, and WebSocket connections. `localization.py` supplies Traditional Chinese prompts for the offline controller. Both local and online workflows use `terminal.py` for readable pegs. The online controller sends actions to the API rather than duplicating server scoring, database access, or permission decisions.

[[FIGURE:module_graph.png|Figure 7. CLI and canonical-core module relationship graph.]]

# 4: Program Design

Program design translates the analysis into components, flows, and data contracts before implementation details are considered. The design uses a controller (`MastermindCLI`), a pure domain package (`mastermind_core`), and a local repository adapter (`CSVScoreStore`).

[[FIGURE:cli_flow.png|Figure 8. Top-level menu and control-flow design.]]

## 4.1: Pre-generation Design

Pre-generation covers everything required before an active code-breaking loop begins: capture the player name, choose a preset or custom configuration, validate all settings, determine the Code Maker, obtain or generate a legal secret, and create an active state. Failure in this stage returns a clear message without creating a partial score record.

## 4.1.1: Configuration Design

Official settings are stored as `GameConfig` constants in a dictionary keyed by normalized difficulty name. Every preset is constructed through the same `__post_init__` validation used for Custom mode. Custom mode prompts for colour count, code length, maximum attempts, duplicate policy, and human/computer Code Maker. Custom games are marked unranked.

[[FIGURE:presets_chart.png|Figure 9. Attempt limits across the four official presets.]]

| Preset | Colours | Code length | Attempts | Duplicates | Ranked |
|---|---:|---:|---:|---|---|
| Easy | 5 | 4 | 12 | No | Yes |
| Normal | 6 | 4 | 10 | Yes | Yes |
| Hard | 8 | 5 | 8 | Yes | Yes |
| Expert | 10 | 6 | 8 | Yes | Yes |

## 4.1.2: Input Validation

Validation is designed as a retryable boundary, not a reason for the program to terminate. `_number` loops until an integer falls within the permitted range. `_yes_no` accepts `y`, `yes`, `n`, or `no` after stripping and case folding. A human secret loops until it passes the same code validator used for guesses.

Guess validation is deliberately completed before feedback or attempt construction. This guarantees that malformed separators, wrong length, unknown colours, or prohibited duplicates cannot consume an attempt. Stable error codes make the same rule usable through API boundaries, while the CLI displays concise messages.

[[FIGURE:code_validation.png|Figure 10. Source excerpt: normalization and validation functions.]]

## 4.2: Generation Design

Generation is the active game phase. The state begins as `CREATED`, immediately transitions to `ACTIVE`, and accepts guesses until it reaches `WON`, `LOST`, or `ABANDONED`. Each accepted guess produces a new immutable `GameState` rather than modifying the old one.

## 4.2.1: Teacher Assignment

The required “Teacher Assignment” heading maps to role assignment. The design assigns Code Maker authority from configuration: official presets use the computer; Custom may select a human. The Code Breaker role is the player submitting guesses. This explicit role model avoids ambiguous Boolean flags scattered through the game loop.

`CodeMakerType` is an enum, and `GameMode` records whether the game is solo or pass-and-play. Role assignment therefore becomes a typed domain decision that is also persisted in the score record.

## 4.2.2: Subject Selection

“Subject Selection” maps to selecting the problem difficulty. The CLI shows four official presets and Custom. A dictionary converts menu numbers to preset names, while `get_preset` normalizes the name and raises `UNKNOWN_DIFFICULTY` for invalid direct calls.

The design keeps user-facing selection separate from configuration values. This prevents a menu branch from reimplementing palette sizes or attempt counts. One authoritative preset table supports the CLI, tests, and wider product.

## 4.2.3: Classroom Generator

“Classroom Generator” maps to creating a game session. `create_game(config, mode)` constructs a `GameState` and performs the only legal `CREATED -> ACTIVE` transition. It also records the start timestamp used for persisted timing information, although elapsed time does not award score points.

The function is intentionally small because configuration validation already occurred in `GameConfig`. This demonstrates design by contract: a valid configuration enters the engine, and an active immutable state leaves it.

## 4.2.4: Undo Design

The CLI does not provide an undo command for accepted guesses. This is a deliberate integrity rule: feedback changes the player's knowledge, so removing an attempt would allow trial information without cost. The immutable attempt tuple also makes silent deletion unnatural.

Before submission, the player can correct terminal text normally. Invalid submissions are not accepted and therefore do not need undo. Abandonment is explicit and produces zero score. A future practice-only undo could be implemented by creating a new state marked unranked, but it must never alter official results.

## 4.2.5: Teacher Generator

“Teacher Generator” maps to secret generation. `generate_secret` accepts a `GameConfig` and optional random-source protocol. With duplicates allowed, it chooses independently for each position. Without duplicates, it samples distinct colours. Production defaults to `secrets.SystemRandom`; tests inject a seeded generator for repeatability.

Human-generated secrets pass through `validate_code`. Both paths therefore guarantee correct length, known colours, and compliance with the duplicate rule before play begins.

## 4.3: Post-generation Design

Post-generation begins when the state becomes terminal. The CLI prints the outcome, calculates or reads the terminal score, constructs a 13-field `ScoreRecord`, and attempts to append it. Persistence failure produces a warning but does not erase the completed game experience.

## 4.3.1: Printing and Exporting

Printing uses the state as the source of truth. Win text reports attempts used; loss text reveals the secret; abandonment states that no score was awarded. Every case prints the numerical score. The detailed record is then available to the high-score view and export operation.

Atomic export is a stronger design than copying the source file directly. It produces a complete new file before replacing the destination, preventing a crash from leaving a half-written report.

## 4.3.2: Summary Data

Summary data contains player name, mode, difficulty, Code Maker, colour count, code length, duplicate policy, attempts used, maximum attempts, score, scoring version, result, and UTC timestamp. It excludes the secret and the full guess history because neither is required for local ranking.

The schema supports fair comparisons and later analysis. A future migration can distinguish scoring versions rather than mixing results calculated by different formulas.

## 4.3.3: Timetable Re-generation

“Timetable Re-generation” maps to starting another game. Returning to the menu and selecting Start creates a fresh configuration, secret, and state. Previous state is not mutated; only its terminal summary remains in CSV.

Fresh generation is important for computer Code Maker games because ordinary play must not reuse a predictable seed. Pass-and-play intentionally allows a new human secret. Regeneration is therefore a new session, not an undo of the former session.

## 4.4: Overall Design

The overall design can be summarised as “functional core, imperative shell.” The core receives values and returns validated values or new state. The CLI shell performs input/output. The storage adapter performs file effects. Dependency injection supplies input, secret input, output, store, and random source for tests.

[[FIGURE:state_machine.png|Figure 11. Legal game-state transitions.]]

This structure produces maintainability and confidence. Pure rule functions are easy to test exhaustively; terminal integration is tested with scripted input; file handling is tested in temporary directories. The same core can be reused by another interface without translating the rules.

# 5: Design Implementation

Implementation converted the design into three cooperating Python areas: `mastermind_core` for rules and immutable state, `mastermind_cli.app` for the interaction loop, and `mastermind_cli.storage` for local records. The implementation favours explicit values over hidden side effects. A game transition returns a new state; a rejected guess raises a stable domain error; and storage is called only after the result is known.

The source is packaged rather than run as a loose script. The entry point parses arguments and launches `MastermindCLI` or, with `--online`, `OnlineCLI`; project metadata supplies both `mastermind` and `cipherboard` commands. This permits the same code to run in development, automated tests, and packaged desktop installations without changing imports.

## 5.1: Initialization

Initialization occurs at two levels. Package initialization exports the public domain API from `mastermind_core.__init__`, so consumers do not depend on private module paths. Runtime initialization constructs a `MastermindCLI` with default terminal input, hidden secret input, printed output, and a CSV store at `data/high_scores.csv`. Tests replace those dependencies with in-memory callables and temporary paths.

The first visible action is printing `Mastermind Logic Lab`, followed by the menu. Selecting Start performs a second, game-specific initialization: name, configuration, secret, mode, active state, and attempt history. No result file is created merely by launching the program; it is created only when the first terminal result is appended.

## 5.1.1: Data Structures

The central data structures are frozen dataclasses with slots. Freezing prevents accidental field assignment, and slots prevent unplanned attributes. Tuples preserve order while making palettes, guesses, and histories immutable. Enums restrict status and role fields to known values.

[[FIGURE:data_model.png|Figure 12. Core data model and relationships used by the CLI.]]

| Structure | Important fields | Responsibility |
|---|---|---|
| `GameConfig` | colours, length, attempts, duplicate rule, Code Maker | Defines and validates the legal game space |
| `Feedback` | black, white | Stores one bounded comparison result |
| `AttemptRecord` | number, guess, feedback, timestamp | Represents one accepted guess |
| `ScoreBreakdown` | attempts, difficulty, time, total, version | Makes scoring auditable |
| `GameState` | config, mode, status, attempts, timestamps, score | Holds the complete rule-engine state |
| `ScoreRecord` | 13 serializable summary fields | Defines the local persistence schema |

`GameState.attempts_used` and `attempts_remaining` are calculated properties rather than separately stored counters. This eliminates a possible inconsistency between history length and displayed allowance. Likewise, `GameStatus.terminal` derives terminal membership from the enum rather than asking callers to repeat four comparisons.

## 5.1.2: Global Variables

Module-level constants are used only for stable policy and schema: `COLOUR_IDS`, `RULE_SET_VERSION`, `SCORING_VERSION`, `CSV_FIELDS`, the official preset table, and rule text. Mutable game state is not global. Each `play_game` call keeps its own local `state` and `secret`, so a completed or abandoned game cannot leak attempts into the next session.

The constants serve as single sources of truth. `COLOUR_IDS` controls palette membership, `CSV_FIELDS` controls both append and export order, and version constants identify the rule and score interpretations. This is safer than scattering literal strings or column lists through menu branches.

## 5.1.3: Configuration File

Project configuration is declared in `pyproject.toml`. It defines release 1.1.0, Python 3.13 compatibility, workspace packages, CLI and GUI executables, linting, type checking, tests, and optional dependencies. Online transport uses the pinned `httpx` and `websockets` packages. `.python-version` selects the development interpreter, while `uv.lock` fixes transitive versions for reproducible installation.

Runtime game configuration is represented by `GameConfig`, not an editable external file. This is intentional: its `__post_init__` method normalizes colours and rejects invalid colour counts, duplicate palette choices, unknown identifiers, illegal lengths, attempt limits, insufficient unique colours, and invalid time-bonus bounds. Presets are therefore executable, validated configuration rather than unverified text.

| Configuration concern | File or object | Validation point |
|---|---|---|
| Python/dependencies | `pyproject.toml`, `uv.lock` | `uv sync --frozen` |
| Installable commands | project script entries | build/install verification |
| Test/lint/type policy | `pyproject.toml` | pytest, Ruff, mypy |
| Game rules | `GameConfig` and presets | dataclass construction |
| Local score location | `CSVScoreStore.path` | parent creation on append/export |

## 5.2: Classes

`MastermindCLI` is the application controller. Its constructor accepts normal input, hidden input, output, a score store, and an optional colour-output override. Its methods correspond to user tasks rather than low-level rules: run the menu, play a game, build Custom configuration, show scores, and export scores. Helper methods handle repeated numeric and yes/no prompting.

[[FIGURE:code_cli_menu.png|Figure 13. Source excerpt: accessible ANSI capability detection and peg formatting.]]

`CSVScoreStore` is a repository adapter. It has `append`, `read`, and `export` operations and owns every CSV-specific detail. `ScoreRecord` is its typed transfer object. Neither class knows how feedback is calculated.

Domain dataclasses are intentionally behaviour-light. `GameConfig` enforces construction invariants; `GameState` exposes derived attempt counts and legal transitions. Rule functions then operate on these values. This balance avoids a monolithic “Game” class while keeping invariants close to their data.

## 5.3: Libraries

Offline gameplay and CSV handling rely on the Python standard library. Online mode adds the project's pinned HTTP and WebSocket dependencies so it can reuse the existing service contracts.

| Library/module | Use | Reason for selection |
|---|---|---|
| `collections.Counter` | Count unmatched colours | Correct linear-time duplicate handling |
| `secrets.SystemRandom` | Generate computer secrets | Operating-system randomness rather than a predictable default PRNG |
| `dataclasses` | Typed immutable records | Compact, inspectable domain models |
| `enum.StrEnum` | Status, mode, role, visibility | Restricted values that serialize clearly |
| `csv` | Read/write local scores | Standards-aware quoting and newline handling |
| `tempfile` and `os` | Safe export and durable flush | Temporary creation, `fsync`, atomic replacement |
| `getpass` | Hide human Code Maker input | Prevent secret echo in normal terminals |
| `pathlib` | Cross-platform paths | Avoid manual path-separator logic |
| `httpx` | HTTP sessions, cookies and protected downloads | Bounded requests without following redirects |
| `websockets` | Live duel client | Synchronous transport with bounded reconnect |
| `pytest` | Automated verification | Fixtures, parameterization, temporary directories, clear failures |

Ruff and mypy are development tools rather than runtime dependencies. Ruff checks style and likely defects; mypy checks the typed contracts. `uv` resolves and runs the environment consistently across macOS, Windows, local development, and CI.

## 5.4: Functions

Functions are grouped by lifecycle: pre-generation functions collect or validate setup; generation functions create secrets, evaluate guesses, and transition state; post-generation functions calculate results and persist summaries; the main function coordinates the terminal session. Pure functions are kept independent of printing and file access so their inputs and outputs can be tested directly.

## 5.4.1: Pre-generation Functions

`normalize_code` accepts a string or sequence. For strings, it trims whitespace, recognizes comma, hyphen, or whitespace separators, and otherwise treats each character as one colour identifier. It uppercases every token and returns a tuple. This means `rbgy`, `R B G Y`, and `r,b,g,y` converge on one representation.

`validate_code` calls normalization and then checks length, palette membership, and the duplicate rule. It raises a `DomainError` containing a stable code and a safe message. `_number` and `_yes_no` implement similar retry boundaries for Custom settings. `get_preset` looks up authoritative validated configurations instead of rebuilding them inside the CLI.

The pre-generation contract is simple: no `GameState` is created until all configuration and secret requirements pass. As a result, later functions can operate on a valid configuration and a legal secret.

## 5.4.2: Generation Functions

`generate_secret` receives a configuration and an optional random-source protocol. It uses independent choices when duplicates are allowed and sampling when they are forbidden. Tests inject deterministic randomness, while ordinary play uses `SystemRandom`.

`calculate_feedback` first marks exact position matches. It then counts only the unmatched secret and guess colours and sums the minimum occurrence count for each colour. Removing black matches before `Counter` intersection is the key to avoiding double counting.

[[FIGURE:code_feedback.png|Figure 14. Source excerpt: duplicate-safe black and white feedback.]]

[[FIGURE:feedback_walkthrough.png|Figure 15. Worked feedback example showing exact-match removal before colour counting.]]

If the secret is `R R B G` and the guess is `R B R Y`, position 1 is black. The unmatched secret contains `R, B, G`; the unmatched guess contains `B, R, Y`. Their count intersection contains one `R` and one `B`, producing two whites. The result is therefore 1 black and 2 white, never 1 black and 3 white.

`submit_guess` is the transactional rule boundary. It rejects non-active state, validates the guess, calculates feedback, appends a numbered and timestamped record, determines whether the result is won or lost, and attaches a score only for terminal state. Because the original dataclass is frozen, the function uses `replace` to return a new state.

[[FIGURE:code_submit_guess.png|Figure 16. Source excerpt: accepted-guess transaction and terminal-state selection.]]

Scoring is versioned as `score_v1`. A non-win is zero. A win receives an attempts component of `(maximum attempts - attempts used + 1) × 100`, plus a difficulty component of `code length × 50 + colour count × 20 + 100 when duplicates are allowed`. Time is stored for compatibility but awards no points, which avoids favouring faster typists over careful reasoning.

[[FIGURE:scoring_chart.png|Figure 17. Score composition for representative preset wins.]]

## 5.4.3: Post-generation Functions

At terminal state, the CLI prints a status-specific message and score. It constructs `ScoreRecord.now(...)` with UTC timestamp, mode, difficulty, Code Maker, configuration summary, attempts, score version, and result. `CSVScoreStore.append` creates the parent directory, writes a header when needed, sanitizes spreadsheet-formula prefixes, flushes, and calls `fsync`.

[[FIGURE:code_storage.png|Figure 18. Source excerpt: CSV sanitization, defensive reading, and atomic export.]]

`read` verifies the header before parsing. Each malformed row is skipped with a runtime warning rather than preventing all valid rows from loading. Records are sorted deterministically. `export` writes the canonical header and validated records to a temporary sibling file, synchronizes it, and calls `os.replace`. If any exception occurs, it removes the temporary file and preserves the former destination.

## 5.4.4: Main function

The installed entry point parses `--online`, `--api-url`, `--product-origin`, `--state-dir`, `--allow-http`, and `--locale`. It constructs the offline controller with a callback for option 6, or starts the online controller directly. The local loop preserves choices 1–5 and Exit returns status code 0. A game returns to the same menu after success, loss, abandonment, or a recoverable save warning.

The executable wrapper catches end-of-input and keyboard interruption at the process boundary. This is the correct layer because these signals may arrive at any prompt. Normal menu and rule methods remain focused on application behaviour rather than duplicating process-level exception handling.

The following pseudocode summarizes the implementation:

```text
main
    construct CLI with terminal and CSV dependencies
    repeat
        print menu and read choice
        if Start: configure, generate, play, score, save
        if Scores: read, sort, print first 20
        if Rules: print rules
        if Export: validate records, write atomic CSV
        if Exit: return success
        if Online: open the authenticated online menu
        otherwise: explain valid range
```

## 5.5: Online CLI Implementation

`OnlineCLI` organizes server-backed actions into numbered submenus. `OnlineClient` performs HTTP requests and refresh-token rotation; `ClientState` stores per-server state; `DuelConnection` handles real-time transport. The GUI and CLI use the same endpoints, accounts, ranking rules, and administrative checks. Browser layout and installation are outside terminal feature parity.

| GUI workflow | CLI equivalent | Authority and persistence |
|---|---|---|
| Solo, practice, Custom and pass-and-play | Play menu; hidden human-secret entry | API creates and validates games |
| History and resume | Paginated history; open by game ID | Owner-only server history |
| Daily puzzle | Official run, resume, practice and daily board | API enforces one official run per UTC day |
| Friend challenge | Create, share code, play, creator results, revoke | Server checks challenge ownership |
| Duel room | Create/join, ready, guess, back, retry, abandon | Server room state and durable events |
| Profile and rankings | Rename, opt in, stats, achievements, filters | API controls public data and personal rank |
| Account | Guest, email upgrade/login, MFA, ZIP export, delete, logout | Existing authentication and recent-login rules |
| Settings and support | Languages, theme, patterns, sound, consent, support | Private preferences and confirmed API actions |
| Administration | Lists, summaries, flags, moderation, audit | Existing administrator grant and MFA required |
| Rules and policies | Rules menu and readable published pages | Web origin supplies current policy text |

**Session handling.** The CLI keeps access tokens in memory and writes the refresh cookie, preferences, pending guesses, and room sequence cursors to a private per-server JSON file. POSIX permissions are 0600 for the file and 0700 for its directory. A cross-process lock avoids simultaneous refresh rotation; a second player uses a different `--state-dir`. Writes use a temporary file and atomic replacement. Server-generated secrets and MFA setup keys are not saved there.

**Network boundaries.** Remote origins require HTTPS unless the user explicitly enables a trusted development-network exception. Redirects are not followed. Email links may use either the configured API origin or the public issuer advertised by that API; the token is submitted only to the configured API. Issuer metadata is used to recognize the callback URL, not to grant authentication. Error text is stripped of terminal control characters before display.

**Reliable mutations.** Before sending a guess, the client saves its idempotency key and body. A lost response leaves that record pending; `retry` sends the same key. A definite rejection clears the pending record so the player can correct the guess. Creation retries also retain their original key. `back` preserves a resumable game; confirmed `abandon` ends it. Local CSV scores and server rankings remain separate records.

**Real-time rooms.** A short-lived one-use ticket authorizes the WebSocket. A receiver thread processes events while the main thread waits for input, and an independent heartbeat keeps presence alive. On reconnect, a fresh ticket and last durable sequence request replay. Opponent guesses remain private until the server permits disclosure. Consecutive reconnect failures are bounded, and leaving a room closes its threads and socket.

**Accessibility.** English and Traditional Chinese are selectable. Light, dark, and plain themes, pattern numbers, high contrast, and optional terminal sound adapt output without hiding letter identifiers. Motion is static. Analytics are disabled by default and only send allowlisted, consented event properties without guesses or secrets.

# 6: Testing & Evaluation

Testing covers environment and boundary readiness, rule and integration correctness, and complete terminal workflows. On 25 November 2026, the release working tree based on `3924d86` passed all 142 Python tests in 27.736 seconds: 61 API, 45 core, 35 CLI, and one installer test. There were no failures, errors, or skipped Python cases. Branch-aware coverage was 99.72% for `mastermind_core` and 75.87% for the combined core and expanded CLI. Five deprecation warnings came from the existing Uvicorn WebSocket adapter. Ruff and mypy passed, with mypy checking 83 source files.

The suite used an isolated MongoDB replica set and Redis, with unique temporary test databases. Offline/controller and mocked-transport checks can run without services; real API and duel checks require them. `verification.json` records the command, package scope, counts, and measured module coverage used by the figures. `pnpm validate` also passed formatting, lint, type checks, 44 JavaScript unit tests (37 web and seven shared-package tests), and the production web build. These are current local results; browser end-to-end results from an earlier release are not counted as evidence for this release.

[[FIGURE:test_results.png|Figure 19. Measured verification result across the repository test suite.]]

## 6.1: Testing plan

The plan combines black-box and white-box techniques. Black-box cases exercise menu choices, valid and invalid user inputs, visible feedback, stored records, and exports. White-box cases target every branch in validation, feedback, state transitions, scoring, and persistence. Temporary directories isolate file tests; injected input and output isolate terminal tests; deterministic random sources isolate generation tests.

| Test level | Main purpose | Representative oracle |
|---|---|---|
| Import/configuration | Confirm environment and invariant construction | Import succeeds or stable error code appears |
| Unit | Verify one rule independently | Exact feedback tuple, state, or score breakdown |
| Integration | Verify components cooperate | Scripted CLI output and temporary CSV |
| Constraint | Prove invalid data cannot corrupt state | Same attempt count after rejection |
| System/output | Verify actual commands and artifacts | Exit code, table content, exported header |
| Acceptance | Judge task completion from player perspective | Complete game without technical knowledge |

Pass criteria were defined before interpretation: all focused core and CLI tests pass; Ruff reports no findings; mypy reports no errors; accepted inputs produce the expected state; rejected inputs preserve state; persistence either succeeds completely or reports a recoverable warning.

## 6.2: Testing Phase 1

Phase 1 verifies that the program can start in a controlled environment and that its outer boundaries reject invalid setup. This prevents later gameplay results from being confused with installation or configuration faults.

## 6.2.1: Library Import Test

The project environment was synchronized from the lockfile and the CLI/core modules were imported through pytest discovery. The complete suite collected and executed successfully. Ruff also resolved the same package structure, and mypy checked all 83 Python source files without errors.

| Case | Action | Expected | Observed |
|---|---|---|---|
| P1-01 | Import `mastermind_core` | Public models and functions available | Pass |
| P1-02 | Import `mastermind_cli` | CLI and storage exports available | Pass |
| P1-03 | Invoke module entry point | Menu begins without traceback | Pass through CLI tests |
| P1-04 | Run typed analysis | Package imports and annotations resolve | 83 files passed |

## 6.2.2: Configuration File Test

Configuration tests construct every official preset and invalid boundary combinations. The expected result is either a normalized immutable object or a specific `DomainError`.

| Case | Input | Expected result | Result |
|---|---|---|---|
| P1-05 | Easy, Normal, Hard, Expert | Valid documented values | Pass |
| P1-06 | 4 colours | `INVALID_COLOUR_COUNT` | Pass |
| P1-07 | repeated palette identifier | `DUPLICATE_COLOUR_OPTION` | Pass |
| P1-08 | code length 7 | `INVALID_CODE_LENGTH` | Pass |
| P1-09 | 21 attempts | `INVALID_MAX_ATTEMPTS` | Pass |
| P1-10 | 3 colours for length 4 without repeats | `INSUFFICIENT_UNIQUE_COLOURS` | Pass |

## 6.2.3: Command Input Test

Scripted callables supplied menu choices and guesses without requiring an interactive terminal. Tests confirm whitespace trimming, invalid-choice recovery, case-insensitive `quit`, default player name, and accepted guess notations. Output was collected as strings and compared with player-visible messages.

| Input | Classification | State effect |
|---|---|---|
| `RBGY` | valid compact code | one accepted attempt |
| `r b g y` | valid separated lowercase | normalized and accepted |
| `R,B,G,Y` | valid comma-separated | normalized and accepted |
| `R--B` | empty separated token | rejected, no attempt |
| `RBG` for length 4 | wrong length | rejected, no attempt |
| `quit` | abandonment command | terminal abandoned state |

## 6.2.4: Parameters Modification Test

Custom-mode tests modify colour count, length, attempts, repetition policy, and Code Maker. Boundary values 5/10 colours, 3/6 positions, and 1/20 attempts are accepted. Values immediately outside the range cause a retry. Yes/no input accepts full words and single letters but rejects ambiguous responses.

The most important combined case selects no duplicates with a human Code Maker. The hidden secret must be valid under the newly created configuration. This proves that parameter changes are used by subsequent validation rather than merely printed.

## 6.3: Testing Phase 2

Phase 2 verifies pure rules, local persistence, authenticated handlers, and online transport. The 142-test run measured branch-aware coverage across both core and CLI: core 99.72%, CSV storage 96.70%, terminal formatting 88.89%, offline controller 73.87%, online transport 78.86%, and online menus 59.33%. The combined value is 75.87%; adding substantial interactive code changes the denominator, so the earlier offline-only coverage percentage is not a comparable current result. The subprocess entry point is exercised, but its child-process execution is not included in the parent coverage file.

[[FIGURE:coverage_chart.png|Figure 20. Branch-aware coverage measured for the expanded core and CLI packages.]]

## 6.3.1: Unit Tests

Feedback unit tests cover all black, all white, mixed, no match, and duplicate-heavy cases. Validation unit tests cover each separator and error code. Engine tests cover secure generation rules, active-state requirements, immutable history growth, win, final-attempt win, loss, abandonment, and illegal terminal submissions. Scoring tests separately verify win components and zero-score statuses.

Examples of strong unit oracles include:

- secret `R B G Y`, guess `R B G Y` gives 4 black and 0 white;
- secret `R B G Y`, guess `Y G B R` gives 0 black and 4 white;
- secret `R R B G`, guess `R B R Y` gives 1 black and 2 white;
- a winning final attempt is `WON`, not `LOST`;
- a non-winning final attempt is `LOST` with zero score; and
- submission to a won, lost, or abandoned state raises an illegal-transition error.

## 6.3.2: Integration Tests

Integration tests instantiate `MastermindCLI` with scripted input, captured output, and a `CSVScoreStore` in `tmp_path`. They exercise the real controller rather than mocking the core. One scenario plays to a win and verifies the printed attempt table and saved result. Others test invalid setup, pass-and-play, score display, export, and storage warnings. Colour-specific cases verify all ten ANSI mappings, automatic terminal detection, `NO_COLOR`, `TERM=dumb`, `FORCE_COLOR`, plain fallback, and aligned history output.

[[FIGURE:terminal_tests.png|Figure 21. Terminal verification commands and observed pass counts.]]

This layer is essential because unit tests cannot detect a disconnected menu option, incorrect prompt loop, or omitted persistence call. Conversely, it remains deterministic because the secret input and storage location are injected.

## 6.3.3: Constraint Checking

Constraint checks test both boundaries and invariants after operations. The most important invariant is that an invalid guess leaves `attempts_used`, `attempts_remaining`, status, and history unchanged. Tests also confirm that feedback totals never exceed code length, white matches cannot reuse black matches, and generated secrets respect palette and duplicate rules.

For persistence, malformed headers yield an empty result with a warning, malformed rows are skipped individually, and export always contains the canonical header. Player names beginning with `=`, `+`, `-`, `@`, tab, or carriage return are escaped before spreadsheet use. These are integrity constraints, not cosmetic behaviours.

## 6.4: Testing Phase 3

Phase 3 evaluates complete outputs and user tasks. Its focus is not internal branches but whether a player can understand the program, complete a game, find the result, and reuse the recorded information.

## 6.4.1: Prints & Exports Tests

Print tests assert the preserved five choices and new online entry, rules text, coloured and plain configuration summaries, attempt-table labels and alignment, pluralization, terminal status message, score, and export confirmation. Export tests read the actual target with `csv.DictReader`, confirming a 13-column header and values that round-trip correctly.

The default export works with an empty store and still creates a usable header-only CSV. An explicit nested destination creates parent directories. A simulated failure leaves the previous destination intact and removes the temporary file. These behaviours make the output suitable for spreadsheet analysis without risking silent data loss.

## 6.4.2: Summary Report Test

The high-score summary is tested with multiple records. Expected ordering is score descending, attempts ascending, timestamp ascending. The display is limited to 20 records, names are truncated to protect table alignment, and an empty store prints `No local scores yet.`

The detailed CSV summary retains configuration context, so the same numerical score is not detached from difficulty or scoring version. It intentionally excludes the secret, which reduces privacy and fair-play risk.

## 6.4.3: Re-Generation Test

Re-generation is tested by starting new game sessions from the menu. Every call to `create_game` yields empty history, active status, and a new start time. Computer-generated secrets are requested anew; human mode requests a new hidden secret. Completed state remains only in the saved summary.

Deterministic generators are used only inside tests. Production generation does not use a fixed seed. This distinction allows exact testing without weakening ordinary play.

## 6.4.4: User Acceptance Test

Acceptance criteria were evaluated as an end-to-end checklist.

| User story | Acceptance criterion | Status |
|---|---|---|
| New player | Can read rules and start Easy without configuration knowledge | Accepted |
| Experienced player | Can select Expert or configure Custom constraints | Accepted |
| Two local players | Can enter a hidden secret and hand over the device | Accepted |
| Typing mistake | Receives corrective message without losing an attempt | Accepted |
| Completed player | Sees result, score, and saved local record | Accepted |
| Returning player | Can view ranked local summaries | Accepted |
| Data user | Can export standards-compliant CSV | Accepted |
| Interrupted user | Exits without an unhandled traceback | Accepted |

The colour-assisted letter representation reduces the main CLI usability gap. Players can scan familiar colours without losing the unambiguous identifiers needed in monochrome terminals, copied logs, and accessible text workflows. The GUI remains the more visual alternative and shares the same rules.

## 6.5: Online Workflow Verification

Real-handler tests use the same HTTP endpoints as the GUI with actual guest and email authentication. They cover pass-and-play completion and statistics, cross-user access denial, daily official restoration and practice, friend challenge creation/results/revocation, support, public rankings, account ZIP export, permanent deletion, MFA, and granted versus denied administrator access. Email delivery is intercepted by the test fixture, so no external message is sent.

A separate test starts a real Uvicorn listener and connects two synchronous CLI clients through Redis-backed rooms. It checks readiness, private concurrent guesses, duplicate-key retry, sequence replay, cross-owner denial, and connection cleanup. The same test runs `python -m mastermind_cli --online` as a subprocess and confirms a clean exit without printing tokens. A room-controller regression enters an invalid guess, receives its rejection, clears the pending submission, and returns safely.

| Regression | Expected result | Evidence |
|---|---|---|
| Email link uses public issuer rather than internal Docker host | Sign-in succeeds through configured API; unrelated origins rejected | Mocked transport and real-handler tests |
| Creation response is lost | Retry uses the same idempotency key | Transport/controller regression |
| Two guests submit duel guesses concurrently | Each accepted attempt occurs once; private fields stay private | Real WebSocket test |
| Refresh cookie rotates | New cookie saved atomically; second process denied same session lock | Client-state test |
| Guest exports account or ordinary user opens admin | Existing registered-account/grant checks reject request | Real-handler tests |
| Compound leaderboard ties and pagination | Stable global ranks and private-profile exclusion | MongoDB query regression |

These results establish important integration paths, not exhaustive proof of every menu sequence or every supported terminal. Broader scripted interaction coverage remains a priority in Section 8.3.

# 7: Debugging & Improvements

This section records seven concrete defect classes and the implementation safeguards that resolve them. Because the current repository is the verified baseline, the entries are a reconstruction from code boundaries and regression tests rather than a claim that each defect corresponds to a separately preserved historical commit.

## 7.1: Error List

| Error | Symptom/risk | Root cause | Resolution |
|---:|---|---|---|
| 1 | Too many white pegs with duplicates | All colours counted before exact matches removed | Remove black positions, then intersect `Counter` values |
| 2 | Invalid guess consumes an attempt | State updated before validation completes | Validate first; construct record only on success |
| 3 | Human secret visible to Code Breaker | Ordinary echoed input used | Use `getpass` and a 40-line hand-off clear |
| 4 | CSV opens as an active formula | Untrusted cells begin with formula marker | Prefix dangerous leading characters with apostrophe |
| 5 | One damaged row breaks score screen | Entire file parsed as all-or-nothing | Validate header; warn and skip malformed rows |
| 6 | Failed export leaves partial target | Destination written directly | Write, flush, sync, then atomically replace |
| 7 | Simultaneous duel guesses conflict or overwrite state | Two API workers mutate one room document concurrently | Serialize room attempts with a Redis lock and regression-test concurrent submissions |

## 7.1.1: Error 1, 2 Debugging

Error 1 appeared in reasoning about repeated colours. A naïve algorithm could count one peg as both black and white. The diagnostic case `secret R R B G` against `guess R B R Y` makes the defect obvious. Matching position 1 must be removed, leaving two colour-only intersections. The final algorithm separates exact-match indexes and compares only unmatched counters.

Error 2 concerned operation order. If a record were appended before `validate_code`, wrong-length or disallowed-duplicate guesses would unfairly reduce the attempt allowance. The corrected transaction validates and calculates feedback before it creates the next immutable history. Regression tests compare the entire pre- and post-error state.

## 7.1.2: Error 3, 4 Debugging

Error 3 affected pass-and-play confidentiality. A normal `input` prompt echoes the secret and remains visible in terminal history. The fix injects `getpass` for hidden entry, validates through the normal rule path, emits blank lines, and prints a hand-off instruction. This is adequate for one shared terminal, though separate-device play would be stronger.

Error 4 affected exported data. Spreadsheet programs may interpret cells beginning with `=`, `+`, `-`, `@`, tab, or carriage return as formulas. Player names are user-controlled, so ordinary CSV quoting alone is insufficient. `csv_safe` prefixes these cells with an apostrophe during append and export. A dedicated test asserts the escaped representation.

## 7.1.3: Error 5, 6 Debugging

Error 5 concerned damaged persistence. A missing header or one non-integer field should not crash menu option 2. The final reader checks required columns once, converts each row in its own guarded block, emits warnings, and returns the remaining valid records. File, encoding, and CSV errors return an empty list safely.

Error 6 concerned interruption during export. Directly opening the requested path in write mode can erase an existing report before new writing succeeds. The corrected sequence uses `mkstemp` in the target directory, writes and synchronizes the complete dataset, and calls `os.replace`, whose same-filesystem replacement is atomic. An exception handler removes the temporary file.

## 7.1.4: Error 7 Debugging

Error 7 was found in the wider GUI/API path that shares the Mastermind engine. Two players could submit duel guesses at almost the same moment, allowing independent MongoDB transactions to contend for the same room and game state. The repair at commit `13fa42f0d9703f945881610a9a2d89ac7d31446f` wraps the authoritative room-to-game mutation in a Redis lock named for the room. The five-second lease and blocking timeout bound failure, while the inner transaction preserves idempotency, attempt order, tie-window logic, and completion events.

Dedicated regression cases submit concurrent guesses, verify that both accepted attempts are retained exactly once, and confirm that retries remain idempotent. The local loop does not require that lock. Online CLI duels now use the same repaired service path; a real two-client WebSocket test checks concurrent guesses, replay, and cleanup.

## 7.2: Improvement List

The implemented program is reliable, but evaluation identified improvements in maintainability, portability, and user experience.

| Priority | Improvement | Expected benefit | Main trade-off |
|---:|---|---|---|
| 1 | Keep domain models typed and immutable | Prevent state drift; easier testing and GUI reuse | More explicit transition code |
| 2 | Harden local persistence and add migration metadata | Safer long-term score history | Additional schema/version handling |
| 3 | Expand dependency injection and interaction coverage | Reproduce prompts and failures precisely | More test fixtures |
| 4 | Maintain accessible terminal colour styling | Faster visual scanning | Preserve plain fallback and alignment |
| 5 | Offer JSON export beside CSV | Richer nested history analysis | Another documented format |
| 6 | Separate-device pass-and-play | Stronger secret confidentiality | Requires networking/authentication |

## 7.2.1: Improvement 1, 2, 3

Improvement 1 is already substantially realized through frozen dataclasses, tuples, enums, derived counters, and replacement-based transitions. Further work could introduce a small command/result type so every accepted or rejected action is represented without relying on exceptions at API edges.

Improvement 2 is partly realized through schema headers, scoring version, formula protection, warnings, `fsync`, and atomic replacement. A future release could add an explicit CSV schema version and automatic backup before migration. It could also lock the score file when two CLI processes append simultaneously.

Improvement 3 is realized through injectable normal input, secret input, output, store, and random source. Coverage shows the interactive controller still has more unvisited paths than the pure core. Additional parameterized scripts for every Custom prompt, every storage warning, EOF, and interruption would reduce this gap.

## 7.3: Additional Feature

The strongest additional feature is architectural reuse. The CLI is not an isolated school script: it uses the same canonical engine as the API and GUI-facing system. Improvements to feedback, validation, scoring, and configuration therefore remain consistent across interfaces.

Other additions include pass-and-play with hidden secret input, four official presets plus Custom, a local high-score table, versioned score records, CSV formula protection, atomic export, malformed-data recovery, and cross-platform installers that include both CLI and GUI entry points. The v1.1.0 packaging records the exact source commit in `RELEASE.txt`, allowing the installed payload to be audited. The desktop CLI points to the internal API service and persists its private session in the mounted data directory. These features extend the minimum expectation without obscuring the game loop.

The v1 CLI also adds accessible terminal colour rendering without a third-party dependency. The palette, accepted guesses, and lost-game reveal use the same formatter. Letter identifiers remain visible, black and white use contrast backgrounds, and automatic plain-text fallback keeps redirected output stable. Three new regression tests cover the formatter, capability policy, and a complete coloured game output path.

## 7.4: Documentation

Documentation exists at three levels. Terminal rules explain play at the moment of need. The repository README explains installation, development commands, architecture, testing, and packaging. This SBA report documents the analysis, algorithms, evidence, evaluation, and user procedure in a form suitable for assessment.

## 7.4.1: User Manual

### Installed application

1. Extract the macOS or Windows release archive and run its installer. Signing and notarization remain separate packaging work; this report does not certify an unsigned download as signed.
2. Choose the installation destination when prompted. The installer reports the GUI, CLI, service helper, bundled runtime, and supporting files it installs.
3. Open `RELEASE.txt` in the extracted archive when build provenance is required; the release package identifies v1.1.0 and its full source commit.
4. Start the GUI from the Applications folder or Start menu for a graphical game.
5. Open Terminal, PowerShell, or Command Prompt and enter `cipherboard` for the CLI.
6. For online features, start the services with `cipherboard-services start`, confirm with `cipherboard-services status`, inspect with `cipherboard-services logs`, and stop with `cipherboard-services stop`.

### Development environment

From the repository root, install the locked environment and launch the CLI:

```console
uv sync --frozen --all-extras
uv run python -m mastermind_cli
```

To verify the implementation:

```console
uv run pytest -q
uv run ruff check packages/mastermind_core apps/cli tests/core tests/cli
uv run mypy packages/mastermind_core apps/cli
```

### Playing a game

1. Enter `1` at the main menu.
2. Enter a player name, or press Enter to use `Player`.
3. Select Easy, Normal, Hard, Expert, or Custom.
4. In Custom mode, answer every bounded prompt. For human Code Maker, type the hidden secret and hand over the device.
5. Enter guesses using enabled letters. `RBGY`, `R B G Y`, `R,B,G,Y`, and `R-B-G-Y` are equivalent when those colours are enabled.
6. In an interactive terminal, the letters appear in their matching colours. Set `NO_COLOR=1` before `cipherboard` when plain output is preferred.
7. Read black as correct colour and position; read white as correct colour but different position.
8. Continue until the code is broken or attempts reach zero. Enter `quit` to abandon with zero score.

### Scores and exports

Menu option `2` prints up to 20 local results. Menu option `4` exports all readable records to `mastermind_scores.csv` by default or to a path you provide. The working score file is `data/high_scores.csv` relative to the launch location unless the packaged application configures another data directory. Do not edit a live score file while a game is being saved.

### Troubleshooting

- If `cipherboard` is not found, reopen the terminal after installation and confirm the selected installation directory is on `PATH`.
- If hidden input seems blank, this is expected: type the secret and press Enter.
- If a guess is rejected, confirm its length, enabled letters, and duplicate policy; the attempt has not been consumed.
- If colour is unavailable or unsuitable, the letters still identify every peg. Use `NO_COLOR=1 cipherboard` on macOS/Linux or `$env:NO_COLOR=1; cipherboard` in PowerShell for plain output.
- If a save/export warning appears, check directory permissions and free space. The game result is still displayed.
- If a damaged CSV is detected, preserve a copy before editing; valid rows may still load while malformed rows are skipped.

### Online operation

Start the installed services before opening option 6, or use `cipherboard --online` directly. In development, start `docker compose up -d mongo redis mailpit api` and run `uv run python -m mastermind_cli --online`. Hosted deployments need `--api-url https://api.example.com --product-origin https://play.example.com`; use the actual service origins, not the example names.

The online menu provides Play, History, Daily, Friends, Rooms, Profile, Leaderboards, Account, Settings, Support, Admin, Rules/privacy, and Local play. Each submenu uses 0 to go back. To join a friend game or duel, enter its share code or room ID. In a game, `refresh` fetches authoritative state, `retry` resends an uncertain guess, `back` preserves it for resumption, and `abandon` requires confirmation.

In Account, request an email link and paste the unopened link into Verify email link. For the desktop development stack, Mailpit shows the email at `http://127.0.0.1:8025`. Configure an authenticator through MFA setup before using protected admin actions. Account ZIP export requires a registered, recently authenticated account; deletion requires the exact confirmation `DELETE`. Export replacement is separately confirmed. Never share the private session directory or an MFA setup key.

Settings controls language, terminal theme, patterns, high contrast, sound, and optional analytics. Published privacy and terms need the web service as well as the API. If services are unavailable, return to local play. A second online player must use a distinct `--state-dir` to avoid sharing credentials or racing refresh rotation.

## 7.4.2: README File

The repository `README.md` is the developer and operator landing page. It describes Cipherboard, the shared-engine architecture, quick-start commands, applications, quality checks, data services, and packaging. The installer documentation adds platform-specific build and signing instructions. The dedicated `docs/operations/CLI.md` guide covers online menus, session storage, connection options, account recovery, and permission limits. This report complements the README: it explains why the CLI was designed this way and presents assessment evidence.

# 8: Conclusion

The Mastermind Game System meets its CLI-centred objective. It supports complete play, readable feedback, configurable constraints, secure computer or human secrets, immutable state, deterministic scoring, recoverable local persistence, and user-controlled export. The result is small enough to understand but structured enough to serve more than one interface.

## 8.1: Self-Reflection

The most important lesson was that apparently simple rules contain difficult boundary cases. Duplicate feedback required deliberate decomposition; input validation required preserving state on rejection; persistence required considering malicious spreadsheet content and interrupted writes. Designing those boundaries first produced code that was easier to test and explain.

I also learned to separate evidence from appearance. A polished terminal table is useful, but correctness comes from invariants and repeatable tests. Likewise, a high coverage value is supportive rather than conclusive: test cases must still assert the right behaviour. Writing this report exposed where the code is strong and where interaction coverage can grow.

## 8.2: Program Evaluation

The program's principal strengths are correctness, modularity, and failure handling. Duplicate-safe feedback is linear in code length; game objects are immutable; scoring is auditable and versioned; storage uses canonical fields and atomic export; and offline play has no network requirement. Online play reuses server authentication, authorization, persistence, and scoring instead of implementing a second set of rules. The shared core also prevents rule divergence between CLI and GUI.

**Efficiency evaluation.** The implementation reduces unnecessary comparison and file-writing work while preserving validation and saved-result integrity. Let `n` represent code length, `a` the number of accepted attempts, and `m` the number of stored scores. The following comparisons describe algorithmic work in the current source; they do not imply a measured percentage improvement in running time.

**Linear feedback processing.** The feedback function scans corresponding pegs once, removes exact matches, and builds colour counters for the unmatched pegs. Counter intersection limits each colour to the number available in both sequences. This takes expected `O(n)` time and `O(n)` temporary space, avoiding the quadratic worst-case work of repeatedly searching a remaining list for each misplaced peg. With only three to six positions, the immediate benefit is a clear, duplicate-safe algorithm; the linear structure also scales more predictably if longer codes are introduced.

**Incremental score saving.** A completed game appends one summary row rather than reading, sorting, and rewriting the entire score history. For a fixed-size record, the amount of application-level data processed by this save path does not grow with `m`. Loading and sorting are deferred until scores are viewed or exported. The explicit flush and `fsync` remain necessary durability costs, so a shorter code path is not treated as proof of lower disk latency.

**Controlled history costs.** Adding an immutable attempt copies the existing tuple of references, an `O(a)` operation. Rendering the complete board takes `O(a * n)` work per accepted guess. Both remain small under the current limit of 20 attempts. Reprinting only a new row could reduce repeated terminal output, but retaining the full history improves readability in terminals without cursor controls. This is a deliberate usability trade-off rather than a reason to remove immutable state or validation.

**Next efficiency improvement.** The main growth-dependent cost is the score reader: it materializes all valid records and sorts them in `O(m log m)` time with `O(m)` storage, even though the menu displays only 20 results. A separate streaming top-20 query could retain the best records in a bounded heap, reducing selection to `O(m log 20)` time and `O(20)` retained records. It would still scan the entire CSV and preserve malformed-row warnings, ranking tie-breaks, and formula protection. Full sorted export would retain its separate all-record path. This is proposed work; the current reader still loads and sorts the full history.

Limitations remain. Local CSV is not designed for concurrent multi-process writing. Pass-and-play privacy depends on one terminal hand-off. Some terminals cannot display ANSI styling, so the CLI must retain letter identifiers and plain fallback. Offline CSV exports contain summary data; the account ZIP provides the server's permitted account history. Combined core/CLI coverage is 75.87%, and the online menu controller is 59.33%, below the core's 99.72%. Not every menu branch has a complete end-to-end terminal script. Online mode depends on service availability; reconnect stops after four consecutive failures and requires a user-driven resume afterward. None prevents the stated use case, but each defines a credible next iteration.

## 8.3: Future Improvements

Future work should prioritize explicit CSV schema migration and locking, broader online menu scripts, offline JSON attempt-history export, and separate-device human Code Maker/Code Breaker sessions. Online duels are already separate-device contests; they do not replace that human-secret hand-off workflow. Themes, patterns, language selection, account export, and reconnect are implemented in this release. Further work should improve progress feedback during slow requests and test more terminal/accessibility combinations. Packaging should add automated signing and notarization verification on macOS and signed installer validation on Windows.

The scoring model could also be evaluated with real player data. Because `score_v1` excludes speed, it rewards reasoning and difficulty but may need recalibration across presets. Any change should create `score_v2`, preserve old records, and avoid retroactively comparing incompatible totals.

## 8.4: Summary

This project demonstrates the complete development cycle: a precise problem, parameter and constraint analysis, modular design, typed implementation, layered testing, debugging, user documentation, and critical evaluation. The release working tree passed 142 Python tests, with 99.72% branch-aware core coverage, 75.87% combined core/CLI coverage, and clean Ruff and mypy checks. The CLI now exposes the GUI's service-backed workflows while retaining offline play and CSV output. Real API and WebSocket checks support the account and multiplayer design; unvisited menu branches and unsigned installer validation remain clear areas for further verification.

# 9: Appendix

The appendix records the reference basis and development schedule. Source-code figures in this report are generated from the repository baseline, and measured charts come from the verification commands stated in Section 6.

## 9.1: References

References were selected for software-development fundamentals, Python standard-library behaviour, test methodology, environment management, and the official assessment context. The original reference list was compiled on 1 September 2026. The 25 November CLI update was checked against repository contracts and tests; it does not imply that these external pages were rechecked on that date.

## 9.1.1: Books

1. Brookshear, J. G., and Brylow, D. *Computer Science: An Overview*. 13th ed., Pearson, 2019.
2. Downey, A. B. *Think Python: How to Think Like a Computer Scientist*. 2nd ed., O'Reilly Media, 2015.
3. Sommerville, I. *Software Engineering*. 10th ed., Pearson, 2015.

## 9.1.2: Websites

1. Hong Kong Examinations and Assessment Authority. “Hong Kong Diploma of Secondary Education Information and Communication Technology: School-based Assessment Teachers' Handbook (2028 Examination).” https://www.hkeaa.edu.hk/DocLibrary/SBA/HKDSE/SBAhandbook-2028-ICT-E.pdf
2. Hong Kong Examinations and Assessment Authority. “2025 HKDSE Information and Communication Technology Assessment Framework.” https://www.hkeaa.edu.hk/DocLibrary/HKDSE/Subject_Information/ict/2025hkdse-e-ict.pdf
3. Python Software Foundation. “`csv` — CSV File Reading and Writing.” https://docs.python.org/3/library/csv.html
4. Python Software Foundation. “`dataclasses` — Data Classes.” https://docs.python.org/3/library/dataclasses.html
5. Python Software Foundation. “`secrets` — Generate Secure Random Numbers.” https://docs.python.org/3/library/secrets.html
6. Python Software Foundation. “`collections` — Container Datatypes.” https://docs.python.org/3/library/collections.html
7. pytest development team. “pytest Documentation.” https://docs.pytest.org/en/stable/
8. Astral. “Running Commands in Projects.” https://docs.astral.sh/uv/concepts/projects/run/

## 9.1.3: AI Tools and Assistance

OpenAI Codex assisted with implementation review, regression tests, documentation, and report preparation for the CLI update. Generated changes were checked against repository source, real API/WebSocket behavior, and measured test output. The candidate should review the final work and complete any assistance declaration required by the school. No runtime improvement percentage or unperformed user study is asserted.

## 9.2: Gantt Chart

The following chart expresses the iterative development schedule. Analysis and design overlap because rule discoveries feed back into constraints. Testing begins before feature completion and continues through packaging and documentation.

[[FIGURE:gantt_chart.png|Figure 22. Project schedule from analysis through verification and report completion.]]

| Phase | Main deliverable | Completion evidence |
|---|---|---|
| Problem definition | Objectives and minimum expectations | Sections 1–2 |
| Analysis | Parameters, constraints, IPO, modular boundaries | Section 3 |
| Design | State, flow, generation, persistence | Section 4 |
| Implementation | Core, CLI, storage, packaging | Section 5 and source figures |
| Testing | Unit, integration, system and acceptance evidence | Section 6 |
| Debugging | Seven resolved defect classes and improvements | Section 7 |
| Documentation | README, user manual, final SBA report | Sections 7.4–9 |
