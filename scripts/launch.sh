#!/usr/bin/env bash

set -euo pipefail

PACKAGE_PATH=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )/.." &> /dev/null && pwd )

# Secret Manager secrets created by terraform-gcp/church.tf:
CREDENTIALS_SECRET="STJOSEPH_YOUTUBE_CLIENT_SECRET"
TOKEN_SECRET="STJOSEPH_YOUTUBE_TOKEN"

cd "${PACKAGE_PATH}" || { >&2 echo "Failed to cd to ${PACKAGE_PATH}."; exit 1; }

refresh_token() {
    [ -f token.json ] || return 0
    python -s -c 'import json, sys; print(json.load(open(sys.argv[1])).get("refresh_token", ""))' token.json
}

if [ ! -f credentials.json ]; then
    echo gcloud secrets versions access latest --secret="${CREDENTIALS_SECRET}" --out-file=credentials.json
    gcloud secrets versions access latest --secret="${CREDENTIALS_SECRET}" --out-file=credentials.json
fi

# Always start from the shared token so the scheduled job and local runs stay in sync:
echo gcloud secrets versions access latest --secret="${TOKEN_SECRET}" --out-file=token.json
gcloud secrets versions access latest --secret="${TOKEN_SECRET}" --out-file=token.json \
    || >&2 echo "No token in ${TOKEN_SECRET}; a browser will open to authenticate."

BEFORE_REFRESH_TOKEN=$(refresh_token)

python -m stjoseph "${@}"

AFTER_REFRESH_TOKEN=$(refresh_token)

# Only the refresh token matters to the scheduled job (access tokens expire within the hour):
if [ -n "${AFTER_REFRESH_TOKEN}" ] && [ "${AFTER_REFRESH_TOKEN}" != "${BEFORE_REFRESH_TOKEN}" ]; then
    echo gcloud secrets versions add "${TOKEN_SECRET}" --data-file=token.json
    gcloud secrets versions add "${TOKEN_SECRET}" --data-file=token.json
fi
