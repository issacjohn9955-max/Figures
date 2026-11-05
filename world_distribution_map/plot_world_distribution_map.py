#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Two-panel distribution map: world + China zoom, labels on the outer margins
connected to their sampling points by thin leader lines.

Layout mirrors the common "world map + China inset" figure in chicken / livestock
pangenome papers: the maps stay clean (no text on top of the geography), every
sample name sits outside the map and a 0.3 pt leader line points to its dot.

Colours come from the house style (figure-style/style/theme.json,
palettes.json): ink #273746, boundary #A9B2BB, land #F4F7F9.  Basemap tints are
style-level neutrals, no gradients (the reference figure uses a photographic
relief basemap, which is not reproducible from the style layer).

Input contract (TSV, tab separated, header required):
    sample   panel   lon   lat   note
    Anhui    china   117.3 31.9  demo

* panel ∈ {world, china} – which panel the row belongs to (a row may appear in
  both panels if you duplicate it with a different panel value).
* lon / lat in decimal degrees, WGS-84.
* sample is the label printed in the margin; keep it short (< 18 characters).

    python3 plot_world_distribution_map.py                 # demo table
    python3 plot_world_distribution_map.py --samples my.tsv --stem fig1_map
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.collections import LineCollection, PolyCollection  # noqa: E402

HERE = Path(__file__).resolve().parent

# --- house style -------------------------------------------------------------
TEXT = "#273746"      # ink
BORDER = "#A9B2BB"    # boundary / hairline grey-blue
LAND = "#F4F7F9"      # land fill (same neutral as the province map module)
OCEAN = "#FFFFFF"
HAIR = "#E3E9ED"
FONT = ["Arial", "Helvetica", "Liberation Sans", "DejaVu Sans"]

BASEMAPS = {
    # journal-safe flat basemap (default)
    "paper": dict(ocean=OCEAN, land=LAND, border=BORDER),
    # warmer stand-in for a relief basemap; still flat, no gradients
    "terrain": dict(ocean="#DDE8EF", land="#EDE6D6", border="#9EA9B0"),
}

WORLD_XLIM, WORLD_YLIM = (-180.0, 180.0), (-58.0, 84.0)
CHINA_XLIM, CHINA_YLIM = (73.0, 136.0), (17.0, 55.0)

# 260 x 95 mm wide panel: world + China zoom, four label columns
FIG_W, FIG_H = 10.24, 3.70
DPI_PNG = 600

WORLD_AX = [0.070, 0.165, 0.465, 0.670]
CHINA_AX = [0.668, 0.225, 0.235, 0.550]


# --- geojson helpers ---------------------------------------------------------
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
        for ring in poly[:1]:          # outer ring only at this scale
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



def draw_world(ax, geo_path, bm, lw_border=0.18, relief=None):
    rings = []
    for geom, _ in _geoms(json.loads(Path(geo_path).read_text())):
        if geom.get("type") in ("Polygon", "MultiPolygon"):
            rings += _rings(geom)
    if relief:
        from PIL import Image
        img = np.asarray(Image.open(relief).convert("RGB"))
        ax.imshow(img, extent=(-180, 180, -90, 90), aspect="auto",
                  zorder=0, interpolation="bilinear")
    else:
        ax.add_collection(PolyCollection(rings, facecolors=bm["land"],
                                         edgecolors="none", zorder=1))
    ax.add_collection(LineCollection(rings, colors=bm["border"],
                                     linewidths=lw_border, zorder=2))


def draw_china(ax, province_path, maritime_path, bm,
               lw_prov=0.18, lw_mar=0.55, relief=None):
    prov = {}
    for geom, props in _geoms(json.loads(Path(province_path).read_text())):
        name = props.get("name")
        if name and str(props.get("adcode")) != "100000_JD":
            prov[name] = _rings(geom)
    all_rings = [r for v in prov.values() for r in v]
    if relief:
        from PIL import Image
        img = np.asarray(Image.open(relief).convert("RGB"))
        # the raster is a global plate-carree grid, so the China panel simply
        # shows the 73-136E / 17-55N crop of the same image
        ax.imshow(img, extent=(-180, 180, -90, 90), aspect="auto",
                  zorder=0, interpolation="bilinear")
    else:
        ax.add_collection(PolyCollection(all_rings, facecolors=bm["land"],
                                         edgecolors="none", zorder=1))
    ax.add_collection(LineCollection(all_rings, colors=bm["border"],
                                     linewidths=lw_prov, zorder=2))
    # national outline: thicker pass over the same rings looks acceptable at
    # 5 cm print size and avoids needing a separate boundary layer
    ax.add_collection(LineCollection(all_rings, colors=TEXT,
                                     linewidths=0.30, zorder=2.5))
    ax.add_collection(LineCollection(all_rings, colors=bm["land"],
                                     linewidths=0.20, zorder=2.6))
    mar = []
    for geom, _ in _geoms(json.loads(Path(maritime_path).read_text())):
        mar += _lines(geom)
    if mar:
        ax.add_collection(LineCollection(mar, colors=TEXT,
                                         linewidths=lw_mar, zorder=4))


