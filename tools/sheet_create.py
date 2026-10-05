"""Create the tracker Google Sheet for the user (in THEIR logged-in browser), same format as the template,
then save its link to me/config.md. No API keys: it uses sheets.new in the browser.

Usage: python3 tools/sheet_create.py [--title "Job Applications Tracker"] [--force]
Skips if me/config.md already has a sheet link (use --force to make another one).
Needs: browser connector running and the user logged in to Google in that browser.
"""
import os, re, subprocess, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from br import Bridge

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG = os.path.join(ROOT, "me", "config.md")
title = sys.argv[sys.argv.index("--title") + 1] if "--title" in sys.argv else "Job Applications Tracker"

cfg = open(CFG).read() if os.path.exists(CFG) else ""
m = re.search(r"Tracker sheet:\s*(https://docs\.google\.com/spreadsheets/d/[\w-]+\S*)", cfg)
if m and "--force" not in sys.argv:
    print("Sheet already set:", m.group(1)); sys.exit(0)

b = Bridge()
tab = b.open("https://sheets.new")
url = ""
for _ in range(40):
    time.sleep(1)
    try:
        url = b.eval(tab, "location.href") or ""
    except Exception:
        continue
    if "accounts.google.com" in url:
        print("Not logged in to Google in this browser. Log in, then run this again."); sys.exit(1)
    if re.search(r"/spreadsheets/d/[\w-]+", url) and b.eval(tab, "!!document.querySelector('.docs-title-input')"):
        break
else:
    print("Could not open a new Google Sheet (is the browser logged in to Google?)."); sys.exit(1)
time.sleep(2)

# name it
b.click(tab, "document.querySelector('.docs-title-input')")
b.eval(tab, "(()=>{const t=document.querySelector('.docs-title-input');t.select();return 1})()")
b.type(tab, title)
b.key(tab, "Enter")
time.sleep(2)

sheet = re.sub(r"(/spreadsheets/d/[\w-]+).*", r"\1/edit", url)
line = f"Tracker sheet: {sheet}"
if re.search(r"(?m)^Tracker sheet:.*$", cfg):
    cfg = re.sub(r"(?m)^Tracker sheet:.*$", line, cfg)
else:
    cfg = line + "\n" + cfg
open(CFG, "w").write(cfg)
print("Created", title, "->", sheet)

# fill header (+ any existing tracker rows) using the normal sync
subprocess.run([sys.executable, os.path.join(ROOT, "tools", "sheet_push.py"), tab], check=False)
print("Saved the link to me/config.md. Open it any time from there.")
