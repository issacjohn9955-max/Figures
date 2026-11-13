#!/usr/bin/env python3
"""Figure 1C - population tree wired to the admixture plot.

Left/above: neighbour-joining tree of the 13 breeds (Rogers' distance on 40k
LD-pruned SNPs). Below: per-individual ancestry proportions (LEA snmf, K = 3
and K = 2). Every tree tip drops straight into the centre of its breed block,
so the two panels read as one object.

Usage
-----
python3 plot_fig1c_tree_admixture.py --data-dir data --out fig1c_tree_admixture
"""
import argparse
import csv
import os

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
from matplotlib.font_manager import FontProperties

def _cjk_font():
    """First available CJK face: macOS, then Linux/CI, else the default."""
    for path in ("/System/Library/Fonts/Hiragino Sans GB.ttc",
                 "/System/Library/Fonts/PingFang.ttc",
                 "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
                 "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"):
        if os.path.exists(path):
            return FontProperties(fname=path)
    for fam in ("Noto Sans CJK SC", "Source Han Sans SC", "WenQuanYi Zen Hei", "SimHei"):
        try:
            return FontProperties(family=fam)
        except Exception:
            continue
    return FontProperties()


CJK = _cjk_font()

MM = 1 / 25.4
INK = "#1B2430"
GREY = "#6B7280"

ZONE_COLOURS = {"North": "#0072B2", "Middle": "#009E73",
                "Northwest": "#D55E00", "Southeast": "#CC79A7"}
ZONE_ORDER = ["North", "Middle", "Northwest", "Southeast"]

ADMIX = {2: ["#4C6E9C", "#D9A441"],
         3: ["#3E5C76", "#7FA88B", "#C9705E"]}


def read_tsv(path):
    with open(path, encoding="utf-8") as fh:
        return list(csv.DictReader(fh, delimiter="\t"))


