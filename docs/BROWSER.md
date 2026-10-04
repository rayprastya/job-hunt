# Connecting the agent to your browser

The agent drives a Chromium browser (Brave or Chrome) through the DevTools protocol. Pick ONE mode.

## Mode A: separate browser profile (simplest, recommended)

Pros: no prompts, never touches your normal tabs. Cons: you log in to job sites once in this profile.

```bash
bash tools/browser-separate.sh            # Brave; use --chrome for Chrome
```

It opens a new window with its own profile (`~/.job-hunt-browser`) and debugging on port 9333.
Log in once to LinkedIn and Google ("Continue with Google" covers most job sites). Logins persist.
Then start the bridge pointing at it:

```bash
CDP_PORT=9333 node tools/cdpd.mjs &       # keep it running
```

## Mode B: your main browser (keeps your existing logins)

1. Close tabs you don't need (attaching can wake sleeping tabs).
2. Open `brave://inspect/#remote-debugging` (Chrome: `chrome://inspect/#remote-debugging`) and turn on
   "Allow remote debugging for this browser instance". It resets every time the browser restarts.
3. Start the bridge:
   ```bash
   node tools/cdpd.mjs &
   ```
4. The browser shows an "Allow" prompt once. Click the browser window, wait 2-3 seconds, then click Allow
   (or Tab to it and press Enter).

The bridge holds one connection, so you approve once per browser session. If the browser restarts,
repeat steps 2-4.

## Check it works

```bash
curl -s -X POST http://127.0.0.1:9339/list | head -c 300
```

## Keep the computer awake for long runs

```bash
caffeinate -dims &      # macOS; plug in the charger and keep the lid open
```

If the computer sleeps, the run stops until it wakes.
