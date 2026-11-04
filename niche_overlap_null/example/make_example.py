#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_example.py —— 生成与真实数据无关的示例输入，用来试版式 / 当模板改

产出（都在本目录）：
    example_null.tsv      4 个变量 × 2 个指标 × 100 次重复
    example_observed.tsv  4 个变量的观测 D / I

数值是合成的（seed 固定），只保证版式能跑通、形态像真实数据：
零分布聚在 0.84（D）/ 0.96（I）附近，观测值落在零分布左侧。
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
VARS = ["BARE", "CROPLAND", "TREES", "WATER"]
PERMS = 100
RNG = np.random.default_rng(20260101)

null_rows, obs_rows = [], []
for k, var in enumerate(VARS):
    d_null = np.clip(RNG.normal(0.84 - 0.01 * k, 0.028, PERMS), 0, 1)
    i_null = np.clip(RNG.normal(0.960 - 0.004 * k, 0.012, PERMS), 0, 1)
    d_obs = float(d_null.mean() - (2.2 + 0.3 * k) * d_null.std())
    i_obs = float(i_null.mean() - (2.0 + 0.2 * k) * i_null.std())

    null_rows += [dict(variable=var, metric="D", replicate=r + 1, value=v)
                  for r, v in enumerate(d_null)]
    null_rows += [dict(variable=var, metric="I", replicate=r + 1, value=v)
                  for r, v in enumerate(i_null)]
    obs_rows.append(dict(variable=var, n_loci=0, D_obs=d_obs, I_obs=i_obs))

pd.DataFrame(null_rows).to_csv(HERE / "example_null.tsv", sep="\t", index=False)
pd.DataFrame(obs_rows).to_csv(HERE / "example_observed.tsv", sep="\t", index=False)
print(f"写出 -> {HERE/'example_null.tsv'} / example_observed.tsv")
print("画图：python3 plot_niche_overlap_null.py --null example/example_null.tsv "
      "--observed example/example_observed.tsv --out example/example_figure --tag ''")
