# job-hunt

Let an AI agent find jobs and apply for you while you're busy, using only answers you gave it once.
It searches LinkedIn, prefers each company's own careers site, fills the forms in your browser,
logs everything to a Google Sheet, and stops to ask you whenever a question isn't covered.

## Quick start

**New here? Read [docs/GETTING_STARTED.md](docs/GETTING_STARTED.md)**: a step-by-step guide, including a way to set
everything up by just chatting with your AI (no terminal).

Terminal version (macOS/Linux; Windows: see the guide, it uses `install.ps1`):
```bash
git clone https://github.com/rayprastya/job-hunt.git ~/job-hunt-download && bash ~/job-hunt-download/install.sh
```

`install.sh` asks where to install the kit and where to keep your private `me/` folder, checks Python/Node/browser,
then interviews you once (identity, target roles, pay, visa, diversity answers, education, skills and years) and
saves the answers to `me/profile.json`. Re-run the interview any time with `python3 tools/onboard.py`.

Then:
1. Put your CV (PDF) in `me/cv/` and set `files.cv` in `me/profile.json`.
2. Create the tracker sheet: [docs/SHEETS.md](docs/SHEETS.md).
3. Connect your browser: [docs/BROWSER.md](docs/BROWSER.md) (separate profile or your main browser).
4. Open your AI agent in the install folder and say **"find me jobs and apply, 5 for now"**.
   Claude Code reads `CLAUDE.md`; other agents: [docs/OTHER_AI.md](docs/OTHER_AI.md).

## What's where

| Path | What |
|---|---|
| `me/` | YOUR private data (profile, rules, CV, tracker). Gitignored, never pushed. Keep it in a private repo or synced folder to use it on other devices. |
| `templates/` | Starting points for `me/` (profile, tracker, a CV HTML template). |
| `docs/GETTING_STARTED.md` | Beginner setup guide and everyday commands. |
| `docs/AGENT_PRINCIPLES.md` | How the agent behaves: outcome-first reports, asks only real decisions, never guesses, owns mistakes, session routine (adapted from firstmate). |
| `docs/WORKFLOW.md` | The step-by-step process the agent follows. |
| `docs/TROUBLESHOOTING.md` | Every roadblock hit so far and its fix. |
| `tools/` | Browser bridge (`cdpd.mjs`), form fillers, tracker + sheet sync, onboarding. |

## Ground rules baked in
- Never invents experience; years of experience come from your own skill table.
- Stops on anything personal or uncertain (health, GPA, essays a company wants hand-written, video answers).
- Never handles your passwords; you log in yourself.
- Respects your skip lists (companies, countries).
- LinkedIn limits Easy Apply per day; company career sites are preferred anyway.

## Known limits (by design or by the sites)
- Ashby, Greenhouse and Lever forms have bot checks: the agent fills everything, you click Submit.
- Workday sites need an account per company; Sea/Shopee/Garena forms need your GPA; some ask for a video.
- LinkedIn caps Easy Apply per day; company career sites are preferred anyway.
- Local-language or "must already live here" roles are filtered out or flagged.
- The agent never sends emails or messages to recruiters for you; email-only postings become leads in the sheet.

## Requirements
macOS, Windows (PowerShell installer: `install.ps1`) or Linux; Python 3.9+, Node 22+, Brave/Chrome/Edge, and an AI coding agent that can run shell commands. Run `python3 tools/selftest.py` to check everything.
