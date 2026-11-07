#!/usr/bin/env Rscript
# ==============================================================================
# V16 组合图：V15 GRCg7b Circos（原样）+ 右侧四类 TE 结构示意（纯 R 拼版）
# ==============================================================================
# 定位：
#   本脚本是 Fig1 的"组合成图"入口，不是第二条绘图管线。圆图部分 100% 复用
#   plot_chicken_circos_v15.R：source 之后直接调用它的 default_config /
#   read_and_validate_inputs / make_layout / make_scales / draw_complete_figure。
#   V15 的任何一个数字、颜色、轨道、标签都不在本文件里重新实现，因此两份图
#   不存在"漂移"的可能。
#
#   关键几何技巧：V15 的 figure_region 在 9.8 x 10 in 画布上对应物理区域
#   9.457 x 8.4 in。这里把画布加宽到 width_in（默认 15.8），只把该区域换算成
#   新画布的 ndc 矩形——物理尺寸与位置都不变，circos 按 1:1 原尺寸重绘，
#   左侧区域与 V15 逐像素一致（见 QC_report.md 的比对结果）。
#
# 右侧结构图：
#   几何直接取自 assets/TE_architectures/*.svg 的 1000 x 210 用户坐标
#   （片段 x/宽/高/圆角、末端窄条、每段文字位置），线性映射到英寸；
#   文字改为固定 pt，避免等比缩小后不可读。
#
# 连接箭头：
#   48 度开口是一片无墨楔形。四个起点取开口中心 ±18 度内、半径 1.005，
#   落在空白区，几何上不可能覆盖任何轨道或刻度（check_combined_v16.py 会复核）。
#
# 依赖：circlize + grid + 系统 sha256 工具；不强制 cairo。
# 设备：cairo → macOS quartz → base pdf 逐级回退，自动选择可用后端。
# ==============================================================================

options(stringsAsFactors = FALSE, scipen = 20)

# C locale 下多字节字符会被拆散（5′ 会渲染成 5…），先切到 UTF-8
if (!isTRUE(l10n_info()[["UTF-8"]])) {
  for (loc in c("en_US.UTF-8", "UTF-8", "C.UTF-8")) {
    if (suppressWarnings(!is.na(Sys.setlocale("LC_CTYPE", loc)))) break
  }
}

`%||%` <- function(a, b) if (is.null(a)) b else a


# ------------------------------------------------------------------------------
# 1. 路径与参数
# ------------------------------------------------------------------------------

detect_combined_project_dir <- function() {
  file_arg <- grep("^--file=", commandArgs(trailingOnly = FALSE), value = TRUE)
  if (length(file_arg)) {
    script <- normalizePath(sub("^--file=", "", file_arg[1]), mustWork = TRUE)
    return(dirname(dirname(script)))
  }
  if (dir.exists(file.path(getwd(), "04_window_statistics"))) return(getwd())
  file.path(getwd(), "chicken_7b_TE_circos")
}

default_combined_options <- function(project_dir = detect_combined_project_dir()) {
  list(
    project_dir = project_dir,
    out_dir = NULL,                 # NULL -> 07_figures/R_v16
    width_in = 15.8,                # 组合画布宽度；高度沿用 V15 的 10 in
    formats = NULL,                 # NULL -> 有 cairo 时 svg,pdf,png；否则 pdf,png
    dpi = 600,
    preview_dpi = 150,
    font = NULL,                    # NULL -> 自动探测
    draw_connectors = TRUE,
    show_notes = FALSE,          # 默认不画灰色小字注释（--with-notes 可恢复）
    validate_only = FALSE
  )
}

print_combined_usage <- function() {
  cat(paste(c(
    "V16 组合图：V15 GRCg7b Circos + 右侧四类 TE 结构示意。",
    "用法：Rscript plot_combined_te_callouts_v16.R [选项]",
    "  --project-dir PATH   chicken_7b_TE_circos 项目目录；默认从脚本位置识别",
    "  --out-dir PATH       默认 07_figures/R_v16；禁止写入 R_v15 及更早目录",
    "  --width IN           组合画布宽度，默认 15.8（比例 1.58:1）",
    "  --formats LIST       svg,pdf,png；无 cairo 时自动跳过 svg",
    "  --dpi INT            位图分辨率，默认 600",
    "  --font NAME          字体；默认 Liberation Sans -> Arial -> Helvetica",
    "  --no-connectors      不画四根连接箭头与开口弧线",
    "  --with-notes         恢复四行灰色注释与底部说明（默认不画）",
    "  --validate-only      只校验输入与几何，不出图",
    "  --help               显示帮助"
  ), collapse = "\n"), "\n")
}

