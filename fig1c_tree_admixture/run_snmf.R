suppressMessages(library(LEA))
setwd("/tmp/f1c")
for (k in 2:5) {
  obj <- snmf("snp_subset.lfmm", K = k, entropy = TRUE, repetitions = 2,
              project = "new", CPU = 4, seed = 20261110)
  ce <- cross.entropy(obj, K = k)
  best <- which.min(ce)
  Q <- Q(obj, K = k, run = best)
  write.table(round(Q, 5), sprintf("Q_k%d.tsv", k), sep = "\t",
              quote = FALSE, row.names = FALSE, col.names = FALSE)
  cat(sprintf("K=%d best=%d ce=%.2f\n", k, best, min(ce)))
  saveRDS(obj, sprintf("snmf_k%d.rds", k))
}
cat("DONE\n")
