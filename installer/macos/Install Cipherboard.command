#!/usr/bin/env bash
set -euo pipefail

SUPABASE_VERSION='2.101.0'
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -d "$SCRIPT_DIR/payload" ]]; then
  SOURCE_DIR="$SCRIPT_DIR/payload"
else
  SOURCE_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
fi

say() { printf '\n%s\n' "$*"; }
fail() { printf '\nInstallation failed: %s\n' "$*" >&2; exit 1; }

say 'Cipherboard installer for macOS'
printf '%s\n' \
  'This installs the GUI, CLI, local database, Redis cache, and local authentication.' \
  'Docker Desktop is the only system-level dependency.'

default_location="$HOME/Applications/Cipherboard"
read -r -p "Install location [$default_location]: " install_dir
install_dir="${install_dir:-$default_location}"
install_dir="${install_dir/#\~/$HOME}"
[[ "$install_dir" == /* ]] || fail 'Choose an absolute install path.'
[[ "$install_dir" != '/' && "$install_dir" != "$HOME" ]] || fail 'Choose a dedicated Cipherboard folder.'

marker="$install_dir/.cipherboard-installation"
if [[ -d "$install_dir" && ! -f "$marker" ]] && [[ -n "$(find "$install_dir" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null)" ]]; then
  fail "The selected folder is not empty and is not a Cipherboard installation: $install_dir"
fi

install_docker() {
  local architecture download_url temporary_dir mount_dir
  architecture="$(uname -m)"
  case "$architecture" in
    arm64) download_url='https://desktop.docker.com/mac/main/arm64/Docker.dmg' ;;
    x86_64) download_url='https://desktop.docker.com/mac/main/amd64/Docker.dmg' ;;
    *) fail "Unsupported Mac architecture: $architecture" ;;
  esac
  read -r -p 'Docker Desktop is required but was not found. Install it now? [Y/n]: ' answer
  [[ ! "$answer" =~ ^[Nn] ]] || fail 'Docker Desktop is required to install Cipherboard.'
  temporary_dir="$(mktemp -d)"
  mount_dir="$temporary_dir/docker"
  mkdir -p "$mount_dir"
  trap 'hdiutil detach "$mount_dir" -quiet 2>/dev/null || true; rm -rf "$temporary_dir"' RETURN
  say 'Downloading Docker Desktop from docker.com...'
  curl --fail --location --progress-bar "$download_url" -o "$temporary_dir/Docker.dmg"
  hdiutil attach -nobrowse -quiet -mountpoint "$mount_dir" "$temporary_dir/Docker.dmg"
  codesign --verify --deep --strict "$mount_dir/Docker.app"
  codesign -dv --verbose=4 "$mount_dir/Docker.app" 2>&1 \
    | grep -q 'Authority=Developer ID Application: Docker Inc' \
    || fail 'The downloaded Docker Desktop application has an unexpected signing identity.'
  say 'macOS may ask for your password to install Docker Desktop.'
  sudo "$mount_dir/Docker.app/Contents/MacOS/install" --user "$USER"
  hdiutil detach "$mount_dir" -quiet
  rm -rf "$temporary_dir"
  trap - RETURN
}

if [[ -x /Applications/Docker.app/Contents/Resources/bin/docker ]]; then
  export PATH="/Applications/Docker.app/Contents/Resources/bin:$PATH"
fi
if ! command -v docker >/dev/null 2>&1; then
  install_docker
  export PATH="/Applications/Docker.app/Contents/Resources/bin:$PATH"
fi
if ! docker info >/dev/null 2>&1 && [[ ! -d /Applications/Docker.app ]]; then
  install_docker
  export PATH="/Applications/Docker.app/Contents/Resources/bin:$PATH"
fi

if ! docker info >/dev/null 2>&1; then
  say 'Starting Docker Desktop. Accept its license and finish any first-run prompts if shown.'
  open -a Docker || fail 'Docker Desktop could not be opened.'
  for _ in {1..150}; do
    docker info >/dev/null 2>&1 && break
    sleep 2
  done
fi
docker info >/dev/null 2>&1 || fail 'Docker Desktop did not become ready. Finish its setup and run this installer again.'
docker compose version >/dev/null 2>&1 || fail 'Docker Compose is unavailable in Docker Desktop.'

say "Copying Cipherboard to $install_dir..."
mkdir -p "$install_dir/app" "$install_dir/bin" "$install_dir/tools" "$install_dir/data"
rsync -a --delete \
  --exclude '.git/' \
  --exclude '.mypy_cache/' \
  --exclude '.pytest_cache/' \
  --exclude '.ruff_cache/' \
  --exclude '.env*' \
  --exclude '.next/' \
  --exclude '.venv/' \
  --exclude 'coverage/' \
  --exclude 'dist/' \
  --exclude 'node_modules/' \
  --exclude 'output/' \
  --exclude 'playwright-report/' \
  --exclude 'test-results/' \
  "$SOURCE_DIR/" "$install_dir/app/"
printf 'Cipherboard desktop installation\n' > "$marker"

architecture="$(uname -m)"
case "$architecture" in
  arm64)
    supabase_target='darwin_arm64'
    supabase_checksum='87cfbc6d8647d7eb7d204351d46aaf4a734d7449c6ca5c5c628a5f5d0be60f74'
    ;;
  x86_64)
    supabase_target='darwin_amd64'
    supabase_checksum='a2ad6f801c14d325a9e58829e4e6d00ed944befea85607cdc6a5c1ba88517d68'
    ;;
  *) fail "Unsupported Mac architecture: $architecture" ;;
esac
supabase_archive="supabase_${SUPABASE_VERSION}_${supabase_target}.tar.gz"
temporary_dir="$(mktemp -d)"
trap 'rm -rf "$temporary_dir"' EXIT
say "Installing the pinned Supabase CLI ($SUPABASE_VERSION)..."
curl --fail --location --progress-bar \
  "https://github.com/supabase/cli/releases/download/v${SUPABASE_VERSION}/${supabase_archive}" \
  -o "$temporary_dir/$supabase_archive"
actual_checksum="$(shasum -a 256 "$temporary_dir/$supabase_archive" | awk '{print $1}')"
[[ "$actual_checksum" == "$supabase_checksum" ]] || fail 'The Supabase CLI checksum did not match.'
tar -xzf "$temporary_dir/$supabase_archive" -C "$temporary_dir"
install -m 0755 "$temporary_dir/supabase" "$install_dir/tools/supabase"

say 'Starting local authentication for first-time configuration...'
"$install_dir/tools/supabase" --workdir "$install_dir/app" start >/dev/null
status_file="$temporary_dir/supabase.env"
"$install_dir/tools/supabase" --workdir "$install_dir/app" status -o env > "$status_file"
set +u
# Supabase emits shell-escaped assignments; only the pinned, checksum-verified local CLI writes this file.
source "$status_file"
set -u
publishable_key="${PUBLISHABLE_KEY:-${ANON_KEY:-}}"
service_role_key="${SERVICE_ROLE_KEY:-${SECRET_KEY:-}}"
[[ -n "$publishable_key" && -n "$service_role_key" ]] || fail 'Supabase did not provide local API keys.'

environment_file="$install_dir/app/.installer.env"
if [[ ! -f "$environment_file" ]]; then
  umask 077
  postgres_password="$(openssl rand -hex 24)"
  encryption_key="$(openssl rand -base64 32 | tr -d '\n')"
  daily_key="$(openssl rand -hex 32)"
  identifier_key="$(openssl rand -hex 32)"
  {
    printf 'POSTGRES_PASSWORD=%s\n' "$postgres_password"
    printf 'SUPABASE_PUBLISHABLE_KEY=%s\n' "$publishable_key"
    printf 'SUPABASE_SERVICE_ROLE_KEY=%s\n' "$service_role_key"
    printf 'MASTERMIND_SECRET_ENCRYPTION_KEYS={"v1":"%s"}\n' "$encryption_key"
    printf 'MASTERMIND_DAILY_HMAC_KEY=%s\n' "$daily_key"
    printf 'MASTERMIND_PUBLIC_IDENTIFIER_HMAC_KEY=%s\n' "$identifier_key"
    printf 'MASTERMIND_RELEASE=desktop-1.0.0\n'
  } > "$environment_file"
fi
chmod 600 "$environment_file"

say 'Building and starting the GUI, API, database, and cache. The first run may take several minutes...'
docker compose \
  --env-file "$environment_file" \
  -f "$install_dir/app/installer/docker-compose.yml" \
  up -d --build

for endpoint in 'http://127.0.0.1:8000/health/ready' 'http://127.0.0.1:3000/en'; do
  ready=false
  for _ in {1..90}; do
    if curl --fail --silent --max-time 2 "$endpoint" >/dev/null 2>&1; then ready=true; break; fi
    sleep 2
  done
  [[ "$ready" == true ]] || fail "A required service did not become ready: $endpoint"
done

ditto "$install_dir/app/installer/runtime/macos/cipherboard" "$install_dir/bin/cipherboard"
ditto "$install_dir/app/installer/runtime/macos/cipherboard-services" "$install_dir/bin/cipherboard-services"
ditto "$install_dir/app/installer/runtime/macos/Cipherboard.app" "$install_dir/Cipherboard.app"
iconset="$temporary_dir/Cipherboard.iconset"
mkdir -p "$iconset" "$install_dir/Cipherboard.app/Contents/Resources"
for icon_spec in \
  '16 icon_16x16.png' \
  '32 icon_16x16@2x.png' \
  '32 icon_32x32.png' \
  '64 icon_32x32@2x.png' \
  '128 icon_128x128.png' \
  '256 icon_128x128@2x.png' \
  '256 icon_256x256.png' \
  '512 icon_256x256@2x.png' \
  '512 icon_512x512.png' \
  '1024 icon_512x512@2x.png'; do
  read -r icon_size icon_name <<< "$icon_spec"
  sips -z "$icon_size" "$icon_size" \
    "$install_dir/app/apps/web/public/icon-512.png" \
    --out "$iconset/$icon_name" >/dev/null
done
iconutil -c icns "$iconset" -o "$install_dir/Cipherboard.app/Contents/Resources/Cipherboard.icns"
chmod 0755 \
  "$install_dir/bin/cipherboard" \
  "$install_dir/bin/cipherboard-services" \
  "$install_dir/Cipherboard.app/Contents/MacOS/Cipherboard"

mkdir -p "$HOME/.local/bin" "$HOME/Applications"
for command_name in cipherboard cipherboard-services; do
  link_path="$HOME/.local/bin/$command_name"
  if [[ ! -e "$link_path" || -L "$link_path" ]]; then
    ln -sfn "$install_dir/bin/$command_name" "$link_path"
  else
    printf 'Kept existing command at %s; use %s directly.\n' "$link_path" "$install_dir/bin/$command_name"
  fi
done
case "${SHELL:-}" in
  */bash) shell_profile="$HOME/.bash_profile" ;;
  *) shell_profile="$HOME/.zprofile" ;;
