#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
China sampling map — adopted WGS samples of Chinese indigenous chicken breeds.

Reads an aggregated per-province table (province, individuals, records, breeds)
and renders a MaxEnt-style four-class choropleth of China: province borders,
national border, nine-dash line, South China Sea islands, graduated legend.

Only aggregated counts live in this repository. Individual accessions and the
source workbook stay in the research workspace — see PRIVACY note in README.

    python3 plot_china_sampling_map.py --lang en
    python3 plot_china_sampling_map.py --lang zh --outdir .
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
from matplotlib.collections import LineCollection  # noqa: E402
from matplotlib.font_manager import FontProperties, findfont  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import PathPatch, Patch, Rectangle  # noqa: E402
from matplotlib.path import Path as MPath  # noqa: E402
import matplotlib.patheffects as pe  # noqa: E402

HERE = Path(__file__).resolve().parent

# --- canvas -----------------------------------------------------------------
LON = (72.0, 136.0)
LAT = (3.0, 55.0)
FIG_W, FIG_H = 5.85, 6.05          # inches ≈ 149 × 154 mm
DPI_PNG = 600

# --- four-class ramp (pangenome_spectrum: light → deep blue) -----------------
CLASS_COLORS = ["#E9EEF1", "#B4AD74", "#5899B2", "#386C8C"]
BREAKS = [20, 50]                  # 1–19 / 20–49 / ≥50 individuals
LABELS_EN = ["None", "1–19", "20–49", "≥50"]
LABELS_ZH = ["无", "1–19", "20–49", "≥50"]

TEXT = "#273746"
GRID = "#A9B2BB"
FONT_EN = ["Arial", "Helvetica", "Liberation Sans", "DejaVu Sans"]
FONT_ZH = ["PingFang SC", "Heiti SC", "Songti SC", "Arial Unicode MS",
           "Noto Sans CJK SC", "DejaVu Sans"]


# ---------------------------------------------------------------------------
# geometry helpers
# ---------------------------------------------------------------------------
def _geoms(obj: dict):
    if obj.get("type") == "FeatureCollection":
        for f in obj["features"]:
            yield f.get("geometry", f), f.get("properties", {})
    elif obj.get("type") == "Feature":
        yield obj["geometry"], obj.get("properties", {})
    else:
        yield obj, obj.get("properties", {})


def _rings(geom: dict):
    t, c = geom["type"], geom["coordinates"]
    polys = [c] if t == "Polygon" else c if t == "MultiPolygon" else []
    out = []
    for poly in polys:
        for ring in poly[:1]:          # exterior rings only
            arr = np.asarray(ring, dtype=float)
            if arr.shape[0] >= 4:
                out.append(arr)
    return out


def _lines(geom: dict):
    t, c = geom["type"], geom["coordinates"]
    if t == "LineString":
        return [np.asarray(c, dtype=float)]
    if t == "MultiLineString":
        return [np.asarray(l, dtype=float) for l in c]
    return []


def rings_to_path(rings) -> MPath:
    verts, codes = [], []
    for r in rings:
        verts.append(r)
        codes.append(np.r_[MPath.MOVETO, [MPath.LINETO] * (len(r) - 2),
                           MPath.CLOSEPOLY])
    return MPath(np.concatenate(verts), np.concatenate(codes).astype(np.uint8))


def centroid(ring: np.ndarray) -> tuple[float, float]:
    x, y = ring[:, 0], ring[:, 1]
    x1, y1 = np.roll(x, -1), np.roll(y, -1)
    cr = x * y1 - x1 * y
    a = cr.sum() / 2.0
    return float(((x + x1) * cr).sum() / (6 * a)), float(((y + y1) * cr).sum() / (6 * a))


def _area(ring: np.ndarray) -> float:
    x, y = ring[:, 0], ring[:, 1]
    return 0.5 * abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))


