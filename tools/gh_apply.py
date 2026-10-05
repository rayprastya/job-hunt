"""Fill a Greenhouse (job-boards.greenhouse.io) application in the current tab via the Brave bridge.

Usage: python3 gh_apply.py <tab> <answers-json> [--submit]
answers-json: {"text": {"label substring": "value"}, "select": {"label substring": "option text to type"}, "check": ["label/option substrings"]}
Identity fields and resume are built in. Without --submit it stops after filling (for captcha-protected boards).
"""
import json, os, sys, time, urllib.request
TAB = sys.argv[1]; ANS = json.load(open(sys.argv[2])); SUBMIT = "--submit" in sys.argv
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import me as ME
CV = ME.require_cv()

def post(c, b):
    d = json.load(urllib.request.urlopen(urllib.request.Request("http://127.0.0.1:9339/" + c, json.dumps(b).encode()), timeout=60))
    if not d["ok"]: raise RuntimeError(d["error"])
    return d.get("out")
def ev(js): return post("eval", {"id": TAB, "expr": js})
def raw(m, p): return post("raw", {"id": TAB, "method": m, "params": p})
def key(k, code, vk):
    for t in ("rawKeyDown", "keyUp"): raw("Input.dispatchKeyEvent", {"type": t, "key": k, "code": code, "windowsVirtualKeyCode": vk})

oid = raw("Runtime.evaluate", {"expression": "document.querySelector('#resume')"})["result"]["objectId"]
raw("DOM.setFileInputFiles", {"files": [CV], "objectId": oid}); time.sleep(5)
text = {"first_name": ME.FIRST, "last_name": ME.LAST, "email": ME.EMAIL, "phone": ME.PHONE_LOCAL}
for i, v in text.items():
    ev("(()=>{const e=document.getElementById('%s');if(!e)return 0;e.focus();e.select();return 1})()" % i)
    raw("Input.insertText", {"text": v})
LAB = "(e=>(document.querySelector('label[for=\"'+e.id+'\"]')?.innerText||e.getAttribute('aria-label')||''))"
for sub, v in ANS.get("text", {}).items():
    ok = ev("(()=>{const e=[...document.querySelectorAll('input[type=text],textarea')].find(e=>%s(e).toLowerCase().includes(%s));if(!e)return 0;e.focus();return 1})()" % (LAB, json.dumps(sub.lower())))
    if ok: raw("Input.insertText", {"text": v})
    else: print("NO_TEXT_FIELD", sub)
def click_el(expr):
    r = ev("(()=>{const e=%s;if(!e)return null;e.scrollIntoView({block:'center'});const b=e.getBoundingClientRect();return JSON.stringify([b.x+b.width/2,b.y+b.height/2])})()" % expr)
    if not r:
        return False
    x, y = json.loads(r)
    for t in ("mousePressed", "mouseReleased"):
        raw("Input.dispatchMouseEvent", {"type": t, "x": x, "y": y, "button": "left", "clickCount": 1})
    time.sleep(0.8)
    return True


def gh_select(label_sub, option):
    """react-select: open the control under the label, type to filter, click the first visible option."""
    ctrl = ("(()=>{const l=[...document.querySelectorAll('label')].find(l=>l.innerText.toLowerCase().includes(%s));"
            "let n=l;for(let i=0;i<5&&n;i++){n=n.parentElement;const c=n&&n.querySelector('[class*=select__control]');if(c)return c}return null})()") % json.dumps(label_sub.lower())
    if not click_el(ctrl):
        return "no field"
    raw("Input.insertText", {"text": option}); time.sleep(1.5)
    if not click_el("[...document.querySelectorAll('[class*=select__option]')].filter(o=>o.offsetParent)[0]"):
        return "no option"
    return "ok"


ev("(()=>{document.querySelectorAll('[aria-expanded=true]').forEach(e=>e.blur());return 1})()")
gh_select("country", ME.COUNTRY_NAME)  # address country (required on many boards)
for sub, v in ANS.get("select", {}).items():
    r = gh_select(sub, v)
    if r != "ok":
        print("SELECT_FAIL", sub, r)
for sub in ANS.get("check", []):
    r = ev("(()=>{const c=[...document.querySelectorAll('input[type=checkbox]')].find(c=>%s(c).toLowerCase().includes(%s));if(!c)return 'none';if(!c.checked)c.click();return c.checked})()" % (LAB, json.dumps(sub.lower())))
    if r != True: print("CHECK_FAIL", sub, r)
time.sleep(1)
print("STATE", ev("JSON.stringify([...document.querySelectorAll('input:not([type=hidden]):not([type=file]):not([type=checkbox]):not([type=search])')].map(e=>%s(e).slice(0,30)+'='+e.value.slice(0,30)).concat([...document.querySelectorAll('[class*=singleValue]')].map(s=>'sel:'+s.innerText)))" % LAB))
if SUBMIT:
    ev("(()=>{[...document.querySelectorAll('button')].find(b=>/submit/i.test(b.innerText)).click();return 1})()")
    time.sleep(10)
    print("RESULT", ev("location.href.slice(0,100)+' '+document.body.innerText.replace(/\\s+/g,' ').slice(0,300)"))
