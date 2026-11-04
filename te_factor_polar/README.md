# te_factor_polar — 气候因子 TE 关联位点的 Shared / Unique 极坐标堆叠柱

复刻 Yuan et al. 2026 *Zoological Research*（本地 `sample.pdf`）**Figure 3B** 的版式：
6 个楔形沿圆周排布，每个楔形是内「Unique」+ 外「Shared」的两层堆叠，楔形之间留白缝，
淡灰色同心环做径向网格，左侧/底部保留一条 L 形黑色坐标轴（刻度 0/100/200/300 贴在轴内侧），
类别名加粗、始终水平，图例横排置顶，左上角一个加粗面板号。

用我们自己的数据重画后，得到 `te_factor_polar.png/.pdf`（4 主因子版，投稿用）与
`te_factor_polar_all7.png/.pdf`（7 个显著因子全量版）。

```
te_factor_polar/
├─ plot_polar_shared.R          # 唯一的绘图脚本（R + ggplot2）
├─ build_input.py               # 从 te_locus_sig.csv 生成输入表（定义见下）
├─ te_factor_shared_unique.tsv  # 真实数据输入表（7 个因子）
├─ te_factor_shared_unique_core.tsv # 同上去掉 <20 条的三个因子（主图用）
├─ example_paper_figB.tsv       # 参考图数字（截图量取，仅用于版式复核）
├─ te_factor_polar.png/.pdf     # 成品①：SRAD / BIO_3 / BIO_9 / WIND
├─ te_factor_polar_all7.png/.pdf# 成品②：再加 ELEV / DM / BIO_18（位点太少，几乎看不见）
├─ demo_paper_style.png/.pdf    # 成品③：用参考图数字跑同款脚本，版式对照用
└─ demo_compare.png             # 参考图 vs 复刻并排
```

## 输入表

制表符分隔，三列，长表：

| category | series | value |
|---|---|---|
| SRAD | Shared | 181 |
| SRAD | Unique | 305 |
| BIO_3 | Shared | 167 |
| … | … | … |

* `category`：楔形名。**文件里的先后顺序 = 从 3 点钟位置起逆时针的绘制顺序**（第一行在右边）。
* `series`：堆叠层。**第一个出现的水平画在外圈，第二个画在内圈**，同时决定图例顺序
  （所以 `Shared` 在前 → 红色在外、图例先红后蓝）。
* `value`：径向数值。

## 数据来源与「Shared / Unique」定义

数据来自 ChickenTE 服务器分析产物 `~/Desktop/ChickenTE/severdata/te_locus_sig.csv`
（29 个品种 × 16,361 个 TE-PAV 位点 × 10 个核心气候变量，逐位点 Spearman，
每个变量内部做 FDR，共 1,268 条显著关联、涉及 982 个位点）。

* **关联**：该 (变量, 位点) 组合在 per-variable FDR 下显著（即出现在 `te_locus_sig.csv` 里）。
* **Unique**：该位点只对这一个变量显著。
* **Shared**：该位点除对本变量显著外，还对至少一个其它变量显著。

因此 Unique + Shared 等于该变量的显著关联数，7 个因子相加 = 1,268 条。
重新生成：

```bash
python3 build_input.py --sig ~/Desktop/ChickenTE/severdata/te_locus_sig.csv \
        --out te_factor_shared_unique.tsv
```

| 因子 | Unique | Shared | 合计 |
|---|---:|---:|---:|
| SRAD | 305 | 181 | 486 |
| BIO_3 | 317 | 167 | 484 |
| BIO_9 | 122 | 126 | 248 |
| WIND | 14 | 25 | 39 |
| ELEV | 3 | 3 | 6 |
| DM | 2 | 1 | 3 |
| BIO_18 | 1 | 1 | 2 |

前三个因子（SRAD/BIO_3/BIO_9）合计 1,218 条，占全部关联的 96%；
`te_factor_polar` 只画 SRAD/BIO_3/BIO_9/WIND 四个（≥20 条），
`te_factor_polar_all7` 是全量版——ELEV/DM/BIO_18 在 0–500 的径向上只有 1–6，
会缩成极细的楔形，投稿时建议用四因子版并在图注里说明剔除阈值。

