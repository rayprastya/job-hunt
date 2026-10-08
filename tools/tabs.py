"""Close application tabs once a submission is confirmed, so the browser doesn't fill up with finished forms.

Library:  from tabs import close_tab; close_tab(tab)        (apply tools call this after a confirmed SUBMITTED)
CLI:      python3 tools/tabs.py sweep [--close]
  Looks at every open application tab (Ashby, Greenhouse, Lever, SmartRecruiters, BrioHR, Zoho, Breezy, Workable).
  A tab whose page says the application went through (e.g. you clicked Submit on a prefilled form) is listed,
  its tracker row is marked Applied, and with --close the tab is closed. Run sheet_push.py afterwards.
Set KEEP_TABS=1 to never close tabs.
"""
import csv, datetime, json, os, re, sys, urllib.request

B = os.environ.get("BRIDGE_URL", "http://127.0.0.1:9339")
ME = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "me")
ATS = re.compile(r"ashbyhq\.com|greenhouse\.io|lever\.co|smartrecruiters\.com|briohr\.com|zohorecruit|breezy\.hr|workable\.com|pmicareers\.com|mokahr\.com|career\.sea\.com")
DONE_TEXT = re.compile(r"successfully submitted|thank(s| you) for (applying|your application)|application (has been |was )?(submitted|received|sent)"
                       r"|we('ve| have) received your application", re.I)
DONE_URL = re.compile(r"/success|/thanks|/thank-you|thankyou|/confirmation|status=success", re.I)


def post(cmd, body, timeout=60):
    d = json.load(urllib.request.urlopen(urllib.request.Request(f"{B}/{cmd}", json.dumps(body).encode()), timeout=timeout))
    if not d["ok"]:
        raise RuntimeError(d["error"])
    return d.get("out")


def close_tab(tab):
    """Close a tab after a confirmed submission. Never raises: a tab that stays open is only clutter."""
    if os.environ.get("KEEP_TABS") or not tab:
        return
    try:
        post("close", {"id": tab})
        print(f"closed tab {tab}")
    except Exception as e:
        print(f"(could not close tab {tab}: {e})")


def job_root(url):
    """The posting part of an application URL, used to find its tracker row."""
    url = url.split("?")[0].split("#")[0].rstrip("/")
    return re.sub(r"/(application|apply|success|thanks|thank-you|confirmation)$", "", url)


def mark_applied(url):
    path = f"{ME}/tracker.csv"
    rows = list(csv.reader(open(path)))
    root, today = job_root(url), datetime.date.today()
    hit = None
    for r in rows[1:]:
        if r[5] and (job_root(r[5]) == root or root.startswith(job_root(r[5])) or job_root(r[5]).startswith(root)):
            hit = r
            break
    if not hit:
        return None
    if hit[9] == "Applied":
        return hit[1] + " - " + hit[2] + " (already Applied)"
    hit[9], hit[10], hit[14] = "Applied", today.isoformat(), (today + datetime.timedelta(days=7)).isoformat()
    hit[15] = ("Submitted (confirmed on the page). " + hit[15]).strip()
    with open(path, "w", newline="") as f:
        csv.writer(f).writerows(rows)
    return hit[1] + " - " + hit[2] + " marked Applied"


def sweep(close):
    tabs = post("list", {}) or []
    found = 0
    for t in tabs:
        url = t.get("url", "")
        if not ATS.search(url):
            continue
        try:
            text = post("eval", {"id": t["id"], "expr": "document.body ? document.body.innerText.slice(0, 4000) : ''"}, timeout=8) or ""
        except Exception:
            continue
        if not (DONE_TEXT.search(text) or DONE_URL.search(url)):
            continue
        found += 1
        row = mark_applied(url)
        print(f"DONE {url}  ->  " + (f"tracker: {row}" if row else "no tracker row matched (log it)"))
        if close:
            close_tab(t["id"])
    print(f"{found} finished application tab(s)")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "sweep":
        sweep("--close" in sys.argv)
    else:
        print(__doc__)
