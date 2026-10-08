#!/usr/bin/env bash
# Open a separate Brave (default) or Chrome profile with remote debugging on port 9333.
# Usage: bash tools/browser-separate.sh [--chrome] [--hidden | --headless]
#   --hidden   (recommended for background runs) a normal browser window launched hidden: invisible to you, but an
#              ordinary browser to websites. LinkedIn signs out true headless browsers, so use this for LinkedIn.
#   --headless true headless; fine for most career sites, NOT for LinkedIn (it revokes the login).
#   First run WITHOUT --headless and log in to LinkedIn/Google in the window. Later runs can use --headless
#   (invisible, same saved logins, doesn't steal focus). Bot-check sites (Ashby/Greenhouse/Lever) still need a
#   visible window for your final Submit click.
set -euo pipefail
PROFILE="${JOB_HUNT_PROFILE:-$HOME/.job-hunt-browser}"
APP="Brave Browser"; BIN_NAMES="brave-browser brave"; HEADLESS=""; HIDDEN=""
for a in "$@"; do
  case "$a" in
    --chrome) APP="Google Chrome"; BIN_NAMES="google-chrome chromium chromium-browser" ;;
    --headless) HEADLESS="--headless=new --window-size=1440,1000" ;;  # user agent fixed below (no "HeadlessChrome")
    --hidden) HIDDEN=1 ;;
  esac
done
ARGS="--remote-debugging-port=9333 --user-data-dir=$PROFILE $HEADLESS"
UA_OS="Macintosh; Intel Mac OS X 10_15_7"; [ "$(uname)" = "Linux" ] && UA_OS="X11; Linux x86_64"
# The user agent must match the real browser version: LinkedIn (and others) sign you out when the same login
# suddenly comes from a "different" browser. Read the installed major version instead of hard-coding one.
if [ "$(uname)" = "Darwin" ]; then VER_OUT=$("/Applications/$APP.app/Contents/MacOS/$APP" --version 2>/dev/null || true)
else VER_OUT=$( (for n in $BIN_NAMES; do command -v "$n" >/dev/null && "$n" --version && break; done) 2>/dev/null || true); fi
MAJOR=$(printf '%s' "$VER_OUT" | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1 | cut -d. -f1)
MAJOR=${MAJOR:-140}
UA="Mozilla/5.0 ($UA_OS) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/$MAJOR.0.0.0 Safari/537.36"
if [ -n "$HIDDEN" ]; then
  if [ "$(uname)" = "Darwin" ]; then
    open -n -g -j -a "$APP" --args $ARGS --window-size=1440,1000   # -j launch hidden, -g keep it in the background
  else
    BIN=""; for n in $BIN_NAMES; do BIN=$(command -v "$n" || true); [ -n "$BIN" ] && break; done
    [ -n "$BIN" ] || { echo "Browser not found"; exit 1; }
    # Off-screen window; under a desktop session this is invisible but still a normal browser.
    "$BIN" $ARGS --window-position=-32000,-32000 --window-size=1440,1000 >/dev/null 2>&1 &
  fi
elif [ "$(uname)" = "Darwin" ]; then
  if [ -n "$HEADLESS" ]; then
    "/Applications/$APP.app/Contents/MacOS/$APP" $ARGS --user-agent="$UA" >/dev/null 2>&1 &
  else
    open -na "$APP" --args $ARGS
  fi
else
  BIN=""; for n in $BIN_NAMES; do BIN=$(command -v "$n" || true); [ -n "$BIN" ] && break; done
  [ -n "$BIN" ] || { echo "Browser not found"; exit 1; }
  if [ -n "$HEADLESS" ]; then "$BIN" $ARGS --user-agent="$UA" >/dev/null 2>&1 & else "$BIN" $ARGS >/dev/null 2>&1 & fi
fi
echo "Started $APP ${HEADLESS:+(headless) }${HIDDEN:+(hidden window) }with profile $PROFILE on port 9333."
[ -z "$HEADLESS" ] && echo "Log in to LinkedIn/Google once in that window."
echo "Then run: CDP_PORT=9333 node tools/cdpd.mjs &"
