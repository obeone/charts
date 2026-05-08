# Olvid bot-daemon Helm Chart

![Version: 0.3.0](https://img.shields.io/badge/Version-0.3.0-informational?style=flat-square) ![AppVersion: 2.0.1](https://img.shields.io/badge/AppVersion-2.0.1-informational?style=flat-square) ![Type: application](https://img.shields.io/badge/Type-application-informational?style=flat-square) [![Artifact Hub](https://img.shields.io/endpoint?url=https://artifacthub.io/badge/repository/obeone)](https://artifacthub.io/packages/helm/obeone/olvid-bot)

## What is Olvid bot-daemon?

[Olvid bot-daemon](https://doc.bot.olvid.io/en/stable/index.html) is a bridge service that lets you automate interactions with [Olvid](https://olvid.io) secure-messaging groups — sending and receiving messages, reacting to events, and orchestrating bots over Olvid's end-to-end-encrypted protocol.

The daemon exposes a gRPC API on port `50051`. Bots and CLI tools authenticate against it with an admin client key and drive conversations programmatically.

**Key Features:**

- 🔐 **End-to-end encrypted**: messages and events ride on Olvid's E2EE protocol
- 🤖 **Bot-friendly gRPC API**: build automation in any gRPC-capable language
- 🔑 **Authenticated access**: clients identify with an admin client key
- 💾 **Persistent identity**: daemon state survives restarts via a PVC at `/daemon/data`
- 🧱 **bjw-s common library**: chart behaviour driven almost entirely from `values.yaml`

## TL;DR

```bash
helm repo add obeone https://charts.obeone.cloud
helm install olvid-bot obeone/olvid-bot \
  --set secrets.admin-credentials.stringData.OLVID_ADMIN_CLIENT_KEY_CLI="$(openssl rand -hex 24)"
```

## Introduction

This chart bootstraps the [Olvid bot-daemon](https://hub.docker.com/r/olvid/bot-daemon) on a Kubernetes cluster using the Helm package manager.

It is built on top of the [bjw-s-labs common library](https://bjw-s-labs.github.io/helm-charts/), so all knobs (controllers, services, persistence, ingress, secrets) follow the bjw-s conventions and live in `values.yaml`.

## Prerequisites

- Kubernetes 1.22+
- Helm 3.10+

## Installing the Chart

The daemon needs an **admin client key** to authenticate gRPC clients. You can either let the chart generate the Secret for you (recommended) or pre-create your own.

### Chart-managed Secret (default)

```bash
helm install olvid-bot obeone/olvid-bot \
  --set secrets.admin-credentials.stringData.OLVID_ADMIN_CLIENT_KEY_CLI="$(openssl rand -hex 24)"
```

### Bring-your-own Secret

```bash
kubectl create secret generic admin-credentials \
  --from-literal=OLVID_ADMIN_CLIENT_KEY_CLI=<your-strong-random-key>

helm install olvid-bot obeone/olvid-bot \
  --set secrets.admin-credentials.enabled=false
```

## Uninstalling the Chart

```bash
helm uninstall olvid-bot
```

The PVC and Secret are **retained** by default. Remove them manually if you want a clean state:

```bash
kubectl delete pvc -l app.kubernetes.io/name=olvid-bot
kubectl delete secret olvid-bot-admin-credentials
```

## Configuration

### Example Configuration

Below is an example `values.yaml` exposing the bot behind an ingress (gRPC traffic is in-cluster only — the ingress here is mostly relevant if you front the daemon with an HTTP gateway):

```yaml
controllers:
  main:
    containers:
      main:
        image:
          repository: olvid/bot-daemon
          tag: "{{ .Chart.AppVersion }}"
          pullPolicy: IfNotPresent

service:
  main:
    ports:
      grpc:
        port: 50051

persistence:
  data:
    enabled: true
    size: 5Gi
    accessMode: ReadWriteOnce
    globalMounts:
      - path: /daemon/data

secrets:
  admin-credentials:
    enabled: true
    stringData:
      OLVID_ADMIN_CLIENT_KEY_CLI: "replace-me-with-a-strong-random-key"

ingress:
  main:
    enabled: false
```

## Parameters

### Image

| Key                                                  | Type   | Default                   | Description                          |
|------------------------------------------------------|--------|---------------------------|--------------------------------------|
| controllers.main.containers.main.image.repository    | string | `olvid/bot-daemon`        | Image repository                     |
| controllers.main.containers.main.image.tag           | string | `{{ .Chart.AppVersion }}` | Image tag (defaults to `appVersion`) |
| controllers.main.containers.main.image.pullPolicy    | string | `IfNotPresent`            | Image pull policy                    |

### Service

| Key                              | Type   | Default     | Description           |
|----------------------------------|--------|-------------|-----------------------|
| service.main.type                | string | `ClusterIP` | Service type          |
| service.main.ports.grpc.port     | int    | `50051`     | gRPC service port     |
| service.main.ports.grpc.protocol | string | `TCP`       | Service port protocol |

### Persistence

| Key                           | Type   | Default          | Description                           |
|-------------------------------|--------|------------------|---------------------------------------|
| persistence.data.enabled      | bool   | `true`           | Enable persistence for `/daemon/data` |
| persistence.data.size         | string | `1Gi`            | PVC size                              |
| persistence.data.accessMode   | string | `ReadWriteOnce`  | PVC access mode                       |
| persistence.data.globalMounts | list   | `[/daemon/data]` | Mount paths for the data volume       |

### Secrets

| Key                                                             | Type   | Default    | Description                                |
|-----------------------------------------------------------------|--------|------------|--------------------------------------------|
| secrets.admin-credentials.enabled                               | bool   | `true`     | Whether the chart creates the admin Secret |
| secrets.admin-credentials.stringData.OLVID_ADMIN_CLIENT_KEY_CLI | string | `eb9uy...` | **Replace with a strong random value**     |

### Ingress

| Key                            | Type   | Default | Description    |
|--------------------------------|--------|---------|----------------|
| ingress.main.enabled           | bool   | `false` | Enable ingress |
| ingress.main.hosts             | list   | `[]`    | Ingress hosts  |
| ingress.main.tls               | list   | `[]`    | Ingress TLS    |

## Using the CLI

Launch a one-off interactive pod **in the same namespace** as the daemon:

```bash
kubectl run -it --rm olvid-cli \
  --image=olvid/bot-python-runner:2.0.1 \
  --restart=Never \
  --env=OLVID_DAEMON_TARGET=olvid-bot-main:50051 \
  --env=OLVID_ADMIN_CLIENT_KEY=$(kubectl get secret olvid-bot-admin-credentials -o jsonpath='{.data.OLVID_ADMIN_CLIENT_KEY_CLI}' | base64 -d) \
  --command -- olvid-cli
```

- `-it --rm` gives you an interactive shell and removes the pod when you exit.
- The DNS name `olvid-bot-main:50051` works because the pod runs in the same namespace as the service. It assumes a release name of `olvid-bot`.
- The Secret name `olvid-bot-admin-credentials` also assumes a release name of `olvid-bot`. If you brought your own Secret, use that name instead (e.g. `admin-credentials`).

## Upgrading

```bash
helm upgrade olvid-bot obeone/olvid-bot --reuse-values
```

> ⚠️ **2.x is a major upstream bump from 1.x.** Review the [Olvid bot-daemon docs](https://doc.bot.olvid.io/en/stable/index.html) before upgrading from a `1.x` chart — gRPC clients may need to be regenerated against the new API.

## Troubleshooting

### Checking Logs

```bash
kubectl logs -l app.kubernetes.io/name=olvid-bot
```

### Verifying the gRPC Service

From any pod in the same namespace:

```bash
kubectl run -it --rm grpc-debug --image=fullstorydev/grpcurl --restart=Never -- \
  -plaintext olvid-bot-main:50051 list
```

## Source Code

- <https://gitlab.com/olvid/olvid>
- <https://hub.docker.com/r/olvid/bot-daemon>
- <https://hub.docker.com/r/olvid/bot-python-runner>
- <https://github.com/obeone/charts/>

## Requirements

| Repository                                 | Name   | Version |
|--------------------------------------------|--------|---------|
| <https://bjw-s-labs.github.io/helm-charts> | common | 4.1.2   |

## Maintainers

| Name   | Email               | Url |
| ------ | ------------------- | --- |
| obeone | <obeone@obeone.org> |     |

----------------------------------------------
Autogenerated from chart metadata using [helm-docs v1.14.2](https://github.com/norwoodj/helm-docs/releases/v1.14.2)