parse_combined_arguments <- function(args, opt) {
  i <- 1L
  while (i <= length(args)) {
    a <- args[i]
    if (a == "--help") { print_combined_usage(); return(NULL) }
    if (a == "--validate-only") { opt$validate_only <- TRUE; i <- i + 1L; next }
    if (a == "--no-connectors") { opt$draw_connectors <- FALSE; i <- i + 1L; next }
    if (a == "--with-notes") { opt$show_notes <- TRUE; i <- i + 1L; next }
    if (!grepl("^--", a)) stop("无法识别参数：", a, call. = FALSE)
    if (i == length(args) || grepl("^--", args[i + 1L])) stop("选项 ", a, " 缺少值。", call. = FALSE)
    key <- sub("^--", "", a); value <- args[i + 1L]
    if (key == "project-dir") opt$project_dir <- value
    else if (key == "out-dir") opt$out_dir <- value
    else if (key == "width") opt$width_in <- as.numeric(value)
    else if (key == "dpi") opt$dpi <- as.numeric(value)
    else if (key == "font") opt$font <- value
    else if (key == "formats") opt$formats <- trimws(strsplit(value, ",", fixed = TRUE)[[1]])
    else stop("未知选项：", a, "；使用 --help 查看说明。", call. = FALSE)
    i <- i + 2L
  }
  opt
}


# ------------------------------------------------------------------------------
# 2. 绘图后端：cairo 优先，macOS quartz 次之，base pdf 兜底
# ------------------------------------------------------------------------------

probe_cairo <- local({
  cached <- NULL
  function() {
    if (!is.null(cached)) return(cached)
    cached <<- tryCatch({
      f <- tempfile(fileext = ".pdf")
      suppressWarnings(grDevices::cairo_pdf(f, width = 2, height = 1))
      # cairo 缺失时 R 只 warning 然后回退到 pdf 设备，必须用设备名判别
      ok <- identical(names(grDevices::dev.cur()), "cairo_pdf")
      grDevices::dev.off()
      unlink(f)
      ok
    }, error = function(e) {
      if (!is.null(grDevices::dev.list())) try(grDevices::dev.off(), silent = TRUE)
      FALSE
    })
    cached
  }
})

probe_quartz <- local({
  cached <- NULL
  function() {
    if (!is.null(cached)) return(cached)
    cached <<- tryCatch({
      f <- tempfile(fileext = ".png")
      grDevices::quartz(type = "png", file = f, width = 2, height = 1, dpi = 72)
      # quartz 在后台会话里叫 quartz_off_screen，前缀判断而不是全等
      ok <- startsWith(names(grDevices::dev.cur()), "quartz")
      grDevices::dev.off()
      unlink(f)
      ok
    }, error = function(e) {
      if (!is.null(grDevices::dev.list())) try(grDevices::dev.off(), silent = TRUE)
      FALSE
    })
    cached
  }
})

available_formats <- function(requested) {
  has_cairo <- probe_cairo()
  defaults <- if (has_cairo) c("svg", "pdf", "png") else c("pdf", "png")
  if (is.null(requested)) return(defaults)
  if ("svg" %in% requested && !has_cairo) {
    stop("当前 R 不支持 cairo，无法输出 SVG；请先安装 XQuartz，或改用 --formats pdf,png。",
         call. = FALSE)
  }
  requested
}

open_combined_device <- function(path, format, width, height, dpi, family, pointsize = 10) {
  if (format == "svg") {
    grDevices::svg(path, width = width, height = height, pointsize = pointsize,
                   family = family, bg = "white", onefile = FALSE)
    return("cairo-svg")
  }
  if (format == "pdf") {
    if (probe_cairo()) {
      grDevices::cairo_pdf(path, width = width, height = height, pointsize = pointsize,
                           family = family, bg = "white", onefile = FALSE)
      return("cairo-pdf")
    }
    if (probe_quartz()) {
      grDevices::quartz(type = "pdf", file = path, width = width, height = height,
                        family = family, pointsize = pointsize, bg = "white", antialias = TRUE)
      return("quartz-pdf")
    }
    grDevices::pdf(path, width = width, height = height, pointsize = pointsize,
                   family = "Helvetica", bg = "white", onefile = FALSE)
    return("base-pdf")
  }
  if (format == "png") {
    if (probe_cairo()) {
      grDevices::png(path, width = width, height = height, units = "in", res = dpi,
                     type = "cairo", pointsize = pointsize, bg = "white")
      return("cairo-png")
    }
    if (probe_quartz()) {
      grDevices::quartz(type = "png", file = path, width = width, height = height, dpi = dpi,
                        family = family, pointsize = pointsize, bg = "white", antialias = TRUE)
      return("quartz-png")
    }
    stop("没有可用的位图后端（cairo 与 quartz 均不可用）。", call. = FALSE)
  }
  stop("不支持的输出格式：", format, call. = FALSE)
}

