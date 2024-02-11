# technitium-dnsserver

![Version: 1.0.10](https://img.shields.io/badge/Version-1.0.10-informational?style=flat-square) ![Type: application](https://img.shields.io/badge/Type-application-informational?style=flat-square) ![AppVersion: 12.0.1](https://img.shields.io/badge/AppVersion-12.0.1-informational?style=flat-square)

Technitium DNS Server is a DNS that can be use as a piHole or AdGuardHome replacement. It can also be used as authoritative server

## Maintainers

| Name | Email | Url |
| ---- | ------ | --- |
| obeone | <obeone@obeone.org> |  |

## Source Code

* <https://github.com/TechnitiumSoftware/DnsServer>

## Requirements

| Repository | Name | Version |
|------------|------|---------|
| https://library-charts.k8s-at-home.com | common | 4.5.2 |

## Values

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| env | object | See below | environment variables. See more environment variables in the [petio documentation](https://petio.org/docs). |
| env.TZ | string | `"UTC"` | Set the container timezone |
| image.pullPolicy | string | `"Always"` | image pull policy |
| image.repository | string | `"technitium/dns-server"` | image repository |
| image.tag | string | chart.appVersion | image tag |
| ingress.main | object | See the [docs](https://github.com/k8s-at-home/library-charts/blob/main/charts/stable/common/README.md) | Enable and configure ingress settings for the chart under this key. |
| persistence | object | See values.yaml | Configure persistence settings for the chart under this key. |
| service | object | See values.yaml | Configures service settings for the chart.  Depending of your k8s version, you'll be able, or not, to mix UDP and TCP services |

