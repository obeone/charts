# Opengist Helm Chart

![Version](https://img.shields.io/badge/version-1.0.3-informational?style=flat-square)

OpenGist is a self-hosted Pastebin powered by Git. All snippets are stored in a Git repository and can be read and/or modified using standard Git commands, or with the web interface.

---

## Source Code

- [OpenGist Project](https://github.com/thomiceli/opengist)
- [Chart Repository](https://github.com/obeone/charts/tree/main/charts/opengist)

## Helm Repository

You can find the Helm chart at:

```bash
https://charts.obeone.cloud
```

Add the repository to Helm:

```bash
helm repo add obeone https://charts.obeone.cloud
helm repo update
```

## Installing the Chart

Install the chart with:

```bash
helm install opengist obeone/opengist
```

You can override default values using the `--values` flag:

```bash
helm install opengist obeone/opengist -f values.yaml
```

## Upgrading the Chart

```bash
helm upgrade opengist obeone/opengist
```

## Uninstalling the Chart

```bash
helm uninstall opengist
```

## Configuration

The following parameters are available to customize the chart:

- **Controllers & Containers**
- **Service Exposure**
- **Ingress**
- **Persistence**

Full list available in the [values.yaml](https://github.com/obeone/charts/tree/main/charts/opengist/values.yaml).

## Important Notes

- Provide a valid `OG_SECRET_KEY` in production.
- Consider using an external database.

## Maintainers

| Name   | Email                |
|--------|----------------------|
| obeone | <obeone@obeone.org>  |

---
_This Helm chart uses the [bjw-s common library](https://github.com/bjw-s/helm-charts)._
