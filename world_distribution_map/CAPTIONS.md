# Figure captions

**最终版（投稿用，2026-11-05 定稿）**：`fig_china_real_world_china.png` / `.pdf`
（真实数据：21 个采样点、363 只个体、24 条记录、10 个省份；世界面板只作定位，中国面板带品种标注，无图内标题）。

后面另附**版式示例**（合成数据）的图注，只用于演示底图与配色，不要用于正文。

---

## 图 X　中国地方鸡种采样点的地理分布（最终版）

> **图 X　中国地方鸡种采样点的地理分布。** (a) 世界面板：中国范围内的 21 个采样点以空心圆标出，
> 方框标出 (b) 的放大范围。(b) 中国放大面板（73–136°E，17–55°N）：品种名排在图外侧两列、
> 按纬度从北到南排列，以 0.3 pt 细线指向对应点位；圆面积与该点采纳的个体数成正比（2–40 只）。
> 共 363 只个体、24 条品种记录、10 个省份。底图为 Natural Earth 1:50 m 晕渲栅格，叠加国界、
> 省界与南海断续线；投影为经纬度网格（按纬度余弦修正显示纵横比），不是等积投影。

**English**

> **Figure X. Geographic distribution of the sampling sites.** (a) World panel: the 21
> sampling sites in China are marked with open circles and the box outlines the area
> enlarged in (b). (b) Enlarged China panel (73–136°E, 17–55°N): breed names are set
> outside the map in two columns ordered from north to south and connected to their sites
> by 0.3 pt leader lines; circle area is proportional to the number of adopted
> individuals at that site (2–40). In total 363 individuals from 24 breed records across
> 10 provinces. Basemap: Natural Earth 1:50 m shaded relief with national and provincial
> boundaries and the South China Sea dashed line; the projection is a plate carrée grid
> with a latitude-cosine display aspect, not an equal-area projection.

---

## 版式示例（合成数据，仅演示，勿用于正文）

`fig_world_distribution.png/.pdf`（白底）与 `fig_world_distribution_relief.png/.pdf`（彩色）
用的是 `samples.tsv` 里 49 条**编造**的坐标（全球 20 条 + 中国 29 条），只演示版式。

> **图 Y　样本的地理来源（版式示例）。** (a) 全球面板：每个空心圆代表一条记录，样本名称
> 排在两侧、按纬度排序并用细线指回点位。(b) 中国放大面板。示例数据共 49 条记录，坐标仅用于
> 版式演示，不代表真实分布。

---

## Before submission

* **审图号**：所有含中国国界/省界的图，中文投稿与学位论文都要换成
  [标准地图服务](http://bzdt.ch.mnr.gov.cn/) 的底图，并在图注末尾写审图号
  （如“审图号：GS(2019)1822 号”）；英文投稿按期刊要求处理。Natural Earth 晕渲底图同样不满足这一要求。
* **换数据**：`samples.tsv` 的示例坐标不能当真；真实数据用 `samples_china_real.tsv`
  （由 `../china_sampling_map/china_sampling_sites.tsv` 转出），数量变了记得同步图注。
* **标签长度**：`sample` 列控制在 18 个字符内；超长名字会顶到相邻面板的标签列。
* **配色**：数据元素的颜色从 `style/palettes.json` 取 `categorical` 色位，不要另造 hex；
  本图用白底黑边点，是为了黑白打印也能看清。
* **投影声明**：图注里不要写“等积投影”——本模板是显示用的经纬度网格，量面积会有偏差。
