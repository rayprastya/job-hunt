# Tracking in Google Sheets

The local file `me/tracker.csv` is the source of truth. The Google Sheet is a mirror you can open anywhere.

## Setup (automatic)

The agent creates the sheet for you, in your own Google account, with the right columns:
- Say **"create my tracker sheet"**, or run `python3 tools/sheet_create.py`.
- Requirements: the browser connector is running and you're logged in to Google in that browser.
- It opens `sheets.new`, names it "Job Applications Tracker", fills the header (and any rows you already have),
  and saves the link into `me/config.md`. If a link is already there it does nothing (`--force` makes another).

No API keys or Google passwords are involved: everything happens in your logged-in browser tab.
`python3 tools/sheet_push.py` then keeps it in sync (the agent does this every ~10 applications).

### Manual alternative
Create a sheet at sheets.new, File > Import > Upload `templates/tracker.csv`, and put its link in `me/config.md`:
```
Tracker sheet: https://docs.google.com/spreadsheets/d/<id>/edit
```

## Columns

Date Added | Company | Role | Location | Remote | Job URL | Source | Fit (1-5) | CV Version | Status | Date Applied | Salary Range | Contact | Next Step | Follow-up Date | Notes

Status values: Shortlisted (waiting on you), Applied, Interview, Offer, Rejected, Withdrawn, No Response, Skipped.
Read the Notes column: it says exactly what is waiting on you and flags any answer you should double-check.
