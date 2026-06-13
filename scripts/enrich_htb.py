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
TAGS = "https://labs.hackthebox.com/api/v4/machine/tags/"
TAG_ORDER = {"Vulnerability": 0, "Technique": 1, "Language": 2, "Technology": 3, "Area of Interest": 4}
CDN = "https://labs.hackthebox.com"
UA = "Mozilla/5.0 (writeups-content enrich)"

CANON = ["title", "difficulty", "os", "points", "rating", "date", "avatar", "tags", "source", "kind", "htb_url"]

S3 = "https://htb-mp-prod-public-storage.s3.eu-central-1.amazonaws.com/avatars/"

def fetch(url, token, binary=False, auth=True):
    headers = {"User-Agent": UA, "Accept": "application/json"}
    if auth and token:
        headers["Authorization"] = "Bearer " + token
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=25) as r:
        return r.read() if binary else json.loads(r.read())

def download_avatar(av, token):
    """Avatars live on the public S3 bucket (most machines) or the labs CDN.
    Return image bytes >= 2KB (skips HTB's 1-bit default placeholder), else None."""
    base = av.split("/")[-1]
    candidates = [(S3 + base, False)]
    if av.startswith("/avatars/"):
        candidates.append((CDN + "/storage" + av, True))
    elif av.startswith("/"):
        candidates.append((CDN + av, True))
    for url, auth in candidates:
        try:
            png = fetch(url, token, binary=True, auth=auth)
            if png and len(png) >= 2048:
                return png
        except Exception:
            pass
    return None

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
        # fetch profile with retry/backoff — HTB rate-limits with empty/429 responses
        info = None
        for attempt in range(4):
            try:
                data = fetch(API + urllib.request.quote(name), TOKEN)
                info = data.get("info", data) if isinstance(data, dict) else {}
                break
            except urllib.error.HTTPError as e:
                if e.code in (429, 500, 502, 503) and attempt < 3:
                    time.sleep(3 * (attempt + 1)); continue
                print("HTTP %s for %s — skipping" % (e.code, name)); break
            except Exception as e:
                if attempt < 3:
                    time.sleep(3 * (attempt + 1)); continue
                print("error for %s: %s — skipping" % (name, e)); break
        if info is None:
            continue
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
            if os.path.exists(avatar_abs):
                fm["avatar"] = avatar_rel          # already downloaded — keep it
            else:
                png = download_avatar(av, TOKEN)
                if png:
                    open(avatar_abs, "wb").write(png)
                    fm["avatar"] = avatar_rel
                else:
                    fm.pop("avatar", None)         # no real avatar — use themed fallback
                    print("no real avatar for %s — using fallback" % name)
        # HTB API is the source of truth — OVERRIDE local values so folder/badge can't drift
        if pts: fm["points"] = pts
        if rating: fm["rating"] = rating
        if os_: fm["os"] = os_
        if diff: fm["difficulty"] = diff
        if rel: fm["date"] = rel
        fm.setdefault("htb_url", "https://app.hackthebox.com/machines/%s" % urllib.request.quote(name))

        # official HTB tags (authoritative) -> frontmatter tags, ordered + capped
        mid = info.get("id")
        if mid:
            for attempt in range(4):
                try:
                    td = fetch(TAGS + str(mid), TOKEN)
                    tl = td.get("info", []) if isinstance(td, dict) else (td if isinstance(td, list) else [])
                    tl = sorted([t for t in tl if t.get("name")], key=lambda t: TAG_ORDER.get(t.get("category"), 9))
                    names = []
                    for t in tl:
                        if t["name"] not in names: names.append(t["name"])
                    if names: fm["tags"] = "[" + ", ".join(names[:8]) + "]"
                    break
                except urllib.error.HTTPError as e:
                    if e.code in (429, 500, 502, 503) and attempt < 3: time.sleep(3 * (attempt + 1)); continue
                    break
                except Exception:
                    if attempt < 3: time.sleep(3 * (attempt + 1)); continue
                    break

        # re-file into the correct difficulty folder if HTB disagrees with our path
        dest = path
        m = re.match(r"(.*/htb/machines/)([^/]+)(/.+\.md)$", path.replace(os.sep, "/"))
        if m and diff and diff.lower() in ("easy", "medium", "hard", "insane") and m.group(2).lower() != diff.lower():
            dest = os.path.join(ROOT, "htb", "machines", diff.lower(), os.path.basename(path))
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            print("re-filed %s: %s -> %s" % (slug, m.group(2), diff.lower()))
        write_frontmatter(dest, fm, body)
        if dest != path:
            os.remove(path)
        print("enriched:", slug, "| diff:", diff, "| pts:", pts, "rating:", rating)
        time.sleep(1.2)                    # be gentle with the API (avoid rate limits)

if __name__ == "__main__":
    main()
