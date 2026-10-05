"""Pre-commit guard for the PUBLIC kit: blocks committing private data.
Blocks: any staged path under me/, secret-looking files, and any staged text containing the user's
email / phone / full name from me/profile.json. Installed by install.sh / install.ps1 as .git/hooks/pre-commit.
Bypass only if you are sure: git commit --no-verify
"""
import json, os, re, subprocess, sys
root = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True).stdout.strip()
staged = [p for p in subprocess.run(["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"], capture_output=True, text=True, cwd=root).stdout.splitlines() if p]
bad = [p for p in staged if p == "me" or p.startswith("me/") or re.search(r"(^|/)\.env|\.(key|pem|p12|pfx)$|secret|credential|cookies|password", p, re.I)]
needles = []
try:
    pr = json.load(open(os.path.join(root, "me", "profile.json")))
    i = pr.get("identity", {})
    needles = [x for x in [i.get("email"), i.get("phone_local"), f"{i.get('first_name','')} {i.get('last_name','')}".strip()] if x and len(x) > 5]
except Exception:
    pass
leaks = []
for p in staged:
    if p in bad:
        continue
    blob = subprocess.run(["git", "show", f":{p}"], capture_output=True, cwd=root).stdout.decode("utf-8", "ignore")
    for n in needles:
        if n.lower() in blob.lower():
            leaks.append(f"{p} contains '{n[:3]}...'")
if bad or leaks:
    print("BLOCKED: this commit would publish private data:")
    for x in bad + leaks:
        print("  -", x)
    print("Remove it from the commit (git restore --staged <file>) or move it into me/. Override only if sure: git commit --no-verify")
    sys.exit(1)
