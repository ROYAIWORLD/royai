#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

if [[ "${RUN_AS_ROY_CHECK:-1}" == "1" ]] && [[ "$(id -un)" != "roy" ]]; then
  echo "[RoyAI_Platform] 경고: 현재 사용자는 'roy'가 아닙니다. 배포 시 roy로 실행하는 것을 권장합니다." >&2
fi

if [[ ! -d venv ]]; then
  python3 -m venv venv
  ./venv/bin/pip install -U pip wheel
  ./venv/bin/pip install -r requirements.txt
fi

export BIND="${BIND:-127.0.0.1}"
export PORT="${PORT:-9120}"
exec ./venv/bin/python run_server.py
