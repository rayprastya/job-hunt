"""Run any kit tool with auto-update on stall.

Usage: python3 tools/run.py <tool.py> [args...]        e.g. python3 tools/run.py easy_apply.py <tab> <job-id> SG
If the tool crashes or reports a stall (STUCK / UNKNOWN_END / RuntimeError / timeout), this updates the kit
(tools/update.py) and, only if new fixes were pulled, retries the tool once. "Needs your answer" results
(NEEDS_ANSWERS, exit 3 with that message) are NOT treated as stalls.
"""
import os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
STALL_MARKERS = ("STUCK", "UNKNOWN_END", "Traceback", "RuntimeError", "NO_FORM", "timed out")


def run(cmd):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=900, stdin=subprocess.DEVNULL)
        out = (p.stdout or "") + (p.stderr or "")
        return p.returncode, out
    except subprocess.TimeoutExpired:
        return 124, "timed out after 15 minutes"


def stalled(code, out):
    if "NEEDS_ANSWERS" in out or "SUBMITTED" in out or "DRY_RUN_STOP" in out or "NO_EASY_APPLY" in out:
        return False
    return code != 0 and any(m in out for m in STALL_MARKERS)


if len(sys.argv) < 2:
    print(__doc__); sys.exit(1)
tool = sys.argv[1] if os.path.isabs(sys.argv[1]) else os.path.join(HERE, sys.argv[1])
cmd = [sys.executable, tool, *sys.argv[2:]]
code, out = run(cmd)
if stalled(code, out):
    print("run: tool stalled; checking for kit updates...", file=sys.stderr)
    u = subprocess.run([sys.executable, os.path.join(HERE, "update.py")], capture_output=True, text=True)
    print(u.stdout.strip(), file=sys.stderr)
    if u.returncode == 2:
        print("run: new fixes pulled; retrying once.", file=sys.stderr)
        code, out = run(cmd)
    else:
        print("run: no newer version to try; see docs/TROUBLESHOOTING.md.", file=sys.stderr)
print(out, end="")
sys.exit(code)
