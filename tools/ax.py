"""Accessibility-tree helper for pages whose UI sits in closed shadow roots (e.g. LinkedIn Easy Apply).

Library use:  from ax import AX; a = AX(tab); nodes = a.nodes(); a.click(node); a.type(node, "text")
CLI:          python3 ax.py <tab> dump [filter-substring]
Talks to the Brave bridge (tools/cdpd.mjs) on 127.0.0.1:9339.
"""
import json, os, sys, time, urllib.request

B = os.environ.get("BRIDGE_URL", "http://127.0.0.1:9339")
INTERACTIVE = {"button", "textbox", "combobox", "checkbox", "radio", "listbox", "option", "spinbutton", "link", "searchbox", "menuitem"}


def post(cmd, body):
    d = json.load(urllib.request.urlopen(urllib.request.Request(f"{B}/{cmd}", json.dumps(body).encode()), timeout=60))
    if not d["ok"]:
        raise RuntimeError(d["error"])
    return d.get("out")


class AX:
    def __init__(self, tab):
        self.tab = tab

    def raw(self, m, p=None):
        return post("raw", {"id": self.tab, "method": m, "params": p or {}})

    def nodes(self, scope_text=None):
        """Interactive nodes with role, name, value, checked, and the heading/group text they sit under."""
        tree = self.raw("Accessibility.getFullAXTree", {})["nodes"]
        by = {n["nodeId"]: n for n in tree}
        out = []
        for n in tree:
            if n.get("ignored"):
                continue
            role = n.get("role", {}).get("value")
            if role not in INTERACTIVE and role not in ("group", "radiogroup", "heading", "dialog", "alertdialog", "StaticText"):
                continue
            props = {p["name"]: p.get("value", {}).get("value") for p in n.get("properties", [])}
            out.append({
                "id": n["nodeId"], "b": n.get("backendDOMNodeId"), "role": role,
                "name": (n.get("name", {}) or {}).get("value", "") or "",
                "value": (n.get("value", {}) or {}).get("value", "") or "",
                "checked": props.get("checked"), "required": props.get("required"),
                "disabled": props.get("disabled"), "expanded": props.get("expanded"),
                "parent": n.get("parentId"),
            })
        self._by = by
        return out

    def ancestors_text(self, node, depth=6):
        txt = []
        pid = node.get("parent")
        for _ in range(depth):
            if not pid or pid not in self._by:
                break
            p = self._by[pid]
            nm = (p.get("name", {}) or {}).get("value", "")
            if nm:
                txt.append(nm)
            pid = p.get("parentId")
        return " / ".join(txt)

    def box(self, b):
        q = self.raw("DOM.getBoxModel", {"backendNodeId": b})["model"]["content"]
        return (q[0] + q[4]) / 2, (q[1] + q[5]) / 2

    def scroll(self, b):
        try:
            self.raw("DOM.scrollIntoViewIfNeeded", {"backendNodeId": b})
        except Exception:
            pass

    def click(self, node):
        b = node["b"] if isinstance(node, dict) else node
        self.scroll(b)
        time.sleep(0.3)
        x, y = self.box(b)
        for t in ("mousePressed", "mouseReleased"):
            self.raw("Input.dispatchMouseEvent", {"type": t, "x": x, "y": y, "button": "left", "clickCount": 1})
        time.sleep(0.6)

    def key(self, k, code, vk):
        for t in ("rawKeyDown", "keyUp"):
            self.raw("Input.dispatchKeyEvent", {"type": t, "key": k, "code": code, "windowsVirtualKeyCode": vk})

    def type(self, node, text, clear=True):
        b = node["b"] if isinstance(node, dict) else node
        self.scroll(b)
        self.raw("DOM.focus", {"backendNodeId": b})
        if clear:
            # select all + delete
            for t in ("rawKeyDown", "keyUp"):
                self.raw("Input.dispatchKeyEvent", {"type": t, "key": "a", "code": "KeyA", "windowsVirtualKeyCode": 65, "modifiers": 4})
            self.key("Backspace", "Backspace", 8)
        if text:
            self.raw("Input.insertText", {"text": text})
        time.sleep(0.3)

    def set_files(self, b, path):
        self.raw("DOM.setFileInputFiles", {"files": [path], "backendNodeId": b})

    def find_file_inputs(self):
        doc = self.raw("DOM.getDocument", {"depth": -1, "pierce": True})["root"]
        found = []

        def walk(n):
            if n.get("nodeName") == "INPUT":
                attrs = dict(zip(n.get("attributes", [])[::2], n.get("attributes", [])[1::2]))
                if attrs.get("type") == "file":
                    found.append((n["backendNodeId"], attrs))
            for k in ("children", "shadowRoots"):
                for c in n.get(k, []) or []:
                    walk(c)
            if n.get("contentDocument"):
                walk(n["contentDocument"])
        walk(doc)
        return found


if __name__ == "__main__":
    a = AX(sys.argv[1])
    flt = sys.argv[3].lower() if len(sys.argv) > 3 else ""
    for n in a.nodes():
        if n["role"] == "StaticText":
            continue
        line = f'{n["role"]:10} b={n["b"]} name={n["name"][:90]!r} val={str(n["value"])[:40]!r} chk={n["checked"]} req={n["required"]}'
        if flt in line.lower():
            print(line)
