"""Learned job preferences: "no-no" rules and things to prefer, kept in me/profile.json (machine-readable, used by
search_jobs.py) and logged in me/preferences.md (human-readable history of why each rule exists).

Usage:
  python3 tools/prefs.py list
  python3 tools/prefs.py avoid company "Acme Corp"            --reason "bad reviews"
  python3 tools/prefs.py avoid title "blockchain"             --reason "not interested in crypto roles"
  python3 tools/prefs.py avoid text "on-call 24/7"            --reason "no heavy on-call"   # matched in descriptions
  python3 tools/prefs.py avoid location "Surabaya"            --reason "won't relocate there"
  python3 tools/prefs.py avoid origin "India"                 --reason "no companies founded/HQ'd there"
  python3 tools/prefs.py prefer title "golang"                --reason "favourite stack"     # ranked first
  python3 tools/prefs.py remove avoid title "blockchain"
  python3 tools/prefs.py check "<title>" "<company>" "<location>" "<description>"   # explain a decision
Kinds: company, title, text, location, origin.
"""
import datetime, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PJ = os.path.join(ROOT, "me", "profile.json")
MD = os.path.join(ROOT, "me", "preferences.md")
KINDS = ("company", "title", "text", "location", "origin")


def load():
    p = json.load(open(PJ))
    prefs = p.setdefault("preferences", {})
    for side in ("avoid", "prefer"):
        prefs.setdefault(side, {})
        for k in KINDS:
            prefs[side].setdefault(k, [])
    # keep older profile fields in sync (skip_companies / skip_countries / skip_company_origins)
    t = p.get("target", {})
    for c in t.get("skip_companies", []):
        if c not in prefs["avoid"]["company"]:
            prefs["avoid"]["company"].append(c)
    for c in t.get("skip_countries", []):
        if c not in prefs["avoid"]["location"]:
            prefs["avoid"]["location"].append(c)
    for c in t.get("skip_company_origins", []):
        if c not in prefs["avoid"]["origin"]:
            prefs["avoid"]["origin"].append(c)
    return p


def save(p):
    json.dump(p, open(PJ, "w"), indent=2, ensure_ascii=False)


def log(line):
    if not os.path.exists(MD):
        open(MD, "w").write("# Job preferences (learned)\n\nRules the agent follows when choosing jobs. "
                            "Machine-readable copy: `preferences` in profile.json.\n\n## History\n")
    with open(MD, "a") as f:
        f.write(f"- {datetime.date.today().isoformat()}: {line}\n")


def match(prefs_side, title, company, location, desc):
    """Return the first matching rule (kind, value) or None."""
    low = {"title": title.lower(), "company": company.lower(), "location": location.lower(), "text": desc.lower()}
    for k in ("company", "title", "location", "text"):
        for v in prefs_side.get(k, []):
            if re.search(r"(?<![a-z0-9])" + re.escape(v.lower()) + r"(?![a-z0-9])", low[k]):
                return k, v
    for v in prefs_side.get("origin", []):
        # origin = where the company is from; flagged when the description repeatedly ties the company to it
        if len(re.findall(r"\b" + re.escape(v.lower()) + r"\b", low["text"])) >= 2 or v.lower() in low["company"]:
            return "origin", v
    return None


def check(title, company, location, desc):
    p = load()
    bad = match(p["preferences"]["avoid"], title, company, location, desc)
    good = match(p["preferences"]["prefer"], title, company, location, desc)
    return bad, good


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a or a[0] in ("-h", "--help"):
        print(__doc__); sys.exit(0)
    p = load()
    reason = ""
    if "--reason" in a:
        i = a.index("--reason"); reason = a[i + 1]; a = a[:i] + a[i + 2:]
    if a[0] == "list":
        for side in ("avoid", "prefer"):
            print(side.upper())
            for k in KINDS:
                if p["preferences"][side][k]:
                    print(f"  {k}: {', '.join(p['preferences'][side][k])}")
        save(p)
    elif a[0] in ("avoid", "prefer") and len(a) >= 3 and a[1] in KINDS:
        side, kind, val = a[0], a[1], a[2]
        if val not in p["preferences"][side][kind]:
            p["preferences"][side][kind].append(val)
        save(p)
        log(f"{side} {kind} \"{val}\"" + (f" ({reason})" if reason else ""))
        print(f"saved: {side} {kind} \"{val}\"")
    elif a[0] == "remove" and len(a) >= 4:
        side, kind, val = a[1], a[2], a[3]
        if val in p["preferences"][side][kind]:
            p["preferences"][side][kind].remove(val)
        save(p)
        log(f"removed {side} {kind} \"{val}\"" + (f" ({reason})" if reason else ""))
        print(f"removed: {side} {kind} \"{val}\"")
    elif a[0] == "check" and len(a) >= 3:
        bad, good = check(*(a[1:] + ["", "", ""])[:4])
        print("AVOID because", bad if bad else "-", "| PREFER because", good if good else "-")
    else:
        print(__doc__); sys.exit(1)
