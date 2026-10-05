# Connecting the agent to your browser ("developer mode")

The agent fills job forms in a real Chromium browser (**Brave, Chrome or Edge**) using the browser's built-in
remote-debugging feature (the "DevTools protocol"). You turn that on in ONE of two ways. Firefox and Safari are not supported.

| | Mode A: separate profile | Mode B: your main browser |
|---|---|---|
| Logins | Log in once in a fresh window | Uses the logins you already have |
| Popups | None | One "Allow" prompt per browser session |
| Your normal tabs | Never touched | Tabs the agent opens appear among yours |
| After a browser restart | Re-run the launch script | Switch the toggle on again + Allow again |
| Recommended for | Unattended / overnight runs | Quick runs when you don't want to log in again |

> Why not just launch your normal browser with `--remote-debugging-port`? Recent Chrome/Brave/Edge ignore that flag
> on your default profile for security. Mode A gives it a separate profile folder; Mode B uses the browser's own toggle.

---

## Mode A: separate profile (recommended)

### macOS / Linux
```bash
bash tools/browser-separate.sh            # Brave (default)
bash tools/browser-separate.sh --chrome   # Chrome
```
### Windows (PowerShell)
```powershell
.\tools\browser-separate.ps1                 # Brave (default)
.\tools\browser-separate.ps1 -Browser chrome # or edge
```

What happens: a NEW browser window opens with its own profile folder (`~/.job-hunt-browser`) and debugging on port 9333.

1. In that window, sign in to **LinkedIn** and **Google** (most job sites offer "Continue with Google").
   These logins are remembered for next time.
2. Start the connector in a terminal and leave it running:
   - macOS/Linux: `CDP_PORT=9333 node tools/cdpd.mjs &`
   - Windows: `$env:CDP_PORT=9333; node tools\cdpd.mjs`
3. Next time, just run the launch script again (step 1 logins are kept), then the connector.

---

## Mode B: your main browser

### 1. Turn on remote debugging ("developer mode")
| Browser | Open this address in the address bar |
|---|---|
| Brave | `brave://inspect/#remote-debugging` |
| Chrome | `chrome://inspect/#remote-debugging` |
| Edge | `edge://inspect/#remote-debugging` |

On that page, switch ON **"Allow remote debugging for this browser instance"**. The page then shows
`Server running at: 127.0.0.1:9222`. This needs a recent browser (Chromium 144+); if you don't see the toggle, update
the browser or use Mode A.

It switches itself OFF whenever the browser restarts, so repeat this step after every restart.

### 2. Start the connector
- macOS/Linux: `node tools/cdpd.mjs &` (add `CDP_BROWSER=chrome` or `CDP_BROWSER=edge` if not Brave)
- Windows: `node tools\cdpd.mjs` (or `$env:CDP_BROWSER="chrome"; node tools\cdpd.mjs`)

### 3. Click "Allow"
The browser shows a prompt asking to allow the connection. Click the browser window first, wait 2-3 seconds
(the button is briefly disabled on purpose), then click **Allow**. If the button won't click, press Tab until it is
highlighted and press Enter. You approve once per browser session; the connector keeps the connection open.

### Tips for Mode B
- Close tabs you don't need first: attaching can wake sleeping tabs and slow the computer.
- Don't use the browser heavily while a batch runs; the agent brings its own tab to the front to fill forms.
- When you're done, switch the toggle off again.

---

## Check that it works
```bash
python3 tools/selftest.py          # Windows: python tools\selftest.py
python3 tools/br.py list           # lists the browser's tabs through the connector
```

## Keep the computer awake for long runs
- macOS: `caffeinate -dims &`, charger plugged in, lid open.
- Windows: Settings > System > Power > Screen and sleep > "Never" while plugged in (set it back afterwards).
- Linux: `systemd-inhibit --what=idle:sleep sleep infinity &`

If the computer sleeps, the run pauses until it wakes. If the browser restarts, redo the steps for your mode.
