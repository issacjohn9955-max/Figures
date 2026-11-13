#!/usr/bin/env python3
"""Figure 2 - environmental variables behind the TE-climate screen.

A  marginal contribution of the 28 screened variables (1 % line)
B  variance decomposition of the 10 core variables (Shapley vs permutation)
C-E spatial surfaces of the three climate axes with the 20 breed origins

Usage
-----
python3 plot_fig2_env.py --data-dir data --out fig2_environment
"""
import argparse
import csv
import json
import os

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm, ListedColormap
from matplotlib.collections import LineCollection
from matplotlib.path import Path as MplPath
from matplotlib.lines import Line2D
from matplotlib.gridspec import GridSpec

MM = 1 / 25.4
INK = "#1B2430"
GREY = "#6B7280"

FIXED = ["bio3", "bio15", "bio18", "wind", "srad"]          # the five locked variables
SURFACES = [("bio3", "BIO3  Isothermality", "bio3"),         # (file, title, column)
            ("bio18", "BIO18  Precipitation, warmest quarter", "bio18"),
            ("srad", "SRAD  Annual mean solar radiation", "srad")]

BIN_COLOURS = ["#E8EEF3", "#9FC4D8", "#4E8FB5", "#1F4E6B"]
ACCENT = "#D55E00"


def read_tsv(path):
    with open(path, encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh, delimiter="\t"))