esac
path_line='export PATH="$HOME/.local/bin:$PATH"'
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]] \
  && ! grep -Fqx "$path_line" "$shell_profile" 2>/dev/null; then
  {
    printf '\n# Added by the Cipherboard installer.\n'
    printf '%s\n' "$path_line"
  } >> "$shell_profile"
fi
app_link="$HOME/Applications/Cipherboard.app"
if [[ "$install_dir/Cipherboard.app" != "$app_link" ]] && [[ ! -e "$app_link" || -L "$app_link" ]]; then
  ln -sfn "$install_dir/Cipherboard.app" "$app_link"
fi

guide="$install_dir/INSTALLATION.txt"
{
  printf 'Cipherboard installation\n========================\n\n'
  printf 'Installed in: %s\n\n' "$install_dir"
  printf 'Installed components:\n'
  printf '  - Cipherboard GUI at http://127.0.0.1:3000/en\n'
  printf '  - Cipherboard interactive CLI\n'
  printf '  - FastAPI game service\n'
  printf '  - PostgreSQL game database\n'
  printf '  - Redis real-time cache\n'
  printf '  - Local Supabase authentication\n'
  printf '  - Docker-managed, pinned application dependencies\n\n'
  printf 'Open the GUI:\n  Double-click Cipherboard.app, or run: cipherboard-services open\n\n'
  printf 'Use the CLI:\n  Open a new Terminal window and run: cipherboard\n'
  printf '  Direct launcher: %s/bin/cipherboard\n\n' "$install_dir"
  printf 'Manage services:\n'
  printf '  cipherboard-services start | stop | restart | status | logs\n\n'
  printf 'Data locations:\n'
  printf '  CLI scores: %s/data/high_scores.csv\n' "$install_dir"
  printf '  GUI data: Docker volumes named cipherboard-desktop_*\n'
} > "$guide"

say 'Installation complete.'
printf 'Installed: GUI, CLI, API, PostgreSQL, Redis, Supabase Auth, and all application dependencies.\n'
printf 'Installation report: %s\n' "$guide"
printf 'CLI: %s/bin/cipherboard\n' "$install_dir"
printf 'GUI: %s/Cipherboard.app\n' "$install_dir"
open "$guide"
open 'http://127.0.0.1:3000/en'
