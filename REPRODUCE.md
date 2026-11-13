# 复现说明（Fig1B–Fig5）

本文件列出**新增的 6 个 Python 图件模块**的运行方法、依赖与验收标准。
更早的 R 模块（`china_sampling_map` … `world_distribution_map`）仍由根目录 `run_all.sh` 覆盖。

所有模块**自包含**：`data/` 里已带齐输入，克隆仓库后逐目录运行即可，不需要连服务器、不需要下载。

---

## 1. 环境

| 项 | 要求 |
|---|---|
| Python | ≥ 3.9（开发环境 3.10，服务器 3.14 也可） |
| 依赖 | `numpy`、`pandas`、`matplotlib`（≥3.5）；**不需要** scipy / GDAL / rasterio / circlize |
| 中文字体 | 仅 `fig1c_tree_admixture` 需要（品种名是中文）。脚本会依次尝试 Hiragino Sans GB → PingFang → Noto Sans CJK → 文泉驿 → SimHei；Linux 上建议 `apt install fonts-noto-cjk`，否则中文会变成方框（图仍能生成，不报错） |

```bash
python3 -c "import numpy, pandas, matplotlib; print(numpy.__version__, pandas.__version__, matplotlib.__version__)"
```

---

## 2. 逐模块运行

每个命令都在**该模块目录内**执行：

| 模块 | 命令 | 输出 |
|---|---|---|
| `fig1b_pca` | `python3 plot_fig1b_pca.py --data-dir data --out fig1b_pca` | `fig1b_pca.png/.pdf` |
| `fig1c_tree_admixture` | `python3 plot_fig1c_tree_admixture.py --data-dir data --out fig1c_tree_admixture` | `fig1c_tree_admixture.png/.pdf` |
| `fig2_environment` | `python3 plot_fig2_env.py --data-dir data --out fig2_environment` | `fig2_environment.png/.pdf` |
| `fig3_rda` | `python3 plot_fig3_rda.py --data-dir data --out fig3_rda` | `fig3_rda.png/.pdf` |
| `fig4_evidence` | `python3 plot_fig4_evidence.py --data-dir data --out fig4_evidence` | `fig4_evidence.png/.pdf` |
| `fig5_te` | `python3 plot_fig5_te.py --data-dir data --out fig5_te` | `fig5_te.png/.pdf` |

一次跑完：

```bash
( cd fig1b_pca            && python3 plot_fig1b_pca.py --data-dir data --out fig1b_pca )
( cd fig1c_tree_admixture && python3 plot_fig1c_tree_admixture.py --data-dir data --out fig1c_tree_admixture )
( cd fig2_environment     && python3 plot_fig2_env.py --data-dir data --out fig2_environment )
( cd fig3_rda             && python3 plot_fig3_rda.py --data-dir data --out fig3_rda )
( cd fig4_evidence        && python3 plot_fig4_evidence.py --data-dir data --out fig4_evidence )
( cd fig5_te              && python3 plot_fig5_te.py --data-dir data --out fig5_te )
```

> `fig5_te` 需要 Fig4 的证据表——已复制到 `fig5_te/data/te_env_pair_evidence.csv`，脚本默认先找这里。

---

## 3. 验收标准

**不要用像素比对跨平台验收**（字体、抗锯齿、matplotlib 版本都会让 PNG 有细微差异）。
按下面三条判断：

1. **命令退出码为 0**，日志里没有 `Traceback`、没有 `Glyph ... missing from font` 警告；
2. **生成的两张图尺寸与仓库一致**（`python3 -c "from PIL import Image; print(Image.open('x.png').size)"`）；

   | 图 | 尺寸（px，600 dpi） |
   |---|---|
   | fig1b_pca | 4204 × 2740 左右 |
   | fig1c_tree_admixture | 4157 × 2456 |
   | fig2_environment | 4204 × 2740 |
   | fig3_rda | 4204 × 2740 |
   | fig4_evidence | 4204 × 2551 |
   | fig5_te | 4204 × 2645 |

3. **关键数字与下表一致**（允许四舍五入差异）。数字来自各自的输入表，与绘图代码无关，是真正的验收点。

| 模块 | 关键数字 |
|---|---|
| fig1b_pca | n = 140 只 / 13 品种；SNP 189,489 位点 → PC1 1.94%、PC2 1.85%；TE 7,749 位点 → PC1 4.27%、PC2 2.36% |
| fig1c_tree_admixture | 140 个体、13 品种；交叉熵 K=2 0.7400、K=3 **0.7389**、K=4 0.7423 |
| fig2_environment | 28 个变量；bio11 20.1%、bio1 15.4%、bio6 13.8%、srad 12.5%、bio3 12.5%；1% 筛选线 |
| fig3_rda | 总约束解释 **43.85%**，伪 F = 1.406，p = 0.001；五轴 15.2 / 9.8 / 8.6 / 6.2 / 4.2% |
| fig4_evidence | 973 对 / 682 位点；LFMM-only 971、Spearman-only 2、两者 **0**、RDA 离群 0；单环境 486；严格核心 **0** |
| fig5_te | 背景 1,680 / 关联 682；LINE 34→33%、LTR 19→20%、DNA 16→17%；所有超家族富集 CI 跨 1；41 条染色体 |

---

## 4. 常见问题

| 现象 | 原因 / 处理 |
|---|---|
| `Glyph ... missing from font(s)` | 服务器缺中文字体，见第 1 节；只有 fig1c 受影响 |
| PNG 尺寸对但内容空白 | 检查 `data/` 是否完整（`fig2` 需要三个 `.npy`，`fig5` 需要 `te_catalog.csv` 与 `main.chrom.sizes`） |
| `fig2` 报 `UnicodeDecodeError` | `china_provinces.geojson` 应为 UTF-8；仓库里那份是对的，别用 GBK 版本覆盖 |
| `fig3` 解析不到变量表 | `rda_summary.txt` 里的表头必须含 `变量  RDA1 ...`；该文件是服务器原样导出的，别手工编辑 |

---

## 5. 与 `run_all.sh` 的关系

根目录的 `run_all.sh` 是作者机器上的自检脚本：它把每个模块拷到 `outputs/` 里重跑，并与仓库里的 PNG 做
**逐像素平均差 < 1%** 的比对。跨平台时这个阈值偏严（字体差异会超），所以新增的 6 个模块**没有**接进它。

需要统一入口时，按第 2 节的循环跑即可。
