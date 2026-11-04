# style/ggplot2_theme.R -------------------------------------------------------
# 本仓库在 R / ggplot2 下的风格入口。
#
# 用法（在仓库根目录）：
#   source("style/ggplot2_theme.R")
#   p <- ggplot(df, aes(x, y, colour = group)) + geom_point() +
#        scale_colour_fs() + theme_fs()
#   save_fs(p, "outputs/fig1")           # 同时写 fig1.pdf + fig1.png(600dpi)
#
# 所有常量来自 style/theme.json 与 style/palettes.json，勿在此处硬编码。

# --- 定位仓库根目录（从被 source 的文件位置向上找 style/palettes.json） ----
.figure_style_root <- local({
  ofile <- tryCatch(normalizePath(sys.frame(1)$ofile), error = function(e) NA_character_)
  start <- if (!is.na(ofile) && nzchar(ofile)) dirname(ofile) else getwd()
  d <- normalizePath(start, mustWork = FALSE)
  for (i in seq_len(8)) {
    if (file.exists(file.path(d, "style", "palettes.json"))) {
      return(d)
    }
    parent <- dirname(d)
    if (identical(parent, d)) break
    d <- parent
  }
  getwd()
})

.fs_or <- function(x, y) if (is.null(x)) y else x

.fs_read <- function(file) {
  if (!requireNamespace("jsonlite", quietly = TRUE)) {
    stop("需要 jsonlite 读取风格配置：install.packages('jsonlite')", call. = FALSE)
  }
  jsonlite::fromJSON(file, simplifyVector = FALSE)
}

.FS_THEME <- .fs_read(file.path(.figure_style_root, "style", "theme.json"))
.FS_PALETTES <- .fs_read(file.path(.figure_style_root, "style", "palettes.json"))

# --- 基础访问器 -------------------------------------------------------------
fs_theme <- function() .FS_THEME

fs_palette <- function(name = NULL) {
  key <- .fs_or(name, .FS_PALETTES$default)
  p <- .FS_PALETTES$palettes[[key]]
  if (is.null(p)) {
    stop("未知调色板: ", key, "；可选: ",
         paste(names(.FS_PALETTES$palettes), collapse = ", "), call. = FALSE)
  }
  p
}

#' 分类色（六色循环）
fs_colors <- function(name = NULL) unlist(fs_palette(name)$categorical, use.names = FALSE)

#' 强调色：primary / secondary / tertiary
fs_accents <- function(name = NULL) unlist(fs_palette(name)$accent, use.names = FALSE)

#' 字体族解析
#'
#' macOS 的 cairo 设备不认 "Arial"（fontconfig 里没有），会直接报
#' `invalid font type`；Helvetica 与 Arial 同度量，且是 theme.json 字体链的第二顺位，
#' 因此 R 侧默认用 Helvetica。装了 ragg/systemfonts 或想强制 Arial 时：
#'   options(figure_style.family = "Arial")
fs_family <- function() {
  .fs_or(getOption("figure_style.family"), "Helvetica")
}

#' 骨架色：ink / threshold / hairline / emphasis_outline
fs_ink <- function(key = "ink") {
  v <- .FS_THEME$colors[[key]]
  if (is.null(v)) stop("未知骨架色: ", key, call. = FALSE)
  v
}

#' pt -> mm（ggplot2 的 linewidth 单位是 mm）
pt2mm <- function(pt) pt * 25.4 / 72

# --- 主题 -------------------------------------------------------------------
.fs_legend_inside <- function() {
  if (utils::packageVersion("ggplot2") >= "3.5.0") {
    ggplot2::theme(
      legend.position = "inside",
      legend.position.inside = c(0.99, 0.99),
      legend.justification = c(1, 1)
    )
  } else {
    ggplot2::theme(
      legend.position = c(0.99, 0.99),
      legend.justification = c(1, 1)
    )
  }
}

#' 出版级 ggplot2 主题
#'
#' @param base_size 基准字号（pt），默认取 theme.json 的 axis 字号
#' @param base_family 字体族，默认 fs_family()（Helvetica；见该函数说明）
#' @param legend "inside"（默认，面板内右上）/ "none" / 其它交给 ggplot 默认
theme_fs <- function(base_size = NULL, base_family = NULL, legend = c("inside", "none", "default"), ...) {
  legend <- match.arg(legend)
  base_size <- .fs_or(base_size, .FS_THEME$typography$pt$axis)
  base_family <- .fs_or(base_family, fs_family())
  ink <- fs_ink("ink")
  soft <- fs_ink("threshold")
  pt <- .FS_THEME$typography$pt

  ggplot2::theme_classic(base_size = base_size, base_family = base_family) +
    ggplot2::theme(
      plot.background     = ggplot2::element_rect(fill = "white", colour = NA),
      panel.background    = ggplot2::element_rect(fill = "white", colour = NA),
      panel.grid          = ggplot2::element_blank(),
      panel.border        = ggplot2::element_blank(),
      axis.line           = ggplot2::element_line(colour = ink, linewidth = pt2mm(.FS_THEME$lines$spine_pt)),
      axis.ticks          = ggplot2::element_line(colour = ink, linewidth = pt2mm(.FS_THEME$lines$tick_width_pt)),
      axis.ticks.length   = grid::unit(pt2mm(.FS_THEME$lines$tick_length_pt), "mm"),
      axis.text           = ggplot2::element_text(colour = ink, size = pt$tick, family = base_family),
      axis.title          = ggplot2::element_text(colour = ink, size = pt$axis, family = base_family),
      plot.title          = ggplot2::element_text(colour = ink, size = pt$title, family = base_family,
                                                  hjust = 0, face = "plain"),
      plot.subtitle       = ggplot2::element_text(colour = soft, size = pt$note, family = base_family, hjust = 0),
      plot.caption        = ggplot2::element_text(colour = soft, size = pt$note, family = base_family, hjust = 1),
      legend.text         = ggplot2::element_text(colour = ink, size = pt$legend, family = base_family),
      legend.title        = ggplot2::element_text(colour = ink, size = pt$legend, family = base_family),
      legend.background   = ggplot2::element_blank(),
      legend.key          = ggplot2::element_blank(),
      legend.key.size     = grid::unit(2.6, "mm"),
      strip.background    = ggplot2::element_blank(),
      strip.text          = ggplot2::element_text(colour = ink, size = pt$tick, family = base_family, hjust = 0),
      plot.margin         = ggplot2::margin(1, 1, 1, 1, "mm"),
      ...
    ) +
    switch(legend,
      inside  = .fs_legend_inside(),
      none    = ggplot2::theme(legend.position = "none"),
      default = ggplot2::theme()
    )
}

