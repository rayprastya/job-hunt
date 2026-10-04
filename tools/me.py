"""Loads the private profile (me/profile.json) for all tools. Nothing personal is hardcoded in tools/."""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ME_DIR = os.path.join(ROOT, "me")
P = json.load(open(os.path.join(ME_DIR, "profile.json")))
I, PAY, LEGAL, EEO, WORK = P["identity"], P["pay"], P["legal"], P["eeo"], P["work"]

FIRST, LAST = I["first_name"], I["last_name"]
FULL_NAME = f"{FIRST} {LAST}".strip()
EMAIL = I["email"]
PHONE_LOCAL = I["phone_local"]
PHONE_CC = str(I.get("phone_country_code", ""))
PHONE_INTL = f"+{PHONE_CC}{PHONE_LOCAL}"
LINKEDIN, GITHUB = I.get("linkedin", ""), I.get("github", "") or I.get("linkedin", "")
CITY, COUNTRY_NAME, NATIONALITY = I.get("city", ""), I.get("country", ""), I.get("nationality", "")
CITY_FULL = f"{CITY}, {COUNTRY_NAME}".strip(", ")
CITY_AUTOCOMPLETE = I.get("city_autocomplete") or CITY_FULL
AGE = str(I.get("age", "") or "")
HOME = LEGAL.get("home_country_code", "ID")
NOTICE = WORK.get("notice_period", "1 month")
NOTICE_WEEKS = str(WORK.get("notice_weeks", 4))
CURRENT_MONTHLY = int(PAY.get("current_monthly") or 0)
HOME_CUR = PAY.get("currency", "")
BONUSES = PAY.get("bonuses", "")
GENDER = EEO.get("gender", "")
MENTAL_HEALTH = EEO.get("mental_health_history", "")
SKILL_YEARS = dict(P.get("skills_years", {}))
SALARY = {HOME: (HOME_CUR, int(PAY.get("expected_monthly_home") or 0))}
SALARY.update({k: (v[0], int(v[1])) for k, v in PAY.get("abroad_monthly", {}).items()})
SALARY = {k: (c, a, str(a)) for k, (c, a) in SALARY.items()}
# rough conversions of current pay for forms that demand another currency (update rates as needed)
FX_PER_UNIT = PAY.get("fx_per_unit", {"MYR": 3700, "SGD": 11800, "USD": 16300})


def cv_path():
    f = P["files"]["cv"]
    return f if os.path.isabs(f) else os.path.join(ROOT, f)


def current_in(cur):
    rate = FX_PER_UNIT.get(cur.upper())
    return str(round(CURRENT_MONTHLY / rate / 100) * 100) if rate and HOME_CUR == "IDR" else None
