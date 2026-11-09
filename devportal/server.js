// DevPortal -- INTENTIONALLY VULNERABLE. Lab use only. Never expose to the internet.
const express = require("express");
const { exec } = require("child_process");
const fs = require("fs");
const path = require("path");
const http = require("http");
const jwt = require("jsonwebtoken");
const cookieParser = require("cookie-parser");

const app = express();
app.use(express.urlencoded({ extended: true }));
app.use(express.json());
app.use(cookieParser());

const JWT_SECRET = "secret123"; // VULN: weak secret, crackable with hashcat/jwt_tool + rockyou
const DOCS = path.join(__dirname, "docs");
const USERS = { guest: { pass: "guest", role: "dev" } };

const page = (body) => `<!doctype html><html><head><title>DevPortal</title>
<style>body{font-family:monospace;max-width:800px;margin:2rem auto;padding:0 1rem;background:#111;color:#ddd}
a{color:#6cf;margin-right:1rem}pre{background:#222;padding:1rem;white-space:pre-wrap}input{width:60%}</style></head>
<body><nav><b>DevPortal</b> | <a href="/">Home</a><a href="/tools/ping">Ping</a><a href="/docs?file=welcome.txt">Docs</a>
<a href="/tools/preview">Link preview</a><a href="/admin">Admin</a><a href="/login">Login</a></nav><hr>${body}</body></html>`;

// VULN: role taken from token payload; jwt.verify allows "none" when algorithms are not pinned in old style usage.
function currentUser(req) {
  const t = req.cookies.token;
  if (!t) return null;
  try {
    const decoded = jwt.decode(t, { complete: true });
    if (decoded && decoded.header.alg === "none") return decoded.payload; // VULN: accepts unsigned tokens
    return jwt.verify(t, JWT_SECRET);
  } catch (e) {
    return null;
  }
}

app.get("/", (req, res) => {
  res.send(page(`<h2>Internal developer portal</h2><p>Login: <code>guest / guest</code></p>
  <!-- TODO: remove debug endpoint /debug/env before go-live -->`)); // VULN: info leak in HTML comment
});

app.get("/login", (req, res) =>
  res.send(page(`<h2>Login</h2><form method=post><input name=username placeholder=user><br>
  <input name=password type=password placeholder=pass><br><button>Login</button></form>`)));

app.post("/login", (req, res) => {
  const { username, password } = req.body;
  const u = USERS[username];
  if (!u || u.pass !== password) return res.send(page("<p>Bad login</p>"));
  const token = jwt.sign({ user: username, role: u.role }, JWT_SECRET, { algorithm: "HS256" });
  res.cookie("token", token); // VULN: no HttpOnly / Secure / SameSite
  res.redirect("/");
});

app.get("/admin", (req, res) => {
  const u = currentUser(req);
  if (!u) return res.status(401).send(page("<p>Login required</p>"));
  if (u.role !== "admin") return res.status(403).send(page(`<p>Hi ${u.user}, admins only.</p>`));
  res.send(page(`<h2>Admin</h2><p>${process.env.FLAG_DEV_JWT || ""}</p>`));
});

app.get("/tools/ping", (req, res) => {
  const host = req.query.host;
  if (!host) return res.send(page(`<h2>Ping</h2><form><input name=host placeholder="10.0.0.1"><button>Ping</button></form>`));
  // VULN: OS command injection. Naive blocklist is bypassable.
  if (/[;&]/.test(host)) return res.send(page("<p>Nice try. Blocked characters.</p>"));
  exec(`ping -c 1 -W 1 ${host}`, { timeout: 5000 }, (err, stdout, stderr) =>
    res.send(page(`<h2>Ping</h2><pre>${stdout}${stderr}</pre>`)));
});

app.get("/docs", (req, res) => {
  const file = req.query.file || "welcome.txt";
  // VULN: path traversal. Strips "../" once, non-recursively.
  const cleaned = file.replace("../", "");
  const p = path.join(DOCS, cleaned);
  fs.readFile(p, "utf8", (err, data) => {
    if (err) return res.status(404).send(page(`<p>Not found: ${p}</p>`)); // VULN: path disclosure
    res.send(page(`<h2>${cleaned}</h2><pre>${data.replace(/</g, "&lt;")}</pre>`));
  });
});

app.get("/tools/preview", (req, res) => {
  const url = req.query.url;
  if (!url) return res.send(page(`<h2>Link preview</h2><form><input name=url placeholder="http://example.com"><button>Fetch</button></form>`));
  // VULN: SSRF. Blocks the literal string "localhost" only; internal Docker hosts are reachable.
  if (url.includes("localhost") || url.includes("127.0.0.1")) return res.send(page("<p>Internal addresses are blocked.</p>"));
  try {
    http.get(url, { timeout: 4000 }, (r) => {
      let body = "";
      r.on("data", (c) => (body += c));
      r.on("end", () => res.send(page(`<h2>Preview of ${url}</h2><pre>${body.slice(0, 4000).replace(/</g, "&lt;")}</pre>`)));
    }).on("error", (e) => res.send(page(`<p>Error: ${e.message}</p>`)));
  } catch (e) {
    res.send(page(`<p>Error: ${e.message}</p>`));
  }
});

app.get("/debug/env", (req, res) => {
  // VULN: debug endpoint left enabled; leaks config hints (flag value redacted, but hostnames are not)
  const safe = Object.fromEntries(Object.entries(process.env).map(([k, v]) => [k, k.startsWith("FLAG") ? "[redacted]" : v]));
  res.json(safe);
});

app.listen(3000, "0.0.0.0", () => console.log("DevPortal on :3000"));
