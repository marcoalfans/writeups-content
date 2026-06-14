---
title: "Sink"
difficulty: Insane
os: Linux
points: 50
rating: 4.9
date: 2021-01-30
avatar: assets/htb/sink.png
tags: [Information Disclosure, Misconfiguration, HTTP request smuggling, AWS Enumeration, Analysis of Logs, Password Reuse, Cookie Manipulation, HTTP Desync]
htb_url: https://app.hackthebox.com/machines/Sink
---
## Summary

Sink is an Insane Linux machine featuring HTTP request smuggling through a HAProxy/Gunicorn desync to hijack admin sessions, followed by exploitation of a Gitea instance containing AWS secrets. Privilege escalation involves abusing AWS Secrets Manager and KMS to decrypt sensitive credentials.

---

## External Writeup

- [Full Writeup by 0xMMN](https://0xmmn.blogspot.com/2023/09/hackthebox-sink-machine-insane.html)

---

## Key Techniques

- HTTP Request Smuggling (CL.TE desync)
- HAProxy / Gunicorn misconfiguration
- Session hijacking via smuggled requests
- Gitea repository enumeration
- AWS Secrets Manager enumeration
- AWS KMS key decryption
- Cloud credential chaining

---

## Attack Path Overview

1. **Enumeration** - Discover HAProxy fronting a Gunicorn backend with a web application
2. **HTTP Request Smuggling** - Exploit CL.TE desync between HAProxy and Gunicorn to smuggle requests and steal admin session cookies
3. **Admin Access** - Use hijacked session to access admin panel, discover Gitea credentials
4. **Gitea Exploitation** - Enumerate Gitea repositories, find AWS access keys and secrets in commit history
5. **AWS Secrets Manager** - Use discovered AWS credentials to list and retrieve secrets from AWS Secrets Manager
6. **AWS KMS** - Decrypt encrypted secrets using AWS Key Management Service
7. **Root** - Use decrypted credentials for root access

---

## Lessons Learned

- HTTP request smuggling remains a critical vulnerability in proxy/backend architectures
- Secrets stored in version control (even private repos) can be extracted from git history
- AWS credential chains across services (IAM -> Secrets Manager -> KMS) can lead to full compromise
- HAProxy and Gunicorn have known desync issues when Content-Length and Transfer-Encoding headers conflict
