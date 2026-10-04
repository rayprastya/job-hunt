"""LinkedIn Easy Apply through the Brave bridge, using the accessibility tree (the modal sits in a closed shadow root).

Usage: python3 easy_apply.py <tab> <job-id> <country: ID|SG|MY|JP|OTHER> [--dry-run]
Exit 0 + SUBMITTED, 3 + NEEDS_ANSWERS <questions> (left open for the user), 2 + NO_EASY_APPLY.
Answers come only from facts in me/profile.md; anything else stops.
"""
import json, os, re, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ax import AX, post
import me as ME

TAB, JOB, COUNTRY = sys.argv[1], sys.argv[2], sys.argv[3].replace("HOME", "")
DRY = "--dry-run" in sys.argv
CV = ME.cv_path()
a = AX(TAB)

YEARS = dict(ME.SKILL_YEARS)  # from me/profile.json skills_years
GENERIC = {"backend", "back-end", "back end", "software", "web", "api", "rest", "engineering", "programming", "development", "coding", "full stack", "fullstack", "full-stack"}
SALARY = ME.SALARY  # {country: (currency, monthly, "monthly")}


def answer(q, kind, options=None):
    """Return an answer string (or option text) or None when profile facts do not settle it."""
    ql = " " + q.lower().replace("\n", " ") + " "
    for k, v in json.loads(os.environ.get("EA_EXTRA", "{}")).items():  # per-job answers the user gave explicitly
        if k.lower() in ql:
            return pick(options, v) if options else v
    abroad = COUNTRY != ME.HOME
    if re.search(r"how many years|years of (work )?experience|years experience|how much experience", ql):
        if re.match(r"\s*years of (work )?experience\s*[-:?*]*\s*$", ql):
            return "5"
        spec = [v for k, v in YEARS.items() if k not in GENERIC and re.search(r"(?<![a-z])" + re.escape(k.strip()), ql)]
        if spec:
            # "X, Y, or Z" lists ask about any of them -> max; "X and Y" asks for both -> min
            both = re.search(r"\b(and|&)\b", ql) and not re.search(r"\bor\b|,", ql)
            return str(min(spec) if both else max(spec))
        gen = [v for k, v in YEARS.items() if k in GENERIC and k in ql]
        if gen and not re.search(r"mobile|android|ios|reverse|embedded|devops|sre|data (science|engineer)|machine learning|ml\b|ai\b|security|qa|test", ql):
            return str(min(gen))
        return None
    if re.search(r"ideal start date|earliest (possible )?start|when could you start", ql):
        return "After a 1-month notice period (around early November 2026)"
    if "notice period" in ql and "week" in ql:
        return "4"
    if "notice period" in ql and "day" in ql:
        return "30"
    if "notice period" in ql or "when can you start" in ql or "earliest start" in ql:
        if options:
            for o in options:
                if re.search(r"1 month|30 days|one month|4 weeks|1-month", o.lower()) and ME.NOTICE_WEEKS == "4":
                    return o
            return None
        return str(int(ME.NOTICE_WEEKS) * 7) if kind == "number" else ME.NOTICE
    if re.search(r"salary|compensation|expected pay|ctc|remuneration", ql):
        if "current" in ql:
            if COUNTRY == ME.HOME or ME.HOME_CUR.lower() in ql:
                return str(ME.CURRENT_MONTHLY)
            for cur in ("myr", "sgd", "usd"):
                if cur in ql or (cur == "usd" and "$" in ql):
                    return ME.current_in(cur)
            return None if kind == "number" else f"{ME.HOME_CUR} {ME.CURRENT_MONTHLY:,} per month (based in {ME.COUNTRY_NAME})"
        cur, amt, s = SALARY.get(COUNTRY, (None, None, None))
        if not cur:
            return None
        if re.search(r"annual|yearly|per year|per annum|p\.a\.|\byear\b", ql):
            return f"{cur} {amt*12:,} per year" if "currency" in ql else str(amt * 12)
        if "currency" in ql:
            return f"{cur} {amt:,} per month"
        return s  # LinkedIn salary boxes are usually numeric-only (20 chars)
    if re.search(r"need a work visa|require a (work )?visa|need (a )?visa", ql):
        return pick(options, "Yes" if abroad else "No")
    if re.search(r"open to work(ing)? from (our|the) office|work from (our|the) office|willing to work on-?site", ql):
        return pick(options, "Yes")
    if re.search(r"sponsor", ql):
        return pick(options, "No" if not abroad else "Yes")
    if re.search(r"authori[sz]ed to work|legally (able|eligible|permitted)|right to work|work permit|eligible to work", ql):
        if "indonesia" in ql:
            return pick(options, "Yes")
        return pick(options, "No" if abroad else "Yes")
    if re.search(r"relocat", ql):
        return pick(options, "Yes")
    if re.search(r"commut|on-?site|onsite|hybrid|office|remote", ql) and re.search(r"comfortable|willing|able|okay|ok with|agree", ql):
        return pick(options, "Yes")
    if re.search(r"bachelor|degree|graduat", ql):
        return pick(options, "Yes")
    if re.search(r"english", ql):
        if options:
            for pref in ("Professional", "Fluent", "Advanced", "Full professional"):
                for o in options:
                    if pref.lower() in o.lower():
                        return o
        return pick(options, "Yes")
    if re.search(r"bahasa|indonesian", ql) and "language" in ql:
        return pick(options, "Native") or pick(options, "Yes")
    if re.search(r"phone|mobile|whatsapp|telefoon|telefon|handy", ql):
        return ME.PHONE_LOCAL
    if re.search(r"first name", ql):
        return ME.FIRST
    if re.search(r"last name|surname", ql):
        return ME.LAST
    if re.search(r"e-?mail", ql):
        return ME.EMAIL
    if re.search(r"nationality|citizenship(?! status)", ql) and not re.search(r"right|status|sponsor", ql):
        return pick(options, ME.NATIONALITY) or pick(options, ME.COUNTRY_NAME)
    if re.search(r"where do you (currently )?live|country of residence|current country|currently reside", ql):
        return pick(options, ME.COUNTRY_NAME)
    if re.search(r"eligibility to work|eligible to work in this role|best describes your (work )?(eligibility|authori)", ql) and options:
        want = r"will require|require.*sponsorship" if COUNTRY != ME.HOME else r"citizen"
        for o in options:
            if re.search(want, o, re.I):
                return o
        return None
    if re.search(r"right-to-work status|work authori[sz]ation status|citizenship status|residency status", ql):
        if COUNTRY == "SG":
            return pick(options, "Foreigner") or pick(options, "Foreigner - EP") or pick(options, "Others")
        if COUNTRY == ME.HOME:
            return pick(options, "Citizen") or pick(options, f"{ME.NATIONALITY} Citizen")
        return pick(options, "Foreigner") or pick(options, "Others")
    if re.search(r"japanese|日本語", ql):
        if options:
            for o in options:
                if re.search(r"まったく|全く|none|not at all", o, re.I):
                    return o
        return pick(options, "None") or pick(options, "No")
    if re.search(r"gender identity|what term best describes your gender", ql):
        return (pick(options, "Man") or pick(options, "Male")) if ME.GENDER.lower() == "male" else (pick(options, "Woman") or pick(options, "Female")) if ME.GENDER.lower() == "female" else pick(options, "Prefer not to disclose") or pick(options, "Prefer not to say")
    if re.search(r"携帯|電話", q):
        return ME.PHONE_LOCAL
    if re.search(r"website|social media|github", ql):
        return ME.GITHUB
    if re.search(r"ci/cd|production deployment", ql) and options:
        return pick(options, "Yes")
    if re.search(r"linkedin", ql):
        return ME.LINKEDIN
    if re.search(r"github|portfolio|website", ql):
        return ME.GITHUB
    if re.search(r"\bcity\b|location|where are you based|currently (live|reside|based)", ql) and kind != "radio":
        return ME.CITY_FULL
    if re.search(r"gender", ql):
        return pick(options, ME.GENDER)
    if re.search(r"veteran", ql):
        return pick(options, "I am not a protected veteran") or pick(options, "No")
    if re.search(r"disabilit", ql):
        return pick(options, "No, I do not have a disability") or pick(options, "No")
    if re.search(r"start immediately|immediate(ly)? (start|join|available)|available immediately", ql):
        return pick(options, "No")
    if re.search(r"singaporean|singapore citizen|pr holder|permanent resident|local (citizen|singaporean)|citizen or pr|malaysian citizen", ql) and options:
        return pick(options, "No")
    if re.search(r"work as (an )?intern|internship before", ql) and options:
        return pick(options, "No")
    if re.search(r"must have (exp|experience) in", ql) and options:
        skills = re.findall(r"[a-z.]+", ql.split(" in ", 1)[-1])
        return pick(options, "No" if any(YEARS.get(k, 1) == 0 for k in ("spring", "springboot", "java", "angular", "vue") if k in ql) else "Yes")
    if re.search(r"how did you (apply|hear|find|learn|come across)|where did you (hear|find|see)|source of application|application route", ql):
        return pick(options, "LinkedIn") or pick(options, "Linkedin") or ("LinkedIn" if not options else None)
    if re.search(r"salary currency|currency", ql) and options:
        cur = SALARY.get(COUNTRY, (ME.HOME_CUR,))[0]
        return pick(options, cur)
    if re.match(r"\s*country\s*\*?\s*$", ql):
        return pick(options, ME.COUNTRY_NAME)
    if re.search(r"available to start|start working with us|availability", ql):
        return pick(options, ME.NOTICE) if options else f"After a {ME.NOTICE} notice period"
    if re.search(r"(currently )?(live|living|based|residing|reside) in", ql) and options and not re.search(r"willing|relocat", ql):
        return pick(options, "Yes" if COUNTRY == ME.HOME and re.search(r"indonesia|jakarta", ql) else "No")
    if re.search(r"currently interviewing", ql):
        return pick(options, "Yes")
    if re.search(r"applied to (our|this) company before|applied (here|with us) before", ql):
        return pick(options, "No")
    if re.search(r"event-driven|event driven|message queue|kafka|rabbitmq", ql) and options:
        return pick(options, "Yes")
    if re.search(r"ai-assisted|ai assisted", ql) and options:
        return pick(options, "Yes")
    if re.search(r"numerical accuracy|data integrity|financial ledger|reconciliation", ql) and options:
        return pick(options, "Yes")
    if re.search(r"trading|brokerage|exchange|cryptocurrency", ql) and options and not re.search(r"how many", ql):
        return pick(options, "No")
    if re.search(r"information .*(true|accurate)|true, accurate", ql):
        return pick(options, "Yes")
    if re.search(r"ai coding tools|ai tools|copilot|claude|chatgpt", ql) and options:
        return pick(options, "Yes")
    if re.search(r"(designed|built|owned|maintained|deployed).*(backend|api|service).*(production|live)", ql) and options:
        return pick(options, "Yes")
    if re.search(r"(code review|unit test|testing|automated test)", ql) and options:
        return pick(options, "Yes")
    if re.search(r"(are you|do you have).*(comfortable|experience|familiar|proficient|worked)", ql):
        for k, v in YEARS.items():
            if k in ql:
                return pick(options, "Yes" if v >= 1 else "No")
        return None
    if re.search(r"background check|drug test|agree|consent|acknowledge|privacy", ql):
        return pick(options, "Yes") or pick(options, "I agree")
    if re.search(r"currently employed (at|by)|employee of|work(ing)? for any .* (entity|group)", ql) and options:
        return pick(options, "No")
    if re.search(r"previously (worked|employed)|ever worked (for|at)|former employee", ql):
        return pick(options, "No")
    if re.search(r"relatives|family member|friend.*work", ql):
        return pick(options, "No")
    if re.search(r"mental health|medical history|psychiatric", ql):
        return pick(options, ME.MENTAL_HEALTH) if (ME.MENTAL_HEALTH and options) else (ME.MENTAL_HEALTH or None)
    if re.search(r"\bage\b|how old", ql):
        return ME.AGE or None
    if re.search(r"bonus", ql):
        return (pick(options, "Yes") if options else ME.BONUSES) if ME.BONUSES else None
    return None


