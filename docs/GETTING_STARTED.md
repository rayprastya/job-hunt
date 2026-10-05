# Getting started (step by step, no experience needed)

This guide takes you from zero to "the AI is applying to jobs for me". It takes about 20 minutes the first time.
There are two ways to do the setup: **Option A** lets your AI assistant do it for you (no terminal),
**Option B** is the terminal way. Both end in the same place.

---

## What you need

| Thing | Why | Where to get it |
|---|---|---|
| A Mac, Windows or Linux computer | The browser automation runs locally | Windows steps: see "Windows" below |
| Brave, Google Chrome or Microsoft Edge | The AI fills job forms in your browser | brave.com / google.com/chrome / (Edge is built into Windows) |
| Python 3 | Runs the helper scripts | Already on most Macs. Check: open Terminal, type `python3 --version` |
| Node.js 22 or newer | Runs the small browser connector (needs built-in WebSocket) | nodejs.org (download the LTS installer) |
| An AI agent that can run commands | Does the actual work | Claude Code (desktop app, terminal, or VS Code), or see `docs/OTHER_AI.md` |
| Your CV as a PDF | Uploaded to applications | |
| A Google account | For the tracking spreadsheet | |

---

## Option A: let the AI set everything up (no terminal)

1. Install **Claude Code** (desktop app: claude.ai/download, or the VS Code extension).
2. Open Claude Code and paste this message:

   > Clone https://github.com/rayprastya/job-hunt into my home folder, read its README and docs/GETTING_STARTED.md,
   > then set it up for me: ask me where to put it and where to keep my private data, ask me the onboarding questions
   > one by one, copy my CV from <path to your CV>, and help me create the tracking Google Sheet.

3. Answer its questions. It runs the same steps as the installer below and writes your answers to `me/profile.json`.
4. When it's done, jump to **"Connect your browser"** below. You can ask the AI to do that part too.

---

## Option B: the terminal way

### 1. Open Terminal
Mac: press `Cmd + Space`, type **Terminal**, press Enter. A window with a text prompt opens.

### 2. Download and run the installer
Copy-paste this line and press Enter:

```bash
git clone https://github.com/rayprastya/job-hunt.git ~/job-hunt-download && bash ~/job-hunt-download/install.sh
```

### 3. What `install.sh` does (and what it asks you)

The installer is a small script; you can read it first in `install.sh`. It runs five steps:

| Step | What happens | What you answer |
|---|---|---|
| 1/5 Install location | Asks where the kit should live and copies it there | A folder, or press Enter for `~/job-hunt` |
| 2/5 Tool check | Checks Python, Node and a browser are installed; warns if something is missing | Nothing (install what it warns about) |
| 3/5 Private folder | Creates your private `me/` folder (CV, answers, tracker). It is **never** uploaded to GitHub. You can put it somewhere synced (Google Drive, iCloud, a private Git repo) to use it on other computers; the installer links it in | A folder, or Enter for `<install folder>/me` |
| 4/5 Interview | Asks the questions job applications usually ask, so the AI never has to guess (list below) | Type each answer and press Enter; Enter alone skips it |
| 5/5 Next steps | Prints what's left to do | Nothing |

**The interview questions** (all saved in `me/profile.json`, editable any time):
- Identity: first/last name, email, phone (country code + number), city, country, nationality, LinkedIn, GitHub/portfolio, age.
- What you want: target roles, seniority, remote/onsite preference, the one home city you'd go onsite in, whether you're open to working abroad, whether a more junior title abroad is OK if the pay is good.
- Never apply to: specific companies, job locations, and companies from certain countries.
- Work: current employer, notice period (text and weeks), employers you never want mentioned.
- Pay: current monthly salary, currency, expected salary at home, current bonuses.
- Legal: countries you can work in without a visa, whether you need sponsorship elsewhere, willing to relocate/travel.
- Diversity questions: gender, veteran status, disability, and what to say if a form asks about mental-health history (leave blank to always be asked).
- Education: degree, school, GPA, degree classification.
- Motivation: 2-3 sentences on why you're looking (used, tailored, for "why us?" questions).
- Consent: OK to tick standard acknowledgements (background check, privacy notices)? Opt in to marketing emails?
- Languages: English level, Japanese level, preferred interview language.
- Rules: auto-submit or review-first, minimum fit score to shortlist, minimum fit score to auto-submit.
- Skills: years of experience per skill, as JSON, e.g. `{"python": 4, "golang": 2, "sql": 5}`. **Be honest**: these are used word-for-word to answer "how many years of X?" questions.

You can re-run the interview any time: `python3 tools/onboard.py` (inside the install folder).

### 4. Put your CV in place
Copy your CV PDF into `me/cv/` and set its path in `me/profile.json` (`"files": {"cv": "me/cv/YourName_CV.pdf"}`).
Tip: make a version without anything you don't want employers to see.

---

## Check your setup

