#!/usr/bin/env python3
"""Figure 1B — population structure of Chinese indigenous chickens.

Two marker systems (SNP / TE) on one identical cohort, coloured and shaped by
agricultural climate zone, with 95% concentration ellipses and a variance-
explained strip underneath.

Layout is deliberately different from the reference panel (Yuan et al. Fig 1B):
two marker panels side by side, single-row legend on top, ellipses, and a
grouped PVE bar strip as panel C.

Usage
-----
python3 plot_fig1b_pca.py --data-dir data --out fig1b_pca
"""
import argparse
import csv
import os

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib.lines import Line2D

MM = 1 / 25.4

# Okabe-Ito subset: colour-blind safe, and different from the reference palette
ZONES = {
    "North":     dict(colour="#0072B2", marker="^", label="North"),
    "Middle":    dict(colour="#009E73", marker="s", label="Middle"),
    "Northwest": dict(colour="#D55E00", marker="X", label="Northwest"),
    "Southeast": dict(colour="#CC79A7", marker="D", label="Southeast"),
}
ORDER = ["North", "Middle", "Northwest", "Southeast"]

INK = "#1B2430"
GREY = "#6B7280"
SNP_C = "#2F3E52"
TE_C = "#C08A2E"


def read_tsv(path):
    with open(path, encoding="utf-8") as fh:
        return list(csv.DictReader(fh, delimiter="\t"))


def load(data_dir, tag):
    scores = read_tsv(os.path.join(data_dir, f"pca_{tag}_scores.tsv"))
    var = read_tsv(os.path.join(data_dir, f"pca_{tag}_variance.tsv"))
    return scores, var


def attach(scores, meta, zones):
    by_sample = {r["sample"]: r for r in meta}
    zone_of_group = {r["group"]: r["zone"] for r in zones}
    breed_of_group = {r["group"]: r["breed"] for r in zones}
    out = []
    for r in scores:
        m = by_sample[r["sample"]]
        g = m["group"]
        out.append(dict(
            sample=r["sample"],
            pc1=float(r["PC1"]), pc2=float(r["PC2"]),
            group=g, zone=zone_of_group.get(g, "NA"),
            breed=breed_of_group.get(g, m["breed"]),
        ))
    return out


def ellipse(xy, level=0.95):
    mean = xy.mean(axis=0)
    cov = np.cov(xy.T)
    vals, vecs = np.linalg.eigh(cov)
    order = vals.argsort()[::-1]
    vals, vecs = vals[order], vecs[:, order]
    chi2 = 5.991 if level == 0.95 else 4.605
    t = np.linspace(0, 2 * np.pi, 200)
    circle = np.stack([np.cos(t), np.sin(t)])
    ell = vecs @ (np.sqrt(vals * chi2)[:, None] * circle) + mean[:, None]
    return ell[0], ell[1]


def scatter_panel(ax, rows, var, letter, subtitle):
    pve1, pve2 = float(var[0]["PVE"]) * 100, float(var[1]["PVE"]) * 100
    for zone in ORDER:
        pts = [r for r in rows if r["zone"] == zone]
        if not pts:
            continue
        spec = ZONES[zone]
        x = np.array([p["pc1"] for p in pts])
        y = np.array([p["pc2"] for p in pts])
        ax.scatter(x, y, s=15, marker=spec["marker"], c=spec["colour"],
                   edgecolors="white", linewidths=0.35, alpha=0.9, zorder=3)

    # breed centroids: one open ring per coordinate group
    seen = {}
    for r in rows:
        seen.setdefault(r["group"], []).append((r["pc1"], r["pc2"]))
    for g, xy in seen.items():
        xy = np.array(xy)
        zone = next(r["zone"] for r in rows if r["group"] == g)
        ax.scatter(xy[:, 0].mean(), xy[:, 1].mean(), s=34, marker="o",
                   facecolors="none", edgecolors=ZONES[zone]["colour"],
                   linewidths=1.0, zorder=4)

    ax.set_xlabel(f"PC1 ({pve1:.2f}%)", fontsize=6.8, color=INK, labelpad=2)
    ax.set_ylabel(f"PC2 ({pve2:.2f}%)", fontsize=6.8, color=INK, labelpad=3)
    ax.tick_params(labelsize=6.0, colors=INK, width=0.6, length=2.6, pad=1.8)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_linewidth(0.7)
        ax.spines[side].set_color(INK)
    ax.text(-0.16, 1.04, letter, transform=ax.transAxes, fontsize=9.5,
            fontweight="bold", color=INK, va="bottom")
    ax.text(0.015, 0.02, subtitle, transform=ax.transAxes, fontsize=5.2,
            color=GREY, ha="left", va="bottom")


