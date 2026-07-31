#!/usr/bin/env bash
#
# Rewrite the GitHub releases produced by chart-releaser so that they carry the
# packaged application version in their title and a useful changelog in their
# body.
#
# chart-releaser reuses the release name as the git tag name, so the tag must
# stay "<chart>-<chart version>" or every download URL stored in index.yaml
# breaks. The title, on the other hand, is a free-form field, so it is rewritten
# here after the fact instead of through --release-name-template.
#
# Usage:
#   scripts/enrich-releases.sh "chart-a,chart-b"
#
# The argument is the comma-separated list of chart names emitted by
# helm/chart-releaser-action as its "changed_charts" output.
#
# Environment:
#   CHARTS_DIR      directory holding the charts (default: charts)
#   HELM_REPO_NAME  repo alias used in the install snippet (default: obeone)
#   HELM_REPO_URL   repo URL used in the install snippet
#   ARTIFACTHUB_ORG Artifact Hub repository name (default: obeone)
#   GH_TOKEN        token used by the gh CLI
#
set -euo pipefail

CHARTS_DIR="${CHARTS_DIR:-charts}"
HELM_REPO_NAME="${HELM_REPO_NAME:-obeone}"
HELM_REPO_URL="${HELM_REPO_URL:-https://charts.obeone.cloud}"
ARTIFACTHUB_ORG="${ARTIFACTHUB_ORG:-obeone}"

# Emit a message on stderr so it never pollutes a function's captured stdout.
log() {
    printf '%s\n' "$*" >&2
}

# Read a scalar field from a Chart.yaml, returning an empty string when the
# field is absent or null rather than yq's literal "null".
chart_field() {
    local chart_file="$1" expression="$2"
    yq -r "${expression} // \"\"" "${chart_file}"
}

# Render the artifacthub.io/changes annotation as a markdown bullet list.
#
# The annotation is a YAML string holding a list whose entries are either
# mappings ({kind, description}) or bare strings; both forms are accepted by
# Artifact Hub, so both are handled here. Prints nothing when the annotation is
# missing or unparseable.
render_chart_changes() {
    local chart_file="$1" raw
    raw="$(chart_field "${chart_file}" '.annotations["artifacthub.io/changes"]')"
    [[ -n "${raw}" ]] || return 0

    printf '%s\n' "${raw}" | yq -r '
        .[]
        | (select(tag == "!!map") | "- **" + .kind + "**: " + .description),
          (select(tag == "!!str") | "- " + .)
    ' 2>/dev/null || true
}

# Resolve the upstream project URL for a chart.
#
# Preference order: an artifacthub.io/links entry whose name mentions
# "upstream", then the first sources[] entry that is not this chart repository,
# then home. Prints an empty string when nothing usable is declared.
upstream_url() {
    local chart_file="$1" url

    url="$(chart_field "${chart_file}" '.annotations["artifacthub.io/links"]' \
        | yq -r '[.[] | select(.name | downcase | test("upstream")) | .url][0] // ""' 2>/dev/null || true)"
    if [[ -n "${url}" ]]; then
        printf '%s' "${url}"
        return 0
    fi

    url="$(chart_field "${chart_file}" \
        '[.sources[]? | select(test("github.com/obeone/charts") | not)][0]')"
    if [[ -n "${url}" ]]; then
        printf '%s' "${url}"
        return 0
    fi

    chart_field "${chart_file}" '.home'
}

