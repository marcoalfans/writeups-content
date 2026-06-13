#!/usr/bin/env python3
"""Validate writeup frontmatter so a malformed file can't break the site.
Exits non-zero (fails CI) if any writeup under htb/ ctf/ bugbounty/ is invalid."""
import os, re, sys, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPACES = {"htb", "ctf", "bugbounty"}
DIFFS = {"easy", "medium", "hard", "insane"}

def frontmatter(path):
    t = open(path, encoding="utf-8").read()
    if not t.startswith("---"):
        return None
    e = t.find("\n---", 3)
    if e == -1:
        return None
    d = {}
    for line in t[3:e].splitlines():
        m = re.match(r"\s*([A-Za-z_]+)\s*:\s*(.+?)\s*$", line)
        if m:
            d[m.group(1)] = m.group(2).strip().strip('"').strip("'")
    return d

errors = []
for path in sorted(glob.glob(os.path.join(ROOT, "**", "*.md"), recursive=True)):
    rel = os.path.relpath(path, ROOT).replace(os.sep, "/")
    parts = rel.split("/")
    if parts[0] not in SPACES or len(parts) < 2:
        continue
    d = frontmatter(path)
    if d is None:
        errors.append("%s: missing or unparseable frontmatter" % rel); continue
    if not d.get("title"):
        errors.append("%s: missing 'title'" % rel)
    # machine writeups: htb/machines/<difficulty>/<slug>.md — folder must match difficulty
    if parts[1] == "machines" and len(parts) >= 4:
        folder = parts[2].lower()
        diff = (d.get("difficulty") or "").lower()
        if folder not in DIFFS:
            errors.append("%s: unknown difficulty folder '%s'" % (rel, folder))
        if not diff:
            errors.append("%s: missing 'difficulty'" % rel)
        elif diff != folder:
            errors.append("%s: difficulty '%s' != folder '%s'" % (rel, diff, folder))

if errors:
    print("VALIDATION FAILED (%d issue(s)):" % len(errors))
    for e in errors:
        print("  - " + e)
    sys.exit(1)
print("All writeups valid.")
