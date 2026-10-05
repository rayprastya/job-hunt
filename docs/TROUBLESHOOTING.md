# Troubleshooting: roadblocks we hit and how they're solved

Every item here happened in a real run. The tools already include the fix; this file explains it so you (or your agent) can recognise it quickly.

**First thing to try when anything stalls:** update the kit, then retry once.
```bash
python3 tools/update.py      # safe: fast-forward only, never touches me/
```
Job sites change their forms often and fixes are pushed here. This also happens automatically: `selftest.py` updates a
stale kit at session start, and tools started through `tools/run.py` update and retry once when they stall.

## Browser connection

| Symptom | Cause | Fix |
|---|---|---|
| All your tabs reload and the Mac lags when the agent connects | Attaching a generic automation tool to your main browser wakes every sleeping tab | Use `tools/cdpd.mjs` (it only attaches to tabs it opens) or a separate profile (`docs/BROWSER.md`). Close extra tabs first if you use your main browser. |
| "Allow remote debugging?" prompt keeps appearing, or its button can't be clicked | Chromium asks once per new connection; the button is disabled for a moment for security | Click the browser window first, wait 2-3 s, or Tab to the button and press Enter. `cdpd.mjs` keeps ONE connection open so you only approve once per browser session. |
| Connection works but new tabs stay blank ("Untitled") | A stale connection from an earlier attempt | Restart the browser, re-enable `brave://inspect/#remote-debugging`, restart `node tools/cdpd.mjs`. |
| `chrome-devtools-axi`/MCP tools: "pageId expected number" | That tool doesn't support the main-browser (toggle) connection mode | Use `tools/cdpd.mjs` instead. |
| Pages in background tabs don't load or clicks land at (0,0) | Background tabs aren't rendered | Tools call `/activate` to bring their tab to the front before acting. Don't use the browser while a batch runs, or use a separate profile/window. |
| `cdpd.mjs` exits with `EADDRINUSE` | Another program (or a second connector) already uses port 9339 | Run it on another port: `BRIDGE_PORT=9341 node tools/cdpd.mjs &`, then prefix tools with `BRIDGE_URL=http://127.0.0.1:9341`. Lets the main-browser and separate-profile connectors run side by side. |
| Finished application tabs pile up | Forms you submitted by hand stay open | `python3 tools/tabs.py sweep --close` marks them Applied and closes them; apply tools close their own tab after a confirmed submit. |
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
- "Salary (in Million IDR)" / "(in thousands)" and "notice period (in Months)" -> answers are scaled to the unit the form asks for.
- The same job applied on a company site reappeared in search under its LinkedIn id -> search also de-duplicates by company + title.
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
| Greenhouse (`job-boards.greenhouse.io`) | Prefill only | reCAPTCHA. Dropdowns: open the control (a second click may be needed when another menu was open), click the option; typing the full option text can filter everything out, so type only a short prefix. The phone "Country" flyout isn't automated yet: `gh_apply.py` prints a CHECK line and you pick it in one click before Submit. |
| Lever (`jobs.lever.co`) | Prefill only | hCaptcha. |
| Sea / Shopee / Monee / Garena careers | `tools/sea_apply.py`, headless OK | Needs `education.gpa`. Dropdowns open only on a real mouse click (keyboard shows "No data"); options render in a class-less `<div>` at the end of `<body>`. "Current Location" is a country list. Degree classification uses UK/US honours, so other systems pick "Others / Not Applicable". Old `careers.monee.com/job-detail?id=` links show an empty page when the posting closed. |
| BrioHR (`boards.briohr.com`) | Prefill only | Visible "I'm not a robot" checkbox: you tick it and Submit. Custom questions are textareas whose label lookup can grab the section title; match by field id or the label right above the box. |
| Workday | Manual | Needs an account per company. |
| Dealls quick apply | Manual | Button doesn't open from automation; use the Dealls app. |
| Tether / video questions | Manual | Some forms require a recorded video. |

## Dropdowns in general
Do what a person does: open the dropdown, **type a short prefix** to filter (typing the full text sometimes filters
everything out), and if the option still isn't visible, **clear the filter and scroll the list** until it appears,
then click it. Native `<select>` elements can be set directly by option text. `gh_apply.py` implements this
type-then-scroll fallback; reuse the same pattern for any new site.

## Google Sheet sync

| Symptom | Cause | Fix |
|---|---|---|
| Typed text didn't land in cells | Sheets ignores inserted text when no cell is in edit mode | `sheet_push.py` pastes a TSV block with a synthetic paste event at A1 instead. |
| Paste overwrote the header | Selection was A1 after load | The tracker CSV (header included) is pasted whole at A1, so the sheet is always a full mirror. |
| A status you changed in the sheet was overwritten | Older kits pushed the local file over the sheet | `sheet_push.py` now reads the sheet first and merges (sheet edits win). Update the kit. |
| "could not read the sheet" | Not logged in to Google in the connected browser, or the link in `me/config.md` points at another tab | Log in in that browser; check the `gid=` in the saved link matches the tracker tab. |
| Old rows stayed at the bottom after the tracker shrank | A paste only overwrites the cells it covers | `sheet_push.py` pastes 60 blank rows after the data to clear leftovers. |

## Agent harness (Claude Code)

| Symptom | Fix |
|---|---|
| Auto-mode classifier blocks "real-world transactions" (submitting applications) | Approve when asked, or add a permission rule for `python3 tools/*.py` in your Claude Code settings if you want unattended runs. |
| Long batches time out the shell tool | Run batches in the background and check the log file. |
| Auto-update refuses with "local edits to kit files" | You changed tracked kit files | `git stash` (or commit them), then `python3 tools/update.py`. Extra scratch files don't block updates. |
| A `while read` loop stops after one item | The inner command read the loop's stdin; feed the loop on another file descriptor (`read -u 9 ... 9< file`) or add `< /dev/null`. |
