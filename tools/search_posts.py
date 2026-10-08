"""Search LinkedIn *posts* (people writing "we're hiring ...") for roles that fit me/profile.json.

Usage: python3 tools/search_posts.py [--days 7|1|30] [--queries "hiring golang jakarta,..."] [--logged-in]
Default (public): finds public LinkedIn posts through Google (site:linkedin.com/posts, recent only) and reads each
post page without logging in, so your LinkedIn account is never used. LinkedIn signs out accounts that run many
automated searches, which is why this is the default. --logged-in uses LinkedIn's own post search in the connected
browser instead (more results, but risks your session; keep it to a few queries).
Output: me/post_leads.json (newest first) and a short table. Each lead has the post text, author, links,
emails and how to apply. The agent never emails or messages anyone: email/DM-only posts are leads for the user.
"""
import argparse, json, os, re, sys, time, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import me as ME
from br import Bridge
import prefs as PREFS

ap = argparse.ArgumentParser()
ap.add_argument("--days", type=int, default=7)
ap.add_argument("--queries", default="")
ap.add_argument("--scrolls", type=int, default=2)
ap.add_argument("--logged-in", action="store_true")
a = ap.parse_args()

T = ME.P.get("target", {})
roles = T.get("roles") or ["Backend Engineer"]
skills = [s for s in ("golang", "python", "django") if ME.P.get("skills_years", {}).get(s)]
places = T.get("post_search_places") or [ME.COUNTRY_NAME, ME.CITY or "", "remote"]
default_q = []
for r in roles[:3]:
    for p in [x for x in places if x][:3]:
        default_q.append(f"hiring {r} {p}")
for s in skills[:2]:
    default_q.append(f"hiring {s} {ME.COUNTRY_NAME}")
queries = [q.strip() for q in (a.queries.split(",") if a.queries else default_q) if q.strip()]
posted = {1: "past-24h", 7: "past-week", 30: "past-month"}.get(a.days, "past-week")

# Signals used to drop posts the user can't or won't apply to.
NOT_HIRING = re.compile(r"(open to work|#opentowork|looking for (a )?(new )?(job|role|opportunit)|i('m| am) (currently )?(job ?hunting|looking for)|hire (our|my) (expert|dedicated|team)|outsourc)", re.I)
SKIP_COUNTRIES = [s.lower() for s in T.get("skip_countries", [])]
INDIA = re.compile(r"\b(bangalore|bengaluru|hyderabad|pune|noida|gurgaon|gurugram|chennai|mumbai|kolkata|ahmedabad|kochi|nagpur|india|lpa|inr)\b|\.in\b|\+91", re.I)
LOCAL_SCRIPT = re.compile(r"[฀-๿぀-ヿ一-鿿가-힯]|\b(tuyển|yêu cầu|kinh nghiệm|ứng viên)\b", re.I)
FIT = re.compile(r"golang|\bgo\b|python|django|backend|back[- ]end|fullstack|full[- ]stack|software engineer", re.I)
TOO_SENIOR = re.compile(r"\b(principal|staff engineer|head of|director|vp of|engineering manager|cto)\b|\b(8|9|1\d)\+? ?(years|yrs|tahun)", re.I)
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")

EXTRACT = r"""(() => {
  const out = [];
  for (const h of document.querySelectorAll('h2')) {
    if (!/Feed post/.test(h.innerText || '')) continue;
    let box = h.parentElement;
    for (let i = 0; i < 6 && box && (box.innerText || '').length < 120; i++) box = box.parentElement;
    if (!box) continue;
    const text = (box.innerText || '').replace(/^Feed post\s*/, '').trim();
    const links = [...box.querySelectorAll('a[href]')].map(x => x.href)
      .filter(u => !/linkedin\.com\/(in|company|feed\/hashtag|search)\//.test(u) && !u.startsWith('javascript'));
    const author = [...box.querySelectorAll('a[href*="/in/"],a[href*="/company/"]')].map(x => x.href.split('?')[0])[0] || '';
    const post = [...box.querySelectorAll('a[href*="/feed/update/"],a[href*="activity"]')].map(x => x.href.split('?')[0])[0] || '';
    out.push({text: text.slice(0, 5000), links: [...new Set(links)].slice(0, 12), author, post});
  }
  return JSON.stringify(out);
})()"""

b = Bridge()
tab = b.open("about:blank")
seen, leads = set(), []