def draw_basemap(ax, polys, extent):
    segs = []
    for ring in polys:
        segs.append(np.asarray(ring))
    ax.add_collection(LineCollection(segs, colors="#9AA5B1", linewidths=0.35, zorder=3))
    ax.set_xlim(extent[0], extent[1])
    ax.set_ylim(extent[2], extent[3])
    ax.set_aspect(1 / np.cos(np.deg2rad(35)))
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_linewidth(0.6)
        s.set_color("#B7C0CA")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default="data")
    ap.add_argument("--geo", default="data/china_provinces.geojson")
    ap.add_argument("--out", default="fig2_environment")
    ap.add_argument("--dpi", type=int, default=600)
    args = ap.parse_args()

    stats = read_tsv(os.path.join(args.data_dir, "variable_stats.tsv"))
    breeds = read_tsv(os.path.join(args.data_dir, "breed_climate.tsv"))
    extent_d = json.load(open(os.path.join(args.data_dir, "extent.json")))
    extent = (extent_d["lon0"], extent_d["lon1"], extent_d["lat0"], extent_d["lat1"])

    geo = json.load(open(args.geo))
    rings = []
    for f in geo["features"]:
        g = f["geometry"]
        coords = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
        for poly in coords:
            for ring in poly:
                rings.append(ring)

    verts, codes = [], []
    for ring in rings:
        verts.extend(ring)
        codes.extend([MplPath.MOVETO] + [MplPath.LINETO] * (len(ring) - 2) + [MplPath.CLOSEPOLY])
    china = MplPath(np.asarray(verts), np.asarray(codes))

    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"],
        "pdf.fonttype": 42,
    })

    fig = plt.figure(figsize=(178 * MM, 116 * MM))
    gs = GridSpec(2, 3, figure=fig, height_ratios=[1.12, 0.88],
                  hspace=0.30, wspace=0.18,
                  left=0.075, right=0.985, top=0.925, bottom=0.105)

    # ------------------------------------------------ A: contribution bars
    axA = fig.add_subplot(gs[0, :2])
    rows = [r for r in stats if r["contribution_pct"]]
    rows.sort(key=lambda r: -float(r["contribution_pct"]))
    names = [r["variable"] for r in rows]
    vals = [float(r["contribution_pct"]) for r in rows]
    cols = [ACCENT if n in FIXED else "#8FA3B5" for n in names]
    axA.bar(range(len(vals)), vals, color=cols, width=0.72, zorder=3)
    axA.axhline(1, ls=(0, (4, 3)), lw=0.8, color="#B03A2E", zorder=4)
    axA.set_xticks(range(len(names)))
    axA.set_xticklabels(names, rotation=60, ha="right", fontsize=5.4)
    axA.set_ylabel("Contribution to significant TE associations (%)", fontsize=6.2)
    axA.tick_params(labelsize=5.4, width=0.6, length=2.4, pad=1.6)
    for s in ("top", "right"):
        axA.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        axA.spines[s].set_linewidth(0.7)
    axA.set_axisbelow(True)
    axA.yaxis.grid(True, color="#EDEFF2", lw=0.5)
    axA.set_ylim(0, max(vals) * 1.12)
    axA.text(-0.06, 1.05, "A", transform=axA.transAxes, fontsize=9.5, fontweight="bold")
    axA.legend(handles=[Line2D([], [], marker="s", ls="none", markersize=4, color=ACCENT,
                               label="locked variable"),
                        Line2D([], [], marker="s", ls="none", markersize=4, color="#8FA3B5",
                               label="screened out")],
               frameon=False, fontsize=5.2, loc="upper right", handletextpad=0.4)

    # ------------------------------------------------ B: Shapley vs permutation
    axB = fig.add_subplot(gs[0, 2])
    core = [r for r in stats if r.get("shapley_pct")]
    core.sort(key=lambda r: -float(r["permutation_pct"]))
    y = np.arange(len(core))
    shap = [float(r["shapley_pct"]) for r in core]
    perm = [float(r["permutation_pct"]) for r in core]
    axB.barh(y - 0.18, shap, height=0.34, color="#4C6E9C", label="Shapley (LMG)", zorder=3)
    axB.barh(y + 0.18, perm, height=0.34, color=ACCENT, label="Permutation", zorder=3)
    axB.set_yticks(y)
    axB.set_yticklabels([r["variable"] for r in core], fontsize=5.2)
    axB.invert_yaxis()
    axB.set_xlabel("Importance (%)", fontsize=6.0)
    axB.tick_params(labelsize=5.2, width=0.6, length=2.2, pad=1.4)
    for s in ("top", "right"):
        axB.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        axB.spines[s].set_linewidth(0.7)
    axB.set_axisbelow(True)
    axB.xaxis.grid(True, color="#EDEFF2", lw=0.5)
    axB.legend(frameon=False, fontsize=4.9, loc="lower right", handlelength=1.0,
               handletextpad=0.35, borderaxespad=0.2)
    axB.text(-0.34, 1.05, "B", transform=axB.transAxes, fontsize=9.5, fontweight="bold")

    # ------------------------------------------------ C-E: surfaces
    lons = np.linspace(extent[0], extent[1], 6)
    lonvals = [float(b["longitude"]) for b in breeds if b["longitude"]]
    for i, (stem, title, col) in enumerate(SURFACES):
        ax = fig.add_subplot(gs[1, i])
        arr = np.load(os.path.join(args.data_dir, f"{stem}.npy")).astype(float)
        vals_site = np.array([float(b[col]) for b in breeds])

        nrow, ncol = arr.shape
        lon_c = extent[0] + (np.arange(ncol) + 0.5) * (extent[1] - extent[0]) / ncol
        lat_c = extent[3] - (np.arange(nrow) + 0.5) * (extent[3] - extent[2]) / nrow
        gx, gy = np.meshgrid(lon_c, lat_c)
        inside = china.contains_points(np.column_stack([gx.ravel(), gy.ravel()]))
        arr = np.where(inside.reshape(arr.shape), arr, np.nan)

        q = np.nanquantile(arr, [0, 0.3, 0.55, 0.78, 1.0])
        q[0], q[-1] = np.nanmin(arr) - 1e-6, np.nanmax(arr) + 1e-6
        cmap = ListedColormap(BIN_COLOURS)
        cmap.set_bad("white")
        norm = BoundaryNorm(q, cmap.N)
        ax.imshow(arr, extent=extent, origin="upper", cmap=cmap, norm=norm,
                  interpolation="bilinear", zorder=1)
        draw_basemap(ax, rings, extent)

        bins = np.clip(np.digitize(vals_site, q) - 1, 0, 3)
        ax.scatter([float(b["longitude"]) for b in breeds], [float(b["latitude"]) for b in breeds],
                   s=16, c="white", edgecolors=INK, linewidths=0.6, zorder=5)

        order = np.argsort(vals_site)
        for idx in list(order[:3]) + list(order[-3:]):
            b = breeds[idx]
            ax.scatter(float(b["longitude"]), float(b["latitude"]), s=46,
                       facecolors="none", edgecolors=ACCENT, linewidths=0.9, zorder=6)

        ax.set_title(title, fontsize=5.8, color=INK, pad=3)
        ax.text(-0.06, 1.02, "CDE"[i], transform=ax.transAxes, fontsize=9.5,
                fontweight="bold")

    handles = [Line2D([], [], marker="s", ls="none", markersize=4.2, color=c,
                      markeredgecolor="#8C97A3", markeredgewidth=0.4) for c in BIN_COLOURS]
    labels = ["Q1 (low)", "Q2", "Q3", "Q4 (high)"]
    fig.legend(handles, labels, loc="lower center", ncol=4, frameon=False, fontsize=5.4,
               handletextpad=0.4, columnspacing=1.6, bbox_to_anchor=(0.42, 0.012),
               title="Climate quartile (raster quantiles)", title_fontsize=5.4)
    fig.text(0.815, 0.028, "orange ring = high / low gradient group", fontsize=5.0, color=GREY)

    for ext in ("png", "pdf"):
        path = f"{args.out}.{ext}"
        fig.savefig(path, dpi=args.dpi)
        print("wrote", path)


if __name__ == "__main__":
    main()
