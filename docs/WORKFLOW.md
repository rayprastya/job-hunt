# Job-hunt workflow (agent instructions)

Any agent (Claude, Codex, Gemini, ...) follows this. Facts about the person come ONLY from `me/profile.json`
(and `me/profile.md`, `me/rules.md`); never invent experience, numbers, or legal answers.

## 0. Before starting
- Read `me/profile.json`, `me/rules.md`, `me/config.md`. If they are missing or empty, run `python3 tools/onboard.py`.
- Browser bridge must be running (`docs/BROWSER.md`): `curl -s -X POST http://127.0.0.1:9339/list`.
- Ask how many applications this run (default: a small first batch of ~5 so the person can check quality).

## 1. Find jobs
- LinkedIn guest search API (fast, no rendering), from a logged-in LinkedIn tab:
  `/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=...&geoId=...&f_TPR=r604800&f_WT=2&start=0`
  Pause ~2 s between requests or LinkedIn returns empty pages.
- Enrich each job with `/voyager/api/jobs/jobPostings/<id>` (csrf-token header = JSESSIONID cookie):
  apply method, company apply URL, already-applied flag, description.
- Filter out: already applied, skip companies/countries from the profile, titles outside the target,
  local-language-required roles, "must already live in X / citizens only" roles.
- Also scan LinkedIn content search for hiring posts; log good ones as leads (never email people on the user's behalf).

## 2. Choose the route (research first)
1. Apply link or email inside the posting -> use it (emails become leads for the user).
2. Same role on the company's own careers site -> apply there.
3. Recruitment agencies and LinkedIn-only postings -> LinkedIn Easy Apply (fallback; LinkedIn caps it per day).

## 3. Apply
| Route | Tool | Submits on its own? |
|---|---|---|
| SmartRecruiters | `python3 tools/sr_apply.py <tab> <job-url> <message-file> [--visa-yes --country=SG]` | Yes |
| Zoho Recruit / Breezy / simple forms | page-specific fill (see TROUBLESHOOTING) | Yes |
| Ashby | `python3 tools/ashby_apply.py <tab> <url> <answers.json> --dry-run --country=XX` | No: prefill, user clicks Submit |
| Greenhouse | `python3 tools/gh_apply.py <tab> <answers.json>` | No: prefill (captcha) |
| LinkedIn Easy Apply | `python3 tools/easy_apply.py <tab> <job-id> <country>` | Yes |

Screening answers come from `tools/answers.py` (driven by `profile.json`). Anything it can't answer -> stop,
log the job as `Shortlisted` with `NEEDS YOU: <question>` and move on. Never stall on one job.

Answer from the profile when the user has given it during onboarding: GPA/degree classification (`education`),
"why us?" (tailor `motivation.summary` to the company, never invent facts), standard acknowledgements
(`consent.policy_acknowledgements`), marketing opt-ins (`consent.marketing_optins`, default No).

Never answer on the user's behalf: personal essays a company says must not be AI-written, health/medical
questions not in the profile, GPA if blank, video questions, anything legal that isn't in the profile.

## 4. Log and report
- After every submission: `python3 tools/log.py <company> <role> <location> <remote> <url> <source> <fit> <status> <notes>`.
- Every ~10 applications: `python3 tools/sheet_push.py <sheet-tab-id>`.
- End of run: summary of applied / waiting on the user (with the exact question) / skipped and why, plus any
  answer that may have been wrong.
