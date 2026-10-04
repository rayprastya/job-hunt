# Tracking in Google Sheets

The local file `me/tracker.csv` is the source of truth. The Google Sheet is a mirror you can open anywhere.

## Setup (2 minutes)

1. Create a new Google Sheet (sheets.new) while logged in to your Google account in the browser the agent uses.
2. File > Import > Upload `templates/tracker.csv` (or paste its header row into A1).
3. Copy the sheet link into `me/config.md`:
   ```
   Tracker sheet: https://docs.google.com/spreadsheets/d/<id>/edit
   ```

No API keys or Google credentials are needed: `tools/sheet_push.py` opens the sheet in your logged-in
browser tab and pastes the whole tracker at A1.

```bash
python3 tools/sheet_push.py <tab-id>     # tab id from: curl -s -X POST http://127.0.0.1:9339/list
```

If your agent has a Google Sheets connector (e.g. a Claude connector), it can write rows directly instead.

## Columns

Date Added | Company | Role | Location | Remote | Job URL | Source | Fit (1-5) | CV Version | Status | Date Applied | Salary Range | Contact | Next Step | Follow-up Date | Notes

Status values: Shortlisted (waiting on you), Applied, Interview, Offer, Rejected, Withdrawn, No Response, Skipped.
Read the Notes column: it says exactly what is waiting on you and flags any answer you should double-check.
