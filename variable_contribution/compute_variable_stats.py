#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
compute_variable_stats.py — 环境变量贡献 / 置换重要性（给 Fig 2A/2B 版式用）

面板 A（全部候选变量，关联筛查口径）
    逐位点 Spearman（每变量内 BH-FDR，与 05_association/te_locus_assoc.py 完全一致）
    contribution_j = 100 × (该变量 q<0.05 的 TE 位点数) / (全部变量 q<0.05 位点数之和)
    即"变量贡献份额"，合计 100%，1% 为筛选阈值线。

面板 B（入选变量，偏 RDA 口径，复现 05_association/te_rda.py）
    contribution = 100 × ΔR²_unique / ΣΔR²_unique
        ΔR²_unique = R²(10 变量全模型) − R²(去掉该变量的 9 变量模型)
    permutation = 100 × mean(ΔR²_perm) / Σmean(ΔR²_perm)
        把该变量列在品种间随机置换（999 次），重拟合，取解释率下降的均值。

输入 : --geno  te_pav_breed_matrix.csv
       --env   climate_modify.csv（含 经度/纬度）
       --sel   env_selected.csv（入选变量, z-score 后的表）
输出 : --out variable_stats.tsv

运行 : python3 compute_variable_stats.py --geno te_pav_breed_matrix.csv \\
           --env climate_modify.csv --sel env_selected.csv --out variable_stats.tsv
