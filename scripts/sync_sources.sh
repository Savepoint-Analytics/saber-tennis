#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
export PYTHONPATH="${REPO_ROOT}/src${PYTHONPATH:+:${PYTHONPATH}}"

PYTHON_BIN="${PYTHON_BIN:-$(command -v python3 || command -v python)}"
"${PYTHON_BIN}" -m tennis_sabermetrics.cli sync-sources "$@"
