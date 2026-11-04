#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
China sampling sites — latitude/longitude point map.

Each marker is one collection site (county / city seat, or the named production
region when the record is only region-level). Marker colour and size encode the
number of adopted individuals; the numbered list on the right carries breed,
origin and counts.

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
FIG_W, FIG_H = 7.45, 6.15          # inches ≈ 189 × 156 mm
DPI_PNG = 600

CLASS_COLORS = ["#B0A81E", "#E8891B", "#C8102E", "#7A1020"]
BREAKS = [10, 20, 30]              # 1–9 / 10–19 / 20–29 / ≥30
CLASS_LABELS = ["1–9", "10–19", "20–29", "≥30"]

TEXT = "#273746"
FONT = ["PingFang SC", "Heiti SC", "Songti SC", "Arial Unicode MS",
        "Noto Sans CJK SC", "DejaVu Sans"]


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
    all_rings = [r for v in prov.values() for r in v]

    fig = plt.figure(figsize=(FIG_W, FIG_H))
    ax = fig.add_axes([0.004, 0.03, 0.630, 0.885])
    axl = fig.add_axes([0.648, 0.03, 0.348, 0.885])
    axl.axis("off")

    # --- map base -------------------------------------------------------
    ax.add_collection(LineCollection(all_rings, colors="black", linewidths=2.0,
                                     zorder=1))
    for rings in prov.values():
        ax.add_patch(PathPatch(rings_to_path(rings), facecolor="#F4F4F2",
                               edgecolor="none", zorder=2))
    ax.add_collection(LineCollection(all_rings, colors="#9AA5AE", linewidths=0.22,
                                     zorder=3))
    ax.add_collection(LineCollection(maritime, colors="black", linewidths=0.85,
                                     zorder=4))

    # --- points ---------------------------------------------------------
    INSET = (103.4, 111.0, 24.1, 28.6)
    counts = np.array([r["individuals"] for r in rows], dtype=float)
    r_mm = 0.95 + 0.75 * np.sqrt(counts / counts.max())     # 1.0–1.7 mm
    s = (r_mm * 2.835) ** 2 * np.pi

    for r, size in zip(rows, s):
        c = CLASS_COLORS[klass(r["individuals"])]
        if r["precision"] == "region":
            ax.scatter(r["lon"], r["lat"], s=size, facecolors="none",
                       edgecolors=c, linewidths=0.9, linestyles="--", zorder=8)
        else:
            ax.scatter(r["lon"], r["lat"], s=size, c=c, edgecolors="white",
                       linewidths=0.45, zorder=8)
        if not (INSET[0] <= r["lon"] <= INSET[1] and INSET[2] <= r["lat"] <= INSET[3]):
            ax.text(r["lon"] + r["dx"], r["lat"] + r["dy"], str(r["id"]),
                    fontsize=5.4, ha="center", va="center", zorder=9, color=TEXT,
                    path_effects=[pe.withStroke(linewidth=1.1, foreground="white")])

    # --- zoom inset: 黔西—湘西 (points 7/8/9/10/11/21 挤在一起) ----------
    iax = fig.add_axes([0.045, 0.058, 0.225, 0.262])
    iax.add_collection(LineCollection(all_rings, colors="black", linewidths=1.4,
                                      zorder=1))
    for rings in prov.values():
        iax.add_patch(PathPatch(rings_to_path(rings), facecolor="#F4F4F2",
                                edgecolor="none", zorder=2))
    iax.add_collection(LineCollection(all_rings, colors="#9AA5AE", linewidths=0.35,
                                      zorder=3))
    for r, size in zip(rows, s):
        if not (INSET[0] <= r["lon"] <= INSET[1] and INSET[2] <= r["lat"] <= INSET[3]):
            continue
        c = CLASS_COLORS[klass(r["individuals"])]
        if r["precision"] == "region":
            iax.scatter(r["lon"], r["lat"], s=size, facecolors="none",
                        edgecolors=c, linewidths=0.9, linestyles="--", zorder=8)
        else:
            iax.scatter(r["lon"], r["lat"], s=size, c=c, edgecolors="white",
                        linewidths=0.45, zorder=8)
        iax.text(r["lon"] + r["dx"] * 0.72, r["lat"] + r["dy"] * 0.72, str(r["id"]),
                 fontsize=5.6, ha="center", va="center", zorder=9, color=TEXT,
                 path_effects=[pe.withStroke(linewidth=1.0, foreground="white")])
    iax.set_xlim(INSET[0], INSET[1])
    iax.set_ylim(INSET[2], INSET[3])
    iax.set_aspect(1.0 / np.cos(np.deg2rad(26)), adjustable="box")
    iax.set_xticks([])
    iax.set_yticks([])
    for sp in iax.spines.values():
        sp.set_visible(True)
        sp.set_linewidth(0.5)
        sp.set_color("#7A8A96")

    iax.set_title("黔西—湘西（放大）", fontsize=5.6, pad=2.0, color="#41505C")

    # 主图上的范围框
    ax.add_patch(Rectangle((INSET[0], INSET[2]), INSET[1] - INSET[0],
                           INSET[3] - INSET[2], fill=False, edgecolor="#7A8A96",
                           linewidth=0.5, zorder=12))

    ax.set_xlim(LON)
    ax.set_ylim(LAT)
    ax.set_aspect(1.0 / np.cos(np.deg2rad(35)), adjustable="box")
    ax.set_xticks([])
    ax.set_yticks([])
    for sp in ax.spines.values():
        sp.set_visible(False)

    # north arrow + scale bar
    x, y, size_ = 0.075, 0.845, 0.026
    ax.plot([x, x], [y - size_, y + size_], transform=ax.transAxes, color=TEXT,
            lw=0.6, clip_on=False)
    ax.plot([x - size_, x + size_], [y, y], transform=ax.transAxes, color=TEXT,
            lw=0.6, clip_on=False)
    ax.text(x, y + size_ + 0.011, "N", transform=ax.transAxes, ha="center",
            va="bottom", fontsize=5.8)
    km, bx, by, bh = 500, 0.800, 0.042, 0.008
    w = km / (111.32 * np.cos(np.deg2rad(35))) / (LON[1] - LON[0])
    for i, c in enumerate(["black", "white"]):
        ax.add_patch(Rectangle((bx + i * w / 2, by), w / 2, bh, transform=ax.transAxes,
                               facecolor=c, edgecolor="black", lw=0.4, zorder=20))
    ax.text(bx + w / 2, by + bh + 0.007, f"{km} km", transform=ax.transAxes,
            ha="center", va="bottom", fontsize=5.2)

    # --- title ----------------------------------------------------------
    total = int(counts.sum())
    fig.text(0.012, 0.965, "中国地方鸡种重测序采样点分布", fontsize=9, ha="left")
    fig.text(0.012, 0.936,
             f"{total} 只个体 · {len(rows)} 个采样点 · "
             f"{sum(r['records'] for r in rows)} 条记录（按县/市定位）",
             fontsize=6.2, color="#5A6B7B", ha="left")

    # --- right-hand list ------------------------------------------------
    axl.set_xlim(0, 1)
    axl.set_ylim(0, 1)
    axl.text(0.000, 0.995, "序号", fontsize=6.2, va="top", color="#5A6B7B")
    axl.text(0.088, 0.995, "品种", fontsize=6.2, va="top", color="#5A6B7B")
    axl.text(0.560, 0.995, "原产地", fontsize=6.2, va="top", color="#5A6B7B")
    axl.text(0.985, 0.995, "个体数", fontsize=6.2, va="top", color="#5A6B7B",
             ha="right")
    axl.plot([0, 1], [0.972, 0.972], color="#C9D2D8", lw=0.5)

    top, step = 0.952, 0.0392
    for i, r in enumerate(rows):
        y = top - i * step
        if i % 2 == 0:
            axl.add_patch(Rectangle((0.0, y - 0.015), 1.0, 0.031, facecolor="#F6F8F9",
                                    edgecolor="none", zorder=0))
        axl.text(0.005, y, f"{r['id']:>2}", fontsize=5.9, va="center")
        axl.scatter(0.052, y, s=15, c=CLASS_COLORS[klass(r["individuals"])],
                    edgecolors="white", linewidths=0.4, zorder=3,
                    clip_on=False)
        axl.text(0.088, y, r["breed_cn"], fontsize=5.9, va="center")
        axl.text(0.560, y, f"{r['province_cn']}·{r['origin_cn']}", fontsize=5.9,
                 va="center", color="#41505C")
        axl.text(0.985, y, str(r["individuals"]), fontsize=5.9, va="center",
                 ha="right")

    # --- legend (bottom of list column) ---------------------------------
    ly = 0.030
    axl.text(0.000, ly + 0.030, "采纳个体数", fontsize=5.9, va="bottom")
    for i, (c, lab) in enumerate(zip(CLASS_COLORS, CLASS_LABELS)):
        x0 = 0.005 + i * 0.135
        axl.scatter(x0 + 0.012, ly, s=26, c=c, edgecolors="white", linewidths=0.4,
                    clip_on=False)
        axl.text(x0 + 0.030, ly, lab, fontsize=5.6, va="center")
    # dashed ring = region-level precision
    axl.scatter(0.560, ly, s=26, facecolors="none", edgecolors="#41505C",
                linewidths=0.5, linestyle="--", clip_on=False)
    axl.text(0.585, ly, "仅到州/平原级", fontsize=5.6, va="center")

    fig.text(0.012, 0.012,
             "数据源：label1029.xlsx 蓝色标注行（FF0070C0）；坐标取县/市政府驻地，"
             "仅省级记录的取产区代表点（虚线圆）。",
             fontsize=4.8, color="#6B7A88")

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
