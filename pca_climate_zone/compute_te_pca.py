#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
compute_te_pca.py — TE 插入位点基因型的个体级 PCA，并按气候区给样本分组
=====================================================================
用途：复刻 Yuan et al. 2026 (Zool Res) Figure 2B 的版式——PC1/PC2 散点、
按 "Climate zone" 六区着色+形状。此处用本项目的真实数据：

  基因型  /data/shine_work/12_TE_SNP_imputation_20261030/results/06_complete/
          te_alt_dosage_individual_complete.csv  (403 samples × 9,805 TE loci, 0/1/2)
  元数据  同目录 samples.tsv (breed / reviewed_longitude / reviewed_latitude)

流程
  1. 坐标 → 省级行政区（阿里 DataV 省界多边形，射线法，不依赖 shapely/GDAL）
  2. 省 → 六大农业气候区（North / Middle / Southeast / Southwest / Northwest / Xizang）
  3. 只保留中国地方鸡品种（剔除原鸡、外国商业品种、境外品种）
  4. MAF ≥ 0.05 过滤位点；矩阵按位点中心化（不标准化，与 02_workflowSNP 的
     pca_structure.py 默认一致）
  5. numpy 经济型 SVD 求主成分，输出得分表与方差表

输出
  pca_te_scores.tsv    sample, breed, province, zone, PC1..PC5
  pca_te_variance.tsv  PC, eigenvalue, variance_explained
  te_zone_counts.tsv   zone, n_samples, n_breeds

用法
  python3 compute_te_pca.py --raw raw --out . --max-maf-missing 0
