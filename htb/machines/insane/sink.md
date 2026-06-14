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

## Enumeration

I started by enumerating the exposed web stack and found a HAProxy frontend sitting in front of a Gunicorn backend serving the web application. The combination of these two components is significant: HAProxy and Gunicorn have known desync issues when the `Content-Length` and `Transfer-Encoding` headers conflict, which is exactly the kind of architecture that invites HTTP request smuggling.

## Foothold

The way in came from an HTTP request smuggling attack against the proxy/backend pair. By crafting a CL.TE desync between HAProxy and Gunicorn, I was able to smuggle requests through the frontend and capture admin session cookies from other in-flight requests.

With the hijacked session cookie I authenticated into the admin panel. From there I discovered Gitea credentials, which opened up the next stage of the chain. Enumerating the Gitea repositories, I dug through the commit history and recovered AWS access keys and secrets that had been committed into version control — even in a private repo, the git history still leaked them.

## Privilege Escalation

The recovered AWS credentials gave me a foothold into the cloud account. I used them to enumerate and list secrets in AWS Secrets Manager, then retrieved the stored secret material. Several of these secrets were encrypted, so I leaned on the AWS Key Management Service (KMS) to decrypt them.

Chaining the AWS services together (IAM credentials leading to Secrets Manager, then to KMS) yielded decrypted credentials that ultimately provided root access on the box.
