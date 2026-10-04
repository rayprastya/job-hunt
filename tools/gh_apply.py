"""Fill a Greenhouse (job-boards.greenhouse.io) application in the current tab via the Brave bridge.

Usage: python3 gh_apply.py <tab> <answers-json> [--submit]
answers-json: {"text": {"label substring": "value"}, "select": {"label substring": "option text to type"}, "check": ["label/option substrings"]}
Identity fields and resume are built in. Without --submit it stops after filling (for captcha-protected boards).
"""
import json, os, sys, time, urllib.request
TAB = sys.argv[1]; ANS = json.load(open(sys.argv[2])); SUBMIT = "--submit" in sys.argv
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import me as ME
CV = ME.cv_path()

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
for sub, v in ANS.get("select", {}).items():
    ok = ev("(()=>{const e=[...document.querySelectorAll('input[role=combobox],input.select__input,input[type=text]')].find(e=>%s(e).toLowerCase().includes(%s));if(!e)return 0;e.scrollIntoView({block:'center'});e.focus();e.click();return 1})()" % (LAB, json.dumps(sub.lower())))
    if not ok: print("NO_SELECT", sub); continue
    raw("Input.insertText", {"text": v}); time.sleep(1.5); key("Enter", "Enter", 13); time.sleep(0.8)
for sub in ANS.get("check", []):
    r = ev("(()=>{const c=[...document.querySelectorAll('input[type=checkbox]')].find(c=>%s(c).toLowerCase().includes(%s));if(!c)return 'none';if(!c.checked)c.click();return c.checked})()" % (LAB, json.dumps(sub.lower())))
    if r != True: print("CHECK_FAIL", sub, r)
time.sleep(1)
print("STATE", ev("JSON.stringify([...document.querySelectorAll('input:not([type=hidden]):not([type=file]):not([type=checkbox]):not([type=search])')].map(e=>%s(e).slice(0,30)+'='+e.value.slice(0,30)).concat([...document.querySelectorAll('[class*=singleValue]')].map(s=>'sel:'+s.innerText)))" % LAB))
if SUBMIT:
    ev("(()=>{[...document.querySelectorAll('button')].find(b=>/submit/i.test(b.innerText)).click();return 1})()")
    time.sleep(10)
    print("RESULT", ev("location.href.slice(0,100)+' '+document.body.innerText.replace(/\\s+/g,' ').slice(0,300)"))
