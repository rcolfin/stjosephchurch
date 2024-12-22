#!/usr/bin/env bash

set -euo pipefail

PACKAGE_PATH=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )/.." &> /dev/null && pwd )

cd "${PACKAGE_PATH}" || { >&2 echo "Failed to cd to ${PACKAGE_PATH}."; exit 1; }

if [ ! -f credentials.json ] || [ ! -f token.json ]; then
    echo gcloud storage cp gs://st-joseph-4ed7624155de0493/*.json .
    gcloud storage cp gs://st-joseph-4ed7624155de0493/*.json .
fi

BEFORE_CREDENTIALS=$(echo 'import os;print(int(os.path.getmtime("credentials.json")))' | python -s)
BEFORE_TOKEN=$(echo 'import os;print(int(os.path.getmtime("token.json")))' | python -s)

python -m stjoseph "${@}"

AFTER_CREDENTIALS=$(echo 'import os;print(int(os.path.getmtime("credentials.json")))' | python -s)
AFTER_TOKEN=$(echo 'import os;print(int(os.path.getmtime("token.json")))' | python -s)

if [ "${AFTER_CREDENTIALS}" \> "${BEFORE_CREDENTIALS}" ]; then
    echo gcloud storage cp credentials.json gs://st-joseph-4ed7624155de0493/
    gcloud storage cp credentials.json gs://st-joseph-4ed7624155de0493/
fi

if [ "${AFTER_TOKEN}" \> "${BEFORE_TOKEN}" ]; then
    echo gcloud storage cp token.json gs://st-joseph-4ed7624155de0493/
    gcloud storage cp token.json gs://st-joseph-4ed7624155de0493/
fi
