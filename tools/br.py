"""Small client + CLI for the browser bridge (tools/cdpd.mjs on 127.0.0.1:9339).

CLI:
  python3 tools/br.py list                      # tabs: id, title, url
  python3 tools/br.py open <url>                # new tab (brought to front), prints id
  python3 tools/br.py goto <tab> <url>
  python3 tools/br.py eval <tab> "<js expression>"
  python3 tools/br.py click <tab> "<js expression returning an element>"   # real mouse click at its centre
  python3 tools/br.py type <tab> "<text>"       # types into the focused element
  python3 tools/br.py key <tab> Enter|Tab|Escape|ArrowDown
  python3 tools/br.py upload <tab> "<js expression returning an <input type=file>>" <file>
  python3 tools/br.py shot <tab> out.jpg        # screenshot
  python3 tools/br.py close <tab>
"""
import base64, json, os, sys, time, urllib.request

BASE = os.environ.get("BRIDGE_URL", "http://127.0.0.1:9339")
KEYS = {"Enter": ("Enter", 13), "Tab": ("Tab", 9), "Escape": ("Escape", 27), "ArrowDown": ("ArrowDown", 40), "ArrowUp": ("ArrowUp", 38), "Backspace": ("Backspace", 8)}


class Bridge:
    def call(self, cmd, body=None, timeout=120):
        req = urllib.request.Request(f"{BASE}/{cmd}", json.dumps(body or {}).encode())
        d = json.load(urllib.request.urlopen(req, timeout=timeout))
        if not d.get("ok"):
            raise RuntimeError(d.get("error"))
        return d.get("out")

    def list(self): return self.call("list")
    def raw(self, tab, method, params=None): return self.call("raw", {"id": tab, "method": method, "params": params or {}})
    def eval(self, tab, expr): return self.call("eval", {"id": tab, "expr": expr}, timeout=600)
    def goto(self, tab, url): return self.call("goto", {"id": tab, "url": url})
    def activate(self, tab): return self.call("activate", {"id": tab})
    def close(self, tab): return self.call("close", {"id": tab})

    def open(self, url):
        tab = self.call("raw", {"method": "Target.createTarget", "params": {"url": url}})["targetId"]
        self.activate(tab)
        return tab

    def click(self, tab, element_expr):
        r = self.eval(tab, "(()=>{const e=%s;if(!e)return null;e.scrollIntoView({block:'center'});const b=e.getBoundingClientRect();return JSON.stringify([b.x+b.width/2,b.y+b.height/2])})()" % element_expr)
        if not r:
            raise RuntimeError("element not found")
        x, y = json.loads(r)
        for t in ("mousePressed", "mouseReleased"):
            self.raw(tab, "Input.dispatchMouseEvent", {"type": t, "x": x, "y": y, "button": "left", "clickCount": 1})
        time.sleep(0.5)

    def type(self, tab, text): self.raw(tab, "Input.insertText", {"text": text})

    def key(self, tab, name):
        k, vk = KEYS[name]
        for t in ("rawKeyDown", "keyUp"):
            self.raw(tab, "Input.dispatchKeyEvent", {"type": t, "key": k, "code": k, "windowsVirtualKeyCode": vk})

    def upload(self, tab, element_expr, path):
        oid = self.raw(tab, "Runtime.evaluate", {"expression": element_expr})["result"]["objectId"]
        self.raw(tab, "DOM.setFileInputFiles", {"files": [os.path.abspath(path)], "objectId": oid})

    def shot(self, tab, out):
        data = self.raw(tab, "Page.captureScreenshot", {"format": "jpeg", "quality": 40})["data"]
        open(out, "wb").write(base64.b64decode(data))


if __name__ == "__main__":
    b, a = Bridge(), sys.argv[1:]
    if not a:
        print(__doc__); sys.exit(0)
    cmd = a[0]
    if cmd == "list":
        for t in b.list():
            print(t["id"], "|", t["title"][:60], "|", t["url"][:100])
    elif cmd == "open":
        print(b.open(a[1]))
    else:
        out = getattr(b, cmd)(*a[1:])
        if out is not None:
            print(out if isinstance(out, str) else json.dumps(out))