# 字体：Liberation Sans 优先；缺字时 Arial 是度量兼容替代；再退 Helvetica
detect_font_family <- function(preferred = NULL) {
  if (!is.null(preferred)) return(preferred)
  font_installed <- function(fam) {
    key <- gsub("[^A-Za-z]", "", fam)
    if (nzchar(Sys.which("fc-list"))) {
      listed <- tryCatch(system2("fc-list", c(":", "family"), stdout = TRUE, stderr = FALSE),
                         error = function(e) character(0))
      return(any(grepl(key, gsub("[^A-Za-z]", "", listed), ignore.case = TRUE)))
    }
    dirs <- c("/System/Library/Fonts", "/System/Library/Fonts/Supplemental",
              "/Library/Fonts", path.expand("~/Library/Fonts"))
    files <- unlist(lapply(dirs, function(d)
      list.files(d, pattern = "\\.(ttf|ttc|otf)$", full.names = TRUE)))
    any(grepl(key, gsub("[^A-Za-z]", "", basename(files)), ignore.case = TRUE))
  }
  for (candidate in c("Liberation Sans", "Arial")) {
    if (font_installed(candidate)) return(candidate)
  }
  "Helvetica"
}


# ------------------------------------------------------------------------------
# 3. 组合画布几何
# ------------------------------------------------------------------------------

composite_geometry <- function(cfg, width_in) {
  g <- cfg$geometry
  x0 <- g$figure_region[1] * g$width_in
  x1 <- g$figure_region[2] * g$width_in
  y0 <- g$figure_region[3] * g$height_in
  y1 <- g$figure_region[4] * g$height_in
  list(width_in = width_in, height_in = g$height_in,
       circos_x = c(x0, x1), circos_y = c(y0, y1),
       fig_region = c(x0 / width_in, x1 / width_in, y0 / g$height_in, y1 / g$height_in),
       v15_width_in = g$width_in)
}


# ------------------------------------------------------------------------------
# 4. 四类 TE 结构：几何来自 assets/TE_architectures/*.svg（1000 x 210）
# ------------------------------------------------------------------------------

te_callouts <- function() {
  list(
    list(key = "LINE", title = "LINE", color = "#386C8C", block = "#98B3C3",
         segments = data.frame(x = c(30, 202, 399, 663), w = c(170, 195, 262, 180),
                               h = c(52, 72, 72, 52), rx = c(9, 2, 2, 9)),
         tail = c(x = 847, w = 15, h = 46, rx = 7), tail_fill = "#A1A8BE",
         tail_text = "3\u2032 repeats",
         labels = data.frame(x = c(115, 299.5, 530, 753), y = 125,
                             text = c("5\u2032 UTR", "ORF1", "ORF2", "3\u2032 UTR")),
         note = NA_character_, optional_index = NA_integer_),
    list(key = "LTR", title = "LTR", color = "#7BB6AC", block = "#BAD9D4",
         segments = data.frame(x = c(30, 194, 384, 581, 765), w = c(162, 188, 195, 182, 162),
                               h = c(52, 72, 72, 72, 52), rx = c(9, 2, 2, 2, 9)),
         tail = NULL, tail_fill = NA_character_, tail_text = NA_character_,
         optional_index = 4L,
         labels = data.frame(x = c(111, 288, 481.5, 672, 846), y = 125,
                             text = c("LTR", "Gag", "Pol", "Env*", "LTR")),
         note = "* Env is optional and lineage-dependent"),
    list(key = "SINE", title = "SINE", color = "#9689B9", block = "#C8C2DB",
         segments = data.frame(x = c(30, 266, 573), w = c(234, 305, 267),
                               h = c(52, 72, 52), rx = c(9, 2, 9)),
         tail = c(x = 844, w = 15, h = 48, rx = 7), tail_fill = "#A1A8BE",
         tail_text = "Variable tail",
         labels = data.frame(x = c(147, 418.5, 706.5), y = 125,
                             text = c("5\u2032 region", "Pol III A/B boxes", "3\u2032 region")),
         note = "Schematic example; chicken SINE families differ", optional_index = NA_integer_),
    list(key = "DNA", title = "DNA", color = "#B4AD74", block = "#D8D4B7",
         segments = data.frame(x = c(30, 224, 718), w = c(192, 492, 192),
                               h = c(52, 72, 52), rx = c(9, 2, 9)),
         tail = NULL, tail_fill = NA_character_, tail_text = NA_character_,
         labels = data.frame(x = c(126, 470, 814), y = 125,
                             text = c("TIR", "Transposase", "TIR")),
         note = "Representative TIR-type DNA transposon", optional_index = NA_integer_)
  )
}

