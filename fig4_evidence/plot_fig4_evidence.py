#!/usr/bin/env python3
"""Figure 4 - cross-method evidence and how it collapses to zero.

A  who supports the 973 locus-variable pairs (LFMM / Spearman / both / RDA)
B  supported pairs per climate variable, split by environment specificity
C  how many variables each supported locus is associated with
D  the evidence ladder: 973 pairs -> 486 single-environment -> 0 concordant core

Usage
-----
python3 plot_fig4_evidence.py --data-dir data --out fig4_evidence
"""
import argparse
import os

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib.patches import Rectangle

MM = 1 / 25.4
INK = "#1B2430"
GREY = "#6B7280"

C_LFMM = "#4C6E9C"
C_SPEAR = "#D9A441"
C_RDA = "#8FA3B5"
C_SHARED = "#7FA88B"
C_SINGLE = "#C9705E"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default="data")
    ap.add_argument("--out", default="fig4_evidence")
    ap.add_argument("--dpi", type=int, default=600)
    args = ap.parse_args()

    d = pd.read_csv(os.path.join(args.data_dir, "te_env_pair_evidence.csv"))
    n_pairs = len(d)
    n_loci = d["locus"].nunique()
    n_lfmm = int((d["method_support"] == "LFMM_only").sum())
    n_spear = int((d["method_support"] == "Spearman_only").sum())
    n_both = int(((d["spearman_supported"]) & (d["lfmm_supported"])).sum())
    n_rda = int(d["rda_locus_support"].astype(str).str.lower().eq("true").sum())
    n_single = int((d["environment_specificity"] == "single_environment").sum())
    n_core = int((d["same_variable_core"].astype(str).str.lower() == "true").sum())

    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"],
        "pdf.fonttype": 42,
        "axes.unicode_minus": False,
    })

    fig = plt.figure(figsize=(178 * MM, 108 * MM))
    gs = GridSpec(2, 2, figure=fig, hspace=0.50, wspace=0.30,
                  left=0.10, right=0.975, top=0.905, bottom=0.11)

    def clean(ax):
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        for s in ("left", "bottom"):
            ax.spines[s].set_linewidth(0.7)
        ax.tick_params(labelsize=5.6, width=0.6, length=2.4, pad=1.8)
        ax.set_axisbelow(True)

    # ---------------------------------------------------- A: who supports
    axA = fig.add_subplot(gs[0, 0])
    labels = ["LFMM only", "Spearman only", "both methods", "also RDA outlier"]
    vals = [n_lfmm, n_spear, n_both, n_rda]
    cols = [C_LFMM, C_SPEAR, C_SHARED, C_RDA]
    y = np.arange(len(vals))[::-1]
    axA.barh(y, vals, color=cols, height=0.62, zorder=3)
    for yy, v in zip(y, vals):
        axA.text(v + max(vals) * 0.02, yy, str(v), va="center", fontsize=5.8, color=INK)
    axA.set_yticks(y)
    axA.set_yticklabels(labels, fontsize=5.8)
    axA.set_xlabel("Locus–variable pairs", fontsize=6.0)
    axA.set_xlim(0, max(vals) * 1.22)
    clean(axA)
    axA.xaxis.grid(True, color="#EDEFF2", lw=0.5)
    axA.text(-0.30, 1.10, "A", transform=axA.transAxes, fontsize=9.5, fontweight="bold")
    axA.text(0.98, 0.06, f"{n_pairs} pairs in total", transform=axA.transAxes,
             fontsize=5.0, color=GREY, ha="right")

    # ---------------------------------------------------- B: per variable
    axB = fig.add_subplot(gs[0, 1])
    order = ["bio3", "bio18", "bio15", "wind", "srad"]
    shared = [int(((d.variable == v) & (d.environment_specificity == "shared_environment")).sum()) for v in order]
    single = [int(((d.variable == v) & (d.environment_specificity == "single_environment")).sum()) for v in order]
    x = np.arange(len(order))
    axB.bar(x, single, width=0.62, color=C_SINGLE, label="single-environment", zorder=3)
    axB.bar(x, shared, width=0.62, bottom=single, color=C_SHARED, label="shared-environment", zorder=3)
    for i, (a, b) in enumerate(zip(single, shared)):
        axB.text(i, a + b + 6, str(a + b), ha="center", fontsize=5.6, color=INK)
    axB.set_xticks(x)
    axB.set_xticklabels(order, fontsize=5.8)
    axB.set_ylabel("Supported pairs", fontsize=6.0)
    axB.set_ylim(0, max(np.array(single) + np.array(shared)) * 1.22)
    clean(axB)
    axB.yaxis.grid(True, color="#EDEFF2", lw=0.5)
    axB.legend(frameon=False, fontsize=5.0, loc="upper right", handlelength=0.9,
               handletextpad=0.35, borderaxespad=0.2)
    axB.text(-0.24, 1.10, "B", transform=axB.transAxes, fontsize=9.5, fontweight="bold")

    # ---------------------------------------------------- C: variables per locus
    axC = fig.add_subplot(gs[1, 0])
    cnt = d.groupby("locus")["variable"].nunique().value_counts().sort_index()
    xs = np.arange(1, 6)
    ys = [int(cnt.get(k, 0)) for k in xs]
    axC.bar(xs, ys, width=0.62, color="#6E8CA8", zorder=3)
    for i, v in zip(xs, ys):
        axC.text(i, v + 8, str(v), ha="center", fontsize=5.6, color=INK)
    axC.set_xticks(xs)
    axC.set_xticklabels([str(k) for k in xs], fontsize=5.8)
    axC.set_xlabel("Variables supported per locus", fontsize=6.0)
    axC.set_ylabel("Number of loci", fontsize=6.0)
    axC.set_ylim(0, max(ys) * 1.20)
    clean(axC)
    axC.yaxis.grid(True, color="#EDEFF2", lw=0.5)
    axC.text(-0.24, 1.10, "C", transform=axC.transAxes, fontsize=9.5, fontweight="bold")

    # ---------------------------------------------------- D: evidence ladder
    axD = fig.add_subplot(gs[1, 1])
    stages = [
        ("Supported pairs", n_pairs),
        ("Single-environment", n_single),
        ("Strict core", n_core),
    ]
    ypos = np.arange(len(stages))[::-1]
    for i, ((lab, v), yy) in enumerate(zip(stages, ypos)):
        w = max(v, 0)
        axD.add_patch(Rectangle((0, yy - 0.28), w, 0.56, facecolor="#4C6E9C" if i < 2 else "#C9705E",
                                edgecolor="none", alpha=0.92, zorder=3))
        axD.text(w + n_pairs * 0.03, yy, f"{v:,}" if v else "0", va="center",
                 fontsize=6.0, color=INK, fontweight="bold" if v == 0 else "normal")
    axD.set_yticks(ypos)
    axD.set_yticklabels([s[0] for s in stages], fontsize=5.6)
    axD.set_xlabel("Locus–variable pairs", fontsize=6.0)
    axD.set_xlim(0, n_pairs * 1.30)
    axD.set_ylim(-0.6, len(stages) - 0.4)
    clean(axD)
    axD.xaxis.grid(True, color="#EDEFF2", lw=0.5)
    axD.text(-0.30, 1.10, "D", transform=axD.transAxes, fontsize=9.5, fontweight="bold")
    axD.text(0.98, 0.05, f"strict core = same variable + concordant direction\n"
                         f"{n_loci} distinct loci · {n_rda} with RDA support",
             transform=axD.transAxes, fontsize=4.8, color=GREY, ha="right", va="bottom")

    for ext in ("png", "pdf"):
        path = f"{args.out}.{ext}"
        fig.savefig(path, dpi=args.dpi)
        print("wrote", path)


if __name__ == "__main__":
    main()
