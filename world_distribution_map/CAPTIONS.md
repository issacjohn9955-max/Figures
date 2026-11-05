# Figure caption

Ready-to-paste caption for the two-panel distribution map. **The numbers below
describe the shipped demo table (20 world + 29 Chinese entries, fabricated
coordinates) — replace them with your real counts before submission.**

---

## 图　样本的地理来源：全球面板与中国放大面板

> **图 X　样本的地理来源。** (a) 全球面板：每个空心圆代表一条采样记录，按经度分列于地图两侧的
> 样本名称以 0.3 pt 细线指向对应点位，避免文字压盖地理要素。(b) 中国放大面板：范围
> 73–136°E、17–55°N，同样的左右分列标注规则。底图为等距圆柱投影（按纬度余弦修正显示
> 纵横比），陆地为浅灰、国界与省界为 0.18 pt 细线，南海断续线单独绘制。示例数据共
> 49 条记录（全球 20 条、中国 29 条），坐标仅用于版式演示，不代表真实品种分布。

**English**

> **Figure X. Geographic origin of the samples.** (a) Global panel: each open circle is
> one sampling record; sample names are set outside the map in two columns ordered by
> latitude and connected to their points by 0.3 pt leader lines, so no text covers the
> geography. (b) Enlarged China panel (73–136°E, 17–55°N) with the same two-column
> labelling rule. Basemap is a plate-carrée projection with a latitude-cosine display
> aspect; land is light grey, national and provincial boundaries are 0.18 pt hairlines,
> and the South China Sea dashed line is drawn separately. The shipped demo table
> contains 49 records (20 global, 29 Chinese) with fabricated coordinates for layout
> demonstration only.

---

## Before submission

* **审图号**：所有含中国国界/省界的图，中文投稿与学位论文都要换成
  [标准地图服务](http://bzdt.ch.mnr.gov.cn/) 的底图，并在图注末尾写审图号
  （如“审图号：GS(2019)1822 号”）；英文投稿按期刊要求处理。
* **替换示例数据**：`samples.tsv` 里的 49 条坐标是编的，正文引用前必须换成真实采样表，
  并同步改图注里的数量。
* **标签长度**：`sample` 列控制在 18 个字符内；超长名字会顶到相邻面板的标签列。
* **配色**：若期刊要求彩色，点位颜色从 `style/palettes.json` 取 `categorical` 色位，
  不要另造 hex；本模块默认白底黑边点是为了黑白打印可读。
* **投影声明**：图注里不要写“等积投影”——本模板是显示用的经纬度网格，量面积会有偏差。
