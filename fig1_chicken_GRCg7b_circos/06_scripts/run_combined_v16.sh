#!/usr/bin/env bash
# V16：V15 Circos + 右侧四类 TE 结构示意；输出 07_figures/R_v16。
# 与 run_circos_R_v15.sh 同样的入口约定：任意工作目录可执行，参数原样透传。
set -euo pipefail
CIRCOS_SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
CIRCOS_PROJECT_DIR="$(cd -- "${CIRCOS_SCRIPT_DIR}/.." && pwd)"
CIRCOS_RSCRIPT="${CHICKEN_CIRCOS_RSCRIPT:-${R_BIN:-Rscript}}"
CIRCOS_LOG_DIR="${CIRCOS_PROJECT_DIR}/07_figures/R_v16"
CIRCOS_LOG="${CIRCOS_LOG_DIR}/run_v16.log"

if ! command -v "${CIRCOS_RSCRIPT}" >/dev/null 2>&1; then
  printf '找不到 Rscript：%s\n' "${CIRCOS_RSCRIPT}" >&2
  exit 127
fi

mkdir -p "${CIRCOS_LOG_DIR}"
{
  printf '# V16 combined figure — %s\n' "$(date '+%Y-%m-%dT%H:%M:%S%z')"
  printf '# command: bash 06_scripts/run_combined_v16.sh %s\n' "$*"
  printf '# R: %s\n' "$("${CIRCOS_RSCRIPT}" --version 2>&1 | head -1)"
  printf '# project: figures/fig1_chicken_GRCg7b_circos (resolved at runtime)\n' 
} > "${CIRCOS_LOG}"

set +e
"${CIRCOS_RSCRIPT}" --vanilla "${CIRCOS_SCRIPT_DIR}/plot_combined_te_callouts_v16.R" \
  --project-dir "${CIRCOS_PROJECT_DIR}" "$@" 2>&1 | tee -a "${CIRCOS_LOG}"
STATUS=${PIPESTATUS[0]}
set -e

if [ "${STATUS}" -ne 0 ]; then
  printf 'V16 渲染失败（exit %s），日志：%s\n' "${STATUS}" "${CIRCOS_LOG}" >&2
  exit "${STATUS}"
fi

# 出图后自动跑几何与完整性校验；没有 python3 时只提示、不失败。
if command -v python3 >/dev/null 2>&1; then
  python3 "${CIRCOS_SCRIPT_DIR}/check_combined_v16.py" --project-dir "${CIRCOS_PROJECT_DIR}" \
    2>&1 | tee -a "${CIRCOS_LOG}"
else
  printf '未找到 python3，跳过 check_combined_v16.py\n' | tee -a "${CIRCOS_LOG}"
fi
