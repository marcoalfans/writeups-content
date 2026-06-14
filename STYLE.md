# Writeup Style Guide

The single source of truth for how writeups in this repo are written and formatted,
so the site stays consistent. The checkable rules are **enforced in CI** by
`scripts/validate.py` (a violating writeup fails the build).

## Frontmatter

```markdown
---
title: "Code"
difficulty: Easy
---
## Summary
...
```

- **You set only** `title` and `difficulty` (and the difficulty folder must match).
- **Auto-managed by the enrich Action** from the official HackTheBox API — do **not** hand-edit:
  `os`, `points`, `rating`, `date`, `avatar`, `tags`, `htb_url`. Just push the writeup; the
  Action fills these and re-files the machine into the correct difficulty folder.
- **No `source:` line.** Attribution lives in [`README.md`](README.md) only.

## Structure (house narrative style)

A writeup is a first-person, narrative walkthrough — **not** a Task/Q&A list. Use these
`##` sections, in order (skip one only if genuinely N/A), with `###` subsections as needed:

1. `## Summary` — one short paragraph: what the box is, its OS, and the attack chain.
2. `## Enumeration` — port/service scanning and web/service discovery.
3. `## Foothold` — how initial access / the user shell was obtained.
4. `## Privilege Escalation` — how root/SYSTEM was obtained.

## Flags

- Always **mask** flags: keep the first 4 and last 4 hex characters and replace the middle
  with asterisks, **preserving the full 32-char length** — e.g. `5d3f************************16bd`.
- Show flags **plainly inline** (e.g. `**user.txt** — \`<masked>\``, or as `cat user.txt` output).
- Never reveal a real flag. Never hide flags in `<details>` collapsibles.

## IP addresses

- Redact the **machine/target IP** as `<YOUR_IP>` (ranges `10.10.10.x`, `10.10.11.x`, `10.129.x.x`).
- **Keep** your attacker/VPN IP (`10.10.14.x`, `10.10.15.x`) so reverse-shell commands stay coherent.

## Images

- **Self-host** under `assets/wu/<machine>/` and reference them repo-root-relative
  (`assets/wu/<machine>/...`). No hotlinks to other sites.
- The machine **avatar** is fetched automatically (official HTB) — don't add one by hand.

## Code

- Use fenced ` ```lang ` blocks. Convert any HTML `<pre>`/`<code>` blocks to fenced blocks.

## Don'ts (all enforced by CI)

- ❌ No emojis anywhere — keep writeups **uniformly emoji-free**.
- ❌ No `<details>` / `<summary>` collapsibles.
- ❌ No redundant leading `# Title` heading or `🔗 [Title](...)` link (the page hero shows both).
- ❌ No platform/export or self-promo boilerplate: "Agent Instructions", "published with GitBook",
  "Querying This Documentation", `llms.txt`, "Thanks to … for creating", "buying me a coffee".
- ❌ No `source:` frontmatter line.
- ❌ No un-redacted machine IPs.

## Adding a writeup

1. Create `htb/machines/<difficulty>/<slug>.md` (or under `ctf/` / `bugbounty/`) with the
   minimal frontmatter above and the narrative sections.
2. Put any screenshots in `assets/wu/<slug>/`.
3. Push. CI validates it against this guide; the enrich Action fills metadata + the manifest,
   and the site shows it automatically.

## Attribution

Adapted sources are credited in [`README.md`](README.md) (with their licenses) — never inside
individual writeups.
