# BrokenBank -- INTENTIONALLY VULNERABLE. Lab use only. Never expose to the internet.
import os
import sqlite3
from flask import Flask, request, session, redirect, render_template_string, g

app = Flask(__name__)
app.secret_key = "dev"  # VULN: hardcoded, guessable signing key
DB = "/tmp/bank.db"

LAYOUT = """<!doctype html><html><head><title>BrokenBank</title>
<style>body{font-family:sans-serif;max-width:760px;margin:2rem auto;padding:0 1rem}
nav a{margin-right:1rem}table{border-collapse:collapse;width:100%}td,th{border:1px solid #ccc;padding:.4rem}
.err{color:#b00;white-space:pre-wrap}</style></head><body>
<nav><b>BrokenBank</b> | <a href="/">Home</a><a href="/search">Customer search</a><a href="/greet">Greeter</a>
{% if session.uid %}<a href="/dashboard">Dashboard</a><a href="/logout">Logout</a>{% else %}<a href="/login">Login</a>{% endif %}</nav><hr>
{{ body|safe }}</body></html>"""


def page(body, **ctx):
    return render_template_string(LAYOUT, body=render_template_string(body, **ctx))


def db():
    if "db" not in g:
        g.db = sqlite3.connect(DB)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_):
    d = g.pop("db", None)
    if d:
        d.close()


def init_db():
    c = sqlite3.connect(DB)
    c.executescript("""
    DROP TABLE IF EXISTS users; DROP TABLE IF EXISTS transfers; DROP TABLE IF EXISTS secrets;
    CREATE TABLE users(id INTEGER PRIMARY KEY, username TEXT, password TEXT, balance INTEGER, role TEXT, note TEXT);
    CREATE TABLE transfers(id INTEGER PRIMARY KEY, src INTEGER, dst INTEGER, amount INTEGER, memo TEXT);
    CREATE TABLE secrets(id INTEGER PRIMARY KEY, name TEXT, value TEXT);
    """)
    c.executemany(
        "INSERT INTO users(username,password,balance,role,note) VALUES(?,?,?,?,?)",
        [
            ("admin", "Xq!9vT#2mL$8zR", 1000000, "admin", os.environ.get("FLAG_BANK_IDOR", "")),
            ("alice", "alice123", 5000, "user", "Saving for a boat"),
            ("bob", "password", 120, "user", "Remember to change my password"),
        ],
    )
    c.execute("INSERT INTO secrets(name,value) VALUES('vault',?)", (os.environ.get("FLAG_BANK_SQLI_UNION", ""),))
    c.commit()
    c.close()


@app.route("/")
def index():
    return page("<h2>Welcome to BrokenBank</h2><p>Banking you can (not) trust.</p>"
                "<p>Test account: <code>bob / password</code></p>")


@app.route("/login", methods=["GET", "POST"])
def login():
    err = ""
    if request.method == "POST":
        u, p = request.form.get("username", ""), request.form.get("password", "")
        # VULN: SQL injection (string-built query)
        q = f"SELECT * FROM users WHERE username='{u}' AND password='{p}'"
        try:
            row = db().execute(q).fetchone()
        except Exception as e:
            row, err = None, f"DB error: {e}\nQuery: {q}"  # VULN: verbose errors
        if row:
            session["uid"], session["username"], session["role"] = row["id"], row["username"], row["role"]
            return redirect("/dashboard")
        err = err or "Invalid credentials"
    return page("""<h2>Login</h2><form method=post>
      <input name=username placeholder=username> <input name=password type=password placeholder=password>
      <button>Login</button></form><p class=err>{{err}}</p>""", err=err)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/dashboard")
