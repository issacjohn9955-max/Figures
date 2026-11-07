# R_v16 — 组合图产物说明

由 `06_scripts/plot_combined_te_callouts_v16.R`（经 `run_combined_v16.sh`）生成。
左侧 Circos 与 `../R_v15/` 逐像素一致，右侧为四类 TE 结构示意与连接箭头。

| 文件 | 说明 |
|---|---|
| `chicken_GRCg7b_R_v16_combined_TE-callouts.pdf` | 矢量主文件，15.8 × 10 in；cairo 可用时内嵌字体，否则由 quartz 输出 |
| `chicken_GRCg7b_R_v16_combined_TE-callouts.png` | 600 dpi，9480 × 6000 px |
| `*.preview.png` | 150 dpi 预览 |
| `*.figure_geometry.tsv` | 画板、圆心半径、面板边界、字体、后端、dpi |
| `*.connectors.tsv` | 四根箭头的起止点、角度、半径、轨道色 |
| `*.input_files.tsv` | 每个输入文件的相对路径、字节数、sha256 |
| `*.settings.R` | 完整生效配置（dput），可复现同一次渲染 |
| `*.output_manifest.tsv` | 本目录产物的字节数与 sha256 |
| `QC_report.md` | 与 V15 一致性、箭头几何的说明 |
| `validation_report.json` | 机器可读的校验结果 |
| `run_v16.log` | 本次运行的命令与输出 |

校验：`python3 06_scripts/check_combined_v16.py`（11 项，含 sha256、PNG 像素尺寸、PDF MediaBox、
箭头是否落在 48° 开口内）。

本目录不含任何个体级基因型、表型或原始 GWAS 矩阵。
