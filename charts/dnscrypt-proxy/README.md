# DNSCrypt Proxy Helm Chart

![Version: 1.3.1](https://img.shields.io/badge/Version-1.3.1-informational?style=flat-square) ![AppVersion: 2.1.12](https://img.shields.io/badge/AppVersion-2.1.12-informational?style=flat-square) ![Type: application](https://img.shields.io/badge/Type-application-informational?style=flat-square) [![Artifact Hub](https://img.shields.io/endpoint?url=https://artifacthub.io/badge/repository/obeone)](https://artifacthub.io/packages/helm/obeone/dnscrypt-proxy)

## What is DNSCrypt Proxy?

DNSCrypt Proxy is a flexible DNS proxy with support for modern encrypted DNS protocols such as [DNSCrypt v2](https://dnscrypt.info/protocol) and [DNS-over-HTTPS](https://www.rfc-editor.org/rfc/rfc8484.txt).

**Key Features:**

- 🔒 **Enhanced Privacy**: Encrypts DNS queries to prevent eavesdropping and tampering
- 🚫 **Filtering Capabilities**: Optional blocking of ads, malware domains, and tracking
- 🌐 **Wide Resolver Support**: Works with a large selection of public DNS resolvers
- ⚡ **High Performance**: Lightweight and efficient with minimal overhead
- 🔄 **Flexible Configuration**: Extensive options for customizing your DNS setup

## TL;DR

```bash
helm repo add obeone https://obeone.github.io/charts/
helm install dnscrypt-proxy obeone/dnscrypt-proxy
```

## Introduction

This chart bootstraps a [DNSCrypt Proxy](https://github.com/DNSCrypt/dnscrypt-proxy) deployment on a Kubernetes cluster using the Helm package manager.

It leverages the [klutchell/dnscrypt-proxy](https://github.com/klutchell/dnscrypt-proxy-docker) Docker image to provide a secure and private DNS resolver for your Kubernetes applications.

## Prerequisites

- Kubernetes 1.16+
- Helm 3.0+

## Installing the Chart

To install the chart with the release name `dnscrypt-proxy`:

```bash
helm install dnscrypt-proxy obeone/dnscrypt-proxy
```

The command deploys DNSCrypt Proxy on the Kubernetes cluster with default configuration. The [Parameters](#parameters) section lists the parameters that can be configured during installation.

## Uninstalling the Chart

To uninstall/delete the `dnscrypt-proxy` deployment:

```bash
helm uninstall dnscrypt-proxy
```

## Configuration

### Example Configuration

Below is an example of a custom `values.yaml` file:

```yaml
# Enable configuration via ConfigMap
configmap:
  config:
    enabled: true
    data:
      dnscrypt-proxy.toml: |
        listen_addresses = ['0.0.0.0:5353']
        log_level = 2
        
        ipv4_servers = true
        ipv6_servers = false
        dnscrypt_servers = true
        doh_servers = true
        odoh_servers = false
        
        require_nolog = true
        require_nofilter = false
        
        # Use Cloudflare and Quad9 as bootstrap resolvers
        bootstrap_resolvers = ['1.1.1.1:53', '9.9.9.9:53']
        
        # Load balance strategy (p2=2 fastest resolvers)
        lb_strategy = 'p2'
        
        # Block malware domains
        blocked_names_file = '/data/blocked-names.txt'
        
        [sources]
          [sources.public-resolvers]
            urls = ['https://raw.githubusercontent.com/DNSCrypt/dnscrypt-resolvers/master/v3/public-resolvers.md']
            cache_file = '/data/public-resolvers.md'
            minisign_key = 'RWQf6LRCGA9i53mlYecO4IzT51TGPpvWucNSCh1CBM0QTaLn73Y7GFO3'
            refresh_delay = 24
            prefix = ''

# Enable persistence for caching and configuration
persistence:
  data:
    enabled: true
    mountPath: /data
    size: 1Gi

# Set timezone
env:
  TZ: "Europe/Paris"
```

### DNS Service Configuration

The chart creates two services by default:
- `dns-udp`: For UDP DNS traffic on port 53
- `dns-tcp`: For TCP DNS traffic on port 53

Both services target port 5353 on the container, which is the default port for DNSCrypt Proxy.

## Parameters

### Common Parameters

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| image.repository | string | `"klutchell/dnscrypt-proxy"` | Image repository |
| image.tag | string | chart.appVersion | Image tag. Use "main" if you want to be able to use DNS probes |
| image.pullPolicy | string | `"IfNotPresent"` | Image pull policy. Set to Always if you used "main" as tag |
| env | object | See below | Environment variables |
| env.TZ | string | `"UTC"` | Container timezone |
| controller.replicas | int | `1` | Number of replicas |

### DNSCrypt Configuration

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| configmap.config.enabled | bool | `false` | Enable the ConfigMap for DNSCrypt configuration |
| configmap.config.data."dnscrypt-proxy.toml" | string | See values.yaml | DNSCrypt configuration file content |

### Service Configuration

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| service.dns-udp.enabled | bool | `true` | Enable UDP DNS service |
| service.dns-udp.type | string | `"ClusterIP"` | UDP service type |
| service.dns-udp.ports.dns-udp.port | int | `53` | UDP service port |
| service.dns-tcp.enabled | bool | `true` | Enable TCP DNS service |
| service.dns-tcp.type | string | `"ClusterIP"` | TCP service type |
| service.dns-tcp.ports.dns-tcp.port | int | `53` | TCP service port |

### Persistence Configuration

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| persistence | object | `{}` | Configure persistence settings |

### Probe Configuration

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| probes.liveness.custom | bool | `true` | Enable custom liveness probe |
| probes.readiness.custom | bool | `true` | Enable custom readiness probe |
| probes.startup.custom | bool | `true` | Enable custom startup probe |

## Why Use DNSCrypt?

### Privacy Benefits

Standard DNS queries are sent in plaintext, which means:
- Your ISP can see and log all websites you visit
- Network attackers can intercept and modify DNS responses
- Your browsing habits can be tracked and profiled

DNSCrypt encrypts all DNS traffic between your applications and the DNS resolver, preventing surveillance and tampering.

### Security Advantages

- **Protection against DNS spoofing**: Ensures you connect to legitimate websites
- **Resistance to censorship**: Makes it harder for networks to block access to websites
- **Malware protection**: Many DNSCrypt resolvers offer built-in filtering of malicious domains

## Troubleshooting

### Checking Logs

```bash
kubectl logs -l app.kubernetes.io/name=dnscrypt-proxy
```

### Testing DNS Resolution

```bash
kubectl run -it --rm debug --image=busybox -- nslookup google.com <service-name>.<namespace>.svc.cluster.local
```

## Source Code

* <https://github.com/DNSCrypt/dnscrypt-proxy>
* <https://github.com/klutchell/dnscrypt-proxy-docker>
* <https://github.com/obeone/charts/>

## Requirements

| Repository | Name | Version |
|------------|------|---------|
| https://library-charts.k8s-at-home.com | common | 4.5.2 |

## Maintainers

| Name | Email | Url |
| ---- | ------ | --- |
| obeone | <obeone@obeone.org> |  |

----------------------------------------------
Autogenerated from chart metadata using [helm-docs v1.14.2](https://github.com/norwoodj/helm-docs/releases/v1.14.2)
