"""Search LinkedIn for jobs matching me/profile.json, enrich them, filter, and save me/candidates.json.

Usage: python3 tools/search_jobs.py [--days 7] [--regions ID,SG,MY,JP,WW] [--keywords "Backend Engineer,Golang"] [--limit-pages 2]
Needs: the browser bridge (tools/cdpd.mjs) running and LinkedIn logged in in that browser.
Output: me/candidates.json, a list of {id, title, company, location, apply, url, applied, flags, desc}.
"""
import argparse, html, json, os, re, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import me as ME
from br import Bridge
import prefs as PREFS

GEO = {"ID": "102478259", "SG": "102454443", "MY": "106808692", "JP": "101355337", "WW": "92000000", "TH": "105146118",
       "VN": "104195383", "HK": "103291313", "TW": "104187078", "AE": "104305776", "NL": "102890719", "DE": "101282230",
       "AU": "101452733", "UK": "101165590", "PH": "103121230", "US": "103644278", "CA": "101174742", "IN": "102713980"}
BAD_TITLE = re.compile(r"intern\b|principal|staff|manager|director|head of|architect|\blead\b|frontend|front-end|mobile|android|ios\b|data scien|"
                       r"machine learning|\bml\b|\bqa\b|tester|test engineer|sre\b|site reliab|devops|security|salesforce|\bsap\b|embedded|"
                       r"sales|support|consultant|trainer|tutor|annotat|teacher|writer|evaluator|data entry|recruit|apprentice", re.I)
LOCAL_ONLY = re.compile(r"authorized to work in the (us|united states)|us citizen|green card|security clearance|"
                        r"(must|need to) (be )?(located|based|reside) in|only apply if you (currently )?live in|permanent resident|citizens? only", re.I)
LANG = re.compile(r"fluent (in )?(german|dutch|japanese|thai|vietnamese|mandarin|chinese|cantonese|arabic|french|korean)|"
                  r"(german|dutch|japanese|thai|vietnamese|mandarin|chinese|korean) (is )?(required|mandatory|native)|jlpt n[12]", re.I)

ap = argparse.ArgumentParser()
ap.add_argument("--days", type=int, default=7)
ap.add_argument("--regions", default="")
ap.add_argument("--keywords", default="")
ap.add_argument("--limit-pages", type=int, default=2)
ap.add_argument("--remote-only", action="store_true")
a = ap.parse_args()

keywords = [k.strip() for k in (a.keywords or ",".join(ME.P["target"].get("roles", []))).split(",") if k.strip()]
regions = [r.strip().upper() for r in (a.regions or f"{ME.HOME},WW").split(",") if r.strip()]
skip_companies = [s.lower() for s in ME.P["target"].get("skip_companies", [])]
skip_countries = [s.lower() for s in ME.P["target"].get("skip_countries", [])]
bad_titles_extra = [s.lower() for s in ME.P["target"].get("skip_title_words", [])]

b = Bridge()
# A static same-origin page (not the LinkedIn app, which can navigate itself mid-run and abort the
# script with "Inspected target navigated or closed"); fetches still carry the user's LinkedIn cookies.
HOST_PAGE = "https://www.linkedin.com/robots.txt"
tab = b.open(HOST_PAGE)
time.sleep(4)


def run(js, tries=3):
    """Evaluate in the LinkedIn tab, reopening it if it navigated away or was closed."""
    global tab
    for i in range(tries):
        try:
            return b.eval(tab, js)
        except RuntimeError as e:
            if i == tries - 1 or not re.search(r"navigated|closed|No target|not found", str(e), re.I):
                raise
            print(f"(LinkedIn tab was lost: {e}; reopening and retrying)")
            try:
                b.close(tab)
            except Exception:
                pass
            tab = b.open(HOST_PAGE)
            time.sleep(4)

# 1) search (guest API = no rendering needed); pause between calls or LinkedIn returns empty pages
qs = []
for kw in keywords:
    for r in regions:
        extra = "&f_WT=2" if (r == "WW" or a.remote_only) else ""
        for start in range(0, 25 * a.limit_pages, 25):
            qs.append(f"/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={kw}&geoId={GEO.get(r, GEO['WW'])}{extra}&f_TPR=r{a.days*86400}&start={start}")
js = "(async()=>{const out=[];for(const u of %s){await new Promise(z=>setTimeout(z,1800));try{out.push(await (await fetch(encodeURI(u))).text())}catch(e){out.push('')}}return out.join('\\n<!--SPLIT-->\\n')})()" % json.dumps(qs)
raw = run(js) or ""
found = {}
for li in raw.split("<li>"):
    m = re.search(r"jobPosting:(\d+)", li)
    if not m:
        continue
    g = lambda c: html.unescape(re.sub(r"<[^>]+>|\s+", " ", (re.search(r'class="[^"]*' + c + r'[^"]*"[^>]*>(.*?)</(?:h3|h4|span|time|div)>', li, re.S) or [None, ""])[1])).strip()
    found.setdefault(m.group(1), {"id": m.group(1), "title": g("base-search-card__title"), "company": g("base-search-card__subtitle"), "location": g("job-search-card__location")})