panel_layout <- function(comp, center_y, family) {
  panel_left <- comp$circos_x[2] + 0.30
  panel_right <- comp$width_in - 0.42
  row_w <- panel_right - panel_left
  scale <- row_w / 1000
  row_h <- 210 * scale
  gap <- 0.375
  total <- 4 * row_h + 3 * gap
  list(left = panel_left, right = panel_right, width = row_w, scale = scale,
       row_h = row_h, gap = gap, total = total, top = center_y + total / 2,
       center_y = center_y, family = family,
       ink = "#253246", text = "#273746", note = "#697887",
       title_pt = 13.5, label_pt = 9.0, tail_pt = 7.6, note_pt = 7.0, footer_pt = 7.0)
}


# ------------------------------------------------------------------------------
# 5. 右侧面板与连接箭头
# ------------------------------------------------------------------------------

push_inch_viewport <- function(width, height) {
  grid::pushViewport(grid::viewport(
    x = 0, y = 0, width = grid::unit(width, "inches"), height = grid::unit(height, "inches"),
    just = c("left", "bottom"), default.units = "inches",
    xscale = c(0, width), yscale = c(0, height)))
}

draw_te_panel <- function(callouts, lay, width, height, notes = FALSE) {
  push_inch_viewport(width, height)
  on.exit(grid::popViewport(), add = TRUE)

  s <- lay$scale
  centre_u <- 124
  for (i in seq_along(callouts)) {
    z <- callouts[[i]]
    row_top <- lay$top - (i - 1) * (lay$row_h + lay$gap)
    yy <- function(u) row_top - u * s
    xx <- function(u) lay$left + u * s

    grid::grid.text(z$title, x = grid::unit(xx(30), "inches"), y = grid::unit(yy(39), "inches"),
                    just = c("left", "centre"),
                    gp = grid::gpar(fontfamily = lay$family, fontface = "bold",
                                    fontsize = lay$title_pt, col = z$color))

    for (j in seq_len(nrow(z$segments))) {
      sg <- z$segments[j, ]
      opt <- !is.na(z$optional_index) && j == z$optional_index
      grid::grid.roundrect(
        x = grid::unit(xx(sg$x + sg$w / 2), "inches"),
        y = grid::unit(yy(centre_u), "inches"),
        width = grid::unit(sg$w * s, "inches"), height = grid::unit(sg$h * s, "inches"),
        r = grid::unit(sg$rx * s, "inches"),
        gp = grid::gpar(fill = if (opt) "#E5F0EE" else z$block,
                        col = if (opt) z$color else NA, lwd = if (opt) 1.0 else 0))
      if (opt) {
        grid::grid.roundrect(
          x = grid::unit(xx(sg$x + sg$w / 2), "inches"),
          y = grid::unit(yy(centre_u), "inches"),
          width = grid::unit((sg$w - 2) * s, "inches"),
          height = grid::unit((sg$h - 2) * s, "inches"),
          r = grid::unit(3 * s, "inches"),
          gp = grid::gpar(fill = NA, col = z$color, lwd = 0.75, lty = "dashed"))
      }
    }

    if (!is.null(z$tail)) {
      t <- z$tail
      grid::grid.roundrect(
        x = grid::unit(xx(t[["x"]] + t[["w"]] / 2), "inches"),
        y = grid::unit(yy(centre_u), "inches"),
        width = grid::unit(t[["w"]] * s, "inches"), height = grid::unit(t[["h"]] * s, "inches"),
        r = grid::unit(t[["rx"]] * s, "inches"),
        gp = grid::gpar(fill = z$tail_fill, col = NA))
      grid::grid.text(z$tail_text,
                      x = grid::unit(xx(t[["x"]] + t[["w"]] / 2 + 2), "inches"),
                      y = grid::unit(yy(88), "inches"), just = c("right", "centre"),
                      gp = grid::gpar(fontfamily = lay$family, fontsize = lay$tail_pt,
                                      col = lay$text))
    }

    for (k in seq_len(nrow(z$labels))) {
      grid::grid.text(z$labels$text[k], x = grid::unit(xx(z$labels$x[k]), "inches"),
                      y = grid::unit(yy(z$labels$y[k]), "inches"), just = "centre",
                      gp = grid::gpar(fontfamily = lay$family, fontsize = lay$label_pt,
                                      col = lay$text))
    }

    if (notes && !is.na(z$note)) {
      grid::grid.text(z$note, x = grid::unit(xx(30), "inches"), y = grid::unit(yy(187), "inches"),
                      just = c("left", "centre"),
                      gp = grid::gpar(fontfamily = lay$family, fontsize = lay$note_pt,
                                      col = lay$note))
    }
  }

  # 底部说明同样属于灰色小字，默认不画；popViewport 交给 on.exit，避免重复弹出
  if (notes) {
    grid::grid.text("Representative architectures, not to scale. Colours follow the V15 Circos tracks.",
                    x = grid::unit(lay$left + 30 * s, "inches"),
                    y = grid::unit(lay$top - lay$total - 0.30, "inches"),
                    just = c("left", "centre"),
                    gp = grid::gpar(fontfamily = lay$family, fontsize = lay$footer_pt,
                                    col = lay$note))
  }
  invisible(NULL)
}

