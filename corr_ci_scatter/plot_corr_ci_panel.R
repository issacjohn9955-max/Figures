#!/usr/bin/env Rscript
# =============================================================================
# plot_corr_ci_panel.R
#
# One publication panel: a grouped scatter (one colour per group), each group
# carrying its own linear fit with a 95% confidence band, and the R / P / (n)
# block printed on the right in the group colour.
#
# Layout copies Figure 4A of Yuan et al. (2026, Zoological Research): top-1%
# windows of one selection statistic on x, the other statistic on y, six
# environmental variables as groups, Pearson r and its P value per group.
#
# Usage
#   Rscript plot_corr_ci_panel.R --input te_method_corr.tsv --out corr_ci_scatter
#
# Input (tab separated, header required)
#   group   group label; used verbatim in the legend and the annotation block
#   x       x coordinate of one point
#   y       y coordinate of one point
#
# Options
#   --input FILE      input table                             (required)
#   --out STEM        output stem, writes STEM.png + STEM.pdf + STEM_stats.tsv
#   --palette NAME    npg (default) | pangenome_spectrum | chromatic_nc |
#                     botanical_genome | greys
#   --method NAME     pearson (default) | spearman
#   --xlab STR        x axis title; prefix with "~" to pass plotmath verbatim,
#                     e.g. '~bold(zF[ST])'                     (default: "x")
#   --ylab STR        y axis title, same convention              (default: "y")
#   --tag STR         panel letter, "" to omit                    (default: "A")
#   --base-size PT    base font size                            (default: 6)
#   --width MM        panel width in mm                          (default: 112)
#   --height MM       panel height in mm                         (default: 56)
#   --dpi INT         PNG resolution                             (default: 600)
#   --point-size MM   point diameter                             (default: 1.2)
#   --point-alpha     point transparency                         (default: 0.8)
#   --line-width MM   regression line width                      (default: 0.6)
#   --band-alpha      confidence band transparency                (default: 0.30)
#   --ann-top MM      gap between the panel top and the first row  (default: 1.4)
#   --ann-step MM     vertical distance between rows               (default: 3.3)
#   --ann-gap MM      horizontal gap between the R / P / n columns (default: 2.4)
#   --ann-right MM    gap between the n column and the right edge  (default: 1.2)
#   --ann-bg ALPHA    white backing rectangle behind the whole block; 0 keeps the
#                     reference panel's look, 0.7-0.9 is the escape hatch when
#                     the block lands on dense points and bands   (default: 0)
#   --ann-char-mm MM  width of one character, used to place the columns
#                     so they never overlap          (default: 0.60 * size * 0.3528)
#   --xlim A,B        override x limits        (default: data range + 5% padding)
#   --ylim A,B        override y limits
#   --legend-pos POS  top (default) | right | none
#
# Requires: ggplot2 (>= 3.4), scales. No other packages.
# =============================================================================
suppressPackageStartupMessages({
  library(ggplot2)
  library(scales)
})

## ---------------------------------------------------------------------------
## 0. arguments
## ---------------------------------------------------------------------------
parse_args <- function(a) {
  out <- list()
  i <- 1
  while (i <= length(a)) {
    key <- a[i]
    if (!startsWith(key, "--")) stop("unexpected argument: ", key)
    key <- sub("^--", "", key)
    if (key %in% c("help")) { out[[key]] <- TRUE; i <- i + 1; next }
    if (i == length(a) || startsWith(a[i + 1], "--")) {
      out[[key]] <- TRUE; i <- i + 1
    } else {
      out[[key]] <- a[i + 1]; i <- i + 2
    }
  }
  out
}
opt <- parse_args(commandArgs(trailingOnly = TRUE))
get_opt <- function(k, default) {
  v <- opt[[k]]
  if (is.null(v)) default else v
}
as_num <- function(v, default) if (is.null(v)) default else as.numeric(v)
as_vec <- function(v, default) {
  if (is.null(v) || !nzchar(v)) return(default)
  as.numeric(strsplit(v, ",")[[1]])
}