print(f"search: {len(found)} unique postings")

# 2) enrich via the logged-in API (apply method, external URL, applied flag, description)
ids = list(found)
js = """(async()=>{const csrf=(document.cookie.match(/JSESSIONID="?([^";]+)/)||[])[1];const H={headers:{'csrf-token':csrf,'accept':'application/json'}};
const ids=%s;const out={};await Promise.all(Array.from({length:4},async(_,w)=>{for(let i=w;i<ids.length;i+=4){const j=ids[i];try{
const d=await (await fetch('/voyager/api/jobs/jobPostings/'+j,H)).json();const am=d.applyMethod||{};const k=Object.keys(am)[0]||'';
out[j]={apply:k.split('.').pop(),url:am[k]?.companyApplyUrl||'',applied:!!d.applyingInfo?.applied,loc:d.formattedLocation||'',desc:(d.description?.text||'').slice(0,4000)}}catch(e){out[j]={err:String(e)}}
await new Promise(z=>setTimeout(z,300))}}));return JSON.stringify(out)})()""" % json.dumps(ids)
info = json.loads(run(js) or "{}")

# 3) filter
import csv
def norm_key(company, title):
    n = lambda x: re.sub(r"[^a-z0-9]+", " ", x.lower()).strip()
    return n(re.sub(r"\(.*?\)|-.*$", "", company)) + "|" + n(title)
TRK = os.path.join(ME.ME_DIR, "tracker.csv")
def url_key(u):
    """An apply link without tracking query/fragment, so the same posting matches however it was reached."""
    u = (u or "").strip().split("#")[0].split("?")[0].rstrip("/").lower()
    return re.sub(r"^https?://(www\.)?", "", u)
done, done_keys, done_urls = "", set(), set()
if os.path.exists(TRK):
    done = open(TRK).read()
    for r in list(csv.reader(open(TRK)))[1:]:
        if len(r) > 2:
            done_keys.add(norm_key(r[1], r[2]))
        if len(r) > 5 and r[5]:
            done_urls.add(url_key(r[5]))
CJK = re.compile(r"[\u3040-\u30ff\u4e00-\u9fff\uac00-\ud7af]")
knows_cjk = any(str(v).lower() not in ("", "none", "no") for k, v in ME.P.get("languages", {}).items() if k in ("japanese", "chinese", "korean", "mandarin"))
keep = []
for j, c in found.items():
    v = info.get(j, {})
    if v.get("err") or v.get("applied") or j in done or norm_key(c["company"], c["title"]) in done_keys:
        continue
    if v.get("url") and url_key(v["url"]) in done_urls:
        continue  # same posting already in the tracker under another company name
    if CJK.search(c["title"]) and not knows_cjk:
        continue  # posting written in Japanese/Chinese/Korean: language required
    loc = (v.get("loc") or c["location"]).lower()
    t = c["title"]
    if BAD_TITLE.search(t) or any(w in t.lower() for w in bad_titles_extra):
        continue
    if any(s in c["company"].lower() for s in skip_companies) or any(s in loc for s in skip_countries):
        continue
    d = v.get("desc", "")
    flags = []
    if LOCAL_ONLY.search(d):
        flags.append("local-only?")
    if LANG.search(d + " " + t):
        flags.append("language-required?")
    origins = [o.lower() for o in ME.P["target"].get("skip_company_origins", [])]
    if any(len(re.findall(r"\b" + re.escape(o) + r"\b", d.lower())) >= 2 for o in origins):
        flags.append("company-origin?")
    bad, good = PREFS.check(t, c["company"], loc, d)
    if bad:
        continue  # learned "no-no" (me/preferences.md explains why)
    if good:
        flags.append(f"preferred:{good[1]}")
    url = v.get("url") or f"https://www.linkedin.com/jobs/view/{j}/"
    keep.append({**c, "location": v.get("loc") or c["location"], "apply": v.get("apply"), "url": url, "flags": flags, "desc": d})

keep.sort(key=lambda k: not any(f.startswith("preferred:") for f in k["flags"]))
json.dump(keep, open(os.path.join(ME.ME_DIR, "candidates.json"), "w"), indent=1, ensure_ascii=False)
print(f"kept {len(keep)} -> me/candidates.json (review flags before applying)")
for k in keep[:200]:
    print(f"{k['id']} | {k['title'][:55]} | {k['company'][:25]} | {k['location'][:28]} | {k['apply']} | {','.join(k['flags'])}")
b.close(tab)
