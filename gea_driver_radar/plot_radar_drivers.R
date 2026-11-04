#!/usr/bin/env Rscript
# ---------------------------------------------------------------------------
# Radar (spider) chart: environment-associated variants per climate driver
#
# Style template taken from Yuan et al. 2026 (Zoological Research 47:1793)
# Figure 3C: 8 spokes clockwise from the top, circular dashed gridlines at
# 0 / 1600 / 3200, a small empty hole at the centre, series coloured
# #FC4E07 and #00AFBB, horizontal vertex markers drawn semi-transparent,
# horizontal legend underneath.
#
# Everything is drawn in Cartesian mm coordinates (radius in millimetres), so
# the spokes are straight lines, the circle is a true circle, and font sizes
# (pt) / line widths (mm) are the physical values that end up in the PDF.
#
# Input: tab-separated file with header
#     variable <tab> series <tab> value
#   * `variable` sets the spokes, IN FILE ORDER: 1st row -> top spoke,
#     then clockwise.
#   * `series` sets the polygons; IN FILE ORDER they define the legend order.
#   * `value` is the plotted count.
#
# Usage:
#   Rscript plot_radar_drivers.R --input counts.tsv --out radar \
#           --ymax 3200 --breaks 0,1600,3200
# ---------------------------------------------------------------------------

suppressPackageStartupMessages({
  library(ggplot2)
})

# ---- arguments ------------------------------------------------------------
defaults <- list(
  input = NULL, out = "radar",
  ymax = NA, breaks = "", hole_frac = 0.096,  # radius at value 0, as fraction of R
  labels = "",                                # optional variable->label table
  tag = "",                                   # panel letter, e.g. C
  radius = 18.5,                              # radar radius, mm
  frame = 1.66,                               # canvas half-width / radius
  label_gap = 0.60,                           # mm between circle and axis label
  axis_size = 5.4, ring_size = 5.0, legend_size = 5.5, tag_size = 12.5,
  colours = "#FC4E07,#00AFBB",
  point_size = 0.98, point_alpha = 0.75,      # marker diameter (mm) / opacity
  lw_series = 0.36, lw_ring = 0.30, lw_spoke = 0.16,
  dash_on = 2.3, dash_off = 0.68,             # mm
  ring_col = "grey12", spoke_col = "grey10", panel_fill = "#F6F6F6",
  dpi = 600, legend_dy = 6.4,                 # mm below the circle to the legend row
  legend_key = 3.4, legend_txt_gap = 0.73, legend_item_gap = 1.6,
  legend_char_w = 1.15
)

parse_args <- function(x, d) {
  i <- 1
  while (i <= length(x)) {
    k <- gsub("-", "_", sub("^--", "", x[i]))
    v <- if (i < length(x)) x[i + 1] else NA
    if (!is.na(v) && !grepl("^--", v)) { d[[k]] <- v; i <- i + 2 }
    else { d[[k]] <- TRUE; i <- i + 1 }
  }
  d
}
opt <- parse_args(commandArgs(trailingOnly = TRUE), defaults)
if (is.null(opt$input)) stop("--input is required")
num <- function(z) as.numeric(z)

R      <- num(opt$radius)
L      <- R * num(opt$frame)
hole_r <- R * num(opt$hole_frac)
stopifnot(hole_r < R)

# ---- data -----------------------------------------------------------------
d <- read.delim(opt$input, stringsAsFactors = FALSE, check.names = FALSE,
                fileEncoding = "UTF-8")
names(d) <- tolower(trimws(names(d)))
stopifnot(all(c("variable", "series", "value") %in% names(d)))
d$value <- as.numeric(d$value)

vars   <- unique(trimws(d$variable))   # spoke order
series <- unique(trimws(d$series))     # legend order
d$variable <- factor(trimws(d$variable), levels = vars)
d$series   <- factor(trimws(d$series),   levels = series)
n <- length(vars)

