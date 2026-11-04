# 图注（中/英）

> 图内数字与这里必须一致；改数据后同步改本文与 `README.md`。
> 三个文件的样本量/方差百分比都不同，不要混用。

---

## fig_pca_te_climate —— TE 插入多态性的 PCA

**中文**

**图 X　中国地方鸡 TE 插入多态性的主成分分析。** 基于 403 份测序个体中通过质控的
9,805 个 TE（转座元件）插入位点，取其中国地方鸡 14 个品种共 146 只，剔除疑似批次离群的
惠阳胡须鸡 6 只后，**140 只个体 / 13 个品种**参与分析。位点经 MAF ≥ 0.05 过滤保留
**7,689 个**，按位点中心化后做奇异值分解；PC1 与 PC2 分别解释 **4.27%** 与 **2.36%**
的总方差。点按样本产地所属农业气候区着色并以形状冗余区分：**North**（▲，n = 12 只 / 2 品种）、
**Middle**（■，n = 24 / 4）、**Northwest**（⊠，n = 6 / 1）、**Southeast**（◇，n = 98 / 6）；
现有基因型覆盖黑龙江、山东、江苏、浙江、江西、湖北、广东、广西、海南、新疆 10 个
省级行政区，尚缺 **Southwest** 与 **Xizang** 两区（故图例中不出现）。气候区由样本复核
经纬度落省、再按中国综合农业气候区划归并（对照表见 `data/climate_zone_provinces.tsv`）。
TE 基因型中观测到的 0/1/2 剂量原样保留，缺失值由 Beagle 5.5 借局部 SNP 单倍型填补；
个体编号在本文中匿名化。

**English**

**Figure X. Principal component analysis of TE insertion polymorphisms in Chinese indigenous
chickens.** Of 9,805 quality-passed TE loci genotyped in 403 sequenced individuals, Chinese
indigenous chickens were retained (146 individuals from 14 breeds); six Huixu chickens
(BC01–BC06) flagged as batch outliers were removed, leaving **140 individuals from 13 breeds**.
Loci were filtered to MAF ≥ 0.05 (**7,689 loci**), mean-centred and decomposed by SVD; PC1 and
PC2 explain **4.27%** and **2.36%** of the variance, respectively. Points are coloured by the
agricultural climate zone of their recorded origin and redundantly encoded by shape:
**North** (▲, n = 12 individuals / 2 breeds), **Middle** (■, n = 24 / 4), **Northwest**
(⊠, n = 6 / 1) and **Southeast** (◇, n = 98 / 6). Genotypes currently cover ten provinces
(Heilongjiang, Shandong, Jiangsu, Zhejiang, Jiangxi, Hubei, Guangdong, Guangxi, Hainan,
Xinjiang); the **Southwest** and **Xizang** zones are not yet represented and therefore do not
appear in the legend. Zones were assigned by intersecting reviewed coordinates with province
polygons and then mapped to the six agricultural climate zones
(`data/climate_zone_provinces.tsv`). Observed 0/1/2 TE dosages were kept as called; missing
calls were imputed with Beagle 5.5 from local SNP haplotypes. Sample identifiers are anonymised.

---

## fig_pca_snp_climate —— SNP 的 PCA（同版式对照）

**中文**

**图 Y　中国地方鸡 SNP 的主成分分析（与图 X 同版式的对照）。** 由 200 份个体、826,068 个
SNP 构成的基因型矩阵中取中国地方鸡 13 个品种 **120 只**（同样剔除惠阳胡须鸡 BC01–BC06
共 6 只）；缺失值按位点均值填补，MAF ≥ 0.05 过滤后保留 **816,437 个 SNP**，中心化后做
奇异值分解。PC1、PC2 分别解释 **2.29%**、**2.07%** 的方差。着色与形状编码同图 X：
North（▲，n = 12）、Middle（■，n = 24）、Northwest（⊠，n = 6）、Southeast（◇，n = 78）。
注意本 PCA 只在中国地方鸡内部计算，不含原鸡与商业品种；原 200 样本版 PCA 的 PC1/PC2
由种间差异主导，不适用于本图。

**English**

**Figure Y. Principal component analysis of SNPs in Chinese indigenous chickens (same layout as
Figure X).** From a genotype matrix of 200 individuals × 826,068 SNPs, **120 individuals of 13
Chinese indigenous breeds** were retained (the same six Huixu chickens, BC01–BC06, were removed).
Missing calls were imputed by per-locus means and variants filtered to MAF ≥ 0.05, leaving
**816,437 SNPs**; the mean-centred matrix was decomposed by SVD. PC1 and PC2 explain **2.29%**
and **2.07%** of the variance. Colour and shape encoding follow Figure X: North (▲, n = 12),
Middle (■, n = 24), Northwest (⊠, n = 6), Southeast (◇, n = 78). This PCA is computed within
Chinese indigenous chickens only — red junglefowl and commercial lines are excluded, because the
original 200-sample PCA was dominated by between-species differentiation.

---

## preview_6zone_synthetic —— 版式预览（合成数据，不可当作结果）

**中文**

**图 Z（合成数据，仅用于版式检查，不代表任何真实结果）.** 用 395 个模拟数据点验证六个
气候区同时出现时的色/形编码与图例排布：North（▲）、Middle（■）、Northwest（⊠）、
Southeast（◇）、Southwest（●）、Xizang（▽）。坐标轴上的 12.40% / 8.15% 是占位数值，
**不对应任何真实分析**；真实数据请见 `fig_pca_te_climate` 与 `fig_pca_snp_climate`。

**English**

**Figure Z (synthetic data — layout check only, not a result).** 395 simulated points verify the
colour/shape encoding and legend layout when all six climate zones are present: North (▲),
Middle (■), Northwest (⊠), Southeast (◇), Southwest (●), Xizang (▽). The variance percentages
(12.40% / 8.15%) are placeholders and **do not correspond to any real analysis**; see
`fig_pca_te_climate` and `fig_pca_snp_climate` for the real data.
