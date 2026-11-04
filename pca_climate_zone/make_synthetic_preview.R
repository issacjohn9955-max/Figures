#!/usr/bin/env Rscript
# =============================================================================
# make_synthetic_preview.R —— 六区全部出现时的版式预览（**合成数据，非真实样本**）
#
# 本项目现有的 TE-403 / SNP-200 两套真实基因型只覆盖 4 个气候区
# （North / Middle / Northwest / Southeast，无 Southwest、无 Xizang），
# 所以真实图里只能看到 4 个图例条目。这个脚本按"每区若干点、中心不同"的
# 方式造一份**合成**得分表，用来验证六区色/形编码在同图例里不打架，
# 也方便以后补齐西南/藏鸡样本时对照检查。文件名与 README 均标注 synthetic。
#
# 用法：Rscript make_synthetic_preview.R
# 输出：data/synthetic_6zone_scores.tsv, data/synthetic_6zone_variance.tsv
#       preview_6zone_synthetic.png/.pdf
# =============================================================================
script_dir <- local({
  a <- commandArgs(trailingOnly = FALSE)
  f <- sub("^--file=", "", a[grep("^--file=", a)])
  if (length(f)) dirname(normalizePath(f[1])) else getwd()
})
set.seed(20261104)

zones <- c("North", "Middle", "Northwest", "Southeast", "Southwest", "Xizang")
centres <- list(
  North     = c(-0.055,  0.020), Middle    = c(-0.010,  0.028),
  Northwest = c(-0.040, -0.012), Southeast = c( 0.030,  0.012),
  Southwest = c(-0.012, -0.040), Xizang    = c( 0.080, -0.052)
)
n_per_zone <- c(North = 70, Middle = 90, Northwest = 40,
                Southeast = 110, Southwest = 55, Xizang = 30)

rows <- lapply(zones, function(z) {
  n  <- n_per_zone[[z]]
  mu <- centres[[z]]
  sd <- 0.009
  data.frame(
    sample = sprintf("SYN_%s_%03d", z, seq_len(n)),
    breed  = "synthetic",
    province = "synthetic",
    zone   = z,
    PC1 = rnorm(n, mu[1], sd),
    PC2 = rnorm(n, mu[2], sd),
    stringsAsFactors = FALSE
  )
})
dat <- do.call(rbind, rows)
dir.create(file.path(script_dir, "data"), showWarnings = FALSE, recursive = TRUE)
write.table(dat, file.path(script_dir, "data", "synthetic_6zone_scores.tsv"),
            sep = "\t", quote = FALSE, row.names = FALSE)

# 方差表：合成数据没有真实方差，写占位值并注明（图上百分比会显示这两个值）
write.table(data.frame(PC = c("PC1", "PC2"),
                       variance_explained = c(12.40, 8.15)),
            file.path(script_dir, "data", "synthetic_6zone_variance.tsv"),
            sep = "\t", quote = FALSE, row.names = FALSE)

# 调真实绘图脚本渲染（同一套版式参数）
cmd <- sprintf(
  "Rscript %s --scores %s --variance %s --out %s --palette chromatic_nc --tag B --width-mm 160 --height-mm 111",
  shQuote(file.path(script_dir, "plot_pca_climate_zone.R")),
  shQuote(file.path(script_dir, "data", "synthetic_6zone_scores.tsv")),
  shQuote(file.path(script_dir, "data", "synthetic_6zone_variance.tsv")),
  shQuote(file.path(script_dir, "preview_6zone_synthetic"))
)
cat("[i] 合成数据（六区全编码预览，非真实样本）：", nrow(dat), "点\n")
cat("[i] 注意：图中的方差百分比是占位值（12.40% / 8.15%），不对应任何真实分析\n")
status <- system(cmd)
quit(status = status)
