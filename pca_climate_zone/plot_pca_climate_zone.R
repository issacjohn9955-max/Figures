#!/usr/bin/env Rscript
# =============================================================================
# plot_pca_climate_zone.R —— 复刻 Yuan et al. 2026 (Zool Res) Fig 2B 版式
#                            PCA 散点 × 六大农业气候区（颜色 + 形状双编码）
#
# 视觉规范来自 ../figure-style/style/{theme,palettes}.json，本脚本不写死任何
# 字号/线宽/画幅/十六进制色值。四处"论文复刻"式覆盖，均在下文注释标明来由：
#   1) 字号整体放大（论文版式：图例/轴标题显著大于正文），type_scale × theme 值；
#   2) 轴标题、图例标题加粗（原图如此）；
#   3) 图例移到面板上方横排两行（原图布局）；
#   4) 六区色/形固定映射，缺区不借用别区颜色。
#
# 用法：
#   Rscript plot_pca_climate_zone.R --scores pca_te_scores.tsv \
#       --variance pca_te_variance.tsv --out figures/fig_pca_te_climate
# 参数：
#   --scores      含 sample, PC1, PC2, zone 的 TSV（UTF-8）
#   --variance    含 PC, variance_explained 的 TSV（用于轴标签百分比）
#   --out         输出前缀（自动写 .pdf + .png@600dpi）
#   --palette     pangenome_spectrum（默认）/ botanical_genome / chromatic_nc
#   --tag         面板字母，如 B；留空不画
#   --type-scale  字号相对 theme.json 的放大倍数（默认 1.85）
#   --point-size  点直径(mm)，默认 theme.json 的 marks.point_diameter_mm × type_scale
#   --preset      画幅预置（single_col / double_col / wide_panel）
#   --width-mm --height-mm  覆写画幅
#   --legend-rows 图例行数（默认 2）
# =============================================================================
suppressPackageStartupMessages({
  library(ggplot2)
})

# --- 风格层 ----------------------------------------------------------------
script_dir <- local({
  a <- commandArgs(trailingOnly = FALSE)
  f <- sub("^--file=", "", a[grep("^--file=", a)])
  if (length(f)) dirname(normalizePath(f[1])) else getwd()
})
# 向上找 figure-style/style/ggplot2_theme.R：脚本无论在 pca_climate_zone/ 还是
# figures_repo/pca_climate_zone/ 下都能定位到风格层
find_style <- function(start) {
  env <- Sys.getenv("FIGURE_STYLE_DIR")
  if (nzchar(env)) {
    f <- file.path(env, "style", "ggplot2_theme.R")
    if (file.exists(f)) return(normalizePath(f))
    stop("FIGURE_STYLE_DIR=", env, " 下没有 style/ggplot2_theme.R", call. = FALSE)
  }
  d <- normalizePath(start, mustWork = FALSE)
  for (i in seq_len(8)) {
    f <- file.path(d, "figure-style", "style", "ggplot2_theme.R")
    if (file.exists(f)) return(normalizePath(f))
    f2 <- file.path(d, "style", "ggplot2_theme.R")
    if (file.exists(f2)) return(normalizePath(f2))
    if (identical(dirname(d), d)) break
    d <- dirname(d)
  }
  stop("找不到 figure-style/style/ggplot2_theme.R：把 figure-style/ 放在本仓库上一级，\n",
       "或设 FIGURE_STYLE_DIR 指向它（含 style/ 子目录）", call. = FALSE)
}
source(find_style(script_dir))

