"""Push new rows from me/tracker.csv into the Google Sheet by typing in the browser (tools/cdpd.mjs bridge).

Usage: python3 sheet_push.py <tab-id>
Rewrites the whole sheet from A1 (header + every row), so status changes sync too.
"""
import csv, json, os, sys, time, urllib.request

TAB = sys.argv[1]
ME = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "me")
SHEET = open(f"{ME}/config.md").read().split("Tracker sheet:")[1].split()[0]
B = "http://127.0.0.1:9339"


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


rows = list(csv.reader(open(f"{ME}/tracker.csv")))  # header + all rows; rewrites the sheet from A1

post("activate", {"id": TAB})
post("goto", {"id": TAB, "url": SHEET.split("#")[0].split("?")[0] + "#gid=0&range=A1"})
for _ in range(30):
    time.sleep(1)
    try:
        if post("eval", {"id": TAB, "expr": "!!document.querySelector('#t-name-box')"}):
            break
    except Exception:
        pass
time.sleep(3)
post("eval", {"id": TAB, "expr": "(()=>{document.querySelector('.waffle-name-box, #t-name-box');return 1})()"})
tsv = "\n".join("\t".join(("'" + v if v[:1] in "=+-@" else v).replace("\n", " ").replace("\t", " ") for v in r) for r in rows)
post("eval", {"id": TAB, "expr": """(()=>{const dt=new DataTransfer();dt.setData('text/plain',%s);
const t=document.activeElement;t.dispatchEvent(new ClipboardEvent('paste',{clipboardData:dt,bubbles:true,cancelable:true}));return t.tagName+'.'+t.className})()""" % json.dumps(tsv)})
time.sleep(3)
print(f"synced {len(rows)-1} rows")
