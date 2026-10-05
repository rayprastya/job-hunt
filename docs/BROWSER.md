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

No settings to change in your browser: the launch script starts a second browser window with debugging already on.

### Step 1. Launch it
- macOS/Linux: `bash tools/browser-separate.sh` (Chrome: add `--chrome`)
- Windows (PowerShell): `.\tools\browser-separate.ps1` (or `-Browser chrome` / `-Browser edge`)

A NEW browser window opens. It looks like a fresh browser (no bookmarks, no logins). That's the job-hunt profile,
stored in `~/.job-hunt-browser` (Windows: `%USERPROFILE%\.job-hunt-browser`).

### Step 2. Log in, inside that new window (once)
1. Go to `linkedin.com` and sign in.
2. Go to `accounts.google.com` and sign in (so "Continue with Google" works on job sites and the tracker sheet opens).
3. Optional: sign in to job boards you use (JobStreet, Glints, Kalibrr...).
4. Optional but recommended: in LinkedIn open `linkedin.com/jobs/application-settings` and upload your CV once,
   then put its file name in `me/profile.json` -> `files.linkedin_resume_name`.

These logins stay saved in that profile for next time.

### Step 3. Start the connector
- macOS/Linux: `CDP_PORT=9333 node tools/cdpd.mjs &`
- Windows: `$env:CDP_PORT=9333; node tools\cdpd.mjs`
No "Allow" prompt appears in this mode.

### Every next time
Run step 1 (the window opens already logged in) and step 3. Keep that window open while the agent works;
you can minimise it but don't close it.

---

## Mode B: your main browser (turn on "developer mode")

Everything here happens **inside the browser**, no terminal needed except step 3.

### Step 1. Open the remote-debugging page
Click the address bar (where you type websites), paste the address for your browser, press Enter:

| Browser | Paste this into the address bar |
|---|---|
| Brave | `brave://inspect/#remote-debugging` |
| Google Chrome | `chrome://inspect/#remote-debugging` |
| Microsoft Edge | `edge://inspect/#remote-debugging` |

(It's not a website, it's a built-in settings page, so it only works typed into the address bar.)

### Step 2. Switch it on
The page looks roughly like this. Find the **Remote debugging** section near the top and tick the box:

```
 ┌──────────────────────────────────────────────────────────────┐
 │  Inspect with Chrome Developer Tools                         │
 │  Devices | Pages | Extensions | Apps | ... | Remote debugging│  <- this tab is selected by the #remote-debugging link
 │                                                              │
 │  Remote debugging                                            │
 │  [x] Allow remote debugging for this browser instance        │  <- TICK THIS
 │      Server running at: 127.0.0.1:9222                       │  <- appears once it's on
 └──────────────────────────────────────────────────────────────┘
```

- When **"Server running at: 127.0.0.1:9222"** appears, it's on.
- No such option? Update the browser (menu > About > update) or use Mode A. It needs a recent version (Chromium 144+).
- It turns itself **off every time the browser restarts**: repeat steps 1-2 after a restart.

### Step 3. Start the connector (the AI can do this for you)
Ask your AI agent "start the browser connector", or run it yourself:
- macOS/Linux: `node tools/cdpd.mjs &` (Chrome: `CDP_BROWSER=chrome node tools/cdpd.mjs &`, Edge: `CDP_BROWSER=edge ...`)
- Windows: `node tools\cdpd.mjs` (Chrome: `$env:CDP_BROWSER="chrome"; node tools\cdpd.mjs`)

### Step 4. Click "Allow" in the browser
Right after step 3, the browser pops up a small dialog, roughly:

```
 ┌──────────────────────────────────────────────┐
 │  Allow remote debugging?                      │
 │  An application wants to control this browser │
 │                          [ Cancel ]  [ Allow ]│
 └──────────────────────────────────────────────┘
```
- Click the browser window first, **wait 2-3 seconds** (the Allow button is greyed out briefly on purpose), then click **Allow**.
- Button won't click? Press **Tab** until "Allow" is highlighted, then **Enter**.
- Missed it or it disappeared? Ask the agent to restart the connector; a fresh prompt appears.
- You'll see a bar "Brave/Chrome is being controlled by automated test software" while connected. That's expected.

You approve once per browser session. If the browser restarts: steps 1, 2, 3, 4 again.

### Step 5. Turn it off when you're done (optional, recommended)
Go back to the page from step 1 and untick the box, or just restart the browser.

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