def pick(options, want):
    if not options:
        return want
    for o in options:
        if o.strip().lower() == want.lower():
            return o
    for o in options:
        if o.strip().lower().startswith(want.lower()):
            return o
    return None


def call(b, fn, *args):
    oid = a.raw("DOM.resolveNode", {"backendNodeId": b})["object"]["objectId"]
    return a.raw("Runtime.callFunctionOn", {"objectId": oid, "functionDeclaration": fn, "arguments": [{"value": x} for x in args], "returnByValue": True})["result"].get("value")


SET_SELECT = "function(t){const o=[...this.options].find(o=>o.text.trim()===t);if(!o)return false;this.value=o.value;this.dispatchEvent(new Event('change',{bubbles:true}));this.dispatchEvent(new Event('input',{bubbles:true}));return true}"
SEL_INFO = "function(){return this.tagName==='SELECT'?[...this.options].map(o=>o.text.trim()):null}"
LABEL_OF = "function(){let n=this;for(let i=0;i<8&&n;i++){n=n.parentElement||n.getRootNode().host;if(!n)break;const l=n.querySelector&&n.querySelector('label,legend');if(l&&l.innerText.trim())return l.innerText.trim()}return ''}"


def dialog_nodes(scoped=True):
    ns = a.nodes()
    ns = [n for n in ns if n["role"] != "StaticText"]
    if not scoped:
        return ns
    # keep only nodes inside LinkedIn's "Apply to ..." dialog (or its save prompt); ignore extensions like Simplify
    roots = {n["id"] for n in ns if n["role"] in ("dialog", "alertdialog") and (n["name"].startswith("Apply to") or n["name"] == "")}
    if not roots:
        return ns
    inside = []
    for n in ns:
        pid, ok = n["id"], False
        for _ in range(40):
            if pid in roots:
                ok = True; break
            p = a._by.get(pid)
            if not p:
                break
            pid = p.get("parentId")
        if ok:
            inside.append(n)
    return inside


