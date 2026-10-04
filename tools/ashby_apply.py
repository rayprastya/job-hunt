"""Fill and submit an Ashby application (jobs.ashbyhq.com/.../application) through the Brave bridge.

Usage: python3 ashby_apply.py <tab-id> <application-url> <answers-json> [--dry-run]
answers-json maps lowercase label substrings to answers; text answers are strings,
yes/no questions take "Yes"/"No". Built-in answers cover identity fields.
Any required field left empty after filling stops with NEEDS_ANSWERS (exit 3).
"""
import json, os, re, sys, time, urllib.request

TAB, URL, ANS = sys.argv[1], sys.argv[2], json.loads(open(sys.argv[3]).read())
DRY = "--dry-run" in sys.argv
COUNTRY = next((x.split("=")[1] for x in sys.argv if x.startswith("--country=")), "ID")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from answers import get_answer
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import me as ME
CV = ME.cv_path()
B = "http://127.0.0.1:9339"

BASE = {
    "full name": ME.FULL_NAME, "name": ME.FULL_NAME, "first name": ME.FIRST, "last name": ME.LAST, "middle name": "",
    "preferred name": ME.FIRST, "email": ME.EMAIL, "phone": ME.PHONE_INTL,
    "linkedin": ME.LINKEDIN, "github": ME.GITHUB, "website": ME.GITHUB, "portfolio": ME.GITHUB,
    "notice period": ME.NOTICE, "relatives": "No", "if yes, please state": "",
    "how did you": "LinkedIn", "hear about": "LinkedIn", "current location": ME.CITY_FULL,
    "location": ME.CITY_FULL, "nationality": ME.NATIONALITY, "gender": ME.GENDER,
}
BASE.update(ANS)


def post(cmd, body):
    d = json.load(urllib.request.urlopen(urllib.request.Request(f"{B}/{cmd}", json.dumps(body).encode()), timeout=60))
    if not d["ok"]:
        raise RuntimeError(d["error"])
    return d.get("out")


def ev(js):
    return post("eval", {"id": TAB, "expr": js})


def raw(m, p):
    return post("raw", {"id": TAB, "method": m, "params": p})


post("activate", {"id": TAB})
post("goto", {"id": TAB, "url": URL})
for _ in range(25):
    time.sleep(1)
    try:
        if ev("!!document.querySelector('input[type=file]')"):
            break
    except Exception:
        pass
time.sleep(2)

# resume: the system resume field, else the last file input
oid = raw("Runtime.evaluate", {"expression": "document.querySelector('#_systemfield_resume')||[...document.querySelectorAll('input[type=file]')].pop()"})["result"]["objectId"]
raw("DOM.setFileInputFiles", {"files": [CV], "objectId": oid})
time.sleep(6)

fields = json.loads(ev("""JSON.stringify([...document.querySelectorAll('[class*=fieldEntry]')].map((fe,i)=>{fe.dataset.fmIdx=i;
const lab=(fe.querySelector('label,legend')?.innerText||'').replace(/\\s+/g,' ').trim();
const inp=fe.querySelector('input:not([type=file]):not([type=hidden]),textarea');
const yn=[...fe.querySelectorAll('button')].filter(b=>/^(Yes|No)$/.test(b.innerText.trim())).length>0;
const radios=[...fe.querySelectorAll('input[type=radio],input[type=checkbox]')].map(r=>(r.closest('label')||r.parentElement).innerText.trim());
return {i,lab,type:yn?'yesno':(inp?inp.type||inp.tagName:'other'),req:/\\*\\s*$/.test(lab)||!!fe.querySelector('[required]'),val:inp?inp.value:'',radios}}))"""))

missing = []
for f in fields:
    lab = f["lab"].lower()
    if lab.startswith("resume") or lab.startswith("cv") or "cover letter" in lab or "upload" in lab or "document" in lab:
        continue
    ans = None
    for k in sorted(BASE, key=len, reverse=True):
        if (k == "name" and re.match(r"\s*name\s*\*?\s*$", lab)) or (k != "name" and re.search(r"(?<![a-z])" + re.escape(k), lab)):
            ans = BASE[k]
            break
    if ans is None:
        opts = ["Yes", "No"] if f["type"] == "yesno" else (f["radios"] or None)
        ans = get_answer(f["lab"], "radio" if opts else "text", opts, COUNTRY)
    if f["type"] == "yesno":
        if ans not in ("Yes", "No"):
            if f["req"]:
                missing.append(f["lab"])
            continue
        ev("""(()=>{const fe=document.querySelector('[data-fm-idx="%d"]');[...fe.querySelectorAll('button')].find(b=>b.innerText.trim()==='%s').click();return 1})()""" % (f["i"], ans))
    elif f["type"] in ("text", "email", "tel", "url", "textarea", "TEXTAREA", "number"):
        if ans is None:
            if f["req"] and not f["val"]:
                missing.append(f["lab"])
            continue
        if f["val"] and "location" not in lab:
            continue
        ev("""(()=>{const e=document.querySelector('[data-fm-idx="%d"]').querySelector('input:not([type=file]):not([type=hidden]),textarea');e.focus();e.select&&e.select();return 1})()""" % f["i"])
        if ans:
            raw("Input.insertText", {"text": ans})
        if "location" in lab:
            time.sleep(2)
            ev("""(()=>{const o=document.querySelector('[role=option]');if(o){o.dispatchEvent(new MouseEvent('mousedown',{bubbles:true}));o.click()}return 1})()""")
    elif f["radios"]:
        pick = ans if isinstance(ans, str) else None
        if pick and any(pick.lower() == r.lower() for r in f["radios"]):
            ev("""(()=>{const fe=document.querySelector('[data-fm-idx="%d"]');const r=[...fe.querySelectorAll('input[type=radio],input[type=checkbox]')].find(r=>(r.closest('label')||r.parentElement).innerText.trim().toLowerCase()===%s);r.click();return 1})()""" % (f["i"], json.dumps(pick.lower())))
        elif f["req"]:
            missing.append(f["lab"] + " " + str(f["radios"]))
    elif f["req"] and f["type"] == "other":
        missing.append(f["lab"])

time.sleep(1)
if missing:
    print("NEEDS_ANSWERS", json.dumps(missing)); sys.exit(3)
print("FILLED", ev("JSON.stringify([...document.querySelectorAll('[class*=fieldEntry]')].map(fe=>(fe.querySelector('label,legend')?.innerText||'').slice(0,30)+'='+((fe.querySelector('input:not([type=file]),textarea')||{}).value||[...fe.querySelectorAll('button[class*=active],button[aria-pressed=true]')].map(b=>b.innerText).join('')||'')).slice(0,25))"))
if DRY:
    print("DRY_RUN_STOP"); sys.exit(0)
ev("(()=>{[...document.querySelectorAll('button')].find(b=>/Submit Application/i.test(b.innerText)).click();return 1})()")
for _ in range(15):
    time.sleep(2)
    t = ev("document.body.innerText.slice(0,3000)")
    if "successfully submitted" in t.lower() or "thank you for applying" in t.lower() or "application was submitted" in t.lower():
        print("SUBMITTED"); sys.exit(0)
print("UNKNOWN_END", ev("[...document.querySelectorAll('[class*=error]')].map(e=>e.innerText).join(' | ').slice(0,500)")); sys.exit(3)