def dashboard():
    if "uid" not in session:
        return redirect("/login")
    me = db().execute("SELECT * FROM users WHERE id=?", (session["uid"],)).fetchone()
    txs = db().execute(
        "SELECT t.*, a.username s, b.username d FROM transfers t JOIN users a ON a.id=t.src "
        "JOIN users b ON b.id=t.dst WHERE t.src=? OR t.dst=? ORDER BY t.id DESC", (me["id"], me["id"])).fetchall()
    extra = ""
    if me["role"] == "admin":
        extra += f"<p><b>Admin console:</b> {os.environ.get('FLAG_BANK_SQLI_LOGIN','')}</p>"
    if me["role"] != "admin" and me["balance"] >= 100000:
        extra += f"<p><b>Premium customer reward:</b> {os.environ.get('FLAG_BANK_LOGIC','')}</p>"
    # VULN: memo rendered with |safe -> stored XSS. Transfer form has no CSRF token.
    return page("""<h2>Hi {{me.username}}</h2><p>Balance: ${{me.balance}} | <a href="/account/{{me.id}}">Account details</a></p>
      {{extra|safe}}
      <h3>Send money</h3><form method=post action=/transfer>
      <input name=to placeholder="recipient username"> <input name=amount placeholder=amount>
      <input name=memo placeholder=memo> <button>Send</button></form>
      <h3>History</h3><table><tr><th>From</th><th>To</th><th>Amount</th><th>Memo</th></tr>
      {% for t in txs %}<tr><td>{{t.s}}</td><td>{{t.d}}</td><td>{{t.amount}}</td><td>{{t.memo|safe}}</td></tr>{% endfor %}
      </table>""", me=me, txs=txs, extra=extra)


@app.route("/transfer", methods=["GET", "POST"])  # VULN: state change also allowed over GET
def transfer():
    if "uid" not in session:
        return redirect("/login")
    f = request.values
    dst = db().execute("SELECT id FROM users WHERE username=?", (f.get("to", ""),)).fetchone()
    try:
        amount = int(f.get("amount", "0"))
    except ValueError:
        return page("<p class=err>Bad amount</p>")
    if not dst:
        return page("<p class=err>No such user</p>")
    src_bal = db().execute("SELECT balance FROM users WHERE id=?", (session["uid"],)).fetchone()[0]
    if amount > src_bal:  # VULN: no check for negative amounts
        return page("<p class=err>Insufficient funds</p>")
    d = db()
    d.execute("UPDATE users SET balance=balance-? WHERE id=?", (amount, session["uid"]))
    d.execute("UPDATE users SET balance=balance+? WHERE id=?", (amount, dst["id"]))
    d.execute("INSERT INTO transfers(src,dst,amount,memo) VALUES(?,?,?,?)", (session["uid"], dst["id"], amount, f.get("memo", "")))
    d.commit()
    return redirect("/dashboard")


@app.route("/account/<int:uid>")
def account(uid):
    if "uid" not in session:
        return redirect("/login")
    # VULN: IDOR -- no ownership check
    row = db().execute("SELECT id, username, balance, role, note FROM users WHERE id=?", (uid,)).fetchone()
    if not row:
        return page("<p>Not found</p>"), 404
    return page("""<h2>Account #{{r.id}}</h2><ul><li>User: {{r.username}}</li><li>Balance: ${{r.balance}}</li>
      <li>Role: {{r.role}}</li><li>Private note: {{r.note}}</li></ul>""", r=row)


@app.route("/search")
def search():
    q = request.args.get("q", "")
    rows, err = [], ""
    if q:
        sql = f"SELECT username, role FROM users WHERE username LIKE '%{q}%'"  # VULN: SQLi (UNION-able)
        try:
            rows = db().execute(sql).fetchall()
        except Exception as e:
            err = f"DB error: {e}"
    return page("""<h2>Customer search</h2><form><input name=q value="{{q}}"><button>Search</button></form>
      <p class=err>{{err}}</p><ul>{% for r in rows %}<li>{{r[0]}} ({{r[1]}})</li>{% endfor %}</ul>""",
                q=q, rows=rows, err=err)


@app.route("/greet")
def greet():
    name = request.args.get("name", "guest")
    # VULN: server-side template injection
    return render_template_string(LAYOUT, body=render_template_string(
        "<h2>Greeter</h2><form><input name=name><button>Greet</button></form><p>Hello, " + name + "!</p>"))


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)
