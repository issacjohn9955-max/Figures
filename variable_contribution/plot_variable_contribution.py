#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
plot_variable_contribution.py — 复刻 "变量贡献 + 置换重要性" 双面板图（MaxEnt/ENM 常见版式）

版式 : A = 全部候选变量的贡献率排序柱状图 + 阈值虚线（默认 1%）
       B = 入选变量的贡献率柱（左轴）+ 第二指标折线（右轴），叠在 A 右上空白处
       参考 Yuan et al. 2026 Zoological Research Figure 2A/2B

输入 : variable_stats.tsv（compute_variable_stats.py 产出）
       variable/n_sig_loci/contribution_pct/selected/shapley_pct/permutation_pct

运行 : python3 plot_variable_contribution.py --input variable_stats.tsv \\
           --out variable_contribution --line perm
"""
import argparse
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Patch
import matplotlib.patheffects as pe

HERE = os.path.dirname(os.path.abspath(__file__))


def _find_style():
    """风格层查找顺序：$FIGURE_STYLE_DIR > 仓库自带 style/ > 并排的 figure-style/style"""
    cands = []
    env = os.environ.get("FIGURE_STYLE_DIR")
    if env:
        cands += [os.path.join(env, "style"), env]
    d = HERE
    for _ in range(6):
        cands += [os.path.join(d, "style"), os.path.join(d, "figure-style", "style")]
        d = os.path.dirname(d)
    for c in cands:
        if os.path.exists(os.path.join(c, "theme.json")):
            return c
    return None


STYLE = _find_style()

MM = 1 / 25.4
FIG_W, FIG_H = 183, 82          # mm, double-column


def load_style():
    if STYLE is None:            # 独立拷贝场景：用内联同款色值
        theme = {"colors": {"ink": "#273746", "emphasis_outline": "#253246"},
                 "marks": {"bar_edge_pt": 0.4}}
        pal = {"categorical": ["#386C8C", "#7BB6AC", "#9689B9", "#B4AD74",
                               "#5899B2", "#A1A8BE"],
               "accent": {"primary": "#E75A46"}}
        return theme, pal
    with open(os.path.join(STYLE, "theme.json")) as f:
        theme = json.load(f)
    with open(os.path.join(STYLE, "palettes.json")) as f:
        pall = json.load(f)
    return theme, pall["palettes"][pall["default"]]


GROUP_LABEL = {
    "temperature": "Temperature",
    "precipitation": "Precipitation",
    "terrain": "Terrain",
    "radiation_humidity": "Radiation / humidity",
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="variable_stats.tsv")
    ap.add_argument("--out", default="variable_contribution")
    ap.add_argument("--line", choices=["perm", "assoc"], default="perm",
                    help="面板 B 折线用置换重要性(perm)还是关联份额(assoc)")
    ap.add_argument("--threshold", type=float, default=1.0)
    ap.add_argument("--dpi", type=int, default=600)
    a = ap.parse_args()

    theme, pal = load_style()
    ink = theme["colors"]["ink"]
    cat = pal["categorical"]
    accent = pal["accent"]["primary"]
    grp_color = {"temperature": cat[0], "precipitation": cat[1],
                 "terrain": cat[3], "radiation_humidity": cat[2]}

    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "Liberation Sans", "DejaVu Sans"],
        "font.size": 7, "axes.labelsize": 7, "xtick.labelsize": 6,
        "ytick.labelsize": 6, "legend.fontsize": 5.6,
        "axes.linewidth": 0.55, "xtick.major.width": 0.55, "ytick.major.width": 0.55,
        "xtick.major.size": 2.4, "ytick.major.size": 2.4,
        "axes.edgecolor": ink, "text.color": ink,
        "xtick.color": ink, "ytick.color": ink, "axes.labelcolor": ink,
        "pdf.fonttype": 42, "ps.fonttype": 42, "axes.unicode_minus": False,
    })

    df = pd.read_csv(a.input, sep="\t", encoding="utf-8-sig")
    df = df.sort_values("contribution_pct", ascending=False).reset_index(drop=True)

    fig = plt.figure(figsize=(FIG_W * MM, FIG_H * MM), facecolor="white")

    # ================= 面板 A =================
    axA = fig.add_axes([0.062, 0.215, 0.923, 0.745])
    x = np.arange(len(df))
    axA.bar(x, df["contribution_pct"], width=0.72, color=cat[0],
            edgecolor=theme["colors"]["emphasis_outline"],
            linewidth=theme["marks"]["bar_edge_pt"], zorder=3)
    axA.axhline(a.threshold, color=accent, lw=0.7, ls=(0, (4, 2)), zorder=4)
    axA.text(len(df) - 0.4, a.threshold + 0.45, f"{a.threshold:g}% threshold",
             color=accent, fontsize=5.4, ha="right", va="bottom")

    axA.set_xlim(-0.7, len(df) - 0.3)
    axA.set_ylim(0, df["contribution_pct"].max() * 1.14)
    axA.set_xticks(x)
    axA.set_xticklabels(df["variable"], rotation=42, ha="right",
                        rotation_mode="anchor", fontsize=6)
    axA.set_ylabel("Contribution (%)", fontsize=7)
    axA.set_yticks(np.arange(0, 21, 5))

    # 进入面板 B 的 10 个核心变量：标签加粗（图注说明）
    core = set(np.where(df["selected"].astype(str).str.lower().isin(["true", "1"]))[0])
    for i, lab in enumerate(axA.get_xticklabels()):
        if i in core:
            lab.set_fontweight("bold")

    # ================= 面板 B =================
    sel = df[df["selected"].astype(str).str.lower().isin(["true", "1"])].copy()
    line_col = "permutation_pct" if a.line == "perm" else "contribution_pct"
    line_lab = ("Permutation importance (%)" if a.line == "perm"
                else "Significant TE loci (%)")
    sel = sel.sort_values(line_col, ascending=False).reset_index(drop=True)

    axB = fig.add_axes([0.540, 0.452, 0.400, 0.478], zorder=10)
    axB.set_facecolor("white")
    xb = np.arange(len(sel))
    axB.bar(xb, sel["shapley_pct"], width=0.76,
            color=[grp_color[g] for g in sel["group"]],
            edgecolor=theme["colors"]["emphasis_outline"],
            linewidth=theme["marks"]["bar_edge_pt"], zorder=3)
    top = sel["shapley_pct"].max()
    for xi, v in zip(xb, sel["shapley_pct"]):
        axB.text(xi, v - top * 0.045, f"{v:.1f}", ha="center", va="top",
                 fontsize=5.2, color="white", zorder=7)
    axB.set_ylim(0, top * 1.30)
    axB.set_xlim(-0.65, len(sel) - 0.35)
    axB.set_xticks(xb)
    axB.set_xticklabels(sel["variable"], rotation=42, ha="right",
                        rotation_mode="anchor", fontsize=5.9)
    axB.set_ylabel("Variable contribution (%)", fontsize=6.4)
    axB.set_yticks(np.arange(0, 13, 5))
    axB.tick_params(labelsize=5.6)

    axB2 = axB.twinx()
    axB2.plot(xb, sel[line_col], color=accent, lw=0.9, zorder=5,
              marker="o", markersize=2.6, markerfacecolor=cat[5],
              markeredgecolor="white", markeredgewidth=0.35)
    axB2.set_ylim(0, sel[line_col].max() * 1.22)
    axB2.set_ylabel(line_lab, fontsize=6.4, rotation=270, labelpad=9)
    axB2.tick_params(labelsize=5.6, length=2.0, width=0.5)
    axB2.spines["top"].set_visible(False)

    for ax in (axA, axB):
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

    # 说明块（替代原图的 Feature Class / Regularization Multiplier）
    axB.text(0.015, 0.985, "Model: partial RDA, 10 variables\n"
                           "Conditioned on space + 3 TE-PC axes",
             transform=axB.transAxes, ha="left", va="top",
             fontsize=5.4, color=ink, linespacing=1.45, zorder=12)

    handles = [Patch(facecolor=grp_color[g], edgecolor=theme["colors"]["emphasis_outline"],
                     linewidth=0.3, label=GROUP_LABEL[g])
               for g in ["temperature", "precipitation", "terrain", "radiation_humidity"]
               if g in set(sel["group"])]
    axB.legend(handles=handles, loc="upper right", bbox_to_anchor=(1.0, 1.02),
               frameon=False, handlelength=0.9, handleheight=0.7,
               labelspacing=0.25, borderpad=0.1, fontsize=5.0)

    fig.text(0.010, 0.945, "A", fontsize=9, fontweight="bold", color=ink)
    fig.text(0.497, 0.945, "B", fontsize=9, fontweight="bold", color=ink)

    for ext in ("png", "pdf"):
        fig.savefig(f"{a.out}.{ext}", dpi=a.dpi, facecolor="white",
                    bbox_inches=None)
    print(f"[done] {a.out}.png / .pdf  ({FIG_W}×{FIG_H} mm)")


if __name__ == "__main__":
    main()