Run `python3 tools/selftest.py` (Windows: `python tools\selftest.py`). It checks Python, Node, your profile, your CV,
the sheet link and the browser connector, and tells you exactly what to fix.

---

## Create the tracking sheet (both options)

1. Go to **sheets.new** (logged in to Google).
2. File > Import > Upload > choose `templates/tracker.csv` from the install folder > "Replace current sheet".
3. Copy the sheet's link and put it in `me/config.md` like this:
   ```
   Tracker sheet: https://docs.google.com/spreadsheets/d/....../edit
   ```
The AI keeps `me/tracker.csv` as the master copy and pastes it into this sheet every ~10 applications.
No Google passwords or API keys are involved: it uses your logged-in browser.

---

## Connect your browser (both options)

Full details: `docs/BROWSER.md`. Short version, pick one:

**Separate browser profile (recommended, no popups):**
1. In the install folder run `bash tools/browser-separate.sh` (or ask the AI: "open the separate job-hunt browser").
2. A new browser window opens. Log in to **LinkedIn** and **Google** in it once.
3. Start the connector: `CDP_PORT=9333 node tools/cdpd.mjs &` (or ask the AI to start it).

**Your normal browser (keeps your existing logins):**
1. Close tabs you don't need.
2. Open `brave://inspect/#remote-debugging` (Chrome: `chrome://inspect/#remote-debugging`) and switch on
   "Allow remote debugging for this browser instance".
3. Ask the AI to start the connector (`node tools/cdpd.mjs &`), then click **Allow** when the browser asks
   (click the browser window, wait 2-3 seconds, then click). Repeat after every browser restart.

---

## Everyday use

Open your AI agent **in the install folder** and talk to it normally. Useful messages:

| Say | What happens |
|---|---|
| "Find me jobs and apply, 5 for now" | Searches, picks good fits, applies, logs, then shows you what it did. Start small and check quality. |
| "Keep applying until I say stop" | Longer run. Keep the laptop plugged in and awake (`caffeinate -dims &` on Mac). |
| "Show me what's waiting on me" | Lists jobs it couldn't finish and the exact question it needs you to answer. |
| "Sync the sheet" | Pastes the tracker into your Google Sheet. |
| "Prefill the Ashby/Greenhouse ones and I'll click submit" | For sites with a bot check: everything gets filled in browser tabs, you only click Submit. |
| "Update my profile: ..." | Changes `me/profile.json` (e.g. new salary expectation). |
| "Stop applying" | It stops after the current application. |

Things it will always ask you about (by design): GPA if you left it blank, health questions, essays a company says must
not be written by AI, video answers, and any legal question your profile doesn't answer.

Read the **Notes** column in the sheet: it says what's waiting on you and flags any answer worth double-checking.

---

## Using it on another computer

1. On the new computer: install the kit again (Option A or B).
2. When the installer asks for the private folder, point it at your synced copy of `me/`
   (e.g. a private GitHub repo you cloned, or a Google Drive / iCloud folder).

## Windows

Everything works natively on Windows 10/11 with PowerShell.

### 1. Install the tools (once)
Open **PowerShell** (Start menu > type "PowerShell" > Enter) and run:
```powershell
winget install Git.Git
winget install Python.Python.3.12
winget install OpenJS.NodeJS.LTS
```
Close and reopen PowerShell afterwards so the new commands are found. (No winget? Download from git-scm.com,
python.org (tick **"Add python.exe to PATH"**) and nodejs.org.)

### 2. Run the Windows installer
```powershell
Set-ExecutionPolicy -Scope Process Bypass
iwr https://raw.githubusercontent.com/rayprastya/job-hunt/main/install.ps1 -OutFile install.ps1
.\install.ps1
```
It asks the same questions as the Mac/Linux installer (install folder, private folder, the interview).
Tip: put the private folder in OneDrive or Google Drive to use it on another PC.

### 3. Browser
Follow `docs/BROWSER.md`, Windows commands:
- Separate profile: `.\tools\browser-separate.ps1` (or `-Browser chrome` / `-Browser edge`), then
  `$env:CDP_PORT=9333; node tools\cdpd.mjs`
- Main browser: open `brave://inspect/#remote-debugging` (Chrome: `chrome://`, Edge: `edge://`), switch on
  "Allow remote debugging for this browser instance", run `node tools\cdpd.mjs`, click **Allow**.

### 4. Check and start
```powershell
python tools\selftest.py
```
Then open your AI agent (Claude desktop app or VS Code extension) in the install folder and say
"find me jobs and apply, 5 for now". On Windows the commands are `python` instead of `python3`; the agent handles that.

### Windows notes
- Keep the PC awake during long runs: Settings > System > Power > Screen and sleep > "Never" (while plugged in).
- If PowerShell refuses to run scripts, run `Set-ExecutionPolicy -Scope Process Bypass` in that window first.
- WSL also works, but then the browser must be started on Windows with the separate-profile command above.

## Something went wrong?
See `docs/TROUBLESHOOTING.md`: it lists every problem hit so far and the fix.
