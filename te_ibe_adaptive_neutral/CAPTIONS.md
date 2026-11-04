# 图注（中/英）

> 图内数字与这里必须一致；改数据后同步改本文与 `README.md`。
> 本图的“自适应 TE”是探索性集合（LFMM 单独显著），正文必须写明，不能写成已验证的适应位点。

---

## te_ibe_adaptive_neutral —— IBD 与 IBE：自适应 TE vs 中性 TE

**中文**

**图 X　中国地方鸡的地理隔离（IBD）与环境隔离（IBE）：自适应与中性 TE 的比较。**
以 249 只个体的 TE 存在剂量矩阵为起点，取其中 **14 个中国地方鸡品种、146 只个体**，
对 **9,765** 个有变异的 TE 位点做两两群体的 Weir–Cockerham θ 估计并按
Σa/Σ(a+b+c) 汇总，纵轴为 **FST/(1−FST)**（Rousset 线性化）。**(E)** 横轴为品种代表
产地之间的 Haversine 地理距离（0–3,300 km）；**(F)** 横轴为 5 个标准化环境变量
（bio3、bio15、bio18、wind、srad）的欧氏环境距离。**红色**为 366 个环境关联 TE
（LFMM2 K=10、genomic-control 后 q<0.05，5 个变量取最小），**青色**为其余 9,399 个
中性 TE；实线为最小二乘回归，阴影为 95% 置信带。共 **91 对**群体比较。
环境关联 TE 的分化随环境距离上升（Mantel r = 0.35，p = 0.067，9,999 次置换），
与地理距离无显著相关（r = 0.27，p = 0.14）；中性 TE 对两者均无信号
（r = 0.06，p = 0.31；r = −0.02，p = 0.34）。TE 剂量中约 19.9% 的基因型由
局部 SNP 单倍型插补（母集 403 样本统计），个体编号与本图无关；受群体数（K = 14）
限制，Mantel 检验功效有限。

**English**

**Figure X. Isolation-by-distance (IBD) and isolation-by-environment (IBE) in Chinese
indigenous chickens: adaptive versus neutral TE insertions.**
Starting from the TE presence-dosage matrix of 249 individuals, **146 individuals from
14 Chinese indigenous breeds** were retained; pairwise Weir–Cockerham θ was estimated
over **9,765** variable TE loci and aggregated by Σa/Σ(a+b+c); the y axis is
**FST/(1−FST)** (Rousset's linearisation). **(E)** x axis: Haversine geographic distance
between breed localities (0–3,300 km). **(F)** x axis: Euclidean environmental distance
over five standardised variables (bio3, bio15, bio18, wind, srad). **Red**: 366
environment-associated TEs (LFMM2, K = 10, genomic-control q < 0.05 for at least one
variable); **teal**: the remaining 9,399 neutral TEs. Lines are ordinary least-squares
fits with 95% confidence bands; **91** population pairs in total. Differentiation of
environment-associated TEs increases with environmental distance (Mantel r = 0.35,
p = 0.067; 9,999 permutations) but not with geographic distance (r = 0.27, p = 0.14),
whereas neutral TEs show no signal for either (r = 0.06, p = 0.31; r = −0.02, p = 0.34).
About 19.9% of TE genotypes were imputed from local SNP haplotypes (statistic from the
full 403-sample set); no individual identifiers are involved. Statistical power is
limited by the number of populations (K = 14).

---

## 口径提醒

| 项 | 值 | 备注 |
|---|---|---|
| 群体 | 14 个中国地方鸡品种 / 146 只 | 剔除 3 个原鸡种与 3 个外源商业品种；理由见 README 第 5 节 |
| 位点 | 9,765 个有变异 TE | 来自母集 9,805 个，剔除单态 |
| 自适应 TE | 366 个，LFMM2 K10 GC-q < 0.05 | **探索性**：严格跨方法核心为 0 个位点 |
| 中性 TE | 9,399 个 | 其余全部 |
| 群体对 | 91 | K(K−1)/2 = 14×13/2 |
| 置换 | 9,999 | 单侧 greater，同 vegan::mantel 默认 |
| 距离 | 地理：Haversine (km)；环境：5 个标准化变量欧氏距 | 与原文“所有标准化环境变量的欧氏距离”一致 |