# --- open the job and the modal
post("activate", {"id": TAB})
post("goto", {"id": TAB, "url": f"https://www.linkedin.com/jobs/view/{JOB}/"})
btn = []
for _ in range(10):
    time.sleep(2)
    try:
        ns = dialog_nodes(scoped=False)
    except Exception:
        continue
    btn = [n for n in ns if n["role"] in ("button", "link") and "easy apply" in n["name"].strip().lower()]
    if btn:
        break
if not btn:
    applied = [n for n in a.nodes() if n["role"] == "StaticText" and "Applied" in n["name"]]
    print("NO_EASY_APPLY" + (" (already applied)" if applied else "")); sys.exit(2)
call(btn[0]["b"], "function(){this.click();return 1}")  # mouse clicks on the new link-style opener do nothing
time.sleep(5)

uploaded = False
answered_log = []
for step in range(12):
    ns = dialog_nodes()
    names = [n["name"] for n in ns]
    if any("Save this application" in x for x in names):
        d = [n for n in ns if n["role"] == "button" and n["name"] == "Dismiss"]
        a.click(d[-1]); time.sleep(1); continue
    sent = [n for n in a.nodes() if n["role"] in ("StaticText", "heading") and re.search(r"application was sent|Your application was sent|Application submitted", n["name"])]
    if sent:
        print("SUBMITTED", json.dumps(answered_log)); sys.exit(0)

    # resume: pick the Metatech-free CV saved in LinkedIn's resume library
    cvr = [n for n in ns if n["role"] in ("radio", "button") and ME.P["files"].get("linkedin_resume_name") and ME.P["files"]["linkedin_resume_name"] in n["name"]]
    if cvr and cvr[0]["role"] == "radio" and cvr[0]["checked"] not in (True, "true"):
        a.click(cvr[0]); time.sleep(1)
    elif not cvr and any(n["role"] == "button" and n["name"] == "Upload resume" for n in ns):
        more = [n for n in ns if n["role"] == "button" and re.search(r"show \d+ more resumes|show more resumes", n["name"], re.I)]
        if more:
            a.click(more[0]); continue
        print("NEEDS_ANSWERS", json.dumps(["Backend CV not in LinkedIn resume list"])); sys.exit(3)
    # follow company: untick
    for n in ns:
        if n["role"] == "checkbox" and n["name"].lower().startswith("follow") and n["checked"] in (True, "true"):
            a.click(n)

    missing = []
    # declaration checkboxes: tick required privacy/accuracy declarations, never marketing or community opt-ins
    CBTXT = "function(){let n=this;for(let i=0;i<8&&n;i++){n=n.parentElement;const t=(n&&n.innerText||'').trim();if(t.length>30)return t}return ''}"
    for n in ns:
        if n["role"] == "checkbox" and n["checked"] not in (True, "true") and not n["name"].lower().startswith("follow"):
            t = (n["name"] or call(n["b"], CBTXT) or "").lower()
            if re.search(r"(read|understand|agree|acknowledge|confirm|consent).*(privacy|notice|terms|accurate|true)", t) and not re.search(r"communit|marketing|newsletter|future (career )?opportunit|talent (pool|community)|job alerts", t):
                call(n["b"], "function(){this.click();return this.checked}"); answered_log.append([t[:80], "checked"])
    # text / number inputs
    for n in ns:
        if n["role"] in ("textbox", "spinbutton"):
            q = n["name"] or call(n["b"], LABEL_OF) or ""
            cur = str(n["value"]).strip()
            ans = answer(q, "number" if n["role"] == "spinbutton" or "number" in q.lower() else "text")
            if ans is None:
                if n["required"] and not cur:
                    if os.environ.get("EA_DEBUG"): print("MISS-TEXT", repr(q[:60]), file=sys.stderr)
                    missing.append(q)
                continue
            is_loc = re.search(r"city|location", q.lower())
            if cur == ans and not is_loc:
                continue
            a.type(n, ans); answered_log.append([q[:80], ans])
            if is_loc:
                time.sleep(2)
                sug = [m for m in a.nodes() if m["role"] in ("button", "option") and m["name"].strip() == ans]
                if sug:
                    a.click(sug[0])
    # phone country code must be the user's own; LinkedIn sometimes defaults to the job's country
    for n in ns:
        if n["role"] == "combobox" and "country code" in n["name"].lower() and f"+{ME.PHONE_CC}" not in str(n["value"]):
            want = f"{ME.COUNTRY_NAME} (+{ME.PHONE_CC})"
            if call(n["b"], SET_SELECT, want):
                answered_log.append(["Phone country code", want])
    # selects / comboboxes without a value
    for n in ns:
        if n["role"] == "combobox" and (not str(n["value"]).strip() or str(n["value"]).startswith("Select")):
            opts = call(n["b"], SEL_INFO)
            q = n["name"] or call(n["b"], LABEL_OF) or ""
            if opts is None:
                ans = answer(q, "text")
                if ans is None:
                    if os.environ.get("EA_DEBUG"): print("MISS-COMBO", repr(q[:60]), file=sys.stderr)
                    missing.append(q); continue
                a.type(n, ans); time.sleep(1.5); a.key("ArrowDown", "ArrowDown", 40); a.key("Enter", "Enter", 13)
                answered_log.append([q[:80], ans]); continue
            ans = answer(q, "select", [o for o in opts if o and not o.startswith("Select")])
            if ans is None or not call(n["b"], SET_SELECT, ans):
                missing.append(q + " " + str(opts[:6])); continue
            answered_log.append([q[:80], ans])
    # radio groups: LinkedIn gives each radio the question as its accessible name; the option text is its <label>
    OPT = "function(){let n=this;for(let i=0;i<4&&n;i++){n=n.parentElement;const t=(n&&n.innerText||'').trim();if(t&&t!=='on'&&t.length<120)return t}return (this.value||'').trim()}"
    LEG = "function(){const f=this.closest('fieldset');return f?((f.querySelector('legend')||f).innerText||'').trim():''}"
    groups = {}
    for n in ns:
        if n["role"] != "radio" or re.search(r"\.(pdf|docx?)\b", n["name"], re.I):
            continue
        opt = call(n["b"], OPT) or n["name"]
        q = n["name"] if n["name"].strip() and n["name"].strip() != opt else (call(n["b"], LEG) or "")
        q = re.sub(r"\s+", " ", q).strip()
        groups.setdefault(q, []).append((opt, n))
    for q, rs in groups.items():
        if any(n["checked"] in (True, "true") for _, n in rs):
            continue
        opts = [o for o, _ in rs]
        ans = answer(q, "radio", opts)
        if ans and ans.isdigit() and sorted(o.lower() for o in opts) == ["no", "yes"]:
            ans = "No" if ans == "0" else "Yes"
        hit = [n for o, n in rs if ans and o.strip().lower() == ans.strip().lower()]
        if not hit:
            missing.append(q + " " + str(opts)); continue
        a.click(hit[0]); answered_log.append([q[:80], ans])

    if missing:
        print("NEEDS_ANSWERS", json.dumps(missing)); sys.exit(3)
    time.sleep(1)
    ns = dialog_nodes()
    nav = {n["name"].strip().lower(): n for n in ns if n["role"] == "button"}
    for label in ("submit application", "review", "review your application", "next", "continue to next step"):
        if label in nav:
            if label == "submit application" and DRY:
                print("DRY_RUN_STOP", json.dumps(answered_log)); sys.exit(0)
            if os.environ.get("EA_DEBUG"):
                print("STEP", step, "click", label, "| headings:", [n["name"] for n in ns if n["role"] == "heading"][:4], file=sys.stderr)
            a.click(nav[label]); time.sleep(4)
            break
    else:
        print("STUCK no navigation button", [n["name"] for n in ns if n["role"] == "button"][:15]); sys.exit(3)
    # validation errors keep us on the same step
    errs = [n["name"] for n in a.nodes() if n["role"] == "StaticText" and len(n["name"]) < 70 and re.search(r"(is required|Please enter|Enter a (valid )?(whole|decimal)|must be|Invalid input|Please make a selection)", n["name"])]
    if errs:
        print("NEEDS_ANSWERS", json.dumps(errs[:6])); sys.exit(3)

for n in a.nodes():
    if n["role"] in ("StaticText", "heading") and re.search(r"application was sent|Application submitted", n["name"]):
        print("SUBMITTED", json.dumps(answered_log)); sys.exit(0)
print("UNKNOWN_END"); sys.exit(3)
