# CyberChef Helm Chart

![Version: 2.0.1](https://img.shields.io/badge/Version-2.0.1-informational?style=flat-square) ![AppVersion: v11.2.0](https://img.shields.io/badge/AppVersion-v11.2.0-informational?style=flat-square) ![Type: application](https://img.shields.io/badge/Type-application-informational?style=flat-square) [![Artifact Hub](https://img.shields.io/endpoint?url=https://artifacthub.io/badge/repository/obeone)](https://artifacthub.io/packages/helm/obeone/cyberchef)

## What is CyberChef?

CyberChef is "[The Cyber Swiss Army Knife](https://github.com/gchq/CyberChef)" — a web app for encryption, encoding, compression, and data analysis, originally developed by GCHQ. Operations are chained together in a visual recipe to transform data step-by-step, all client-side in your browser.

**Key Features:**

- 🔐 **Cryptography**: AES, DES, RSA, hashing, HMAC, key derivation, and dozens more primitives
- 🔡 **Encoding**: Base64, hex, URL, HTML entities, character escapes, charsets
- 🗜️ **Compression**: gzip, bzip2, zlib, raw deflate
- 🔍 **Data analysis**: regex, hexdumps, magic detection, file extraction, network protocol parsing
- 🧪 **Recipe builder**: chain operations, save and share via URL, run on local data only
- 🌍 **Self-hosted & multi-arch**: stays inside your network — image built for `amd64` and `arm64`

## TL;DR

```bash
helm repo add obeone https://charts.obeone.cloud
helm install cyberchef obeone/cyberchef
```

## Introduction

This chart bootstraps a [CyberChef](https://github.com/gchq/CyberChef) deployment on a Kubernetes cluster using the Helm package manager.

It deploys the multi-arch [`obeoneorg/cyberchef`](https://hub.docker.com/r/obeoneorg/cyberchef) image (rebuilt from the upstream sources) so you can run CyberChef on `amd64` and `arm64` nodes alike.

## Prerequisites

- Kubernetes 1.16+
- Helm 3.0+

## Installing the Chart

To install the chart with the release name `cyberchef`:

```bash
helm install cyberchef obeone/cyberchef
```

The command deploys CyberChef on the Kubernetes cluster with default configuration. The [Parameters](#parameters) section lists the parameters that can be configured during installation.

## Uninstalling the Chart

To uninstall the `cyberchef` deployment:

```bash
helm uninstall cyberchef
```

## Configuration

### Example Configuration

Below is an example `values.yaml` exposing CyberChef behind an ingress:

```yaml
image:
  repository: obeoneorg/cyberchef
  pullPolicy: IfNotPresent

env:
  TZ: "Europe/Paris"

ingress:
  main:
    enabled: true
    ingressClassName: nginx
    annotations:
      cert-manager.io/cluster-issuer: letsencrypt-prod
    hosts:
      - host: cyberchef.example.com
        paths:
          - path: /
            pathType: Prefix
    tls:
      - hosts:
          - cyberchef.example.com
        secretName: cyberchef-tls

# CyberChef is stateless, persistence is rarely needed.
persistence: {}
```

### Service Configuration

The container exposes CyberChef on port `8000`. The default service maps cluster port `8000` to the same container port. Adjust `service.main.ports.http.port` if you need a different cluster-side port.

## Parameters

### Image

| Key                | Type   | Default                | Description                                |
|--------------------|--------|------------------------|--------------------------------------------|
| image.repository   | string | `obeoneorg/cyberchef`  | Image repository                           |
| image.tag          | string | `chart.appVersion`     | Image tag (defaults to chart `appVersion`) |
| image.pullPolicy   | string | `Always`               | Image pull policy                          |

### Environment

| Key      | Type   | Default   | Description           |
|----------|--------|-----------|-----------------------|
| env      | object | See below | Environment variables |
| env.TZ   | string | `UTC`     | Container timezone    |

### Service

| Key                                | Type   | Default | Description       |
|------------------------------------|--------|---------|-------------------|
| service.main.ports.http.port       | int    | `8000`  | HTTP service port |

### Ingress

| Key                           | Type   | Default  | Description                                  |
|-------------------------------|--------|----------|----------------------------------------------|
| ingress.main.enabled          | bool   | `false`  | Enable the ingress                           |
| ingress.main.ingressClassName | string | `""`     | Ingress class                                |
| ingress.main.hosts            | list   | See docs | Ingress hosts (see k8s-at-home common chart) |
| ingress.main.tls              | list   | See docs | Ingress TLS configuration                    |

### Persistence

| Key         | Type   | Default | Description                                             |
|-------------|--------|---------|---------------------------------------------------------|
| persistence | object | `{}`    | Persistence configuration (rarely needed for CyberChef) |

## Why Self-Host CyberChef?

### Privacy

The public CyberChef instance is harmless for everyday use, but pasting sensitive payloads (tokens, internal hashes, customer data) into a third-party site is rarely a good idea — even when "everything happens client-side".

Hosting your own instance keeps every byte inside your network, behind your own auth, with your own logs.

### Air-gapped & offline use

A self-hosted CyberChef works without Internet access, which makes it a perfect fit for incident response, malware triage, and DFIR labs that operate offline by design.

### Performance

Large payloads (multi-MB pcap parsing, file extraction recipes) feel snappier when the JavaScript bundle is served from inside the cluster instead of the public CDN.

## Troubleshooting

### Checking Logs

```bash
kubectl logs -l app.kubernetes.io/name=cyberchef
```

### Verifying the Service

```bash
kubectl port-forward svc/cyberchef 8000:8000
# then open http://127.0.0.1:8000 in a browser
```

## Source Code

- <https://github.com/gchq/CyberChef>
- <https://hub.docker.com/r/obeoneorg/cyberchef>
- <https://github.com/obeone/charts/>

## Requirements

| Repository                               | Name   | Version |
|------------------------------------------|--------|---------|
| <https://library-charts.k8s-at-home.com> | common | 4.5.2   |

## Maintainers

| Name   | Email               | Url |
| ------ | ------------------- | --- |
| obeone | <obeone@obeone.org> |     |

----------------------------------------------
Autogenerated from chart metadata using [helm-docs v1.14.2](https://github.com/norwoodj/helm-docs/releases/v1.14.2)
