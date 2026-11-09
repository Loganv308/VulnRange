# VulnRange

Three intentionally vulnerable web apps with 10 flags, for practising in an isolated lab.

> ⚠️ These apps contain real RCE, SQLi and SSRF bugs. Run them only on an isolated lab network.
> Never port-forward them, and never run them on a box that holds anything you care about.

## Quick start

```bash
./setup.sh                          # binds to 127.0.0.1
BIND_IP=10.10.50.5 ./setup.sh       # bind to your lab-VLAN IP and attack from a Kali VM
./check_flag.py 'FLAG{...}'         # submit a flag / view progress
docker compose down -v && ./setup.sh --reset   # wipe state and regenerate flags
```

Flags are random per install and live in `.env`. Don't open it; use `check_flag.py`.

| App | URL | Stack | Port |
|---|---|---|---|
| BrokenBank | http://BIND_IP:8001 | Python / Flask / SQLite | 8001 |
| DevPortal | http://BIND_IP:8002 | Node / Express | 8002 |
| FileShare | http://BIND_IP:8003 | PHP 8.2 / Apache | 8003 |

There's also a fourth container, `metadata`. It has no published port and sits on an internal-only
Docker network. You can only reach it by pivoting through DevPortal.

## Challenges

Difficulty: ★ easy, ★★ medium, ★★★ harder

### BrokenBank (:8001)
| # | Name | Diff | Hint |
|---|---|---|---|
| 1 | Login bypass | ★ | Log in as `admin` without knowing the password. |
| 2 | The vault | ★★ | There's a table the UI never shows you. Customer search is chatty. |
| 3 | Nosy neighbour | ★ | Logged in as bob, look at what the admin wrote in *their* private note. |
| 4 | Infinite money | ★★ | Become a "premium customer" (≥ $100,000) as a normal user. |
| 5 | Templates gone wild | ★★★ | Get a shell-level read of `/home/bank/flag_ssti.txt`. Try `{{7*7}}` somewhere. |

Unflagged bonus findings: stored XSS, CSRF on transfers (it accepts GET too), verbose SQL errors,
and a hardcoded Flask `secret_key` (try forging a session with `flask-unsign`).

### DevPortal (:8002)
| # | Name | Diff | Hint |
|---|---|---|---|
| 1 | Outside the docs | ★ | `/opt/flag.txt` lives outside the docs folder. Two different bugs get you there. |
| 2 | Promote yourself | ★★ | You're `guest` with role `dev`. `/admin` wants `admin`. Look at your cookie. |
| 3 | Metadata heist | ★★★ | Steal the "cloud credentials" from the internal metadata service. Read the page source first. |

Unflagged bonus findings: an info-leak debug endpoint, a missing HttpOnly flag on the cookie, and full path disclosure.

### FileShare (:8003)
| # | Name | Diff | Hint |
|---|---|---|---|
| 1 | Read the config | ★★ | `config.php` never renders. Read its *source* anyway. |
| 2 | Shell upload | ★★★ | Get code execution and read `/flag_rce.txt`. The upload filter has two weak checks. |

Unflagged bonus finding: stored XSS through crafted upload filenames in the gallery.

## Suggested tooling
Burp Suite (Community is fine), sqlmap (do #2 by hand first), ffuf/gobuster, jwt_tool or hashcat
(`-m 16500`), flask-unsign, and a PHP webshell you write yourself.

## Learning loop
After you capture each flag, open the source, find the line marked `VULN:`, and write the fix.
Then rebuild and confirm your exploit no longer works. That last step is what turns this into
AppSec practice and not just CTF practice.

Stuck? See `SOLUTIONS.md` (spoilers).
