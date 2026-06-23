# cloakbrowser-mcp

A Helm chart for [CloakBrowser MCP](https://github.com/swimmwatch/cloakbrowser-mcp),
a Model Context Protocol browser-automation server that runs upstream
[`@playwright/mcp`](https://github.com/microsoft/playwright-mcp) with the CloakBrowser
Chromium binary.

The chart deploys the bridge in its **streamable-http** transport so it can be reached
over the network and pointed at by any MCP client, instead of the default stdio mode
that only works for a local child process. Everything is driven from `values.yaml`
through the [bjw-s common library](https://github.com/bjw-s-labs/helm-charts).

## TL;DR

```bash
helm repo add obeone https://charts.obeone.cloud
helm install cbm obeone/cloakbrowser-mcp
```

The MCP endpoint is then served inside the cluster at:

```
http://cbm-cloakbrowser-mcp.<namespace>.svc.cluster.local:3000/mcp
```

## Requirements

- Kubernetes >= 1.31
- Helm >= 3.18

## What it does

The bridge launches a headless CloakBrowser Chromium and exposes the Playwright MCP
toolset (navigate, click, type, snapshot, screenshot, evaluate, and so on) over HTTP.
It listens on port `3000` and serves two health endpoints, `/healthz` and `/readyz`,
which the chart wires into the liveness, readiness and startup probes.

## Configuration

The whole upstream image is configured through environment variables (the entrypoint
takes no arguments), exposed under
`controllers.main.containers.main.env`. The defaults shipped by the chart:

| Variable                          | Default            | Purpose                                              |
| --------------------------------- | ------------------ | ---------------------------------------------------- |
| `CLOAK_PLAYWRIGHT_MCP_TRANSPORT`  | `streamable-http`  | Network transport instead of stdio.                  |
| `CLOAK_PLAYWRIGHT_MCP_HTTP_HOST`  | `0.0.0.0`          | Bind address so the Service can reach the pod.       |
| `CLOAK_PLAYWRIGHT_MCP_HTTP_PORT`  | `3000`             | Listen port.                                         |
| `CLOAK_PLAYWRIGHT_MCP_LOG_LEVEL`  | `info`             | `trace`, `debug`, `info`, `warn`, `error`, `fatal`, `silent`. |
| `PLAYWRIGHT_MCP_HEADLESS`         | `true`             | Headless Chromium.                                   |
| `PLAYWRIGHT_MCP_OUTPUT_DIR`       | `/data`            | Where artifacts (screenshots, traces) are written.   |

Add or override any other upstream variable by extending the same `env` map. See the
project's configuration reference for the full list (HTTPS listener, TLS certs, extra
Chromium args, and so on).

### Common values

| Key                                                    | Default                       | Description                                            |
| ------------------------------------------------------ | ----------------------------- | ------------------------------------------------------ |
| `controllers.main.containers.main.image.repository`    | `swimmwatch/cloakbrowser-mcp` | Image (mirrored on `ghcr.io/swimmwatch/cloakbrowser-mcp`). |
| `controllers.main.containers.main.image.tag`           | chart `appVersion`            | Image tag.                                             |
| `controllers.main.containers.main.resources`           | 250m / 512Mi req, 2Gi mem lim | Chromium is memory-hungry; no CPU limit so it can burst. |
| `service.main.ports.http.port`                         | `3000`                        | ClusterIP Service port.                                |
| `ingress.main.enabled`                                 | `false`                       | Enable to expose the endpoint outside the cluster.     |
| `persistence.data`                                     | `emptyDir` at `/data`         | Artifact volume. Switch to a PVC to keep artifacts.    |
| `persistence.dshm`                                     | `emptyDir` (Memory) at `/dev/shm` | Backs Chromium shared memory so it does not crash on heavy pages. |

### Persisting artifacts

By default `/data` is an `emptyDir`, so artifacts are discarded when the pod restarts.
To keep them, turn the `data` volume into a PersistentVolumeClaim:

```yaml
persistence:
  data:
    type: persistentVolumeClaim
    accessMode: ReadWriteOnce
    size: 2Gi
    globalMounts:
      - path: /data
```

### Exposing it through ingress

The bridge speaks plain HTTP, so terminate TLS at the ingress controller:

```yaml
ingress:
  main:
    enabled: true
    className: nginx
    hosts:
      - host: cloakbrowser.example.com
        paths:
          - path: /
            pathType: Prefix
            service:
              identifier: main
              port: http
    tls:
      - hosts:
          - cloakbrowser.example.com
        secretName: tls-cloakbrowser-example-com
```

## Security

- Runs as the non-root `node` user (uid 1000) from the upstream image.
- Drops all Linux capabilities and disallows privilege escalation.
- The ServiceAccount token is not mounted (`automountServiceAccountToken: false`); the
  bridge never calls the Kubernetes API.

`readOnlyRootFilesystem` is intentionally left off because Chromium needs to write to
several paths outside the mounted volumes.

## Source

- Upstream: <https://github.com/swimmwatch/cloakbrowser-mcp>
- Image: <https://hub.docker.com/r/swimmwatch/cloakbrowser-mcp>
