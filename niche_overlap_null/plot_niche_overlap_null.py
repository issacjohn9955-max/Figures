#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""plot_niche_overlap_null.py —— 复刻 Figure 2J 版式：零分布直方图 + 观测值虚线

一个面板 = 一个环境变量：
  * 青色 / 黄色 两组柱状图 = 100 次置换得到的零分布（Schoener's D / Hellinger's I）
  * 青色点划线 / 黄色虚线 = 实际观测到的 D / I（极端高 vs 极端低组）
  * 轴底倒三角 = 观测值（和虚线同色）
  * 左上角 D = … / I = … 文本 = 观测值数值

输入（都是 compute_te_overlap.py 的输出，也可以直接喂 ENMTools 的结果）：
  --null      variable  metric  replicate  value      (metric ∈ {D, I})
  --observed  variable  D_obs   I_obs                (其余列忽略)

用法：
  python3 plot_niche_overlap_null.py --null data/null_distributions.tsv \\
          --observed data/observed_overlap.tsv --out niche_overlap_null

依赖：numpy + matplotlib。
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.ticker import MaxNLocator, FormatStrFormatter

# 取自原图（Figure 2J）的像素色值
C_D = "#00C6CE"      # Schoener's D（青）
C_I = "#F4C901"      # Hellinger's I（黄）
INK = "#111111"

FONT = "Arial"


def setup_style() -> None:
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": [FONT, "Helvetica", "DejaVu Sans"],
        "font.size": 7,
        "axes.linewidth": 0.9,
        "axes.edgecolor": INK,
        "axes.labelcolor": INK,
        "axes.labelweight": "bold",
        "axes.titleweight": "bold",
        "xtick.color": INK,
        "ytick.color": INK,
        "xtick.direction": "out",
        "ytick.direction": "out",
        "xtick.major.size": 2.6,
        "ytick.major.size": 2.6,
        "xtick.major.width": 0.9,
        "ytick.major.width": 0.9,
        "xtick.labelsize": 6.5,
        "ytick.labelsize": 6.5,
        "legend.frameon": False,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "svg.fonttype": "none",
    })


def load(null_path: Path, obs_path: Path, order: str) -> tuple[pd.DataFrame, pd.DataFrame, list[str]]:
    null = pd.read_csv(null_path, sep="\t")
    obs = pd.read_csv(obs_path, sep="\t")
    need = {"variable", "metric", "value"}
    if not need.issubset(null.columns):
        raise SystemExit(f"--null 至少需要 {sorted(need)} 这几列。")
    if not {"variable", "D_obs", "I_obs"}.issubset(obs.columns):
        raise SystemExit("--observed 至少需要 variable / D_obs / I_obs 三列。")

    if order == "obs":
        variables = obs.sort_values("D_obs")["variable"].tolist()
    elif order == "file":
        variables = obs["variable"].tolist()
    else:                                     # 用户自定义顺序：逗号分隔
        variables = [v.strip() for v in order.split(",") if v.strip()]
    missing = set(variables) - set(null["variable"])
    if missing:
        raise SystemExit(f"--null 里缺少这些变量：{sorted(missing)}")
    return null, obs.set_index("variable"), variables


def fmt_ticks(ax) -> None:
    """x 轴按数据范围自动选 3~4 个刻度，统一两位小数。"""
    ax.xaxis.set_major_locator(MaxNLocator(nbins=4))
    ax.xaxis.set_major_formatter(FormatStrFormatter("%.2f"))
    ax.yaxis.set_major_locator(MaxNLocator(nbins=4, integer=True))


