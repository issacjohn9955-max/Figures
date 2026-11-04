#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
China sampling sites — latitude/longitude point map, house style.

Colours come from the style library (1577377232/Genomics-Figure-Styles,
palettes.json → pangenome_spectrum) and its theme colours:
  class ramp   #B4AD74 → #7BB6AC → #5899B2 → #386C8C
  text / axis  #273746   province line #A9B2BB

    python3 plot_china_sampling_points.py
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import matplotlib.patheffects as pe  # noqa: E402
from matplotlib.collections import LineCollection  # noqa: E402
from matplotlib.patches import PathPatch, Rectangle  # noqa: E402
from matplotlib.path import Path as MPath  # noqa: E402

HERE = Path(__file__).resolve().parent

LON = (72.0, 136.0)
LAT = (3.0, 55.0)
FIG_W, FIG_H = 6.95, 6.30          # inches ≈ 177 × 160 mm
DPI_PNG = 600

# --- house palette (pangenome_spectrum) -------------------------------------
CLASS_COLORS = ["#B4AD74", "#7BB6AC", "#5899B2", "#386C8C"]
BREAKS = [10, 20, 30]              # 1–9 / 10–19 / 20–29 / ≥30
CLASS_LABELS = ["1–9", "10–19", "20–29", "≥30"]

TEXT = "#273746"
GRID = "#A9B2BB"
FILL = "#FFFFFF"
FONT = ["PingFang SC", "Heiti SC", "Songti SC", "Arial Unicode MS",
        "Noto Sans CJK SC", "DejaVu Sans"]

INSET = (102.6, 111.9, 23.6, 29.2)


def _geoms(obj):
    if obj.get("type") == "FeatureCollection":
        for f in obj["features"]:
            yield f.get("geometry", f), f.get("properties", {})
    elif obj.get("type") == "Feature":
        yield obj["geometry"], obj.get("properties", {})
    else:
        yield obj, obj.get("properties", {})


def _rings(geom):
    t, c = geom["type"], geom["coordinates"]
    polys = [c] if t == "Polygon" else c if t == "MultiPolygon" else []
    out = []
    for poly in polys:
        for ring in poly[:1]:
            arr = np.asarray(ring, dtype=float)
            if arr.shape[0] >= 4:
                out.append(arr)
    return out


def _lines(geom):
    t, c = geom["type"], geom["coordinates"]
    if t == "LineString":
        return [np.asarray(c, dtype=float)]
    if t == "MultiLineString":
        return [np.asarray(l, dtype=float) for l in c]
    return []


def rings_to_path(rings):
    verts, codes = [], []
    for r in rings:
        verts.append(r)
        codes.append(np.r_[MPath.MOVETO, [MPath.LINETO] * (len(r) - 2),
                           MPath.CLOSEPOLY])
    return MPath(np.concatenate(verts), np.concatenate(codes).astype(np.uint8))


def klass(n: int) -> int:
    return sum(n >= b for b in BREAKS)


def draw_base(ax, prov, maritime, lw_nation=0.9, lw_prov=0.22, lw_mar=0.8):
    all_rings = [r for v in prov.values() for r in v]
    # 小岛单独用细线，否则粗描边会把它们糊成一团
    big = [r for r in all_rings if max(np.ptp(r[:, 0]), np.ptp(r[:, 1])) > 0.45]
    small = [r for r in all_rings if max(np.ptp(r[:, 0]), np.ptp(r[:, 1])) <= 0.45]
    ax.add_collection(LineCollection(small, colors=TEXT, linewidths=0.32, zorder=1))
    ax.add_collection(LineCollection(big, colors=TEXT, linewidths=lw_nation, zorder=1))
    for rings in prov.values():
        ax.add_patch(PathPatch(rings_to_path(rings), facecolor=FILL,
                               edgecolor="none", zorder=2))
    ax.add_collection(LineCollection(all_rings, colors=GRID,
                                     linewidths=lw_prov, zorder=3))
    if maritime:
        ax.add_collection(LineCollection(maritime, colors=TEXT,
                                         linewidths=lw_mar, zorder=4))