if (is.na(num(opt$ymax))) opt$ymax <- max(d$value, na.rm = TRUE)
ymax <- num(opt$ymax)

brks <- if (nzchar(opt$breaks)) {
  sort(num(strsplit(opt$breaks, ",")[[1]]))
} else {
  pretty(c(0, ymax))
}

axis_lab <- vars
if (nzchar(opt$labels)) {
  lm <- read.delim(opt$labels, stringsAsFactors = FALSE, check.names = FALSE,
                   fileEncoding = "UTF-8")
  names(lm) <- tolower(trimws(names(lm)))
  m <- setNames(trimws(lm$label), trimws(lm$variable))
  axis_lab <- ifelse(is.na(m[vars]), vars, m[vars])
}

# ---- geometry helpers -----------------------------------------------------
theta <- function(i) pi / 2 - (i - 1) * 2 * pi / n      # clockwise from top
r_of  <- function(v) hole_r + (R - hole_r) * pmin(v, ymax) / ymax

# circle as a polygon
circle <- function(r, t0 = 0, t1 = 2 * pi, m = 720) {
  t <- seq(t0, t1, length.out = m)
  data.frame(x = r * cos(t), y = r * sin(t))
}

# dashes along a circle, so that dash length stays constant in mm
arc_dashes <- function(r, on, off, phase = 0) {
  if (r < 1e-6) return(NULL)
  seg <- (on + off) / r                                # angular period (radians)
  nseg <- max(1, floor(2 * pi / seg))
  seg <- 2 * pi / nseg
  on_ang <- seg * on / (on + off)
  out <- lapply(seq_len(nseg), function(k) {
    a0 <- phase + (k - 1) * seg
    cc <- circle(r, a0, a0 + on_ang, m = 10)
    cc$dash <- k
    cc
  })
  do.call(rbind, out)
}

# --- layer data ------------------------------------------------------------
disc <- circle(R)                                     # background disc

rings <- do.call(rbind, lapply(seq_along(brks), function(i) {
  cc <- arc_dashes(r_of(brks[i]), num(opt$dash_on), num(opt$dash_off), phase = 0.06)
  cc$grp <- sprintf("g%02d_%03d", i, cc$dash)
  cc
}))

spokes <- data.frame(x = 0, y = 0,
                     xe = R * cos(theta(seq_len(n))),
                     ye = R * sin(theta(seq_len(n))))

poly <- do.call(rbind, lapply(split(d, d$series), function(s) {
  s <- s[order(as.numeric(s$variable)), ]
  rr <- r_of(s$value); tt <- theta(as.numeric(s$variable))
  p <- data.frame(x = rr * cos(tt), y = rr * sin(tt), series = s$series[1])
  rbind(p, p[1, ])
}))

verts <- do.call(rbind, lapply(split(d, d$series), function(s) {
  s <- s[order(as.numeric(s$variable)), ]
  rr <- r_of(s$value); tt <- theta(as.numeric(s$variable))
  data.frame(x = rr * cos(tt), y = rr * sin(tt), series = s$series[1])
}))

ang <- theta(seq_len(n)); ca <- cos(ang); sa <- sin(ang)
axis_df <- data.frame(
  x = (R + num(opt$label_gap)) * ca,
  y = (R + num(opt$label_gap)) * sa,
  label = axis_lab,
  hjust = ifelse(abs(ca) < 0.10, 0.5, ifelse(ca > 0, 0, 1)),
  vjust = ifelse(abs(ca) < 0.10, ifelse(sa > 0, 0, 1), 0.5)
)

ring_df <- data.frame(
  x = -0.35,
  y = r_of(brks) + ifelse(brks == max(brks), -1.30, 0.35),
  label = formatC(brks, format = "d", big.mark = ""),
  vjust = ifelse(brks == max(brks), 1, 0)
)

mm2size <- function(pt) pt * 0.3528      # geom_text/geom_point size unit is mm

