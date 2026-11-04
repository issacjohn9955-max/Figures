#!/usr/bin/env python3
"""Build the polar-plot input table from the TE x climate association result.

Definition used here (the TE-env analogue of "Shared / Unique" in the
reference panel):
  * a TE locus is *associated* with a climate variable when that
    (variable, locus) pair passes the per-variable FDR threshold, i.e. the
    pair is listed in te_locus_sig.csv;
  * Unique = the locus is significant for THAT variable and for no other
    variable (shared across the 8+ factors = 0);
  * Shared = the locus is significant for that variable AND for at least one
    other variable.
So Unique + Shared = the number of significant associations of that variable,
and the sum over variables equals the number of rows of te_locus_sig.csv.

Usage:
    python3 build_input.py --sig /path/to/te_locus_sig.csv \
            --out te_factor_shared_unique.tsv [--labels BIO_3=...,WIND=...]

Output columns: category, series, value  (series order: Shared, Unique)
Categories are written in decreasing order of total, which is also the
counter-clockwise draw order in plot_polar_shared.R.
"""
import argparse
import csv
import os
from collections import defaultdict

DEFAULT_LABELS = {
    "srad": "SRAD",
    "bio3": "BIO_3",
    "bio9": "BIO_9",
    "bio18": "BIO_18",
    "bio19": "BIO_19",
    "bio2": "BIO_2",
    "wind": "WIND",
    "elev": "ELEV",
    "dm": "DM",
    "rh_dry": "RH_DRY",
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sig", required=True, help="te_locus_sig.csv (variable,locus,rho,p,q)")
    ap.add_argument("--out", default="te_factor_shared_unique.tsv")
    ap.add_argument("--labels", default="", help="extra name=LABEL pairs, comma separated")
    args = ap.parse_args()

    labels = dict(DEFAULT_LABELS)
    if args.labels:
        for kv in args.labels.split(","):
            if "=" in kv:
                k, v = kv.split("=", 1)
                labels[k.strip()] = v.strip()

    loc2vars = defaultdict(set)
    var_count = defaultdict(int)
    with open(args.sig, encoding="utf-8-sig", newline="") as fh:
        for row in csv.DictReader(fh):
            var, loc = row["variable"].strip(), row["locus"].strip()
            loc2vars[loc].add(var)
            var_count[var] += 1

    rows = []
    for var in var_count:
        uniq = sum(1 for loc, vs in loc2vars.items() if var in vs and len(vs) == 1)
        shared = sum(1 for loc, vs in loc2vars.items() if var in vs and len(vs) > 1)
        rows.append((labels.get(var, var.upper()), var, uniq, shared, uniq + shared))

    rows.sort(key=lambda r: (-r[4], r[1]))
    with open(args.out, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, delimiter="\t", lineterminator="\n")
        w.writerow(["category", "series", "value"])
        for lab, var, uniq, shared, total in rows:
            w.writerow([lab, "Shared", shared])
            w.writerow([lab, "Unique", uniq])

    print(f"{'category':10s} {'variable':8s} {'unique':>7s} {'shared':>7s} {'total':>7s}")
    for lab, var, uniq, shared, total in rows:
        print(f"{lab:10s} {var:8s} {uniq:7d} {shared:7d} {total:7d}")
    print(f"\nloci: {len(loc2vars)}, associations: {sum(var_count.values())}")
    print("written:", os.path.abspath(args.out))


if __name__ == "__main__":
    main()
