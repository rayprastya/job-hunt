"""Fill and submit a SmartRecruiters one-click application through the Brave bridge (tools/cdpd.mjs).

Usage: python3 sr_apply.py <tab-id> <oneclick-apply-url> <message-file> [--dry-run]
Answers only what me/profile.md settles; any unknown screening question stops with exit 3.
"""
import json, os, re, sys, time, urllib.request

TAB, URL, MSG_FILE = sys.argv[1], sys.argv[2], sys.argv[3]
DRY = "--dry-run" in sys.argv
VISA = "yes" if "--visa-yes" in sys.argv else "no"
COUNTRY = next((x.split("=")[1] for x in sys.argv if x.startswith("--country=")), "OTHER" if VISA == "yes" else "ID")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from answers import get_answer
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import me as ME
CV = ME.cv_path()
B = "http://127.0.0.1:9339"

HELPERS = r"""
window.__deep=function(sel,root=document){const out=[];const walk=r=>{r.querySelectorAll(sel).forEach(e=>out.push(e));r.querySelectorAll('*').forEach(e=>{if(e.shadowRoot)walk(e.shadowRoot)})};walk(root);return out};
window.__label=e=>(e.getAttribute('aria-label')||e.placeholder||(e.labels&&e.labels[0]&&e.labels[0].innerText)||e.getRootNode().host?.getAttribute('label')||e.innerText||'').trim().slice(0,70);
window.__set=(e,v)=>{const p=e.tagName==='TEXTAREA'?HTMLTextAreaElement.prototype:HTMLInputElement.prototype;Object.getOwnPropertyDescriptor(p,'value').set.call(e,v);['input','change','blur'].forEach(t=>e.dispatchEvent(new Event(t,{bubbles:true,composed:true})))};
window.__click=b=>(b.shadowRoot?.querySelector('button')||b).click();
'ok'
"""


def post(cmd, body):
    req = urllib.request.Request(f"{B}/{cmd}", json.dumps(body).encode())
    d = json.load(urllib.request.urlopen(req, timeout=60))
    if not d["ok"]:
        raise RuntimeError(d["error"])
    return d.get("out")


def ev(js):
    return post("eval", {"id": TAB, "expr": js})


def wait(js, secs=20):
    for _ in range(secs):
        try:
            if ev(js):
                return True
        except Exception:
            pass
        time.sleep(1)
    return False


post("goto", {"id": TAB, "url": URL})
time.sleep(3)
if "/oneclick-ui/" not in URL:
    wait("document.readyState==='complete'")
    time.sleep(2)
    URL = post("eval", {"id": TAB, "expr": "([...document.querySelectorAll('a')].find(a=>/interested/i.test(a.innerText)&&a.href.includes('jobs.smartrecruiters.com/oneclick'))||{}).href||''"})
    if not URL:
        print("NO_APPLY_LINK"); sys.exit(2)
    post("goto", {"id": TAB, "url": URL})
    time.sleep(3)
wait("document.readyState==='complete'")
ev(HELPERS)
if not wait("(window.__deep||(()=>[]))('input[type=file]').length>0", 25):
    ev(HELPERS)
    if not wait("__deep('input[type=file]').length>0", 10):
        print("NO_FORM"); sys.exit(2)

# CV upload (autofills name/email/phone)
oid = post("raw", {"id": TAB, "method": "Runtime.evaluate", "params": {"expression": "__deep('input[type=file]').find(f=>/\\.pdf/.test(f.accept))"}})["result"]["objectId"]
post("raw", {"id": TAB, "method": "DOM.setFileInputFiles", "params": {"files": [CV], "objectId": oid}})
wait("(__deep('input').find(e=>e.id==='email-input')||{}).value", 20)

