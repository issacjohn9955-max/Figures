#!/usr/bin/env python3
"""V16 组合图的几何与产物校验。

只读 07_figures/R_v16 下的记录文件，不重新渲染，因此可以在 CI 或提交前秒级跑完。
检查四类内容：

1. 版式：画板比例、右侧面板是否完全避开圆图、四根箭头是否都落在 48 度开口内。
2. 产物：output_manifest.tsv 里每个文件的字节数与 sha256。
3. 位图：PNG 的 IHDR 尺寸是否等于 画板英寸 x dpi。
4. 矢量：PDF 的 MediaBox 是否等于 画板英寸 x 72。

用法：
    python3 check_combined_v16.py --project-dir ../
退出码：0 全部通过；1 有失败项。
"""

from __future__ import annotations

import argparse
import hashlib
import re
import struct
import sys
from pathlib import Path

OPENING_DEG = 48.0
OPENING_HALF = OPENING_DEG / 2.0
TRACK_OUTER_USER = 0.9975  # V15 最外圈（染色体标签带）外半径


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8") as handle:
        header = handle.readline().rstrip("\n").split("\t")
        return [dict(zip(header, line.rstrip("\n").split("\t"))) for line in handle if line.strip()]


def geometry_map(path: Path) -> dict[str, str]:
    return {row["item"]: row["value"] for row in read_tsv(path)}


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def png_size(path: Path) -> tuple[int, int]:
    with path.open("rb") as handle:
        header = handle.read(24)
    if header[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"不是 PNG：{path}")
    return struct.unpack(">II", header[16:24])


def pdf_mediabox(path: Path) -> tuple[float, float]:
    data = path.read_bytes()
    matches = re.findall(rb"/MediaBox\s*\[\s*([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s*\]", data)
    if not matches:
        raise ValueError(f"PDF 里找不到 MediaBox：{path}")
    x0, y0, x1, y1 = (float(v) for v in matches[0])
    return x1 - x0, y1 - y0


class Report:
    def __init__(self) -> None:
        self.rows: list[tuple[str, bool, str]] = []

    def check(self, name: str, ok: bool, detail: str = "") -> None:
        self.rows.append((name, bool(ok), detail))

    def render(self) -> bool:
        width = max(len(name) for name, _, _ in self.rows)
        for name, ok, detail in self.rows:
            print(f"  [{'PASS' if ok else 'FAIL'}] {name.ljust(width)}  {detail}")
        failed = [name for name, ok, _ in self.rows if not ok]
        print()
        if failed:
            print(f"结果：{len(failed)} 项失败 -> {', '.join(failed)}")
        else:
            print(f"结果：{len(self.rows)} 项全部通过")
        return not failed


