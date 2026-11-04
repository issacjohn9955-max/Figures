#!/usr/bin/env python3
"""Build the input table for plot_corr_ci_panel.R from the TE-environment run.

Two independent screens are compared per environmental variable, mirroring the
logic of Yuan et al. (2026) Figure 4A (F_ST windows vs |s_XP-EHH| windows):

  x = |z-scored RDA loading| of the TE locus on the variable's dominant axis
  y = |Spearman rho| between TE presence/absence and that variable (29 breeds)

Points = the top 1% of loci on the RDA axis, per variable (n = 157), which is
the same "top 1% evidence" rule used for the windows in the paper.

Axis -> variable assignment is taken verbatim from te_env_out/rda_summary.txt
(correlation between sample scores and each climate variable):

    bio18 RDA1 .798 | bio19 RDA4 .549 | bio2 RDA6 -.756
    bio3  RDA3 -.626 | bio9 RDA8 .546 | srad RDA2 -.609

Six variables are kept so that each one sits on a different RDA axis; that also
keeps the panel inside the six-category colour rule of the house style.

Usage
    python3 build_te_method_corr.py --base ~/Desktop/ChickenTE/severdata/te_env_out
"""
import argparse
import os

import numpy as np
import pandas as pd
from scipy.stats import pearsonr

AXIS = {                      # variable -> dominant RDA axis (see docstring)
    "bio18": "RDA1", "bio19": "RDA4", "bio2": "RDA6",
    "bio3": "RDA3", "bio9": "RDA8", "srad": "RDA2",
}
LABEL = {
    "bio18": "BIO_18", "bio19": "BIO_19", "bio2": "BIO_2",
    "bio3": "BIO_3", "bio9": "BIO_9", "srad": "SRAD",
}
TOP_FRAC = 0.01


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=os.path.expanduser(
        "~/Desktop/ChickenTE/severdata/te_env_out"))
    ap.add_argument("--out", default="te_method_corr.tsv")
    args = ap.parse_args()

    load = pd.read_csv(os.path.join(args.base, "rda_locus_loadings.csv"),
                       encoding="utf-8-sig")
    assoc = pd.read_csv(os.path.join(args.base, "te_locus_assoc.csv"),
                        encoding="utf-8-sig")

    rows, report = [], []
    for var, axis in AXIS.items():
        z = load[["locus", axis + "_z"]].rename(columns={axis + "_z": "z"}).dropna()
        z["abs_z"] = z["z"].abs()
        thr = z["abs_z"].quantile(1 - TOP_FRAC)
        top = z[z["abs_z"] >= thr]
        a = assoc.loc[assoc["variable"] == var, ["locus", "rho"]]
        m = top.merge(a, on="locus")
        x = m["abs_z"].to_numpy()
        y = m["rho"].abs().to_numpy()
        r, p = pearsonr(x, y)
        report.append((var, axis, len(m), thr, r, p))
        rows.append(pd.DataFrame({"group": LABEL[var], "x": x, "y": y}))

    out = pd.concat(rows, ignore_index=True)
    out.to_csv(args.out, sep="\t", index=False, float_format="%.5g")
    print(f"wrote {args.out}: {len(out)} rows, {out['group'].nunique()} groups")
    print(f"{'variable':8s} {'axis':5s} {'n':>4s} {'cut':>6s} {'R':>8s} {'P':>10s}")
    for var, axis, n, thr, r, p in report:
        print(f"{var:8s} {axis:5s} {n:4d} {thr:6.2f} {r:+8.3f} {p:10.2e}")


if __name__ == "__main__":
    main()
