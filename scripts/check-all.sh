#!/usr/bin/env bash

# Checks all the Python packages.

SCRIPT_PATH=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
SCRIPT_NAME=$( basename "${BASH_SOURCE[0]}" )
PYTHON_ROOT_PATH=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )/.." &> /dev/null && pwd )

if ! command -v "poetry" &> /dev/null; then
    exec "${SCRIPT_PATH}/console.sh" "${SCRIPT_PATH}/${SCRIPT_NAME}"
fi

# shellcheck disable=SC2207
PACKAGE_PATHS=($(find "${PYTHON_ROOT_PATH}" -name "pyproject.toml" -exec dirname {} \;))
FAILED=()

for PACKAGE_PATH in "${PACKAGE_PATHS[@]}"; do
    PACKAGE_NAME=$(basename "${PACKAGE_PATH}")
    pushd "${PACKAGE_PATH}" >/dev/null ||  { FAILED+=("${PACKAGE_NAME}"); continue; }
    poetry run "${SCRIPT_PATH}/check.sh" || { FAILED+=("${PACKAGE_NAME}"); }
    popd >/dev/null || { continue; }
done

if [ ${#FAILED[@]} -gt 0 ]; then
    >&2 echo "The following packages failed to be checked: ${FAILED[*]}"
    exit 1
fi