# Olvid bot-daemon Helm Chart

![Chart Version](https://img.shields.io/badge/chart-0.1.0-informational?style=flat-square)
![App Version](https://img.shields.io/badge/app-1.4.1-brightgreen?style=flat-square)

**Olvid bot-daemon** is a bridge that lets you automate interactions with Olvid secure-messaging groups.

Have a look at [the documentation](https://doc.bot.olvid.io/en/stable/index.html) for more information on how to use it.

This chart leverages the [bjw-s common library](https://github.com/bjw-s/helm-charts) so that nearly everything is configured via **values.yaml**.

---

## Requirements

- Kubernetes >= 1.22
- Helm >= 3.10

---

## Installation

```bash
helm repo add obeone https://charts.obeone.cloud
helm repo update

# Generate a strong admin key and install the chart
helm install olvid-bot obeone/olvid-bot \
  --set secrets.admin-credentials.stringData.OLVID_ADMIN_CLIENT_KEY_CLI="$(openssl rand -hex 24)"
```

### Managing the Secret yourself

```bash
kubectl create secret generic admin-credentials \
  --from-literal=OLVID_ADMIN_CLIENT_KEY_CLI=<your-key>

helm install olvid-bot obeone/olvid-bot \
  --set secrets.admin-credentials.enabled=false
```

---

## Configuration highlights

| Key                                                | Default                   | Purpose                                    |
|----------------------------------------------------|---------------------------|--------------------------------------------|
| `controllers.main.containers.main.image.tag`       | `{{ .Chart.AppVersion }}` | Daemon image tag                           |
| `service.main.ports.grpc.port`                     | `50051`                   | Internal gRPC port                         |
| `persistence.data.size`                            | `1Gi`                     | PVC size for `/daemon/data`                |
| `secrets.admin-credentials.enabled`                | `true`                    | Whether to create the Secret               |

See **values.yaml** for the full list of options.

---

## Using the CLI (`kubectl run`)

Launch a one-off interactive pod **in the same namespace** as the daemon:

```bash
kubectl run -it --rm olvid-cli \
  --image=olvid/bot-python-runner:1.4.1 \
  --restart=Never \
  --env=OLVID_DAEMON_TARGET=olvid-bot-main:50051 \
  --env=OLVID_ADMIN_CLIENT_KEY=$(kubectl get secret olvid-bot-admin-credentials -o jsonpath='{.data.OLVID_ADMIN_CLIENT_KEY_CLI}' | base64 -d) \
  --command -- olvid-cli
```

* `-it --rm` gives you an interactive shell and removes the pod when you exit.
* The DNS name `olvid-bot-main:50051` works because the pod runs in the same namespace as the service. It assumes a release name of `olvid-bot`.
* The secret name `olvid-bot-admin-credentials` also assumes a release name of `olvid-bot`.
* If you manage the secret yourself (see above), use that secret's name instead (e.g. `admin-credentials`).

---

## Upgrading

```bash
helm upgrade olvid-bot obeone/olvid-bot --reuse-values
```

Bump `appVersion` in **Chart.yaml** to upgrade the daemon image.

---

## Uninstalling

```bash
helm uninstall olvid-bot
```

The PVC and Secret are **retained** by default. Delete them manually if you no longer need them.

---

### License

Released under the terms of the upstream Olvid project.