def draw_panel(ax, var: str, d_null: np.ndarray, i_null: np.ndarray,
               d_obs: float, i_obs: float, bins: int, tag_title: bool,
               edges: np.ndarray | None = None, labels: dict | None = None) -> None:
    labels = labels or {}
    xlabel = labels.get("xlabel", "Identity index")
    ylabel = labels.get("ylabel", "Count")
    legend_d = labels.get("legend_d", r"Schoener's $\mathit{D}$")
    legend_i = labels.get("legend_i", r"Hellinger's $\mathit{I}$")
    lo = min(d_null.min(), i_null.min(), d_obs, i_obs)
    hi = max(d_null.max(), i_null.max(), d_obs, i_obs)
    span = hi - lo if hi > lo else 0.02
    # 左边留出 30% 的空槽放 D = / I = 文本（原图也是左边大片留白）
    xlo = 0.0 if lo < 0.06 else lo - 0.36 * span
    xhi = hi + 0.03 * span

    if edges is None:
        edges = np.linspace(lo - 0.02 * (hi - lo), hi + 0.02 * (hi - lo), bins + 1)
    ax.hist(d_null, bins=edges, color=C_D, edgecolor="none", zorder=2)
    ax.hist(i_null, bins=edges, color=C_I, edgecolor="none", zorder=3, alpha=0.95)

    # 观测值：虚线 + 轴底倒三角
    ax.vlines(d_obs, 0, 0.94, colors=C_D, linestyles=(0, (4, 1.2, 1, 1.2)),
              linewidth=1.15, zorder=4, transform=ax.get_xaxis_transform())
    ax.vlines(i_obs, 0, 0.94, colors=C_I, linestyles="--",
              linewidth=1.3, zorder=4, transform=ax.get_xaxis_transform())
    ax.plot([d_obs], [0], marker="v", markersize=4.6, color=C_D,
            clip_on=False, zorder=6, transform=ax.get_xaxis_transform())
    ax.plot([i_obs], [0], marker="v", markersize=4.6, color=C_I,
            clip_on=False, zorder=6, transform=ax.get_xaxis_transform())

    top = ax.get_ylim()[1]
    ax.set_ylim(0, top * 1.62)

    # 左上角数值
    ax.text(0.02, 0.965, f"D = {d_obs:.2f}", transform=ax.transAxes,
            ha="left", va="top", color=C_D, fontsize=7, fontweight="bold")
    ax.text(0.02, 0.845, f"I = {i_obs:.2f}", transform=ax.transAxes,
            ha="left", va="top", color=C_I, fontsize=7, fontweight="bold")

    # 图例
    handles = [
        Patch(facecolor=C_D, edgecolor="none", label=legend_d),
        Patch(facecolor=C_I, edgecolor="none", label=legend_i),
    ]
    leg = ax.legend(handles=handles, loc="upper right", bbox_to_anchor=(1.0, 1.03),
                    ncol=2, frameon=True, facecolor="white", edgecolor="none",
                    framealpha=1.0, handlelength=0.85, handleheight=0.85,
                    handletextpad=0.35, columnspacing=0.9, borderaxespad=0.0,
                    fontsize=6.3)
    for txt in leg.get_texts():
        txt.set_fontweight("bold")

    ax.set_xlim(xlo, xhi)
    fmt_ticks(ax)
    for lbl in ax.get_xticklabels() + ax.get_yticklabels():
        lbl.set_fontweight("bold")
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.set_ylabel(ylabel, fontsize=7, fontweight="bold", labelpad=3)
    ax.set_xlabel(xlabel, fontsize=7, fontweight="bold", labelpad=2)
    if tag_title:
        ax.set_title(var.upper(), loc="left", fontsize=8, fontweight="bold", pad=5)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--null", required=True, type=Path)
    ap.add_argument("--observed", required=True, type=Path)
    ap.add_argument("--out", default="niche_overlap_null", type=Path)
    ap.add_argument("--ncol", type=int, default=2)
    ap.add_argument("--bins", type=int, default=22)
    ap.add_argument("--binsize", type=float, default=None,
                    help="固定柱宽（数据单位）；不给就按面板范围自动分 --bins 个柱")
    ap.add_argument("--order", default="obs",
                    help="面板顺序：obs=D 从低到高，file=输入顺序，或逗号分隔变量名")
    ap.add_argument("--tag", default="J", help="整图左上角的面板字母，空串则不画")
    ap.add_argument("--width", type=float, default=6.4)
    ap.add_argument("--row-height", type=float, default=1.90)
    ap.add_argument("--dpi", type=int, default=600)
    ap.add_argument("--xlabel", default="Identity index", help="x 轴标题")
    ap.add_argument("--ylabel", default="Count", help="y 轴标题")
    ap.add_argument("--legend-d", default=r"Schoener's $\mathit{D}$",
                    help="青色指标在图例里的名字（可写 mathtext）")
    ap.add_argument("--legend-i", default=r"Hellinger's $\mathit{I}$",
                    help="黄色指标在图例里的名字（可写 mathtext）")
    args = ap.parse_args()

    setup_style()
    null, obs, variables = load(args.null, args.observed, args.order)

    nrow = int(np.ceil(len(variables) / args.ncol))
    fig = plt.figure(figsize=(args.width, nrow * args.row_height + 0.55))
    gs = fig.add_gridspec(nrow, args.ncol, left=0.105, right=0.985,
                          top=1 - 0.42 / fig.get_figheight(),
                          bottom=0.30 / fig.get_figheight(),
                          wspace=0.28, hspace=0.62)

    for k, var in enumerate(variables):
        ax = fig.add_subplot(gs[k // args.ncol, k % args.ncol])
        sub = null[null["variable"] == var]
        d_null = sub.loc[sub["metric"] == "D", "value"].to_numpy()
        i_null = sub.loc[sub["metric"] == "I", "value"].to_numpy()
        row = obs.loc[var]
        edges = None
        if args.binsize:
            lo = min(d_null.min(), i_null.min(), row["D_obs"], row["I_obs"])
            hi = max(d_null.max(), i_null.max(), row["D_obs"], row["I_obs"])
            edges = np.arange(lo, hi + args.binsize, args.binsize)
        draw_panel(ax, var, d_null, i_null, float(row["D_obs"]), float(row["I_obs"]),
                   args.bins, tag_title=True, edges=edges,
                   labels=dict(xlabel=args.xlabel, ylabel=args.ylabel,
                               legend_d=args.legend_d, legend_i=args.legend_i))

    if args.tag:
        fig.text(0.012, 1 - 0.06 / fig.get_figheight(), args.tag,
                 fontsize=17, fontweight="bold", ha="left", va="top")

    stem = Path(args.out)
    stem.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(stem.with_suffix(".pdf"))
    fig.savefig(stem.with_suffix(".png"), dpi=args.dpi, facecolor="white")
    print(f"写出 -> {stem}.pdf / {stem}.png")


if __name__ == "__main__":
    main()
