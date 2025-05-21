# transfer.sh Helm Chart

![Version: 1.0.2](https://img.shields.io/badge/Version-1.0.2-informational?style=flat-square) ![AppVersion: v1.6.1](https://img.shields.io/badge/AppVersion-v1.6.1-informational?style=flat-square) ![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square)

High-performance, secure and user-friendly command-line file sharing tool.
Easily upload, share and manage files directly from the browser and the terminal with support for configurable storage backends and access controls.

## TL;DR

```bash
helm repo add obeone https://charts.obeone.cloud/
helm repo update
helm install my-release obeone/transfer.sh
```

## Introduction

This chart bootstraps a [transfer.sh](https://github.com/dutchcoders/transfer.sh) deployment on a Kubernetes cluster using the Helm package manager.

It utilizes the [bjw-s common library chart](https://github.com/bjw-s/helm-charts/tree/main/charts/library/common) for common functionality.

## Prerequisites

*   Kubernetes: `>=1.16.0-0`
*   Helm: `v3.x`

## Installing the Chart

To install the chart with the release name `my-release`:

```bash
helm install my-release obeone/transfer.sh
```

The command deploys `transfer.sh` on the Kubernetes cluster in the default configuration. The [Parameters](#parameters) section lists the parameters that can be configured during installation.

## Uninstalling the Chart

To uninstall/delete the `my-release` deployment:

```bash
helm delete my-release
```

The command removes all the Kubernetes components associated with the chart and deletes the release.

## Parameters

The following table lists the configurable parameters of the `transfer.sh` chart and their default values.

| Key                                                 | Type     | Default                                                                                                                               | Description                                                                                                                                                              |
| --------------------------------------------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `controllers.main.containers.main.image.repository` | `string` | `dutchcoders/transfer.sh`                                                                                                             | Image repository for transfer.sh.                                                                                                                                        |
| `controllers.main.containers.main.image.tag`        | `string` | `v1.6.1-noroot`                                                                                                                       | Image tag for transfer.sh.                                                                                                                                               |
| `controllers.main.containers.main.image.pullPolicy` | `string` | `IfNotPresent`                                                                                                                        | Image pull policy.                                                                                                                                                       |
| `controllers.main.strategy`                         | `string` | `Recreate`                                                                                                                            | Deployment strategy. Can be `Recreate` or `RollingUpdate`.                                                                                                               |
| `controllers.main.containers.main.args`             | `list`   | `["--provider=local"]`                                                                                                                | Arguments to pass to the transfer.sh container. You can change the provider to `s3`, `gdrive`, etc. See [transfer.sh documentation](https://github.com/dutchcoders/transfer.sh). |
| `controllers.main.containers.main.env`              | `object` | `{"BASEDIR":"/storage"}`                                                                                                              | Environment variables to set in the container. `transfer.sh` supports environment variables to customize its behavior. See [transfer.sh documentation](https://github.com/dutchcoders/transfer.sh). |
| `controllers.main.containers.main.envFrom`          | `list`   | `[]`                                                                                                                                  | Environment variables from secrets or config maps. Useful for sensitive information like API keys. Example: `secretRef: { name: transfer-sh-secret }`.                   |
| `service.main.ports.http.port`                      | `integer`| `80`                                                                                                                                  | Service port for HTTP access.                                                                                                                                            |
| `service.main.ports.http.targetPort`                | `integer`| `8080`                                                                                                                                | Target port on the container for HTTP access.                                                                                                                            |
| `ingress.main.enabled`                              | `boolean`| `false`                                                                                                                               | Enable ingress for the main service.                                                                                                                                     |
| `ingress.main.hosts`                                | `list`   | `[{"host":"chart-example.local","paths":[{"path":"/","pathType":"Prefix","service":{"identifier":"main","port":"http"}}]}]`             | Ingress host configuration.                                                                                                                                              |
| `ingress.main.tls`                                  | `list`   | `[{"hosts":["chart-example.local"],"secretName":"tls-chart-example-local"}]`                                                          | Ingress TLS configuration.                                                                                                                                               |
| `persistence.storage.enabled`                       | `boolean`| `false`                                                                                                                               | Enable persistence for storage.                                                                                                                                          |
| `persistence.storage.accessMode`                    | `string` | `ReadWriteOnce`                                                                                                                       | Persistence access mode.                                                                                                                                                 |
| `persistence.storage.size`                          | `string` | `10Gi`                                                                                                                                | Persistence volume size.                                                                                                                                                 |
| `persistence.storage.globalMounts`                  | `list`   | `[{"path":"/storage"}]`                                                                                                               | Global mount path for storage.                                                                                                                                           |

Specify each parameter using the `--set key=value[,key=value]` argument to `helm install`. For example,

```bash
helm install my-release obeone/transfer.sh --set controllers.main.containers.main.args='{--provider=s3,--s3-bucket=mybucket}'
```

Alternatively, a YAML file that specifies the values for the parameters can be provided while installing the chart. For example,

```bash
helm install my-release obeone/transfer.sh -f values.yaml
```

> **Tip**: You can use the default [`values.yaml`](https://github.com/obeone/charts/tree/main/charts/transfer.sh/values.yaml)

## Dependencies

| Repository                               | Name   | Version |
| ---------------------------------------- | ------ | ------- |
| `https://bjw-s-labs.github.io/helm-charts` | common | `4.0.1` |

## Maintainers

| Name   | Email             |
| ------ | ----------------- |
| obeone | obeone@obeone.org |

## Sources

*   [https://github.com/dutchcoders/transfer.sh](https://github.com/dutchcoders/transfer.sh)
*   [https://github.com/obeone/charts/tree/main/charts/transfer.sh](https://github.com/obeone/charts/tree/main/charts/transfer.sh)

## Icon

![transfer.sh icon](https://raw.githubusercontent.com/obeone/charts/main/logo/transfer.sh.jpg)
