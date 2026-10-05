"""Apply on Sea Group career sites (career.sea.com, careers.monee.com, careers.garena.com, Shopee): no account needed.

Usage: python3 tools/sea_apply.py <tab> <posting-or-apply-url> [--dry-run]
Uploads the CV (the site autofills name, contact, education, experience), then sets current location, degree
classification, CGPA, sponsorship, referral channel and website from me/profile.json, ticks the terms and submits.
Needs education.gpa in the profile (e.g. "3.22/4.00"). Works in a headless browser.
Exit 0 + SUBMITTED, 3 + NEEDS_ANSWERS <what>, 1 + FAILED <why>.
"""
import json, re, sys, time
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ax import AX, post
import me as ME
from tabs import close_tab

TAB, URL = sys.argv[1], sys.argv[2]
DRY = "--dry-run" in sys.argv
a = AX(TAB)
P = json.load(open(os.path.join(ME.ME_DIR, "profile.json")))
EDU = P.get("education", {})
GPA = str(EDU.get("gpa") or "").strip()
if not GPA:
    print("NEEDS_ANSWERS education.gpa (Sea forms require CGPA like 3.50/4.00)"); sys.exit(3)
if "/" not in GPA:
    GPA = f"{float(GPA):.2f}/{float(EDU.get('gpa_scale') or 4):.2f}"
CLASSIFICATIONS = ["First-Class Honours", "Upper Second-Class Honours", "Lower Second-Class Honours", "Honours with Merit",
                   "Summa Cum Laude", "Magna Cum Laude", "High Merit", "Pass with Merit", "Pass"]
cls = str(EDU.get("classification") or "")
CLASS = next((c for c in CLASSIFICATIONS if c.lower() in cls.lower()), "Others / Not Applicable")


def ev(js):
    return post("eval", {"id": TAB, "expr": js})


def mouse(xy):
    for t in ("mousePressed", "mouseReleased"):
        a.raw("Input.dispatchMouseEvent", {"type": t, "x": xy[0], "y": xy[1], "button": "left", "clickCount": 1})
    time.sleep(1)


# Dropdown menus render in a class-less <div> at the end of <body>.
POPUP = "[...document.body.children].filter(e=>e.tagName=='DIV'&&!e.className)"


def popup_options():
    return [o.strip() for o in (ev(POPUP + ".map(e=>e.innerText).join('\\n')") or "").split("\n") if o.strip()]


def popup_click(text):
    xy = ev("(()=>{const m=%s.flatMap(e=>[...e.querySelectorAll('*')]).filter(x=>(x.innerText||String()).trim()===%s);"
            "const x=m[m.length-1];if(!x)return null;x.scrollIntoView({block:'nearest'});const r=x.getBoundingClientRect();"
            "return [r.x+r.width/2,r.y+r.height/2]})()" % (POPUP, json.dumps(text)))
    if xy:
        mouse(xy)
    return bool(xy)


# Find the first element matching `sel` that comes after the visible label text, in document order.
AFTER = """((label, sel) => {
  const lab = [...document.querySelectorAll('label,span,div,p,h3,h4')].find(e => [...e.childNodes].some(
    n => n.nodeType === 3 && n.textContent.trim().replace(/\\s*\\*$/, '').startsWith(label)));
  if (!lab) return null;
  return [...document.querySelectorAll(sel)].find(c => lab.compareDocumentPosition(c) & Node.DOCUMENT_POSITION_FOLLOWING) || null;
})"""


def center_of(label, sel):
    return ev("(()=>{const c=%s(%s,%s);if(!c)return null;c.scrollIntoView({block:'center'});const r=c.getBoundingClientRect();return [r.x+r.width/2,r.y+r.height/2]})()"
              % (AFTER, json.dumps(label), json.dumps(sel)))


def label_combobox(label):
    return center_of(label, "[role=combobox]")


def choose(label, pick):
    """pick: exact option text, or a function(options) -> option text."""
    xy = label_combobox(label)
    if not xy:
        return f"field '{label}' not found"
    mouse(xy)
    time.sleep(0.5)
    opts = popup_options()
    want = pick(opts) if callable(pick) else pick
    if want and popup_click(want):
        a.key("Escape", "Escape", 27)
        return None
    a.key("Escape", "Escape", 27)
    return f"'{label}': no option {want!r} in {opts[:20]}"