def marker(ax, r, s):
    c = CLASS_COLORS[klass(r["individuals"])]
    if r["precision"] == "region":
        ax.scatter(r["lon"], r["lat"], s=s, facecolors="none", edgecolors=c,
                   linewidths=1.0, linestyles="--", zorder=8)
    else:
        ax.scatter(r["lon"], r["lat"], s=s, c=c, edgecolors="white",
                   linewidths=0.5, zorder=8)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sites", default=str(HERE / "china_sampling_sites.tsv"))
    ap.add_argument("--geo", default=str(HERE / "data" / "china_provinces.geojson"))
    ap.add_argument("--maritime", default=str(HERE / "data" / "china_maritime.geojson"))
    ap.add_argument("--outdir", default=str(HERE))
    ap.add_argument("--stem", default="china_sampling_points")
    args = ap.parse_args(argv)

    for f in (args.geo, args.maritime, args.sites):
        if not Path(f).exists():
            raise SystemExit(f"missing input: {f}")

    plt.rcParams.update({
        "font.family": FONT,
        "text.color": TEXT,
        "axes.linewidth": 0.0,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    })

    rows = []
    with open(args.sites, encoding="utf-8") as fh:
        head = fh.readline().rstrip("\n").split("\t")
        for line in fh:
            if not line.strip():
                continue
            d = dict(zip(head, line.rstrip("\n").split("\t")))
            for k in ("id", "individuals", "records"):
                d[k] = int(d[k])
            for k in ("lon", "lat", "dx", "dy"):
                d[k] = float(d[k])
            rows.append(d)
    rows.sort(key=lambda r: r["id"])

    prov = {}
    for geom, props in _geoms(json.loads(Path(args.geo).read_text())):
        if props.get("name") and str(props.get("adcode")) != "100000_JD":
            prov[props["name"]] = _rings(geom)
    maritime = []
    for geom, _ in _geoms(json.loads(Path(args.maritime).read_text())):
        maritime += _lines(geom)

    fig = plt.figure(figsize=(FIG_W, FIG_H))
    ax = fig.add_axes([0.012, 0.028, 0.976, 0.880])

    draw_base(ax, prov, maritime)

    counts = np.array([r["individuals"] for r in rows], dtype=float)
    r_mm = 1.15 + 0.95 * np.sqrt(counts / counts.max())     # 1.25–2.1 mm
    sizes = (r_mm * 2.835) ** 2 * np.pi

    for r, s in zip(rows, sizes):
        marker(ax, r, s)
        if not (INSET[0] <= r["lon"] <= INSET[1] and INSET[2] <= r["lat"] <= INSET[3]):
            ax.text(r["lon"] + r["dx"], r["lat"] + r["dy"], r["label"],
                    fontsize=5.3, ha="center", va="center", zorder=9, color=TEXT,
                    path_effects=[pe.withStroke(linewidth=1.4, foreground="white")])

    # --- zoom inset -----------------------------------------------------
    iax = fig.add_axes([0.035, 0.055, 0.205, 0.235])
    draw_base(iax, prov, [], lw_nation=0.9, lw_prov=0.32)
    for r, s in zip(rows, sizes):
        if not (INSET[0] <= r["lon"] <= INSET[1] and INSET[2] <= r["lat"] <= INSET[3]):
            continue
        marker(iax, r, s)
        iax.text(r["lon"] + r["dx"] * 0.75, r["lat"] + r["dy"] * 0.75, r["label"],
                 fontsize=5.6, ha="center", va="center", zorder=9, color=TEXT,
                 path_effects=[pe.withStroke(linewidth=1.3, foreground="white")])
    iax.set_xlim(INSET[0], INSET[1])
    iax.set_ylim(INSET[2], INSET[3])
    iax.set_aspect(1.0 / np.cos(np.deg2rad(26)), adjustable="box")
    iax.set_xticks([])
    iax.set_yticks([])
    for sp in iax.spines.values():
        sp.set_visible(True)
        sp.set_linewidth(0.5)
        sp.set_color(GRID)
    iax.set_title("黔西—湘西（放大）", fontsize=5.6, pad=2.0, color=TEXT)

    ax.add_patch(Rectangle((INSET[0], INSET[2]), INSET[1] - INSET[0],
                           INSET[3] - INSET[2], fill=False, edgecolor=GRID,
                           linewidth=0.55, zorder=12))

    ax.set_xlim(LON)
    ax.set_ylim(LAT)
    ax.set_aspect(1.0 / np.cos(np.deg2rad(35)), adjustable="box")
    ax.set_xticks([])
    ax.set_yticks([])
    for sp in ax.spines.values():
        sp.set_visible(False)

    # north arrow
    x, y, s_ = 0.070, 0.845, 0.024
    ax.plot([x, x], [y - s_, y + s_], transform=ax.transAxes, color=TEXT, lw=0.6,
            clip_on=False)
    ax.plot([x - s_, x + s_], [y, y], transform=ax.transAxes, color=TEXT, lw=0.6,
            clip_on=False)
    ax.text(x, y + s_ + 0.010, "N", transform=ax.transAxes, ha="center",
            va="bottom", fontsize=5.8)

    # legend: vertical stack over the Bay of Bengal (empty area west of the SCS)
    lx, ly, dy = 0.262, 0.330, 0.030
    ax.text(lx, ly + 0.026, "采纳个体数", transform=ax.transAxes, fontsize=5.8,
            va="bottom")
    for i, (c, lab) in enumerate(zip(CLASS_COLORS, CLASS_LABELS)):
        yy = ly - i * dy
        ax.scatter(lx + 0.010, yy, s=24, c=c, edgecolors="white", linewidths=0.4,
                   transform=ax.transAxes, clip_on=False, zorder=21)
        ax.text(lx + 0.024, yy, lab, transform=ax.transAxes, fontsize=5.5,
                va="center")
    yy = ly - 4.35 * dy
    ax.scatter(lx + 0.010, yy, s=24, facecolors="none", edgecolors=TEXT,
               linewidths=0.5, linestyles="--", transform=ax.transAxes,
               clip_on=False, zorder=21)
    ax.text(lx + 0.024, yy, "仅到州/平原级", transform=ax.transAxes, fontsize=5.5,
            va="center")

    # scale bar
    km, bx, by, bh = 500, 0.800, 0.045, 0.008
    w = km / (111.32 * np.cos(np.deg2rad(35))) / (LON[1] - LON[0])
    for i, c in enumerate([TEXT, "white"]):
        ax.add_patch(Rectangle((bx + i * w / 2, by), w / 2, bh,
                               transform=ax.transAxes, facecolor=c,
                               edgecolor=TEXT, lw=0.4, zorder=20))
    ax.text(bx + w / 2, by + bh + 0.007, f"{km} km", transform=ax.transAxes,
            ha="center", va="bottom", fontsize=5.2)

    total = int(counts.sum())
    fig.text(0.012, 0.962, "中国地方鸡种重测序采样点分布", fontsize=8.6, ha="left")
    fig.text(0.012, 0.933,
             f"{total} 只个体 · {len(rows)} 个采样点 · "
             f"{sum(r['records'] for r in rows)} 条记录（按县/市定位；虚线圆为州/平原级）",
             fontsize=5.9, color="#5A6B7B", ha="left")
    fig.text(0.012, 0.010,
             "数据源：label1029.xlsx 蓝色标注行（FF0070C0）；坐标取县/市政府驻地；"
             "配色取 style 库 pangenome_spectrum。",
             fontsize=4.6, color="#6B7A88")

    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)
    png, pdf = out / f"{args.stem}.png", out / f"{args.stem}.pdf"
    fig.savefig(png, dpi=DPI_PNG, facecolor="white")
    fig.savefig(pdf, facecolor="white")
    print(f"saved -> {png}")
    print(f"{total} individuals / {len(rows)} sites")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
