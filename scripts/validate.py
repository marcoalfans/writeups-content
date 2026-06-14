#!/usr/bin/env python3
"""Enforce the conventions in STYLE.md so writeups stay consistent.
Fails CI (exit 1) on any violation under htb/ ctf/ bugbounty/."""
import os, re, sys, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPACES = {"htb", "ctf", "bugbounty"}
DIFFS = {"easy", "medium", "hard", "insane"}

EMOJI = re.compile("[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U00002B00-\U00002BFF\U0001F000-\U0001F0FF]")
MACHINE_IP = re.compile(r"\b10\.10\.1[01]\.\d+\b|\b10\.129\.\d+\.\d+\b")
BOILERPLATE = re.compile(r"gitbook\.com|Agent Instructions|published with GitBook|Querying This Documentation|llms\.txt|buying me a coffee|Thanks to .*for creating", re.I)

def split(path):
    t = open(path, encoding="utf-8").read()
    if not t.startswith("---"):
        return None, t
    e = t.find("\n---", 3)
    if e == -1:
        return None, t
    fm = {}
    for line in t[3:e].splitlines():
        m = re.match(r"\s*([A-Za-z_]+)\s*:\s*(.+?)\s*$", line)
        if m:
            fm[m.group(1)] = m.group(2).strip().strip('"').strip("'")
    return fm, t[e + 4:]

errors = []
for path in sorted(glob.glob(os.path.join(ROOT, "**", "*.md"), recursive=True)):
    rel = os.path.relpath(path, ROOT).replace(os.sep, "/")
    parts = rel.split("/")
    if parts[0] not in SPACES or len(parts) < 2:
        continue
    fm, body = split(path)
    def err(msg): errors.append("%s: %s" % (rel, msg))

    # --- frontmatter ---
    if fm is None:
        err("missing or unparseable frontmatter"); continue
    if not fm.get("title"):
        err("missing 'title'")
    if "source" in fm:
        err("has a 'source:' line — attribution belongs in README only")
    if parts[1] == "machines" and len(parts) >= 4:
        folder = parts[2].lower(); diff = (fm.get("difficulty") or "").lower()
        if folder not in DIFFS: err("unknown difficulty folder '%s'" % folder)
        if not diff: err("missing 'difficulty'")
        elif diff != folder: err("difficulty '%s' != folder '%s'" % (diff, folder))

    # --- body conventions (see STYLE.md) ---
    b = body.lstrip("\n")
    if EMOJI.search(body): err("contains emoji — keep writeups emoji-free")
    if "<details" in body.lower(): err("uses <details> — show content inline, no collapsibles")
    if re.match(r"#\s+\S", b): err("redundant leading '# Title' — the page hero already shows it")
    if re.search(r"(?m)^\s*🔗", body): err("redundant '🔗' link line — hero already links to HTB")
    if BOILERPLATE.search(body): err("contains source/platform boilerplate (GitBook / thanks / coffee)")
    if MACHINE_IP.search(body): err("leaks a machine IP (10.10.10/11.x or 10.129.x.x) — use <YOUR_IP>")

if errors:
    print("VALIDATION FAILED (%d issue(s)) — see STYLE.md:" % len(errors))
    for e in errors:
        print("  - " + e)
    sys.exit(1)
print("All writeups valid and on-style.")
