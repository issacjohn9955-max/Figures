# 图注 / Captions — te_factor_polar

## 中文

**图 X　气候因子关联 TE 位点的专有与共享数量。**
极坐标堆叠柱按气候因子分楔：内层（蓝）为该因子**专有**的显著 TE 位点数（位点仅对本因子显著），
外层（红）为**共享**位点数（位点除本因子外至少还对另一个因子显著），两层之和为该因子的显著关联总数；
楔形自 3 点钟位置逆时针排列，径向刻度为 TE 位点数。数据为 29 个鸡品种 × 16,361 个 TE 存在/缺失
（PAV）位点 × 10 个核心气候变量的逐位点 Spearman 关联（每个气候变量内做 FDR 校正，
共 1,268 条显著关联、涉及 982 个位点）；仅展示关联数 ≥20 的四个因子（SRAD、BIO_3、BIO_9、WIND，
合计 1,257 条，占全部显著关联的 99.1%），关联数仅 6、3、2 的 ELEV、DM、BIO_18 未展示。

## English

**Figure X. Unique and shared climate-associated TE loci per climate driver.**
Polar stacked bars, one wedge per climate variable. The inner layer (blue) gives the number of TE loci
uniquely associated with that variable; the outer layer (red) gives the number associated with that
variable and at least one other variable; the two layers sum to the variable's total significant
associations. Wedges run counter-clockwise from the 3 o'clock position; the radial axis is the number
of TE loci. Underlying data: locus-wise Spearman tests between 16,361 TE presence/absence (PAV) loci in
29 chicken populations and 10 core climate variables, FDR-corrected within each climate variable
(1,268 significant associations, 982 distinct loci). Only the four variables with ≥20 associations
(SRAD, BIO_3, BIO_9, WIND; 1,257 associations, 99.1% of the total) are shown; ELEV, DM and BIO_18
(6, 3 and 2 associations) are omitted.

## 说明

* 数字必须与 `te_factor_polar.png` 一致：SRAD 305+181、BIO_3 317+167、BIO_9 122+126、WIND 14+25。
* 若改用 `te_factor_polar_all7.png`，把最后一句改成「七个显著因子全部展示，ELEV/DM/BIO_18
  的关联数仅 6/3/2，在 0–500 的径向上近乎不可见」。
* 参考图（Yuan et al. 2026 Figure 3B）的因子是 8 个农业气候综合变量中的 6 个，
  本图的因子名沿用我们自己的 WorldClim 变量缩写（BIO_3 = 等温性、BIO_9 = 最干季均温、
  SRAD = 太阳辐射、WIND = 风速、ELEV = 海拔、DM = 水分亏缺、BIO_18 = 最暖季降水）。
