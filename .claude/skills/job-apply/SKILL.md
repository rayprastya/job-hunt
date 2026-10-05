---
name: job-apply
description: Find jobs, apply on company sites first (LinkedIn Easy Apply as fallback), log to the tracker and Google Sheet. Use for any job search, application, CV tailoring, or tracker request.
---

# Job-hunt workflow (agent instructions)

Any agent (Claude, Codex, Gemini, ...) follows this. Facts about the person come ONLY from `me/profile.json`
(and `me/profile.md`, `me/rules.md`); never invent experience, numbers, or legal answers.

## 0. Before starting
- Run `python3 tools/selftest.py` first: it auto-updates the kit if it hasn't checked in 12 hours
  (`tools/update.py`: fast-forward only, never touches `me/`, refuses if you edited kit files).
- Run apply tools through `python3 tools/run.py <tool.py> ...`: if a tool stalls or crashes it updates the kit and,
  only when new fixes arrived, retries once. If it still stalls, log the job and move on.
- Read `me/profile.json`, `me/rules.md`, `me/config.md`. If they are missing or empty, run `python3 tools/onboard.py`.
- Browser bridge must be running (`docs/BROWSER.md`): `curl -s -X POST http://127.0.0.1:9339/list`
  (another port: set `BRIDGE_PORT` for `cdpd.mjs` and `BRIDGE_URL=http://127.0.0.1:<port>` for the tools).
- **The Google Sheet is the source of truth.** Run `python3 tools/sheet_push.py --pull` before searching or applying:
  it merges the sheet into `me/tracker.csv` (edits, added and deleted rows in the sheet win), so a job the user marked
  Applied, Rejected or Skipped in the sheet is never applied to again.
- Run `python3 tools/tabs.py sweep --close`: tabs where the user already clicked Submit get marked Applied and closed.
- Ask how many applications this run (default: a small first batch of ~5 so the person can check quality).

## Tools at a glance
| Need | Command |
|---|---|
| Check setup (auto-updates the kit) | `python3 tools/selftest.py` |
| Update the kit now | `python3 tools/update.py` |
| Run a tool with auto-update on stall | `python3 tools/run.py easy_apply.py <tab> <job-id> <country>` |
| Search + filter jobs | `python3 tools/search_jobs.py --regions ID,SG,WW --days 7` -> `me/candidates.json` |
| Drive the browser manually | `python3 tools/br.py list|open|goto|eval|click|type|key|upload|shot|close` |
| Tailored CV to PDF | copy `templates/cv-example.html`, edit, then `python3 tools/cv_pdf.py me/cv/x.html me/cv/Name_CV.pdf` |
| Save a no-no / preference | `python3 tools/prefs.py avoid title "blockchain" --reason "..."` |
| Log / sync | `python3 tools/log.py ...`, `python3 tools/sheet_push.py` |
(On Windows use `python` instead of `python3`.)

## 1. Find jobs
- Fast path: `python3 tools/search_jobs.py` (uses target roles, regions and skip lists from the profile).
- LinkedIn guest search API (fast, no rendering), from a logged-in LinkedIn tab:
  `/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=...&geoId=...&f_TPR=r604800&f_WT=2&start=0`
  Pause ~2 s between requests or LinkedIn returns empty pages.
- Enrich each job with `/voyager/api/jobs/jobPostings/<id>` (csrf-token header = JSESSIONID cookie):
  apply method, company apply URL, already-applied flag, description.
- Filter out: already applied, learned no-nos (`preferences.avoid`, see `me/preferences.md`), skip companies/countries from the profile, titles outside the target,
  local-language-required roles, "must already live in X / citizens only" roles.
