# Tracking in Google Sheets

The Google Sheet is the source of truth. Edit it freely: change a Status, fix a note, add a job you applied to
yourself, or delete a row. `me/tracker.csv` is the agent's local working copy.

Every sync (`python3 tools/sheet_push.py`) first reads the sheet, merges it into `me/tracker.csv`, then writes the
merged list back:
- a change you made in the sheet wins;
- a change only the agent made (for example a new application) is kept;
- a row you deleted in the sheet is deleted locally too (unless the agent changed it since the last sync);
- rows you added in the sheet are added locally.

`python3 tools/sheet_push.py --pull` only reads the sheet. The agent runs it before every session so it never applies
to a job the sheet says is already done. `me/.sheet_base.csv` remembers the last sync; don't edit it.

## Setup (automatic)

The agent creates the sheet for you, in your own Google account, with the right columns:
- Say **"create my tracker sheet"**, or run `python3 tools/sheet_create.py`.
- Requirements: the browser connector is running and you're logged in to Google in that browser.
- It opens `sheets.new`, names it "Job Applications Tracker", fills the header (and any rows you already have),
  and saves the link into `me/config.md`. If a link is already there it does nothing (`--force` makes another).

No API keys or Google passwords are involved: everything happens in your logged-in browser tab.
`python3 tools/sheet_push.py` then keeps it in sync (the agent does this every ~10 applications and at the end).

### Manual alternative
Create a sheet at sheets.new, File > Import > Upload `templates/tracker.csv`, and put its link in `me/config.md`:
```
Tracker sheet: https://docs.google.com/spreadsheets/d/<id>/edit
```

## Columns

Date Added | Company | Role | Location | Remote | Job URL | Source | Fit (1-5) | CV Version | Status | Date Applied | Salary Range | Contact | Next Step | Follow-up Date | Notes

Status values: Shortlisted (waiting on you), Applied, Interview, Offer, Rejected, Withdrawn, No Response, Skipped.
Read the Notes column: it says exactly what is waiting on you and flags any answer you should double-check.
