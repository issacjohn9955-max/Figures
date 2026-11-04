# Figures

Publication-ready figure code with its rendered outputs. Each folder is one figure:
a script, a small input table, and the exported PNG (600 dpi) + vector PDF.

## Contents

| Folder | Figure | Outputs |
|---|---|---|
| [`china_sampling_map/`](china_sampling_map/README.md) | Adopted WGS individuals of Chinese indigenous chicken breeds — province choropleth **and** county-level point map with zoom inset | `fig1_province_counts.png/.pdf`, `fig2_sampling_sites.png/.pdf`, plus `CAPTIONS.md` |
| [`corr_ci_scatter/`](corr_ci_scatter/README.md) | Method agreement per environmental variable — points coloured by variable, one linear fit + 95 % confidence band each, `R` / `P` / `(n)` block on the right (Figure 4A layout) | `corr_ci_scatter.png/.pdf`, `corr_ci_scatter_stats.tsv` |
| [`niche_overlap_null/`](niche_overlap_null/README.md) | Observed vs null niche-overlap index — one panel per environmental variable: two permutation histograms (Schoener's D / Hellinger's I) with the observed value pinned by a dashed rule and an axis triangle | `niche_overlap_null.png/.pdf`, plus `CAPTIONS.md` |
| [`gea_driver_radar/`](gea_driver_radar/README.md) | Driver radar — one spoke per environmental variable, one polygon per evidence layer, on a shared count axis (Figure 3C layout); the paper reproduction **and** the ChickenTE TE version | `radar_paper_fig3c.png/.pdf`, `radar_chickente_te.png/.pdf` |
| [`gea_marginal_scatter/`](gea_marginal_scatter/README.md) | Genotype–environment association screen — one panel per environmental variable: RDA correlation vs LFMM −log10(P), with marginal −log10(P) histogram and cumulative percentage | `gea_marginal_scatter.png/.pdf` |
| [`pca_climate_zone/`](pca_climate_zone/README.md) | PCA of Chinese indigenous chickens coloured by agricultural climate zone (colour + shape double encoding, horizontal two-row legend above the panel) — TE-insertion version **and** SNP version, same layout | `fig_pca_te_climate.png/.pdf`, `fig_pca_snp_climate.png/.pdf`, `preview_6zone_synthetic.png/.pdf` (synthetic layout check), plus `CAPTIONS.md` |
| [`te_ibe_adaptive_neutral/`](te_ibe_adaptive_neutral/README.md) | IBD vs IBE — FST/(1−FST) against geographic distance (E) and environmental distance (F), adaptive vs neutral TEs, each with a linear fit + 95% CI and a Mantel r/p legend | `te_ibe_adaptive_neutral.png/.pdf` |

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
cd corr_ci_scatter
Rscript plot_corr_ci_panel.R --input te_method_corr.tsv --out corr_ci_scatter \
        --xlab '~bold("|"*italic(z)[RDA]*"|")' --ylab '~bold("|"*rho*"|")'

cd ../china_sampling_map
python3 plot_china_sampling_map.py --lang en   # province choropleth
python3 plot_china_sampling_map.py --lang zh
python3 plot_china_sampling_points.py          # county-level point map

cd gea_marginal_scatter
Rscript plot_gea_panels.R --input example_gea_stats.tsv \
        --labels example_labels.tsv --out gea_marginal_scatter

cd pca_climate_zone
Rscript plot_pca_climate_zone.R --scores data/pca_te_scores.tsv \
        --variance data/pca_te_variance.tsv --out fig_pca_te_climate \
        --palette chromatic_nc --tag B --width-mm 160 --height-mm 111
Rscript make_synthetic_preview.R               # 6-zone layout check (synthetic)
```

Requirements: Python 3.9+, `numpy`, `matplotlib` for the maps (no GDAL/geopandas
needed — the China boundary is read straight from GeoJSON); R ≥ 4.1 with
`ggplot2`, `patchwork` and `scales` for the GEA panels.

## Style snapshot

`style/` is a read-only snapshot of the [`figure-style`](style/README.md) kit
(`theme.json`, `palettes.json`, `ggplot2_theme.R`, `matplotlib.mplstyle`) so that
cloning this repository is enough to regenerate a figure. Modules look for the
style layer in this order: `$FIGURE_STYLE_DIR` → this repository's `style/`
snapshot → a sibling `figure-style/` checkout.

Because it is a snapshot it does **not** update itself. After editing the source
kit, refresh it and re-render the affected figures:

```bash
bash style/sync_from_figure_style.sh          # copy + record the source commit in style/VENDORED.md
bash style/sync_from_figure_style.sh --check  # compare only; exit 1 on drift
```