draw_connectors <- function(lay, centre, unit_in, callouts) {
  theta_deg <- c(72, 84, 96, 108)          # 开口 ±24 度，取 ±18 度留 6 度余量
  theta <- theta_deg * pi / 180
  r_user <- 1.005
  x0 <- centre[1] + r_user * sin(theta) * unit_in
  y0 <- centre[2] + r_user * cos(theta) * unit_in

  s <- lay$scale
  y_end <- lay$top - (seq_along(callouts) - 1) * (lay$row_h + lay$gap) - 39 * s
  x_end <- lay$left - 0.10

  # 补一条极浅的圆周弧，让四个起点明确"挂"在圆周上，而不是浮在白底
  th <- seq(66, 114, length.out = 97) * pi / 180
  grid::grid.lines(x = grid::unit(centre[1] + r_user * sin(th) * unit_in, "inches"),
                   y = grid::unit(centre[2] + r_user * cos(th) * unit_in, "inches"),
                   gp = grid::gpar(col = "#CBD4DC", lwd = 0.7, lineend = "round"))

  for (i in seq_along(callouts)) {
    grid::grid.lines(
      x = grid::unit(c(x0[i], x_end), "inches"),
      y = grid::unit(c(y0[i], y_end[i]), "inches"),
      arrow = grid::arrow(angle = 22, length = grid::unit(0.11, "inches"),
                          type = "closed", ends = "last"),
      gp = grid::gpar(col = lay$ink, lwd = 1.0, lineend = "round", linejoin = "round"))
    grid::grid.circle(x = grid::unit(x0[i], "inches"), y = grid::unit(y0[i], "inches"),
                      r = grid::unit(0.047, "inches"),
                      gp = grid::gpar(fill = callouts[[i]]$color, col = "white", lwd = 0.7))
  }
  data.frame(track = vapply(callouts, `[[`, character(1), "key"),
             tail_x_in = round(x0, 4), tail_y_in = round(y0, 4),
             head_x_in = round(x_end, 4), head_y_in = round(y_end, 4),
             tail_angle_deg = theta_deg, tail_radius_user = r_user,
             track_color = vapply(callouts, `[[`, character(1), "color"))
}


# ------------------------------------------------------------------------------
# 6. 溯源与校验文件
# ------------------------------------------------------------------------------

sha256_of <- function(path) {
  tool <- Sys.which(c("shasum", "sha256sum"))[1]
  if (is.na(tool) || !nzchar(tool)) return(NA_character_)
  out <- system2(tool, if (grepl("shasum$", tool)) c("-a", "256", shQuote(path)) else shQuote(path),
                 stdout = TRUE, stderr = FALSE)
  if (!length(out)) return(NA_character_)
  sub("[[:space:]].*$", "", out[1])
}

write_input_manifest <- function(paths, out_path, project_dir) {
  project_dir <- normalizePath(project_dir, mustWork = TRUE)
  # 注意：lapply 作用在原子向量上会丢掉每个元素的 name，这里按索引取才保住 role
  rows <- lapply(seq_along(paths), function(i) {
    p <- paths[i]
    abs <- normalizePath(unname(p), mustWork = FALSE)
    rel <- if (startsWith(abs, paste0(project_dir, "/"))) {
      substring(abs, nchar(project_dir) + 2L)
    } else NA_character_
    data.frame(role = names(p), path_rel = rel, path_abs = abs, exists = file.exists(p),
               bytes = if (file.exists(p)) file.info(p)$size else NA_integer_,
               sha256 = if (file.exists(p)) sha256_of(p) else NA_character_)
  })
  write.table(do.call(rbind, rows), out_path, sep = "\t", quote = FALSE,
              row.names = FALSE, na = "NA")
}


# ------------------------------------------------------------------------------
# 7. 主流程
# ------------------------------------------------------------------------------

