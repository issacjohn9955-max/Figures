#!/usr/bin/env Rscript
# =============================================================================
# te_ibe_mantel.R
#   复刻 Yuan et al. 2026 (Zool Res) Figure 3E / 3F：
#   IBD（地理隔离）与 IBE（环境隔离）—— FST/(1-FST) 对 地理距离 / 环境距离,
#   “自适应位点”与“中性位点”各一条线性回归 + 95% CI，图例给出 Mantel test r/p。
#
#   本实现用 TE（转座子插入存在剂量 0/1/2）替代原文的 SNP：
#     遗传分化 : 逐位点 Weir & Cockerham (1984) theta，成对群体按
#                ratio-of-averages（Σa / Σ(a+b+c)）汇总 —— 与 VCFtools 加权 FST 同一口径
#     自适应位点: 默认 LFMM2 genomic-control q < 0.05（任一环境变量）
#     中性位点  : 其余全部有变异 TE
#     地理距离  : 群体代表坐标的 Haversine 距离 (km)
#     环境距离  : 标准化环境变量的欧氏距离（与原文一致）
#     显著性    : Mantel test，9999 次群体标签置换（单侧 greater），同 vegan::mantel
#
#   用法（两种）:
#     Rscript te_ibe_mantel.R --cohort cn14 --outdir out_cn14      # 从头算
#     Rscript te_ibe_mantel.R --from-pairs out_cn14                # 只重画图（读已有表）
#
#   输入（默认从服务器 14_TE_403_downstream_20261030 下载，见 README）:
#     te_dosage.csv     个体 × TE 位点的存在剂量（0/1/2，已用 SNP 单倍型插补）
#     samples.tsv       个体 → 组、经纬度
#     environment.csv   个体 → 5 个标准化环境变量（组内共享）
#     te_lfmm_q.tsv     位点 × 变量的 LFMM2 q 值及 strict/exploratory 标记
# =============================================================================

suppressPackageStartupMessages({ library(ggplot2); library(grid) })

# ------------------------------- 参数解析 -----------------------------------
parse_args <- function(a) {
  o <- list(dosage = "raw/input/primary20/te_dosage.csv",
            samples = "raw/input/primary20/samples.tsv",
            env = "raw/input/primary20/environment.csv",
            evidence = "raw/integration/primary20_all_evidence.tsv.gz",
            outdir = ".", cohort = "cn14", rule = "lfmm", qcut = 0.05,
            adaptive_file = NULL, from_pairs = NULL, perm = 9999, seed = 1,
            freq = NULL, het = NULL, groups_file = NULL,
            dpi = 600, lab_x_km = "Distance (km)",
            lab_x_env = "Environmental distance")
  given <- character(); i <- 1
  while (i <= length(a)) {
    k <- gsub("-", "_", sub("^--", "", a[i])); v <- a[i + 1]
    if (!k %in% names(o)) stop("未知参数: ", a[i])
    o[[k]] <- v; given <- c(given, k); i <- i + 2
  }
  o$given <- given
  o$qcut <- as.numeric(o$qcut); o$perm <- as.integer(o$perm); o$dpi <- as.integer(o$dpi)
  o
}
opt <- parse_args(commandArgs(trailingOnly = TRUE))
dir.create(opt$outdir, showWarnings = FALSE, recursive = TRUE)

# 在本模块目录直接 `Rscript te_ibe_mantel.R` 时，自动使用随附的 cn14 群体级聚合表
if (is.null(opt$from_pairs) && !any(c("freq", "dosage") %in% opt$given) &&
    file.exists("input/cn14_group_freq.csv.gz")) {
  opt$freq <- "input/cn14_group_freq.csv.gz"
  opt$het <- "input/cn14_group_het.csv.gz"
  opt$groups_file <- "input/cn14_groups.tsv"
  if (is.null(opt$adaptive_file)) opt$adaptive_file <- "input/adaptive_loci_lfmm_q05.txt"
  message("[i] 未显式指定输入，使用本目录 input/ 下的 cn14 群体级聚合表")
}