def public_posts(q):
    """Google -> recent linkedin.com/posts URLs -> each post's public text (og:description)."""
    qdr = {1: "d", 7: "w", 30: "m"}.get(a.days, "w")
    b.goto(tab, "https://www.google.com/search?hl=en&num=30&tbs=qdr:" + qdr + "&q=" + urllib.parse.quote("site:linkedin.com/posts " + q))
    time.sleep(5)
    if "sorry" in (b.eval(tab, "location.href") or ""):
        print("(Google asked for a robot check; stopping public search for now)")
        return None
    urls = json.loads(b.eval(tab, "JSON.stringify([...new Set([...document.querySelectorAll('a[href]')].map(a=>a.href.split('#')[0].split('?')[0]).filter(u=>/linkedin\\.com\\/posts\\//.test(u)))])") or "[]")
    out = []
    for u in urls[:12]:
        b.goto(tab, u)
        time.sleep(4)
        info = json.loads(b.eval(tab, """JSON.stringify({t:(document.querySelector('meta[property="og:description"]')||{}).content||'',
            a:(document.querySelector('meta[property="og:title"]')||{}).content||'',
            when:((document.body.innerText.match(/\\n(\\d+[hdw]|\\d+mo)\\s/)||[])[1])||'',
            links:[...document.querySelectorAll('.attributed-text-segment-list__content a[href], article a[href]')].map(x=>x.href).filter(h=>!/linkedin\\.com\\/(in|company|feed\\/hashtag|signup|login)/.test(h))})""") or "{}")
        if info.get("t"):
            out.append({"text": info["t"], "links": info.get("links", [])[:10], "author": info.get("a", ""), "post": u, "when": info.get("when", "")})
        time.sleep(2)
    return out


def logged_in_posts(q):
    """LinkedIn's own post search in the connected (logged-in) browser."""
    url = ("https://www.linkedin.com/search/results/content/?keywords=" + urllib.parse.quote(q)
           + f'&datePosted=%22{posted}%22&sortBy=%22date_posted%22')
    b.goto(tab, url)
    time.sleep(7)
    for _ in range(a.scrolls):
        try:
            b.eval(tab, "window.scrollBy(0, document.body.scrollHeight)")
        except Exception:
            pass
        time.sleep(2.5)
    if "/login" in (b.eval(tab, "location.href") or ""):
        print("(LinkedIn signed this browser out; use the default public mode)")
        return None
    return json.loads(b.eval(tab, EXTRACT) or "[]")


for q in queries:
    try:
        posts = logged_in_posts(q) if a.logged_in else public_posts(q)
    except Exception as e:
        print(f"(query '{q}' failed: {e})")
        continue
    if posts is None:
        break
    time.sleep(6 if not a.logged_in else 20)  # be gentle: fast repeated searches get flagged
    for p in posts:
        t = p["text"]
        key = re.sub(r"\W+", " ", t[:300]).strip().lower()
        if not t or key in seen:
            continue
        seen.add(key)
        reason = None
        if NOT_HIRING.search(t):
            reason = "job seeker post"
        elif not FIT.search(t):
            reason = "not a backend/fullstack role"
        elif LOCAL_SCRIPT.search(t):
            reason = "written in a language you don't speak"
        elif "india" in SKIP_COUNTRIES and INDIA.search(t):
            reason = "India-based"
        elif TOO_SENIOR.search(t):
            reason = "too senior"
        elif ME.employment_mismatch(t):
            reason = ME.employment_mismatch(t) + " role (you want " + "/".join(T.get("employment_types", [])) + ")"
        elif not re.search("|".join(re.escape(x) for x in ([w for w in places if w] + ["remote", "wfh", "work from home", "anywhere"])), t, re.I):
            reason = "not in your places (" + ", ".join(w for w in places if w) + ") and not remote"
        else:
            bad, _good = PREFS.check(t.split("\n")[0][:200], "", t, t)
            if bad:
                reason = f"your no-no: {bad[0]} '{bad[1]}'"
        emails = sorted(set(EMAIL.findall(t)))
        p["links"] = [u for u in p["links"] if "/uas/login" not in u and "mailto" not in u and "trk=public_post_ellipsis" not in u]
        apply_links = [u for u in p["links"] if re.search(r"jobs|careers|apply|lever|greenhouse|ashby|smartrecruiters|workable|forms\.|bit\.ly|lnkd\.in", u, re.I)]
        if emails and all(re.search(r"@(gmail|yahoo|outlook|hotmail)\.", e, re.I) for e in emails) and not apply_links:
            reason = reason or None
            p["caution"] = "recruiter uses a free email address: check the company is real before sending your CV"
        how = ("apply link" if apply_links else "email (send it yourself)" if emails else "DM / comment (yourself)")
        leads.append({"query": q, "text": t, "author": p["author"], "post": p["post"], "emails": emails,
                      "apply_links": apply_links, "how": how, "skip": reason, "caution": p.get("caution", "")})
b.close(tab)

keep = [l for l in leads if not l["skip"]]
json.dump({"queries": queries, "kept": keep, "dropped": [l for l in leads if l["skip"]]},
          open(os.path.join(ME.ME_DIR, "post_leads.json"), "w"), indent=2, ensure_ascii=False)
print(f"posts read: {len(leads)}, kept {len(keep)} -> me/post_leads.json")
drop_counts = {}
for l in leads:
    if l["skip"]:
        drop_counts[l["skip"]] = drop_counts.get(l["skip"], 0) + 1
print("dropped:", drop_counts)
for i, l in enumerate(keep, 1):
    first = re.sub(r"\s+", " ", l["text"])[:160]
    print(f"{i:2}. [{l['how']}] {first}")
    if l["apply_links"]:
        print("     link:", l["apply_links"][0])
    if l["emails"]:
        print("     email:", ", ".join(l["emails"]))