"""
import argparse
import json
import os

import numpy as np
import pandas as pd

# --- 六大农业气候区（与原论文 Figure 2B 的图例命名一致）---------------------
ZONE_ORDER = ["North", "Middle", "Northwest", "Southeast", "Southwest", "Xizang"]

PROVINCE_TO_ZONE = {
    # 北方：东北 + 华北 + 黄淮海
    "黑龙江省": "North", "吉林省": "North", "辽宁省": "North",
    "内蒙古自治区": "North", "北京市": "North", "天津市": "North",
    "河北省": "North", "山西省": "North", "山东省": "North",
    "河南省": "North", "陕西省": "North",
    # 中部：长江中下游
    "江苏省": "Middle", "上海市": "Middle", "浙江省": "Middle",
    "安徽省": "Middle", "江西省": "Middle", "湖北省": "Middle",
    "湖南省": "Middle",
    # 东南：华南 + 东南沿海
    "广东省": "Southeast", "广西壮族自治区": "Southeast", "海南省": "Southeast",
    "福建省": "Southeast", "台湾省": "Southeast",
    "香港特别行政区": "Southeast", "澳门特别行政区": "Southeast",
    # 西北：蒙新干旱区
    "甘肃省": "Northwest", "宁夏回族自治区": "Northwest",
    "青海省": "Northwest", "新疆维吾尔自治区": "Northwest",
    # 西南：云贵川渝
    "四川省": "Southwest", "云南省": "Southwest", "贵州省": "Southwest",
    "重庆市": "Southwest",
    # 青藏
    "西藏自治区": "Xizang",
}

# 中国地方鸡品种（本项目 TE-403 集合里出现过的 14 个）；其余为原鸡/商业/境外品种
CHINESE_LOCAL_BREEDS = [
    "惠阳胡须鸡", "胡须鸡", "杏花鸡", "清远麻鸡", "文昌鸡",
    "广西瑶鸡", "广西三黄鸡", "郧阳大鸡", "仙居鸡", "白耳黄鸡",
    "溧阳鸡", "林甸鸡", "济宁百日鸡", "吐鲁番斗鸡",
]


def point_in_ring(x, y, ring):
    """射线法：点是否在多边形环内。ring = [[lon, lat], ...]"""
    inside = False
    n = len(ring)
    j = n - 1
    for i in range(n):
        xi, yi = ring[i][0], ring[i][1]
        xj, yj = ring[j][0], ring[j][1]
        if ((yi > y) != (yj > y)) and \
           (x < (xj - xi) * (y - yi) / (yj - yi + 1e-15) + xi):
            inside = not inside
        j = i
    return inside


def point_in_geometry(x, y, geom):
    t = geom["type"]
    coords = geom["coordinates"]
    if t == "Polygon":
        polys = [coords]
    elif t == "MultiPolygon":
        polys = coords
    else:
        return False
    for poly in polys:
        outer = poly[0]
        if not point_in_ring(x, y, outer):
            continue
        if any(point_in_ring(x, y, hole) for hole in poly[1:]):
            continue
        return True
    return False


def load_provinces(geojson_path):
    with open(geojson_path, encoding="utf-8") as f:
        gj = json.load(f)
    return [(feat["properties"]["name"], feat["geometry"]) for feat in gj["features"]]


def locate_province(lon, lat, provinces):
    for name, geom in provinces:
        if point_in_geometry(lon, lat, geom):
            return name
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default="raw", help="存放原始导出表的目录")
    ap.add_argument("--out", default=".", help="输出目录")
    ap.add_argument("--geojson",
                    default="../figures_repo/china_sampling_map/data/china_provinces.geojson")
    ap.add_argument("--maf", type=float, default=0.05)
    ap.add_argument("--exclude-prefix", default="BC",
                    help="按样本 ID 前缀剔除批次离群个体，逗号分隔；传空串则保留全部")
    ap.add_argument("--npc", type=int, default=5)
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    provinces = load_provinces(args.geojson)

    # 1) 元数据 + 省级定位 ----------------------------------------------------
    meta = pd.read_csv(os.path.join(args.raw, "te_samples_403.tsv"), sep="\t")
    meta = meta[["sample", "breed", "reviewed_longitude", "reviewed_latitude"]].copy()
    meta["province"] = None
    cache = {}
    for i, row in meta.iterrows():
        lon, lat = row["reviewed_longitude"], row["reviewed_latitude"]
        if pd.isna(lon) or pd.isna(lat):
            continue
        key = (round(float(lon), 3), round(float(lat), 3))
        if key not in cache:
            cache[key] = locate_province(lon, lat, provinces)
        meta.at[i, "province"] = cache[key]
    meta["zone"] = meta["province"].map(PROVINCE_TO_ZONE)

    # 2) 只保留中国地方鸡品种 -------------------------------------------------
    keep = meta[meta["breed"].isin(CHINESE_LOCAL_BREEDS) & meta["zone"].notna()].copy()
    pre = [x.strip() for x in args.exclude_prefix.split(",") if x.strip()]
    if pre:
        drop = keep["sample"].astype(str).str.startswith(tuple(pre))
        if drop.any():
            print(f"[!] 剔除 {int(drop.sum())} 个批次离群个体（前缀 {','.join(pre)}）："
                  + ", ".join(sorted(keep.loc[drop, 'breed'].unique())))
        keep = keep[~drop]
    print(f"[i] 中国地方鸡样本 {len(keep)} 个体 / {keep['breed'].nunique()} 品种")
    print(keep.groupby("zone").size().to_string())

    # 3) 基因型矩阵 ----------------------------------------------------------
    dos = pd.read_csv(os.path.join(args.raw, "te_alt_dosage_individual_complete.csv"))
    dos["sample"] = dos["sample"].astype(str)
    dos = dos.set_index("sample")
    ids = [s for s in keep["sample"].astype(str) if s in dos.index]
    X = dos.loc[ids].to_numpy(dtype=np.float32)
    print(f"[i] 原始矩阵: {X.shape[0]} samples × {X.shape[1]} TE loci")

    maf = X.mean(axis=0) / 2.0
    maf = np.minimum(maf, 1 - maf)
    keep_locus = (maf >= args.maf) & (X.std(axis=0) > 0)
    X = X[:, keep_locus]
    print(f"[i] MAF ≥ {args.maf} 过滤后: {X.shape[1]} loci")

    # 4) 中心化 + SVD PCA ----------------------------------------------------
    Xc = X - X.mean(axis=0, keepdims=True)
    U, S, Vt = np.linalg.svd(Xc, full_matrices=False)
    scores = U * S                       # samples × k
    eig = S ** 2 / (X.shape[0] - 1)
    ratio = eig / eig.sum()
    k = min(args.npc, scores.shape[1])
    print(f"[i] 解释方差: " + ", ".join(f"PC{i+1}={ratio[i]*100:.2f}%" for i in range(min(5, k))))

    # 5) 输出 ----------------------------------------------------------------
    out = keep.set_index("sample").loc[ids].reset_index()
    for i in range(k):
        out[f"PC{i+1}"] = scores[:, i]
    out["zone"] = pd.Categorical(out["zone"], categories=ZONE_ORDER, ordered=True)
    out = out.sort_values(["zone", "province", "breed", "sample"])
    cols = ["sample", "breed", "province", "zone"] + [f"PC{i+1}" for i in range(k)]
    out[cols].to_csv(os.path.join(args.out, "pca_te_scores.tsv"), sep="\t",
                     index=False, float_format="%.6f")

    pd.DataFrame({"PC": [f"PC{i+1}" for i in range(k)],
                  "eigenvalue": eig[:k],
                  "variance_explained": ratio[:k]}
                 ).to_csv(os.path.join(args.out, "pca_te_variance.tsv"), sep="\t",
                          index=False, float_format="%.8f")

    counts = (out.groupby(["zone", "province", "breed"], observed=True)
              .size().reset_index(name="n_samples"))
    counts.to_csv(os.path.join(args.out, "te_zone_counts.tsv"), sep="\t", index=False)
    print(f"[done] -> {args.out}/pca_te_scores.tsv ({len(out)} samples)")


if __name__ == "__main__":
    main()
