import glob, json, os
import numpy as np
from PIL import Image

TIF = "/data/shine_work/01_workflow/01_worldclim/data/tif"
OUT = "/tmp/f2env"
os.makedirs(OUT, exist_ok=True)

LON0, LON1, LAT0, LAT1 = 73.0, 135.5, 17.5, 54.5
RES = 1 / 12.0

def crop(path):
    a = np.array(Image.open(path), dtype=np.float32)
    nrow, ncol = a.shape
    c0 = int(round((LON0 + 180) / RES)); c1 = int(round((LON1 + 180) / RES))
    r0 = int(round((90 - LAT1) / RES)); r1 = int(round((90 - LAT0) / RES))
    return a[r0:r1, c0:c1]

def save(name, arr):
    np.save(f"{OUT}/{name}.npy", arr.astype(np.float32))
    print(name, arr.shape, float(np.nanmin(arr)), float(np.nanmax(arr)))

save("bio3", crop(f"{TIF}/wc2.1_5m_bio_3.tif"))
save("bio18", crop(f"{TIF}/wc2.1_5m_bio_18.tif"))

months = sorted(glob.glob(f"{TIF}/wc2.1_5m_srad_*.tif"))
print("srad months", len(months))
stack = np.stack([crop(p) for p in months])
srad_kj = np.nanmean(stack, axis=0)
save("srad", srad_kj * 0.0115741)   # kJ m-2 day-1 -> W m-2

json.dump({"lon0": LON0, "lon1": LON0 + srad_kj.shape[1] * RES,
           "lat0": LAT0, "lat1": LAT0 + srad_kj.shape[0] * RES,
           "res": RES, "shape": list(srad_kj.shape)},
          open(f"{OUT}/extent.json", "w"), indent=2)
print(open(f"{OUT}/extent.json").read())
