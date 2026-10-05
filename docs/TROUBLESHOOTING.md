# Troubleshooting: roadblocks we hit and how they're solved

Every item here happened in a real run. The tools already include the fix; this file explains it so you (or your agent) can recognise it quickly.

**First thing to try when anything stalls:** update the kit, then retry once.
```bash
git fetch && git pull --ff-only     # in the kit folder; me/ is never touched
```
Job sites change their forms often and fixes are pushed here. `python3 tools/selftest.py` also tells you when your copy is behind.

## Browser connection

| Symptom | Cause | Fix |
|---|---|---|
| All your tabs reload and the Mac lags when the agent connects | Attaching a generic automation tool to your main browser wakes every sleeping tab | Use `tools/cdpd.mjs` (it only attaches to tabs it opens) or a separate profile (`docs/BROWSER.md`). Close extra tabs first if you use your main browser. |
| "Allow remote debugging?" prompt keeps appearing, or its button can't be clicked | Chromium asks once per new connection; the button is disabled for a moment for security | Click the browser window first, wait 2-3 s, or Tab to the button and press Enter. `cdpd.mjs` keeps ONE connection open so you only approve once per browser session. |
| Connection works but new tabs stay blank ("Untitled") | A stale connection from an earlier attempt | Restart the browser, re-enable `brave://inspect/#remote-debugging`, restart `node tools/cdpd.mjs`. |
| `chrome-devtools-axi`/MCP tools: "pageId expected number" | That tool doesn't support the main-browser (toggle) connection mode | Use `tools/cdpd.mjs` instead. |
| Pages in background tabs don't load or clicks land at (0,0) | Background tabs aren't rendered | Tools call `/activate` to bring their tab to the front before acting. Don't use the browser while a batch runs, or use a separate profile/window. |
| Copying login cookies from your main profile is blocked by the agent's safety check | Moving session credentials is treated as sensitive | Log in once in the separate profile (Sign in with Google makes it quick), or use the main browser. |

## LinkedIn Easy Apply

| Symptom | Cause | Fix |
|---|---|---|
| Modal can't be found by normal JS | The Easy Apply modal lives in a closed shadow root | `tools/ax.py` reads the accessibility tree and acts by node id. |
| "Easy Apply" is a link, mouse click does nothing | New LinkedIn UI | `easy_apply.py` clicks the opener via script (`this.click()`). |
| Radio options read as "on" | Option text sits in a sibling element, not the `<label>` | Option text is read from the nearest ancestor with text. |
| Typing went into a "Simplify"/other extension panel | Extensions inject their own forms | Actions are scoped to LinkedIn's "Apply to ..." dialog only. |
| City field doesn't stick | It's a typeahead that needs a suggestion picked | After typing, the matching suggestion is clicked. |
| "Please enter a valid phone number" | Phone country code defaulted to the job's country | Phone country code is forced to your own (`profile.json`). |
| "You reached today's Easy Apply limit" | LinkedIn caps Easy Apply per day | Stop Easy Apply for the day; apply on company sites (`docs/WORKFLOW.md`). |
| The routine picked an old LinkedIn-stored CV | LinkedIn remembers previous uploads | Upload your current CV once at linkedin.com/jobs/application-settings and set `files.linkedin_resume_name`. |
| Validation error detector fired on a question containing "please enter" | Question text matched the error regex | Only short texts (< 70 chars) count as errors. |

## Wrong answers we caught (and the rule fixes)

Always review `Notes` in the tracker; these were real mistakes, now fixed:

- "Years of NoSQL" answered with SQL years -> skill keys match on word boundaries and specific skills (nosql, sql server, postgresql) win over generic ones.
- "Mobile app scraping / reverse engineering" answered with generic engineering years -> generic words (engineering, software, web) are only a fallback and never for mobile/reverse/ML/devops questions.
- "Microsoft SQL Server" answered with general SQL years -> explicit `sql server` key.
- "Annual salary" answered with the monthly number -> annual questions get monthly x 12.
- "X, Y, or Z experience" answered 0 because one item was 0 -> lists joined by "or"/commas use the max; "X and Y" uses the min.
- Ashby label "advantage" matched the key "age" -> label keys match whole words only.
- Resume uploaded into a photo field -> pick the file input whose `accept` includes `.pdf`.

## Company application systems

| System | Status | Notes |
|---|---|---|
| SmartRecruiters (`jobs.smartrecruiters.com`) | Automatic | `sr_apply.py`; Singapore asks citizenship status (Foreigner - EP when you need sponsorship); some forms have a separate consent page. |
| Breezy (`*.breezy.hr`, e.g. Kredivo) | Automatic | Resume parsing can mis-fill work history; check entries. Use a real mouse click for Submit. |
| Zoho Recruit (e.g. HFM) | Automatic | Dismiss the cookie banner first; "Annual Salary Expectation" + currency dropdown + policy checkbox. |
| Ashby (`jobs.ashbyhq.com`) | Prefill only | Invisible bot check blocks automated Submit. `ashby_apply.py --dry-run` fills everything; you click Submit. |
| Greenhouse (`job-boards.greenhouse.io`) | Prefill only | reCAPTCHA; selects are react-select (open the control, type, click option); address "Country" is a separate select from phone country. |
| Lever (`jobs.lever.co`) | Prefill only | hCaptcha. |
| Sea / Shopee / Garena careers | Needs GPA | Form requires CGPA and degree classification. |
| Workday | Manual | Needs an account per company. |
| Dealls quick apply | Manual | Button doesn't open from automation; use the Dealls app. |
| Tether / video questions | Manual | Some forms require a recorded video. |

## Google Sheet sync

| Symptom | Cause | Fix |
|---|---|---|
| Typed text didn't land in cells | Sheets ignores inserted text when no cell is in edit mode | `sheet_push.py` pastes a TSV block with a synthetic paste event at A1 instead. |
| Paste overwrote the header | Selection was A1 after load | The tracker CSV (header included) is pasted whole at A1, so the sheet is always a full mirror. |
| Old rows stayed at the bottom after the tracker shrank | A paste only overwrites the cells it covers | `sheet_push.py` pastes 60 blank rows after the data to clear leftovers. |

## Agent harness (Claude Code)

| Symptom | Fix |
|---|---|
| Auto-mode classifier blocks "real-world transactions" (submitting applications) | Approve when asked, or add a permission rule for `python3 tools/*.py` in your Claude Code settings if you want unattended runs. |
| Long batches time out the shell tool | Run batches in the background and check the log file. |
| A `while read` loop stops after one item | The inner command read the loop's stdin; feed the loop on another file descriptor (`read -u 9 ... 9< file`) or add `< /dev/null`. |