# --- labels ------------------------------------------------------------------
def leader_labels(ax, rows, sizes=None, fontsize=5.2, pad=0.012, y_top=0.950,
                  y_bot=0.050, line_lw=0.30, marker_s=12.0):
    """Stack labels outside the axes and connect each one to its point."""
    for side in ("left", "right"):
        group = [r for r in rows if r["side"] == side]
        group.sort(key=lambda r: -r["lat"])          # north at the top
        if not group:
            continue
        ys = (np.linspace(y_top, y_bot, len(group)) if len(group) > 1
              else [0.5 * (y_top + y_bot)])
        for r, y in zip(group, ys):
            x = -pad if side == "left" else 1.0 + pad
            ax.annotate(
                r["sample"], xy=(r["lon"], r["lat"]), xycoords="data",
                xytext=(x, y), textcoords="axes fraction",
                ha="right" if side == "left" else "left", va="center",
                fontsize=fontsize, color=TEXT, annotation_clip=False,
                arrowprops=dict(arrowstyle="-", lw=line_lw, color=TEXT,
                                shrinkA=2.0, shrinkB=2.6),
            )
    sizes = sizes if sizes is not None else [marker_s] * len(rows)
    ax.scatter([r["lon"] for r in rows], [r["lat"] for r in rows],
               s=sizes, facecolors="white", edgecolors=TEXT,
               linewidths=0.45, zorder=10)


def marker_sizes(rows):
    counts = np.array([r.get("individuals", 1) or 1 for r in rows], dtype=float)
    r_mm = 1.15 + 0.95 * np.sqrt(counts / counts.max())
    return (r_mm * 2.835) ** 2 * np.pi


def style_axis(ax, xlim, ylim, aspect_lat):
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.set_aspect(1.0 / np.cos(np.deg2rad(aspect_lat)), adjustable="box")
    ax.set_xticks([])
    ax.set_yticks([])
    for sp in ax.spines.values():
        sp.set_visible(True)
        sp.set_linewidth(0.45)
        sp.set_color(BORDER)


# --- IO ----------------------------------------------------------------------
def read_samples(path):
    head, rows = None, []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if not line:
                continue
            if head is None:
                head = line.split("\t")
                continue
            d = dict(zip(head, line.split("\t")))
            rows.append(dict(sample=d["sample"].strip(),
                             panel=d["panel"].strip().lower(),
                             lon=float(d["lon"]), lat=float(d["lat"]),
                             individuals=int(float(d.get("individuals") or 1)),
                             side=d.get("side", "").strip().lower()))
    return rows