## ---------------------------------------------------------------------------
## 1. palettes and theme
## ---------------------------------------------------------------------------
# npg = the six-colour Nature Publishing Group set, which is what the reference
# panel uses (#E64B35 #4DBBD5 #00A087 #3C5488 #F39B7F #8491B4). The other three
# are the house palettes from figure-style/style/palettes.json.
PALETTES <- list(
  npg                = c("#E64B35", "#4DBBD5", "#00A087", "#3C5488", "#F39B7F", "#8491B4"),
  pangenome_spectrum = c("#386C8C", "#7BB6AC", "#9689B9", "#B4AD74", "#5899B2", "#A1A8BE"),
  chromatic_nc       = c("#315B90", "#50A7BD", "#8AA45D", "#A388C2", "#D2A259", "#65A69A"),
  botanical_genome   = c("#3F7A62", "#93B8A0", "#568D95", "#AEB5C5", "#8F8FAE", "#C1AC88"),
  greys              = c("#2B2B2B", "#6E6E6E", "#9C9C9C", "#C4C4C4", "#DCDCDC", "#EFEFEF")
)
palette_for <- function(name, n) {
  base <- PALETTES[[name]]
  if (is.null(base)) stop("unknown palette: ", name,
                          " (choose from ", paste(names(PALETTES), collapse = ", "), ")")
  if (n <= length(base)) return(base[seq_len(n)])
  colorRampPalette(base)(n)
}

base_size <- as_num(get_opt("base-size", NULL), 6)
mm_pt     <- 0.3528           # 1 pt in mm, the unit ggplot2 text sizes use

theme_panel <- function(size = base_size, pos = "top") {
  th <- theme_classic(base_size = size, base_family = "Helvetica") +
    theme(
      panel.grid        = element_blank(),
      axis.line         = element_line(linewidth = 0.45, colour = "black"),
      axis.ticks        = element_line(linewidth = 0.45, colour = "black"),
      # negative length = ticks inside the panel, as in the reference
      axis.ticks.length = unit(-2.2, "pt"),
      axis.text         = element_text(size = size - 0.5, colour = "black",
                                       margin = margin(t = 4, r = 4)),
      axis.title        = element_text(size = size + 0.5, colour = "black", face = "bold"),
      axis.title.x      = element_text(margin = margin(t = 4)),
      axis.title.y      = element_text(margin = margin(r = 2)),
      legend.position   = pos,
      legend.direction  = "horizontal",
      legend.title      = element_blank(),
      legend.text       = element_text(size = size - 1, colour = "black", face = "bold"),
      legend.key.size   = unit(2.4, "mm"),
      legend.key.width  = unit(2.8, "mm"),
      legend.spacing.x  = unit(1.2, "mm"),
      legend.spacing.y  = unit(0.6, "mm"),
      legend.margin     = margin(0, 0, 1, 0),
      plot.margin       = margin(4, 4, 2, 2),
      plot.tag          = element_text(size = size + 3, face = "bold", hjust = 0, vjust = 1),
      plot.tag.position = "topleft"
    )
  if (pos == "none") th <- th + theme(legend.position = "none")
  th
}

## ---------------------------------------------------------------------------
## 2. input
## ---------------------------------------------------------------------------
input <- get_opt("input", NULL)
if (is.null(input)) stop("--input is required")
stem  <- get_opt("out", tools::file_path_sans_ext(basename(input)))

d <- read.delim(input, check.names = FALSE, stringsAsFactors = FALSE)
need <- c("group", "x", "y")
if (!all(need %in% names(d)))
  stop("input needs the columns: ", paste(need, collapse = ", "),
       " (found: ", paste(names(d), collapse = ", "), ")")
d <- d[stats::complete.cases(d[, need]), need]
d$group <- factor(d$group, levels = unique(d$group))

## ---------------------------------------------------------------------------
## 3. per-group statistics
## ---------------------------------------------------------------------------
method <- get_opt("method", "pearson")
if (!method %in% c("pearson", "spearman")) stop("--method must be pearson or spearman")

st <- do.call(rbind, lapply(split(d, d$group), function(s) {
  ct <- suppressWarnings(cor.test(s$x, s$y, method = method))
  data.frame(group = as.character(s$group[1]), n = nrow(s),
             r = unname(ct$estimate), p = ct$p.value)
}))
st$group <- factor(st$group, levels = levels(d$group))
st <- st[order(st$group), , drop = FALSE]