def set_text(label, value):
    """Replace the text of the input after `label` (focus, select all, type, so the page's framework sees it)."""
    xy = center_of(label, "input:not([type=file]):not([type=checkbox]),textarea")
    if not xy:
        return False
    mouse(xy)
    ev("(()=>{const i=document.activeElement;i.select&&i.select();return 1})()")
    a.key("Backspace", "Backspace", 8)
    a.raw("Input.insertText", {"text": value})
    time.sleep(0.3)
    a.key("Tab", "Tab", 9)
    return True


# 1. Open the application form.
apply_url = re.sub(r"/(position|job-detail)\b", "/apply", URL.split("?")[0]) if "/apply/" not in URL else URL
if "job-detail" in URL:
    apply_url = URL  # monee: click Apply on the detail page
post("goto", {"id": TAB, "url": apply_url})
for _ in range(20):
    time.sleep(1)
    try:
        if ev("!!document.querySelector('input[type=file]')"):
            break
        btn = ev("(()=>{const b=[...document.querySelectorAll('button,a')].find(e=>(e.innerText||String()).trim()==='Apply');if(b){b.click();return 1}return 0})()")
    except Exception:
        pass
time.sleep(2)
if not ev("!!document.querySelector('input[type=file]')"):
    print("FAILED no application form at", apply_url); sys.exit(1)
title = ev("(document.querySelector('h1,h2')||{}).innerText||document.title")

# 2. CV upload; the site parses it and autofills most fields.
files = a.find_file_inputs()
a.set_files(files[0][0], ME.cv_path())
for _ in range(20):
    time.sleep(1)
    if ev("[...document.querySelectorAll('input')].some(i=>i.value===%s)" % json.dumps(ME.FIRST)):
        break
time.sleep(2)

problems = []
if not ev("[...document.querySelectorAll('input')].some(i=>i.value===%s)" % json.dumps(ME.EMAIL)):
    set_text("Email Address", ME.EMAIL)
problems.append(choose("Current Location", lambda o: next((x for x in o if x.lower() == ME.COUNTRY_NAME.lower()), None)))
problems.append(choose("Degree Classification", CLASS))
if not set_text("Cumulative Grade Point Average", GPA):
    problems.append("CGPA field not found")
# Sponsorship: the posting's location line sits between the title and "Personal Information".
HOME_PLACES = {"ID": ["indonesia", "jakarta", "bandung", "surabaya", "bogor", "tangerang"], "SG": ["singapore"], "MY": ["malaysia", "kuala lumpur"]}
header = (ev("document.body.innerText.split('Personal Information')[0].slice(-400)") or "").lower()
home = HOME_PLACES.get(ME.HOME, []) + [ME.COUNTRY_NAME.lower(), ME.CITY.lower()]
needs_visa = not any(w and w in header for w in home)
problems.append(choose("Do you need, or will you need", "Yes" if needs_visa else "No"))
problems.append(choose("How did you know about this role", lambda o: next((x for x in o if "linkedin" in x.lower()), None)))
set_text("Website URL", "https://" + ME.LINKEDIN.split("://")[-1])
boxes = [n for n in a.nodes() if n["role"] == "checkbox"]
if boxes and boxes[-1]["checked"] != "true":
    a.click(boxes[-1])
box = "done" if [n for n in a.nodes() if n["role"] == "checkbox"][-1:] and [n for n in a.nodes() if n["role"] == "checkbox"][-1]["checked"] == "true" else "unchecked"
if box != "done":
    problems.append("could not tick the Terms and Conditions box")
problems = [p for p in problems if p]
if problems:
    print("NEEDS_ANSWERS", json.dumps(problems)); sys.exit(3)
if DRY:
    print("DRY_RUN_STOP", title); sys.exit(0)

xy = ev("(()=>{const b=[...document.querySelectorAll('button,div')].filter(e=>(e.innerText||String()).trim()==='Submit').pop();b.scrollIntoView({block:'center'});const r=b.getBoundingClientRect();return [r.x+r.width/2,r.y+r.height/2]})()")
mouse(xy)
for _ in range(15):
    time.sleep(1)
    txt = ev("document.body.innerText.slice(0,1500)")
    if "successfully submitted" in txt.lower() or "successful submission" in txt.lower():
        print("SUBMITTED", title); close_tab(TAB); sys.exit(0)
errs = ev("[...document.querySelectorAll('[id$=-message],[class*=error]')].map(e=>e.innerText.trim()).filter(Boolean).slice(0,8).join(' | ')")
print("FAILED not confirmed:", errs or txt[:300]); sys.exit(1)
