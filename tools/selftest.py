"""Checks a fresh install before the first run. Usage: python3 tools/selftest.py"""
import json, os, shutil, subprocess, sys, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
ok = True
def check(name, cond, hint=""):
    global ok
    print(("PASS " if cond else "FAIL ") + name + ("" if cond else f"  -> {hint}"))
    ok = ok and bool(cond)

u = subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "update.py")] + ([] if "--force-update" in sys.argv else ["--if-stale"]), capture_output=True, text=True)
if u.stdout.strip():
    print(u.stdout.strip())
if u.returncode == 2:
    print("Kit was updated; re-run this self-test to check the new version."); sys.exit(0)
check("kit update check", u.returncode in (0, 2), "see the update message above")
check("python 3.9+", sys.version_info >= (3, 9), "install Python 3.9 or newer")
node = shutil.which("node")
ver = subprocess.run([node, "--version"], capture_output=True, text=True).stdout.strip() if node else ""
check(f"node 22+ ({ver or 'missing'})", ver and int(ver.lstrip("v").split(".")[0]) >= 22, "install Node.js 22 LTS from nodejs.org (the bridge needs built-in WebSocket)")
try:
    import me as ME
    check("me/profile.json loads", True)
    check("name and email set", ME.FIRST and ME.EMAIL, "run python3 tools/onboard.py")
    check("home country code set", ME.HOME != "XX", "run python3 tools/onboard.py (two-letter code, e.g. ID)")
    check("CV file exists", os.path.exists(ME.cv_path()), f"put your CV at {ME.cv_path()} or fix files.cv in me/profile.json")
    check("skills_years filled", len(ME.SKILL_YEARS) >= 3, "add your skills and honest years in me/profile.json")
    cfg = os.path.join(ME.ME_DIR, "config.md")
    check("tracker sheet link in me/config.md", os.path.exists(cfg) and "docs.google.com" in open(cfg).read(), "run: python3 tools/sheet_create.py (creates it in your Google account and saves the link)")
    from answers import get_answer
    print("  sample answers:", {q: get_answer(q, "text", None, ME.HOME) for q in ["How many years of Python?", "notice period", "Mobile phone number"]})
except Exception as e:
    check("profile", False, f"{e} (run python3 tools/onboard.py)")
try:
    tabs = json.load(urllib.request.urlopen(urllib.request.Request(os.environ.get("BRIDGE_URL", "http://127.0.0.1:9339") + "/list", b"{}"), timeout=5))
    check("browser bridge running", tabs.get("ok"), "see docs/BROWSER.md")
except Exception:
    check("browser bridge running", False, "connect a browser: EITHER your normal browser (turn on brave://inspect/#remote-debugging, run node tools/cdpd.mjs, click Allow) OR the background profile (bash tools/browser-separate.sh, log in to LinkedIn+Google once, then --headless and CDP_PORT=9333 node tools/cdpd.mjs). The background profile cannot reuse your normal browser's logins. See docs/BROWSER.md")
print("\nAll good, you can start." if ok else "\nFix the FAIL lines above, then run this again.")