# ------------------------------- 绘图函数 -----------------------------------
COL  <- c("Adaptive TE" = "#F8696B", "Neutral TE" = "#00BFBF")   # 主色（取自原文）
fmt_p <- function(p) if (p < 0.001) "p < 0.001" else sprintf("p = %.2f", p)

# 手绘图例：上两行 Mantel 结果（空心圆 + 同色文字 + 浅色 key 底块），
# 下两行位点类别（实心圆 + 黑字）。全部用数据坐标，随面板范围自适应。
panel_legend <- function(xr, yr, lab_adapt, lab_neut) {
  x0 <- xr[1] + diff(xr) * 0.455; dx <- diff(xr); dy <- diff(yr)
  y1 <- yr[2] - dy * 0.075
  keyw <- dx * 0.013; keyh <- dy * 0.028; txt_x <- x0 + dx * 0.030
  rows <- y1 - dy * c(0, 0.075); out <- list()
  for (k in 1:2) {
    col <- unname(COL[k]); lab <- c(lab_adapt, lab_neut)[k]
    out[[length(out) + 1]] <- annotate("rect", xmin = x0 - keyw, xmax = x0 + keyw,
      ymin = rows[k] - keyh, ymax = rows[k] + keyh, fill = col, alpha = 0.22, colour = NA)
    out[[length(out) + 1]] <- annotate("point", x = x0, y = rows[k], shape = 21,
      size = 2.3, stroke = 0.55, fill = "white", colour = col)
    out[[length(out) + 1]] <- annotate("text", x = txt_x, y = rows[k], hjust = 0,
      label = lab, colour = col, size = 3.15)
  }
  rows2 <- y1 - dy * c(0.170, 0.222)
  for (k in 1:2) {
    out[[length(out) + 1]] <- annotate("point", x = x0, y = rows2[k], shape = 16,
      size = 2.0, colour = unname(COL[k]))
    out[[length(out) + 1]] <- annotate("text", x = txt_x, y = rows2[k], hjust = 0,
      label = names(COL)[k], colour = "grey10", size = 3.15)
  }
  out
}

make_panel <- function(dat, xvar, xlab, mantel_rows) {
  xr <- range(dat[[xvar]], na.rm = TRUE); xr <- xr + c(-0.02, 0.03) * diff(xr)
  yr <- range(dat$fst_lin, na.rm = TRUE); yr <- c(min(0, yr[1]), yr[2] * 1.12)
  la <- sprintf("Mantel test r = %.2f, %s", mantel_rows$r[1], fmt_p(mantel_rows$p[1]))
  ln <- sprintf("Mantel test r = %.2f, %s", mantel_rows$r[2], fmt_p(mantel_rows$p[2]))
  ggplot(dat, aes(x = .data[[xvar]], y = fst_lin, colour = class, fill = class)) +
    geom_smooth(method = "lm", formula = y ~ x, se = TRUE, level = 0.95,
                linewidth = 1.5, alpha = 0.28, show.legend = FALSE) +
    geom_point(shape = 21, size = 1.30, stroke = 0.38, alpha = 0.9, show.legend = FALSE) +
    scale_colour_manual(values = COL, guide = "none") +
    scale_fill_manual(values = COL, guide = "none") +
    scale_x_continuous(expand = expansion(mult = c(0.01, 0.02))) +
    scale_y_continuous(expand = expansion(mult = c(0.01, 0.02))) +
    labs(x = xlab, y = expression(F[ST] * "/(1-" * F[ST] * ")")) +
    coord_cartesian(xlim = xr, ylim = yr) +
    theme_classic(base_size = 14, base_family = "Helvetica") +
    theme(axis.line = element_line(linewidth = 0.9, colour = "black"),
          axis.ticks = element_line(linewidth = 0.9, colour = "black"),
          axis.ticks.length = unit(2.2, "pt"),
          axis.text = element_text(size = 12, colour = "grey10"),
          axis.title = element_text(size = 13.5, face = "bold", colour = "black"),
          plot.margin = margin(6, 8, 4, 6), panel.background = element_blank()) +
    panel_legend(xr, yr, la, ln)
}

