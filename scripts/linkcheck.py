#!/usr/bin/env python3
"""Report dead external links / images referenced in writeups. Non-failing —
writes a summary to the GitHub Actions job summary. 403/blocked may be false
positives (sites that reject bots), so treat the report as advisory."""
import os, re, glob, urllib.request, urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPACES = ("htb/", "ctf/", "bugbounty/")

urls = {}
for path in sorted(glob.glob(os.path.join(ROOT, "**", "*.md"), recursive=True)):
    rel = os.path.relpath(path, ROOT).replace(os.sep, "/")
    if not rel.startswith(SPACES):
        continue
    t = open(path, encoding="utf-8").read()
    for u in re.findall(r'\]\((https?://[^)\s]+)\)', t) + re.findall(r'src="(https?://[^"]+)"', t):
        urls.setdefault(u, rel)

def status(u):
    for method in ("HEAD", "GET"):
        try:
            req = urllib.request.Request(u, method=method, headers={"User-Agent": "Mozilla/5.0"})
            return urllib.request.urlopen(req, timeout=15).status
        except urllib.error.HTTPError as e:
            if method == "HEAD" and e.code in (403, 405, 501):
                continue
            return e.code
        except Exception:
            if method == "HEAD":
                continue
            return "ERR"
    return "ERR"

dead = []
for u in sorted(urls):
    code = status(u)
    if isinstance(code, int) and code < 400:
        continue
    dead.append((code, u, urls[u]))

lines = ["# Link & image health", "",
         "Checked **%d** unique URLs — **%d** flagged." % (len(urls), len(dead)),
         "", "_(403/ERR are often bot-blocking false positives.)_", ""]
for code, u, f in dead:
    lines.append("- `%s` %s  — in `%s`" % (code, u, f))
report = "\n".join(lines)
print(report)
summary = os.environ.get("GITHUB_STEP_SUMMARY")
if summary:
    with open(summary, "a") as f:
        f.write(report + "\n")
