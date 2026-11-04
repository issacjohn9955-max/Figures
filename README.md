# Figures

Publication-ready figure code with its rendered outputs. Each folder is one figure:
a script, a small input table, and the exported PNG (600 dpi) + vector PDF.

## Contents

| Folder | Figure | Outputs |
|---|---|---|
| [`china_sampling_map/`](china_sampling_map/README.md) | Adopted WGS individuals of Chinese indigenous chicken breeds — province choropleth **and** county-level point map with zoom inset | `fig1_province_counts.png/.pdf`, `fig2_sampling_sites.png/.pdf`, plus `CAPTIONS.md` |
| [`gea_marginal_scatter/`](gea_marginal_scatter/README.md) | Genotype–environment association screen — one panel per environmental variable: RDA correlation vs LFMM −log10(P), with marginal −log10(P) histogram and cumulative percentage | `gea_marginal_scatter.png/.pdf` |

## Conventions

* Every figure folder has its own `README.md` stating **data provenance** and the
  exact selection rule used, so a figure can never be mistaken for a different
  dataset.
* Only aggregated or derived tables are committed — no individual-level records,
  raw sequencing data or unpublished metadata.
* Boundary data is downloaded by the script's documented `curl` commands rather
  than committed (see each module's *Boundary data* section).
* Exports: PNG at 600 dpi for preview and vector PDF with editable text for
  layout work; 5.5–7 pt type, white background, no gradients or shadows.

## Re-running a figure

```bash
cd china_sampling_map
python3 plot_china_sampling_map.py --lang en   # province choropleth
python3 plot_china_sampling_map.py --lang zh
python3 plot_china_sampling_points.py          # county-level point map

cd gea_marginal_scatter
Rscript plot_gea_panels.R --input example_gea_stats.tsv \
        --labels example_labels.tsv --out gea_marginal_scatter
```

Requirements: Python 3.9+, `numpy`, `matplotlib` for the maps (no GDAL/geopandas
needed — the China boundary is read straight from GeoJSON); R ≥ 4.1 with
`ggplot2`, `patchwork` and `scales` for the GEA panels.