# --- 标度 -------------------------------------------------------------------
.fs_discrete <- function(aesthetics, palette, ...) {
  cols <- fs_colors(palette)
  ggplot2::discrete_scale(
    aesthetics = aesthetics,
    palette = function(n) {
      if (n > length(cols)) {
        stop("类别数 ", n, " 超过调色板的 ", length(cols),
             " 色上限：请改用分面（facet_wrap/facet_grid）而不是再加颜色。", call. = FALSE)
      }
      cols[seq_len(n)]
    },
    ...
  )
}

#' 分类颜色标度
scale_colour_fs <- function(palette = NULL, ...) .fs_discrete("colour", palette, ...)
#' 分类填充标度
scale_fill_fs <- function(palette = NULL, ...) .fs_discrete("fill", palette, ...)

#' 强调色标度（珊瑚 / 紫 / 琥珀），仅用于 ≤3 类的前景
scale_colour_fs_accent <- function(palette = NULL, ...) {
  ggplot2::scale_colour_manual(values = unname(fs_accents(palette)), ...)
}
scale_fill_fs_accent <- function(palette = NULL, ...) {
  ggplot2::scale_fill_manual(values = unname(fs_accents(palette)), ...)
}

# --- 导出 -------------------------------------------------------------------
# 设备选择：这台机器上 R 的 cairo 缺 X11 库（capabilities("cairo") 仍报 TRUE 但实际
# 加载失败），所以 PDF 一律用标准 pdf 设备 + 内置 Helvetica：不依赖 X11，文字保持矢量
# 可编辑。真要用 Arial 嵌入，就装 ragg/systemfonts 后自行 ggsave(device = cairo_pdf)。
.fs_pdf_device <- function(filename, width, height, bg = "white", ...) {
  grDevices::pdf(file = filename, width = width, height = height,
                 family = "Helvetica", useDingbats = FALSE, bg = bg, ...)
}

# PNG：有 ragg 就用 ragg（真 Arial + 写入 DPI 元数据），否则用系统 png 设备。
.fs_png_device <- function(filename, width, height, res = 600, bg = "white", ...) {
  if (requireNamespace("ragg", quietly = TRUE)) {
    ragg::agg_png(filename = filename, width = width, height = height, units = "in",
                  res = res, background = bg, ...)
  } else {
    grDevices::png(filename = filename, width = width, height = height, units = "in",
                   res = res, bg = bg, ...)
  }
}

#' 按规范导出：默认 PDF（矢量，文字可编辑）+ PNG 600 dpi
#'
#' @param stem 不含扩展名的路径，如 "outputs/fig1"
save_fs <- function(plot, stem, preset = NULL, formats = NULL, dpi = NULL,
                    width_mm = NULL, height_mm = NULL, ...) {
  preset <- .fs_or(preset, .FS_THEME$figure$default_preset)
  spec <- .FS_THEME$figure$presets[[preset]]
  if (is.null(spec)) {
    stop("未知画幅: ", preset, "；可选: ",
         paste(names(.FS_THEME$figure$presets), collapse = ", "), call. = FALSE)
  }
  w <- .fs_or(width_mm, spec$width)
  h <- .fs_or(height_mm, spec$height)
  dpi <- .fs_or(dpi, .FS_THEME$figure$dpi)
  formats <- .fs_or(formats, unlist(.FS_THEME$figure$formats))

  dir.create(dirname(stem), recursive = TRUE, showWarnings = FALSE)
  written <- character(0)
  for (fmt in formats) {
    path <- paste0(stem, ".", fmt)
    if (identical(fmt, "pdf")) {
      ggplot2::ggsave(path, plot, width = w, height = h, units = "mm", dpi = dpi,
                      device = .fs_pdf_device, ...)
    } else {
      ggplot2::ggsave(path, plot, width = w, height = h, units = "mm", dpi = dpi,
                      device = .fs_png_device, ...)
    }
    if (!file.exists(path)) {
      stop("导出失败，没有生成文件: ", path, call. = FALSE)
    }
    written <- c(written, path)
  }
  invisible(written)
}

#' 面板字母（小写加粗，左上角外侧）
#'
#' geom_text 的 size 单位是 mm，换算：pt = size * 72.27/25.4
panel_tag <- function(label, x = -0.02, y = 1.02, size = NULL) {
  pt <- .fs_or(size, .FS_THEME$typography$pt$axis)
  ggplot2::annotate(
    "text", x = x, y = y, label = label,
    hjust = 1, vjust = 0, fontface = "bold",
    size = pt / (72.27 / 25.4),
    colour = fs_ink("ink")
  )
}
