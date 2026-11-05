#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Self-check: rebuild every figure from the inputs committed next to it, then
# compare the new PNG with the one already in the repository.
#
#   bash run_all.sh              # 全部跑；产物与日志在 outputs/ 下
#   bash run_all.sh polar        # 只跑名字里含 polar 的模块
#
# 每个模块在 outputs/<name>/work/ 里的副本中运行，仓库自己的文件不会被改动。
# 退出码 0 = 全部通过（skip 不算失败）；1 = 有模块失败或重渲染结果与已提交图不一致。
# ---------------------------------------------------------------------------
set -u
ROOT=$(cd "$(dirname "$0")" && pwd)
OUT="$ROOT/outputs"
FILTER="${1:-}"
mkdir -p "$OUT"

ok=(); fail=(); skip=()
say()   { printf '%s\n' "$*"; }
head2() { printf '\n=== %s\n' "$*"; }
have_r()  { Rscript -e "q(status=ifelse(requireNamespace('$1', quietly=TRUE),0,1))" >/dev/null 2>&1; }
have_py() { python3 -c "import $1" >/dev/null 2>&1; }

# 比对新旧 PNG：输出平均绝对差（%），<1% 视为一致
compare() {
  python3 - "$1" "$2" <<'PY' 2>/dev/null
import sys
try:
    from PIL import Image, ImageChops
    import numpy as np
except Exception:
    sys.exit(3)
a, b = (Image.open(p).convert("RGB") for p in sys.argv[1:3])
if a.size != b.size:
    b = b.resize(a.size)
d = np.asarray(ImageChops.difference(a, b)).astype(float).mean() / 255 * 100
print(f"{d:.2f}")
sys.exit(0 if d < 1.0 else 1)
PY
}

record() { case "$1" in ok) ok+=("$2") ;; fail) fail+=("$2");; skip) skip+=("$2");; esac; say "  [$1] $2  $3"; }

# run_module <name> <module dir> <exported png basenames...> -- <command...>
run_module() {
  local name="$1" dir="$2"; shift 2
  local exports=()
  while [[ $# -gt 0 && "$1" != "--" ]]; do exports+=("$1"); shift; done
  shift || true
  [[ -n "$FILTER" && "$name" != *"$FILTER"* ]] && return 0

  head2 "$name"
  local work="$OUT/$name"
  rm -rf "$work"; mkdir -p "$work"
  cp -R "$ROOT/$dir" "$work/work"

  ( cd "$work/work" && "$@" ) > "$work/render.log" 2>&1
  if [[ $? -ne 0 ]]; then
    local err; err=$(grep -iE 'error|no package|missing|not found|无法' "$work/render.log" | head -2 | tr '\n' ' ')
    record fail "$name" "${err:-见 $work/render.log}"
    return 0
  fi

  local drifted="" missing=""
  for f in "${exports[@]}"; do
    if [[ ! -f "$work/work/$f" ]]; then missing="$missing $f"; continue; fi
    local d; d=$(compare "$ROOT/$dir/$f" "$work/work/$f"); local rc=$?
    case $rc in
      0) : ;;
      1) drifted="$drifted $f(${d}%)" ;;
      *) : ;;   # 3 = 没有 PIL，跳过像素比对
    esac
  done

  if [[ -n "$missing" ]]; then
    record fail "$name" "没有生成:$missing"
  elif [[ -n "$drifted" ]]; then
    record fail "$name" "与已提交的图不一致:$drifted"
  else
    record ok "$name" "重渲染一致"
  fi
}

# --- 1. china_sampling_map（需要 curl 下载的边界数据）----------------------
if [[ -f "$ROOT/china_sampling_map/data/china_provinces.geojson" ]]; then
  run_module china_map china_sampling_map fig1_province_counts.png -- \
    python3 plot_china_sampling_map.py --lang en
  run_module china_points china_sampling_map fig2_sampling_sites.png -- \
    python3 plot_china_sampling_points.py
  run_module china_points_labelled china_sampling_map fig3_sampling_sites_labelled.png -- \
    python3 plot_china_sampling_labelled.py
else
  if [[ -z "$FILTER" || "china" == *"$FILTER"* ]]; then
    head2 "china_sampling_map"; say "  [skip] 缺 data/china_provinces.geojson（README「Boundary data」里的 curl 命令）"
    record skip china_sampling_map "缺边界数据"
  fi
fi

# --- 2. corr_ci_scatter ----------------------------------------------------
run_module corr_ci_scatter corr_ci_scatter corr_ci_scatter.png -- \
  Rscript plot_corr_ci_panel.R --input te_method_corr.tsv --out corr_ci_scatter \
    --xlab '~bold("|"*italic(z)[RDA]*"|")' --ylab '~bold("|"*rho*"|")'

# --- 3. gea_driver_radar ---------------------------------------------------
run_module gea_driver_radar_te gea_driver_radar radar_chickente_te.png -- \
  Rscript plot_radar_drivers.R --input chickente_te_counts.tsv --out radar_chickente_te \
    --ymax 3200 --breaks 0,1600,3200
