# job-hunt

Let an AI agent find jobs and apply for you while you're busy, using only answers you gave it once.
It searches LinkedIn, prefers each company's own careers site, fills the forms in your browser, logs everything to a
Google Sheet, learns which jobs you don't want, and stops to ask you whenever a question isn't covered.

Works with Claude Code and other AI coding agents, on macOS, Windows and Linux.

## Quick start

**New here? Read [docs/GETTING_STARTED.md](docs/GETTING_STARTED.md)**: a step-by-step guide, including a way to set
everything up by just chatting with your AI (no terminal).

**macOS / Linux** (Terminal):
```bash
git clone https://github.com/rayprastya/job-hunt.git ~/job-hunt-download && bash ~/job-hunt-download/install.sh
```

**Windows** (PowerShell):
```powershell
Set-ExecutionPolicy -Scope Process Bypass
iwr https://raw.githubusercontent.com/rayprastya/job-hunt/main/install.ps1 -OutFile install.ps1; .\install.ps1
```

The installer asks where to install the kit and where to keep your private `me/` folder, checks Git/Python/Node/browser,
then interviews you once (identity, target roles, pay, visa, diversity answers, education, motivation, skills and
honest years, jobs you never want) and saves everything to `me/profile.json`. Re-run the interview any time:
`python3 tools/onboard.py`.

Then:
1. Put your CV (PDF) in `me/cv/` (the installer asks for its path).
2. Create the tracker sheet: [docs/SHEETS.md](docs/SHEETS.md).
3. Connect your browser: [docs/BROWSER.md](docs/BROWSER.md) (summary below).
4. Check everything: `python3 tools/selftest.py` (Windows: `python tools\selftest.py`).
5. Open your AI agent in the install folder and say **"find me jobs and apply, 5 for now"**.
   Claude Code reads `CLAUDE.md`; other agents: [docs/OTHER_AI.md](docs/OTHER_AI.md).

## Browser setup in 30 seconds
The agent fills forms in Brave, Chrome or Edge. Pick one (full steps with pictures: [docs/BROWSER.md](docs/BROWSER.md)):
- **Separate window (easiest):** run `bash tools/browser-separate.sh` (Windows: `.\tools\browser-separate.ps1`),
  log in to LinkedIn + Google in the window that opens, then `CDP_PORT=9333 node tools/cdpd.mjs &`.
- **Your normal browser:** type `brave://inspect/#remote-debugging` (or `chrome://` / `edge://`) in the address bar,
  tick **"Allow remote debugging for this browser instance"**, run `node tools/cdpd.mjs &`, then click **Allow**
  in the popup. Redo after every browser restart.

## Everyday use (just talk to the agent)

| Say | What happens |
|---|---|
| "Find me jobs and apply, 5 for now" | Searches, picks good fits, applies, logs, then reports. Start small and check quality. |
| "Keep applying until I say stop" | Longer run (keep the computer plugged in and awake). |
| "Show me what's waiting on me" | Jobs it couldn't finish, with the exact question it needs you to answer. |
| "No more crypto roles" / "skip that company" | Saved as a rule; future searches skip it (see *Learns your no-nos*). |
| "Prefill the bot-check ones, I'll click submit" | Ashby/Greenhouse/Lever forms filled in browser tabs; you only click Submit. |
| "Sync the sheet" | Pastes the tracker into your Google Sheet. |
| "Update the kit" | Pulls the latest fixes (also happens automatically, see below). |
| "Stop applying" | Stops after the current application and summarises. |

## What makes it reliable
- **Never guesses.** Answers only from your profile; years of experience come from your own skill table; tailoring a
  CV means choosing true facts, never adding new ones. Health, blank GPA, "no-AI" essays and video answers always come back to you.
- **Asks only real decisions,** in one batched message with a recommendation, and saves your answer so it never asks twice.
- **Owns its mistakes:** a wrong answer gets flagged in the tracker, the rule gets fixed, and the lesson is written down.
  Behaviour guide: [docs/AGENT_PRINCIPLES.md](docs/AGENT_PRINCIPLES.md) (adapted from
  [firstmate](https://github.com/kunchenguid/firstmate)).
- **Learns your no-nos.** Every "I don't want this kind of job" becomes a rule (company, title words, description
  phrases, location, company origin) used by every search; likes get ranked first. History with reasons in
  `me/preferences.md`. Manage manually with `python3 tools/prefs.py list|avoid|prefer|remove`.
- **Keeps itself updated.** At session start it updates a stale kit (`tools/update.py`: fast-forward only, never
  touches `me/`); tools started through `tools/run.py` update and retry once when they stall.
- **Never stalls on one job:** stuck jobs are logged with the reason and it moves on.
- **Keeps your data private:** `me/` is never pushed; `me/.gitignore` blocks secrets (keys, tokens, cookies, `.env`)
  even in a private repo; a pre-commit guard refuses commits containing `me/` files or your email/phone/name.
  You log in yourself; the kit never stores passwords.

## What's where

| Path | What |
|---|---|
| `me/` | YOUR private data: `profile.json`, `rules.md`, `preferences.md`, `learnings.md`, CV, `tracker.csv`. Never pushed. Sync it via a private repo or cloud folder to use other devices. |
| `templates/` | Starting points for `me/` (profile, tracker, preferences, learnings, CV HTML template). |
| `docs/GETTING_STARTED.md` | Beginner setup (no-terminal option, macOS, Windows) and everyday commands. |
| `docs/BROWSER.md` | Browser "developer mode" step by step, both modes, Brave/Chrome/Edge. |
| `docs/SHEETS.md` | Google Sheet tracking (no API keys needed). |
| `docs/AGENT_PRINCIPLES.md` | How the agent behaves and its session routine. |
| `docs/WORKFLOW.md` | The step-by-step process and which tool to use for each site type. |
| `docs/TROUBLESHOOTING.md` | Every roadblock hit so far and its fix. |
| `docs/OTHER_AI.md` | Using Codex, Gemini, Cursor or chat-only AIs. |
| `docs/UPSTREAM.md` | How firstmate improvements are tracked (weekly GitHub issue + "review firstmate updates"). |
| `tools/` | See below. |

**Tools:** `selftest.py` (check + auto-update), `update.py`, `run.py` (stall retry), `search_jobs.py`, `prefs.py`,
`easy_apply.py`, `sr_apply.py` (SmartRecruiters), `ashby_apply.py`, `gh_apply.py` (Greenhouse), `answers.py`,
`log.py`, `sheet_push.py`, `cv_pdf.py`, `br.py` (browser CLI), `cdpd.mjs` (browser connector), `onboard.py`,
`guard_commit.py`, `upstream_check.py`, `browser-separate.sh/.ps1`.

## Known limits (by design or by the sites)
- Ashby, Greenhouse and Lever forms have bot checks: the agent fills everything, you click Submit.
- Workday sites need an account per company; Sea/Shopee/Garena forms need your GPA; some ask for a video.
- LinkedIn caps Easy Apply per day; company career sites are preferred anyway.
- Local-language or "must already live here" roles are filtered out or flagged.
- The agent never sends emails or messages to recruiters for you; email-only postings become leads in the sheet.

## Requirements
macOS, Windows or Linux; Python 3.9+, Node 22+, Git, Brave/Chrome/Edge, and an AI coding agent that can run shell
commands. `python3 tools/selftest.py` checks all of it and tells you what to fix.

## License
GPL-3.0 (see `LICENSE`).
