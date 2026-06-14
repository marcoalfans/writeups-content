# writeups-content

Content store for the **Writeups** section of
[marcoalfans.github.io](https://marcoalfans.github.io/writeups/). Kept in a
separate repo so the portfolio repo stays UI-only — the site fetches this
content at runtime (raw URLs) and renders it client-side.

## Layout

```
manifest.json              # auto-generated index (do not edit by hand)
htb/
  machines/<difficulty>/<slug>.md
  challenges/<category>.md
ctf/ , bugbounty/          # same pattern
assets/                    # screenshots referenced by writeups
scripts/gen_manifest.py    # builds manifest.json from folders + frontmatter
.github/workflows/manifest.yml
```

## Conventions

All writeups follow [`STYLE.md`](STYLE.md) — the single source of truth for frontmatter,
structure, flag masking, IP redaction, and formatting. The rules there are **enforced in CI**
(`scripts/validate.py`), so the site stays consistent as content grows.

## Authoring a writeup

1. Add a Markdown file under `htb/`, `ctf/`, or `bugbounty/` with frontmatter:

   ```markdown
   ---
   title: "Code"
   difficulty: Easy
   os: Linux
   date: 2025-08-02
   tags: [python, sudo]
   ---
   ## Summary
   ...
   ```

2. Push. The **Regenerate manifest** Action rebuilds `manifest.json`, and the
   site picks the new writeup up automatically (path → nav: `htb/machines/easy/code.md`
   becomes HackTheBox → Machines → Easy → Code).

Images: drop them in `assets/` and reference relatively; the site rewrites
relative paths to this repo's raw URL.

## Attribution

A number of the HackTheBox machine writeups in this repo were **adapted and
paraphrased** from the following MIT-licensed sources. Credit is recorded here
(rather than inside each writeup); the original MIT copyright/permission notices
are preserved in [`LICENSE`](LICENSE):

- [**momenbasel/htb-writeups**](https://github.com/momenbasel/htb-writeups) — Moamen Basel (MIT)
- [**zweilosec/htb-writeups**](https://github.com/zweilosec/htb-writeups) — zweilosec (MIT)
- [**dev-angelist/writeups-and-walkthroughs**](https://dev-angelist.gitbook.io/writeups-and-walkthroughs/hackthebox) — dev-angelist (no explicit license; included with attribution and paraphrased)

Sincere thanks to all authors. Where their material was used, the prose was
rewritten and machine metadata (difficulty, OS, points, rating, avatar, tags) was
re-sourced from the official HackTheBox API.