- Also scan LinkedIn content search for hiring posts; log good ones as leads (never email people on the user's behalf).

## 2. Choose the route (research first)
1. Apply link or email inside the posting -> use it (emails become leads for the user).
2. Same role on the company's own careers site -> apply there.
3. Recruitment agencies and LinkedIn-only postings -> LinkedIn Easy Apply (fallback; LinkedIn caps it per day).

## 3. Apply

**Background first.** Run applications in the headless (invisible) browser so the user's screen and tabs stay free:
start it with `bash tools/browser-separate.sh --headless` and its connector with
`BRIDGE_PORT=9341 CDP_PORT=9333 node tools/cdpd.mjs &`, then prefix apply tools with `BRIDGE_URL=http://127.0.0.1:9341`.
Use it for every site that needs no login and no human click (SmartRecruiters, Sea Group, Zoho, Breezy).
Use the user's normal browser (port 9339) only for: LinkedIn search and Easy Apply and the Google Sheet, unless the
headless profile has been logged in once (`bash tools/browser-separate.sh`, log in, close); and bot-check forms
(Ashby/Greenhouse/Lever) that the user must Submit by hand.

| Route | Tool | Submits on its own? |
|---|---|---|
| SmartRecruiters | `python3 tools/sr_apply.py <tab> <job-url> <message-file> [--visa-yes --country=SG]` | Yes |
| Sea Group (Sea, Shopee, Monee, Garena) | `python3 tools/sea_apply.py <tab> <posting-url> [--dry-run]` (needs `education.gpa`) | Yes |
| Zoho Recruit / Breezy / simple forms | page-specific fill (see TROUBLESHOOTING) | Yes |
| Ashby | `python3 tools/ashby_apply.py <tab> <url> <answers.json> --dry-run --country=XX` | No: prefill, user clicks Submit |
| Greenhouse | `python3 tools/gh_apply.py <tab> <answers.json>` | No: prefill (captcha) |
| LinkedIn Easy Apply | `python3 tools/easy_apply.py <tab> <job-id> <country>` | Yes |

Screening answers come from `tools/answers.py` (driven by `profile.json`). Anything it can't answer -> stop,
log the job as `Shortlisted` with `NEEDS YOU: <question>` and move on. Never stall on one job.

Answer from the profile when the user has given it during onboarding: GPA/degree classification (`education`),
"why us?" (tailor `motivation.summary` to the company, never invent facts), standard acknowledgements
(`consent.policy_acknowledgements`), marketing opt-ins (`consent.marketing_optins`, default No).

Cover letters: follow `cover_letter.mode`. `auto` = write one whenever the form has a cover letter field;
`required` = only when the field is required; `ask` or blank = the first time a form offers one, ask the user once
with options (write them automatically / only when required / never / ask each time) and save the choice to
`cover_letter.mode`. If there's no reference letter or style yet, offer a default (short, 3 paragraphs, specific to
the company, no cliches) or ask for an example.

Pay for a country with no saved number (`pay.abroad_monthly`): if `pay.when_missing` is `research`, look up the
market rate (Glassdoor, Levels.fyi, Nodeflair, Payscale, the posting itself) and use a fair mid-to-upper figure; if it
is `ask` or blank, ask the user with options: (a) they give a number, (b) the agent researches the market rate and
uses it, (c) skip pay questions for that country. Save the answer to `pay.abroad_monthly` so it's asked only once.

"Message to the hiring team" (SmartRecruiters and others): follow `cover_letter.hiring_message_notes`, or the cover
letter style when blank. Default tone: soft, not a hard sell; 80-130 words; who they are now, 2-3 concrete facts with
numbers from the current job first, one line on why this team, a warm close. Only true facts from the CV/profile.
If the profile has too few concrete facts, ask the user for 2-3 achievements once and save them.

Cover letters and "why us?" texts: read `cover_letter.reference_file` (a letter the user likes) and
`cover_letter.style_notes`, mirror that tone and structure, use only true facts from the CV/profile, and tailor to the
company. Save each one in `me/cover_letters/<company>.md` so the user can see what was sent.

Never answer on the user's behalf: personal essays a company says must not be AI-written, health/medical
questions not in the profile, GPA if blank, video questions, anything legal that isn't in the profile.

## 4. Log and report
- After a confirmed submission the apply tools close their tab themselves (`KEEP_TABS=1` keeps it). Close any other
  tab you opened for a job once it's logged; never close tabs the user opened.
- After every submission: `python3 tools/log.py <company> <role> <location> <remote> <url> <source> <fit> <status> <notes>`.
- Every ~10 applications and at the end: `python3 tools/sheet_push.py <sheet-tab-id>` (pulls the sheet first, merges,
  then writes the merged list back, so edits the user made in the sheet meanwhile are kept).
- End of run: summary of applied / waiting on the user (with the exact question) / skipped and why, plus any
  answer that may have been wrong.
