#!/usr/bin/env Rscript
# =============================================================================
# plot_gea_panels.R
#
# Genotype-environment association (GEA) screen, drawn as one panel per
# environmental variable:
#
#   bottom  : scatter of RDA correlation (y) vs LFMM -log10(P) (x), points
#             coloured by whether they pass both thresholds (candidate SNPs)
#   top     : marginal histogram of -log10(P) (log10 counts, left axis) with
#             the cumulative percentage overlaid (right axis)
#
# The two building blocks are stitched with patchwork, which keeps the strip
# and the scatter on exactly the same x scale.
#
# Usage
#   Rscript plot_gea_panels.R --input example_gea_stats.tsv \
#           --labels example_labels.tsv --out gea_marginal_scatter
#
# Input (tab-separated, header required)
#   trait   environmental variable, one panel per value
#   r       RDA correlation coefficient (signed or absolute)
#   p       LFMM P-value (or FDR q-value; pass --thr-p accordingly)
#   snp     optional SNP id, ignored for plotting
#
# Options
#   --input FILE       stats table                     (required)
#   --labels FILE      two columns: trait, display label (optional)
#   --out STEM         output stem                     (default: gea_panels)
#   --thr-r NUM        |r| threshold                   (default: 0.2)
#   --thr-p NUM        P/FDR threshold, 0.01 -> x = 2  (default: 0.01)
#   --abs-r            take |r| before plotting        (default: off)
#   --ncol INT         panels per row                  (default: 4)
#   --width NUM        figure width, inches            (default: 12)
#   --height NUM       figure height, inches           (default: 6.9)
#   --dpi INT          PNG resolution                  (default: 600)
#   --tag STR          panel letter, "" to omit        (default: "B")
#   --xmax NUM         force one x limit for all panels (default: per trait)
#   --bins INT         histogram bins per panel        (default: 40)
#
# Requires: ggplot2 (>= 3.4), patchwork, scales. No other packages.
# =============================================================================
suppressPackageStartupMessages({
  library(ggplot2)
  library(patchwork)
  library(scales)
})

## ---------------------------------------------------------------------------
## 0. palette and theme
## ---------------------------------------------------------------------------
PAL <- list(
  ns      = "black",     # points failing either threshold
  sig     = "#00B238",   # candidate SNPs (pass both)
  hist_lo = "grey64",    # bins below the P threshold
  hist_hi = "#E08B32",   # bins above the P threshold
  cut     = "#3C7EA8"    # threshold rules
)

gea_theme <- function(base_size = 7) {
  theme_classic(base_size = base_size) +
    theme(
      panel.border      = element_rect(colour = "black", fill = NA, linewidth = 0.35),
      axis.line         = element_blank(),
      axis.ticks        = element_line(linewidth = 0.3),
      axis.ticks.length = unit(1.8, "pt"),
      axis.text         = element_text(colour = "black", size = base_size - 0.5),
      axis.title        = element_text(colour = "black", size = base_size + 1),
      plot.margin       = margin(2, 3, 2, 2)
    )
}

