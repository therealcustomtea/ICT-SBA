# Desktop installers

Cipherboard ships guided installers for macOS and Windows. Each installer asks for a dedicated installation folder, installs both the browser GUI and interactive CLI, creates launchers, starts every required local service, verifies readiness, and writes an `INSTALLATION.txt` report inside the selected folder.

## What is installed

- the Cipherboard GUI and its FastAPI service;
- the `cipherboard` interactive CLI and shared game engine;
- version-pinned MongoDB replica-set, Redis, and Mailpit containers;
- first-party guest, email-link, refresh-token, session-revocation, and TOTP authentication;
- database index initialization and all pinned Python/Node application dependencies inside container images;
- GUI, service-management, and CLI launchers.

Docker Desktop is the only system-level dependency. If it is absent, the installer offers to download the official signed installer, verifies its platform signature, and starts it. Docker Desktop has its own license and [macOS](https://docs.docker.com/desktop/setup/install/mac-install/) or [Windows](https://docs.docker.com/desktop/setup/install/windows-install/) system requirements; the user must review and accept those terms. The application binds the GUI, API, and Mailpit inbox only to loopback addresses, so this installer is intended for private workstation use rather than public hosting.

## Install on macOS

1. Extract `Cipherboard-macOS.zip`.
2. Double-click `Install Cipherboard.command`. If Gatekeeper asks, Control-click it and choose **Open**.
3. Enter an absolute installation path or accept `~/Applications/Cipherboard`.
4. Complete Docker Desktop's first-run prompt if it appears.

The installer creates `Cipherboard.app`, links the CLI commands into `~/.local/bin`, adds that directory to the current shell's login profile when needed, opens the installation report, and launches the GUI. Open a new terminal before using the newly added PATH entry.

## Install on Windows

1. Extract `Cipherboard-Windows.zip`.
2. Double-click `Install Cipherboard.cmd`.
3. Enter an installation path or accept `%LOCALAPPDATA%\Programs\Cipherboard`.
4. Complete Docker Desktop/WSL first-run setup if it appears.

The installer supports 64-bit Intel/AMD Windows, adds its `bin` folder to the current user's `PATH`, creates Desktop and Start Menu shortcuts, opens the installation report, and launches the GUI. Open a new terminal before using the newly added PATH entry.

## Use Cipherboard

Open the GUI from `Cipherboard.app` on macOS or the Cipherboard shortcut on Windows. The GUI is also available at `http://127.0.0.1:3000/en` while services are running.

Run the CLI in Terminal, Command Prompt, or PowerShell:

```text
cipherboard
```

Manage the GUI stack with:

```text
cipherboard-services start
cipherboard-services open
cipherboard-services stop
cipherboard-services restart
cipherboard-services status
cipherboard-services logs
```

Email sign-in links sent by the local installation appear in Mailpit at `http://127.0.0.1:8025`. Stopping services preserves MongoDB data and CLI scores. CLI scores are stored in `<install folder>/data/high_scores.csv`; GUI data uses Docker volumes prefixed `cipherboard-desktop_`.

## Build release archives

From the repository root:

```bash
python3 infra/installers/build_release_archives.py
```

The command creates `dist/installers/Cipherboard-macOS.zip`, `Cipherboard-Windows.zip`, and `SHA256SUMS.txt`. The dedicated GitHub Actions workflow validates platform script syntax, builds the same archives, uploads them as workflow artifacts, and attaches them to tagged GitHub releases.