def main() -> int:
    parser = argparse.ArgumentParser(description="校验 V16 组合图的版式与产物")
    parser.add_argument("--project-dir", default=str(Path(__file__).resolve().parent.parent))
    parser.add_argument("--out-dir", default=None)
    args = parser.parse_args()

    project = Path(args.project_dir).resolve()
    out_dir = Path(args.out_dir).resolve() if args.out_dir else project / "07_figures" / "R_v16"
    prefix = "chicken_GRCg7b_R_v16_combined_TE-callouts"

    geom_path = out_dir / f"{prefix}.figure_geometry.tsv"
    conn_path = out_dir / f"{prefix}.connectors.tsv"
    manifest_path = out_dir / f"{prefix}.output_manifest.tsv"
    for required in (geom_path, conn_path, manifest_path):
        if not required.exists():
            print(f"缺少记录文件：{required}", file=sys.stderr)
            return 1

    geom = geometry_map(geom_path)
    connectors = read_tsv(conn_path)
    report = Report()

    # --- 1. 版式 ---
    width_in = float(geom["composite_width_in"])
    height_in = float(geom["composite_height_in"])
    aspect = float(geom["aspect"])
    center_x = float(geom["circle_center_x_in"])
    center_y = float(geom["circle_center_y_in"])
    radius = float(geom["circle_radius_in"])
    panel_left = float(geom["panel_left_in"])
    panel_right = float(geom["panel_right_in"])
    dpi = int(float(geom["dpi"]))

    report.check("aspect 1.55–1.75", 1.55 <= aspect <= 1.75, f"{aspect:.2f}")
    report.check("圆图未被缩放", abs(float(geom["circos_width_in"]) - 9.8) < 1e-6,
                 f"V15 画布 {geom['circos_width_in']} in")
    report.check("面板避开圆图", panel_left > center_x + radius + 0.05,
                 f"左缘 {panel_left:.2f} in > 圆心+半径 {center_x + radius:.2f} in")
    report.check("面板在画板内", panel_right < width_in, f"右缘 {panel_right:.2f} < {width_in} in")

    # --- 2. 连接箭头：必须在开口楔形内，且完全在圆外 ---
    bad_tail, bad_head = [], []
    for row in connectors:
        angle = float(row["tail_angle_deg"])
        tail_radius = float(row["tail_radius_user"])
        if abs(angle - 90.0) > OPENING_HALF or tail_radius <= TRACK_OUTER_USER:
            bad_tail.append(f"{row['track']}({angle:.0f}°, r={tail_radius})")
        head_x = float(row["head_x_in"])
        head_y = float(row["head_y_in"])
        if head_x >= panel_left:
            bad_head.append(row["track"])
        else:
            # 箭头终点也不能落回圆内
            dx, dy = head_x - center_x, head_y - center_y
            if (dx * dx + dy * dy) ** 0.5 <= radius:
                bad_head.append(f"{row['track']}(终点在圆内)")

    report.check("箭头起点在 48° 开口内", not bad_tail, ", ".join(bad_tail) or f"{len(connectors)} 条")
    report.check("箭头终点在面板侧", not bad_head, ", ".join(bad_head) or f"{len(connectors)} 条")
    report.check("四类结构齐备", [r["track"] for r in connectors] == ["LINE", "LTR", "SINE", "DNA"],
                 " / ".join(r["track"] for r in connectors))

    # --- 3. 产物完整性 ---
    manifest = read_tsv(manifest_path)
    missing, mismatched = [], []
    for row in manifest:
        path = out_dir / row["file"]
        if not path.exists():
            missing.append(row["file"])
            continue
        if path.stat().st_size != int(row["bytes"]):
            mismatched.append(f"{row['file']}(字节数)")
            continue
        if sha256_of(path) != row["sha256"]:
            mismatched.append(f"{row['file']}(sha256)")
    report.check("产物齐备", not missing, ", ".join(missing) or f"{len(manifest)} 个文件")
    report.check("sha256 一致", not mismatched, ", ".join(mismatched) or "全部匹配")

    # --- 4. 位图与矢量尺寸 ---
    png_name = f"{prefix}.png"
    if any(row["file"] == png_name for row in manifest):
        pw, ph = png_size(out_dir / png_name)
        report.check("PNG 像素尺寸", (pw, ph) == (round(width_in * dpi), round(height_in * dpi)),
                     f"{pw}x{ph} px ({dpi} dpi)")
    pdf_name = f"{prefix}.pdf"
    if any(row["file"] == pdf_name for row in manifest):
        page_w, page_h = pdf_mediabox(out_dir / pdf_name)
        report.check("PDF 页面尺寸", abs(page_w - width_in * 72) < 0.5 and abs(page_h - height_in * 72) < 0.5,
                     f"{page_w:.1f}x{page_h:.1f} pt ({page_w / 72:.2f}x{page_h / 72:.2f} in)")
    svg_name = f"{prefix}.svg"
    if any(row["file"] == svg_name for row in manifest):
        report.check("SVG 存在", (out_dir / svg_name).stat().st_size > 0, f"{svg_name}")

    try:
        shown = out_dir.relative_to(project)
    except ValueError:
        shown = out_dir
    print(f"输出目录：{shown}")
    print()
    return 0 if report.render() else 1


if __name__ == "__main__":
    sys.exit(main())
