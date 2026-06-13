#!/usr/bin/env python3
"""Enrich HTB machine writeups with avatar + stats from the authenticated HTB API.

Runs in CI with the HTB_TOKEN repo secret. For each htb/machines/**/<slug>.md it
fetches the machine profile, downloads the avatar into assets/htb/<slug>.png, and
writes avatar/points/rating/os/difficulty/date into the file's frontmatter so the
next gen_manifest pass bakes them into manifest.json.

No token -> no-op (exit 0), so the workflow still succeeds without the secret.
Idempotent: skips a machine whose avatar already exists and whose frontmatter
already carries `points` (delete the png to force a refresh).
"""
import os, re, json, glob, time, urllib.request, urllib.error

TOKEN = os.environ.get("HTB_TOKEN", "").strip()
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = "https://labs.hackthebox.com/api/v4/machine/profile/"
CDN = "https://labs.hackthebox.com"
UA = "Mozilla/5.0 (writeups-content enrich)"

CANON = ["title", "difficulty", "os", "points", "rating", "date", "avatar", "tags", "source", "kind", "htb_url"]

def fetch(url, token, binary=False):
    req = urllib.request.Request(url, headers={
        "Authorization": "Bearer " + token, "User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.read() if binary else json.loads(r.read())

def read_frontmatter(path):
    text = open(path, encoding="utf-8").read()
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    fm = {}
    for line in text[3:end].splitlines():
        m = re.match(r"\s*([A-Za-z_]+)\s*:\s*(.*)$", line)
        if m:
            fm[m.group(1)] = m.group(2).strip()
    return fm, text[end + 4:].lstrip("\n")

def write_frontmatter(path, fm, body):
    out = ["---"]
    for k in CANON:
        if k in fm and fm[k] not in (None, "", []):
            out.append("%s: %s" % (k, fm[k]))
    for k, v in fm.items():               # any extra keys we didn't anticipate
        if k not in CANON and v not in (None, "", []):
            out.append("%s: %s" % (k, v))
    out.append("---\n")
    open(path, "w", encoding="utf-8").write("\n".join(out) + body.lstrip("\n") + ("\n" if not body.endswith("\n") else ""))

def main():
    if not TOKEN:
        print("HTB_TOKEN not set — skipping enrichment (no-op).")
        return
    files = sorted(glob.glob(os.path.join(ROOT, "htb", "machines", "**", "*.md"), recursive=True))
    os.makedirs(os.path.join(ROOT, "assets", "htb"), exist_ok=True)
    logged_keys = False
    for path in files:
        slug = re.sub(r"\.md$", "", os.path.basename(path))
        fm, body = read_frontmatter(path)
        name = (fm.get("title") or slug).strip('"')
        avatar_rel = "assets/htb/%s.png" % slug
        avatar_abs = os.path.join(ROOT, avatar_rel)
        if os.path.exists(avatar_abs) and fm.get("points"):
            print("skip (already enriched):", slug); continue
        try:
            data = fetch(API + urllib.request.quote(name), TOKEN)
        except urllib.error.HTTPError as e:
            print("HTTP %s for %s — skipping" % (e.code, name)); continue
        except Exception as e:
            print("error for %s: %s — skipping" % (name, e)); continue
        info = data.get("info", data) if isinstance(data, dict) else {}
        if not logged_keys:                # one-time schema dump (keys only, no values)
            print("HTB profile keys:", sorted(info.keys())); logged_keys = True
        # tolerant field extraction
        av = info.get("avatar")
        pts = info.get("points") or info.get("static_points")
        rating = info.get("stars") or info.get("rating")
        os_ = info.get("os")
        diff = info.get("difficultyText") or info.get("difficulty")
        rel = info.get("release") or info.get("created_at") or ""
        if isinstance(rel, str) and "T" in rel:
            rel = rel.split("T")[0]
        if av:
            try:
                png = fetch(CDN + av if av.startswith("/") else av, TOKEN, binary=True)
                open(avatar_abs, "wb").write(png)
                fm["avatar"] = avatar_rel
            except Exception as e:
                print("avatar download failed for %s: %s" % (name, e))
        if pts: fm["points"] = pts
        if rating: fm["rating"] = rating
        if os_ and not fm.get("os"): fm["os"] = os_
        if diff and not fm.get("difficulty"): fm["difficulty"] = diff
        if rel and not fm.get("date"): fm["date"] = rel
        fm.setdefault("htb_url", "https://app.hackthebox.com/machines/%s" % urllib.request.quote(name))
        write_frontmatter(path, fm, body)
        print("enriched:", slug, "| pts:", pts, "rating:", rating)
        time.sleep(0.5)                    # be gentle with the API

if __name__ == "__main__":
    main()