render_panels <- function(pairs_tab, mantel_tab, opt) {
  pairs_tab <- pairs_tab[is.finite(pairs_tab$fst_lin), ]
  pairs_tab$class <- factor(pairs_tab$class, levels = names(COL))
  pE <- make_panel(pairs_tab, "geo_km", opt$lab_x_km, mantel_tab[mantel_tab$dist == "geo", ])
  pF <- make_panel(pairs_tab, "env_dist", opt$lab_x_env, mantel_tab[mantel_tab$dist == "env", ])
  W <- 11.1; H <- 5.06
  open_png <- function(file) {
    # 跨平台：macOS 用 quartz，Linux 用 cairo，Windows 用 windows；失败再退回默认设备
    types <- if (.Platform$OS.type == "windows") "windows" else
             if (identical(Sys.info()[["sysname"]], "Darwin")) c("quartz", "cairo") else "cairo"
    for (tp in types) {
      ok <- tryCatch({
        suppressWarnings(png(file, width = W, height = H, units = "in",
                             res = opt$dpi, type = tp))
        grDevices::dev.cur() > 1
      }, error = function(e) FALSE)
      if (isTRUE(ok)) return(invisible(TRUE))
    }
    png(file, width = W, height = H, units = "in", res = opt$dpi)
    invisible(TRUE)
  }
  open_device <- function(file, dev) {
    if (dev == "pdf") pdf(file, width = W, height = H, family = "Helvetica") else open_png(file)
  }
  draw <- function(file, dev) {
    open_device(file, dev)
    grid.newpage()
    pushViewport(viewport(layout = grid.layout(1, 2)))
    for (k in 1:2) {
      pushViewport(viewport(layout.pos.col = k))
      print(if (k == 1) pE else pF, newpage = FALSE)
      grid.text(c("E", "F")[k], x = unit(0.015, "npc"), y = unit(0.975, "npc"),
                just = c("left", "top"),
                gp = gpar(fontsize = 26, fontface = "bold", fontfamily = "Helvetica"))
      popViewport()
    }
    popViewport(); invisible(dev.off())
  }
  draw(file.path(opt$outdir, "te_ibe_adaptive_neutral.png"), "png")
  draw(file.path(opt$outdir, "te_ibe_adaptive_neutral.pdf"), "pdf")
  cat(sprintf("      %s/te_ibe_adaptive_neutral.{png,pdf}\n", opt$outdir))
}

# ------------------------- 模式 A：只重画图 ---------------------------------
if (!is.null(opt$from_pairs)) {
  pairs_tab  <- read.delim(file.path(opt$from_pairs, "te_ibe_pairs.tsv"))
  mantel_tab <- read.delim(file.path(opt$from_pairs, "te_ibe_mantel.tsv"))
  opt$outdir <- if (opt$outdir == ".") opt$from_pairs else opt$outdir
  render_panels(pairs_tab, mantel_tab, opt)
  cat("[ok] 已用已有成对表重绘图\n"); quit(save = "no")
}

