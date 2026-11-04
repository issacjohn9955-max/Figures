# China sampling — adopted WGS individuals, province and point level

Where the adopted whole-genome-sequencing samples of Chinese indigenous chicken
breeds come from. Two views of the same table:

* **province choropleth** (`china_sampling_map.*`) — four-class fill, MaxEnt-map
  visual language;
* **point map** (`china_sampling_points.*`) — every collection site plotted at its
  county/city coordinates, labelled with the place name, plus a zoom inset for the
  crowded southwest cluster.

![Province map](china_sampling_map.png)

![Point map](china_sampling_points.png)

## Data provenance

Source workbook: `label1029.xlsx` (research workspace, **not** committed here).

Selection rule, as specified by the project owner:

1. rows whose summary-sheet marker is shaded blue (`FF0070C0`), **or**
2. rows tagged as in-house / 本实验室数据.

That yields **26 blue rows**. Two of them are duplicate re-uploads of an earlier
row (sheets note “与第57行重复，不重复采纳” / “与第63行重复”), so the point figure
uses **24 records → 21 sites → 363 individuals**; the province figure still counts
those two rows and shows **367**.

| Province | Individuals | Records |
|---|---:|---:|
| Henan 河南 | 93 | 8 |
| Guizhou 贵州 | 78 | 7 |
| Gansu 甘肃 | 46 | 2 |
| Heilongjiang 黑龙江 | 30 | 1 |
| Anhui 安徽 | 29 | 2 |
| Hainan 海南 | 29 | 1 |
| Hunan 湖南 | 22 | 2 |
| Beijing 北京 | 20 | 1 |
| Fujian 福建 | 10 | 1 |
| Hubei 湖北 | 10 | 1 |

Class breaks: province map `1–19 / 20–49 / ≥50`; point map `1–9 / 10–19 / 20–29 / ≥30`.

## Coordinates

`china_sampling_sites.tsv` carries one row per collection site:

| column | meaning |
|---|---|
| `lon`, `lat` | coordinate of the county / city government seat (DataV GeoAtlas `center`), or the representative point of a named production region |
| `precision` | `county`, `city`, `prefecture`, `region` — `region` rows are drawn as **dashed rings** because the record is only “江汉平原” or “中原产区” level |
| `dx`, `dy` | label offset in degrees, hand-tuned so the 21 numbers do not collide |
| `individuals`, `records` | adopted individuals and how many blue rows were merged into this site |

Merged duplicates: 淅川乌骨鸡 (2 rows), 正阳三黄鸡 (2), 固始鸡 (2). Duplicate
re-uploads dropped: 贵州黔东南小香鸡 row 58, 威宁鸡 row 62.

Sites whose record is only region-level:

| id | breed | placed at | reason |
|---|---|---|---|
| 15 | 河南斗鸡 | Kaifeng 114.34 E, 34.80 N | record says only “河南省（中原斗鸡产区）” |
| 19 | 江汉鸡 | Xiantao 113.45 E, 30.36 N | record says only “湖北省江汉平原” |
| 7 | 黔东南小香鸡 | Kaili 107.98 E, 26.58 N | prefecture-level record |

## Files

| Path | Role |
|---|---|
| `china_sampling_counts.tsv` | Province aggregates — input of the choropleth |
| `china_sampling_sites.tsv` | Site coordinates + short place label + label offset — input of the point map |
| `plot_china_sampling_map.py` | Choropleth renderer (matplotlib + GeoJSON) |
| `plot_china_sampling_points.py` | Point-map renderer (same stack, plus zoom inset) |
| `data/*.geojson` | Boundary inputs (see *Boundary data*) |
| `china_sampling_map.png/.pdf` | Province map, EN; `_zh` variant also present |
| `china_sampling_points.png/.pdf` | Point map (Chinese labels, since breed names are Chinese) |

## Usage

```bash
python3 plot_china_sampling_map.py --lang en      # province map
python3 plot_china_sampling_map.py --lang zh
python3 plot_china_sampling_points.py             # point map + inset
```

Options: `--counts` / `--sites`, `--geo`, `--maritime`, `--outdir`, `--stem`.
Edit the TSV and re-run; label offsets live in the same file.

## Boundary data

* `data/china_provinces.geojson` — province polygons from the Alibaba DataV
  GeoAtlas service (`100000_full.json`, AMap-derived); its `100000_JD` feature is
  the nine-dash line and is drawn separately.
* `data/china_maritime.geojson` — maritime boundary as `MultiLineString`, from
  [cnmetlab/cnmaps-data](https://github.com/cnmetlab/cnmaps-data).

`data/` is git-ignored, so fetch both after cloning:

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

* Province map 149 × 154 mm, point map 189 × 156 mm; white background, no grid,
  no gradients or shadows.
* Text 5.5–7 pt, PingFang SC / Heiti SC for Chinese, Arial/DejaVu Sans fallback.
* Point map uses the house palette from
  [1577377232/Genomics-Figure-Styles](https://github.com/1577377232/Genomics-Figure-Styles)
  (`palettes.json` → `pangenome_spectrum`, the theme's default):
  class ramp `#B4AD74 → #7BB6AC → #5899B2 → #386C8C` (four steps of the six-colour
  cycle, ordered light → dark), text/border `#273746`, province lines `#A9B2BB`.
  No invented colours; the choropleth keeps the MaxEnt ramp because it mirrors the
  reference figure it reproduces.
* Marker colour and area both encode the individual count (redundant encoding);
  `region`-level records get a dashed ring.
* Sites are labelled with the 2–3 character place name (黄山, 淅川, 长汀 …) rather
  than a number or the breed name: it fits at national scale, while the breed ↔
  place mapping stays in the source table.
* National border is a thick stroke under the fills (the fill covers its inner
  half), so border and fill share one vector path and can never misregister.
* The southwest cluster gets a zoom inset (`103.4–111.0 E, 24.1–28.6 N`) with the
  extent boxed on the main map; its numbers are moved into the inset only.
* Export: PNG 600 dpi + vector PDF with editable text (`pdf.fonttype = 42`).

## Privacy

Only aggregates and site coordinates are committed — no accession IDs, no sample
metadata, no sequencing data. The source workbook stays in the research workspace.