run_module gea_driver_radar_paper gea_driver_radar radar_paper_fig3c.png -- \
  Rscript plot_radar_drivers.R --input example_paper_fig3c.tsv --out radar_paper_fig3c \
    --ymax 3200 --breaks 0,1600,3200 --tag C

# --- 4. gea_marginal_scatter（唯一需要 patchwork 的模块）-------------------
if have_r patchwork; then
  run_module gea_marginal_scatter gea_marginal_scatter gea_marginal_scatter.png -- \
    Rscript plot_gea_panels.R --input example_gea_stats.tsv --labels example_labels.tsv \
      --out gea_marginal_scatter
else
  if [[ -z "$FILTER" || "marginal" == *"$FILTER"* ]]; then
    head2 "gea_marginal_scatter"
    say "  [skip] 缺 R 包 patchwork：Rscript -e 'install.packages(\"patchwork\")'"
    record skip gea_marginal_scatter "缺 R 包 patchwork"
  fi
fi

# --- 5. niche_overlap_null -------------------------------------------------
if have_py matplotlib && have_py pandas; then
  run_module niche_overlap_null niche_overlap_null niche_overlap_null.png -- \
    python3 plot_niche_overlap_null.py --null data/null_distributions.tsv \
      --observed data/observed_overlap.tsv --out niche_overlap_null
else
  head2 "niche_overlap_null"; say "  [skip] 缺 python 包 matplotlib/pandas"
  record skip niche_overlap_null "缺 python 包"
fi

# --- 6. pca_climate_zone ---------------------------------------------------
run_module pca_climate_zone pca_climate_zone fig_pca_te_climate.png fig_pca_snp_climate.png -- \
  bash -c 'Rscript plot_pca_climate_zone.R --scores data/pca_te_scores.tsv --variance data/pca_te_variance.tsv --out fig_pca_te_climate --palette chromatic_nc --tag B --width-mm 160 --height-mm 111 &&
           Rscript plot_pca_climate_zone.R --scores data/pca_snp_scores.tsv --variance data/pca_snp_variance.tsv --out fig_pca_snp_climate --palette chromatic_nc --tag B --width-mm 160 --height-mm 111'

# --- 7. te_ibe_adaptive_neutral -------------------------------------------
run_module te_ibe_adaptive_neutral te_ibe_adaptive_neutral te_ibe_adaptive_neutral.png -- \
  Rscript te_ibe_mantel.R --freq input/cn14_group_freq.csv.gz --het input/cn14_group_het.csv.gz \
    --groups-file input/cn14_groups.tsv --adaptive-file input/adaptive_loci_lfmm_q05.txt --outdir .

# --- 8. te_factor_polar ----------------------------------------------------
run_module te_factor_polar te_factor_polar te_factor_polar.png -- \
  Rscript plot_polar_shared.R --input te_factor_shared_unique_core.tsv --out te_factor_polar \
    --ymax 500 --breaks 0,100,200,300,400,500 --tag B --width 84 --height 80
run_module te_factor_polar_all7 te_factor_polar te_factor_polar_all7.png -- \
  Rscript plot_polar_shared.R --input te_factor_shared_unique.tsv --out te_factor_polar_all7 \
    --ymax 500 --breaks 0,100,200,300,400,500 --tag B --width 84 --height 80
run_module te_factor_polar_demo te_factor_polar demo_paper_style.png -- \
  Rscript plot_polar_shared.R --input example_paper_figB.tsv --out demo_paper_style \
    --ymax 340 --breaks 0,100,200,300 --tag B --width 84 --height 80

# --- 9. variable_contribution ----------------------------------------------
run_module variable_contribution variable_contribution variable_contribution.png -- \
  python3 plot_variable_contribution.py --input variable_stats.tsv \
    --out variable_contribution --line perm

# --- 10. world_distribution_map ---------------------------------------------
if have_py matplotlib; then
  run_module world_distribution_map world_distribution_map fig_world_distribution.png -- \
    python3 plot_world_distribution_map.py
  run_module world_distribution_map_relief world_distribution_map fig_world_distribution_relief.png -- \
    python3 plot_world_distribution_map.py --relief data/relief/NE1_50M_SR_W.jpg \
      --stem fig_world_distribution_relief
else
  head2 "world_distribution_map"; say "  [skip] 缺 python 包 matplotlib"
  record skip world_distribution_map "缺 python 包"
fi

# --- summary ---------------------------------------------------------------
say ""
say "----------------------------------------------------------------"
say "ok ${#ok[@]}   fail ${#fail[@]}   skip ${#skip[@]}"
for x in "${fail[@]:-}"; do [[ -n "$x" ]] && say "  FAIL $x"; done
for x in "${skip[@]:-}"; do [[ -n "$x" ]] && say "  SKIP $x"; done
say "产物与日志：$OUT"
[[ ${#fail[@]} -eq 0 ]] && exit 0 || exit 1