def nj(dist, names):
    n = len(names)
    d = {}
    for i in range(n):
        for j in range(i + 1, n):
            d[(i, j)] = d[(j, i)] = float(dist[i, j])
    nodes = {i: {"children": [], "len": 0.0, "name": names[i]} for i in range(n)}
    active, nxt = list(range(n)), n

    while len(active) > 2:
        m = len(active)
        r = {a: sum(d[(a, b)] for b in active if b != a) for a in active}
        best = None
        for x in range(m):
            for y in range(x + 1, m):
                a, b = active[x], active[y]
                q = (m - 2) * d[(a, b)] - r[a] - r[b]
                if best is None or q < best[0]:
                    best = (q, a, b)
        _, i, j = best
        dij = d[(i, j)]
        li = 0.5 * dij + (r[i] - r[j]) / (2 * (m - 2))
        nodes[i]["len"] = max(li, 0.0)
        nodes[j]["len"] = max(dij - li, 0.0)
        u = nxt
        nxt += 1
        nodes[u] = {"children": [i, j], "len": 0.0, "name": None}
        for k in active:
            if k in (i, j):
                continue
            d[(u, k)] = d[(k, u)] = 0.5 * (d[(i, k)] + d[(j, k)] - dij)
        active = [k for k in active if k not in (i, j)] + [u]

    a, b = active
    nodes[a]["len"] = nodes[b]["len"] = d[(a, b)] / 2
    root = nxt
    nodes[root] = {"children": [a, b], "len": 0.0, "name": None}
    return nodes, root


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default="data")
    ap.add_argument("--out", default="fig1c_tree_admixture")
    ap.add_argument("--dpi", type=int, default=600)
    args = ap.parse_args()

    dist_rows = read_tsv(os.path.join(args.data_dir, "breed_dist.tsv"))
    breeds = [r["breed"] for r in dist_rows]
    D = np.array([[float(r[b]) for b in breeds] for r in dist_rows])

    samples = read_tsv(os.path.join(args.data_dir, "samples_meta.tsv"))
    q3 = np.loadtxt(os.path.join(args.data_dir, "Q_k3.tsv"))
    q2 = np.loadtxt(os.path.join(args.data_dir, "Q_k2.tsv"))
    q2 = q2[: len(q3)] if q2.shape[0] != q3.shape[0] else q2
    zones = {r["breed"]: r["zone"] for r in read_tsv(os.path.join(args.data_dir, "groups_zone.tsv"))}

    # individuals grouped by breed, breeds in tree order
    idx_of_breed = {b: [i for i, s in enumerate(samples) if s["breed"] == b] for b in breeds}

    nodes, root = nj(D, breeds)

    # ---- tip order + tree layout -------------------------------------
    order = []

    def walk(u):
        if nodes[u]["name"] is not None:
            order.append(u)
            return
        for c in nodes[u]["children"]:
            walk(c)

    walk(root)

    gap = 2.4
    width_of = {b: len(idx_of_breed[b]) for b in breeds}
    x_center, x = {}, 1.0
    for b in order and [nodes[u]["name"] for u in order]:
        x_center[b] = x + (width_of[b] - 1) / 2
        x += width_of[b] + gap
    total_w = x

    depth = {root: 0}
    stack = [root]
    while stack:
        u = stack.pop()
        for c in nodes[u]["children"]:
            depth[c] = depth[u] + 1
            stack.append(c)

    # every tip ends on the same baseline
    for u, nd in nodes.items():
        if nd["name"] is not None:
            depth[u] = max(depth.values())

    def xpos(u):
        if nodes[u]["name"] is not None:
            return x_center[nodes[u]["name"]]
        xs = [xpos(c) for c in nodes[u]["children"]]
        return sum(xs) / len(xs)

    ymax = max(depth.values())

    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["PingFang SC", "Noto Sans CJK SC", "WenQuanYi Zen Hei",
                            "Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"],
        "pdf.fonttype": 42,
        "axes.unicode_minus": False,
    })

    fig = plt.figure(figsize=(176 * MM, 104 * MM))
    ax = fig.add_axes([0.045, 0.085, 0.92, 0.83])

    # ---- tree (root at top, tips at y = 0) ---------------------------
    segs = []
    for u, nd in nodes.items():
        if nd["name"] is not None:
            continue
        kids = nd["children"]
        x0, x1 = min(xpos(k) for k in kids), max(xpos(k) for k in kids)
        y = ymax - depth[u]
        segs.append([(x0, y), (x1, y)])
        for k in kids:
            segs.append([(xpos(k), y), (xpos(k), ymax - depth[k])])
    ax.add_collection(LineCollection(segs, colors="#2B3440", linewidths=0.72,
                                     capstyle="projecting", joinstyle="miter"))

    # ---- admixture ---------------------------------------------------
    top3, h3 = -2.55, 2.10
    top2, h2 = top3 - h3 - 0.30, 0.72

    def bars(Q, base, height, colours):
        for b in [nodes[u]["name"] for u in order]:
            for i in idx_of_breed[b]:
                xleft = x_center[b] - (width_of[b] - 1) / 2 + idx_of_breed[b].index(i)
                bottom = 0.0
                for k, c in enumerate(colours):
                    ax.add_patch(Rectangle((xleft - 0.52, base - (bottom + Q[i, k]) * height),
                                           1.04, Q[i, k] * height, facecolor=c,
                                           edgecolor=c, linewidth=0.2, zorder=2))
                    bottom += Q[i, k]

    bars(q3, top3, h3, ADMIX[3])
    bars(q2, top2, h2, ADMIX[2])

    # ---- zone strip ---------------------------------------------------
    strip = top2 - h2 - 0.28
    for b in [nodes[u]["name"] for u in order]:
        xleft = x_center[b] - (width_of[b] - 1) / 2
        ax.add_patch(Rectangle((xleft - 0.5, strip), width_of[b], 0.16,
                               facecolor=ZONE_COLOURS.get(zones.get(b, ""), "#BBBBBB"),
                               edgecolor="none", zorder=2))

    ax.set_xlim(0, total_w)
    ax.set_ylim(strip - 0.30, ymax * 1.10)
    ax.axis("off")

    # ---- labels -------------------------------------------------------
    for i, u in enumerate(order):
        b = nodes[u]["name"]
        ly = -0.18 if i % 2 == 0 else -1.28
        ax.plot([x_center[b], x_center[b]], [0.0, ly + 0.16], color="#2B3440",
                lw=0.72, zorder=3)
        ax.text(x_center[b], ly, b, fontsize=5.3, color=INK, ha="center",
                va="top", fontproperties=CJK)

    ax.text(-3.5, ymax * 0.45, "NJ tree", rotation=90, fontsize=6.2, color=GREY,
            ha="center", va="center")
    ax.text(-3.5, top3 - h3 / 2, "K = 3", rotation=90, fontsize=6.2, color=GREY,
            ha="center", va="center")
    ax.text(-3.5, top2 - h2 / 2, "K = 2", rotation=90, fontsize=5.8, color=GREY,
            ha="center", va="center")

    handles = [Line2D([], [], marker="s", linestyle="none", markersize=4.4,
                      markerfacecolor=ZONE_COLOURS[z], markeredgecolor="none", label=z)
               for z in ZONE_ORDER]
    leg = fig.legend(handles=handles, loc="lower center", ncol=4, frameon=False,
                     fontsize=5.6, handletextpad=0.4, columnspacing=1.4,
                     bbox_to_anchor=(0.5, 0.005), title="Climate zone", title_fontsize=5.6)
    leg.get_title().set_color(GREY)
    leg.get_title().set_style("italic")

    # ancestry component key
    comp = [Line2D([], [], marker="s", linestyle="none", markersize=4.2,
                   markerfacecolor=c, markeredgecolor="none", label=f"C{i+1}")
            for i, c in enumerate(ADMIX[3])]
    leg2 = fig.legend(handles=comp, loc="upper left", ncol=3, frameon=False,
                      fontsize=5.4, handletextpad=0.35, columnspacing=1.1,
                      bbox_to_anchor=(0.045, 0.945), title="Ancestry (K = 3)",
                      title_fontsize=5.4)
    leg2.get_title().set_color(GREY)
    leg2.get_title().set_style("italic")

    fig.text(0.955, 0.955, "cladogram · branch lengths not to scale",
             fontsize=5.2, color=GREY, ha="right")
    fig.text(0.045, 0.972, "C", fontsize=10, fontweight="bold", color=INK)
    fig.text(0.068, 0.966, f"{len(samples)} individuals · {len(breeds)} breeds · ordered by the tree",
             fontsize=5.5, color=GREY)

    for ext in ("png", "pdf"):
        path = f"{args.out}.{ext}"
        fig.savefig(path, dpi=args.dpi)
        print("wrote", path)


if __name__ == "__main__":
    main()