## ---------------------------------------------------------------------------
## 1. marginal strip: histogram of -log10(P) + cumulative percentage
## ---------------------------------------------------------------------------
# Notes on the dual axis, the only fragile part of this figure:
#   * do NOT use scale_y_log10() -- sec_axis() transforms are applied in the
#     transformed space and the percentage mapping goes wrong;
#   * instead plot log10(count) directly on a linear axis and label the ticks
#     as powers of ten;
#   * the cumulative curve is rescaled into the same units, pct * (ytop / 100),
#     and sec_axis() divides it back out.
strip_plot <- function(d, xmax, thr_x, bins = 40, base_size = 7, xname = "P") {

  brks <- seq(0, xmax, length.out = max(4L, bins) + 1L)
  bw   <- diff(brks)[1]
  h    <- hist(d$x, breaks = brks, plot = FALSE)

  hd <- data.frame(mid = h$mids, n = h$counts)
  hd <- hd[hd$n > 0, , drop = FALSE]
  hd$grp <- factor(ifelse(hd$mid < thr_x, "lo", "hi"), levels = c("lo", "hi"))
  hd$y   <- log10(hd$n)

  cs   <- data.frame(mid = h$mids, pct = 100 * cumsum(h$counts) / sum(h$counts))
  lmax <- log10(max(h$counts))
  ytop <- max(1, lmax * 1.08)          # small headroom instead of a whole decade
  k    <- ytop / 100
  ybrk <- unique(c(0, floor(lmax / 2), floor(lmax)))
  if (length(ybrk) < 2) ybrk <- c(0, ytop)

  # ASCII ">=" keeps every device (pdf, png, cairo, Windows) happy; switch to
  # intToUtf8(0x2265) if your graphics device has the glyph.
  x_lab  <- format(round(thr_x, 2), nsmall = 0)   # 2 for 0.01, 1.3 for 0.05
  lab_lt <- sprintf("-log10 %s < %s",  xname, x_lab)
  lab_ge <- sprintf("-log10 %s >= %s", xname, x_lab)

  ggplot() +
    geom_col(data = hd, aes(mid, y, fill = grp), width = bw, linewidth = 0) +
    geom_line(data = cs, aes(mid, pct * k, colour = "cum"),
              linewidth = 0.4, key_glyph = "path") +
    scale_fill_manual(name = NULL, drop = FALSE,
                      values = c(lo = PAL$hist_lo, hi = PAL$hist_hi),
                      labels = c(lab_lt, lab_ge)) +
    scale_colour_manual(name = NULL, values = c(cum = "black"),
                        labels = "Cumulative (%)") +
    guides(fill   = guide_legend(order = 1, override.aes = list(colour = "white", linewidth = 0.3)),
           colour = guide_legend(order = 2)) +
    scale_x_continuous(limits = c(0, xmax), expand = expansion(mult = c(0.01, 0.01))) +
    scale_y_continuous(
      limits = c(0, ytop),
      breaks = ybrk,
      labels = function(b) ifelse(b >= 3, label_scientific()(10^b),
                                  label_number(accuracy = 1)(10^b)),
      expand = expansion(mult = c(0, 0.03)),
      sec.axis = sec_axis(~ . / k, breaks = c(0, 50, 100))
    ) +
    labs(y = "Counts", x = NULL) +
    gea_theme(base_size) +
    theme(
      axis.text.x       = element_blank(),
      axis.ticks.x      = element_blank(),
      axis.text.y.right = element_text(angle = 90, hjust = 0.5, vjust = 0.5),
      legend.position      = c(0.99, 0.55),
      legend.justification = c(1, 0.5),
      legend.direction     = "vertical",
      legend.background    = element_rect(fill = "white", colour = NA),
      legend.key.height    = unit(0.17, "cm"),
      legend.key.width     = unit(0.45, "cm"),
      legend.text          = element_text(size = base_size - 1.5),
      legend.spacing.y     = unit(0.01, "cm"),
      legend.margin        = margin(0, 0, 0, 0),
      legend.box.spacing   = unit(0, "cm")
    )
}

## ---------------------------------------------------------------------------
## 2. scatter: RDA correlation vs LFMM -log10(P)
## ---------------------------------------------------------------------------
scatter_plot <- function(d, label, xmax, thr_x, thr_r, ymax = 0.5, base_size = 7,
                         xname = "P", clip_n = 0) {

  d$grp <- factor(ifelse(d$r >= thr_r & d$x >= thr_x, "sig", "ns"),
                  levels = c("ns", "sig"))

  ggplot(d, aes(x, r)) +
    geom_hline(yintercept = thr_r, colour = PAL$cut, linetype = "dashed", linewidth = 0.35) +
    geom_vline(xintercept = thr_x, colour = PAL$cut, linetype = "dashed", linewidth = 0.35) +
    geom_point(aes(colour = grp, alpha = grp, size = grp), stroke = 0) +
    annotate("text", x = xmax / 2, y = ymax * 0.97, label = label, vjust = 1,
             size = 2.4, fontface = "bold") +
    scale_colour_manual(values = c(ns = PAL$ns, sig = PAL$sig), guide = "none") +
    scale_alpha_manual(values = c(ns = 0.6, sig = 0.95), guide = "none") +
    scale_size_manual(values = c(ns = 0.42, sig = 0.62), guide = "none") +
    scale_x_continuous(limits = c(0, xmax),
                       breaks = seq(0, xmax, by = if (xmax > 6) 2 else 1),
                       expand = expansion(mult = c(0.01, 0.01))) +
    scale_y_continuous(limits = c(0, ymax),
                       breaks = seq(0, ymax, if (ymax > 0.55) 0.2 else 0.1),
                       expand = expansion(mult = c(0.01, 0.01))) +
    labs(x = if (xname == "P") expression(-log[10] * italic(P)) else sprintf("-log10 %s", xname),
         y = "Correlation") +
    { if (clip_n > 0) annotate("text", x = xmax * 0.99, y = ymax * 0.02, hjust = 1, vjust = 0,
                               label = sprintf("%s loci >= %g", format(clip_n, big.mark = ","), xmax),
                               size = 1.7, colour = "grey45") } +
    gea_theme(base_size) +
    theme(axis.text.y = element_text(angle = 90, hjust = 0.5, vjust = 0.5))
}

## ---------------------------------------------------------------------------
## 3. one panel = strip over scatter
## ---------------------------------------------------------------------------
panel_plot <- function(d, label, xmax, thr_x, thr_r, bins = 40, base_size = 7,
                       xname = "P", clip_n = 0, ymax = NULL) {
  if (is.null(ymax)) ymax <- max(0.5, min(1, ceiling(max(d$r, na.rm = TRUE) * 10) / 10))
  strip_plot(d, xmax, thr_x, bins, base_size, xname) /
    scatter_plot(d, label, xmax, thr_x, thr_r, ymax, base_size, xname, clip_n) +
    plot_layout(heights = c(1, 3.05))
}

