#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
remote_snp_pca_cn.py — 在服务器上对中国地方鸡子集重算 SNP PCA
=============================================================
为什么要重算：2026-10-27 那版 PCA 用了 200 个样本（含灰原鸡/绿原鸡/锡兰原鸡、
洛岛红、白来航、Corish 等外类群），PC1/PC2 被种间差异主导，中国地方品种全挤在
一小团里，没法按气候区看结构。这里只保留 14 个中国地方鸡品种、MAF ≥ 0.05 的
位点重算，PC 才反映栽培群体内部的分化。

运行位置：8.134.79.130（danding）: /data/shine_work
  $PY pca_cn_only.py  →  写出 pca_snp_cn_scores.csv / pca_snp_cn_variance.csv
"""
import numpy as np
import pandas as pd

BASE = "/data/shine_work/02_workflowSNP/02_genotype/results"
CHINESE_LOCAL_BREEDS = [
    "惠阳胡须鸡", "胡须鸡", "杏花鸡", "清远麻鸡", "文昌鸡",
    "广西瑶鸡", "广西三黄鸡", "郧阳大鸡", "仙居鸡", "白耳黄鸡",
    "溧阳鸡", "林甸鸡", "济宁百日鸡", "吐鲁番斗鸡",
]
MAF_MIN = 0.05

z = np.load(f"{BASE}/genotype_dosage.npz")
X = z["dosage"].astype(np.float32)
samples = [l.strip() for l in open(f"{BASE}/samples.txt") if l.strip()]
print(f"[i] 全矩阵 {X.shape}, 缺失值 {int((X < 0).sum())}")

meta = pd.read_csv(f"{BASE}/sample_metadata.tsv", sep="\t", encoding="utf-8-sig")
meta["breed"] = meta["population"].astype(str).str.replace(r"^\d+_", "", regex=True)
meta = meta.set_index("sample")
keep = [s for s in samples if s in meta.index and meta.loc[s, "breed"] in CHINESE_LOCAL_BREEDS]
idx = [samples.index(s) for s in keep]
X = X[idx]
print(f"[i] 中国地方鸡 {X.shape[0]} 个体 / {len(set(meta.loc[keep,'breed']))} 品种")

# 缺失按位点均值填 -> MAF 过滤（MAF 用观测值算）
miss = X < 0
af = np.where(miss, np.nan, X).astype(np.float64).mean(axis=0) / 2.0
af = np.nan_to_num(af, nan=0.5)
maf = np.minimum(af, 1 - af)
sel = (maf >= MAF_MIN) & (~miss.all(axis=0))
X = X[:, sel]
miss = miss[:, sel]
colmean = np.where(miss, np.nan, X).astype(np.float64)
colmean = np.nanmean(colmean, axis=0)
X = np.where(miss, colmean, X).astype(np.float32)
print(f"[i] MAF ≥ {MAF_MIN} 后 {X.shape[1]} 位点")

Xc = X - X.mean(axis=0, keepdims=True)
U, S, Vt = np.linalg.svd(Xc, full_matrices=False)
eig = S ** 2 / (X.shape[0] - 1)
ratio = eig / eig.sum()
print("[i] 解释方差 " + ", ".join(f"PC{i+1}={ratio[i]*100:.2f}%" for i in range(5)))

out = pd.DataFrame(U[:, :5] * S[:5], columns=[f"PC{i+1}" for i in range(5)])
out.insert(0, "sample", keep)
out.insert(1, "breed", meta.loc[keep, "breed"].values)
out.to_csv(f"{BASE}/pca_snp_cn_scores.csv", index=False, float_format="%.6f")
pd.DataFrame({"PC": [f"PC{i+1}" for i in range(5)], "variance_explained": ratio[:5]}
             ).to_csv(f"{BASE}/pca_snp_cn_variance.csv", index=False, float_format="%.8f")
print(f"[done] {BASE}/pca_snp_cn_scores.csv")
