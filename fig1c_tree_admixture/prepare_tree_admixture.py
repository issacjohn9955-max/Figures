#!/usr/bin/env python3
"""Prepare input for a tree + admixture figure (Fig1C).

Writes to /tmp/f1c:
  snp_subset.lfmm   140 individuals x N loci, LEA 9-coded genotype matrix
  breed_freq.tsv    13 breeds x N loci allele frequencies (for the NJ tree)
  samples.tsv       sample / breed / group
  summary.json
"""
import json
import os

import numpy as np
import pandas as pd

R12 = "/data/shine_work/12_TE_SNP_imputation_20261030/results"
OUT = "/tmp/f1c"
os.makedirs(OUT, exist_ok=True)

rng = np.random.default_rng(20261110)
N_SNP = 40000

env = pd.read_csv(f"{R12}/06_complete/samples_with_environment.tsv", sep="\t")
prim = env[env["primary_analysis_status"].astype(str).str.startswith("include")].copy()
EXCLUDE = ["Corish", "洛岛红", "白来航", "灰原鸡", "绿原鸡", "锡兰原鸡"]
prim = prim[~prim["breed"].astype(str).isin(EXCLUDE)]
prim = prim[~prim["canonical_sample_id"].astype(str).str.startswith("BC")]
ids = prim["canonical_sample_id"].astype(str).tolist()
breed = prim.set_index(prim["canonical_sample_id"].astype(str))["breed"].to_dict()
print(f"[cohort] {len(ids)} samples / {len(set(breed.values()))} breeds")

WORK = f"{R12}/09_snp_structure/work"
fam = pd.read_csv(f"{WORK}/snp_ld.pruned.fam", sep=r"\s+", header=None)
fam_ids = fam[1].astype(str).tolist()

with open(f"{WORK}/snp_ld.pruned.bed", "rb") as fh:
    assert fh.read(3) == b"\x6c\x1b\x01"
    raw = np.fromfile(fh, dtype=np.uint8)

n_all = len(fam_ids)
nbytes = (n_all + 3) // 4
n_snp = raw.size // nbytes
raw = raw[: n_snp * nbytes].reshape(n_snp, nbytes)

lut = np.zeros((256, 4), dtype=np.int8)
for b in range(256):
    for k in range(4):
        lut[b, k] = {0: 2, 1: -1, 2: 1, 3: 0}[(b >> (2 * k)) & 3]
G = lut[raw].reshape(n_snp, nbytes * 4)[:, :n_all].T.astype(np.float32)   # samples x snps
G[G < 0] = np.nan
del raw, lut

registry = {name: i for i, name in enumerate(fam_ids)}
def pos(s):
    return registry[s] if s in registry else registry[s.split("__")[-1]]
G = G[[pos(s) for s in ids], :]

# MAF + missingness screen
n_obs = (~np.isnan(G)).sum(axis=0)
mean = np.nansum(G, axis=0) / np.maximum(n_obs, 1)
p = mean / 2
keep = (n_obs >= 0.9 * G.shape[0]) & (p >= 0.05) & (p <= 0.95)
G = G[:, keep]
print(f"[screen] {keep.sum()} loci pass")

pick = np.sort(rng.choice(G.shape[1], size=min(N_SNP, G.shape[1]), replace=False))
G = G[:, pick]
# mean-impute, round back to 0/1/2 (LEA wants integers)
mu = np.nanmean(G, axis=0)
G = np.where(np.isnan(G), mu, G)
G = np.rint(G).astype(np.int8)
print(f"[matrix] {G.shape}")

with open(f"{OUT}/snp_subset.lfmm", "w") as fh:
    for row in G:
        fh.write(" ".join(map(str, row.tolist())) + "\n")

df = pd.DataFrame(np.asarray(G == 1) + 2 * np.asarray(G == 2), dtype=float)
df.insert(0, "breed", [breed[s] for s in ids])
freq = df.groupby("breed").mean().round(4)
freq.to_csv(f"{OUT}/breed_freq.tsv", sep="\t")

pd.DataFrame({"sample": ids, "breed": [breed[s] for s in ids]}).to_csv(
    f"{OUT}/samples.tsv", sep="\t", index=False)

json.dump({"samples": len(ids), "breeds": int(freq.shape[0]), "loci": int(G.shape[1])},
          open(f"{OUT}/summary.json", "w"), indent=2)
print(freq.shape)
