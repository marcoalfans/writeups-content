---
title: "Chemistry"
difficulty: Easy
---

# Chemistry %

🔗 [Cap](https://www.hackthebox.com/machines/cap)

<details>

<summary>About</summary>

</details>

## Task 0 - Deploy machine

🎯 Target IP: `<YOUR_IP>`

Create a directory on the Desktop with the machine's name, and inside this directory, create another directory to store the materials and outputs needed to run the machine, including the scans made with nmap.

## Task 1 - Reconnaissance

<pre class="language-bash"><code class="lang-bash">su
<strong>echo "<YOUR_IP> cap.htb" >> /etc/hosts
</strong>
mkdir -p htb/cap.htb
cd htb/cap.htb
mkdir {nmap,content,exploits,scripts}
# At the end of the room
# To clean up the last line from the /etc/hosts file
<strong>sed -i '$ d' /etc/hosts
</strong></code></pre>

My usual first recon step is to ping the target, which confirms we can reach it and hints at the underlying OS.

```bash
ping -c 3 cap.htb
PING cap.htb (<YOUR_IP>) 56(84) bytes of data.
64 bytes from cap.htb (<YOUR_IP>): icmp_seq=6 ttl=63 time=77.8 ms
64 bytes from cap.htb (<YOUR_IP>): icmp_seq=9 ttl=63 time=80.1 ms
64 bytes from cap.htb (<YOUR_IP>): icmp_seq=11 ttl=63 time=51.5 ms
```

These three ICMP replies come back with a TTL near 64, which points to a **\*nix** host; Windows machines typically respond with a TTL around 128.

### 1.1 - How many TCP ports are open?

Let's jump straight into an active nmap port scan.

```bash
sudo nmap -p0- -sS -Pn -T4 -vvv cap.htb -oN nmap/tcp_port_scan
```

```bash
PORT   STATE SERVICE REASON
21/tcp open  ftp     syn-ack ttl 63
22/tcp open  ssh     syn-ack ttl 63
80/tcp open  http    syn-ack ttl 63
```

<table><thead><tr><th width="154.99999999999997">command</th><th>result</th></tr></thead><tbody><tr><td>sT</td><td>TCP connect port scan (Default without root privilege)</td></tr><tr><td>sC</td><td>Run default scripts</td></tr><tr><td>sV</td><td>Enumerate versions</td></tr><tr><td>vvv</td><td>Verbosity</td></tr><tr><td>T4</td><td>Run a bit faster</td></tr><tr><td>oN</td><td>Output to file with nmap formatting</td></tr></tbody></table>

The scan reveals 3 open TCP ports on the host: 21, 22, 80.

3

Next, let's enumerate the services running behind those open ports:

```bash
sudo nmap -sV -sC -p 21,22,80 cap.htb -oN nmap/service_port_scan
```

```bash
PORT   STATE SERVICE VERSION
21/tcp open  ftp     vsftpd 3.0.3
22/tcp open  ssh     OpenSSH 8.2p1 Ubuntu 4ubuntu0.2 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   3072 fa:80:a9:b2:ca:3b:88:69:a4:28:9e:39:0d:27:d5:75 (RSA)
|   256 96:d8:f8:e3:e8:f7:71:36:c5:49:d5:9d:b6:a4:c9:0c (ECDSA)
|_  256 3f:d0:ff:91:eb:3b:f6:e1:9f:2e:8d:de:b3:de:b2:18 (ED25519)
80/tcp open  http    gunicorn
|_http-server-header: gunicorn
|_http-title: Security Dashboard
| fingerprint-strings: 
|   FourOhFourRequest: 
|     HTTP/1.0 404 NOT FOUND
|     Server: gunicorn
|     Date: Thu, 02 Jan 2025 11:42:26 GMT
|     Connection: close
|     Content-Type: text/html; charset=utf-8
|     Content-Length: 232
|     <!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">
|     <title>404 Not Found</title>
|     <h1>Not Found</h1>
|     <p>The requested URL was not found on the server. If you entered the URL manually please check your spelling and try again.</p>
|   GetRequest: 
|     HTTP/1.0 200 OK
|     Server: gunicorn
|     Date: Thu, 02 Jan 2025 11:42:21 GMT
|     Connection: close
|     Content-Type: text/html; charset=utf-8
|     Content-Length: 19386
|     <!DOCTYPE html>
|     <html class="no-js" lang="en">
|     <head>
|     <meta charset="utf-8">
|     <meta http-equiv="x-ua-compatible" content="ie=edge">
|     <title>Security Dashboard</title>
|     <meta name="viewport" content="width=device-width, initial-scale=1">
|     <link rel="shortcut icon" type="image/png" href="/static/images/icon/favicon.ico">
|     <link rel="stylesheet" href="/static/css/bootstrap.min.css">
|     <link rel="stylesheet" href="/static/css/font-awesome.min.css">
|     <link rel="stylesheet" href="/static/css/themify-icons.css">
|     <link rel="stylesheet" href="/static/css/metisMenu.css">
|     <link rel="stylesheet" href="/static/css/owl.carousel.min.css">
|     <link rel="stylesheet" href="/static/css/slicknav.min.css">
|     <!-- amchar
|   HTTPOptions: 
|     HTTP/1.0 200 OK
|     Server: gunicorn
|     Date: Thu, 02 Jan 2025 11:42:21 GMT
|     Connection: close
|     Content-Type: text/html; charset=utf-8
|     Allow: OPTIONS, GET, HEAD
|     Content-Length: 0
|   RTSPRequest: 
|     HTTP/1.1 400 Bad Request
|     Connection: close
|     Content-Type: text/html
|     Content-Length: 196
|     <html>
|     <head>
|     <title>Bad Request</title>
|     </head>
|     <body>
|     <h1><p>Bad Request</p></h1>
|     Invalid HTTP Version &#x27;Invalid HTTP Version: &#x27;RTSP/1.0&#x27;&#x27;
|     </body>
|_    </html>
1 service unrecognized despite returning data. If you know the service/version, please submit the following fingerprint at https://nmap.org/cgi-bin/submit.cgi?new-service :
SF-Port80-TCP:V=7.94SVN%I=7%D=1/2%Time=67767B84%P=x86_64-pc-linux-gnu%r(Ge
SF:tRequest,1FBC,"HTTP/1\.0\x20200\x20OK\r\nServer:\x20gunicorn\r\nDate:\x
SF:20Thu,\x2002\x20Jan\x202025\x2011:42:21\x20GMT\r\nConnection:\x20close\
SF:r\nContent-Type:\x20text/html;\x20charset=utf-8\r\nContent-Length:\x201
SF:9386\r\n\r\n<!DOCTYPE\x20html>\n<html\x20class=\"no-js\"\x20lang=\"en\"
SF:>\n\n<head>\n\x20\x20\x20\x20<meta\x20charset=\"utf-8\">\n\x20\x20\x20\
SF:x20<meta\x20http-equiv=\"x-ua-compatible\"\x20content=\"ie=edge\">\n\x2
SF:0\x20\x20\x20<title>Security\x20Dashboard</title>\n\x20\x20\x20\x20<met
SF:a\x20name=\"viewport\"\x20content=\"width=device-width,\x20initial-scal
SF:e=1\">\n\x20\x20\x20\x20<link\x20rel=\"shortcut\x20icon\"\x20type=\"ima
SF:ge/png\"\x20href=\"/static/images/icon/favicon\.ico\">\n\x20\x20\x20\x2
SF:0<link\x20rel=\"stylesheet\"\x20href=\"/static/css/bootstrap\.min\.css\
SF:">\n\x20\x20\x20\x20<link\x20rel=\"stylesheet\"\x20href=\"/static/css/f
SF:ont-awesome\.min\.css\">\n\x20\x20\x20\x20<link\x20rel=\"stylesheet\"\x
SF:20href=\"/static/css/themify-icons\.css\">\n\x20\x20\x20\x20<link\x20re
SF:l=\"stylesheet\"\x20href=\"/static/css/metisMenu\.css\">\n\x20\x20\x20\
SF:x20<link\x20rel=\"stylesheet\"\x20href=\"/static/css/owl\.carousel\.min
SF:\.css\">\n\x20\x20\x20\x20<link\x20rel=\"stylesheet\"\x20href=\"/static
SF:/css/slicknav\.min\.css\">\n\x20\x20\x20\x20<!--\x20amchar")%r(HTTPOpti
SF:ons,B3,"HTTP/1\.0\x20200\x20OK\r\nServer:\x20gunicorn\r\nDate:\x20Thu,\
SF:x2002\x20Jan\x202025\x2011:42:21\x20GMT\r\nConnection:\x20close\r\nCont
SF:ent-Type:\x20text/html;\x20charset=utf-8\r\nAllow:\x20OPTIONS,\x20GET,\
SF:x20HEAD\r\nContent-Length:\x200\r\n\r\n")%r(RTSPRequest,121,"HTTP/1\.1\
SF:x20400\x20Bad\x20Request\r\nConnection:\x20close\r\nContent-Type:\x20te
SF:xt/html\r\nContent-Length:\x20196\r\n\r\n<html>\n\x20\x20<head>\n\x20\x
SF:20\x20\x20<title>Bad\x20Request</title>\n\x20\x20</head>\n\x20\x20<body
SF:>\n\x20\x20\x20\x20<h1><p>Bad\x20Request</p></h1>\n\x20\x20\x20\x20Inva
SF:lid\x20HTTP\x20Version\x20&#x27;Invalid\x20HTTP\x20Version:\x20&#x27;RT
SF:SP/1\.0&#x27;&#x27;\n\x20\x20</body>\n</html>\n")%r(FourOhFourRequest,1
SF:89,"HTTP/1\.0\x20404\x20NOT\x20FOUND\r\nServer:\x20gunicorn\r\nDate:\x2
SF:0Thu,\x2002\x20Jan\x202025\x2011:42:26\x20GMT\r\nConnection:\x20close\r
SF:\nContent-Type:\x20text/html;\x20charset=utf-8\r\nContent-Length:\x2023
SF:2\r\n\r\n<!DOCTYPE\x20HTML\x20PUBLIC\x20\"-//W3C//DTD\x20HTML\x203\.2\x
SF:20Final//EN\">\n<title>404\x20Not\x20Found</title>\n<h1>Not\x20Found</h
SF:1>\n<p>The\x20requested\x20URL\x20was\x20not\x20found\x20on\x20the\x20s
SF:erver\.\x20If\x20you\x20entered\x20the\x20URL\x20manually\x20please\x20
SF:check\x20your\x20spelling\x20and\x20try\x20again\.</p>\n");
Service Info: OSs: Unix, Linux; CPE: cpe:/o:linux:linux_kernel
```

Beyond confirming the 'Gunicorn' web server, which I already knew about, whatweb doesn't reveal much else.

```bash
whatweb cap.htb
http://cap.htb [200 OK] Bootstrap, Country[RESERVED][ZZ], HTML5, HTTPServer[gunicorn], IP[<YOUR_IP>], JQuery[2.2.4], Modernizr[2.8.3.min], Script, Title[Security Dashboard], X-UA-Compatible[ie=edge]
```

To map out the target's scope, let's open the web server in a browser:

The page is a security-events dashboard showing failed logins and similar metrics. The 'Security Snapshot' section offers a packet sniffer with a counter and lets us download the captured traffic.

Under 'IP Config' we can view the network interface of the attacker machine `<YOUR_IP>`

The 'Network Status' section lists all the current connections:

Lastly, the 'user tab' in the top-right is just a non-functional mockup, but the name 'Nathan' is worth keeping in mind, it could come in handy for the SSH and FTP services.

Running GoBuster for directory enumeration and reviewing the page source turns up nothing else of interest.

```bash
gobuster dir -u http://cap.htb -w /usr/share/wordlists/dirb/common.txt
```

### 1.2 - After running a "Security Snapshot", the browser is redirected to a path of the format /\[something]/\[id], where \[id] represents the id number of the scan. What is the \[something]?

That redirect is a useful clue for our next move, so let's generate some ICMP traffic and see whether it gets captured.

It does, and we can answer the question simply by looking at the url path.

data

## Task 2 - Exploitation & User Flag

### 2.1 - Are you able to get to other users' scans?

Running ffuf against a wordlist of common usernames returned nothing useful.

What stands out in the Security Snapshot is the URL pattern when a new capture is created, of the form /data/ , where the id increments with each capture.

Tampering with that parameter revealed an Insecure Direct Object Reference (IDOR) vulnerability, a flaw that lets an attacker reach or alter objects by manipulating the identifiers used in a web page.

This implies the server keeps the most recent scans, including packet captures from earlier users. Starting from /data/1, browsing to /data/0 does indeed expose a packet capture containing multiple packets.

So we can confirm that reaching other users' scans is possible, which answers the question.

yes

### 2.2 - What is the ID of the PCAP file that contains sensative data?

We can now open the pcap file (which is named after the machine) and inspect the traffic in Wireshark, hunting for ftp, http, or other cleartext sensitive data.

Right away we spot a successful FTP login by the earlier-mentioned user 'Nathan', with the password in plaintext.

0

### 2.3 - Which application layer protocol in the pcap file can the sensitive data be found in?

The sensitive data lives in the FTP protocol; below is the full TCP Stream:

With the FTP credentials in hand, we'll also try reusing them against SSH.

ftp

### 2.4 - We've managed to collect nathan's FTP password. On what other service does this password work?

As anticipated, let's test the credentials against both the FTP and SSH services.

#### FTP/21

`ftp nathan@cap.htb`

#### SSH/22

The credentials work on both services ;)