# --- 六大气候区：图例顺序 + 颜色来源 + 形状 --------------------------------
# 颜色不写 hex，只写"从调色板的哪一格取"：categorical = 分类色循环的第 n 格，
# accent = 强调色。六区名与形状对应原论文 Figure 2B 的图例（pch 语义一致）。
ZONE_ORDER <- c("North", "Middle", "Northwest", "Southeast", "Southwest", "Xizang")
# 色位按 chromatic_nc 的语义挑：蓝=North、绿=Middle、红=Northwest、紫=Southeast、
# 青绿=Southwest、琥珀=Xizang（与原图 蓝/绿/红/紫/青/珊瑚 的色相家族一致）。
ZONE_SPEC <- list(
  North     = list(colour = c("categorical", 1), shape = 17),      # 实心上三角
  Middle    = list(colour = c("categorical", 3), shape = 15),      # 实心方
  Northwest = list(colour = c("accent", "primary"), shape = 7),    # 方框加叉
  Southeast = list(colour = c("accent", "secondary"), shape = 9),  # 菱形加十
  Southwest = list(colour = c("categorical", 6), shape = 16),      # 实心圆
  Xizang    = list(colour = c("categorical", 5), shape = 6)        # 空心下三角
)

resolve_colour <- function(spec, palette) {
  if (spec[1] == "categorical") {
    fs_colors(palette)[as.integer(spec[2])]
  } else {
    unlist(fs_palette(palette)$accent[[spec[2]]])
  }
}

# --- 参数 ------------------------------------------------------------------
parse_args <- function(a) {
  out <- list(scores = NULL, variance = NULL, out = NULL, palette = NULL,
              tag = "", type_scale = 1.85, point_size = NULL,
              preset = NULL, width_mm = NULL, height_mm = NULL, legend_rows = 2)
  i <- 1
  while (i <= length(a)) {
    if (!grepl("^--", a[i])) { i <- i + 1; next }
    k <- gsub("-", "_", sub("^--", "", a[i]))
    v <- if (i < length(a)) a[i + 1] else ""
    out[[k]] <- if (k %in% c("type_scale", "width_mm", "height_mm", "point_size",
                             "legend_rows")) as.numeric(v) else v
    i <- i + 2
  }
  for (k in c("point_size", "width_mm", "height_mm")) {
    if (!is.null(out[[k]]) && length(out[[k]]) && is.na(out[[k]])) out[[k]] <- NULL
  }
  out
}
opt <- parse_args(commandArgs(trailingOnly = TRUE))
palette <- .fs_or(opt$palette, NULL)

dat <- read.delim(opt$scores, check.names = FALSE, stringsAsFactors = FALSE)
var <- read.delim(opt$variance, check.names = FALSE, stringsAsFactors = FALSE)
pct <- function(pc) {
  v <- var$variance_explained[var$PC == pc]
  if (!length(v)) stop("variance 表中缺少 ", pc, call. = FALSE)
  sprintf("%.2f", if (v[1] <= 1) v[1] * 100 else v[1])
}

dat$zone <- factor(dat$zone, levels = ZONE_ORDER)
dat <- dat[!is.na(dat$zone), ]
used <- levels(droplevels(dat$zone))
if (!length(used)) stop("没有可画的数据", call. = FALSE)
message(sprintf("[i] %d 个体 · %d 品种 · %d/%d 气候区：%s", nrow(dat),
                length(unique(dat$breed)), length(used), length(ZONE_ORDER),
                paste(used, collapse = ", ")))

# 六区固定映射：缺区不会"借用"别区的颜色
zone_cols <- vapply(ZONE_SPEC[ZONE_ORDER], function(x) resolve_colour(x$colour, palette),
                    character(1))
zone_shapes <- vapply(ZONE_SPEC[ZONE_ORDER], function(x) as.integer(x$shape), integer(1))

# --- 版式参数：全部由 theme.json 派生 --------------------------------------
th <- fs_theme(); pt <- th$typography$pt
ts <- opt$type_scale
ink <- fs_ink("ink")
pt_mm <- th$marks$point_diameter_mm * ts * 0.95
if (!is.null(opt$point_size)) pt_mm <- opt$point_size
stroke_mm <- pt2mm(th$marks$marker_edge_pt) * 1.1   # 实心符号描边
stroke_open <- stroke_mm * 2.2                       # 线型符号加粗

