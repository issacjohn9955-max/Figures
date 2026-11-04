#!/usr/bin/env bash
# =============================================================================
# sync_from_figure_style.sh —— 把 figure-style/style 的快照同步进本仓库
#
#   bash style/sync_from_figure_style.sh            # 覆盖快照并更新 VENDORED.md
#   bash style/sync_from_figure_style.sh --check    # 只比对；有差异 exit 1
#   SOURCE=/path/to/figure-style bash style/sync_from_figure_style.sh
#
# 快照是"只读副本"：本仓库里的图全部读这份，所以源仓库改动后必须显式同步一次，
# 并重跑受影响的图，避免出现"规范改了、图没改"的漂移。
# =============================================================================
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(dirname "$HERE")"
SOURCE="${SOURCE:-$(dirname "$REPO")/figure-style}"
FILES=(theme.json palettes.json ggplot2_theme.R matplotlib.mplstyle)
MODE="${1:-sync}"

if [ ! -f "$SOURCE/style/theme.json" ]; then
  echo "[x] 找不到源风格层：$SOURCE/style/theme.json" >&2
  echo "    用 SOURCE=/path/to/figure-style 指定，或先 clone figure-style。" >&2
  exit 2
fi

drift=0
for f in "${FILES[@]}"; do
  if ! cmp -s "$SOURCE/style/$f" "$HERE/$f"; then
    drift=1
    echo "[!] 与源不一致：style/$f"
  fi
done

if [ "$MODE" = "--check" ]; then
  if [ "$drift" -eq 0 ]; then
    echo "[ok] 快照与 $SOURCE 一致"
    exit 0
  fi
  echo "[x] 快照落后于源仓库，请运行：bash style/sync_from_figure_style.sh" >&2
  exit 1
fi

for f in "${FILES[@]}"; do
  cp "$SOURCE/style/$f" "$HERE/$f"
done

COMMIT="$(git -C "$SOURCE" rev-parse --short HEAD 2>/dev/null || echo 'unknown')"
# 记录来源时不要写死个人绝对路径：并排 checkout 记成 ../figure-style
if [ "$(cd "$SOURCE" && pwd)" = "$(cd "$(dirname "$REPO")/figure-style" 2>/dev/null && pwd)" ]; then
  SOURCE_DESC="../figure-style（本机并排 checkout）"
else
  SOURCE_DESC="$SOURCE"
fi
{
  echo "# 快照来源记录"
  echo
  echo "| 字段 | 值 |"
  echo "|---|---|"
  echo "| 源仓库 | \`$SOURCE_DESC\` |"
  echo "| 源 commit | \`$COMMIT\` |"
  echo "| 同步时间 | $(date '+%Y-%m-%d %H:%M:%S %z') |"
  echo "| 文件 | ${FILES[*]} |"
  echo "| 同步命令 | \`bash style/sync_from_figure_style.sh\` |"
} > "$HERE/VENDORED.md"

echo "[done] 已从 $SOURCE（commit $COMMIT）同步 ${#FILES[@]} 个文件，并更新 VENDORED.md"
echo "[i] 记得重跑受影响的图，确认成品与新的字号/配色一致"
