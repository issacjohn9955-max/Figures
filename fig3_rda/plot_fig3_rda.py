#!/usr/bin/env python3
"""Figure 3 - redundancy analysis of TE composition against climate.

A  variance captured by each constrained axis (+ permutation p)
B  RDA triplot: 20 breed groups, 5 climate arrows
C  variable x axis correlation matrix

Usage
-----
python3 plot_fig3_rda.py --data-dir data --out fig3_rda
"""
import argparse
import csv
import os
import re

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib.lines import Line2D

MM = 1 / 25.4
INK = "#1B2430"
GREY = "#6B7280"

CAT_COLOUR = {"local": "#0072B2", "commercial": "#D55E00", "junglefowl": "#009E73"}
CAT_LABEL = {"local": "Chinese local breed", "commercial": "Commercial line",
             "junglefowl": "Wild junglefowl"}
JUNGLE = {"绿原鸡", "灰原鸡", "锡兰原鸡"}
COMMERCIAL = {"白来航", "洛岛红", "Corish", "Cobb", "Ross"}

COUNT = {"惠阳胡须鸡": 6, "白耳黄鸡": 6, "济宁百日鸡": 6, "绿原鸡": 20, "白来航": 29,
         "胡须鸡": 20, "林甸鸡": 6, "溧阳鸡": 6, "清远麻鸡": 20, "洛岛红": 31,
         "广西三黄鸡": 10, "Corish": 5, "灰原鸡": 8, "锡兰原鸡": 10, "吐鲁番斗鸡": 6,
         "文昌鸡": 24, "杏花鸡": 14, "仙居鸡": 6, "广西瑶鸡": 10, "郧阳大鸡": 6}