# ============================== 数据装配 =====================================
# 两种入口：
#   ① 个体级剂量表（原始流程，需 samples + environment + evidence）
#   ② 群体级频率/杂合度矩阵（随仓库提交的聚合表，可离线完整重跑）
if (!is.null(opt$freq)) {
  cat("[1/6] 读取群体级频率表 ...\n")
  Pm <- as.matrix(read.csv(opt$freq, row.names = 1, check.names = FALSE))
  Hm <- as.matrix(read.csv(opt$het, row.names = 1, check.names = FALSE))
  gt <- read.delim(opt$groups_file, check.names = FALSE)
  groups <- gt$group
  stopifnot(all(groups %in% rownames(Pm)), all(groups %in% rownames(Hm)),
            identical(colnames(Pm), colnames(Hm)))
  P <- Pm[groups, , drop = FALSE]; H <- Hm[groups, , drop = FALSE]
  n <- gt$n_ind; lon <- gt$lon; lat <- gt$lat
  envg <- gt[, c("bio3", "bio15", "bio18", "wind", "srad"), drop = FALSE]
  K <- length(groups)
  cat(sprintf("      群体级模式 K=%2d 组, L=%4d 位点\n", K, ncol(P)))
  if (is.null(opt$adaptive_file)) stop("--freq 模式必须用 --adaptive-file 指定自适应位点表")
  adapt <- setdiff(readLines(opt$adaptive_file), c("", "locus"))
  is_adap <- colnames(P) %in% adapt
  rule_txt <- sprintf("外部位点表 (n=%d)", length(adapt))
  cat(sprintf("      规则: %s → 自适应 %d / 中性 %d 位点\n", rule_txt, sum(is_adap), sum(!is_adap)))
} else {
  cat("[1/6] 读取数据 ...\n")
  dos <- read.csv(opt$dosage, row.names = 1, check.names = FALSE)
  smp <- read.delim(opt$samples, check.names = FALSE, quote = "")
  env <- read.csv(opt$env, row.names = 1, check.names = FALSE)
  stopifnot(nrow(dos) == nrow(smp), all(rownames(dos) == smp$sample))
  X <- as.matrix(dos) / 2                     # 等位基因频率尺度 0-1
  grp_all <- smp$group

  # 队列：all = 20 组（含 3 个原鸡种 + 3 个外源商业品种，与服务器 LFMM 主队列一致）
  #       domestic = 去掉 3 个原鸡种；cn14 = 只保留中国地方鸡种
  JUNGLE  <- c("35_灰原鸡", "39_绿原鸡", "41_锡兰原鸡")
  FOREIGN <- c("31_Corish", "34_洛岛红", "36_白来航")
  groups <- switch(opt$cohort,
    all      = unique(grp_all),
    domestic = setdiff(unique(grp_all), JUNGLE),
    cn14     = setdiff(unique(grp_all), c(JUNGLE, FOREIGN)),
    stop("cohort 只能是 all / domestic / cn14"))
  groups <- groups[order(as.integer(sub("_.*", "", groups)))]
  keep_s <- grp_all %in% groups
  X <- X[keep_s, , drop = FALSE]; g <- grp_all[keep_s]; smp <- smp[keep_s, , drop = FALSE]
  K <- length(groups)
  cat(sprintf("      队列 %-8s K=%2d 组, n=%3d 个体, L=%4d 位点\n",
              opt$cohort, K, length(g), ncol(X)))

  cat("[2/6] 定义自适应 / 中性位点 ...\n")
  if (!is.null(opt$adaptive_file)) {
    adapt <- setdiff(readLines(opt$adaptive_file), c("", "locus"))
    is_adap <- colnames(X) %in% adapt
    rule_txt <- sprintf("外部位点表 (n=%d)", length(adapt))
  } else {
    ev <- read.delim(opt$evidence)
    ev <- ev[ev$variable %in% c("bio3", "bio15", "bio18", "wind", "srad"), ]
    loci <- colnames(X)
    agg <- function(col, fun) {
      z <- aggregate(ev[[col]], list(locus = ev$locus), FUN = fun)
      z$x[match(loci, z$locus)]
    }
    if (opt$rule == "lfmm") {
      is_adap <- agg("lfmm_k10_q_gc", min) < opt$qcut
      rule_txt <- sprintf("LFMM2 K10 GC-q < %g（5 个变量取最小）", opt$qcut)
    } else if (opt$rule == "pc3") {
      is_adap <- agg("pc3_q_common_observed", min) < opt$qcut
      rule_txt <- sprintf("PC3 偏 Spearman q < %g", opt$qcut)
    } else if (opt$rule == "strict") {
      is_adap <- agg("strict_evidence", max) %in% TRUE
      rule_txt <- "严格跨方法核心（LFMM + PC3 + PC3geo 同向 q<0.05）"
    } else if (opt$rule == "exploratory") {
      is_adap <- agg("exploratory_group_q10", max) %in% TRUE
      rule_txt <- "探索集合（组水平 q<0.10 且同向）"
    } else stop("rule 只能是 lfmm / pc3 / strict / exploratory")
  }
  is_adap[is.na(is_adap)] <- FALSE
  cat(sprintf("      规则: %s → 自适应 %d / 中性 %d 位点\n", rule_txt, sum(is_adap), sum(!is_adap)))

  # 群体频率、观测杂合度、样本量
  P <- t(sapply(groups, function(k) colMeans(X[g == k, , drop = FALSE])))
  H <- t(sapply(groups, function(k) colMeans(X[g == k, , drop = FALSE] == 0.5)))
  n <- sapply(groups, function(k) sum(g == k))
  lon <- tapply(smp$reviewed_longitude, g, mean)[groups]
  lat <- tapply(smp$reviewed_latitude, g, mean)[groups]
  envg <- aggregate(env[keep_s, , drop = FALSE], by = list(group = g), FUN = mean)
  envg <- envg[match(groups, envg$group), -1, drop = FALSE]
}
is_adap[is.na(is_adap)] <- FALSE
if (sum(is_adap) < 10) warning("自适应位点少于 10 个，成对 FST 极不稳定，仅供版式演示")

