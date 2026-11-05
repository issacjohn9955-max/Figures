#!/usr/bin/env bash
# Rebuild data/relief/NE1_50M_SR_W.jpg from Natural Earth (public domain).
#
#   bash tools/fetch_relief.sh
#
# Downloads the 1:50m shaded-relief raster (88 MB zip), then downsamples it to
# 5400 x 2700 (2.5 MB JPEG) so the repository stays small.  The script only
# needs curl + unzip + Pillow; run it when the committed JPEG has to be
# regenerated, not for ordinary figure rebuilds.
set -euo pipefail
cd "$(dirname "$0")/.."

TMP=$(mktemp -d)
curl -L --fail -A 'Mozilla/5.0' -o "$TMP/ne1.zip" \
  "https://naciscdn.org/naturalearth/50m/raster/NE1_50M_SR_W.zip"
unzip -q -o "$TMP/ne1.zip" -d "$TMP"
python3 - "$TMP/NE1_50M_SR_W/NE1_50M_SR_W.tif" <<'PY'
import sys
from PIL import Image
im = Image.open(sys.argv[1]).convert("RGB").resize((5400, 2700), Image.LANCZOS)
im.save("data/relief/NE1_50M_SR_W.jpg", quality=88, optimize=True)
print("wrote data/relief/NE1_50M_SR_W.jpg")
PY
rm -rf "$TMP"