def assign_side(rows, panel):
    """Split labels between the two margins.

    An explicit `side` column wins.  Otherwise the panel's points are split at
    their median longitude, which keeps the two label stacks balanced; a fixed
    cut-off puts nearly every Chinese point on the same side and the labels
    collide.
    """
    grp = [r for r in rows if r["panel"] == panel]
    if not grp:
        return
    auto = [r for r in grp if r["side"] not in ("left", "right")]
    if auto:
        cut = float(np.median([r["lon"] for r in auto]))
        for r in auto:
            r["side"] = "left" if r["lon"] < cut else "right"
    for r in grp:
        if r["side"] not in ("left", "right"):
            r["side"] = "left"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="world + China distribution map")
    ap.add_argument("--samples", default=str(HERE / "samples.tsv"))
    ap.add_argument("--world-geo", default=str(HERE / "data" / "world_countries_110m.geojson"))
    ap.add_argument("--china-geo", default=str(HERE / "data" / "china_provinces.geojson"))
    ap.add_argument("--maritime", default=str(HERE / "data" / "china_maritime.geojson"))
    ap.add_argument("--basemap", default="paper", choices=sorted(BASEMAPS))
    ap.add_argument("--relief", default=None,
                    help="optional equirectangular raster drawn behind the world "
                         "panel (e.g. Natural Earth NE1_50M_SR_W; not shipped)")
    ap.add_argument("--outdir", default=str(HERE))
    ap.add_argument("--stem", default="fig_world_distribution")
    ap.add_argument("--labels", action="store_true", default=True,
                    help="margin labels with leader lines (default: on)")
    ap.add_argument("--no-labels", dest="labels", action="store_false")
    ap.add_argument("--label-panels", default="both",
                    choices=("both", "world", "china", "none"),
                    help="which panel gets margin labels (default: both)")
    ap.add_argument("--sizes-panel", default="china",
                    choices=("china", "world", "both"),
                    help="which panel scales circles by the individuals column")
    ap.add_argument("--locator", action="store_true",
                    help="draw the China-panel extent as a box on the world map")
    ap.add_argument("--panel-letters", action="store_true", default=True)
    ap.add_argument("--no-panel-letters", dest="panel_letters", action="store_false")
    args = ap.parse_args(argv)

    for f in (args.samples, args.world_geo, args.china_geo, args.maritime):
        if not Path(f).exists():
            raise SystemExit(f"missing input: {f}")
    if args.relief and not Path(args.relief).exists():
        raise SystemExit(f"missing relief raster: {args.relief}")

    plt.rcParams.update({
        "font.family": FONT,
        "text.color": TEXT,
        "axes.linewidth": 0.0,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    })

    rows = read_samples(args.samples)
    for panel in ("world", "china"):
        assign_side(rows, panel)
    world = [r for r in rows if r["panel"] == "world"]
    china = [r for r in rows if r["panel"] == "china"]

    bm = BASEMAPS[args.basemap]
    fig = plt.figure(figsize=(FIG_W, FIG_H))

    ax_w = fig.add_axes(WORLD_AX)
    draw_world(ax_w, args.world_geo, bm, relief=args.relief)
    style_axis(ax_w, WORLD_XLIM, WORLD_YLIM, 40.0)

    ax_c = fig.add_axes(CHINA_AX)
    draw_china(ax_c, args.china_geo, args.maritime, bm, relief=args.relief)
    style_axis(ax_c, CHINA_XLIM, CHINA_YLIM, 30.0)

    want = {"both": ("world", "china"), "world": ("world",),
            "china": ("china",), "none": ()}[args.label_panels] if args.labels else ()
    # circle area can encode individuals, but only on the panel where the sites
    # are actually distinguishable; on the world panel the 21 Chinese sites sit
    # on top of each other, so uniform small dots read better
    w_sizes = marker_sizes(world) if args.sizes_panel in ("world", "both") else 11.0
    c_sizes = marker_sizes(china) if args.sizes_panel in ("china", "both") else 11.0

    def _dots(ax, grp, sz):
        ax.scatter([r["lon"] for r in grp], [r["lat"] for r in grp], s=sz,
                   facecolors="white", edgecolors=TEXT, linewidths=0.45, zorder=10)

    if "world" in want:
        leader_labels(ax_w, world, sizes=w_sizes, fontsize=5.0, pad=0.012)
    else:
        _dots(ax_w, world, w_sizes)
    if "china" in want:
        leader_labels(ax_c, china, sizes=c_sizes, fontsize=4.9, pad=0.020)
    else:
        _dots(ax_c, china, c_sizes)

    if args.locator:
        from matplotlib.patches import Rectangle
        ax_w.add_patch(Rectangle((CHINA_XLIM[0], CHINA_YLIM[0]),
                                 CHINA_XLIM[1] - CHINA_XLIM[0],
                                 CHINA_YLIM[1] - CHINA_YLIM[0],
                                 fill=False, edgecolor=TEXT, linewidth=0.55,
                                 zorder=12))

    if args.panel_letters:
        for ax, letter in ((ax_w, "a"), (ax_c, "b")):
            ax.text(0.0, 1.015, letter, transform=ax.transAxes, fontsize=7.0,
                    fontweight="bold", color=TEXT, ha="left", va="bottom")

    stem = Path(args.outdir) / args.stem
    for ext, kw in (("png", dict(dpi=DPI_PNG)), ("pdf", {})):
        fig.savefig(f"{stem}.{ext}", facecolor="white", **kw)
    print(f"wrote {stem}.png / {stem}.pdf  ({len(world)} world, {len(china)} china)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