def parse_summary(path):
    txt = open(path, encoding="utf-8").read()
    axes = []
    for m in re.finditer(r"(RDA\d):\s*特征值占总方差\s*([\d.]+),\s*置换p=([\d.]+)\s*(\*?显著)?", txt):
        axes.append({"axis": m.group(1), "var": float(m.group(2)), "p": float(m.group(3))})
    corr = {}
    block = txt.split("气候变量 × 轴 相关")[1]
    for line in block.splitlines()[2:]:
        parts = line.split()
        if len(parts) == 6 and re.match(r"^[A-Za-z]+[0-9]*$", parts[0]):
            corr[parts[0]] = [float(x) for x in parts[1:]]
    total = re.search(r"总约束解释比例:\s*([\d.]+)", txt)
    fp = re.search(r"伪F=([\d.]+),\s*permutation p=([\d.]+)", txt)
    return axes, corr, float(total.group(1)) if total else None, (float(fp.group(1)), float(fp.group(2))) if fp else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default="data")
    ap.add_argument("--out", default="fig3_rda")
    ap.add_argument("--dpi", type=int, default=600)
    args = ap.parse_args()

    axes, corr, total, fp = parse_summary(os.path.join(args.data_dir, "rda_summary.txt"))
    with open(os.path.join(args.data_dir, "rda_sample_scores.csv"), encoding="utf-8-sig") as fh:
        sites = list(csv.DictReader(fh))

    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Hiragino Sans GB", "Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"],
        "pdf.fonttype": 42,
        "axes.unicode_minus": False,
    })

    fig = plt.figure(figsize=(178 * MM, 116 * MM))
    gs = GridSpec(2, 2, figure=fig, width_ratios=[0.40, 0.60],
                  height_ratios=[0.42, 0.58], hspace=0.52, wspace=0.28,
                  left=0.085, right=0.98, top=0.90, bottom=0.10)

    # ------------------------------------------------------------ A: axes
    axA = fig.add_subplot(gs[0, 0])
    labs = [a["axis"] for a in axes]
    vals = [a["var"] * 100 for a in axes]
    axA.bar(range(len(vals)), vals, color="#4C6E9C", width=0.68, zorder=3)
    for i, a in enumerate(axes):
        star = "***" if a["p"] <= 0.001 else "**" if a["p"] <= 0.01 else "*"
        axA.text(i, vals[i] + 0.4, star, ha="center", va="bottom", fontsize=5.6, color=INK)
    axA.set_xticks(range(len(labs)))
    axA.set_xticklabels(labs, fontsize=5.6)
    axA.set_ylabel("Variance explained (%)", fontsize=6.2)
    axA.tick_params(labelsize=5.6, width=0.6, length=2.4, pad=1.6)
    for s in ("top", "right"):
        axA.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        axA.spines[s].set_linewidth(0.7)
    axA.set_axisbelow(True)
    axA.yaxis.grid(True, color="#EDEFF2", lw=0.5)
    axA.set_ylim(0, max(vals) * 1.30)
    axA.text(-0.20, 1.06, "A", transform=axA.transAxes, fontsize=9.5, fontweight="bold")
    axA.text(0.98, 0.93, f"total constrained {total*100:.1f}%\nF = {fp[0]:.2f}, p = {fp[1]:.3f}",
             transform=axA.transAxes, fontsize=4.9, color=GREY, va="top", ha="right")

    # ------------------------------------------------------------ C: heatmap
    axC = fig.add_subplot(gs[1, 0])
    vars_ = ["bio3", "bio15", "bio18", "wind", "srad"]
    M = np.array([corr[v] for v in vars_])
    vmax = np.abs(M).max()
    im = axC.imshow(M, cmap="RdBu_r", vmin=-vmax, vmax=vmax, aspect="auto")
    axC.set_xticks(range(M.shape[1]))
    axC.set_xticklabels([a["axis"] for a in axes], fontsize=5.4)
    axC.set_yticks(range(M.shape[0]))
    axC.set_yticklabels(vars_, fontsize=5.4)
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            axC.text(j, i, f"{M[i, j]:.2f}", ha="center", va="center", fontsize=4.6,
                     color="white" if abs(M[i, j]) > 0.55 * vmax else INK)
    axC.tick_params(width=0.5, length=2.0, pad=1.4)
    for s in axC.spines.values():
        s.set_linewidth(0.6)
    axC.set_xlabel("Constrained axis", fontsize=6.0, labelpad=2)
    axC.text(-0.20, 1.06, "C", transform=axC.transAxes, fontsize=9.5, fontweight="bold")
    cb = fig.colorbar(im, ax=axC, fraction=0.045, pad=0.03)
    cb.ax.tick_params(labelsize=5.0, width=0.5, length=1.8)
    cb.outline.set_linewidth(0.5)
    cb.set_label("correlation", fontsize=5.4)

    # ------------------------------------------------------------ B: triplot
    axB = fig.add_subplot(gs[:, 1])
    x = np.array([float(s["RDA1"]) for s in sites])
    y = np.array([float(s["RDA2"]) for s in sites])
    names = [s["breed"] for s in sites]
    cats = ["junglefowl" if n in JUNGLE else "commercial" if n in COMMERCIAL else "local"
            for n in names]
    sizes = np.array([COUNT.get(n, 6) for n in names], dtype=float)
    sizes = 18 + (sizes - sizes.min()) / (sizes.max() - sizes.min()) * 90

    for cat in ("local", "commercial", "junglefowl"):
        m = [i for i, c in enumerate(cats) if c == cat]
        if not m:
            continue
        axB.scatter(x[m], y[m], s=sizes[m], c=CAT_COLOUR[cat], edgecolors="white",
                    linewidths=0.5, alpha=0.92, zorder=4)

    lim = max(np.abs(x).max(), np.abs(y).max()) * 1.25
    axB.set_xlim(-lim, lim)
    axB.set_ylim(-lim, lim)
    axB.axhline(0, color="#C9D0D8", lw=0.5, zorder=1)
    axB.axvline(0, color="#C9D0D8", lw=0.5, zorder=1)

    corr_mat = np.array([corr[v] for v in vars_])
    scale = 0.52 * lim / np.abs(corr_mat[:, :2]).max()
    for i, v in enumerate(vars_):
        dx, dy = corr_mat[i, 0] * scale, corr_mat[i, 1] * scale
        axB.annotate("", xy=(dx, dy), xytext=(0, 0),
                     arrowprops=dict(arrowstyle="-|>", lw=0.9, color="#8C3B2E",
                                     shrinkA=0, shrinkB=0, mutation_scale=7), zorder=5)
        axB.text(dx * 1.09, dy * 1.09, v, fontsize=5.6, color="#8C3B2E",
                 ha="center", va="center", zorder=6)

    order = np.argsort(-np.hypot(x, y))[:6]
    for k, i in enumerate(order):
        side = 1 if k % 2 == 0 else -1
        axB.annotate(names[i], (x[i], y[i]), xytext=(6 * side, 5), textcoords="offset points",
                     fontsize=4.8, color=INK, zorder=7, ha="left" if side > 0 else "right",
                     bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="none", alpha=0.75))

    axB.set_xlabel(f"RDA1 ({axes[0]['var']*100:.1f}%)", fontsize=6.4)
    axB.set_ylabel(f"RDA2 ({axes[1]['var']*100:.1f}%)", fontsize=6.4)
    axB.tick_params(labelsize=5.6, width=0.6, length=2.4, pad=1.8)
    for s in ("top", "right"):
        axB.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        axB.spines[s].set_linewidth(0.7)
    axB.text(-0.12, 1.03, "B", transform=axB.transAxes, fontsize=9.5, fontweight="bold")

    handles = [Line2D([], [], marker="o", ls="none", markersize=5, markerfacecolor=CAT_COLOUR[c],
                      markeredgecolor="white", markeredgewidth=0.4, label=CAT_LABEL[c])
               for c in ("local", "commercial", "junglefowl")]
    leg1 = axB.legend(handles=handles, frameon=False, fontsize=5.0, loc="lower left",
                      handletextpad=0.4, borderaxespad=0.3)
    axB.add_artist(leg1)
    axB.text(0.985, 0.02, "point size ∝ n individuals", transform=axB.transAxes,
             fontsize=4.8, color=GREY, ha="right")

    for ext in ("png", "pdf"):
        path = f"{args.out}.{ext}"
        fig.savefig(path, dpi=args.dpi)
        print("wrote", path)


if __name__ == "__main__":
    main()