SSH

2.5 - Submit the flag located in the nathan user's home directory.

Having already noticed interesting files in the previous task, let's go ahead and grab the user flag from Nathan's directory.

\

<details>

<summary>🚩 Flag 1 (user.txt)</summary>

f17c************************c401

</details>

## Task 3 - Privilege Escalation & Root Flag

### 3.1 - What is the full path to the binary on this machine has special capabilities that can be abused to obtain root privileges?

Running `sudo -l`, we find no commands that Nathan is allowed to run with sudo privileges:

Rather than starting with automated tooling like Linpeas, and bearing the question's hint in mind, let's run a few targeted commands:

```bash
crontab -l
cat /proc/version
getcap -r /2>/dev/null
```

Checking cronjobs, the kernel version, and [capabilities](https://man7.org/linux/man-pages/man7/capabilities.7.html), the only promising result comes from the linux capabilities, so let's pursue that!&#x20;

Looking at the first line of that output, `/usr/bin/python3.8 = cap_setuid,cap_net_bind_service+eip`, we notice '[cap\_setuid](https://man7.org/linux/man-pages/man2/setuid.2.html)', meaning the python interpreter can elevate privileges.&#x20;

/usr/bin/python3.8

### 3.2 - Submit the flag located in root's home directory.

The plan is to set our uid to 0 (the root user), so let's do that.

We can change it right on the target by running OS commands through the python3.8 interpreter: `usr/bin/python3.8`

```python
import os
os.setuid(0)
os.system("/bin/bash")
```

once the uid is set to 0 we gain root privileges!

To finish, we head into the root directory and read the root.txt flag: `cat /root/root.txt`

<details>

<summary>🚩 Flag 2 (root.txt)</summary>

751f************************f9b7

</details>

---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://dev-angelist.gitbook.io/writeups-and-walkthroughs/hackthebox/chemistry.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
