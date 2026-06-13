#!/usr/bin/env python3
"""Regenerate manifest.json by scanning writeup folders + frontmatter.
Run by .github/workflows/manifest.yml on every push. Authoring a writeup =
add a .md under htb/ , ctf/ or bugbounty/ — the manifest updates itself.

Path -> nav mapping:  htb/machines/easy/code.md
  space    = htb            (first path segment)
  category = [machines,easy] (segments between space and filename)
  slug     = code            (filename without .md)
"""
import os, re, json, glob

SPACES = {"htb", "ctf", "bugbounty"}
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def parse_frontmatter(text):
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    fm = {}
    for line in text[3:end].splitlines():
        m = re.match(r"\s*([A-Za-z_]+)\s*:\s*(.+?)\s*$", line)
        if not m:
            continue
        key, val = m.group(1), m.group(2).strip()
        val = val.strip('"').strip("'")
        if val.startswith("[") and val.endswith("]"):
            val = [v.strip().strip('"').strip("'") for v in val[1:-1].split(",") if v.strip()]
        fm[key] = val
    return fm

entries = []
for path in sorted(glob.glob(os.path.join(ROOT, "**", "*.md"), recursive=True)):
    rel = os.path.relpath(path, ROOT).replace(os.sep, "/")
    parts = rel.split("/")
    if parts[0] not in SPACES or len(parts) < 2:
        continue
    space = parts[0]
    category = parts[1:-1]
    slug = re.sub(r"\.md$", "", parts[-1])
    with open(path, encoding="utf-8") as f:
        fm = parse_frontmatter(f.read())
    entry = {"space": space, "category": category, "slug": slug,
             "title": fm.get("title", slug.replace("-", " ").title()), "file": rel}
    for k in ("difficulty", "os", "date"):
        if fm.get(k):
            entry[k] = fm[k]
    entry["tags"] = fm.get("tags", []) if isinstance(fm.get("tags"), list) else []
    entries.append(entry)

entries.sort(key=lambda e: (e["space"], e["category"], e["slug"]))
manifest = {"version": 1, "count": len(entries), "entries": entries}
with open(os.path.join(ROOT, "manifest.json"), "w", encoding="utf-8") as f:
    f.write(json.dumps(manifest, indent=2) + "\n")
print("manifest.json: %d entries" % len(entries))
