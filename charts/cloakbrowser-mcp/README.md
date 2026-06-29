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
| `CLOAK_PLAYWRIGHT_MCP_HTTP_AUTH_TOKEN` | _unset_       | Bearer token guarding the endpoint. Unset means no auth. See the security section, you almost certainly want this. |

A few more knobs the chart leaves at their upstream defaults, overridable through the same
`env` map:

| Variable                                    | Default     | Purpose                                              |
| ------------------------------------------- | ----------- | ---------------------------------------------------- |
| `CLOAK_PLAYWRIGHT_MCP_HTTP_ENDPOINT`        | `/mcp`      | Path the MCP server is served on.                    |
| `CLOAK_PLAYWRIGHT_MCP_HTTP_PROTOCOL`        | `http`      | Set to `https` (with mounted certs) to terminate TLS in the pod. |
| `CLOAK_PLAYWRIGHT_MCP_HTTP_SESSION_MAX`     | `32`        | Max concurrent browser sessions.                     |
| `CLOAK_PLAYWRIGHT_MCP_HTTP_SESSION_IDLE_TTL_MS` | `3600000` | Idle session timeout.                              |
| `CLOAK_PLAYWRIGHT_MCP_STEALTH_ARGS`         | `true`      | CloakBrowser stealth flags.                          |
| `CLOAK_PLAYWRIGHT_MCP_NO_SANDBOX`           | `true`      | Disable the Chromium sandbox (usually required in containers). |
| `PLAYWRIGHT_MCP_BROWSER_ENGINE`             | `cloak`     | Engine: `cloak`, `chromium`, `firefox`, `webkit`.    |

See the project's [docker configuration reference](https://github.com/swimmwatch/cloakbrowser-mcp/blob/main/docs/docker.md)
for the complete list (HTTPS listener, TLS certs, session backend, extra Chromium args).

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

### This endpoint is unauthenticated by default, and it is powerful

Upstream, the server binds `127.0.0.1` and is meant to be a local child process. This chart
deliberately flips that: it binds `0.0.0.0` and publishes the bridge through a Kubernetes
Service (and, if you enable it, an Ingress) so MCP clients can reach it over the network.

That means the endpoint hands anyone who can reach it a fully scriptable, real browser:
navigate anywhere, follow redirects, read internal-only URLs, hit cloud metadata endpoints,
exfiltrate responses. It is an SSRF and lateral-movement primitive on a plate. A ClusterIP
Service is reachable by every pod in the cluster, and an Ingress can expose it to the whole
internet.

So, unless the server sits on a trusted, isolated network you fully control:

- **Set an auth token.** Provide `CLOAK_PLAYWRIGHT_MCP_HTTP_AUTH_TOKEN` so every request
  (and every probe) must carry `Authorization: Bearer <token>`. Source it from a Secret you
  create, never inline it in `values.yaml`:

  ```yaml
  # kubectl create secret generic cloakbrowser-mcp-auth --from-literal=token='<a-long-random-token>'
  controllers:
    main:
      containers:
        main:
          env:
            CLOAK_PLAYWRIGHT_MCP_HTTP_AUTH_TOKEN:
              valueFrom:
                secretKeyRef:
                  name: cloakbrowser-mcp-auth
                  key: token
  ```

- **Mind the probes.** Once a token is set, `/healthz` and `/readyz` also require it, so the
  default probes will return 401 and the pod never becomes Ready. Add the same Bearer header
  to each probe spec (it lands in the pod manifest in clear text, which is the upstream
  tradeoff), or terminate auth in front of the pod. The shipped `values.yaml` carries a
  ready-to-uncomment example next to the probes.

- **Terminate TLS** at the Ingress (the bridge speaks plain HTTP), or set
  `CLOAK_PLAYWRIGHT_MCP_HTTP_PROTOCOL=https` with mounted certs, and restrict who can reach
  the Service with NetworkPolicies.

### Pod hardening (shipped defaults)

- Runs as the non-root `node` user (uid 1000) from the upstream image.
- Drops all Linux capabilities and disallows privilege escalation.
- The ServiceAccount token is not mounted (`automountServiceAccountToken: false`); the
  bridge never calls the Kubernetes API.

`readOnlyRootFilesystem` is intentionally left off because Chromium needs to write to
several paths outside the mounted volumes.

## Source

- Upstream: <https://github.com/swimmwatch/cloakbrowser-mcp>
- Image: <https://hub.docker.com/r/swimmwatch/cloakbrowser-mcp>