msg = open(MSG_FILE).read().strip()
ev("""(()=>{const q=id=>__deep('input,textarea').find(e=>e.id===id);
const set=(id,v)=>{const e=q(id);if(e&&!e.value)__set(e,v)};
set('first-name-input',%(first)s);set('last-name-input',%(last)s);set('email-input',%(email)s);
set('confirm-email-input',%(email)s);set('linkedin-input',%(li)s);
set('website-input',%(gh)s);
const m=q('hiring-manager-message-input');if(m)__set(m,%(msg)s);
const c=__deep('input').find(e=>/City/.test(__label(e)));if(c){__set(c,'');c.focus()}
return 'ok'})()""" % dict(first=json.dumps(ME.FIRST), last=json.dumps(ME.LAST), email=json.dumps(ME.EMAIL), li=json.dumps(ME.LINKEDIN), gh=json.dumps(ME.GITHUB), msg=json.dumps(msg)))
post("raw", {"id": TAB, "method": "Input.insertText", "params": {"text": ME.CITY}})
wait("__deep('div').some(d=>d.textContent.replace(/\\s+/g,' ').trim()===%s)" % json.dumps(ME.CITY_AUTOCOMPLETE), 10)
ev("""(()=>{const o=__deep('div').filter(d=>d.textContent.replace(/\\s+/g,' ').trim()===%s);const el=o[o.length-1];if(el){el.dispatchEvent(new MouseEvent('mousedown',{bubbles:true,composed:true}));el.click()}return o.length})()""" % json.dumps(ME.CITY_AUTOCOMPLETE))
time.sleep(1)
tel = ev("(__deep('input[type=tel]')[0]||{}).value||''")
if not tel:
    ev("(()=>{const t=__deep('input[type=tel]')[0];if(t)__set(t,%s);return 1})()" % json.dumps(ME.PHONE_LOCAL))

state = ev("""JSON.stringify({first:(__deep('input').find(e=>e.id==='first-name-input')||{}).value,
email:(__deep('input').find(e=>e.id==='email-input')||{}).value,
city:(__deep('input').find(e=>/City/.test(__label(e)))||{}).value,
tel:(__deep('input[type=tel]')[0]||{}).value})""")
print("FORM", state)
if DRY:
    print("DRY_RUN_STOP"); sys.exit(0)

ev("(()=>{const n=__deep('spl-button').find(b=>/^Next$/.test(b.textContent.trim()));if(n){__click(n)}return 1})()")
time.sleep(4)
# required privacy notice only (the one marked required); never the marketing consent
ev("""(()=>{__deep('input[type=checkbox]').forEach(c=>{const h=c.getRootNode().host;let n=h;for(let i=0;i<4&&n&&!(n.textContent||'').trim();i++)n=n.parentElement;const t=((n||h)?.textContent||'');if(/declare that you have read and agree|privacy notice|privacy policy|processing of your personal data/i.test(t)&&!/marketing|business updates/i.test(t)&&!c.checked)c.click()});return 1})()""")
ev("(()=>{__click(__deep('spl-button').find(b=>/^Submit$/.test(b.textContent.trim())));return 1})()")
time.sleep(6)