# ---- manual legend --------------------------------------------------------
# one short line + a vertex marker + the series name per entry, centred on x=0
kw   <- num(opt$legend_key)                       # key line length, mm
tg   <- num(opt$legend_txt_gap)                   # key -> text gap, mm
ig   <- num(opt$legend_item_gap)                  # entry -> entry gap, mm
cwl  <- num(opt$legend_char_w)                    # mean bold glyph width, mm
txt_w <- nchar(series) * cwl
item_w <- kw + tg + txt_w
total_w <- sum(item_w) + ig * (length(series) - 1)
x <- -total_w / 2
legend_ly <- data.frame()
legend_lab <- data.frame()
for (i in seq_along(series)) {
  legend_ly  <- rbind(legend_ly, data.frame(
    x = x, xe = x + kw, series = series[i]))
  legend_lab <- rbind(legend_lab, data.frame(
    x = x + kw + tg, label = series[i], series = series[i]))
  x <- x + item_w[i] + ig
}
leg_y <- -(R + num(opt$legend_dy))

# ---- plot -----------------------------------------------------------------
p <- ggplot() +
  geom_polygon(data = disc, aes(x, y), fill = opt$panel_fill, colour = NA) +
  geom_path(data = rings, aes(x, y, group = grp),
            colour = opt$ring_col, linewidth = num(opt$lw_ring), lineend = "butt") +
  geom_segment(data = spokes, aes(x = x, y = y, xend = xe, yend = ye),
               colour = opt$spoke_col, linewidth = num(opt$lw_spoke)) +
  geom_path(data = poly, aes(x, y, colour = series, group = series),
            linewidth = num(opt$lw_series), lineend = "round", linejoin = "round") +
  geom_point(data = verts, aes(x, y, colour = series),
             size = num(opt$point_size), stroke = 0,
             alpha = num(opt$point_alpha)) +
  geom_text(data = axis_df, aes(x, y, label = label, hjust = hjust, vjust = vjust),
            size = mm2size(num(opt$axis_size)), fontface = "bold", colour = "black") +
  geom_text(data = ring_df, aes(x, y, label = label, vjust = vjust),
            hjust = 1, size = mm2size(num(opt$ring_size)), colour = opt$ring_col) +
  geom_segment(data = transform(legend_ly, y = leg_y, ye = leg_y),
               aes(x = x, xend = xe, y = y, yend = ye, colour = series),
               linewidth = num(opt$lw_series)) +
  geom_point(data = transform(legend_ly, y = leg_y),
             aes(x = (x + xe) / 2, y = y, colour = series),
             size = num(opt$point_size), stroke = 0) +
  geom_text(data = transform(legend_lab, y = leg_y),
            aes(x = x, y = y, label = label),
            hjust = 0, vjust = 0.5, size = mm2size(num(opt$legend_size)),
            fontface = "bold", colour = "black") +
  annotate("text", x = -L + 0.5, y = L - 0.2, label = opt$tag, hjust = 0, vjust = 1,
           size = mm2size(num(opt$tag_size)), fontface = "bold", colour = "black") +
  scale_colour_manual(values = trimws(strsplit(opt$colours, ",")[[1]]), name = NULL) +
  coord_equal(xlim = c(-L, L), ylim = c(-L, L), expand = FALSE, clip = "off") +
  theme_void(base_family = "sans") +
  theme(legend.position = "none",
        plot.margin     = margin(0, 0, 0, 0))

# ---- export ---------------------------------------------------------------
w <- 2 * L / 25.4
h <- 2 * L / 25.4
ggsave(paste0(opt$out, ".png"), p, width = w, height = h, dpi = num(opt$dpi),
       bg = "white")
ggsave(paste0(opt$out, ".pdf"), p, width = w, height = h, bg = "white")
cat(sprintf("written: %s.png / %s.pdf  (%.1f x %.1f mm, %s dpi, radar d=%.1f mm)\n",
            opt$out, opt$out, 2 * L, 2 * L,
            opt$dpi, 2 * R))
