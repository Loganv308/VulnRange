#!/usr/bin/env python3
"""Check a captured flag without revealing the others. Progress is saved to .progress."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
NAMES = {
    "FLAG_BANK_SQLI_LOGIN": "BrokenBank 1 - Login bypass",
    "FLAG_BANK_SQLI_UNION": "BrokenBank 2 - The vault",
    "FLAG_BANK_IDOR": "BrokenBank 3 - Nosy neighbour",
    "FLAG_BANK_LOGIC": "BrokenBank 4 - Infinite money",
    "FLAG_BANK_SSTI": "BrokenBank 5 - Templates gone wild",
    "FLAG_DEV_FILE": "DevPortal 1 - Outside the docs",
    "FLAG_DEV_JWT": "DevPortal 2 - Promote yourself",
    "FLAG_SSRF": "DevPortal 3 - Metadata heist",
    "FLAG_FS_LFI": "FileShare 1 - Read the config",
    "FLAG_FS_RCE": "FileShare 2 - Shell upload",
}

env = dict(l.split("=", 1) for l in (ROOT / ".env").read_text().splitlines() if "=" in l)
prog_file = ROOT / ".progress"
progress = set(json.loads(prog_file.read_text())) if prog_file.exists() else set()

if len(sys.argv) > 1:
    guess = sys.argv[1].strip()
    hit = next((k for k in NAMES if env.get(k) == guess), None)
    if hit:
        progress.add(hit)
        prog_file.write_text(json.dumps(sorted(progress)))
        print(f"[+] Correct! {NAMES[hit]}")
    else:
        print("[-] Not a valid flag.")

print(f"\nProgress: {len(progress)}/{len(NAMES)}")
for k, n in NAMES.items():
    print(f"  [{'x' if k in progress else ' '}] {n}")
