# job-hunt

Let an AI agent find jobs and apply for you while you're busy, using only answers you gave it once.
It searches LinkedIn, prefers each company's own careers site, fills the forms in your browser,
logs everything to a Google Sheet, and stops to ask you whenever a question isn't covered.

## Quick start

```bash
git clone https://github.com/rayprastya/job-hunt.git && cd job-hunt
bash install.sh          # asks where to install, then a short interview -> me/profile.json
```

Then:
1. Put your CV (PDF) in `me/cv/` and set `files.cv` in `me/profile.json`.
2. Create the tracker sheet: [docs/SHEETS.md](docs/SHEETS.md).
3. Connect your browser: [docs/BROWSER.md](docs/BROWSER.md) (separate profile or your main browser).
4. Open your agent in this folder and say **"find me jobs and apply"**.
   Claude Code reads `CLAUDE.md`; other agents: [docs/OTHER_AI.md](docs/OTHER_AI.md).

## What's where

| Path | What |
|---|---|
| `me/` | YOUR private data (profile, rules, CV, tracker). Gitignored, never pushed. Keep it in a private repo or synced folder to use it on other devices. |
| `templates/` | Starting points for `me/`. |
| `docs/WORKFLOW.md` | The step-by-step process the agent follows. |
| `docs/TROUBLESHOOTING.md` | Every roadblock hit so far and its fix. |
| `tools/` | Browser bridge (`cdpd.mjs`), form fillers, tracker + sheet sync, onboarding. |

## Ground rules baked in
- Never invents experience; years of experience come from your own skill table.
- Stops on anything personal or uncertain (health, GPA, essays a company wants hand-written, video answers).
- Never handles your passwords; you log in yourself.
- Respects your skip lists (companies, countries).
- LinkedIn limits Easy Apply per day; company career sites are preferred anyway.

## Requirements
macOS or Linux, Python 3, Node 20+, Brave or Chrome, and an AI coding agent that can run shell commands.
