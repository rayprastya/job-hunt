// Persistent CDP bridge: holds ONE connection to the running Brave (so Brave's
// "Allow remote debugging" prompt is answered once) and serves commands on
// http://127.0.0.1:9339 as POST /<cmd> with a JSON body.
//   list                         -> [{id,title,url}]
//   open   {url}                 -> {id}   (new background tab)
//   goto   {id,url}
//   eval   {id,expr}             -> value  (awaits promises)
//   close  {id}
//   activate {id}                -> bring tab to front (background tabs may not load)
//   raw    {id?,method,params}   -> any CDP command (e.g. DOM.setFileInputFiles)
// Only tabs this bridge opened are attached to, so the user's other tabs are never woken.
import http from "node:http";
import { readFileSync } from "node:fs";
import { homedir } from "node:os";

// Endpoint: CDP_WS (full ws URL) > CDP_PORT (separate profile started with --remote-debugging-port)
// > the main browser's DevToolsActivePort file (Brave by default, CDP_BROWSER=chrome for Chrome).
async function endpoint() {
  if (process.env.CDP_WS) return process.env.CDP_WS;
  if (process.env.CDP_PORT) {
    const v = await (await fetch(`http://127.0.0.1:${process.env.CDP_PORT}/json/version`)).json();
    return v.webSocketDebuggerUrl;
  }
  const mac = process.platform === "darwin";
  const base = process.env.CDP_BROWSER === "chrome"
    ? (mac ? `${homedir()}/Library/Application Support/Google/Chrome` : `${homedir()}/.config/google-chrome`)
    : (mac ? `${homedir()}/Library/Application Support/BraveSoftware/Brave-Browser` : `${homedir()}/.config/BraveSoftware/Brave-Browser`);
  const [port, path] = readFileSync(`${base}/DevToolsActivePort`, "utf8").trim().split("\n");
  return `ws://127.0.0.1:${port}${path}`;
}
const ws = new WebSocket(await endpoint());
let seq = 0;
const pending = new Map();
const sessions = new Map();
ws.onmessage = (m) => {
  const d = JSON.parse(m.data);
  if (d.id && pending.has(d.id)) {
    const { res, rej } = pending.get(d.id);
    pending.delete(d.id);
    d.error ? rej(new Error(d.error.message)) : res(d.result);
  }
};
ws.onclose = () => { console.log("brave connection closed"); process.exit(1); };
const send = (method, params = {}, sessionId) =>
  new Promise((res, rej) => {
    const id = ++seq;
    pending.set(id, { res, rej });
    ws.send(JSON.stringify({ id, method, params, ...(sessionId ? { sessionId } : {}) }));
  });
const session = async (id) => {
  if (!sessions.has(id)) sessions.set(id, (await send("Target.attachToTarget", { targetId: id, flatten: true })).sessionId);
  return sessions.get(id);
};

const handlers = {
  async list() {
    const { targetInfos } = await send("Target.getTargets");
    return targetInfos.filter((t) => t.type === "page").map((t) => ({ id: t.targetId, title: t.title, url: t.url }));
  },
  async open({ url }) {
    return { id: (await send("Target.createTarget", { url, background: true })).targetId };
  },
  async goto({ id, url }) {
    await send("Page.navigate", { url }, await session(id));
    return "ok";
  },
  async eval({ id, expr }) {
    const r = await send("Runtime.evaluate", { expression: expr, awaitPromise: true, returnByValue: true, userGesture: true }, await session(id));
    if (r.exceptionDetails) throw new Error(r.exceptionDetails.exception?.description || r.exceptionDetails.text);
    return r.result.value;
  },
  async activate({ id }) {
    await send("Target.activateTarget", { targetId: id });
    return "ok";
  },
  async raw({ id, method, params }) {
    return await send(method, params || {}, id ? await session(id) : undefined);
  },
  async close({ id }) {
    sessions.delete(id);
    await send("Target.closeTarget", { targetId: id });
    return "ok";
  },
};

ws.onopen = async () => {
  await send("Target.getTargets"); // resolves once Brave has allowed the connection
  console.log("connected to brave");
  http
    .createServer((req, res) => {
      let body = "";
      req.on("data", (c) => (body += c));
      req.on("end", async () => {
        const h = handlers[req.url.slice(1)];
        try {
          if (!h) throw new Error("unknown command");
          const out = await h(body ? JSON.parse(body) : {});
          res.end(JSON.stringify({ ok: true, out }));
        } catch (e) {
          res.end(JSON.stringify({ ok: false, error: e.message }));
        }
      });
    })
    .listen(9339, "127.0.0.1", () => console.log("bridge on 127.0.0.1:9339"));
};
