#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""compute_te_overlap.py —— 极端环境组之间的 TE 插入频谱重叠（Schoener's D / Hellinger's I）

复刻 Yuan et al. (2026, Zoological Research) Figure 2J 的零分布版式，但把
"MaxEnt 适生区重叠"换成"TE 插入频率谱重叠"——因为前者需要 MaxEnt 栅格，
后者用我们已有的 TE PAV 矩阵就能算，两者用的是同一套 D / I 公式。

统计量（ENMTools 的定义，Warren et al. 2008）::

    D(p, q) = 1 - 0.5 * Σ |p_i - q_i|
    I(p, q) = 1 - 0.5 * Σ (√p_i - √q_i)^2

其中 p、q 是两条归一化后的频率向量（这里取某变量 |ρ| 前 N 的 TE 位点上，
H 组 / L 组的平均插入频率）。

观测值：变量取值最高 3 个品种（H）vs 最低 3 个品种（L）。
零分布：100 次随机抽互斥的 3+3 品种，重复同样的计算；观测值显著落在零分布
之外，就说明极端环境组的 TE 谱确实分化了。

用法::

    python3 compute_te_overlap.py \
        --pav  ~/Desktop/ChickenTE/severdata/te_env_out/te_pav_breed_matrix.csv \
        --env  ~/Desktop/ChickenTE/severdata/te_env_out/env_matrix_raw.csv \
        --assoc ~/Desktop/ChickenTE/severdata/te_env_out/te_locus_assoc.csv \
        --breed-meta data/breed_metadata.tsv \
        --outdir data

输出（都在 --outdir 下）::

    observed_overlap.tsv     variable, n_loci, H_group, L_group, D_obs, I_obs
    null_distributions.tsv   variable, metric, replicate, value     (画图用)
    overlap_summary.tsv      variable, D_obs, I_obs, D_null_*, I_null_*

只依赖 numpy + pandas。
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

# 本项目 env_filter 筛出来的 10 个环境变量（见 severdata/env_filter_out*/）
DEFAULT_VARS = [
    "bio2", "bio3", "bio9", "bio18", "bio19",
    "elev", "srad", "wind", "dm", "rh_dry",
]


# --------------------------------------------------------------------------- #
# 重叠指数
# --------------------------------------------------------------------------- #
def schoener_d(p: np.ndarray, q: np.ndarray) -> float:
    """Schoener's D，0 = 完全不重叠，1 = 完全相同。"""
    p = p / p.sum()
    q = q / q.sum()
    return float(1.0 - 0.5 * np.abs(p - q).sum())


def hellinger_i(p: np.ndarray, q: np.ndarray) -> float:
    """Hellinger's I，0 = 完全不重叠，1 = 完全相同。"""
    p = p / p.sum()
    q = q / q.sum()
    return float(1.0 - 0.5 * ((np.sqrt(p) - np.sqrt(q)) ** 2).sum())


# --------------------------------------------------------------------------- #
# 数据装载
# --------------------------------------------------------------------------- #
def load_inputs(pav_path: Path, env_path: Path, assoc_path: Path,
                meta_path: Path | None, pool: str, max_missing: float):
    pav = pd.read_csv(pav_path, index_col=0)
    env = pd.read_csv(env_path, index_col=0)
    assoc = pd.read_csv(assoc_path)

    if set(pav.index) != set(env.index):
        raise SystemExit("PAV 矩阵与 env 表的品种名不一致，先对齐再跑。")

    # 位点 QC：缺失率过高的位点丢掉，剩余缺失用该位点均值补
    freq = pav.values.astype(float)
    keep = np.isnan(freq).mean(axis=0) <= max_missing
    freq = freq[:, keep]
    loci = np.asarray(pav.columns)[keep]
    col_mean = np.nanmean(freq, axis=0)
    nan = np.isnan(freq)
    if nan.any():
        freq[nan] = np.take(col_mean, np.where(nan)[1])

    breeds = list(pav.index)
    if meta_path is not None:
        meta = pd.read_csv(meta_path, sep="\t")
        meta = meta.set_index("breed").reindex(breeds)
        if meta["category"].isna().any():
            raise SystemExit("breed_metadata.tsv 里有品种没写 category。")
        if pool != "all":
            allowed = meta.index[meta["category"] == pool].tolist()
        else:
            allowed = breeds
    else:
        allowed = breeds

    return freq, loci, breeds, env, assoc, allowed


def profile(freq: np.ndarray, rows: list[int], cols: np.ndarray) -> np.ndarray:
    """一组品种在选定位点上的平均插入频率向量。"""
    return freq[np.ix_(rows, np.where(cols)[0])].mean(axis=0)