"""
import argparse

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.decomposition import PCA

COLUMN_MAP = {
    "海拔(m)": "elev", "年均温BIO1(℃)": "bio1", "平均气温日较差BIO2(℃)": "bio2",
    "等温性BIO3(%)": "bio3", "温度季节性BIO4(SD×100)": "bio4",
    "最热月极端最高均温BIO5(℃)": "bio5", "最冷月极端最低均温BIO6(℃)": "bio6",
    "气温年较差BIO7(℃)": "bio7", "最湿季均温BIO8(℃)": "bio8",
    "最干季均温BIO9(℃)": "bio9", "最热季均温BIO10(℃)": "bio10",
    "最冷季均温BIO11(℃)": "bio11", "年降水量BIO12(mm)": "bio12",
    "最湿月降水BIO13(mm)": "bio13", "最干月降水BIO14(mm)": "bio14",
    "降水季节性BIO15(CV)": "bio15", "最湿季降水BIO16(mm)": "bio16",
    "最干季降水BIO17(mm)": "bio17", "最热季降水BIO18(mm)": "bio18",
    "最冷季降水BIO19(mm)": "bio19", "年平均风速(m/s)": "wind",
    "年平均太阳辐射(W/m²)": "srad", "年平均水汽压(kPa)": "vapr",
    "年平均相对湿度(%)": "rh", "最湿季平均相对湿度(%)": "rh_wet",
    "最干季平均相对湿度(%)": "rh_dry", "年平均露点温度(℃)": "dew",
    "deMartonne干燥指数": "dm",
}
RAW_VARS = list(COLUMN_MAP.values())
FULL_COL = {v: k for k, v in COLUMN_MAP.items()}   # english → 中文列名

# 变量分组：给面板 B 的柱子上色用
GROUP = {}
for v in ("bio1", "bio2", "bio3", "bio4", "bio5", "bio6", "bio7",
          "bio8", "bio9", "bio10", "bio11"):
    GROUP[v] = "temperature"
for v in ("bio12", "bio13", "bio14", "bio15", "bio16", "bio17",
          "bio18", "bio19"):
    GROUP[v] = "precipitation"
for v in ("elev",):
    GROUP[v] = "terrain"
for v in ("wind", "srad", "vapr", "rh", "rh_wet", "rh_dry", "dew", "dm"):
    GROUP[v] = "radiation_humidity"


def zscale(a):
    a = np.asarray(a, float)
    sd = a.std(axis=0, ddof=1)
    sd[sd == 0] = 1.0
    return (a - a.mean(axis=0)) / sd


def resid_after(y, w):
    b, *_ = np.linalg.lstsq(w, y, rcond=None)
    return y - w @ b


def r2_of(yw, xr):
    b, *_ = np.linalg.lstsq(xr, yw, rcond=None)
    return 1 - ((yw - xr @ b) ** 2).sum() / (yw ** 2).sum()


def bh_fdr(pvals):
    """NaN 安全的 Benjamini-Hochberg（与 te_locus_assoc.py 同一实现）"""
    p = np.asarray(pvals, float)
    q = np.full(p.shape, np.nan)
    m = ~np.isnan(p)
    pv = p[m]
    n = pv.size
    if n == 0:
        return q
    order = np.argsort(pv)
    ps = pv[order]
    qs = ps * n / np.arange(1, n + 1)
    qs = np.minimum.accumulate(qs[::-1])[::-1]
    qv = np.empty(n)
    qv[order] = np.clip(qs, 0, 1)
    q[m] = qv
    return q


def spearman_screen(y0, e, label):
    """y0: n×p 频率矩阵; e: n×k 环境矩阵 → rho/p（n×k 对 p 维位点）"""
    n, p = y0.shape
    yr = pd.DataFrame(y0).rank(axis=0).values          # NaN 保持 NaN
    er = pd.DataFrame(e).rank(axis=0).values
    clean = ~np.isnan(yr).any(axis=0)                  # 无缺失的位点走向量化
    if clean.sum():
        yc = yr[:, clean] - yr[:, clean].mean(axis=0)
        ec = er - er.mean(axis=0)
        num = ec.T @ yc
        den = np.sqrt((ec ** 2).sum(axis=0))[:, None] * np.sqrt((yc ** 2).sum(axis=0))[None, :]
        rho_c = num / den
        nn_c = np.full(clean.sum(), n)
    else:
        rho_c = np.empty((e.shape[1], 0)); nn_c = np.empty(0)

    rho = np.full((e.shape[1], p), np.nan)
    nn = np.full((e.shape[1], p), np.nan)
    rho[:, clean] = rho_c
    nn[:, clean] = nn_c
    for i, loc in enumerate(np.where(~clean)[0]):      # 零星缺失位点：成对剔除
        ok_y = ~np.isnan(yr[:, loc])
        for j in range(e.shape[1]):
            ok = ok_y & ~np.isnan(er[:, j])
            if ok.sum() < 10:
                continue
            r, _ = stats.spearmanr(er[ok, j], yr[ok, loc])
            rho[j, loc] = r
            nn[j, loc] = ok.sum()

    with np.errstate(invalid="ignore", divide="ignore"):
        t = rho * np.sqrt((nn - 2) / (1 - rho ** 2))
    pv = 2 * stats.t.sf(np.abs(t), nn - 2)
    print(f"  [spearman] {label}: {p} 位点 × {e.shape[1]} 变量")
    return rho, pv


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--geno", required=True)
    ap.add_argument("--env", required=True)
    ap.add_argument("--sel", required=True)
    ap.add_argument("--out", default="variable_stats.tsv")
    ap.add_argument("--nperm", type=int, default=999)
    ap.add_argument("--npc", type=int, default=3)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--q", type=float, default=0.05)
    a = ap.parse_args()

    # ---------- 读取并对齐 ----------
    raw = pd.read_csv(a.env, encoding="utf-8-sig")
    raw["sample"] = raw["序号"].astype(str) + "_" + raw["品种"].astype(str)
    raw = raw.set_index("sample")
    lon = pd.to_numeric(raw["经度"], errors="coerce").values
    lat = pd.to_numeric(raw["纬度"], errors="coerce").values
    sel = pd.read_csv(a.sel, encoding="utf-8-sig").set_index("sample")
    sel_vars = [c for c in sel.columns if c != "sample"]
    geno = (pd.read_csv(a.geno, encoding="utf-8-sig")
            .drop_duplicates("sample").set_index("sample"))

    common = sorted(set(geno.index) & set(raw.index) & set(sel.index))
    geno, raw, sel = geno.loc[common], raw.loc[common], sel.loc[common]
    n = len(common)
    rng_ = geno.max() - geno.min()
    geno = geno.loc[:, rng_ >= 0.05]
    y0 = geno.fillna(geno.mean()).values.astype(float)
    print(f"[i] {n} 品种 × {y0.shape[1]} 个多态 TE 位点")

    # ---------- 面板 A：28 个候选变量的关联筛查 ----------
    e_all = np.column_stack([pd.to_numeric(raw[FULL_COL[v]], errors="coerce").values
                             for v in RAW_VARS])
    rho_all, p_all = spearman_screen(y0, e_all, "all candidate variables")
    n_sig = {}
    for j, v in enumerate(RAW_VARS):
        q = bh_fdr(p_all[j])
        n_sig[v] = int(((q < a.q) & ~np.isnan(p_all[j])).sum())
    tot_sig = sum(n_sig.values())
    print(f"[i] q<{a.q} 关联总数 {tot_sig}; 分布: "
          + ", ".join(f"{k}={v}" for k, v in
                      sorted(n_sig.items(), key=lambda kv: -kv[1]) if v > 0))
    contrib_a = {v: 100.0 * n_sig[v] / tot_sig if tot_sig else 0.0 for v in RAW_VARS}

    # ---------- 面板 B：入选变量的偏 RDA 贡献 / 置换重要性 ----------
    geo = zscale(np.column_stack([lon, lat]))
    gpc = PCA(n_components=a.npc, random_state=a.seed).fit_transform(zscale(y0))
    z = np.column_stack([np.ones(n), geo, zscale(gpc)])
    yw = resid_after(zscale(y0), z)
    x = sel[sel_vars].astype(float).values
    xr = resid_after(x, z)
    full = r2_of(yw, xr)
    print(f"[i] 偏 RDA 全模型 R² = {full:.4f}（服务器记录 0.4952）")

    uniq, pimp, shap = {}, {}, {}
    k = len(sel_vars)
    # 全部 2^k 个子集的解释率：唯一贡献与 Shapley(LMG) 分解共用
    r2_sub = np.zeros(2 ** k)
    for mask in range(1, 2 ** k):
        cols = [i for i in range(k) if mask >> i & 1]
        r2_sub[mask] = r2_of(yw, xr[:, cols])
    from math import factorial
    w = {s: factorial(s) * factorial(k - s - 1) / factorial(k) for s in range(k)}
    rng = np.random.default_rng(a.seed)
    for j, v in enumerate(sel_vars):
        keep = [c for c in range(k) if c != j]
        uniq[v] = full - r2_of(yw, xr[:, keep])
        shap[v] = sum(w[bin(mask).count("1")] *
                      (r2_sub[mask | (1 << j)] - r2_sub[mask])
                      for mask in range(2 ** k) if not mask >> j & 1)
        drops = np.empty(a.nperm)
        for b in range(a.nperm):
            xp = x.copy()
            xp[:, j] = xp[rng.permutation(n), j]
            drops[b] = full - r2_of(yw, resid_after(xp, z))
        pimp[v] = float(drops.mean())
        print(f"  {v:8s} Shapley={100*shap[v]/full:6.2f}%  unique ΔR²={uniq[v]:.4f}  perm ΔR²={pimp[v]:+.4f}")

    su, sp = sum(uniq.values()), sum(pimp.values())
    rows = []
    for v in RAW_VARS:
        rows.append({
            "variable": v,
            "group": GROUP[v],
            "n_sig_loci": n_sig[v],
            "contribution_pct": round(contrib_a[v], 3),          # 面板 A
            "selected": v in sel_vars,
            "shapley_pct": round(100 * shap[v] / full, 3) if v in sel_vars else np.nan,
            "unique_pct": round(100 * uniq[v] / su, 3) if v in sel_vars else np.nan,
            "permutation_pct": round(100 * pimp[v] / sp, 3) if v in sel_vars else np.nan,
        })
    out = pd.DataFrame(rows).sort_values("contribution_pct", ascending=False)
    out.to_csv(a.out, sep="\t", index=False, encoding="utf-8-sig")
    print(f"[done] {a.out}")
    print(out[out.n_sig_loci > 0].to_string(index=False))


if __name__ == "__main__":
    main()
