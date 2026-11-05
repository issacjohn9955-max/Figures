#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
China sampling map with breed names outside the map and leader lines.

Same data as fig2 (china_sampling_sites.tsv: 363 individuals at 21 sites), but
the names no longer sit on top of the geography: they are stacked in two margin
columns ordered by latitude, and a 0.3 pt line points to each site.  Circle area
still encodes the number of adopted individuals.

    python3 plot_china_sampling_labelled.py
    python3 plot_china_sampling_labelled.py --relief ../world_distribution_map/data/relief/NE1_50M_SR_W.jpg
    python3 plot_china_sampling_labelled.py --no-labels      # points only
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.collections import LineCollection, PolyCollection  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from plot_china_sampling_points import _geoms, _lines, _rings  # noqa: E402

TEXT = "#273746"
GRID = "#A9B2BB"
FILL = "#F4F7F9"
FONT = ["Arial", "Helvetica", "Liberation Sans", "DejaVu Sans"]

LON = (73.0, 136.0)
LAT = (17.0, 55.0)
FIG_W, FIG_H = 6.30, 4.33          # 160 x 110 mm
DPI_PNG = 600

MAP_AX = [0.205, 0.085, 0.590, 0.775]
DEFAULT_RELIEF = HERE / "data" / "relief" / "NE1_50M_SR_W.jpg"


def load_sites(path):
    rows = []
    with open(path, encoding="utf-8") as fh:
        head = fh.readline().rstrip("\n").split("\t")
        for line in fh:
            if not line.strip():
                continue
            d = dict(zip(head, line.rstrip("\n").split("\t")))
            rows.append(dict(
                label=(d.get("label_en") or d.get("label") or "").strip(),
                lon=float(d["lon"]), lat=float(d["lat"]),
                individuals=int(d["individuals"]),
                precision=d.get("precision", "county"),
            ))
    return rows


def load_layers(geo_path, maritime_path):
    prov = {}
    for geom, props in _geoms(json.loads(Path(geo_path).read_text())):
        name = props.get("name")
        if name and str(props.get("adcode")) != "100000_JD":
            prov[name] = _rings(geom)
    mar = []
    for geom, _ in _geoms(json.loads(Path(maritime_path).read_text())):
        mar += _lines(geom)
    return prov, mar


def draw_base(ax, prov, maritime, relief=None):
    rings = [r for v in prov.values() for r in v]
    if relief:
        from PIL import Image
        img = np.asarray(Image.open(relief).convert("RGB"))
        ax.imshow(img, extent=(-180, 180, -90, 90), aspect="auto",
                  zorder=0, interpolation="bilinear")
    else:
        ax.add_collection(PolyCollection(rings, facecolors=FILL,
                                         edgecolors="none", zorder=1))
    ax.add_collection(LineCollection(rings, colors=GRID, linewidths=0.22, zorder=2))
    ax.add_collection(LineCollection(rings, colors=TEXT, linewidths=0.55, zorder=2.5))
    ax.add_collection(LineCollection(rings, colors=BG, linewidths=0.42, zorder=2.6))
    if maritime:
        ax.add_collection(LineCollection(maritime, colors=TEXT, linewidths=0.7,
                                         zorder=4))


def marker_sizes(rows):
    counts = np.array([r["individuals"] for r in rows], dtype=float)
    r_mm = 1.15 + 0.95 * np.sqrt(counts / counts.max())
    return (r_mm * 2.835) ** 2 * np.pi


def draw_points(ax, rows, sizes):
    for r, s in zip(rows, sizes):
        ax.scatter(r["lon"], r["lat"], s=s, facecolors="white",
                   edgecolors=TEXT, linewidths=0.5, zorder=8)


def draw_labels(ax, rows, fontsize=5.1, pad=0.030, y_top=0.975, y_bot=0.025):
    cut = float(np.median([r["lon"] for r in rows]))
    for side in ("left", "right"):
        grp = [r for r in rows
               if (r["lon"] < cut) == (side == "left")]
        grp.sort(key=lambda r: -r["lat"])
        ys = np.linspace(y_top, y_bot, len(grp)) if len(grp) > 1 else [0.5]
        for r, y in zip(grp, ys):
            x = -pad if side == "left" else 1.0 + pad
            ax.annotate(
                r["label"], xy=(r["lon"], r["lat"]), xycoords="data",
                xytext=(x, y), textcoords="axes fraction",
                ha="right" if side == "left" else "left", va="center",
                fontsize=fontsize, color=TEXT, annotation_clip=False,
                arrowprops=dict(arrowstyle="-", lw=0.30, color=TEXT,
                                shrinkA=2.0, shrinkB=2.8),
            )


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="China sampling map with margin labels")
    ap.add_argument("--sites", default=str(HERE / "china_sampling_sites.tsv"))
    ap.add_argument("--geo", default=str(HERE / "data" / "china_provinces.geojson"))
    ap.add_argument("--maritime", default=str(HERE / "data" / "china_maritime.geojson"))
    ap.add_argument("--relief", default=str(DEFAULT_RELIEF),
                    help="optional basemap raster; pass '' for the flat style")
    ap.add_argument("--outdir", default=str(HERE))
    ap.add_argument("--stem", default="fig3_sampling_sites_labelled")
    ap.add_argument("--labels", action="store_true", default=True)
    ap.add_argument("--no-labels", dest="labels", action="store_false")
    args = ap.parse_args(argv)

    relief = None
    if args.relief and Path(args.relief).exists():
        relief = args.relief
    rows = load_sites(args.sites)
    prov, mar = load_layers(args.geo, args.maritime)

    global BG
    BG = "#F4F7F9" if relief is None else "#FFFFFF"
    plt.rcParams.update({
        "font.family": FONT, "text.color": TEXT,
        "pdf.fonttype": 42, "ps.fonttype": 42,
    })

    fig = plt.figure(figsize=(FIG_W, FIG_H))
    ax = fig.add_axes(MAP_AX)
    draw_base(ax, prov, mar, relief=relief)
    sizes = marker_sizes(rows)
    draw_points(ax, rows, sizes)
    if args.labels:
        draw_labels(ax, rows)

    ax.set_xlim(*LON)
    ax.set_ylim(*LAT)
    ax.set_aspect(1.0 / np.cos(np.deg2rad(35)), adjustable="box")
    ax.set_xticks([])
    ax.set_yticks([])
    for sp in ax.spines.values():
        sp.set_visible(True)
        sp.set_linewidth(0.45)
        sp.set_color(GRID)

    total = sum(r["individuals"] for r in rows)
    fig.text(0.012, 0.962,
             f"{total} individuals at {len(rows)} sites (24 records, 10 provinces); "
             "circle area = individuals (2-40); names ordered by latitude",
             fontsize=5.4, color="#5A6B7B", ha="left")

    stem = Path(args.outdir) / args.stem
    for ext, kw in (("png", dict(dpi=DPI_PNG)), ("pdf", {})):
        fig.savefig(f"{stem}.{ext}", facecolor="white", **kw)
    print(f"wrote {stem}.png / {stem}.pdf  ({len(rows)} sites, {total} individuals, "
          f"relief={'yes' if relief else 'no'})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