for _ in range(4):
    url = ev("location.href")
    if "/success" in url:
        print("SUBMITTED"); sys.exit(0)
    # Singapore citizenship-status select: foreign national needing sponsorship -> "Foreigner - EP"
    if ev("__deep('sr-question-field-select').some(q=>/citizenship status/i.test(q.textContent))"):
        ev("(()=>{const q=__deep('sr-question-field-select').find(q=>/citizenship status/i.test(q.textContent));const i=__deep('input',q.shadowRoot||q)[0];i.focus();i.click();return 1})()")
        time.sleep(2)
        ev("(()=>{const o=__deep('spl-dropdown-item').find(o=>o.textContent.replace(/\\s+/g,' ').trim()==='Foreigner - EP');o.dispatchEvent(new MouseEvent('mousedown',{bubbles:true,composed:true}));o.click();return 1})()")
        time.sleep(1)
    # generic select questions (sr-question-field-select): type the answer and pick the matching item
    sels = json.loads(ev("JSON.stringify(__deep('sr-question-field-select').map((q,i)=>{q.dataset.fmSel=i;return q.textContent.replace(/\\s+/g,' ').trim().slice(0,200)}))"))
    for i, lab in enumerate(sels):
        if re.search(r"citizenship status|voluntary|gender|ethnic|race", lab, re.I):
            continue
        filled = ev("(()=>{const q=__deep('sr-question-field-select')[%d];const i=__deep('input',q.shadowRoot||q)[0];return i?i.value:''})()" % i)
        if filled:
            continue
        ans = get_answer(lab, "text", None, COUNTRY)
        if not ans:
            continue
        ev("(()=>{const q=__deep('sr-question-field-select')[%d];const i=__deep('input',q.shadowRoot||q)[0];i.focus();i.click();return 1})()" % i)
        time.sleep(1)
        ev("(()=>{const q=__deep('sr-question-field-select')[%d];const o=__deep('spl-dropdown-item').filter(o=>o.offsetParent!==null||1).find(o=>o.textContent.replace(/\\s+/g,' ').trim().toLowerCase().startsWith(%s));if(o){o.dispatchEvent(new MouseEvent('mousedown',{bubbles:true,composed:true}));o.click();return 1}return 0})()" % (i, json.dumps(ans.lower()[:8])))
        time.sleep(1)
    qs = json.loads(ev("""JSON.stringify(__deep('spl-radio-group,spl-select,spl-input,spl-textarea,spl-checkbox-group').map(g=>({tag:g.tagName,q:g.textContent.replace(/\\s+/g,' ').trim().slice(0,200),opts:[...g.querySelectorAll('spl-radio,spl-checkbox')].map(r=>r.getAttribute('value')+'='+(r.getAttribute('label')||r.shadowRoot?.textContent||r.textContent||'').replace(/\\s+/g,' ').trim())})))"""))
    if not qs:
        print("UNKNOWN_STATE", url); sys.exit(3)
    answered_all = True
    unanswered = []
    for gi, q in enumerate(qs):
        text = q["q"]
        if q["tag"] == "SPL-INPUT" and not text:
            continue
        if False and ev("__deep('sr-question-field-select').some(q=>/citizenship status/i.test(q.textContent))"):
            continue
        if q["opts"]:
            labels = [o.split("=", 1)[1].strip() for o in q["opts"]]
            ans = get_answer(text, "radio", labels, COUNTRY)
            hit = [o.split("=", 1)[0] for o in q["opts"] if ans and o.split("=", 1)[1].strip().lower() == ans.lower()]
            if not hit:
                answered_all = False; unanswered.append(text); continue
            ev("""(()=>{const g=__deep('spl-radio-group,spl-checkbox-group').filter(g=>g.textContent.replace(/\\s+/g,' ').trim().startsWith(%s.slice(0,40)))[0];const r=[...g.querySelectorAll('spl-radio,spl-checkbox')].find(r=>r.getAttribute('value')==%s);(r.shadowRoot?.querySelector('input')||r).click();return 1})()""" % (json.dumps(text), json.dumps(hit[0])))
        else:
            ans = get_answer(text, "text", None, COUNTRY)
            if ans is None:
                answered_all = False; unanswered.append(text); continue
            ok = ev("""(()=>{const g=__deep('spl-input,spl-textarea').filter(g=>g.textContent.replace(/\\s+/g,' ').trim().startsWith(%s.slice(0,40)))[0];if(!g)return 0;const i=__deep('input,textarea',g.shadowRoot||g)[0]||g.querySelector('input,textarea');if(!i)return 0;i.focus();return 1})()""" % json.dumps(text))
            if not ok:
                answered_all = False; unanswered.append(text); continue
            post("raw", {"id": TAB, "method": "Input.insertText", "params": {"text": ans}})
    if not answered_all:
        print("NEEDS_ANSWERS", json.dumps(unanswered)); sys.exit(3)
    ev("(()=>{__click(__deep('spl-button').find(b=>/Submit|Next/.test(b.textContent)));return 1})()")
    time.sleep(6)
print("UNKNOWN_END", ev("location.href")); sys.exit(3)