# R and P are printed to two significant digits (signif(x, 2)), which is what
# turns 0.00413 into "0.0041" and 1.6e-07 stays in scientific notation.
fmt <- function(v) as.character(signif(v, 2))
# plotmath: the letter is bold italic, "=" is glued to the value with * so no
# extra space is inserted, and the number itself stays upright bold.
st$lab_r <- sprintf("bold(bolditalic(R)*\"=\"*%s)", fmt(st$r))
st$lab_p <- sprintf("bold(bolditalic(P)*\"=\"*%s)", fmt(st$p))
st$lab_n <- sprintf("bold(\"(\"*italic(n)*\"=%d)\")", st$n)

## ---------------------------------------------------------------------------
## 4. annotation block geometry
## ---------------------------------------------------------------------------
# The R / P / n block is a fixed-height stack of coloured labels in the right
# part of the panel. Its horizontal anchors are NOT a fraction of the x range:
# text has a fixed physical width, so on a table with a narrow x range a
# fraction-based anchor would pile the three columns on top of each other.
# The anchors are therefore solved from an estimate of the text width in mm,
# converted to data units with the panel's mm-per-unit scale.
xr <- range(d$x)
yr <- range(d$y)
step <- as_num(get_opt("ann-step", NULL), 3.3)      # mm between rows
top_mm <- as_num(get_opt("ann-top", NULL), 1.4)     # gap below the panel top
gap_mm <- as_num(get_opt("ann-gap", NULL), 2.4)     # gap between columns
right_mm <- as_num(get_opt("ann-right", NULL), 1.2) # gap from the right edge

# rough panel size: the axis furniture is taken off the output size
left_mm  <- 12
panel_w  <- as_num(get_opt("width", NULL), 112) - left_mm - 4
panel_h  <- as_num(get_opt("height", NULL), 56) - 13
xr_pad   <- xr + c(-1, 1) * 0.05 * diff(xr)         # ggplot's default 5% padding
yr_pad   <- yr + c(-1, 1) * 0.05 * diff(yr)
mm_per_x <- panel_w / diff(xr_pad)
mm_per_y <- panel_h / diff(yr_pad)

text_pt  <- base_size - 0.5                          # label size used below
char_mm  <- as_num(get_opt("ann-char-mm", NULL), 0.60 * text_pt * mm_pt)

# widths are estimated from the text that is actually drawn, not from the
# plotmath source code (which is several times longer)
txt_r <- sprintf("R=%s", fmt(st$r))
txt_p <- sprintf("P=%s", fmt(st$p))
txt_n <- sprintf("(n=%d)", st$n)
w_mm  <- c(max(nchar(txt_r)), max(nchar(txt_p)), max(nchar(txt_n))) * char_mm
x_right <- xr_pad[2] - right_mm / mm_per_x
x_n <- x_right - w_mm[3] / mm_per_x
x_p <- x_n - gap_mm / mm_per_x - w_mm[2] / mm_per_x
x_r <- x_p - gap_mm / mm_per_x - w_mm[1] / mm_per_x

ann <- data.frame(
  x   = rep(c(x_r, x_p, x_n), each = nrow(st)),
  grp = rep(st$group, times = 3),
  lab = c(st$lab_r, st$lab_p, st$lab_n)
)
y_top <- yr_pad[2] - top_mm / mm_per_y
ann$y <- y_top - rep(seq_len(nrow(st)) - 1, times = 3) * step / mm_per_y
if (min(ann$y) < yr_pad[1])
  warning("annotation block runs past the bottom of the panel; lower --ann-step")

## ---------------------------------------------------------------------------
## 5. plot
## ---------------------------------------------------------------------------
pal <- get_opt("palette", "npg")
cols <- palette_for(pal, nlevels(d$group))
names(cols) <- levels(d$group)

px_size   <- as_num(get_opt("point-size", NULL), 1.2)
px_alpha  <- as_num(get_opt("point-alpha", NULL), 0.8)
line_w    <- as_num(get_opt("line-width", NULL), 0.6)
band_a    <- as_num(get_opt("band-alpha", NULL), 0.30)
halo      <- as_num(get_opt("ann-halo", NULL), 0.18)   # 0 = no outline
ann_bg    <- as_num(get_opt("ann-bg", NULL), 0)         # 0 = reference look
legend_pos <- get_opt("legend-pos", "top")
leg_guide  <- if (identical(legend_pos, "right")) {
  guide_legend(ncol = 1)
} else {
  guide_legend(nrow = 1, byrow = TRUE)
}

