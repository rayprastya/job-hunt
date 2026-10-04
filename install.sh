#!/usr/bin/env bash
# job-hunt installer: puts the kit where you want it, then interviews you once so an AI agent
# can search and apply to jobs for you using only YOUR answers.
# Usage: bash install.sh            (or: curl -fsSL https://raw.githubusercontent.com/rayprastya/job-hunt/main/install.sh | bash)
set -euo pipefail

REPO="https://github.com/rayprastya/job-hunt.git"
say() { printf '\n\033[1m%s\033[0m\n' "$*"; }
ask() { local q="$1" def="${2:-}" a; if [ -n "$def" ]; then read -r -p "$q [$def]: " a </dev/tty; echo "${a:-$def}"; else read -r -p "$q: " a </dev/tty; echo "$a"; fi; }

say "1/5  Where should job-hunt live?"
DEST=$(ask "Install folder" "$HOME/job-hunt")
DEST="${DEST/#\~/$HOME}"
if [ -d "$DEST/.git" ]; then
  echo "Found an existing checkout at $DEST, updating it."
  git -C "$DEST" pull --ff-only || true
elif [ -f "$(dirname "$0")/README.md" ] && [ "$(cd "$(dirname "$0")" && pwd)" != "$DEST" ] && [ -d "$(dirname "$0")/tools" ]; then
  mkdir -p "$DEST"; cp -R "$(dirname "$0")"/. "$DEST"/
else
  git clone "$REPO" "$DEST"
fi
cd "$DEST"

say "2/5  Checking tools (python3, node 20+, a Chromium browser)"
command -v python3 >/dev/null || { echo "python3 is required"; exit 1; }
command -v node >/dev/null || echo "WARNING: node 20+ is needed for the browser bridge (tools/cdpd.mjs). Install it from https://nodejs.org"
ls /Applications 2>/dev/null | grep -qE "Brave Browser|Google Chrome" || echo "NOTE: install Brave or Chrome; see docs/BROWSER.md"

say "3/5  Your private folder (me/). It is gitignored: nothing in it is ever pushed."
ME=$(ask "Private data folder (keep it in a private repo or synced folder to use it on other devices)" "$DEST/me")
ME="${ME/#\~/$HOME}"
mkdir -p "$ME/cv"
if [ "$ME" != "$DEST/me" ]; then ln -sfn "$ME" "$DEST/me"; fi
[ -f "$ME/tracker.csv" ] || cp templates/tracker.csv "$ME/tracker.csv"

say "4/5  A few questions so the agent can fill applications for you (Enter to skip, you can edit me/profile.json later)"
python3 tools/onboard.py "$ME"

say "5/5  Done."
cat <<EOF
Next steps:
  1. Put your CV in $ME/cv/ (PDF). Keep a version without anything you don't want shared.
  2. Make a Google Sheet for tracking (docs/SHEETS.md) and paste its link into $ME/config.md.
  3. Connect your browser (docs/BROWSER.md): separate profile (simplest) or your main browser.
  4. Open your AI agent in $DEST and say: "find me jobs and apply" (Claude Code reads CLAUDE.md;
     other agents: see docs/OTHER_AI.md).
EOF