def load_provinces(path: Path) -> dict[str, list[np.ndarray]]:
    obj = json.loads(path.read_text())
    out: dict[str, list[np.ndarray]] = {}
    for geom, props in _geoms(obj):
        name = props.get("name")
        if not name or str(props.get("adcode")) == "100000_JD":
            continue
        out[name] = _rings(geom)
    return out


def load_maritime(path: Path):
    obj = json.loads(path.read_text())
    out = []
    for geom, _ in _geoms(obj):
        out += _lines(geom)
    return out


# ---------------------------------------------------------------------------
# drawing
# ---------------------------------------------------------------------------
def compass(ax, x=0.055, y=0.855, size=0.028):
    ax.plot([x, x], [y - size, y + size], transform=ax.transAxes, color=TEXT,
            lw=0.6, clip_on=False, zorder=20)
    ax.plot([x - size, x + size], [y, y], transform=ax.transAxes, color=TEXT,
            lw=0.6, clip_on=False, zorder=20)
    ax.text(x, y + size + 0.012, "N", transform=ax.transAxes, ha="center",
            va="bottom", fontsize=6, color=TEXT, zorder=20)


def scalebar(ax, km=500, x=0.430, y=0.030, h=0.008):
    span = km / (111.32 * np.cos(np.deg2rad(35)))
    w = span / (LON[1] - LON[0])
    for i, c in enumerate(["black", "white"]):
        ax.add_patch(Rectangle((x + i * w / 2, y), w / 2, h,
                               transform=ax.transAxes, facecolor=c,
                               edgecolor="black", lw=0.4, zorder=20))
    ax.text(x + w / 2, y + h + 0.008, f"{km} km", transform=ax.transAxes,
            ha="center", va="bottom", fontsize=5.5, color=TEXT, zorder=20)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--counts", default=str(HERE / "china_sampling_counts.tsv"))
    ap.add_argument("--geo", default=str(HERE / "data" / "china_provinces.geojson"))
    ap.add_argument("--maritime", default=str(HERE / "data" / "china_maritime.geojson"))
    ap.add_argument("--lang", choices=["en", "zh"], default="en")
    ap.add_argument("--outdir", default=str(HERE))
    ap.add_argument("--stem", default="china_sampling_map")
    args = ap.parse_args(argv)

    lang = args.lang
    labels = LABELS_ZH if lang == "zh" else LABELS_EN
    name_key = "province_cn" if lang == "zh" else "province_en"

    # fonts -------------------------------------------------------------
    family = FONT_ZH if lang == "zh" else FONT_EN
    try:
        fp = FontProperties(family=family)
        resolved = findfont(fp, fallback_to_default=False)
    except Exception:
        resolved = None
    if resolved is None and lang == "zh":
        print("WARNING: no CJK font found — Chinese labels will render as boxes.",
              file=sys.stderr)
    plt.rcParams.update({
        "font.family": family,
        "text.color": TEXT,
        "axes.linewidth": 0.0,
        "pdf.fonttype": 42,          # editable text in the PDF
        "ps.fonttype": 42,
    })

    # data --------------------------------------------------------------
    rows = []
    with open(args.counts, encoding="utf-8") as fh:
        header = fh.readline().rstrip("\n").split("\t")
        for line in fh:
            if not line.strip():
                continue
            rec = dict(zip(header, line.rstrip("\n").split("\t")))
            for k in ("individuals", "records", "breeds"):
                rec[k] = int(rec[k])
            for k in ("dx", "dy"):
                rec[k] = float(rec.get(k) or 0)
            rows.append(rec)

    def klass(n: int) -> int:
        if n <= 0:
            return 0
        return 1 + sum(n >= b for b in BREAKS)

    for f in (args.geo, args.maritime):
        if not Path(f).exists():
            sys.exit(f"missing boundary file: {f}\n"
                     "see 'Boundary data' in README.md for the two curl commands")

    prov = load_provinces(Path(args.geo))
    maritime = load_maritime(Path(args.maritime))
    data = {r["province_cn"]: r for r in rows}   # GeoJSON 的 name 是中文名

    # figure ------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
    fig.subplots_adjust(left=0.015, right=0.985, top=0.885, bottom=0.030)

    all_rings = [r for rings in prov.values() for r in rings]

    # national border: thick stroke under the fills, inner half gets covered
    ax.add_collection(LineCollection(all_rings, colors=TEXT, linewidths=1.5,
                                     zorder=1))
    # province fills
    for name, rings in prov.items():
        rec = data.get(name)
        color = CLASS_COLORS[klass(rec["individuals"])] if rec else CLASS_COLORS[0]
        ax.add_patch(PathPatch(rings_to_path(rings), facecolor=color,
                               edgecolor="none", zorder=2))
    # province borders / nine-dash line
    ax.add_collection(LineCollection(all_rings, colors=GRID,
                                     linewidths=0.22, zorder=3))
    ax.add_collection(LineCollection(maritime, colors=TEXT, linewidths=0.8,
                                     zorder=4))

    # frame -------------------------------------------------------------
    ax.set_xlim(LON)
    ax.set_ylim(LAT)
    ax.set_aspect(1.0 / np.cos(np.deg2rad(35)), adjustable="box")
    ax.set_xticks([])
    ax.set_yticks([])
    for sp in ax.spines.values():
        sp.set_visible(False)

    compass(ax)
    scalebar(ax)

    total = sum(r["individuals"] for r in rows)
    n_rec = sum(r["records"] for r in rows)
    n_prov = len(rows)
    subtitle = (f"{total} individuals · {n_rec} breed records · {n_prov} provinces"
                if lang == "en" else
                f"{total} 只个体 · {n_rec} 条品种记录 · {n_prov} 个省份")
    title = ("Adopted WGS samples of Chinese indigenous chicken breeds"
             if lang == "en" else "中国地方鸡种重测序采样个体分布")
    ax.set_title(title, fontsize=7.0, pad=14, loc="left", x=0.02)
    ax.text(0.02, 1.005, subtitle, transform=ax.transAxes, fontsize=6.0,
            color="#5A6B7B", va="bottom", ha="left")

    # legend ------------------------------------------------------------
    handles = [Patch(facecolor=c, edgecolor="#9AA5AE" if i == 0 else "none",
                     linewidth=0.5, label=labels[i])
               for i, c in enumerate(CLASS_COLORS)]
    leg = ax.legend(handles=handles, loc="lower left", bbox_to_anchor=(0.012, 0.012),
                    frameon=False, fontsize=6.0, handlelength=1.0,
                    handleheight=0.8, columnspacing=1.0, handletextpad=0.45,
                    ncol=4, borderpad=0.0,
                    title="Adopted individuals" if lang == "en" else "采纳个体数",
                    title_fontsize=6.0)
    leg._legend_box.align = "left"

    # provenance --------------------------------------------------------
    src = ("Source: label1029.xlsx - rows shaded blue (FF0070C0) or tagged as "
           "in-house data; counts aggregated per province."
           if lang == "en" else
           "数据源：label1029.xlsx 中蓝色标注行及“本实验室数据”行，按省汇总。")
    fig.text(0.01, 0.012, src, fontsize=4.6, color="#6B7A88", ha="left", va="bottom")

    # save --------------------------------------------------------------
    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)
    suffix = "" if lang == "en" else "_zh"
    png = out / f"{args.stem}{suffix}.png"
    pdf = out / f"{args.stem}{suffix}.pdf"
    fig.savefig(png, dpi=DPI_PNG, facecolor="white")
    fig.savefig(pdf, facecolor="white")
    print(f"saved -> {png}")
    print(f"saved -> {pdf}")
    print(f"{total} individuals / {n_rec} records / {n_prov} provinces")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