# ---------------------- Weir & Cockerham 成对 FST ---------------------------# ---------------------- Weir & Cockerham 成对 FST ---------------------------
# 说明：h 用“观测杂合度”。Balding-Nichols 模拟显示，用 2p(1-p) 近似会高估低分化
# 情形（theta=0.05、n=6/6 时 +17%），改用观测杂合度后偏差约 -1%。
wc_pair <- function(p1, p2, h1, h2, n1, n2) {
  r <- 2; nb <- (n1 + n2) / 2
  nc <- (r * nb - (n1^2 + n2^2) / (r * nb)) / (r - 1)
  pb <- (n1 * p1 + n2 * p2) / (n1 + n2)
  s2 <- (n1 * (p1 - pb)^2 + n2 * (p2 - pb)^2) / ((r - 1) * nb)
  hb <- (n1 * h1 + n2 * h2) / (r * nb)
  a  <- (nb / nc) * (s2 - (pb * (1 - pb) - ((r - 1) / r) * s2 - hb / 4) / (nb - 1))
  b  <- (nb / (nb - 1)) * (pb * (1 - pb) - ((r - 1) / r) * s2 - ((2 * nb - 1) / (4 * nb)) * hb)
  list(a = a, den = a + b + hb / 2)
}
fst_pair <- function(i, j, mask) {
  o <- wc_pair(P[i, mask], P[j, mask], H[i, mask], H[j, mask], n[i], n[j])
  ok <- is.finite(o$a) & is.finite(o$den) & o$den > 1e-12
  if (!any(ok)) return(NA_real_)
  sum(o$a[ok]) / sum(o$den[ok])              # ratio-of-averages
}

cat("[3/6] 计算成对 FST ...\n")
F_ad <- matrix(NA_real_, K, K); F_ne <- matrix(NA_real_, K, K)
for (i in 1:(K - 1)) for (j in (i + 1):K) {
  F_ad[i, j] <- F_ad[j, i] <- fst_pair(i, j, is_adap)
  F_ne[i, j] <- F_ne[j, i] <- fst_pair(i, j, !is_adap)
}
dimnames(F_ad) <- dimnames(F_ne) <- list(groups, groups)

