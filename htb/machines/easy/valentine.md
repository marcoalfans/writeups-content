---
title: "Valentine"
difficulty: Easy
os: Linux
points: 20
rating: 4.8
date: 2018-02-17
avatar: assets/htb/valentine.png
tags: [Weak Permissions, Web Site Structure Discovery, SSL, Web Application, Vulnerability Assessment, Session Management and Hijacking, Software & OS exploitation]
htb_url: https://app.hackthebox.com/machines/Valentine
---
# Valentine

🔗 [Valentine](https://www.hackthebox.com/machines/Valentine)

### Task 1 - Deploy the machine

🎯 Target IP: `<YOUR_IP>`

On the Desktop, set up a folder named after the machine, and within it add a sub-folder to hold all the assets and output produced during the engagement, such as the nmap scans.

### Task 2 - Reconnaissance

<pre class="language-bash"><code class="lang-bash">su
<strong>echo "<YOUR_IP> valentine.htb" >> /etc/hosts
</strong>
mkdir -p htb/valentine.htb
cd htb/valentine.htb
mkdir {nmap,content,exploits,scripts}
# At the end of the room
# To clean up the last line from the /etc/hosts file
<strong>sed -i '$ d' /etc/hosts
</strong></code></pre>

My usual first move is to ping the host, which confirms connectivity and hints at the operating system.

```bash
ping -c 3 valentine.htb
PING valentine.htb (<YOUR_IP>) 56(84) bytes of data.
64 bytes from valentine.htb (<YOUR_IP>): icmp_seq=1 ttl=63 time=61.0 ms
64 bytes from valentine.htb (<YOUR_IP>): icmp_seq=2 ttl=63 time=59.5 ms
64 bytes from valentine.htb (<YOUR_IP>): icmp_seq=3 ttl=63 time=60.0 ms
```

The three ICMP replies show a TTL close to 64, which points to a \*nix host. Windows boxes typically report a TTL around 128.

### 2.1 - How many TCP ports are open on the remote host?

```bash
nmap -p0- -sS -Pn -vvv valentine.htb -oN nmap/tcp_port_scan
```

```bash
PORT    STATE SERVICE REASON
22/tcp  open  ssh     syn-ack ttl 63
80/tcp  open  http    syn-ack ttl 63
443/tcp open  https   syn-ack ttl 63
```

<table><thead><tr><th width="154.99999999999997">command</th><th>result</th></tr></thead><tbody><tr><td>sS</td><td>SynScan</td></tr><tr><td>sC</td><td>run default scripts</td></tr><tr><td>sV</td><td>enumerate versions</td></tr><tr><td>A</td><td>aggressive mode</td></tr><tr><td>T4</td><td>run a bit faster</td></tr><tr><td>oN</td><td>output to file with nmap formatting</td></tr></tbody></table>

The scan reveals 3 open TCP ports on the host: 22, 80, 443.

3

### 2.2 - Which flag is used with nmap to execute its vulnerability discovery scripts (with the category "vuln") on the target??

Next we run a more targeted scan with the -sCV flags to grab service versions and run the standard scripts.

```bash
nmap -p22,80,443 -sS -Pn -n -v -sCV --script vuln -T4 valentine.htb -oN nmap/port_scan
```

```
PORT    STATE    SERVICE   VERSION
22/tcp  filtered ssh
80/tcp  open     http      Apache httpd 2.2.22 ((Ubuntu))
|_http-server-header: Apache/2.2.22 (Ubuntu)
| http-methods: 
|_  Supported Methods: GET HEAD POST OPTIONS
|_http-title: Site doesn't have a title (text/html).
443/tcp open     ssl/https Apache/2.2.22 (Ubuntu)
| http-methods: 
|_  Supported Methods: GET HEAD POST OPTIONS
|_http-server-header: Apache/2.2.22 (Ubuntu)
|_http-title: Site doesn't have a title (text/html).
| ssl-cert: Subject: commonName=valentine.htb/organizationName=valentine.htb/stateOrProvinceName=FL/countryName=US
| Issuer: commonName=valentine.htb/organizationName=valentine.htb/stateOrProvinceName=FL/countryName=US
| Public Key type: rsa
| Public Key bits: 2048
| Signature Algorithm: sha1WithRSAEncryption
| Not valid before: 2018-02-06T00:45:25
| Not valid after:  2019-02-06T00:45:25
| MD5:   a413:c4f0:b145:2154:fb54:b2de:c7a9:809d
|_SHA-1: 2303:80da:60e7:bde7:2ba6:76dd:5214:3c3c:6f53:01b1
|_ssl-date: 2024-07-14T09:44:55+00:00; 0s from scanner time.
```

With no SSH credentials in hand, our starting point will be the web services on ports 80 and 443.

#### Port 80 and 443

Browsing the site turns up nothing notable, so we run whatweb and a gobuster directory scan against each of the ports.

```bash
whatweb valentine.htb
http://valentine.htb [200 OK] Apache[2.2.22], Country[RESERVED][ZZ], HTTPServer[Ubuntu Linux][Apache/2.2.22 (Ubuntu)], IP[<YOUR_IP>], PHP[5.3.10-1ubuntu3.26], X-Powered-By[PHP/5.3.10-1ubuntu3.26]
```

```bash
gobuster dir -u http://valentine.htb -w /usr/share/wordlists/dirb/common.txt
```

A few interesting directories show up, which I'll come back to later.

This question isn't about the box itself; it's a general one about nmap's options.

\--script vuln

### 2.3 - What is the 2014 CVE ID for an information disclosure vulnerability that the service on port 443 is vulnerable to?

These questions, along with the earlier one, point toward running the `--script vuln` flag against port 443. A quick search surfaces likely vulnerabilities, and we then look for one tied to the machine's theme (Valentine) and the image shown on the index page.

nmap ships with a dedicated script for checking the Heartbleed vulnerability:

```bash
nmap -p443 -Pn --script ssl-heartbleed -T4 valentine.htb -oN nmap/vuln
```

```bash
PORT    STATE SERVICE
443/tcp open  https
| ssl-heartbleed: 
|   VULNERABLE:
|   The Heartbleed Bug is a serious vulnerability in the popular OpenSSL cryptographic software library. It allows for stealing information intended to be protected by SSL/TLS encryption.
|     State: VULNERABLE
|     Risk factor: High
|       OpenSSL versions 1.0.1 and 1.0.2-beta releases (including 1.0.1f and 1.0.2-beta1) of OpenSSL are affected by the Heartbleed bug. The bug allows for reading memory of systems protected by the vulnerable OpenSSL versions and could allow for disclosure of otherwise encrypted confidential information as well as the encryption keys themselves.
|           
|     References:
|       https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2014-0160
|       http://www.openssl.org/news/secadv_20140407.txt 
|_      http://cvedetails.com/cve/2014-0160/
```

CVE-2014-0160

### 2.4 -  What password can be leaked using (CVE-2014-0160)?

A PoC and working exploit for the flaw live in this github repo:

With that exploit, pulling sensitive data out of memory is quite easy. Run it a handful of times and a base64-encoded string eventually appears.

Here, we opt to exploit it through the metasploit module built for this vulnerability:

The `spool memory_leak.txt` command saves the output locally, and repeated runs let us observe different chunks of memory.

Doing so surfaces this notable string:&#x20;

```
$text=aGVhcnRibGVlZGJlbGlldmV0aGVoeXBlCg==
```

that is a base64 string.

heartbleedbelievethehype

### 2.5 - What is the relative path of a folder on the website that contains two interesting files, including note.txt?

Visiting the 'hidden' web directory gobuster found, /dev, we spot two files worth a look:

notes.txt

hype\_key

/dev

### 2.6 -  What is the filename of the RSA key found on the website?

hype\_key

hype\_key

### Task 3 - Find user flag

### 3.1 - Submit the flag located in the hype user's home directory.

We can decode hype\_key from hex into ASCII

which gives us an encrypted RSA private key (likely an id\_rsa for SSH access), which we save as id\_rsa\_psw.

Since we already have a candidate password, heartbleedbelievethehype, we can attempt to decrypt it:

`openssl rsa -in id_rsa_psw`

`ssh hype@valentine.htb -i id_rsa`

<details>

<summary>🚩 Flag 1 (user.txt)</summary>

5d03************************97b9

</details>

### 3.2 - What is the name of the terminal multiplexing software that the hype user has run previously?

tmux

### 3.3 - What is the full path to the socket file used by the tmux session?

/.devs/dev\_sess

### 3.4 - What user is that tmux session running as?

root

### Task 4 - Find root flag

### 4.1 - Submit the flag located in root's home directory.

<details>

<summary>🚩 Flag 2 (root.txt)</summary>

2ec3************************a477

</details>

---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://dev-angelist.gitbook.io/writeups-and-walkthroughs/hackthebox/valentine.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
