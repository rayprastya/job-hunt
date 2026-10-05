# Keeping up with firstmate

`docs/AGENT_PRINCIPLES.md` adapts ideas from [firstmate](https://github.com/kunchenguid/firstmate), which is actively
maintained. We don't copy its files (they're written for a different job), so updates are reviewed, not auto-merged.

## How you hear about changes
- A GitHub Action (`.github/workflows/upstream-watch.yml`) runs every Monday and opens an issue in this repo when the
  watched firstmate files change. You can also run it any time from the repo's Actions tab ("Run workflow").
- Or check locally: `python3 tools/upstream_check.py` (add `--diff` to see the changes).

## How to review (ask your agent)
Say: **"review firstmate updates"**. The agent should:
1. Run `python3 tools/upstream_check.py --diff`.
2. For each change, decide if it improves how a job-hunt agent behaves (communication, asking for decisions,
   honesty, diagnosing problems, session routine, storing lessons). Ignore anything specific to firstmate's own
   machinery (workers, watchers, PR pipelines, harnesses).
3. Port useful ideas into `docs/AGENT_PRINCIPLES.md` (or WORKFLOW/TROUBLESHOOTING) in our own words, keeping it short.
4. Run `python3 tools/upstream_check.py --mark-reviewed`, commit `upstream.json` plus the doc changes, and close the issue.

## What's watched
See `upstream.json`: firstmate's `AGENTS.md` and the skills `ask-user-authority`, `diagnostic-reasoning`,
`captain-hold-lifecycle`, `stow`. Add paths there if we borrow more ideas later.
