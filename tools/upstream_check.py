"""Check firstmate (the project our agent principles are adapted from) for relevant changes since our last review.

Usage:
  python3 tools/upstream_check.py                 # list relevant upstream commits since last review (exit 10 if any)
  python3 tools/upstream_check.py --diff          # also print the diff of watched files
  python3 tools/upstream_check.py --mark-reviewed # record upstream HEAD as reviewed (commit upstream.json afterwards)
Uses the public GitHub API (no token needed; set GITHUB_TOKEN to raise the rate limit).
"""
import datetime, json, os, sys, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG_PATH = os.path.join(ROOT, "upstream.json")
cfg = json.load(open(CFG_PATH))
API = f"https://api.github.com/repos/{cfg['repo']}"


def get(url, accept="application/vnd.github+json"):
    h = {"Accept": accept, "User-Agent": "job-hunt-upstream-check"}
    if os.environ.get("GITHUB_TOKEN"):
        h["Authorization"] = "Bearer " + os.environ["GITHUB_TOKEN"]
    with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=60) as r:
        body = r.read().decode()
    return json.loads(body) if "json" in accept else body


head = get(f"{API}/commits/{cfg['branch']}")["sha"]
if "--mark-reviewed" in sys.argv:
    cfg["last_reviewed"], cfg["last_reviewed_date"] = head, datetime.date.today().isoformat()
    json.dump(cfg, open(CFG_PATH, "w"), indent=2)
    print(f"marked reviewed at {head[:10]}; commit upstream.json")
    sys.exit(0)

if head == cfg["last_reviewed"]:
    print("No upstream changes since last review.")
    sys.exit(0)
cmp = get(f"{API}/compare/{cfg['last_reviewed']}...{head}")
watched = cfg["watch"]
files = [f for f in cmp.get("files", []) if any(f["filename"] == w or f["filename"].startswith(w) for w in watched)]
if not files:
    print(f"{cmp.get('total_commits', '?')} upstream commits, none touch the watched files. Run --mark-reviewed to skip them.")
    sys.exit(0)
print(f"Upstream {cfg['repo']}: {len(files)} watched file(s) changed since {cfg['last_reviewed'][:10]} ({cfg.get('last_reviewed_date')}).")
print(f"Compare: https://github.com/{cfg['repo']}/compare/{cfg['last_reviewed']}...{head}\n")
for f in files:
    print(f"- {f['filename']} (+{f.get('additions', 0)} -{f.get('deletions', 0)})")
titles = [c["commit"]["message"].splitlines()[0] for c in cmp.get("commits", [])]
print("\nRecent upstream commit titles (all files):")
for t in titles[-30:]:
    print("  *", t)
if "--diff" in sys.argv:
    for f in files:
        print(f"\n===== {f['filename']} =====\n{f.get('patch', '(diff too large; open the compare link)')}")
print(f"\nNext: read the changes, adapt anything useful into {cfg['maps_to']} in our own words, then run --mark-reviewed.")
sys.exit(10)
