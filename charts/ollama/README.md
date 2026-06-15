# Ollama Helm Chart

![Version: 0.1.0](https://img.shields.io/badge/Version-0.1.0-informational?style=flat-square) ![AppVersion: latest](https://img.shields.io/badge/AppVersion-latest-informational?style=flat-square) ![Type: application](https://img.shields.io/badge/Type-application-informational?style=flat-square) [![Artifact Hub](https://img.shields.io/endpoint?url=https://artifacthub.io/badge/repository/obeone)](https://artifacthub.io/packages/helm/obeone/ollama)

## What is Ollama?

[Ollama](https://ollama.com) runs large language models locally — it pulls, manages and serves models (Llama, Mistral, Gemma, Qwen, …) behind a simple HTTP API on port `11434`, with an OpenAI-compatible `/v1` surface.

This chart deploys the [`ollama/ollama`](https://hub.docker.com/r/ollama/ollama) server on Kubernetes with a persistent model store and optional NVIDIA GPU acceleration. Behaviour is driven by the [bjw-s-labs common library](https://bjw-s-labs.github.io/helm-charts/), so almost every knob lives in `values.yaml`.

**Key features:**

- 🧠 **Local LLM serving** — the full Ollama API (`/api/*`) plus the OpenAI-compatible `/v1/*` endpoints
- 🔌 **Optional transparent proxy + metrics sidecar, flipped by a single switch** — see [The exporter / transparent proxy](#the-exporter--transparent-proxy) below
- 🚀 **GPU acceleration** — `runtimeClassName` + `NVIDIA_*` env wired out of the box, CPU-only friendly by default
- 💾 **Persistent model library** — blobs survive pod restarts via a PVC at `/root/.ollama`
- 📈 **Prometheus-ready** — `/metrics` and an optional `ServiceMonitor`
- 🧱 **bjw-s common library** — declarative, opinionated, one thin entrypoint template

## TL;DR

```bash
helm repo add obeone https://charts.obeone.cloud
helm install ollama obeone/ollama
```

## The exporter / transparent proxy

This is the headline feature of the chart, so it gets its own section.

The `exporter` sidecar is a **transparent proxy** that sits in front of Ollama: it listens on `:8000`, forwards every API request to the Ollama server in the same pod (`http://localhost:11434`), and exposes Prometheus metrics on `/metrics` for the traffic it sees. Build it from [frcooper/ollama-exporter](https://github.com/frcooper/ollama-exporter) and point `controllers.main.containers.exporter.image.repository` at your registry.

Because the proxy is **in the API path**, the chart wires the `http` Service port (`11434`) to the sidecar's `:8000` rather than straight to Ollama. All client traffic therefore flows through the proxy and gets accounted for.

### A single switch toggles the whole path

You do **not** juggle several coupled values to turn the sidecar on or off. The chart keys everything off the exporter container's own `enabled` flag and rewrites the Service wiring for you (in `templates/common.yaml`, before the bjw-s loader renders):

```yaml
controllers:
  main:
    containers:
      exporter:
        enabled: false   # <-- the only line you touch
```

| `exporter.enabled` | `http` Service port → targetPort | `metrics` port (`:8000`) | Sidecar container |
|--------------------|----------------------------------|--------------------------|-------------------|
| `true` (default)   | `11434 → 8000` (through proxy)    | present                  | present           |
| `false`            | `11434 → 11434` (direct to Ollama)| dropped                  | dropped           |

So when you disable it, the API keeps working — traffic just goes straight to Ollama and there is no dangling `:8000` Service port left pointing at a container that no longer exists. No other value needs changing.

> ℹ️ The default ships the proxy **on**. If you have no metrics/proxy image to run, set `exporter.enabled: false` and Ollama is served directly.

## Prerequisites

- Kubernetes 1.31+
- Helm 3.18+
- For GPU acceleration: an NVIDIA GPU node with the [NVIDIA device plugin](https://github.com/NVIDIA/k8s-device-plugin) and, depending on your runtime, `defaultPodOptions.runtimeClassName: nvidia`. CPU-only clusters work with the defaults.
- For the proxy/metrics sidecar (default on): a reachable image built from [frcooper/ollama-exporter](https://github.com/frcooper/ollama-exporter). If you don't have one, set `controllers.main.containers.exporter.enabled: false`.

## Installing the chart

```bash
helm install ollama obeone/ollama
```

The chart will:

1. Create a `Deployment` with one replica (single RWO PVC → `Recreate` strategy).
2. Provision a 100 GiB PVC mounted at `/root/.ollama` for models and blobs.
3. Expose a `ClusterIP` service on port `11434` (through the proxy by default).

GPU + direct-serving example:

```bash
helm install ollama obeone/ollama \
  --set defaultPodOptions.runtimeClassName=nvidia \
  --set controllers.main.containers.exporter.enabled=false \
  --set persistence.data.size=200Gi
```

## Uninstalling the chart

```bash
helm uninstall ollama
```

The PVC is retained by default — delete it explicitly for a clean slate:

```bash
kubectl delete pvc -l app.kubernetes.io/name=ollama
```

## Configuration

### Example `values.yaml`

```yaml
defaultPodOptions:
  runtimeClassName: nvidia          # GPU; leave "" for CPU-only

controllers:
  main:
    containers:
      ollama:
        image:
          repository: ollama/ollama
          tag: "0.6.0"              # pin for reproducibility
        env:
          OLLAMA_KEEP_ALIVE: 30m
          OLLAMA_CONTEXT_LENGTH: "64000"
        resources:
          requests:
            memory: 10Gi            # bump to fit your models
      exporter:
        enabled: true               # transparent proxy + /metrics (see above)
        image:
          repository: registry.example.com/ollama-exporter

persistence:
  data:
    size: 200Gi

serviceMonitor:
  metrics:
    enabled: true                   # needs a Prometheus Operator stack
```

## Parameters

### Pod / GPU

| Key                                          | Type   | Default | Description                                                        |
|----------------------------------------------|--------|---------|--------------------------------------------------------------------|
| defaultPodOptions.runtimeClassName           | string | `""`    | NVIDIA RuntimeClass for GPU; empty = CPU-only                      |
| defaultPodOptions.automountServiceAccountToken | bool | `false` | Ollama does not call the Kubernetes API                            |
| defaultPodOptions.nodeSelector               | object | `{}`    | Pin the workload to specific node(s), typically a GPU host         |

### Ollama container

| Key                                                            | Type   | Default          | Description                                       |
|----------------------------------------------------------------|--------|------------------|---------------------------------------------------|
| controllers.main.containers.ollama.image.repository            | string | `ollama/ollama`  | Ollama server image                               |
| controllers.main.containers.ollama.image.tag                  | string | `latest`         | Image tag — pin to a release for reproducibility  |
| controllers.main.containers.ollama.env.OLLAMA_KEEP_ALIVE       | string | `30m`            | How long a model stays loaded after the last call |
| controllers.main.containers.ollama.env.OLLAMA_NUM_PARALLEL     | string | `"2"`            | Parallel requests per model                       |
| controllers.main.containers.ollama.env.OLLAMA_MAX_LOADED_MODELS| string | `"4"`            | Max models kept loaded simultaneously             |
| controllers.main.containers.ollama.env.OLLAMA_CONTEXT_LENGTH   | string | `"64000"`        | Default context window size                       |
| controllers.main.containers.ollama.env.OLLAMA_FLASH_ATTENTION  | string | `"true"`         | Enable Flash Attention                            |

### Exporter / proxy sidecar

| Key                                                    | Type   | Default                   | Description                                                          |
|--------------------------------------------------------|--------|---------------------------|---------------------------------------------------------------------|
| controllers.main.containers.exporter.enabled           | bool   | `true`                    | **Single switch** for the proxy + metrics path (see section above)  |
| controllers.main.containers.exporter.image.repository  | string | `ollama-exporter`         | Proxy/exporter image — set to your own build                        |
| controllers.main.containers.exporter.image.tag         | string | `latest`                  | Image tag                                                           |
| controllers.main.containers.exporter.env.OLLAMA_HOST   | string | `http://localhost:11434`  | Upstream Ollama URL the proxy forwards to                           |

### Service

| Key                                          | Type   | Default          | Description                                                  |
|----------------------------------------------|--------|------------------|-------------------------------------------------------------|
| service.main.type                            | string | `ClusterIP`      | Service type                                                |
| service.main.ipFamilyPolicy                  | string | `PreferDualStack`| Dual-stack, degrades to single-stack                        |
| service.main.ports.http.port                 | int    | `11434`          | API port; `targetPort` is managed by `exporter.enabled`     |
| service.main.ports.metrics.port              | int    | `8000`           | Exporter `/metrics` port (dropped when the exporter is off) |

### Persistence

| Key                              | Type   | Default          | Description                                          |
|----------------------------------|--------|------------------|------------------------------------------------------|
| persistence.data.enabled         | bool   | `true`           | Model/blob store at `/root/.ollama`                  |
| persistence.data.size            | string | `100Gi`          | PVC size — size it for the models you intend to pull |
| persistence.data.accessMode      | string | `ReadWriteOnce`  | PVC access mode                                      |
| persistence.tmp.enabled          | bool   | `true`           | `emptyDir` scratch for `OLLAMA_TMPDIR` at `/tmp/ollama` |

### ServiceMonitor

| Key                              | Type   | Default | Description                                                      |
|----------------------------------|--------|---------|-----------------------------------------------------------------|
| serviceMonitor.metrics.enabled   | bool   | `false` | Prometheus Operator `ServiceMonitor` scraping the exporter      |

### Ingress

| Key                  | Type | Default | Description                                              |
|----------------------|------|---------|---------------------------------------------------------|
| ingress.main.enabled | bool | `false` | Enable ingress (routes to the proxied API port, not `/metrics`) |
| ingress.main.hosts   | list | …       | Ingress hosts                                           |
| ingress.main.tls     | list | `[]`    | Ingress TLS                                             |

## Metrics

When the exporter is enabled (default), Prometheus metrics are served on `:8000/metrics`. With a Prometheus Operator stack present, scrape them by enabling the bundled `ServiceMonitor`:

```bash
helm upgrade ollama obeone/ollama --reuse-values \
  --set serviceMonitor.metrics.enabled=true
```

Disabling the exporter (`exporter.enabled=false`) removes both the sidecar and the `metrics` port, so leave the `ServiceMonitor` off in that case.

## GPU notes

GPU exposure is effective only when `defaultPodOptions.runtimeClassName` points at an NVIDIA RuntimeClass. The `ollama` container already carries `NVIDIA_VISIBLE_DEVICES=all` and `NVIDIA_DRIVER_CAPABILITIES=compute,utility`, plus `OLLAMA_SCHED_SPREAD=1` to spread work across all GPUs. For [Sablier](https://acouvreur.github.io/sablier/) scale-to-zero on a GPU group, set pod labels under `controllers.main.pod.labels`.

## Upgrading

```bash
helm upgrade ollama obeone/ollama --reuse-values
```

## Troubleshooting

### Checking logs

```bash
kubectl logs -l app.kubernetes.io/name=ollama -c ollama
kubectl logs -l app.kubernetes.io/name=ollama -c exporter   # if enabled
```

### Pulling and querying a model

```bash
kubectl exec -it deploy/ollama -c ollama -- ollama pull llama3.2
kubectl run -it --rm ollama-curl --image=curlimages/curl --restart=Never -- \
  -s http://ollama:11434/api/tags
```

The `ollama` Service name assumes a release name of `ollama`.

## Source Code

- <https://github.com/ollama/ollama>
- <https://hub.docker.com/r/ollama/ollama>
- <https://github.com/frcooper/ollama-exporter>
- <https://github.com/obeone/charts/>

## Requirements

| Repository                                 | Name   | Version |
|--------------------------------------------|--------|---------|
| <https://bjw-s-labs.github.io/helm-charts> | common | 5.0.1   |

## Maintainers

| Name   | Email               | Url |
| ------ | ------------------- | --- |
| obeone | <obeone@obeone.org> |     |