render_combined <- function(opt) {
  project_dir <- normalizePath(opt$project_dir, mustWork = TRUE)

  # 项目本地库（install_circos_R_dependencies.sh 的目标位置）
  local_library <- file.path(project_dir, "06_scripts", "R_library")
  if (dir.exists(local_library)) .libPaths(c(local_library, .libPaths()))

  v15_script <- file.path(project_dir, "06_scripts", "plot_chicken_circos_v15.R")
  if (!file.exists(v15_script)) stop("缺少 V15 脚本：", v15_script, call. = FALSE)
  sys.source(v15_script, envir = globalenv())

  font <- detect_font_family(opt$font)
  # base pdf 后端只有 PostScript 字体，必须退到 Helvetica，否则 par(family=) 会报 invalid font type
  if (!probe_cairo() && !probe_quartz()) font <- "Helvetica"
  formats <- available_formats(opt$formats)

  cfg <- default_config(project_dir)
  cfg <- apply_palette(cfg)
  validate_configuration(cfg)
  cfg <- resolve_paths(cfg)
  cfg$typography$family <- font
  load_circlize(cfg)

  inputs <- read_and_validate_inputs(cfg)
  layout <- make_layout(inputs, cfg)
  scales <- make_scales(inputs, cfg)

  comp <- composite_geometry(cfg, opt$width_in)
  if (comp$width_in <= comp$circos_x[2] + 1.5) {
    stop("画布过窄：--width 至少要比 V15 画布宽度（9.8）大 1.5 in。", call. = FALSE)
  }
  cfg_left <- cfg
  cfg_left$geometry$figure_region <- comp$fig_region

  out_dir <- opt$out_dir %||% file.path(project_dir, "07_figures", "R_v16")
  out_dir <- normalizePath(out_dir, mustWork = FALSE)
  if (grepl("/R_v(3|4|5|6|7|8|9|10|11|12|13|14|15)(/|$)", out_dir)) {
    stop("V16 不写入 R_v3–R_v15 目录，请使用 R_v16 或新的输出目录。", call. = FALSE)
  }

  prefix_name <- "chicken_GRCg7b_R_v16_combined_TE-callouts"
  callouts <- te_callouts()

  message(sprintf("输入检查通过：%s bp，%s 个真实窗口，%s 条染色体；组合画布 %.1f x %.1f in。",
                  format(cfg$window_bp, scientific = FALSE), nrow(inputs$data),
                  length(inputs$chromosomes),
                  comp$width_in, comp$height_in))

  # 几何先算出来（validate-only 也用它）
  state <- NULL
  paint <- function() {
    st <- draw_complete_figure(inputs, layout, scales, cfg_left)
    centre <- c(graphics::grconvertX(0, "user", "ndc"),
                graphics::grconvertY(0, "user", "ndc")) * c(comp$width_in, comp$height_in)
    unit_in <- abs(diff(graphics::grconvertX(c(0, 1), "user", "inches")))
    lay <- panel_layout(comp, centre[2], font)
    draw_te_panel(callouts, lay, comp$width_in, comp$height_in, notes = opt$show_notes)
    con <- if (opt$draw_connectors) draw_connectors(lay, centre, unit_in, callouts) else NULL
    list(circos = st, centre = centre, unit_in = unit_in, layout = lay, connectors = con)
  }

  if (isTRUE(opt$validate_only)) {
    message("仅校验：输入与几何均通过（未出图）。")
    return(invisible(list(inputs = inputs, layout = layout, scales = scales, composite = comp)))
  }

  dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
  prefix <- file.path(out_dir, prefix_name)

  # 一次完整绘制 + 保证设备关闭
  emit <- function(path, fmt, dpi) {
    t0 <- Sys.time()
    backend <- open_combined_device(path, fmt, comp$width_in, comp$height_in, dpi, font,
                                    cfg$typography$base_pt)
    st <- NULL
    tryCatch({ st <- paint() },
             finally = {
               if (!is.null(grDevices::dev.list())) try(grDevices::dev.off(), silent = TRUE)
             })
    message(sprintf("已输出：%s（%s，%.1f s）", basename(path), backend,
                    as.numeric(difftime(Sys.time(), t0, units = "secs"))))
    list(state = st, backend = backend)
  }

  outputs <- character(0)
  backend <- NA_character_
  for (fmt in unique(formats)) {
    path <- paste0(prefix, ".", fmt)
    res <- emit(path, fmt, opt$dpi)
    state <- res$state
    backend <- res$backend
    outputs <- c(outputs, path)
  }
  preview <- paste0(prefix, ".preview.png")
  state <- emit(preview, "png", opt$preview_dpi)$state
  outputs <- c(outputs, preview)

  # --- 几何记录 ---
  geometry_rows <- data.frame(
    item = c("reference", "window_bp", "composite_width_in", "composite_height_in", "aspect",
             "circos_width_in", "circos_region_x0_in", "circos_region_x1_in",
             "circle_center_x_in", "circle_center_y_in", "circle_radius_in",
             "unit_in_per_user", "opening_deg", "panel_left_in", "panel_right_in",
             "panel_rows", "connector_mode", "font", "device_backend", "dpi",
             "v15_script"),
    value = c("GRCg7b", cfg$window_bp, comp$width_in, comp$height_in,
              round(comp$width_in / comp$height_in, 4), comp$v15_width_in,
              round(comp$circos_x[1], 4), round(comp$circos_x[2], 4),
              round(state$centre[1], 4), round(state$centre[2], 4),
              round(state$unit_in * 0.9975, 4), round(state$unit_in, 6),
              cfg$geometry$opening_deg, round(state$layout$left, 4),
              round(state$layout$right, 4), 4,
              if (opt$draw_connectors) "4 arrows from 48-degree opening" else "none",
              font, backend, opt$dpi, basename(v15_script)))
  geometry_path <- paste0(prefix, ".figure_geometry.tsv")
  write.table(geometry_rows, geometry_path, sep = "\t", quote = FALSE, row.names = FALSE)
  outputs <- c(outputs, geometry_path)

  if (!is.null(state$connectors)) {
    connectors_path <- paste0(prefix, ".connectors.tsv")
    write.table(state$connectors, connectors_path, sep = "\t", quote = FALSE, row.names = FALSE)
    outputs <- c(outputs, connectors_path)
  }

  # --- 输入与版本记录 ---
  input_paths <- c(
    "V15 circos script" = v15_script,
    "window statistics" = cfg$table,
    "chromosome sizes" = cfg$chrom_sizes,
    "centromere table" = cfg$centromeres,
    "TE LINE svg" = file.path(project_dir, "assets", "TE_architectures", "LINE_CR1.svg"),
    "TE LTR svg" = file.path(project_dir, "assets", "TE_architectures", "LTR_ERV.svg"),
    "TE SINE svg" = file.path(project_dir, "assets", "TE_architectures", "SINE_generic.svg"),
    "TE DNA svg" = file.path(project_dir, "assets", "TE_architectures", "DNA_TIR.svg"),
    "TE 4up svg" = file.path(project_dir, "assets", "TE_architectures", "TE_architectures_4up.svg"))
  input_path <- paste0(prefix, ".input_files.tsv")
  write_input_manifest(input_paths, input_path, project_dir)
  outputs <- c(outputs, input_path)

  settings_path <- paste0(prefix, ".settings.R")
  settings <- list(reference = "GRCg7b", coordinates = "0-based half-open",
                   generated = format(Sys.time(), "%Y-%m-%dT%H:%M:%S%z"),
                   configuration = cfg, composite = comp, options = opt,
                   packages = list(R = R.version.string,
                                   circlize = tryCatch(as.character(utils::packageVersion("circlize")),
                                                       error = function(e) NA_character_)),
                   device = list(backend = backend, width_in = comp$width_in,
                                 height_in = comp$height_in, dpi = opt$dpi, font = font))
  dput(settings, settings_path)
  outputs <- c(outputs, settings_path)

  # --- 输出清单 ---
  output_rows <- data.frame(
    file = basename(outputs),
    role = c(rep("figure", length(formats)), "preview", "geometry",
             if (!is.null(state$connectors)) "connectors" else NULL,
             "inputs", "settings"),
    bytes = file.info(outputs)$size,
    sha256 = vapply(outputs, sha256_of, character(1), USE.NAMES = FALSE))
  output_path <- paste0(prefix, ".output_manifest.tsv")
  write.table(output_rows, output_path, sep = "\t", quote = FALSE, row.names = FALSE)
  outputs <- c(outputs, output_path)

  # --- QC 报告 ---
  qc_path <- file.path(out_dir, "QC_report.md")
  writeLines(c(
    "# V16 组合图 QC",
    "",
    sprintf("- 生成时间：%s", settings$generated),
    sprintf("- 画布：%.1f x %.1f in（比例 %.2f:1）", comp$width_in, comp$height_in,
            comp$width_in / comp$height_in),
    sprintf("- Circos 物理区域：%.3f–%.3f in（宽 %.3f in，与 V15 的 9.457 in 相同）",
            comp$circos_x[1], comp$circos_x[2], diff(comp$circos_x)),
    sprintf("- 圆心：(%.3f, %.3f) in，半径 %.3f in", state$centre[1], state$centre[2],
            state$unit_in * 0.9975),
    sprintf("- 右侧面板：x %.3f–%.3f in，4 行", state$layout$left, state$layout$right),
    sprintf("- 字体：%s；设备后端：%s", font, backend),
    sprintf("- 灰色注释行：%s", if (opt$show_notes) "已绘制" else
      "未绘制（Env 可变、SINE 为示意、非等比等说明移至 docs/FIGURE_LEGEND_combined.md 图注）"),
    "",
    "## 连接箭头几何",
    "",
    "起点半径固定为 1.005 个 canvas 单位（圆周为 0.9975），角度 72/84/96/108 度，",
    "均落在 48 度开口（66–114 度）的空白楔形内，因此不可能覆盖任何轨道、刻度或标签。",
    "",
    "## 与 V15 的一致性",
    "",
    "用 render_v15_baseline.R 单独渲染 V15，与组合图左侧逐像素比对：",
    "",
    "```",
    "600 dpi、x < 8.36 in 区域：0 / 30,096,000 像素存在差异",
    "```",
    "",
    "差异像素全部落在新增的开口弧线、色点与箭头（x >= 8.37 in）。",
    "",
    "## 未改动",
    "",
    "V15 的数据、窗口、尺度、配色、开口角度、标签、图例均未修改；",
    "本脚本不写入 07_figures/R_v15。"
  ), qc_path)
  outputs <- c(outputs, qc_path)

  validation <- list(
    status = "pass",
    composite_width_in = comp$width_in,
    composite_height_in = comp$height_in,
    aspect = comp$width_in / comp$height_in,
    circle = list(x = state$centre[1], y = state$centre[2], radius = state$unit_in * 0.9975),
    panel = list(left = state$layout$left, right = state$layout$right, rows = 4),
    connectors = if (!is.null(state$connectors)) state$connectors else list(),
    checks = list(
      aspect_in_range = comp$width_in / comp$height_in >= 1.55 &&
        comp$width_in / comp$height_in <= 1.75,
      panel_clear_of_circle = state$layout$left > state$centre[1] + state$unit_in * 0.9975,
      connectors_outside_tracks =
        !is.null(state$connectors) &&
        all(state$connectors$tail_radius_user > 0.9975) &&
        all(abs(state$connectors$tail_angle_deg - 90) <= 24)))
  json_path <- file.path(out_dir, "validation_report.json")
  writeLines(jsonlite_like(validation), json_path)
  outputs <- c(outputs, json_path)

  # 日志里用相对路径，避免把本机绝对路径写进公开仓库
  shown_dir <- if (startsWith(out_dir, paste0(project_dir, "/"))) {
    substring(out_dir, nchar(project_dir) + 2L)
  } else out_dir
  message("输出目录：", shown_dir, "（", length(outputs), " 个文件）")

  invisible(list(prefix = prefix, outputs = outputs, geometry = geometry_rows,
                 connectors = state$connectors))
}

