"""Interactive onboarding: asks the questions applications usually need and writes me/profile.json,
me/profile.md, me/rules.md and me/config.md. Re-run any time; existing answers are kept as defaults.

Usage: python3 tools/onboard.py [me-folder]
"""
import json, os, sys

ME = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..", "me"))
os.makedirs(ME, exist_ok=True)
PJ = os.path.join(ME, "profile.json")
data = json.load(open(PJ)) if os.path.exists(PJ) else json.load(open(os.path.join(os.path.dirname(__file__), "..", "templates", "profile.example.json")))
tty = open("/dev/tty") if os.path.exists("/dev/tty") else sys.stdin


def ask(path, question):
    node = data
    keys = path.split(".")
    for k in keys[:-1]:
        node = node.setdefault(k, {})
    cur = node.get(keys[-1], "")
    shown = json.dumps(cur, ensure_ascii=False) if isinstance(cur, (dict, list)) else str(cur)
    print(f"{question}\n  [{shown}] > ", end="", flush=True)
    a = tty.readline().strip()
    if not a:
        return
    if isinstance(cur, bool):
        node[keys[-1]] = a.lower().startswith("y")
    elif isinstance(cur, (int, float)) and a.replace(".", "", 1).isdigit():
        node[keys[-1]] = type(cur)(float(a)) if isinstance(cur, float) else int(float(a))
    elif isinstance(cur, list):
        node[keys[-1]] = [x.strip() for x in a.split(",") if x.strip()]
    else:
        node[keys[-1]] = a


QUESTIONS = [
    ("identity.first_name", "First name"), ("identity.last_name", "Last name"), ("identity.email", "Email"),
    ("identity.phone_country_code", "Phone country code (digits, e.g. 62)"), ("identity.phone_local", "Phone number without country code"),
    ("identity.city", "City you live in"),
    ("identity.city_autocomplete", "Your city as job sites autocomplete it (e.g. 'Jakarta, Jakarta Special Capital Region, Indonesia')"), ("identity.country", "Country you live in"), ("identity.nationality", "Nationality (e.g. Indonesian)"),
    ("identity.linkedin", "LinkedIn URL"), ("identity.github", "GitHub / portfolio URL"), ("identity.age", "Age (only used if a form asks)"),
    ("target.roles", "Target roles, comma separated (e.g. Backend Engineer, Fullstack Developer)"),
    ("target.seniority", "Seniority you want to be pitched as (e.g. Mid, Mid to Senior)"),
    ("target.remote", "Work setup (e.g. remote preferred; onsite only in Jakarta)"),
    ("target.home_onsite_city", "If onsite in your home country, which city only?"),
    ("target.abroad_ok", "Open to roles abroad with relocation? (y/n)"),
    ("target.abroad_junior_ok", "Abroad: OK to take a more junior title if the pay is good? (y/n)"),
    ("target.skip_companies", "Companies to never apply to, comma separated"),
    ("target.skip_countries", "Job locations (countries) to never apply to, comma separated"),
    ("preferences.avoid.title", "Job title words you never want (comma separated, e.g. blockchain, sales, intern)"),
    ("preferences.avoid.text", "Description phrases that are a no-no (comma separated, e.g. 24/7 on-call, unpaid trial)"),
    ("preferences.prefer.title", "Title words you especially want (ranked first, e.g. golang, payments)"),
    ("target.skip_company_origins", "Never apply to companies headquartered/founded in these countries, comma separated"),
    ("work.current_employer", "Current employer (as on your CV)"), ("work.notice_period", "Notice period (e.g. 1 month)"),
    ("work.notice_weeks", "Notice period in weeks"), ("work.hide_employers", "Employers to never mention, comma separated"),
    ("pay.current_monthly", "Current monthly salary (number, in your currency)"), ("pay.currency", "Your currency (e.g. IDR)"),
    ("pay.expected_monthly_home", "Expected monthly salary at home (number)"),
    ("pay.bonuses", "Current bonuses (e.g. THR 1x, year-end 1x)"),
    ("legal.authorized_countries", "Countries you can legally work in without a visa, comma separated"),
    ("legal.needs_sponsorship_elsewhere", "Need visa sponsorship everywhere else? (y/n)"),
    ("legal.willing_to_relocate", "Willing to relocate? (y/n)"), ("legal.willing_to_travel", "Willing to travel? (y/n)"),
    ("eeo.gender", "Gender for diversity questions (or 'Prefer not to say')"),
    ("eeo.veteran", "Veteran status (e.g. Not a veteran)"), ("eeo.disability", "Disability (e.g. No)"),
    ("eeo.mental_health_history", "If a form asks about mental-health medical history: answer (No / Prefer not to say / leave blank to always ask)"),
    ("education.degree", "Highest degree (e.g. B.A.Eng. in Informatics)"), ("education.school", "School"),
    ("education.gpa", "GPA (e.g. 3.40/4.00), leave blank if you don't want it used"),
    ("education.classification", "Degree classification / honours (e.g. Cum Laude, Very Satisfactory, First Class, None)"),
    ("motivation.summary", "2-3 sentences on why you're looking and what you want next (reused for 'why us?' questions, tailored per company)"),
    ("consent.policy_acknowledgements", "OK to tick standard acknowledgements (background check, no-AI-in-live-interviews, privacy notices)? (y/n)"),
    ("consent.marketing_optins", "OK to opt in to marketing / talent-community emails? (y/n)"),
    ("languages.interview_language", "Preferred interview language (e.g. English)"),
    ("languages.english", "English level (e.g. Professional working proficiency)"), ("languages.japanese", "Japanese level (None if none)"),
    ("files.cv", "Path to your CV PDF (e.g. me/cv/Jane_Doe_CV.pdf)"),
    ("files.linkedin_resume_name", "File name of that CV once uploaded to LinkedIn (linkedin.com/jobs/application-settings), so Easy Apply picks it"),
    ("rules.approval_mode", "Approval mode: auto (submit on its own) or review (stop before every submit)"),
    ("rules.min_fit_shortlist", "Minimum fit score 1-5 to shortlist a job"),
    ("rules.auto_submit_fit", "Minimum fit score 1-5 to submit without asking (auto mode)"),
]

print("Answer what you can; Enter keeps the value in [brackets].\n")
for path, q in QUESTIONS:
    ask(path, q)
print("\nYears of experience per skill are used for 'how many years of X' questions.")
print("Current values:", json.dumps(data.get("skills_years", {})))
ask("skills_years", "Paste updated skills as JSON (e.g. {\"python\": 4, \"golang\": 2}) or Enter to keep")
if isinstance(data.get("skills_years"), str):
    try:
        data["skills_years"] = json.loads(data["skills_years"])
    except Exception:
        print("Could not parse that JSON; keeping the old skills.")

json.dump(data, open(PJ, "w"), indent=2, ensure_ascii=False)
cfg = os.path.join(ME, "config.md")
if not os.path.exists(cfg):
    open(cfg, "w").write("Tracker sheet: <paste your Google Sheet link>\n")
print(f"\nSaved {PJ}. The agent reads this file; edit it any time.")
