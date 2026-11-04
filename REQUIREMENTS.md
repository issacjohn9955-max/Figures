# 环境与依赖 / Environment

克隆下来能复现到哪一步，取决于本机装了什么。这份文件是唯一的依赖清单；
`bash run_all.sh` 会按下面的表逐模块重渲染并和仓库里的成品图比对，缺什么会直接报出来。

## 1. 实测通过的组合

| | 版本 | 说明 |
|---|---|---|
| R | 4.5.2 (aarch64-apple-darwin) | 所有 `.R` 脚本；R ≥ 4.1 即可 |
| ggplot2 | 4.0.1 | **4.x 与 3.x 出的极坐标图有细微差别**，见第 4 节 |
| Python | 3.13 | 所有 `.py` 脚本；3.9+ 即可 |
| numpy / pandas / matplotlib | 2.1.3 / 2.2.3 / 3.10.0 | 地图、直方图、零分布图 |

## 2. 逐模块依赖

| 模块 | R 包 | Python 包 | 外部数据 |
|---|---|---|---|
| `china_sampling_map` | — | numpy, matplotlib | **需 curl 下载两份 geojson**（见该模块 README「Boundary data」） |
| `corr_ci_scatter` | ggplot2, grid | — | 无（`te_method_corr.tsv` 已入库） |
| `gea_driver_radar` | ggplot2, grid | — | 无 |
| `gea_marginal_scatter` | ggplot2, **patchwork**, scales | — | 无（`example_*.tsv` 已入库） |
| `niche_overlap_null` | — | numpy, pandas, matplotlib | 无（`data/*.tsv` 已入库；重算才需 severdata） |
| `pca_climate_zone` | ggplot2, jsonlite | — | 无（`data/*.tsv` 已入库） |
| `te_ibe_adaptive_neutral` | ggplot2 | — | 无（`input/` 下的群体级聚合表已入库） |
| `te_factor_polar` | ggplot2, grid, scales | — | 无（输入表已入库；从原始结果重建才需 severdata） |
| `variable_contribution` | — | numpy, pandas, matplotlib | 无（`variable_stats.tsv` 已入库；从原始结果重算才需 severdata 的三个上游表） |
| `style/` | jsonlite（`ggplot2_theme.R`），ragg **可选** | matplotlib | — |

`ragg` 只是让 PNG 用真 Arial 并写入 DPI 元数据；没有它自动退回系统 `png()` 设备，
出来的图一样能用于投稿（字体是 Helvetica，与 Arial 同度量）。

## 3. 装依赖

```bash
# R：默认库不可写时装到用户库（R_LIBS_USER 或脚本里 .libPaths() 都能生效）
mkdir -p ~/R/libs
Rscript -e 'install.packages("patchwork", repos="https://cloud.r-project.org", lib=path.expand("~/R/libs"))'
R_LIBS_USER=~/R/libs bash run_all.sh

# Python
python3 -m pip install numpy pandas matplotlib scipy
```

## 4. 版本敏感点（会影响成品像素）

1. **ggplot2 4.x 的极坐标**：4.x 会把类目标签的位置算进 panel，径向轴因此比圆环长出一截；
   3.5.x 出的图轴与圆环等高。`te_factor_polar/README.md` 里记了这条差异。
   要严格复刻 3.x 的观感，需要手绘 L 形轴。
2. **字体**：整库按 Helvetica/Arial 度量出图。Linux 上若没有这两款字体，`pdf()` 会回退到
   Nimbus Sans，字宽会有百分级差异。
3. **`run_all.sh` 的判据**：新渲染的 PNG 与仓库里的那张做平均绝对差，
   <1% 记为「一致」，>1% 记为「漂移」。字体替换、`ggplot2` 大版本变化都会让它变红。

## 5. 已知缺口

| 缺口 | 影响 | 处理 |
|---|---|---|
| `china_sampling_map/data/*.geojson` 不入库 | 干净克隆跑不了地图，脚本会报 `missing boundary file` 并指向 README 里的 curl 命令 | 按 README 下载后即可跑 |
| `gea_marginal_scatter` 需要 `patchwork` | 本机默认 R 库不可写，且当前网络拉不到 CRAN 索引（`src/contrib/PACKAGES` 取不到，`available.packages()` 返回 0 个包），所以这个包装不上，该模块的图只能看不能重渲 | 换台机器 / 用 conda 的 R / 挂上能通 CRAN 的镜像后 `install.packages("patchwork")` |
| 部分 `build_*.py` 的 `--base` 默认指向 `~/Desktop/ChickenTE/severdata` | 只影响「从原始结果重建输入表」，不影响重画 | 显式传 `--base` 指到自己的路径 |
| 成品 PNG 里没写版本戳 | 无法从图本身判断是哪版代码出的 | 以 `git log -- <模块>` 为准 |
