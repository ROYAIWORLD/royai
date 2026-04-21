#!/usr/bin/env bash
# RoyAI 플랫폼 프로세스 재시작. 사용: /Services/RoyAI_Platform/gs
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"
LOG="${ROYAI_RESTART_LOG:-/tmp/royai_platform.log}"

echo "[gs] RoyAI_Platform 재시작 (${ROOT})"

# cmdline이 ./venv/bin/python run_server.py 형태라 경로 기반 pkill이 안 맞는 경우가 많음 → cwd로 식별
kill_by_cwd() {
  local pid cwd
  for pid in $(pgrep -f "run_server\.py" 2>/dev/null || true); do
    cwd=$(readlink "/proc/${pid}/cwd" 2>/dev/null || sudo readlink "/proc/${pid}/cwd" 2>/dev/null || true)
    if [[ "$cwd" == "$ROOT" ]]; then
      echo "[gs] 종료 PID ${pid} (cwd=${cwd})"
      kill "$pid" 2>/dev/null || sudo kill "$pid" 2>/dev/null || true
    fi
  done
}

kill_by_cwd
sleep 1

if [[ "$(id -un)" == "roy" ]]; then
  nohup ./start_royai_platform.sh >>"$LOG" 2>&1 &
elif command -v sudo >/dev/null 2>&1; then
  sudo -u roy bash -lc "cd '$ROOT' && nohup ./start_royai_platform.sh >>'$LOG' 2>&1 &"
else
  nohup ./start_royai_platform.sh >>"$LOG" 2>&1 &
fi

echo "[gs] 기동 요청 완료. 로그: $LOG"
