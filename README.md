# 🚀 obeone/charts

> A curated collection of GPG-signed Helm charts for self-hosted apps.

[![Artifact Hub](https://img.shields.io/endpoint?url=https://artifacthub.io/badge/repository/obeone&style=for-the-badge)](https://artifacthub.io/packages/search?repo=obeone)
[![Repo](https://img.shields.io/badge/repo-charts.obeone.cloud-2ea44f?style=for-the-badge&logo=helm&logoColor=white)](https://charts.obeone.cloud)
[![Signed](https://img.shields.io/badge/charts-GPG%20signed-blueviolet?style=for-the-badge&logo=gnuprivacyguard&logoColor=white)](public_key.gpg)
[![License](https://img.shields.io/badge/license-MIT-blue?style=for-the-badge)](LICENSE)

---

## ⚡ Quick start

```console
helm repo add obeone https://charts.obeone.cloud
helm repo update
helm search repo obeone
```

Install any chart with provenance verification:

```console
helm install my-release obeone/<chart> --verify
```

---

## 📦 Charts

| | Chart | App | Description |
| :-: | --- | --- | --- |
| 🔪 | [**cyberchef**](charts/cyberchef) | `v10.19.4` | GCHQ's [Cyber Swiss Army Knife](https://github.com/gchq/CyberChef) — encode, decode, encrypt, analyze. Multi-arch. |
| 🛡️ | [**dnscrypt-proxy**](charts/dnscrypt-proxy) | `2.1.14` | Flexible [DNS proxy](https://github.com/DNSCrypt/dnscrypt-proxy) with encrypted DNS protocols (DoH, DoT, DNSCrypt). |
| 🖌️ | [**draw-things**](charts/draw-things) | `latest` | [Draw Things](https://drawthings.ai) gRPC server — Stable Diffusion inference backend for the macOS/iOS app, GPU-accelerated. |
| 🎨 | [**fooocus**](charts/fooocus) | `latest` | [Fooocus](https://github.com/lllyasviel/Fooocus) — open-source image-generation UI on top of Stable Diffusion. |
| 🌍 | [**libretranslate**](charts/libretranslate) | `v1.6.5` | [LibreTranslate](https://github.com/LibreTranslate/LibreTranslate) — free, offline-capable machine-translation API. |
| 📡 | [**mktxp**](charts/mktxp) | `latest` | [MKTXP](https://github.com/akpw/mktxp) — Prometheus exporter for MikroTik RouterOS metrics. |
| 📂 | [**nfs-server**](charts/nfs-server) | `2.2.2` | Lightweight, multi-arch [containerized NFS server](https://github.com/obeone/docker-nfs-server). |
| 💬 | [**olvid-bot**](charts/olvid-bot) | `1.5.0` | [Olvid bot-daemon](https://gitlab.com/olvid/olvid) — bridge to automate Olvid secure-messaging groups. |
| 📝 | [**opengist**](charts/opengist) | `1.10.0` | [Opengist](https://github.com/thomiceli/opengist) — self-hosted, Git-backed Pastebin / GitHub Gist alternative. |
| 🌐 | [**technitium-dnsserver**](charts/technitium-dnsserver) | `15.2.0` | [Technitium DNS Server](https://github.com/TechnitiumSoftware/DnsServer) — recursive / authoritative DNS, PiHole & AdGuard alternative. |
| 📤 | [**transfer.sh**](charts/transfer.sh) | `v1.6.1` | [transfer.sh](https://github.com/dutchcoders/transfer.sh) — CLI-friendly file-sharing with pluggable storage backends. |
| 🪟 | [**winbox**](charts/winbox) | `3.40` | [MikroTik Winbox](https://github.com/obeone/winbox-docker) in your browser — VNC-streamed, Wine-powered. |

> 💡 Each chart ships with a per-folder `README.md` and a `values.yaml` annotated for [helm-docs](https://github.com/norwoodj/helm-docs).

---

## 🔐 Provenance

Every chart is signed with the GPG key `helm@obeone.org`:

```text
B9FE852F28888D27F8C9A11CD33E04CD22E335CE
```

Import the [public key](public_key.gpg) and verify on install:

```console
gpg --import public_key.gpg
helm install <release> obeone/<chart> --verify
```

---

## 🛠️ Contributing

Per-chart docs live under `charts/<name>/README.md`. When editing a chart:

1. If `Chart.yaml` changes — run `helm dep up charts/<name>`.
2. Run `helm lint charts/<name>` and fix every warning before committing.
3. Bump `version:` in `Chart.yaml` (chart-releaser only ships new versions)
   and add an entry under `annotations.artifacthub.io/changes`.

Releases are cut automatically by
[`chart-releaser-action`](.github/workflows/release.yml) on every push to `main`.

---

Made with ❤️ and a healthy dose of YAML by [**@obeone**](https://github.com/obeone).
x
