# variable_contribution — 环境变量贡献 + 置换重要性（两面板）

复刻 **Yuan et al. 2026, Zoological Research 47(5):1793–1812, Figure 2A/2B** 的版式：
主面板是"全部候选变量按贡献率排序的柱状图 + 阈值虚线"，右上叠一个"入选变量的贡献柱 +
置换重要性折线"的双轴小面板。原图是 MaxEnt/ENM 输出，这里换成 TE × 气候的 GEA 口径。

输出：`variable_contribution.png`（183 × 82 mm，600 dpi）、`variable_contribution.pdf`（矢量文字）。

## 一、图里每个数从哪来

| 面板 | 量 | 定义 |
|---|---|---|
| A | Contribution (%) | 该变量 FDR 显著 TE 位点数 ÷ 全部显著关联数 × 100（合计 100%） |
| B 柱 | Variable contribution (%) | 偏 RDA 中该变量的 **Shapley（LMG）贡献**，对全部 2¹⁰ 个子集求平均，合计 = 全模型 R² |
| B 线 | Permutation importance (%) | 把该变量在品种间随机置换 999 次，重拟合后解释率的平均下降，归一化到 100% |

**A 的口径**：28 个候选气候变量 × 15,620 个多态 TE 位点逐对 Spearman，变量内 BH-FDR
（与 `05_association/te_locus_assoc.py` 同一实现），取 q<0.05。合计 **3,940** 条显著关联，
**11 个变量** 越过 1% 阈值线。

**B 的口径**：偏 RDA，`Condition = 经纬度 + TE-PAV 矩阵自身 PCA 前 3 轴`（对应服务器
`te_rda.py --npc 3`），10 个核心变量，29 品种。全模型 **R² = 0.4952**，与服务器
`05_association/results/rda_summary.txt` 的记录完全一致。

## 二、复现

```bash
# 1) 算数（需要三个上游表，见下）
python3 compute_variable_stats.py \
    --geno  te_pav_breed_matrix.csv \
    --env   climate_modify.csv \
    --sel   env_selected.csv \
    --out   variable_stats.tsv

# 2) 画图
python3 plot_variable_contribution.py --input variable_stats.tsv \
        --out variable_contribution --line perm
```

输入表来源（本仓库只存派生表 `variable_stats.tsv`，不存原始矩阵）：

| 文件 | 来源 | 规模 |
|---|---|---|
| `te_pav_breed_matrix.csv` | 服务器 `04_te_pav/results/` | 29 品种 × 16,361 位点 PAV 频率 |
| `climate_modify.csv` | `~/Desktop/ChickenTE/其他/气候数据整理/` | 29 行 × 42 列（含经纬度） |
| `env_selected.csv` | 服务器 `03_climate/results/` | 29 × 10（z-score 后的核心变量） |

重算开销：单核约 **2.5 分钟**（置换 + 2¹⁰ 子集全在 numpy 里做）。务必设
`OMP_NUM_THREADS=1`，这种 29×15,620 的小矩阵反复 `lstsq`，多线程 BLAS 反而慢 6 倍。

## 三、解读时必须带上的两个警告

1. **B 的柱几乎等高（9.2–11.1%）**：这是共线性下的真实现象，不是画错。10 个核心变量
   彼此相关，任何"贡献分解"都会把方差摊平；Shapley 分解只能保证**合计 = 全模型 R²**，
   不能保证拉开差距。排序信息主要来自折线。
2. **置换重要性与边际关联不一致**：`bio2`（18.7%）、`bio19`（17.5%）在 A 中
   **没有一条显著关联**，却是 B 中置换重要性最高的两个。共线性 + n=29 时置换重要性
   度量的是"不可替代性"，不是"边际信号"，两者不符时**不能**据此宣称 bio2/bio19 更重要。

## 四、版式开关

| 参数 | 作用 |
|---|---|
| `--line perm`（默认） | 面板 B 折线 = 置换重要性 |
| `--line assoc` | 面板 B 折线 = 该变量在 A 中的关联份额（10 个变量内重新归一） |
| `--threshold 1.0` | 面板 A 的阈值虚线 |
| `--dpi 600` | PNG 分辨率 |

风格层取自 `figure-style/style/`（`pangenome_spectrum` 配色 + theme.json 的字号/线宽）；
找不到时脚本内置同款色值，可单独拷走使用。

## 五、踩过的坑

- **样本顺序**：用 `sorted(set(...))` 对齐品种会按字符串排序（`1_`、`10_`、`2_`…），
  经纬度必须按**同一个顺序**取；错位后全模型 R² 会从 0.4952 掉到 0.489 且置换重要性全变。
  脚本里 lon/lat 在 `raw.loc[common]` 之后取，就是为了避开这一条。
- **值标签不要放在柱顶**：折线会穿过去（原图就有这个毛病）。这里把数值放进柱内、白字。
