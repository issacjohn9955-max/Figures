# style/ —— figure-style 快照（vendored）

本目录是 `figure-style` 仓库 `style/` 层的**只读快照**，目的是让本仓库**克隆下来就能出图**，
不必额外准备第二个仓库。

| 文件 | 内容 |
|---|---|
| `theme.json` | 画幅预置、字号层级、线宽、骨架色、规则开关（唯一事实来源） |
| `palettes.json` | 三套配色：`pangenome_spectrum`（默认）/ `botanical_genome` / `chromatic_nc` |
| `ggplot2_theme.R` | R 入口：`theme_fs()` / `scale_colour_fs()` / `save_fs()` / `panel_tag()` |
| `matplotlib.mplstyle` | Python 入口配套的 rc 参数 |

## 谁在用

`pca_climate_zone/plot_pca_climate_zone.R` 会按以下顺序找风格层：

1. 环境变量 `FIGURE_STYLE_DIR`（指向含 `style/` 的目录）——显式指定优先；
2. 从脚本目录向上找到的 **本目录** `style/ggplot2_theme.R`（默认，仓库内自带）；
3. 从脚本目录向上找到的并排 `figure-style/style/ggplot2_theme.R`（本机开发时的源仓库兜底）。

`ggplot2_theme.R` 内部会沿目录向上找 `style/palettes.json` 定位"根"，找到本目录的上一层
（即本仓库根）即可正常工作。

## 来源与授权

* 上游：[1577377232/Genomics-Figure-Styles](https://github.com/1577377232/Genomics-Figure-Styles) v2.0
  （`figures/gwas_manhattan/`，commit `13f1fbb`）
* 中间层：本机 `figure-style` 仓库，commit 见 `VENDORED.md`
* 搬运边界与未搬项见 `VENDORED.md`；本仓库只取"画幅/字号/配色/视觉规则"，不含对方的研究流程。

## 与源仓库的同步

本快照**不会自动更新**。改完 `figure-style` 后回来跑：

```bash
bash style/sync_from_figure_style.sh            # 从 ../figure-style/style 覆盖并记录新 commit
bash style/sync_from_figure_style.sh --check    # 只比对，有差异返回 1（可放进 CI）
```

同步后重跑受影响的图，否则会出现"源仓库改了、仓库里的图没改"的漂移。
