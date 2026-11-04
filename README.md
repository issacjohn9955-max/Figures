# Figures

Publication-ready figure code with its rendered outputs. Each folder is one figure:
a script, a small input table, and the exported PNG (600 dpi) + vector PDF.

## Contents

| Folder | Figure | Outputs |
|---|---|---|
| [`china_sampling_map/`](china_sampling_map/README.md) | Adopted WGS individuals per province, Chinese indigenous chicken breeds — four-class choropleth of China with nine-dash line | `china_sampling_map.png/.pdf` (EN), `china_sampling_map_zh.png/.pdf` (ZH) |

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
python3 plot_china_sampling_map.py --lang en
python3 plot_china_sampling_map.py --lang zh
```

Requirements: Python 3.9+, `numpy`, `matplotlib`. No GDAL/geopandas needed — the
China boundary is read straight from GeoJSON.
