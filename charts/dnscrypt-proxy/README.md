# dnscrypt-proxy

![Version: 1.2.0](https://img.shields.io/badge/Version-1.2.0-informational?style=flat-square) ![AppVersion: 2.1.7](https://img.shields.io/badge/AppVersion-2.1.7-informational?style=flat-square)

A flexible DNS proxy, with support for encrypted DNS protocols.

**Homepage:** <https://github.com/DNSCrypt/dnscrypt-proxy>

## Maintainers

| Name | Email | Url |
| ---- | ------ | --- |
| obeone | <obeone@obeone.org> |  |

## Source Code

* <https://github.com/klutchell/dnscrypt-proxy-docker>
* <https://github.com/obeone/charts/>

## Requirements

Kubernetes: `>=1.16.0-0`

| Repository | Name | Version |
|------------|------|---------|
| https://library-charts.k8s-at-home.com | common | 4.5.2 |

## Values

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| configmap | object | See below | Configure configMaps for the chart here. Additional configMaps can be added by adding a dictionary key similar to the 'config' object. |
| configmap.config.annotations | object | `{}` | Annotations to add to the configMap |
| configmap.config.data | object | `{"dnscrypt-proxy.toml":"listen_addresses = ['0.0.0.0:5353']\nlog_level = 1\n\nipv4_servers = true\nipv6_servers = false\ndnscrypt_servers = true\ndoh_servers = false\nodoh_servers = false\nbootstrap_resolvers = ['9.9.9.11:53', '8.8.8.8:53']\nlb_strategy = 'p2'\n\nrequire_nolog = true\nrequire_nofilter = true\n\n[sources]\n  [sources.public-resolvers]\n    urls = ['https://raw.githubusercontent.com/DNSCrypt/dnscrypt-resolvers/master/v3/public-resolvers.md', 'https://download.dnscrypt.info/resolvers-list/v3/public-resolvers.md', 'https://ipv6.download.dnscrypt.info/resolvers-list/v3/public-resolvers.md']\n    cache_file = 'public-resolvers.md'\n    minisign_key = 'RWQf6LRCGA9i53mlYecO4IzT51TGPpvWucNSCh1CBM0QTaLn73Y7GFO3'\n    refresh_delay = 72\n    prefix = ''\n"}` | configMap data content. Helm template enabled. |
| configmap.config.data."dnscrypt-proxy.toml" | string | `"listen_addresses = ['0.0.0.0:5353']\nlog_level = 1\n\nipv4_servers = true\nipv6_servers = false\ndnscrypt_servers = true\ndoh_servers = false\nodoh_servers = false\nbootstrap_resolvers = ['9.9.9.11:53', '8.8.8.8:53']\nlb_strategy = 'p2'\n\nrequire_nolog = true\nrequire_nofilter = true\n\n[sources]\n  [sources.public-resolvers]\n    urls = ['https://raw.githubusercontent.com/DNSCrypt/dnscrypt-resolvers/master/v3/public-resolvers.md', 'https://download.dnscrypt.info/resolvers-list/v3/public-resolvers.md', 'https://ipv6.download.dnscrypt.info/resolvers-list/v3/public-resolvers.md']\n    cache_file = 'public-resolvers.md'\n    minisign_key = 'RWQf6LRCGA9i53mlYecO4IzT51TGPpvWucNSCh1CBM0QTaLn73Y7GFO3'\n    refresh_delay = 72\n    prefix = ''\n"` | Configuration This is a simple configuration. You can find a sample config here : https://github.com/DNSCrypt/dnscrypt-proxy/blob/master/dnscrypt-proxy/example-dnscrypt-proxy.toml And the manual : https://github.com/DNSCrypt/dnscrypt-proxy/wiki |
| configmap.config.enabled | bool | `false` | Enables or disables the configMap |
| configmap.config.labels | object | `{}` | Labels to add to the configMap |
| controller.replicas | int | `1` |  |
| env | object | See below | environment variables. See more environment variables in the [dnscrypt-proxy documentation](https://dnscrypt-proxy.org/docs). |
| env.TZ | string | `"UTC"` | Set the container timezone |
| image.pullPolicy | string | `"IfNotPresent"` | image pull policy. Set to Slways if you used "main" as tag |
| image.repository | string | `"klutchell/dnscrypt-proxy"` | image repository |
| image.tag | string | chart.appVersion | image tag. Use "main" if you want to be able to use DNS probes |
| ingress.main | object | See values.yaml | Enable and configure ingress settings for the chart under this key. |
| persistence | object | See values.yaml | Configure persistence settings for the chart under this key. |
| probes.liveness.custom | bool | `true` |  |
| probes.liveness.spec.exec.command[0] | string | `"/usr/local/bin/dnsprobe"` |  |
| probes.liveness.spec.exec.command[1] | string | `"google.com"` |  |
| probes.liveness.spec.exec.command[2] | string | `"127.0.0.1:5353"` |  |
| probes.liveness.spec.failureThreshold | int | `3` |  |
| probes.liveness.spec.initialDelaySeconds | int | `30` |  |
| probes.liveness.spec.periodSeconds | int | `5` |  |
| probes.liveness.spec.timeoutSeconds | int | `3` |  |
| probes.readiness.custom | bool | `true` |  |
| probes.readiness.spec.exec.command[0] | string | `"/usr/local/bin/dnsprobe"` |  |
| probes.readiness.spec.exec.command[1] | string | `"google.com"` |  |
| probes.readiness.spec.exec.command[2] | string | `"127.0.0.1:5353"` |  |
| probes.readiness.spec.failureThreshold | int | `1` |  |
| probes.readiness.spec.periodSeconds | int | `5` |  |
| probes.readiness.spec.timeoutSeconds | int | `1` |  |
| probes.startup.custom | bool | `true` |  |
| probes.startup.spec.exec.command[0] | string | `"/usr/local/bin/dnsprobe"` |  |
| probes.startup.spec.exec.command[1] | string | `"google.com"` |  |
| probes.startup.spec.exec.command[2] | string | `"127.0.0.1:5353"` |  |
| probes.startup.spec.failureThreshold | int | `10` |  |
| probes.startup.spec.initialDelaySeconds | int | `10` |  |
| probes.startup.spec.periodSeconds | int | `5` |  |
| probes.startup.spec.timeoutSeconds | int | `3` |  |
| service | object | See values.yaml | Configures service settings for the chart. |

----------------------------------------------
Autogenerated from chart metadata using [helm-docs v1.14.2](https://github.com/norwoodj/helm-docs/releases/v1.14.2)
