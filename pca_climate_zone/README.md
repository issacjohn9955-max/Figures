# pca_climate_zone —— PCA 散点 × 六大农业气候区（复刻论文版式）

参考图：`sample.pdf`（Yuan et al., *Zoological Research*）中标注 **B** 的 PCA 面板——
PC1/PC2 散点、按 **Climate zone** 六区着色 + 不同符号，六区图例横排两行压在面板上方，
轴标题与刻度加粗。

本模块把这张图拆成"**一个可复用绘图脚本 + 两套本项目真实数据的成品图**"，
所有字号 / 线宽 / 画幅 / 配色来自 `../figure-style/style/*.json`，不写死任何十六进制色值。

---

## 1. 目录内容

| 文件 | 作用 |
|---|---|
| `plot_pca_climate_zone.R` | **主脚本**：读 `sample_id, PC1, PC2, zone` 表即可出图（论文版式，160 × 111 mm，PNG 600 dpi + 矢量 PDF） |
| `compute_te_pca.py` | TE 基因型 → 个体级 PCA（含坐标 → 省级 → 气候区归并） |
| `prepare_snp_pca.py` | 把 SNP PCA 结果 + 元数据整理成绘图表 |
| `remote_snp_pca_cn.py` | 服务器端用中国地方鸡子集重算 SNP PCA（原始 200 样本版被外类群主导，不能用） |
| `make_synthetic_preview.R` | **合成数据**预览：六区全部出现时的版式（现有真实数据只有 4 区） |
| `data/pca_te_scores.tsv` | TE 版得分表（140 个体，已匿名化为 S001…） |
| `data/pca_snp_scores.tsv` | SNP 版得分表（120 个体，已匿名化为 N001…） |
| `data/*_variance.tsv` | 每个 PC 的解释方差 |
| `data/climate_zone_provinces.tsv` | 省 → 气候区对照表（可改，改完重跑即可换分区口径） |
| `data/zone_counts.tsv` | 数据集 × 气候区 × 省份 × 品种 × 样本数 |
| `fig_pca_te_climate.png/.pdf` | 成品图 1：TE 插入多态性的 PCA |
| `fig_pca_snp_climate.png/.pdf` | 成品图 2：SNP 的 PCA（同一版式，作对照） |
| `preview_6zone_synthetic.png/.pdf` | **合成数据**：六区版式对照样例，只用于版式检查 |
| `CAPTIONS.md` | 中英图注 |

## 2. 复现命令

> 仓库根 `.gitignore` 默认忽略 `data/`（防止省界 geojson 等大文件入库），本模块的派生小表
> 已在该文件里开了白名单（`!pca_climate_zone/data/`、`!pca_climate_zone/data/*.tsv`）。
> 新建模块时若也要提交输入表，照此在 `.gitignore` 加一条例外，否则 `git add` 会静默跳过。
> `data/synthetic_6zone_*.tsv` 由 `make_synthetic_preview.R` 自动生成。


```bash
# 依赖：R ≥ 4.1 + ggplot2、jsonlite；figure-style 仓库的 style/ 层。两种找法：
#   ① 把 figure-style/ 放在本仓库上一级（默认，脚本自动向上查找）
#   ② 或设 FIGURE_STYLE_DIR=/path/to/figure-style
cd pca_climate_zone

Rscript plot_pca_climate_zone.R \
  --scores data/pca_te_scores.tsv --variance data/pca_te_variance.tsv \
  --out fig_pca_te_climate --palette chromatic_nc --tag B \
  --width-mm 160 --height-mm 111

Rscript plot_pca_climate_zone.R \
  --scores data/pca_snp_scores.tsv --variance data/pca_snp_variance.tsv \
  --out fig_pca_snp_climate --palette chromatic_nc --tag B \
  --width-mm 160 --height-mm 111

Rscript make_synthetic_preview.R     # 六区版式预览（合成数据）
```

换自己的数据：只要一张 TSV，列名 `sample_id, breed, province, zone, PC1, PC2 …`，
`zone` 取值限定在 `North / Middle / Northwest / Southeast / Southwest / Xizang`。
`--tag ""` 去掉面板字母，`--palette pangenome_spectrum` 换回仓库默认配色。

## 3. 数据来源与口径

**两套数据都在 8.134.79.130（danding）上，本模块只提交派生得分表，不提交基因型、不提交登录号。**

### 图 1：TE 插入多态性 PCA

* 输入：`/data/shine_work/12_TE_SNP_imputation_20261030/results/06_complete/`
  `te_alt_dosage_individual_complete.csv` —— 403 样本 × 9,805 个 TE 位点的 0/1/2 剂量
  （observations 保真，缺失由 Beagle 5.5 用局部 SNP 单倍型填补，见同目录 `complete_te_qc.json`）。
* 元数据：同目录 `samples.tsv`（品种 + 复核经纬度）。
* 筛选：中国地方鸡 14 品种 → 146 只；**剔除惠阳胡须鸡 BC01–BC06 共 6 只**（两套 PCA 里都远离
  同名"胡须鸡"HHX 批次，疑似不同 call set 的批次效应，见 §5）→ **140 只 / 13 品种**。