## 复现

```bash
# 主图（4 因子，输入表 te_factor_shared_unique_core.tsv）
Rscript plot_polar_shared.R --input te_factor_shared_unique_core.tsv --out te_factor_polar \
        --ymax 500 --breaks 0,100,200,300,400,500 --tag B --width 84 --height 80

# 全量（7 因子）
Rscript plot_polar_shared.R --input te_factor_shared_unique.tsv --out te_factor_polar_all7 \
        --ymax 500 --breaks 0,100,200,300,400,500 --tag B --width 84 --height 80

# 版式复核（参考图数字）
Rscript plot_polar_shared.R --input example_paper_figB.tsv --out demo_paper_style \
        --ymax 340 --breaks 0,100,200,300 --tag B --width 84 --height 80
```

`te_factor_shared_unique_core.tsv` 就是从全量表里筛出合计 ≥20 条的四个因子：
`awk -F'\t' 'NR==1||$1=="SRAD"||$1=="BIO_3"||$1=="BIO_9"||$1=="WIND"' te_factor_shared_unique.tsv`

## 版式参数

| 参数 | 默认 | 说明 |
|---|---|---|
| `--ymax` | 自动取 `pretty()` | 径向最大值；环的最外圈画在这个值上 |
| `--breaks` | 每 100 一格 | 带刻度标签的主环 |
| `--minor` | 主环间隔的一半 | 不带标签的次环（参考图里 50 一格） |
| `--bar-width` | 0.90 | 楔形占扇区宽度的比例，剩下的就是白缝 |
| `--colours` | `#FD6456,#4BCCE0` | 外圈/内圈颜色（参考图取色：红 `#FD6456`、蓝 `#4BCCE0`） |
| `--start-deg` | 0 | 第一个楔形中心的角度，逆时针、0 = 3 点钟方向 |
| `--tag` | 空 | 左上角面板号（`B`），不需要就留空 |
| `--label-size / --tick-size / --legend-size / --tag-size` | 8.4 / 7.4 / 8.4 / 11.5 | 字号（pt） |
| `--width / --height / --dpi` | 84 / 80 / 600 | 输出画幅（mm）与位图分辨率 |

## 实现要点（踩过的坑）

1. **L 形坐标轴不是手画的**：`coord_polar()` + `theme_classic()` 时 ggplot 会保留
   `axis.line`，于是左边线/底边线仍是直线，而网格变成圆环——参考图那条「左侧竖轴 + 底部横线」
   就是这么来的。用 `theme_classic()` 而不是 `theme_void()` 才能保住它。
2. **图的朝向要自己算**：ggplot 的 `start` 从 12 点钟起、`direction = -1` 是逆时针，
   且第一个扇区中心还要再偏 `180/n`。本脚本已按 ggplot2 4.x 实测标定：
   `start_deg` 就是「第一个楔形中心逆时针离开 3 点钟的度数」，第一行 = 最右边那个楔形。
3. **`clip = "off"` 会让面板不再正方形**：必须同时 `theme(aspect.ratio = 1)`，否则圆环被拉成椭圆。
4. **堆叠顺序**：`fill` 因子的第一个水平落在**外圈**，第二个在内圈；
   想要「Unique 在内、Shared 在外、图例先 Shared」，输入表里 Shared 行在前。
5. **径向轴比圆环长一截**：ggplot2 4.x 会把类别标签的位置也算进 panel，面板因此比圆环大一圈，
   左侧轴自然会长出圆环外。参考图（ggplot2 3.x 出的）轴与圆环等高，这点本脚本没有强行对齐。

## 复核

`demo_compare.png` 左边是 `sample.pdf` 的原始截图，右边是 `example_paper_figB.tsv`
（从截图按刻度环量出的数值）跑同款脚本的结果：楔形角度（BIO_2 在 3 点钟、逆时针
BARE→TREES→SRAD_11→PREC_08→CROPLAND）、内外层比例、环间距与轴刻度都对得上。
