"""Render an HTML CV (e.g. a tailored copy of templates/cv-example.html) to PDF with headless Chrome/Brave/Edge.
Usage: python3 tools/cv_pdf.py me/cv/backend.html me/cv/Your_Name_CV.pdf
"""
import os, shutil, subprocess, sys
src, out = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
cands = ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
         "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge", shutil.which("google-chrome") or "", shutil.which("chromium") or "",
         shutil.which("brave-browser") or "", r"C:\Program Files\Google\Chrome\Application\chrome.exe",
         r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe", r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"]
exe = next((c for c in cands if c and os.path.exists(c)), None)
if not exe:
    sys.exit("No Chrome/Brave/Edge found to render the PDF.")
subprocess.run([exe, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", f"--print-to-pdf={out}", "file://" + src.replace("\\", "/")],
               check=True, stderr=subprocess.DEVNULL)
print("wrote", out)