# 实心符号与线型符号分两层画：线型符号（7/9/6）只有描边，需要更粗的 stroke 才不
# 会在小尺寸 + 浅色下"糊掉"；两层共用同一套 colour/shape 标度，图例自动合并。
OPEN_SHAPES <- c(0:14, 32:127)
open_zones  <- ZONE_ORDER[vapply(ZONE_SPEC[ZONE_ORDER],
                                 function(x) as.integer(x$shape) %in% OPEN_SHAPES,
                                 logical(1))]
dat_filled <- dat[!as.character(dat$zone) %in% open_zones, , drop = FALSE]
dat_open   <- dat[as.character(dat$zone) %in% open_zones, , drop = FALSE]

p <- ggplot(dat, aes(PC1, PC2, colour = zone, shape = zone)) +
  geom_point(data = dat_filled, size = pt_mm, stroke = stroke_mm) +
  geom_point(data = dat_open, size = pt_mm, stroke = stroke_open) +
  scale_colour_manual(values = zone_cols, drop = TRUE,
                      guide = guide_legend(nrow = opt$legend_rows, byrow = TRUE,
                                           override.aes = list(size = pt_mm * 1.15,
                                                               stroke = stroke_open))) +
  scale_shape_manual(values = zone_shapes, drop = TRUE,
                     guide = guide_legend(nrow = opt$legend_rows, byrow = TRUE,
                                          override.aes = list(size = pt_mm * 1.15,
                                                              stroke = stroke_open))) +
  labs(x = sprintf("PC1 (%s%%)", pct("PC1")),
       y = sprintf("PC2 (%s%%)", pct("PC2")),
       colour = "Climate zone", shape = "Climate zone",
       tag = if (nzchar(opt$tag)) opt$tag else NULL) +
  theme_fs(legend = "default") +
  theme(
    # OVERRIDE 1：字号放大 = theme.json 值 × type_scale（论文/答辩版式）
    axis.text         = element_text(size = pt$tick * ts, colour = ink, face = "bold"),
    axis.title        = element_text(size = pt$axis * ts, colour = ink, face = "bold"),
    legend.text       = element_text(size = pt$legend * ts, colour = ink, face = "bold"),
    legend.title      = element_text(size = pt$legend * ts, colour = ink, face = "bold"),
    # OVERRIDE 2：面板字母（单面板一般不画；复刻原图时才用 --tag）
    plot.tag          = element_text(size = pt$title * ts * 1.15, colour = ink,
                                     face = "bold", hjust = 0, vjust = 1),
    plot.tag.position = c(0.01, 0.99),
    # OVERRIDE 3：轴线/刻度随放大字号一并加粗
    axis.line         = element_line(colour = ink, linewidth = pt2mm(th$lines$spine_pt) * 1.9),
    axis.ticks        = element_line(colour = ink, linewidth = pt2mm(th$lines$tick_width_pt) * 1.6),
    axis.ticks.length = grid::unit(pt2mm(th$lines$tick_length_pt) * 1.5, "mm"),
    # OVERRIDE 4：图例在面板上方，标题居左、条目横排（原图布局）
    legend.position       = "top",
    legend.direction      = "horizontal",
    legend.title.position = "left",
    legend.key.size       = grid::unit(0.55 * ts, "lines"),
    legend.spacing.x      = grid::unit(1.1 * ts, "mm"),
    legend.box.margin     = margin(t = 0.3 * ts, b = 1.0 * ts),
    plot.margin           = margin(1.4 * ts, 1.4 * ts, 1.1 * ts, 1.1 * ts, "mm")
  )

save_fs(p, opt$out, preset = opt$preset,
        width_mm = opt$width_mm, height_mm = opt$height_mm)
message("[done] -> ", paste0(opt$out, c(".pdf", ".png"), collapse = " / "))
