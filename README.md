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

Some writeups here are adapted from
[**momenbasel/htb-writeups**](https://github.com/momenbasel/htb-writeups) by
Moamen Basel, used under the MIT License. The original copyright and license
notice are preserved in [`LICENSE`](LICENSE). Thanks to the original author.