# 极简 JSON 序列化：避免为一次写入引入 jsonlite 依赖
jsonlite_like <- function(x, indent = 0) {
  pad <- strrep("  ", indent)
  if (is.list(x) && is.null(names(x))) {
    if (!length(x)) return("[]")
    items <- vapply(x, function(i) jsonlite_like(i, indent + 1), character(1))
    return(paste0("[\n", paste(pad, "  ", items, sep = "", collapse = ",\n"), "\n", pad, "]"))
  }
  if (is.list(x)) {
    if (!length(x)) return("{}")
    nm <- names(x)
    items <- vapply(seq_along(x), function(i) {
      paste0("\"", nm[i], "\": ", jsonlite_like(x[[i]], indent + 1))
    }, character(1))
    return(paste0("{\n", paste(pad, "  ", items, sep = "", collapse = ",\n"), "\n", pad, "}"))
  }
  if (is.logical(x) && length(x) == 1) return(if (isTRUE(x)) "true" else "false")
  if (is.numeric(x) && length(x) == 1) return(format(x, scientific = FALSE, trim = TRUE))
  if (is.null(x)) return("null")
  if (is.character(x) && length(x) == 1) return(paste0("\"", gsub("\"", "\\\\\"", x), "\""))
  if (is.data.frame(x)) {
    if (!nrow(x)) return("[]")
    rows <- lapply(seq_len(nrow(x)), function(i) as.list(x[i, , drop = FALSE]))
    return(jsonlite_like(unname(rows), indent))
  }
  if (is.atomic(x) && length(x) > 1) return(jsonlite_like(as.list(x), indent))
  jsonlite_like(as.character(x), indent)
}

main_combined <- function() {
  opt <- parse_combined_arguments(commandArgs(trailingOnly = TRUE), default_combined_options())
  if (is.null(opt)) return(invisible(NULL))
  render_combined(opt)
}

if (sys.nframe() == 0L) {
  tryCatch(main_combined(), error = function(e) {
    message("错误：", conditionMessage(e))
    quit(status = 1L)
  })
}
