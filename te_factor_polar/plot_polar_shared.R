#!/usr/bin/env Rscript
# ---------------------------------------------------------------------------
# Polar stacked bar chart: "Shared" vs "Unique" counts per category
#
# Replicates the panel style of Yuan et al. 2026 (Zoological Research)
# Figure 3B: 6 wedges on a circle (60 deg apart), each wedge a two-layer stack
# (inner = Unique, outer = Shared), white gaps between wedges, faint grey
# concentric rings, an L-shaped black axis on the left/bottom carrying the
# radial tick labels, a horizontal upper legend, and a bold panel tag.
#
# Input: tab-separated file with header
#     category <tab> series <tab> value
#   * `category`  wedge labels; IN FILE ORDER they run counter-clockwise
#                 starting at 3 o'clock (first row -> rightmost wedge).
#   * `series`    stack layers; the FIRST level of the factor is drawn on the
#                 OUTER radius, the SECOND on the inner radius. So the usual
#                 Shared,Unique ordering puts Shared outside and Unique inside,
#                 and sets the legend order.
#   * `value`     count plotted on the radial axis.
#
# Usage:
#   Rscript plot_polar_shared.R --input counts.tsv --out polar \
#           --ymax 500 --breaks 0,100,200,300,400,500
# ---------------------------------------------------------------------------

suppressPackageStartupMessages({
  library(ggplot2)
  library(grid)
})

# ---- arguments ------------------------------------------------------------
parse_args <- function(x) {
  out <- list(input = NULL, out = "polar", ymax = NA, breaks = "", minor = "",
              width = 88, height = 86, dpi = 600,
              colours = "#FD6456,#4BCCE0",          # outer, inner
              bar_width = 0.90,                     # fraction of the wedge
              label_size = 8.4, tick_size = 7.4, legend_size = 8.4,
              tag = "", tag_size = 11.5,
              ring_col = "grey87", ring_minor_col = "grey94",
              ring_size = 0.35, ring_minor_size = 0.28,
              axis_col = "black", axis_size = 0.55, border_col = "grey89", border_size = 0.30,
              start_deg = 0, ccw = TRUE, legend_key = 3.0,
              y_title = "", label_pad = 2.2)
  i <- 1
  while (i <= length(x)) {
    k <- x[i]
    v <- if (i < length(x)) x[i + 1] else NA
    key <- gsub("-", "_", sub("^--", "", k))
    if (!is.na(v) && !grepl("^--", v)) { out[[key]] <- v; i <- i + 2 }
    else { out[[key]] <- TRUE; i <- i + 1 }
  }
  out
}
opt <- parse_args(commandArgs(trailingOnly = TRUE))
if (is.null(opt$input)) stop("--input is required")

num <- function(z) as.numeric(z)
cols <- trimws(strsplit(opt$colours, ",")[[1]])

# ---- data -----------------------------------------------------------------
d <- read.delim(opt$input, stringsAsFactors = FALSE, check.names = FALSE,
                fileEncoding = "UTF-8")
names(d) <- tolower(trimws(names(d)))
stopifnot(all(c("category", "series", "value") %in% names(d)))

cats   <- unique(d$category)          # wedge order = order of appearance
series <- unique(d$series)            # first = outer ring, second = inner
n      <- length(cats)

d$category <- factor(d$category, levels = cats)
d$series   <- factor(d$series,   levels = series)

# ---- radial scale ---------------------------------------------------------
tot <- tapply(d$value, d$category, sum)
if (is.na(num(opt$ymax))) {
  opt$ymax <- max(pretty(c(0, max(tot) * 1.05)))
}
ymax <- num(opt$ymax)

mk_brks <- function(spec, fallback_every = 100, top = ymax) {
  if (nzchar(spec)) return(sort(num(strsplit(spec, ",")[[1]])))
  seq(0, floor(top / fallback_every) * fallback_every, by = fallback_every)
}
brks <- mk_brks(opt$breaks)
minor <- if (nzchar(opt$minor)) sort(num(strsplit(opt$minor, ",")[[1]])) else {
  step <- if (length(brks) > 1) diff(brks)[1] else 100
  setdiff(seq(0, ymax, by = step / 2), brks)
}
minor <- minor[minor < ymax]