## ---------------------------------------------------------------------------
## 4. whole figure
## ---------------------------------------------------------------------------
#' @param df      data.frame with columns trait, r, p (and optionally snp)
#' @param labels  optional named character vector trait -> display label
gea_figure <- function(df, labels = NULL, thr_r = 0.2, thr_p = 0.01,
                       ncol = 4, bins = 40, tag = "B",
                       base_size = 7, xmax = NULL, xname = "P") {

  df$p[df$p <= 0] <- .Machine$double.xmin
  df$x <- -log10(df$p)

  traits <- unique(df$trait)
  panels <- vector("list", length(traits))
  ymax   <- max(0.5, min(1, ceiling(max(df$r, na.rm = TRUE) * 10) / 10))  # one scale for all

  for (i in seq_along(traits)) {
    d <- df[df$trait == traits[i], , drop = FALSE]
    lab <- if (!is.null(labels) && traits[i] %in% names(labels)) labels[[traits[i]]] else traits[i]

    xmax_i <- if (is.null(xmax)) ceiling(max(d$x)) else xmax
    xmax_i <- max(xmax_i, ceiling(-log10(thr_p)) + 1)

    clip_n <- sum(d$x > xmax_i)
    if (clip_n > 0) d$x <- pmin(d$x, xmax_i)   # pile the overflow on the right edge

    panels[[i]] <- panel_plot(d, lab, xmax_i, -log10(thr_p), thr_r, bins, base_size,
                              xname, clip_n, ymax)
  }

  fig <- wrap_plots(panels, ncol = ncol)

  if (nzchar(tag)) {
    fig <- wrap_elements(fig) + labs(tag = tag) +
      theme(plot.tag = element_text(size = 12, face = "bold"))
  }
  fig + theme(plot.background = element_rect(fill = "white", colour = NA))
}

## ---------------------------------------------------------------------------
## 5. CLI
## ---------------------------------------------------------------------------
parse_args <- function(args) {
  opt <- list(input = NULL, labels = NULL, out = "gea_panels",
              thr_r = 0.2, thr_p = 0.01, abs_r = FALSE, ncol = 4,
              width = 12, height = 6.9, dpi = 600, tag = "B",
              xmax = NULL, bins = 40, x_name = "P")
  i <- 1
  while (i <= length(args)) {
    a <- args[i]
    if (a == "--abs-r") { opt$abs_r <- TRUE; i <- i + 1; next }
    if (grepl("^--", a)) {
      key <- gsub("-", "_", sub("^--", "", a))
      if (key %in% names(opt) && i < length(args)) {
        opt[[key]] <- args[i + 1]; i <- i + 2; next
      }
    }
    if (a %in% c("-h", "--help")) {
      cat("see the header of plot_gea_panels.R for usage\n"); quit(save = "no")
    }
    i <- i + 1
  }
  for (k in c("thr_r", "thr_p", "width", "height")) opt[[k]] <- as.numeric(opt[[k]])
  for (k in c("dpi", "ncol", "bins")) opt[[k]] <- as.integer(opt[[k]])
  if (!is.null(opt$xmax)) opt$xmax <- as.numeric(opt$xmax)
  opt$abs_r <- isTRUE(opt$abs_r) || identical(opt$abs_r, "TRUE")
  opt
}

main <- function() {
  opt <- parse_args(commandArgs(trailingOnly = TRUE))
  if (is.null(opt$input)) stop("--input is required (see header for usage)")

  df <- read.delim(opt$input, stringsAsFactors = FALSE, check.names = FALSE)
  need <- c("trait", "r", "p")
  miss <- setdiff(need, names(df))
  if (length(miss)) stop("missing column(s) in input: ", paste(miss, collapse = ", "))
  if (opt$abs_r) df$r <- abs(df$r)

  labels <- NULL
  if (!is.null(opt$labels)) {
    lb <- read.delim(opt$labels, stringsAsFactors = FALSE)
    labels <- setNames(lb$label, lb$trait)
  }

  fig <- gea_figure(df, labels = labels, thr_r = opt$thr_r, thr_p = opt$thr_p,
                    ncol = opt$ncol, bins = opt$bins, tag = opt$tag,
                    xmax = opt$xmax, xname = opt$x_name)

  png_file <- paste0(opt$out, ".png")
  pdf_file <- paste0(opt$out, ".pdf")
  ggsave(png_file, fig, width = opt$width, height = opt$height, dpi = opt$dpi, bg = "white")
  ggsave(pdf_file, fig, width = opt$width, height = opt$height, bg = "white")
  message("wrote ", png_file, " and ", pdf_file)
}

if (sys.nframe() == 0L) main()
