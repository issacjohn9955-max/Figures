#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
prepare_snp_pca.py — 把服务器上已有的 SNP PCA 结果整理成绘图表
================================================================
数据来源（未重算，直接复用 2026-10-27 的产物）：
  /data/shine_work/02_workflowSNP/02_genotype/results/pca/genetic_pca_scores.csv
  /data/shine_work/02_workflowSNP/02_genotype/results/pca/genetic_pca_eigenvalues.csv
  元数据 sample_metadata.tsv（200 samples，population/经度/纬度）
  方法见 scripts/pca_structure.py：826,068 SNP，中心化后 SVD（不做 SNP 标准化）

输出
  pca_snp_scores.tsv    sample, breed, province, zone, PC1..PC5
  pca_snp_variance.tsv  PC, eigenvalue, variance_explained
"""
import argparse
import json
import os

import pandas as pd

from compute_te_pca import (CHINESE_LOCAL_BREEDS, PROVINCE_TO_ZONE, ZONE_ORDER,
                            load_provinces, locate_province)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default="raw")
    ap.add_argument("--exclude-prefix", default="BC")
    # 默认用"已剔除 BC 批次"的重算版（PC 值也在这 120 只上重新求解，避免
    # 用 126 只算出的主成分去画 120 只的点、方差百分比对不上）
    ap.add_argument("--scores", default="pca_snp_cn_noBC_scores.csv")
    ap.add_argument("--variance", default="pca_snp_cn_noBC_variance.csv")
    ap.add_argument("--out", default=".")
    ap.add_argument("--geojson",
                    default="../figures_repo/china_sampling_map/data/china_provinces.geojson")
    args = ap.parse_args()

    meta = pd.read_csv(os.path.join(args.raw, "sample_metadata.tsv"), sep="\t",
                       encoding="utf-8-sig")
    # 默认读"中国地方鸡子集"重算版；旧的 200 样本混合版需显式指定
    score = pd.read_csv(os.path.join(args.raw, args.scores), encoding="utf-8-sig")
    eig = pd.read_csv(os.path.join(args.raw, args.variance), encoding="utf-8-sig")
    if "breed" in score.columns:
        eig = eig.rename(columns={"PC": "PC"})
    key = "id" if "id" in score.columns else "sample"
    df = score.merge(meta[["sample", "lon", "lat", "population"]], left_on=key,
                     right_on="sample", how="inner")
    if "breed" not in df.columns:
        df["breed"] = df["population"].astype(str).str.replace(r"^\d+_", "", regex=True)

    provinces = load_provinces(args.geojson)
    cache = {}
    df["province"] = None
    for i, row in df.iterrows():
        key = (round(float(row["lon"]), 3), round(float(row["lat"]), 3))
        if key not in cache:
            cache[key] = locate_province(row["lon"], row["lat"], provinces)
        df.at[i, "province"] = cache[key]
    df["zone"] = df["province"].map(PROVINCE_TO_ZONE)
    pre = [x.strip() for x in args.exclude_prefix.split(",") if x.strip()]
    if pre:
        drop = df["sample"].astype(str).str.startswith(tuple(pre))
        if drop.any():
            print(f"[!] 剔除 {int(drop.sum())} 个批次离群个体（前缀 {','.join(pre)}）："
                  + ", ".join(sorted(df.loc[drop, 'breed'].unique())))
        df = df[~drop].copy()

    missing = df[df["province"].isna()]
    if len(missing):
        print(f"[!] {len(missing)} 个样本坐标落在境外/省界外："
              + ", ".join(sorted(missing["population"].unique())))
    df = df[df["breed"].isin(CHINESE_LOCAL_BREEDS) & df["zone"].notna()].copy()
    df["zone"] = pd.Categorical(df["zone"], categories=ZONE_ORDER, ordered=True)
    df = df.sort_values(["zone", "province", "breed", "sample"])

    cols = ["sample", "breed", "province", "zone"] + [f"PC{i}" for i in range(1, 6)]
    df[cols].to_csv(os.path.join(args.out, "pca_snp_scores.tsv"), sep="\t",
                    index=False, float_format="%.6f")
    eig.head(5).to_csv(os.path.join(args.out, "pca_snp_variance.tsv"), sep="\t",
                       index=False, float_format="%.8f")
    print(f"[i] {len(df)} 个体 / {df['breed'].nunique()} 品种")
    print(df.groupby("zone", observed=True).size().to_string())
    print(f"[done] -> {args.out}/pca_snp_scores.tsv")


if __name__ == "__main__":
    main()
