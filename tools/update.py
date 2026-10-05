"""Keep the kit current. Safe: fast-forward only, never touches me/ (gitignored), never discards your edits.

Usage:
  python3 tools/update.py            # update if behind; prints what changed
  python3 tools/update.py --if-stale # only check if the last check was > 12 hours ago (used at session start)
  python3 tools/update.py --check    # report only, don't pull
Exit codes: 0 = already current or skipped, 2 = updated (new fixes pulled), 1 = could not update (reason printed).
"""
import os, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STAMP = os.path.join(ROOT, "me", ".last_update_check")
STALE_SECONDS = 12 * 3600


def git(*a):
    return subprocess.run(["git", "-C", ROOT, *a], capture_output=True, text=True, timeout=120)


def main():
    if not os.path.isdir(os.path.join(ROOT, ".git")):
        print("update: not a git checkout; download the latest kit manually from GitHub."); return 1
    if "--if-stale" in sys.argv and os.path.exists(STAMP) and time.time() - os.path.getmtime(STAMP) < STALE_SECONDS:
        return 0
    if git("fetch", "-q").returncode != 0:
        print("update: could not reach GitHub (offline?); continuing with the current version."); return 1
    os.makedirs(os.path.dirname(STAMP), exist_ok=True)
    open(STAMP, "w").write(str(time.time()))
    behind = git("rev-list", "--count", "HEAD..@{u}").stdout.strip() or "0"
    if behind == "0":
        print("update: kit is up to date."); return 0
    log = git("log", "--oneline", "HEAD..@{u}").stdout.strip()
    print(f"update: {behind} new commit(s) available:\n{log}")
    if "--check" in sys.argv:
        return 0
    dirty = [l for l in git("status", "--porcelain", "--untracked-files=no").stdout.splitlines() if l.strip() and not l[3:].startswith("me/")]
    if dirty:
        print("update: you have local edits to kit files, so I won't pull automatically:\n  " + "\n  ".join(dirty)
              + "\n  Commit or stash them (git stash), then run: python3 tools/update.py"); return 1
    r = git("pull", "--ff-only", "-q")
    if r.returncode != 0:
        print("update: pull failed: " + (r.stderr.strip() or r.stdout.strip())); return 1
    print("update: done, now on the latest version."); return 2


if __name__ == "__main__":
    sys.exit(main())