# --------------------------- 地理 / 环境距离 --------------------------------
hav <- function(lo1, la1, lo2, la2) {
  R <- 6371.0088; a1 <- la1 * pi / 180; b1 <- lo1 * pi / 180
  a2 <- la2 * pi / 180; b2 <- lo2 * pi / 180
  h <- sin((a2 - a1) / 2)^2 + cos(a1) * cos(a2) * sin((b2 - b1) / 2)^2
  2 * R * asin(pmin(1, sqrt(h)))
}
GEO <- outer(seq_len(K), seq_len(K), Vectorize(function(i, j) hav(lon[i], lat[i], lon[j], lat[j])))
ENV <- as.matrix(dist(envg))
dimnames(GEO) <- dimnames(ENV) <- list(groups, groups)

# ------------------------------- Mantel -------------------------------------
mantel_test <- function(A, B, perm = 9999, seed = 1) {
  iu <- upper.tri(A); x <- A[iu]; y <- B[iu]
  ok <- is.finite(x) & is.finite(y); x <- x[ok]; y <- y[ok]
  r0 <- cor(x, y); set.seed(seed)
  k <- nrow(A); st <- numeric(perm)
  for (b in seq_len(perm)) { p <- sample(k); st[b] <- cor(x, B[p, p][iu][ok]) }
  c(r = r0, p = (sum(st >= r0) + 1) / (perm + 1), n = length(x))
}

cat(sprintf("[4/6] Mantel tests (%d 次置换) ...\n", opt$perm))
lin_ad <- F_ad / (1 - F_ad); lin_ne <- F_ne / (1 - F_ne)
res <- list()
for (cls in c("adaptive", "neutral")) {
  lin <- if (cls == "adaptive") lin_ad else lin_ne
  for (dt in c("geo", "env")) {
    m <- mantel_test(lin, if (dt == "geo") GEO else ENV, opt$perm, opt$seed)
    res[[length(res) + 1]] <- data.frame(class = cls, dist = dt,
      r = unname(m["r"]), p = unname(m["p"]), n_pairs = unname(m["n"]),
      n_loci = if (cls == "adaptive") sum(is_adap) else sum(!is_adap))
  }
}
mantel_tab <- do.call(rbind, res); print(mantel_tab, row.names = FALSE)

# ------------------------------ 输出表 --------------------------------------
iu <- upper.tri(GEO)
pairs_tab <- rbind(
  data.frame(class = "Adaptive TE", pair = outer(groups, groups, paste, sep = " | ")[iu],
             fst = F_ad[iu], fst_lin = lin_ad[iu], geo_km = GEO[iu], env_dist = ENV[iu]),
  data.frame(class = "Neutral TE", pair = outer(groups, groups, paste, sep = " | ")[iu],
             fst = F_ne[iu], fst_lin = lin_ne[iu], geo_km = GEO[iu], env_dist = ENV[iu]))
pairs_tab$class <- factor(pairs_tab$class, levels = names(COL))
write.table(pairs_tab, file.path(opt$outdir, "te_ibe_pairs.tsv"), sep = "\t",
            quote = FALSE, row.names = FALSE)
mantel_tab$cohort <- opt$cohort; mantel_tab$rule <- rule_txt
write.table(mantel_tab[, c("cohort", "class", "dist", "r", "p", "n_pairs", "n_loci", "rule")],
            file.path(opt$outdir, "te_ibe_mantel.tsv"), sep = "\t", quote = FALSE, row.names = FALSE)
groups_tab <- data.frame(group = groups, n_ind = n, lon = as.numeric(lon), lat = as.numeric(lat),
                         envg, check.names = FALSE)
write.table(groups_tab, file.path(opt$outdir, "te_ibe_groups.tsv"), sep = "\t",
            quote = FALSE, row.names = FALSE)

# ------------------------------- 出图 ---------------------------------------
cat("[5/6] 绘图 ...\n")
render_panels(pairs_tab, mantel_tab, opt)
cat("[6/6] 输出: te_ibe_pairs.tsv / te_ibe_mantel.tsv / te_ibe_groups.tsv / te_ibe_adaptive_neutral.{png,pdf}\n")
