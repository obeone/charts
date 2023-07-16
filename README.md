# Helm charts

[![Artifact Hub](https://img.shields.io/endpoint?url=https://artifacthub.io/badge/repository/obeone)](https://artifacthub.io/packages/search?repo=obeone)

To use this repository :

```console
helm repo add obeone https://charts.obeone.cloud
helm repo update
```

All charts are [signed](https://helm.sh/docs/topics/provenance/). You can checked using key [B9FE852F28888D27F8C9A11CD33E04CD22E335CE](public_key.gpg)

## Winbox

Mikrotik Winbox in browser [[Sources]](https://github.com/obeone/winbox-docker) [[Chart]](charts/winbox)

## CyberChef

CyberChef, The Cyber Swiss Army Knife [[Demo]](https://gchq.github.io/cyberchef) [[Sources]](https://github.com/gchq/CyberChef) [[Chart]](charts/cyberchef)

## MKTXP

A Prometheus metrics exporter for Mikrotik's RouterOS
[[Sources]](https://github.com/akpw/mktxp) [[Chart]](charts/mktxp)

## DNSCrypt proxy

A flexible DNS proxy, with support for encrypted DNS protocols. [[Sources]](https://github.com/klutchell/dnscrypt-proxy-docker) [[Chart]](charts/dnscrypt-proxy)

## Technitium DNSServer

Technitium DNS Server is a DNS that can be use as a piHole or AdGuardHome replacement. It can also be used as authoritative server
[[Sources]](https://github.com/TechnitiumSoftware/DnsServer) [[Chart]](charts/technitium-dnsserver)

## NFS Server

A lightweight, robust, flexible, and containerized NFS server.
[[Sources]](https://github.com/obeone/docker-nfs-server) [[Chart]](charts/nfs-server)
