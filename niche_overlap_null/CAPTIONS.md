# 图注 / Figure captions

## 中文

**图 J｜极端环境组之间的 TE 插入频谱重叠。** 每个面板对应一个环境变量。把 13 个
中国地方鸡群体按该变量取值排序，取最高的 3 个为 H 组、最低的 3 个为 L 组；在这
个变量 |Spearman ρ| 最大的 250 个 TE 位点上分别求两组的平均插入频率向量
（归一化后用 `D = 1 − ½Σ|p−q|`、`I = 1 − ½Σ(√p−√q)²`）。柱状图是 100 次随机
重分组（互斥的 3+3 个群体）得到的零分布，青色为 Schoener's D、黄色为
Hellinger's I；同色竖虚线为观测值，轴底倒三角为观测值位置，左上角标注数值。
10 个变量中 9 个的观测重叠低于零分布（置换 p < 0.05），srad 与随机分组无差异。
数据为 29 个群体 × 16,361 个 TE 位点的插入频率矩阵（剔除缺失率 >20% 后保留
16,354 个位点），环境变量见 README。

## English

**Figure J | TE insertion-spectrum overlap between extreme-environment groups.**
One panel per environmental variable. The 13 Chinese indigenous chicken populations
were ranked by the variable, the three highest taken as the H group and the three
lowest as the L group; their mean insertion-frequency vectors were compared over
the 250 TE loci with the largest |Spearman ρ| for that variable, using
`D = 1 − ½Σ|p−q|` and `I = 1 − ½Σ(√p−√q)²`. Bars show the null distributions from
100 random 3-vs-3 regroupings (cyan, Schoener's D; yellow, Hellinger's I); the
same-colour dashed rules and axis triangles mark the observed values, printed at
the top left of each panel. Observed overlap fell below the null for 9 of the
10 variables (permutation p < 0.05); srad was indistinguishable from random
grouping. Input was the breed-level insertion-frequency matrix of 16,361 TE loci
in 29 populations (16,354 retained after dropping loci with >20% missing data).
