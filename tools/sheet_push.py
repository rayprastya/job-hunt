"""Two-way sync between me/tracker.csv and the Google Sheet, through the browser (tools/cdpd.mjs bridge).

Usage: python3 sheet_push.py [tab-id] [--pull]   (without a tab id it opens its own tab)
The sheet is the source of truth: it is read first and merged into me/tracker.csv (anything you edited, added or
deleted in the sheet wins), then the merged tracker is written back to the sheet from A1.
--pull only reads the sheet into me/tracker.csv (run it before deciding whether a job was already applied).
me/.sheet_base.csv remembers what was last synced, so a change made on only one side is never overwritten.
"""
import csv, io, json, os, re, sys, time, urllib.request

ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
PULL_ONLY = "--pull" in sys.argv
TAB = ARGS[0] if ARGS else None
ME = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "me")
SHEET = open(f"{ME}/config.md").read().split("Tracker sheet:")[1].split()[0]
B = os.environ.get("BRIDGE_URL", "http://127.0.0.1:9339")


def post(cmd, body):
    d = json.load(urllib.request.urlopen(urllib.request.Request(f"{B}/{cmd}", json.dumps(body).encode()), timeout=60))
    if not d["ok"]:
        raise RuntimeError(d["error"])
    return d.get("out")


def raw(m, p=None):
    return post("raw", {"id": TAB, "method": m, "params": p or {}})


def key(k, code, vk):
    for t in ("rawKeyDown", "keyUp"):
        raw("Input.dispatchKeyEvent", {"type": t, "key": k, "code": code, "windowsVirtualKeyCode": vk})


BASE = f"{ME}/.sheet_base.csv"


def norm(v):
    return " ".join(str(v).replace("\t", " ").split())


def rkey(r):
    r = list(r) + [""] * 16
    return (norm(r[5]), norm(r[1]).lower(), norm(r[2]).lower())


def read_csv(path):
    return list(csv.reader(open(path))) if os.path.exists(path) else []


def merge(local, sheet, base):
    """3-way merge by (url, company, role). Sheet edits win; local-only changes are kept."""
    header = local[0] if local else sheet[0]
    L = {rkey(r): r for r in local[1:]}
    S = {rkey(r): r for r in sheet[1:] if any(c.strip() for c in r)}
    Bk = {rkey(r): r for r in base[1:]} if base else None
    out, seen = [], set()
    for k in [rkey(r) for r in local[1:]] + [rkey(r) for r in sheet[1:]]:
        if k in seen or (k not in L and k not in S):
            continue
        seen.add(k)
        l, s, b = L.get(k), S.get(k), (Bk or {}).get(k)
        if l and not s:
            if Bk is not None and b and all(norm(x) == norm(y) for x, y in zip(l, b)):
                continue  # deleted in the sheet, unchanged locally
            out.append(l)
        elif s and not l:
            if Bk is not None and b:
                continue  # deleted locally on purpose
            out.append((s + [""] * 16)[:16])
        else:
            row = []
            for i in range(16):
                lv, sv = (l + [""] * 16)[i], (s + [""] * 16)[i]
                bv = (b + [""] * 16)[i] if b else None
                if norm(lv) == norm(sv):
                    row.append(lv)
                elif bv is not None and norm(sv) == norm(bv):
                    row.append(lv)  # only the local side changed
                else:
                    row.append(sv)  # sheet changed (or no history): sheet wins
            out.append(row)
    return [header] + out


def write_csv(path, rows):
    with open(path, "w", newline="") as f:
        csv.writer(f).writerows(rows)


if TAB is None:
    TAB = post("raw", {"method": "Target.createTarget", "params": {"url": "about:blank"}})["targetId"]
post("activate", {"id": TAB})
GID = (re.search(r"gid=(\d+)", SHEET) or [None, "0"])[1]  # the tab in the saved link (default: first tab)
post("goto", {"id": TAB, "url": SHEET.split("#")[0].split("?")[0] + f"#gid={GID}&range=A1"})
for _ in range(30):
    time.sleep(1)
    try:
        if post("eval", {"id": TAB, "expr": "!!document.querySelector('#t-name-box')"}):
            break
    except Exception:
        pass
time.sleep(3)
sid = re.search(r"/d/([\w-]+)", SHEET)[1]
text = post("eval", {"id": TAB, "expr": "fetch('/spreadsheets/d/%s/gviz/tq?tqx=out:csv&headers=1&gid=%s',{credentials:'include'}).then(r=>r.ok?r.text():'ERR'+r.status)" % (sid, GID)})
if not text or text.startswith("ERR"):
    sys.exit(f"could not read the sheet ({text}); are you logged in to Google in this browser?")
sheet = list(csv.reader(io.StringIO(text)))
local = read_csv(f"{ME}/tracker.csv")
before = len(local) - 1
rows = merge(local, sheet, read_csv(BASE))
write_csv(f"{ME}/tracker.csv", rows)
print(f"pulled: sheet {len([r for r in sheet[1:] if any(r)])} rows, local {before} -> merged {len(rows)-1}")
if PULL_ONLY:
    write_csv(BASE, rows) if not os.path.exists(BASE) else None
    sys.exit(0)
PAD_ROWS = 60  # blank rows pasted after the data so rows removed from the tracker disappear from the sheet too
tsv = "\n".join("\t".join(("'" + v if v[:1] in "=+-@" else v).replace("\n", " ").replace("\t", " ") for v in r) for r in rows) + ("\n" + "\t" * 15) * PAD_ROWS
post("eval", {"id": TAB, "expr": """(()=>{const dt=new DataTransfer();dt.setData('text/plain',%s);
const t=document.activeElement;t.dispatchEvent(new ClipboardEvent('paste',{clipboardData:dt,bubbles:true,cancelable:true}));return t.tagName+'.'+t.className})()""" % json.dumps(tsv)})
time.sleep(3)
write_csv(BASE, rows)
print(f"synced {len(rows)-1} rows")