* 位点：MAF ≥ 0.05 过滤后 **7,689 个 TE 位点**；矩阵按位点中心化（不标准化），经济型 SVD。
* 结果：PC1 = **4.27%**，PC2 = **2.36%**。

### 图 2：SNP PCA

* 输入：`/data/shine_work/02_workflowSNP/02_genotype/results/genotype_dosage.npz`
  （200 样本 × 826,068 SNP，缺失 −1）。
* 为什么重算：2026-10-27 的原版 PCA 混了灰原鸡/绿原鸡/锡兰原鸡、洛岛红、白来航等外类群，
  PC1/PC2 被种间差异吃掉，中国品种全挤在一小团。这里只取中国地方鸡子集重算。
* 筛选：14 品种 126 只 → 剔除 BC01–BC06 → **120 只 / 13 品种**。
* 位点：缺失按位点均值填补，MAF ≥ 0.05 → **816,437 个 SNP**；中心化 + SVD。
* 结果：PC1 = **2.29%**，PC2 = **2.07%**。

### 气候区

按省界多边形（阿里 DataV `100000_full.json`，射线法，不依赖 GDAL/shapely）把每个样本
落到省级行政区，再按 `data/climate_zone_provinces.tsv` 归到六区。本项目现有样本只覆盖
**4 个区**：North（黑龙江、山东）、Middle（江苏、浙江、江西、湖北）、
Southeast（广东、广西、海南）、Northwest（新疆）。**没有 Southwest 和 Xizang 的基因型**，
所以真实图里只有 4 个图例条目——这不是漏画，是数据范围如此。

## 4. 版式拆解（这张图为什么长这样）

| 元素 | 做法 | 取值来源 |
|---|---|---|
| 轴 | 只有左/下轴脊，刻度朝外，无网格、无边框 | `theme.json: lines.spines / grid` |
| 字号 | 轴标题、刻度、图例统一放大到正文的 1.85 倍 | `--type-scale`（默认 1.85）× `theme.json: typography.pt` |
| 字重 | 轴标题、刻度标签、图例标题与条目**全部加粗** | 原图如此（theme.json 里是 regular，故脚本内覆写） |
| 图例 | 面板上方横排，标题"Climate zone"居左，条目按行优先排 2 行 | `guide_legend(nrow = 2, byrow = TRUE)` |
| 编码 | 颜色 + **形状**双编码（形状冗余，色盲/灰度印刷也能区分） | `ZONE_SPEC`：北🔺 / 中▪ / 西北⊠ / 东南◇+ / 西南● / 藏▽ |
| 配色 | 取 `chromatic_nc` 的语义色位：蓝=North、绿=Middle、红=Northwest、紫=Southeast、青绿=Southwest、琥珀=Xizang | `palettes.json` |
| 线型符号 | 7/9/6 这类只有描边的符号单独加粗描边，否则小尺寸+浅色会糊掉 | 脚本内 `OPEN_SHAPES` 分层绘制 |
| 导出 | PNG 600 dpi + 矢量 PDF，白底 | `save_fs()` |

与原图的两处有意偏离：① 原图占位更"满"（1,022 只、PC1 20.31%），本项目样本量与解释度都小得多；
② 原图六区齐全，本项目只有四区。

## 5. 注意事项 / 待确认

1. **BC01–BC06（惠阳胡须鸡）异常**：在 TE 和 SNP 两套 PCA 里都自成一簇、远离同名"胡须鸡"HHX
   批次（TE 版 PC1 ≈ −17.7、PC2 ≈ +18.3，是全场最极端的 6 个点）。两套独立的基因型矩阵都这样，
   说明不是单一流程的偶发错误，更像**来源/call set 批次差异**，或者这批样本根本不是惠阳胡须鸡。
   当前成品图按"批次离群"剔除；若要保留，把 `--exclude-prefix` 传空串即可。
2. **PC1 解释度低（4.27% / 2.29%）** 是这类数据的常态：个体级、位点数上百万、群体间分化细碎，
   方差摊在很多主成分上。想在图里拿到更"漂亮"的百分比，可改画**品种均值 PCA**——
   服务器 `results/pca_pop/` 那版 20 群体的 PC1 = 32.17%、PC2 = 11.35%，缺点是每个点代表一个品种。
3. 六区里 Southwest / Xizang 缺基因型；补齐后直接重跑同一脚本，版式无需改动，
   `preview_6zone_synthetic.png` 是六区齐全时的样子。
4. 图内数字（n、百分比）与 `CAPTIONS.md`、`data/zone_counts.tsv` 一致；改数据必须同步改图注。

## 6. 署名与合规

* 配色/字号/画幅规范来自 `figure-style` 仓库；该规范派生自
  [1577377232/Genomics-Figure-Styles](https://github.com/1577377232/Genomics-Figure-Styles) v2.0（见 `ATTRIBUTION.md`）。
* 中国省界来自阿里 DataV `https://geo.datav.aliyun.com/areas_v3/bound/100000_full.json`。
* 本模块不含个体登录号：`data/*_scores.tsv` 的 `sample_id` 是 S001… / N001… 匿名编号，
  真实 ID 对照表留在研究目录 `pca_climate_zone/anonymization_map.tsv`，不入库。