expr_or_text <- function(v, default) {
  if (is.null(v)) return(default)
  if (startsWith(v, "~")) parse(text = substring(v, 2))[[1]] else v
}
xlab <- expr_or_text(get_opt("xlab", NULL), "x")
ylab <- expr_or_text(get_opt("ylab", NULL), "y")

# backing rectangle, sized to the block plus 1.4 mm of breathing room
ann_bg_layer <- annotate(
  "rect",
  xmin = x_r - 1.4 / mm_per_x, xmax = x_right + 1.4 / mm_per_x,
  ymin = min(ann$y) - 1.5 / mm_per_y, ymax = max(ann$y) + 1.5 / mm_per_y,
  fill = "white", alpha = ann_bg, colour = NA
)

p <- ggplot(d, aes(x = x, y = y, colour = group, fill = group))
if (all(table(d$group) >= 3)) {
  p <- p + geom_smooth(method = "lm", formula = y ~ x, se = TRUE, level = 0.95,
                       alpha = band_a, linewidth = line_w, show.legend = TRUE)
}
p <- p +
  # points go in their own layer so that no confidence band covers them
  geom_point(size = px_size, alpha = px_alpha, stroke = 0, show.legend = TRUE) +
  # Optional white backing behind the block. On dense data the labels land on
  # top of points and bands: a halo alone leaves crescents where a point is cut
  # in half, and a salmon label on a salmon band is unreadable. A translucent
  # rectangle (no border) fixes both and stays nearly invisible on white.
  # Set --ann-bg 0 to get the reference panel's bare-on-white look.
  {if (ann_bg > 0) ann_bg_layer else NULL} +
  # optional white halo on top of that backing; harmless when the backing is on
  geom_text(data = ann, aes(x = x, y = y, label = lab),
            parse = TRUE, hjust = 0, vjust = 0.5, colour = "white",
            size = text_pt * mm_pt + halo, show.legend = FALSE,
            inherit.aes = FALSE) +
  geom_text(data = ann, aes(x = x, y = y, label = lab, colour = grp),
            parse = TRUE, hjust = 0, vjust = 0.5, size = text_pt * mm_pt,
            show.legend = FALSE, inherit.aes = FALSE) +
  scale_colour_manual(values = cols, drop = FALSE) +
  scale_fill_manual(values = cols, drop = FALSE) +
  # The same nrow/ncol on both aesthetics keeps the colour and fill keys merged;
  # without it ggplot2 wraps a horizontal legend as soon as the labels are much
  # longer than ten characters.
  guides(colour = leg_guide, fill = leg_guide) +
  labs(x = xlab, y = ylab, tag = get_opt("tag", "A"), colour = NULL, fill = NULL) +
  theme_panel(base_size, legend_pos)

if (!is.null(opt[["xlim"]]) || !is.null(opt[["ylim"]])) {
  p <- p + coord_cartesian(
    xlim = if (is.null(opt[["xlim"]])) NULL else as_vec(opt[["xlim"]], NULL),
    ylim = if (is.null(opt[["ylim"]])) NULL else as_vec(opt[["ylim"]], NULL)
  )
}

## ---------------------------------------------------------------------------
## 6. export
## ---------------------------------------------------------------------------
w <- as_num(get_opt("width", NULL), 112)
h <- as_num(get_opt("height", NULL), 56)
dpi <- as_num(get_opt("dpi", NULL), 600)

save_fs <- function(file, ...) {
  ggsave(file, p, width = w, height = h, units = "mm", bg = "white", ...)
  if (!file.exists(file)) stop("failed to write ", file)
  message("wrote ", file)
}

# default devices on purpose: this machine's R has no cairo module, and the
# plain pdf()/png() pair is enough for this panel (no semi-transparent text).
save_fs(paste0(stem, ".png"), dpi = dpi)
save_fs(paste0(stem, ".pdf"))

lab_as_text <- function(e) if (is.character(e)) e else paste(deparse(e), collapse = "")
out_stats <- data.frame(
  group  = st$group,
  n      = st$n,
  R      = fmt(st$r),
  P      = fmt(st$p),
  x_label = lab_as_text(xlab),
  y_label = lab_as_text(ylab),
  method = method
)
write.table(out_stats, paste0(stem, "_stats.tsv"), sep = "\t",
            quote = FALSE, row.names = FALSE)
message("wrote ", stem, "_stats.tsv")
print(out_stats[, c("group", "n", "R", "P")], row.names = FALSE)
