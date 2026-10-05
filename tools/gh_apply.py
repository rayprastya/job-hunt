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
    d = json.load(urllib.request.urlopen(urllib.request.Request(os.environ.get("BRIDGE_URL", "http://127.0.0.1:9339") + "/" + c, json.dumps(b).encode()), timeout=60))
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
    """react-select: open the control under the label and click the matching option. Retries because menus render
    late and a click can just close another open menu; types a short prefix for long lists."""
    ctrl = ("(()=>{const l=[...document.querySelectorAll('label')].find(l=>l.innerText.toLowerCase().includes(%s));"
            "let n=l;for(let i=0;i<5&&n;i++){n=n.parentElement;const c=n&&n.querySelector('[class*=select__control]');if(c)return c}return null})()") % json.dumps(label_sub.lower())
    pick = ("[...document.querySelectorAll('[class*=select__option]')].filter(o=>o.offsetParent)"
            ".find(o=>o.innerText.trim().toLowerCase().startsWith(%s))") % json.dumps(option.lower())
    if not ev("!!" + ctrl):
        return "no field"
    for attempt in range(3):
        click_el(ctrl)
        for _ in range(6):
            if ev("[...document.querySelectorAll('[class*=select__option]')].some(o=>o.offsetParent)"):
                break
            time.sleep(0.5)
        if click_el(pick):
            return "ok"
        if attempt == 1:
            # 1) type a short prefix to filter (full text can filter everything out)
            raw("Input.insertText", {"text": option[:4]}); time.sleep(1.2)
            if click_el(pick):
                return "ok"
            # 2) no luck typing: clear the filter and scroll through the list until the option shows up
            for _ in range(4):
                raw("Input.dispatchKeyEvent", {"type": "rawKeyDown", "key": "Backspace", "code": "Backspace", "windowsVirtualKeyCode": 8})
            time.sleep(0.8)
            for _ in range(40):
                if click_el(pick):
                    return "ok"
                more = ev("(()=>{const m=document.querySelector('[class*=select__menu-list]');if(!m)return false;const before=m.scrollTop;m.scrollTop+=m.clientHeight*0.8;return m.scrollTop>before})()")
                if not more:
                    break
                time.sleep(0.3)
        raw("Input.dispatchKeyEvent", {"type": "rawKeyDown", "key": "Escape", "code": "Escape", "windowsVirtualKeyCode": 27})
        time.sleep(0.5)
    return "no option"


ev("(()=>{document.querySelectorAll('[aria-expanded=true]').forEach(e=>e.blur());return 1})()")
# address country (required on many boards): its label is exactly "Country"
phone_country_note = bool(ev("!!document.getElementById('country')"))  # flyout picker: not automated yet (see TROUBLESHOOTING)
for sub, v in ANS.get("select", {}).items():
    r = gh_select(sub, v)
    if r != "ok":
        print("SELECT_FAIL", sub, r)
for sub in ANS.get("check", []):
    r = ev("(()=>{const c=[...document.querySelectorAll('input[type=checkbox]')].find(c=>%s(c).toLowerCase().includes(%s));if(!c)return 'none';if(!c.checked)c.click();return c.checked})()" % (LAB, json.dumps(sub.lower())))
    if r != True: print("CHECK_FAIL", sub, r)
time.sleep(1)
print("STATE", ev("JSON.stringify([...document.querySelectorAll('input:not([type=hidden]):not([type=file]):not([type=checkbox]):not([type=search])')].map(e=>%s(e).slice(0,30)+'='+e.value.slice(0,30)).concat([...document.querySelectorAll('[class*=singleValue]')].map(s=>'sel:'+s.innerText)))" % LAB))
if phone_country_note:
    print("CHECK: pick your phone country (" + ME.COUNTRY_NAME + ") in the form's Country field before submitting")
if SUBMIT:
    ev("(()=>{[...document.querySelectorAll('button')].find(b=>/submit/i.test(b.innerText)).click();return 1})()")
    time.sleep(10)
    print("RESULT", ev("location.href.slice(0,100)+' '+document.body.innerText.replace(/\\s+/g,' ').slice(0,300)"))
