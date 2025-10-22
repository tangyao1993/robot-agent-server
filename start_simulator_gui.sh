#!/usr/bin/env bash
set -euo pipefail

ENV_NAME="robot"

if ! command -v conda >/dev/null 2>&1; then
  echo "错误: 未检测到 conda，可先安装 Anaconda 或 Miniconda。" >&2
  exit 1
fi

eval "$(conda shell.bash hook)"
conda activate "$ENV_NAME"

python -m simulator.main --gui --auto-connect "$@"