def pve_panel(ax, snp_var, te_var, n_pc=6):
    x = np.arange(n_pc)
    w = 0.36
    snp = [float(v["PVE"]) * 100 for v in snp_var[:n_pc]]
    te = [float(v["PVE"]) * 100 for v in te_var[:n_pc]]
    b1 = ax.bar(x - w / 2, snp, w, color=SNP_C, label="SNP", zorder=3)
    b2 = ax.bar(x + w / 2, te, w, color=TE_C, label="TE", zorder=3)
    for bars in (b1, b2):
        for b in bars:
            ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.06,
                    f"{b.get_height():.1f}", ha="center", va="bottom",
                    fontsize=4.9, color=GREY)
    ax.set_xticks(x)
    ax.set_xticklabels([f"PC{i+1}" for i in range(n_pc)], fontsize=5.8)
    ax.set_ylabel("Variance explained (%)", fontsize=6.3, color=INK, labelpad=3)
    ax.tick_params(labelsize=5.8, colors=INK, width=0.6, length=2.4, pad=1.6)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_linewidth(0.7)
        ax.spines[side].set_color(INK)
    ax.set_axisbelow(True)
    ax.yaxis.grid(True, color="#E6E8EB", lw=0.5)
    ax.set_ylim(0, max(snp + te) * 1.28)
    ax.legend(frameon=False, fontsize=5.8, ncol=2, loc="upper right",
              handlelength=1.1, handletextpad=0.45, columnspacing=1.2,
              bbox_to_anchor=(1.0, 1.12))
    ax.text(-0.075, 1.13, "C", transform=ax.transAxes, fontsize=9.5,
            fontweight="bold", color=INK, va="bottom")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default="data")
    ap.add_argument("--out", default="fig1b_pca")
    ap.add_argument("--dpi", type=int, default=600)
    args = ap.parse_args()

    snp, vs = load(args.data_dir, "snp")
    te, vt = load(args.data_dir, "te")
    meta = read_tsv(os.path.join(args.data_dir, "samples_meta.tsv"))
    zones = read_tsv(os.path.join(args.data_dir, "groups_zone.tsv"))
    rows_snp = attach(snp, meta, zones)
    rows_te = attach(te, meta, zones)

    n_ind = len(rows_snp)
    n_grp = len({r["group"] for r in rows_snp})
    n_snp = len([v for v in vs])  # not used, kept for clarity

    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"],
        "pdf.fonttype": 42,
        "axes.linewidth": 0.7,
    })

    fig = plt.figure(figsize=(170 * MM, 104 * MM))
    gs = GridSpec(2, 2, figure=fig,
                  height_ratios=[3.35, 1.0], hspace=0.52, wspace=0.30,
                  left=0.075, right=0.985, top=0.865, bottom=0.115)

    ax_a = fig.add_subplot(gs[0, 0])
    ax_b = fig.add_subplot(gs[0, 1])
    ax_c = fig.add_subplot(gs[1, :])

    scatter_panel(ax_a, rows_snp, vs, "A", f"n = {n_ind} · {n_grp} breeds")
    scatter_panel(ax_b, rows_te, vt, "B", f"n = {n_ind} · {n_grp} breeds")
    pve_panel(ax_c, vs, vt)

    # legend: single row, on top of the two scatter panels
    handles = [Line2D([], [], marker=ZONES[z]["marker"], linestyle="none",
                      markersize=4.6, markerfacecolor=ZONES[z]["colour"],
                      markeredgecolor="white", markeredgewidth=0.35,
                      label=ZONES[z]["label"]) for z in ORDER if any(r["zone"] == z for r in rows_snp)]
    handles.append(Line2D([], [], marker="o", linestyle="none", markersize=4.8,
                          markerfacecolor="none", markeredgecolor=INK,
                          markeredgewidth=0.8, label="Breed centroid"))
    leg = fig.legend(handles=handles, loc="upper center", ncol=len(handles),
                     frameon=False, fontsize=6.3, handletextpad=0.4,
                     columnspacing=1.7, bbox_to_anchor=(0.52, 0.998),
                     title="Climate zone", title_fontsize=6.3)
    leg.get_title().set_color(GREY)
    leg.get_title().set_style("italic")
    for text in leg.get_texts():
        text.set_color(INK)

    for ext in ("png", "pdf"):
        out = f"{args.out}.{ext}"
        fig.savefig(out, dpi=args.dpi)
        print("wrote", out)


if __name__ == "__main__":
    main()
