# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository purpose

Personal Helm chart repository published at <https://charts.obeone.cloud> and indexed on Artifact Hub. Each subdirectory of `charts/` is a self-contained, GPG-signed Helm chart packaging a self-hosted application (Winbox, CyberChef, Technitium DNS, DNSCrypt-proxy, Olvid bot, etc.).

## Generic values — charts are public

Every chart is published and meant to be reused by strangers. Anything shipped in a chart (`values.yaml` defaults, `values.schema.json` examples, README snippets) **must use generic placeholders**, never real or personal data:

- Hosts/ingress/URLs → `example.com`, `chart-example.local`; IPs → documented ranges (`192.0.2.0/24`, `203.0.113.0/24`).
- No real secrets, tokens, passwords, emails, internal hostnames, or cluster-specific names. Secrets default to empty/commented, with a `# --` comment telling the user to set them.
- Defaults should be safe and work out of the box for an arbitrary cluster, not tuned to one environment.
- No cluster-specific Service defaults. In particular, do **not** ship dual-stack (`ipFamilyPolicy: PreferDualStack` / `ipFamilies`) or `internalTrafficPolicy` in a chart's `values.yaml`: those are local cluster conventions, not portable defaults. Let Kubernetes apply its own defaults; mention such knobs only as commented examples if useful.
- Don't bake personal performance/tuning constants into defaults (e.g. context length, parallelism, keep-alive timers). Ship the upstream app's own defaults and expose tuning knobs as commented examples.
- `values_local.yaml` is the only place for real/ad-hoc values; it never ships in a release.

(The repo's own identity — `charts.obeone.cloud`, the `helm@obeone.org` signing key — is legitimate repo metadata, not chart content; this rule is about what each chart hands to its users.)

## Mandatory workflow when modifying a chart

From `AGENTS.md` — these rules apply to every change, no exceptions:

1. If `charts/<name>/Chart.yaml` is touched (dependency version, appVersion, etc.), run `helm dep up charts/<name>` to refresh `Chart.lock` and the `charts/` subdir.
2. Before committing **any** chart change, run `helm lint charts/<name>` and fix every error/warning it surfaces.

When bumping a chart, also bump `version:` in `Chart.yaml` (chart-releaser only publishes new versions) and add an entry under `annotations.artifacthub.io/changes`.

## Chart anatomy

Two common-library lineages coexist — check `Chart.yaml` dependencies before editing templates:

- **k8s-at-home `common`** (`https://library-charts.k8s-at-home.com`, v4.x) — used by most charts (winbox, dnscrypt-proxy, technitium-dnsserver, cyberchef, fooocus, mktxp, opengist, libretranslate, transfer.sh, ...). Templates are typically a thin wrapper that just calls the common lib; configuration lives in `values.yaml`.
- **bjw-s-labs `common`** (`https://bjw-s-labs.github.io/helm-charts`, v4.x) — used by newer charts (olvid-bot). Different values schema (controllers/services/persistence keys); do not copy values between the two lineages.  

Per-chart files of note:
- `values.yaml` — annotated with helm-docs-style `# --` comments; do not strip them.
- `values.schema.json` — JSON Schema validated by Helm at install time; keep it in sync with new values you add.
- `values_local.yaml` — local override used for ad-hoc testing; never used in releases.
- `README_CONFIG.md.gotmpl` (when present) — helm-docs template; `README.md` is generated from it.

## Release pipeline

`.github/workflows/release.yml` runs on push to `main`:
1. Fast-forwards `gh-pages` from `main`.
2. Adds the upstream chart repos (`k8s-at-home`, `bitnami`, `bjw-s`) so `helm dep` can resolve.
3. Runs `helm/chart-releaser-action` with `CR_SIGN=true` and the GPG key `helm@obeone.org` (provided via `secrets.GPG_PRIVATE_KEY`). `CR_SKIP_EXISTING=true` — bumping `version:` is required for a new release to appear.

Public signing key fingerprint: `B9FE852F28888D27F8C9A11CD33E04CD22E335CE` (`public_key.gpg`).

## Scope discipline

- Edit only the chart(s) directly involved in the request. Don't sweep cosmetic changes across unrelated charts.
- Prefer editing `values.yaml` over hard-coding in templates; most charts have no custom templates beyond `common.all`.
