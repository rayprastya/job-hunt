#!/usr/bin/env bash
# Open a separate Brave (default) or Chrome profile with remote debugging on port 9333.
# Usage: bash tools/browser-separate.sh [--chrome] [--headless]
#   First run WITHOUT --headless and log in to LinkedIn/Google in the window. Later runs can use --headless
#   (invisible, same saved logins, doesn't steal focus). Bot-check sites (Ashby/Greenhouse/Lever) still need a
#   visible window for your final Submit click.
set -euo pipefail
PROFILE="${JOB_HUNT_PROFILE:-$HOME/.job-hunt-browser}"
APP="Brave Browser"; BIN_NAMES="brave-browser brave"; HEADLESS=""
for a in "$@"; do
  case "$a" in
    --chrome) APP="Google Chrome"; BIN_NAMES="google-chrome chromium chromium-browser" ;;
    --headless) HEADLESS="--headless=new --window-size=1440,1000" ;;  # user agent fixed below (no "HeadlessChrome")
  esac
done
ARGS="--remote-debugging-port=9333 --user-data-dir=$PROFILE $HEADLESS"
UA_OS="Macintosh; Intel Mac OS X 10_15_7"; [ "$(uname)" = "Linux" ] && UA_OS="X11; Linux x86_64"
UA="Mozilla/5.0 ($UA_OS) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
if [ "$(uname)" = "Darwin" ]; then
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
echo "Started $APP ${HEADLESS:+(headless) }with profile $PROFILE on port 9333."
[ -z "$HEADLESS" ] && echo "Log in to LinkedIn/Google once in that window."
echo "Then run: CDP_PORT=9333 node tools/cdpd.mjs &"