# --------------------------------------------------------------------------- #
# 主流程
# --------------------------------------------------------------------------- #
def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pav", required=True, type=Path,
                    help="品种 × TE 位点 的插入频率矩阵（首列品种名）")
    ap.add_argument("--env", required=True, type=Path,
                    help="品种 × 环境变量 的原始值表（首列品种名）")
    ap.add_argument("--assoc", required=True, type=Path,
                    help="TE 位点 × 环境变量 的关联表（variable,locus,rho,p,q）")
    ap.add_argument("--breed-meta", type=Path, default=None,
                    help="data/breed_metadata.tsv，用于限定品种池")
    ap.add_argument("--pool", default="local",
                    choices=["local", "commercial", "jungle_fowl", "all"],
                    help="参与 H/L 分组与置换的品种池（默认 local=中国地方鸡）")
    ap.add_argument("--vars", nargs="+", default=DEFAULT_VARS,
                    help="要画的环境变量（默认本项目筛选出的 10 个）")
    ap.add_argument("--top-loci", type=int, default=250,
                    help="每个变量取 |ρ| 前 N 个 TE 位点（默认 500）")
    ap.add_argument("--perms", type=int, default=100,
                    help="零分布置换次数（默认 100，与原图一致）")
    ap.add_argument("--group-size", type=int, default=3,
                    help="H / L 组各几个品种（默认 3，与原图一致）")
    ap.add_argument("--max-missing", type=float, default=0.2,
                    help="位点缺失率上限（默认 0.2）")
    ap.add_argument("--seed", type=int, default=20261104)
    ap.add_argument("--outdir", type=Path, default=Path("data"))
    args = ap.parse_args()

    freq, loci, breeds, env, assoc, allowed = load_inputs(
        args.pav, args.env, args.assoc, args.breed_meta, args.pool,
        args.max_missing)
    idx = {b: i for i, b in enumerate(breeds)}
    allowed_rows = [idx[b] for b in allowed]
    print(f"位点 {freq.shape[1]} / 品种池 {len(allowed)} ({args.pool})")

    rng = np.random.default_rng(args.seed)
    obs_rows, null_rows, sum_rows = [], [], []

    for var in args.vars:
        sub = assoc[assoc["variable"] == var]
        if sub.empty:
            raise SystemExit(f"关联表里没有变量 {var}。")
        sub = sub.reindex(sub["rho"].abs().sort_values(ascending=False).index)
        picked = set(sub["locus"].head(args.top_loci))
        cols = np.isin(loci, list(picked))

        s = env.loc[allowed, var].astype(float)
        h_breeds = s.nlargest(args.group_size).index.tolist()
        l_breeds = s.nsmallest(args.group_size).index.tolist()

        pH = profile(freq, [idx[b] for b in h_breeds], cols)
        pL = profile(freq, [idx[b] for b in l_breeds], cols)
        d_obs, i_obs = schoener_d(pH, pL), hellinger_i(pH, pL)

        # 零分布：随机抽互斥的 3+3 个品种
        nd, ni = [], []
        n_allowed = len(allowed_rows)
        for rep in range(args.perms):
            perm = rng.permutation(n_allowed)
            a = [allowed_rows[j] for j in perm[:args.group_size]]
            b = [allowed_rows[j] for j in perm[args.group_size:2 * args.group_size]]
            pA, pB = profile(freq, a, cols), profile(freq, b, cols)
            nd.append(schoener_d(pA, pB))
            ni.append(hellinger_i(pA, pB))
        nd, ni = np.asarray(nd), np.asarray(ni)

        obs_rows.append(dict(variable=var, n_loci=int(cols.sum()),
                             H_group="|".join(h_breeds),
                             L_group="|".join(l_breeds),
                             D_obs=d_obs, I_obs=i_obs))
        null_rows += [dict(variable=var, metric="D", replicate=r, value=v)
                      for r, v in enumerate(nd, 1)]
        null_rows += [dict(variable=var, metric="I", replicate=r, value=v)
                      for r, v in enumerate(ni, 1)]
        sum_rows.append(dict(
            variable=var, D_obs=d_obs, I_obs=i_obs,
            D_null_mean=nd.mean(), D_null_p=(nd <= d_obs).mean(),
            I_null_mean=ni.mean(), I_null_p=(ni <= i_obs).mean(),
        ))
        print(f"  {var:7s} loci={int(cols.sum()):5d}  "
              f"D={d_obs:.3f} (null {nd.mean():.3f}, p={(nd <= d_obs).mean():.2f})  "
              f"I={i_obs:.3f} (null {ni.mean():.3f}, p={(ni <= i_obs).mean():.2f})")

    args.outdir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(obs_rows).to_csv(args.outdir / "observed_overlap.tsv",
                                  sep="\t", index=False)
    pd.DataFrame(null_rows).to_csv(args.outdir / "null_distributions.tsv",
                                   sep="\t", index=False)
    pd.DataFrame(sum_rows).to_csv(args.outdir / "overlap_summary.tsv",
                                  sep="\t", index=False)
    print(f"写出 -> {args.outdir}/observed_overlap.tsv "
          f"null_distributions.tsv overlap_summary.tsv")


if __name__ == "__main__":
    main()
