# China sampling map — adopted WGS individuals per province

A four-class choropleth of China showing where the adopted whole-genome-sequencing
samples of Chinese indigenous chicken breeds come from. Same visual language as the
MaxEnt suitability maps commonly used in Chinese ecology papers (blank → olive →
orange → red, thin grey province borders, black national border, nine-dash line and
South China Sea islands), repurposed for sampling effort instead of habitat
suitability.

![China sampling map](china_sampling_map.png)

## Data provenance

Source workbook: `label1029.xlsx` (research workspace, **not** committed here).

Selection rule, as specified by the project owner:

1. rows whose summary-sheet marker is shaded blue (`FF0070C0`), **or**
2. rows tagged as in-house / 本实验室数据.

Result: **26 breed records · 22 breed entries · 367 individuals · 10 provinces**.
Rows without an accession number (in-house data) are counted by their recorded
individual count; otherwise the count is capped by the number of listed
SRR/ERR/CRR accessions.

| Province | Individuals | Records | Breeds |
|---|---:|---:|---:|
| Henan 河南 | 93 | 8 | 5 |
| Guizhou 贵州 | 78 | 7 | 6 |
| Gansu 甘肃 | 46 | 2 | 2 |
| Heilongjiang 黑龙江 | 30 | 1 | 1 |
| Anhui 安徽 | 29 | 2 | 2 |
| Hainan 海南 | 29 | 1 | 1 |
| Hunan 湖南 | 22 | 2 | 2 |
| Beijing 北京 | 20 | 1 | 1 |
| Fujian 福建 | 10 | 1 | 1 |
| Hubei 湖北 | 10 | 1 | 1 |

Class breaks: `1–19` / `20–49` / `≥50` individuals; provinces outside the table are
`None` and drawn in light grey.

## Files

| Path | Role |
|---|---|
| `china_sampling_counts.tsv` | Aggregated counts only — the single input of the figure |
| `plot_china_sampling_map.py` | Renderer (matplotlib + GeoJSON, no GDAL/geopandas) |
| `data/*.geojson` | Boundary inputs (see *Boundary data* below) |
| `china_sampling_map.png/.pdf` | English figure, 600 dpi / vector |
| `china_sampling_map_zh.png/.pdf` | Chinese figure, same layout |

## Usage

```bash
python3 plot_china_sampling_map.py --lang en      # -> china_sampling_map.png + .pdf
python3 plot_china_sampling_map.py --lang zh      # -> china_sampling_map_zh.*
```

Options: `--counts`, `--geo`, `--maritime`, `--outdir`, `--stem`.
Edit `china_sampling_counts.tsv` (add `dx`/`dy` label offsets per province) and
re-run; nothing else needs touching.

## Boundary data

* `data/china_provinces.geojson` — province polygons from the Alibaba DataV
  GeoAtlas service (`100000_full.json`, AMap-derived); its `100000_JD` feature is
  the nine-dash line and is drawn separately.
* `data/china_maritime.geojson` — maritime boundary as `MultiLineString`, from
  [cnmetlab/cnmaps-data](https://github.com/cnmetlab/cnmaps-data).

`**/data/` is git-ignored by this repository, so fetch the two files after cloning:

```bash
mkdir -p data && cd data
curl -Lo china_provinces.geojson \
  https://geo.datav.aliyun.com/areas_v3/bound/100000_full.json
curl -Lo china_maritime.geojson \
  https://raw.githubusercontent.com/cnmetlab/cnmaps-data/main/cnmaps_data/data/datasets/administrative/amap/maritime/100000.geojson
```

For journal submission inside China, replace them with the standard map service
boundary (`bzdt.ch.mnr.gov.cn`) and print its approval number (审图号).

## Style notes

* Canvas 149 × 154 mm, white background, no grid, no gradients or shadows.
* Text 5.5–7 pt, Arial/Helvetica with Liberation Sans/DejaVu Sans fallback;
  Chinese variant uses PingFang SC / Heiti SC.
* Four-class ramp `#EFEFEF / #B0A81E / #E8891B / #C8102E` — the MaxEnt convention,
  chosen because the target figure language is the suitability map.
* National border is a thick stroke under the fills (the fill covers its inner
  half), so border and fill share one vector path and can never misregister.
* Labels carry a thin halo; provinces smaller than the label get a leader line.
* Export: PNG 600 dpi + vector PDF with editable text (`pdf.fonttype = 42`).

## Privacy

Only per-province aggregates are committed. Individual accession lists, sample
metadata and the source workbook stay in the research workspace; nothing
individual-level is pushed to this style repository.
