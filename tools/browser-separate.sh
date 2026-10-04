#!/usr/bin/env bash
# Open a separate Brave (default) or Chrome profile with remote debugging on port 9333.
# Usage: bash tools/browser-separate.sh [--chrome]
set -euo pipefail
PROFILE="${JOB_HUNT_PROFILE:-$HOME/.job-hunt-browser}"
APP="Brave Browser"
[ "${1:-}" = "--chrome" ] && APP="Google Chrome"
if [ "$(uname)" = "Darwin" ]; then
  open -na "$APP" --args --remote-debugging-port=9333 --user-data-dir="$PROFILE"
else
  BIN=$(command -v brave-browser || command -v brave || command -v google-chrome || command -v chromium)
  "$BIN" --remote-debugging-port=9333 --user-data-dir="$PROFILE" >/dev/null 2>&1 &
fi
echo "Opened $APP with profile $PROFILE on port 9333. Log in to LinkedIn/Google once in that window."
echo "Then run: CDP_PORT=9333 node tools/cdpd.mjs &"