# ---- polar rotation -------------------------------------------------------
# `--start-deg` = polar angle of the FIRST wedge centre, in degrees measured
# counter-clockwise from 3 o'clock (0 = right, 90 = top, 180 = left).
# Calibrated on ggplot2 4.x: with direction = -1 the first wedge sits at
# 240 deg when start = 0, hence the 240 - start mapping below.
dir <- if (isTRUE(opt$ccw)) -1 else 1
theta0 <- (240 - num(opt$start_deg)) * pi / 180

# ---- plot -----------------------------------------------------------------
p <- ggplot(d, aes(x = category, y = value, fill = series)) +
  geom_hline(yintercept = minor, colour = opt$ring_minor_col,
             linewidth = num(opt$ring_minor_size)) +
  geom_hline(yintercept = brks, colour = opt$ring_col,
             linewidth = num(opt$ring_size)) +
  geom_hline(yintercept = ymax, colour = opt$border_col,
             linewidth = num(opt$border_size)) +
  geom_col(width = num(opt$bar_width), colour = NA) +
  scale_fill_manual(values = cols, breaks = series, name = NULL) +
  scale_y_continuous(
    limits = c(0, ymax),
    breaks = brks,
    labels = function(v) format(v, big.mark = "", trim = TRUE),
    expand = expansion(mult = c(0, 0.015))
  ) +
  scale_x_discrete(expand = expansion(add = 0)) +
  coord_polar(theta = "x", start = theta0, direction = dir, clip = "off") +
  labs(tag = opt$tag, y = opt$y_title) +
  theme_classic(base_family = "sans") +
  theme(
    aspect.ratio      = 1,
    panel.background  = element_rect(fill = "white", colour = NA),
    panel.border      = element_blank(),
    panel.grid        = element_blank(),
    axis.line         = element_line(colour = opt$axis_col,
                                     linewidth = num(opt$axis_size)),
    axis.ticks        = element_line(colour = opt$axis_col,
                                     linewidth = num(opt$axis_size)),
    axis.ticks.length = unit(-2.1, "pt"),
    axis.text.x       = element_text(size = num(opt$label_size), face = "bold",
                                     colour = "black",
                                     margin = margin(t = num(opt$label_pad))),
    axis.text.y       = element_text(size = num(opt$tick_size), colour = "black",
                                     margin = margin(r = 3.2)),
    axis.title        = element_blank(),
    legend.position   = "top",
    legend.direction  = "horizontal",
    legend.title      = element_blank(),
    legend.text       = element_text(size = num(opt$legend_size), face = "bold"),
    legend.key        = element_blank(),
    legend.key.size   = unit(num(opt$legend_key), "mm"),
    legend.spacing.x  = unit(4.0, "mm"),
    legend.background = element_blank(),
    legend.margin     = margin(t = 0, b = -1),
    plot.tag          = element_text(size = num(opt$tag_size), face = "bold"),
    plot.tag.position = c(0.005, 0.985),
    plot.margin       = margin(3, 4, 2, 2)
  ) +
  guides(fill = guide_legend(
    # square colour keys, no border, drawn as in the reference panel
    keywidth  = unit(num(opt$legend_key), "mm"),
    keyheight = unit(num(opt$legend_key), "mm"),
    override.aes = list(colour = NA, linewidth = 0)
  ))

# ---- export ---------------------------------------------------------------
w <- num(opt$width) / 25.4; h <- num(opt$height) / 25.4
ggsave(paste0(opt$out, ".png"), p, width = w, height = h, dpi = num(opt$dpi),
       bg = "white")
ggsave(paste0(opt$out, ".pdf"), p, width = w, height = h, bg = "white")
cat(sprintf("written: %s.png / %s.pdf  (%.0f x %.0f mm, %s dpi)\n",
            opt$out, opt$out, num(opt$width), num(opt$height), num(opt$dpi)))
