"""Append one row to me/tracker.csv. Usage: log.py company role location remote url source fit status notes"""
import csv, os, sys, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import me as ME
c, role, loc, remote, url, src, fit, status, notes = sys.argv[1:10]
d = datetime.date.today().isoformat()
fu = (datetime.date.today() + datetime.timedelta(days=7)).isoformat() if status == "Applied" else ""
row = [d, c, role, loc, remote, url, src, fit, os.path.basename(ME.cv_path()) if status == "Applied" else "", status, d if status == "Applied" else "", "", "", "", fu, notes]
with open(os.path.join(ME.ME_DIR, "tracker.csv"), "a", newline="") as f:
    csv.writer(f).writerow(row)
n = sum(1 for _ in open(os.path.join(ME.ME_DIR, "tracker.csv"))) - 1
print("logged", n)
