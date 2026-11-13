#!/usr/bin/env python3
"""Figure 5 - which TE families carry the climate signal, and where they sit.

A  TE class composition of all tested loci vs the climate-associated loci
B  family-level enrichment (observed / expected), top families
C  circular chromosome map of the 682 associated loci

Usage
-----
python3 plot_fig5_te.py --data-dir data --out fig5_te
"""
import argparse
import math
import os

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib.patches import Wedge

MM = 1 / 25.4
INK = "#1B2430"
GREY = "#6B7280"

CLASS_ORDER = ["LINE", "LTR", "DNA", "MITE", "mixed"]
CLASS_COLOUR = {"LINE": "#3E5C76", "LTR": "#7FA88B", "DNA": "#C9705E",
                "MITE": "#9C89B8", "mixed": "#B9C2CC"}
ACCENT = "#C0392B"


def primary_class(s):
    if not isinstance(s, str) or not s.strip():
        return "unknown"
    parts = [p for p in s.split(";") if p and p != "Unknown"]
    if not parts:
        return "unknown"
    return parts[0] if len(parts) == 1 else "mixed"


def z_to_p(z):
    return math.erfc(abs(z) / math.sqrt(2))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default="data")
    ap.add_argument("--out", default="fig5_te")
    ap.add_argument("--dpi", type=int, default=600)
    ap.add_argument("--pairs", default=None,
                    help="pair evidence table; autodetected in the local and repo layouts")
    args = ap.parse_args()

    cat = pd.read_csv(os.path.join(args.data_dir, "te_catalog.csv"))
    candidates = [args.pairs] if args.pairs else [
        os.path.join(args.data_dir, "te_env_pair_evidence.csv"),
        os.path.join(args.data_dir, "..", "..", "Fig4", "data", "te_env_pair_evidence.csv"),
        os.path.join(args.data_dir, "..", "fig4_evidence", "data", "te_env_pair_evidence.csv"),
    ]
    pairs_path = next(p for p in candidates if p and os.path.exists(p))
    pairs = pd.read_csv(pairs_path)
    sizes = pd.read_csv(os.path.join(args.data_dir, "main.chrom.sizes"),
                        sep=r"\s+", header=None, names=["chrom", "len"])

    fg_loci = pairs.drop_duplicates("locus")[["locus"]].copy()
    ann = cat.set_index("locus")[["te_class", "te_family"]]
    fg_loci["te_class"] = fg_loci["locus"].map(ann["te_class"])
    fg_loci["te_family"] = fg_loci["locus"].map(ann["te_family"])
    fg_loci["te_superfamily"] = fg_loci["locus"].map(cat.set_index("locus")["te_superfamily"])

    cat["cls"] = cat["te_class"].map(primary_class)
    fg_loci["cls"] = fg_loci["te_class"].map(primary_class)

    bg_counts = cat["cls"].value_counts()
    fg_counts = fg_loci["cls"].value_counts()
    n_bg, n_fg = len(cat), len(fg_loci)

    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"],
        "pdf.fonttype": 42,
        "axes.unicode_minus": False,
    })

    fig = plt.figure(figsize=(178 * MM, 112 * MM))
    gs = GridSpec(2, 2, figure=fig, width_ratios=[0.52, 0.48],
                  height_ratios=[0.55, 0.45], hspace=0.55, wspace=0.22,
                  left=0.10, right=0.99, top=0.90, bottom=0.10)

    def clean(ax):
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        for s in ("left", "bottom"):
            ax.spines[s].set_linewidth(0.7)
        ax.tick_params(labelsize=5.4, width=0.6, length=2.2, pad=1.6)
        ax.set_axisbelow(True)

    # ------------------------------------------------- A: class composition
    axA = fig.add_subplot(gs[0, 0])
    classes = [c for c in CLASS_ORDER if c in bg_counts.index or c in fg_counts.index]
    bg_pct = [100 * bg_counts.get(c, 0) / n_bg for c in classes]
    fg_pct = [100 * fg_counts.get(c, 0) / n_fg for c in classes]
    x = np.arange(len(classes))
    w = 0.36
    axA.bar(x - w / 2, bg_pct, w, color="#C9D2DB", label=f"all tested loci (n={n_bg})", zorder=3)
    axA.bar(x + w / 2, fg_pct, w, color=ACCENT, label=f"climate-associated (n={n_fg})", zorder=3)
    for i, (b, f) in enumerate(zip(bg_pct, fg_pct)):
        axA.text(i - w / 2, b + 1.2, f"{b:.0f}", ha="center", fontsize=4.8, color=GREY)
        axA.text(i + w / 2, f + 1.2, f"{f:.0f}", ha="center", fontsize=4.8, color=ACCENT)
    axA.set_xticks(x)
    axA.set_xticklabels(classes, fontsize=5.6)
    axA.set_ylabel("Share of loci (%)", fontsize=6.0)
    axA.set_ylim(0, max(bg_pct + fg_pct) * 1.28)
    clean(axA)
    axA.yaxis.grid(True, color="#EDEFF2", lw=0.5)
    axA.legend(frameon=False, fontsize=4.9, loc="upper right", handlelength=0.9,
               handletextpad=0.35, borderaxespad=0.2)
    axA.text(-0.16, 1.10, "A", transform=axA.transAxes, fontsize=9.5, fontweight="bold")

    # ------------------------------------------------- B: family enrichment
    axB = fig.add_subplot(gs[1, 0])
    def super_of(name):
        if not isinstance(name, str) or not name.strip():
            return None
        first = [x for x in name.split(";") if x and x != "Unknown"][0]
        return first.split("/")[-1]

    bg_fam, fg_fam = {}, {}
    for name in cat["te_superfamily"].dropna():
        k = super_of(name)
        if k:
            bg_fam[k] = bg_fam.get(k, 0) + 1
    for name in fg_loci["te_superfamily"].dropna():
        k = super_of(name)
        if k:
            fg_fam[k] = fg_fam.get(k, 0) + 1
    rows = []
    for f, nb in bg_fam.items():
        if nb < 20:
            continue
        nf = fg_fam.get(f, 0)
        obs = nf / n_fg
        exp = nb / n_bg
        fold = obs / exp if exp else np.nan
        se = math.sqrt(max(exp * (1 - exp) / n_fg, 1e-12))
        z = (obs - exp) / se if se else 0
        rows.append((f, nb, nf, fold, z_to_p(z)))
    fam = pd.DataFrame(rows, columns=["family", "bg", "fg", "fold", "p"]).sort_values("fold", ascending=False)
    fam = fam.head(9)
    fam["lo"] = np.exp(np.log(fam["fold"]) - 1.96 * np.sqrt(1 / np.maximum(fam["fg"], 1) - 1 / n_fg
                                                          + 1 / fam["bg"] - 1 / n_bg))
    fam["hi"] = np.exp(np.log(fam["fold"]) + 1.96 * np.sqrt(1 / np.maximum(fam["fg"], 1) - 1 / n_fg
                                                          + 1 / fam["bg"] - 1 / n_bg))
    fam = fam.iloc[::-1]
    y = np.arange(len(fam))
    for i, r in enumerate(fam.itertuples()):
        col = ACCENT if (r.lo > 1 or r.hi < 1) else "#6E8CA8"
        axB.plot([r.lo, r.hi], [i, i], color=col, lw=0.9, solid_capstyle="butt", zorder=3)
        axB.plot(r.fold, i, "o", color=col, markersize=3.4, zorder=4)
        axB.text(r.hi + 0.03, i, f"{r.fg}/{r.bg}", va="center", fontsize=4.6, color=GREY)
    axB.axvline(1, color=GREY, lw=0.7, ls=(0, (3, 2)), zorder=2)
    axB.set_yticks(y)
    axB.set_yticklabels(fam["family"], fontsize=5.2)
    axB.set_xlabel("Fold enrichment (95% CI)", fontsize=6.0)
    axB.set_xlim(0.55, max(fam["hi"].max() * 1.30, 1.6))
    axB.set_ylim(-0.7, len(fam) - 0.3)
    clean(axB)
    axB.xaxis.grid(True, color="#EDEFF2", lw=0.5)
    axB.text(-0.30, 1.12, "B", transform=axB.transAxes, fontsize=9.5, fontweight="bold")
    axB.text(0.99, -0.30, "label = associated / background loci; dashed line = no enrichment",
             transform=axB.transAxes, fontsize=4.6, color=GREY, ha="right")

    # ------------------------------------------------- C: circular map
    axC = fig.add_subplot(gs[:, 1])
    axC.set_aspect("equal")
    axC.axis("off")

    sizes["len"] = sizes["len"].astype(float)
    order = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13",
             "14", "15", "16", "17", "18", "19", "20", "21", "22", "23", "24", "25",
             "26", "27", "28", "29", "30", "31", "32", "33", "34", "35", "36", "37",
             "38", "39", "Z", "W"]
    sizes = sizes.set_index("chrom").loc[order].reset_index()
    total = sizes["len"].sum()
    gap = 2.2
    span = 360 - gap * len(sizes)
    start = 90.0
    pos = {}
    for i, r in sizes.iterrows():
        width = span * r["len"] / total
        pos[str(r["chrom"])] = (start, width)
        start -= width + gap

    r_out, r_in = 1.00, 0.955
    for chrom, (a0, wdt) in pos.items():
        axC.add_patch(Wedge((0, 0), r_out, a0 - wdt, a0, width=r_out - r_in,
                            facecolor="#DCE3EA", edgecolor="white", lw=0.35, zorder=2))
        mid = a0 - wdt / 2
        if wdt < 0.85:
            continue
        lab_r = 1.06
        rot = mid - 90
        if mid < -90 or mid > 90:
            rot = mid + 90
        axC.text(lab_r * math.cos(math.radians(mid)), lab_r * math.sin(math.radians(mid)),
                 chrom, fontsize=4.2, color=INK, ha="center", va="center",
                 rotation=rot, rotation_mode="anchor")

    chrom_len = dict(zip(sizes["chrom"].astype(str), sizes["len"]))
    seen = set()
    for locus in fg_loci["locus"]:
        chrom, p = str(locus).split(":")[:2]
        if chrom not in pos or chrom in seen and False:
            continue
        a0, wdt = pos[chrom]
        frac = min(float(p) / chrom_len[chrom], 1.0)
        ang = a0 - wdt * frac
        axC.plot([0.945 * math.cos(math.radians(ang)), 0.915 * math.cos(math.radians(ang))],
                 [0.945 * math.sin(math.radians(ang)), 0.915 * math.sin(math.radians(ang))],
                 color=ACCENT, lw=0.45, alpha=0.8, zorder=3, solid_capstyle="butt")

    axC.text(0, 0.16, f"{n_fg}", fontsize=15, color=ACCENT, ha="center", va="center", fontweight="bold")
    axC.text(0, 0.045, "climate-associated\nTE loci", fontsize=4.8, color=GREY, ha="center", va="center")
    axC.text(0, -0.10, f"{len(sizes)} chromosomes\n{total/1e6:.0f} Mb (GRCg7b)", fontsize=4.6,
             color=GREY, ha="center", va="center")
    axC.set_xlim(-1.22, 1.22)
    axC.set_ylim(-1.22, 1.22)
    axC.text(-1.18, 1.10, "C", fontsize=9.5, fontweight="bold")

    for ext in ("png", "pdf"):
        path = f"{args.out}.{ext}"
        fig.savefig(path, dpi=args.dpi)
        print("wrote", path)


if __name__ == "__main__":
    main()
