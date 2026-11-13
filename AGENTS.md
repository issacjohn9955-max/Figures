# AGENTS.md — 图件复现任务

本仓库是一套论文图件的"代码 + 数据 + 成品"仓库。每个目录是一个独立图件模块。

**你的任务：在一台新机器上把下面 6 个 Python 模块重新跑一遍，判断能否复现。**
详细背景见 [`REPRODUCE.md`](REPRODUCE.md)，本文件只讲怎么做和怎么交付。

---

## 0. 硬性约束（先读这条）

1. **不要修改 `data/` 下的任何文件**。这些是成品图的输入，改了就对不上稿件。
2. **不要修改绘图脚本的参数、字号、配色、画幅**。若渲染结果与仓库里的图不同，**报告差异，不要"修好它"**。
3. **不要联网**，不要下载数据，不要安装非必要的包。所有输入都在各自模块的 `data/` 里。
4. **不要在仓库根目录运行脚本**，每个模块的命令都必须在该模块目录内执行。
5. 生成的图**覆盖同名文件前先备份**，或统一输出到 `outputs/`。

---

## 1. 环境

```bash
python3 -c "import sys, numpy, pandas, matplotlib; print(sys.version.split()[0], numpy.__version__, pandas.__version__, matplotlib.__version__)"
```

- Python ≥ 3.9；需要 `numpy`、`pandas`、`matplotlib`（≥3.5）
- **不需要** scipy / GDAL / rasterio / R / circlize
- 中文字体（只有 `fig1c_tree_admixture` 需要）：

```bash
fc-list :lang=zh | head          # 看看有没有中文字体
# 没有的话：
# Debian/Ubuntu: apt-get install -y fonts-noto-cjk
# RHEL/CentOS:   yum install -y google-noto-sans-cjk-fonts
```

字体缺失不会让命令失败，但 `fig1c` 的中文品种名会变成方框——这属于"跑成功但结果不可用"，必须报告。

---

## 2. 执行

先确认版本：

```bash
git -C <repo> log -1 --format='%h %s'
```

预期为 `f4b0775` 或之后。然后逐条执行（在仓库根目录）：

```bash
( cd fig1b_pca            && python3 plot_fig1b_pca.py --data-dir data --out fig1b_pca )
( cd fig1c_tree_admixture && python3 plot_fig1c_tree_admixture.py --data-dir data --out fig1c_tree_admixture )
( cd fig2_environment     && python3 plot_fig2_env.py --data-dir data --out fig2_environment )
( cd fig3_rda             && python3 plot_fig3_rda.py --data-dir data --out fig3_rda )
( cd fig4_evidence        && python3 plot_fig4_evidence.py --data-dir data --out fig4_evidence )
( cd fig5_te              && python3 plot_fig5_te.py --data-dir data --out fig5_te )
```

每条命令的退出码、stdout、stderr 都要留下记录（建议 `2>&1 | tee logs/<module>.log`）。

---

## 3. 验收：只看三件事

**不要做像素级比对。** 字体、抗锯齿、matplotlib 版本不同，PNG 必然有差异，这不代表复现失败。

### ① 有没有跑通
- 退出码 0
- 日志里没有 `Traceback`
- 没有 `Glyph ... missing from font(s)` 警告

### ② 尺寸对不对

```bash
python3 -c "from PIL import Image; import glob; [print(f, Image.open(f).size) for f in sorted(glob.glob('fig*/*.png'))]"
```

| 图 | 期望尺寸（px） |
|---|---|
| `fig1b_pca/fig1b_pca.png` | 约 4204 × 2740 |
| `fig1c_tree_admixture/fig1c_tree_admixture.png` | 4157 × 2456 |
| `fig2_environment/fig2_environment.png` | 4204 × 2740 |
| `fig3_rda/fig3_rda.png` | 4204 × 2740 |
| `fig4_evidence/fig4_evidence.png` | 4204 × 2551 |
| `fig5_te/fig5_te.png` | 4204 × 2645 |

±10 px 以内算通过（不同 matplotlib 版本的 tight bbox 略有差别）。

### ③ 数字对不对（最重要）

这些数字来自各自的输入表，与绘图代码无关，**是唯一可靠的验收点**。
请把实际跑出来的数值填进右列：

| 模块 | 期望值 | 实际 |
|---|---|---|
| fig1b_pca | 140 只 / 13 品种；SNP 189,489 位点，PC1 **1.94%**、PC2 **1.85%** | |
| | TE 7,749 位点，PC1 **4.27%**、PC2 **2.36%** | |
| fig1c_tree_admixture | 140 个体 / 13 品种；K=2 CE 0.7400、K=3 **0.7389**、K=4 0.7423 | |
| fig2_environment | 28 个变量；bio11 20.1%、bio1 15.4%、bio6 13.8%、srad 12.5%、bio3 12.5% | |
| fig3_rda | 总约束 **43.85%**，伪 F **1.406**，p **0.001**；五轴 15.2/9.8/8.6/6.2/4.2% | |
| fig4_evidence | 973 对 / 682 位点；LFMM-only **971**、Spearman-only **2**、两者 **0**、RDA 离群 **0** | |
| | 单环境 **486**；严格核心 **0** | |
| fig5_te | 背景 **1,680** / 关联 **682**；LINE 34→33%、LTR 19→20%、DNA 16→17% | |
| | 超家族富集 DTM 1.14、ERV3 0.98、CR1 0.96，**所有 CI 跨 1** | |

---

## 4. 出问题时怎么做

| 情况 | 你要做的 |
|---|---|
| 命令报错 | 贴完整 traceback + 该模块 `data/` 的文件清单（`ls -l data/`） |
| 尺寸差很多 | 贴实际尺寸 + matplotlib 版本 |
| 数字对不上 | **停下来**，贴实际值，不要自行调整输入或代码"凑"数字 |
| 中文变方框 | 报"缺中文字体" + `fc-list :lang=zh` 的输出 |
| 图片能生成但明显错乱（元素重叠、坐标轴空白） | 贴 PNG 路径 + 截图，不要修 |

**任何情况下都不要为了让结果"看起来对"而修改 `data/` 或脚本。**

---

## 5. 交付格式

提交一份 `REPRO_REPORT.md`，包含：

1. 仓库 commit、主机系统、Python / numpy / pandas / matplotlib 版本
2. 六个模块逐条：命令、退出码、耗时、日志路径
3. 尺寸核对表（期望 vs 实际）
4. 数字核对表（第 3 节那张表，填"实际"列）
5. 所有警告（逐条列出，尤其是字体相关的）
6. 结论：哪些模块完全复现、哪些有差异、差异来源的判断
7. 生成图的路径清单

---

## 6. 参考

- [`REPRODUCE.md`](REPRODUCE.md)：环境、命令、验收标准的完整版
- 每个模块的 `README.md`：该图的口径、算法与注意事项
- [`FIGURE_GUIDE.md`](FIGURE_GUIDE.md)：每张图的原理与"不能怎么用"
- [`FINAL_FIGURES.md`](FINAL_FIGURES.md)：投稿时该引用哪些文件
