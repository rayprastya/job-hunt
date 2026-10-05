# Using a different AI agent (not Claude Code)

The kit is plain files plus Python/Node scripts, so any coding agent that can read files and run shell commands works.

| Agent | What it reads | Setup |
|---|---|---|
| Claude Code | `CLAUDE.md` -> `.claude/skills/job-apply/SKILL.md` | Nothing extra. |
| OpenAI Codex CLI | `AGENTS.md` | Nothing extra; `AGENTS.md` points to the same workflow. |
| Gemini CLI | `GEMINI.md` or `AGENTS.md` | `ln -s AGENTS.md GEMINI.md` |
| Cursor / Windsurf / others | Project rules | Add a rule: "Follow AGENTS.md for any job search or application request." |
| ChatGPT / claude.ai (no shell) | Uploaded files (include `docs/AGENT_PRINCIPLES.md`) | Upload `docs/WORKFLOW.md`, `me/profile.json`, your CV. It can tailor CVs and draft answers, but can't drive the browser; you submit. |

What every agent needs to be able to do:
1. Run shell commands (python3, node, curl).
2. Keep `node tools/cdpd.mjs` running in the background (or you start it in another terminal).
3. Ask you before anything it can't answer from `me/profile.json`.

Things that are Claude Code specific and how to replace them:
- Claude's web search for salary research -> any web search tool, or answer from `profile.json` `pay.abroad_monthly`.
- Claude's Google Drive/Sheets connector -> `tools/sheet_push.py` (browser-based, no credentials).
- Claude Code permission prompts -> your agent's own approval setting; keep a human approval for submitting applications if your agent supports it.
