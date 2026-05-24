# Draw Things gRPC Server Helm Chart

![Version: 0.1.0](https://img.shields.io/badge/Version-0.1.0-informational?style=flat-square) ![AppVersion: latest](https://img.shields.io/badge/AppVersion-latest-informational?style=flat-square) ![Type: application](https://img.shields.io/badge/Type-application-informational?style=flat-square) [![Artifact Hub](https://img.shields.io/endpoint?url=https://artifacthub.io/badge/repository/obeone)](https://artifacthub.io/packages/helm/obeone/draw-things)

## What is Draw Things?

[Draw Things](https://drawthings.ai) is an on-device Stable Diffusion app for macOS and iOS. The official [`draw-things-grpc-server-cli`](https://hub.docker.com/r/drawthingsai/draw-things-grpc-server-cli) container exposes the same inference pipeline behind a gRPC API, so the phone/Mac app can offload generation to a beefy GPU box.

This chart deploys that gRPC server on Kubernetes, paired with a persistent volume for model storage and an NVIDIA GPU request. Behaviour is driven by the [bjw-s-labs common library](https://bjw-s-labs.github.io/helm-charts/), so all knobs live in `values.yaml`.

**Key features:**

- 🎨 **Same engine as the app** — the Draw Things app talks to it natively over gRPC
- 🚀 **GPU acceleration** — one `nvidia.com/gpu` requested by default
- 💾 **Persistent model library** — checkpoints survive pod restarts via a PVC at `/grpc-models`
- 🧱 **bjw-s common library** — declarative, opinionated, no custom templates to maintain

## TL;DR

```bash
helm repo add obeone https://charts.obeone.cloud
helm install draw-things obeone/draw-things
```

## Prerequisites

- Kubernetes 1.31+
- Helm 3.18+
- An NVIDIA GPU node with the [NVIDIA device plugin](https://github.com/NVIDIA/k8s-device-plugin) installed (so `nvidia.com/gpu` resources are schedulable). Depending on your runtime, you may also need to set `defaultPodOptions.runtimeClassName: nvidia`.

## Installing the chart

```bash
helm install draw-things obeone/draw-things
```

The chart will:

1. Create a `Deployment` with one replica (single-GPU singleton).
2. Provision a 50 GiB PVC mounted at `/grpc-models`.
3. Expose a `ClusterIP` service on port `7859`.

To override common knobs:

```bash
helm install draw-things obeone/draw-things \
  --set persistence.models.size=200Gi \
  --set defaultPodOptions.runtimeClassName=nvidia
```

## Uninstalling the chart

```bash
helm uninstall draw-things
```

The PVC is retained by default — delete it explicitly if you want a clean slate:

```bash
kubectl delete pvc -l app.kubernetes.io/name=draw-things
```

## Configuration

### Example `values.yaml`

```yaml
defaultPodOptions:
  runtimeClassName: nvidia

controllers:
  main:
    containers:
      main:
        resources:
          limits:
            nvidia.com/gpu: 1
          requests:
            nvidia.com/gpu: 1

persistence:
  models:
    enabled: true
    size: 200Gi
    accessMode: ReadWriteOnce
    globalMounts:
      - path: /grpc-models

service:
  main:
    ports:
      grpc:
        port: 7859
```

### Parameters

#### Image

| Key | Type | Default | Description |
| --- | --- | --- | --- |
| controllers.main.containers.main.image.repository | string | `drawthingsai/draw-things-grpc-server-cli` | Image repository |
| controllers.main.containers.main.image.tag | string | `{{ .Chart.AppVersion }}` | Image tag (defaults to `appVersion: latest`) |
| controllers.main.containers.main.image.pullPolicy | string | `IfNotPresent` | Image pull policy |
| controllers.main.containers.main.command | list | `["gRPCServerCLI"]` | Container command |
| controllers.main.containers.main.args | list | `["/grpc-models"]` | Container args |

#### GPU & runtime

| Key | Type | Default | Description |
| --- | --- | --- | --- |
| defaultPodOptions.runtimeClassName | string | unset | NVIDIA RuntimeClass name. Set to `nvidia` if your cluster needs explicit runtime opt-in. |
| controllers.main.containers.main.resources.requests.`nvidia.com/gpu` | int | `1` | GPUs requested (must equal limits) |
| controllers.main.containers.main.resources.limits.`nvidia.com/gpu` | int | `1` | GPUs allocated |

#### Service

| Key | Type | Default | Description |
| --- | --- | --- | --- |
| service.main.type | string | `ClusterIP` | Service type |
| service.main.ports.grpc.port | int | `7859` | gRPC service port |
| service.main.ports.grpc.protocol | string | `TCP` | Service port protocol |

#### Persistence

| Key | Type | Default | Description |
| --- | --- | --- | --- |
| persistence.models.enabled | bool | `true` | Enable PVC for `/grpc-models` |
| persistence.models.size | string | `50Gi` | PVC size |
| persistence.models.accessMode | string | `ReadWriteOnce` | PVC access mode |
| persistence.models.globalMounts | list | `[/grpc-models]` | Mount paths for the models volume |

#### Ingress

| Key | Type | Default | Description |
| --- | --- | --- | --- |
| ingress.main.enabled | bool | `false` | Enable ingress. gRPC requires end-to-end h2c support. |
| ingress.main.hosts | list | `[]` | Ingress hosts |
| ingress.main.tls | list | `[]` | Ingress TLS |

## Loading models

The container looks up checkpoints in `/grpc-models`. Three ways to populate it:

1. **`kubectl cp`** — fine for a quick test:

   ```bash
   POD=$(kubectl get pod -l app.kubernetes.io/name=draw-things -o name | head -n1)
   kubectl cp ./my-model.safetensors default/${POD#pod/}:/grpc-models/
   ```

2. **Init container** (downloader) — declare an extra container in `controllers.main.initContainers` that `wget`s checkpoints into `/grpc-models` at boot time.

3. **Pre-populated PVC** — point `persistence.models.existingClaim` at a PVC you already filled out-of-band (NFS share, restored snapshot, etc.).

## Connecting from the Draw Things app

```bash
kubectl port-forward svc/draw-things 7859:7859
```

Then in the macOS / iOS app, add a remote server pointing to `127.0.0.1:7859`.

## Troubleshooting

### Pod stuck in `Pending` — `0/N nodes are available: insufficient nvidia.com/gpu`

The cluster has no schedulable GPU. Verify with:

```bash
kubectl get nodes -o json | jq '.items[].status.allocatable | with_entries(select(.key | contains("nvidia")))'
```

Install / fix the [NVIDIA device plugin](https://github.com/NVIDIA/k8s-device-plugin) before continuing.

### Container starts but immediately exits

Check logs:

```bash
kubectl logs -l app.kubernetes.io/name=draw-things
```

A frequent cause is an empty `/grpc-models` directory — populate it (see above) or the server will refuse to start.

## Source code

- <https://github.com/drawthingsai/draw-things-community>
- <https://hub.docker.com/r/drawthingsai/draw-things-grpc-server-cli>
- <https://github.com/obeone/charts/>

## Requirements

| Repository | Name | Version |
| --- | --- | --- |
| <https://bjw-s-labs.github.io/helm-charts> | common | 5.0.1 |

## Maintainers

| Name | Email | Url |
| --- | --- | --- |
| obeone | <obeone@obeone.org> | |
