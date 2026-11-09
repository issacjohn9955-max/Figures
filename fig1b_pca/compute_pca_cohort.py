#!/usr/bin/env python3
"""Recompute SNP and TE PCA on the SAME primary cohort (249 individuals / 20 groups).

Runs on danding. Writes small score/variance tables to /tmp/f1b_pca.
"""
import json
import os

import numpy as np
import pandas as pd

R12 = "/data/shine_work/12_TE_SNP_imputation_20261030/results"
OUT = "/tmp/f1b_pca"
COHORT = os.environ.get("COHORT", "all")          # all | local
OUT = f"/tmp/f1b_pca/{COHORT}"
os.makedirs(OUT, exist_ok=True)

# ---------------------------------------------------------------- cohort
env = pd.read_csv(f"{R12}/06_complete/samples_with_environment.tsv", sep="\t")
prim = env[env["primary_analysis_status"].astype(str).str.startswith("include")].copy()
EXCLUDE = ["Corish", "洛岛红", "白来航", "灰原鸡", "绿原鸡", "锡兰原鸡"]   # commercial + wild
if COHORT.startswith("local"):
    prim = prim[~prim["breed"].astype(str).isin(EXCLUDE)].copy()
if COHORT == "local140":
    # 惠阳胡须鸡 BC01-BC06: batch outlier in both marker sets (see repo notes)
    prim = prim[~prim["canonical_sample_id"].astype(str).str.startswith("BC")].copy()
ids = prim["canonical_sample_id"].astype(str).tolist()
print(f"[cohort] {len(ids)} samples / {prim['coordinate_index'].nunique()} groups")


def pca(genotype, sample_ids, maf_min=0.05, n_pc=10):
    """genotype: (n_samples, n_loci) dosage 0/1/2 with NaN for missing."""
    g = genotype.astype(np.float32)
    # locus mean / frequency from observed calls
    obs = ~np.isnan(g)
    n_obs = obs.sum(axis=0)
    mean = np.nansum(g, axis=0) / np.maximum(n_obs, 1)
    keep = (n_obs >= 0.8 * g.shape[0]) & (mean / 2 >= maf_min) & (mean / 2 <= 1 - maf_min)
    g = g[:, keep]
    mean = mean[keep]
    # mean-impute, then centre
    g = np.where(np.isnan(g), mean, g)
    g -= g.mean(axis=0, keepdims=True)
    gram = g @ g.T                                   # n x n, cheap
    eigval, eigvec = np.linalg.eigh(gram.astype(np.float64))
    order = np.argsort(eigval)[::-1]
    eigval, eigvec = eigval[order], eigvec[:, order]
    eigval = np.clip(eigval, 0, None)
    scores = eigvec * np.sqrt(eigval)
    pve = eigval / eigval.sum()
    # sign convention: PC1 loads positively on the majority
    for j in range(scores.shape[1]):
        if scores[:, j].sum() < 0:
            scores[:, j] *= -1
    k = min(n_pc, scores.shape[1])
    out = pd.DataFrame(scores[:, :k], columns=[f"PC{i+1}" for i in range(k)])
    out.insert(0, "sample", sample_ids)
    var = pd.DataFrame({
        "PC": [f"PC{i+1}" for i in range(k)],
        "eigenvalue": eigval[:k],
        "PVE": pve[:k],
        "cumulative_PVE": np.cumsum(pve[:k]),
    })
    return out, var, int(keep.sum())


# ---------------------------------------------------------------- SNP (PLINK bed)
WORK = f"{R12}/09_snp_structure/work"
fam = pd.read_csv(f"{WORK}/snp_ld.pruned.fam", sep=r"\s+", header=None)
fam_ids = fam[1].astype(str).tolist()

with open(f"{WORK}/snp_ld.pruned.bed", "rb") as fh:
    assert fh.read(3) == b"\x6c\x1b\x01", "not a PLINK bed"
    raw = np.fromfile(fh, dtype=np.uint8)

n_all = len(fam_ids)
nbytes = (n_all + 3) // 4
n_snp = raw.size // nbytes
raw = raw[: n_snp * nbytes].reshape(n_snp, nbytes)
print(f"[snp] {n_snp} variants x {n_all} samples")

lut = np.zeros((256, 4), dtype=np.int8)
for b in range(256):
    for k in range(4):
        code = (b >> (2 * k)) & 3
        lut[b, k] = {0: 2, 1: -1, 2: 1, 3: 0}[code]   # -1 = missing
g_snp = lut[raw].reshape(n_snp, nbytes * 4)[:, :n_all].T.astype(np.float32)
g_snp[g_snp < 0] = np.nan
del raw, lut

def fam_pos(sample_id, registry):
    """fam/sample columns sometimes drop the RJF__ prefix."""
    if sample_id in registry:
        return registry[sample_id]
    alt = str(sample_id).split("__")[-1]
    if alt in registry:
        return registry[alt]
    raise KeyError(sample_id)


fam_registry = {}
for i, f in enumerate(fam_ids):
    fam_registry.setdefault(f, i)
idx = [fam_pos(s, fam_registry) for s in ids]
g_snp = g_snp[idx, :]
snp_scores, snp_var, n_keep_snp = pca(g_snp, ids)
print(f"[snp] kept {n_keep_snp} variants after MAF filter")
snp_scores.to_csv(f"{OUT}/pca_snp_scores.tsv", sep="\t", index=False)
snp_var.to_csv(f"{OUT}/pca_snp_variance.tsv", sep="\t", index=False)
del g_snp

# ---------------------------------------------------------------- TE
te = pd.read_csv(f"{R12}/06_complete/te_alt_dosage_individual_complete.csv",
                 encoding="utf-8-sig")
te["sample"] = te["sample"].astype(str)
te = te.set_index("sample")
te_registry = {name: i for i, name in enumerate(te.index)}
te = te.iloc[[fam_pos(s, te_registry) for s in ids], :]
te.index = ids
g_te = te.to_numpy(dtype=np.float32)
print(f"[te] {g_te.shape[0]} samples x {g_te.shape[1]} loci")

te_scores, te_var, n_keep_te = pca(g_te, ids)
print(f"[te] kept {n_keep_te} loci after MAF filter")
te_scores.to_csv(f"{OUT}/pca_te_scores.tsv", sep="\t", index=False)
te_var.to_csv(f"{OUT}/pca_te_variance.tsv", sep="\t", index=False)

# ---------------------------------------------------------------- metadata
meta = prim[["canonical_sample_id", "breed", "coordinate_index",
             "reviewed_longitude", "reviewed_latitude"]].copy()
meta.columns = ["sample", "breed", "group", "lon", "lat"]
meta["sample"] = meta["sample"].astype(str)
meta.to_csv(f"{OUT}/samples_meta.tsv", sep="\t", index=False)

summary = {
    "cohort_samples": len(ids),
    "cohort_groups": int(prim["coordinate_index"].nunique()),
    "snp_variants_used": n_keep_snp,
    "te_loci_used": n_keep_te,
    "snp_pc1_pve": float(snp_var.PVE.iloc[0]),
    "snp_pc2_pve": float(snp_var.PVE.iloc[1]),
    "te_pc1_pve": float(te_var.PVE.iloc[0]),
    "te_pc2_pve": float(te_var.PVE.iloc[1]),
}
json.dump(summary, open(f"{OUT}/summary.json", "w"), indent=2)
print(json.dumps(summary, indent=2))
