#!/usr/bin/env Rscript
# =============================================================================
# make_example_data.R
#
# Generates the synthetic table used by plot_gea_panels.R. The numbers are
# made up: -log10(P) is drawn from an exponential so that most SNPs sit near
# P = 1 with a long right tail, RDA correlation is weakly tied to it, and about
# a fifth of the SNPs are pushed to r ~ 0 to reproduce the dense floor that
# dominates real GEA plots.
#
# Output:
#   example_gea_stats.tsv   trait, snp, r, p
#   example_labels.tsv      trait, label
# =============================================================================
set.seed(20260301)

traits <- data.frame(
  trait = c("BARE", "BIO_2", "CROPLAND", "PREC_08",
            "SHRUBS", "SRAD_11", "TREES", "WATER"),
  label = c("Areas with minimal vegetation", "Mean diurnal range",
            "Land used for crops", "Precipitation in August",
            "Woody plants", "Solar radiation in November",
            "Land covered by tree foliage", "Areas covered by lakes and rivers"),
  n     = c(2500, 2600, 2400, 2450, 2200, 2400, 2500, 2550),
  rate  = c(1.9, 1.45, 1.7, 1.8, 2.4, 1.7, 1.7, 1.35),
  xmax  = c(5, 10, 7, 6, 4, 7, 7, 10),
  stringsAsFactors = FALSE
)

out <- vector("list", nrow(traits))
for (i in seq_len(nrow(traits))) {
  n <- traits$n[i]
  x <- c(rexp(n, traits$rate[i]), runif(round(n * 0.006), 2, traits$xmax[i]))
  x <- pmin(x, traits$xmax[i])

  r <- 0.16 + 0.012 * x + rnorm(length(x), 0, 0.045)
  r <- pmin(pmax(r, 0.004), 0.5)

  floor_idx <- sample(length(x), round(0.22 * length(x)))
  r[floor_idx] <- runif(length(floor_idx), 0, 0.014)

  out[[i]] <- data.frame(
    trait = traits$trait[i],
    snp   = sprintf("rs%07d", seq_along(x) + i * 100000L),
    r     = signif(r, 4),
    p     = signif(10^(-x), 4),
    stringsAsFactors = FALSE
  )
}

stats <- do.call(rbind, out)
write.table(stats, "example_gea_stats.tsv", sep = "\t", quote = FALSE, row.names = FALSE)
write.table(traits[, c("trait", "label")], "example_labels.tsv",
            sep = "\t", quote = FALSE, row.names = FALSE)
message("wrote ", nrow(stats), " rows in example_gea_stats.tsv")