# Find the upstream release page matching an application version.
#
# Only GitHub upstreams can be resolved precisely: the two usual tag spellings
# ("v1.2.3" and "1.2.3") are probed through the API and the first existing one
# wins. Anything else falls back to the project's release listing, and non
# GitHub upstreams print nothing.
upstream_release_url() {
    local project_url="$1" app_version="$2" path owner repo candidate html_url

    [[ -n "${project_url}" && -n "${app_version}" ]] || return 0
    [[ "${project_url}" == https://github.com/* ]] || return 0

    path="${project_url#https://github.com/}"
    path="${path%/}"
    path="${path%.git}"
    owner="${path%%/*}"
    repo="${path#*/}"
    repo="${repo%%/*}"
    [[ -n "${owner}" && -n "${repo}" && "${owner}" != "${path}" ]] || return 0

    # gh api prints the API error payload on stdout when a tag is missing, so the
    # exit status is what decides here, never the captured text.
    for candidate in "v${app_version}" "${app_version}"; do
        if html_url="$(gh api "repos/${owner}/${repo}/releases/tags/${candidate}" \
            --jq '.html_url' 2>/dev/null)" && [[ -n "${html_url}" ]]; then
            printf '%s' "${html_url}"
            return 0
        fi
    done

    printf 'https://github.com/%s/%s/releases' "${owner}" "${repo}"
}

# Write the full markdown body for one chart release to stdout.
build_body() {
    local chart="$1" chart_file="$2" version="$3" app_version="$4"
    local description changes project_url release_url

    description="$(chart_field "${chart_file}" '.description')"
    changes="$(render_chart_changes "${chart_file}")"
    project_url="$(upstream_url "${chart_file}")"
    release_url="$(upstream_release_url "${project_url}" "${app_version}")"

    if [[ -n "${description}" ]]; then
        printf '%s\n\n' "${description}"
    fi

    printf '## Chart changelog\n\n'
    if [[ -n "${changes}" ]]; then
        printf '%s\n\n' "${changes}"
    else
        printf 'No changelog entry was recorded for chart version %s.\n\n' "${version}"
    fi
    printf 'Full history: [Artifact Hub changelog](https://artifacthub.io/packages/helm/%s/%s?modal=changelog)\n\n' \
        "${ARTIFACTHUB_ORG}" "${chart}"

    printf '## Upstream\n\n'
    if [[ -n "${app_version}" ]]; then
        # shellcheck disable=SC2016  # the backticks are markdown code spans
        printf 'Application version: `%s`\n\n' "${app_version}"
    else
        printf 'This chart does not pin an application version.\n\n'
    fi
    if [[ -n "${release_url}" ]]; then
        printf 'Upstream release notes: %s\n\n' "${release_url}"
    elif [[ -n "${project_url}" ]]; then
        printf 'Upstream project: %s\n\n' "${project_url}"
    fi

    printf '## Install\n\n'
    printf '```bash\n'
    printf 'helm repo add %s %s\n' "${HELM_REPO_NAME}" "${HELM_REPO_URL}"
    printf 'helm install %s %s/%s --version %s\n' \
        "${chart}" "${HELM_REPO_NAME}" "${chart}" "${version}"
    printf '```\n'
}

# Retitle and rewrite the release of a single chart.
#
# Returns 0 even when the release is missing: chart-releaser skips existing
# releases, so a chart can legitimately appear in changed_charts without a
# freshly created release to edit.
enrich_chart() {
    local chart="$1"
    local chart_file="${CHARTS_DIR}/${chart}/Chart.yaml"
    local version app_version tag title body_file

    if [[ ! -f "${chart_file}" ]]; then
        log "skip ${chart}: ${chart_file} not found"
        return 0
    fi

    version="$(chart_field "${chart_file}" '.version')"
    app_version="$(chart_field "${chart_file}" '.appVersion')"
    if [[ -z "${version}" ]]; then
        log "skip ${chart}: no version in ${chart_file}"
        return 0
    fi

    tag="${chart}-${version}"
    if ! gh release view "${tag}" >/dev/null 2>&1; then
        log "skip ${chart}: release ${tag} does not exist"
        return 0
    fi

    if [[ -n "${app_version}" ]]; then
        title="${chart} ${version} (app ${app_version})"
    else
        title="${chart} ${version}"
    fi

    body_file="$(mktemp)"
    build_body "${chart}" "${chart_file}" "${version}" "${app_version}" >"${body_file}"

    log "updating ${tag} -> ${title}"
    gh release edit "${tag}" --title "${title}" --notes-file "${body_file}"
    rm -f "${body_file}"
}

main() {
    local changed="${1:-}" chart

    if [[ -z "${changed}" ]]; then
        log 'no changed charts, nothing to enrich'
        return 0
    fi

    # changed_charts is a comma-separated list; tolerate stray whitespace.
    IFS=',' read -ra charts <<<"${changed}"
    for chart in "${charts[@]}"; do
        chart="${chart//[[:space:]]/}"
        [[ -n "${chart}" ]] || continue
        enrich_chart "${chart}"
    done
}

main "$@"
