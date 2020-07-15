#!/usr/bin/env python3
import sys
import rasterio
import numpy as np
import argparse

# Parameter definitions
parser = argparse.ArgumentParser()
parser.add_argument("--mnt",
                    help="Path to the MNT file.",
                    required=True)
parser.add_argument("--wse",
                    default='{sc_idx}',
                    help="Pattern of path to wse files, where '%(default)s' " +
                    "will be replaced by the scenario index.",
                    required=True)
parser.add_argument("--scenarios",
                    help="Number of scenarios.",
                    type=int,
                    required=True)
parser.add_argument("--model",
                    help="Model name (will be used for output file names)",
                    required=True)
args = parser.parse_args()

# Parameter validation
pattern = '{sc_idx}'
if(pattern not in args.wse):
    exit(
        "The WSE argument must be a pattern that contains '{sc_idx}', " +
        "which will be replaced by the scenario index.")

# Hardcoded depth classes
classes = [0, 0.3, 0.6, 0.9, 1.2, 1.5]
suffixes = ["0to30cm", "30to60cm", "60to90cm",
            "90to120cm", "120to150cm", "over150cm"]

mnt = rasterio.open(args.mnt)
wse = rasterio.open(args.wse.format(sc_idx=1))

# Validate MNT and WSE files
if (wse.crs != 32198 or mnt.crs != 32198):
    exit("MNT and WSE files must in EPSG:32198 projection (NAD83 Quebec Lambert).")
if (mnt.bounds.left > wse.bounds.left or
    mnt.bounds.right < wse.bounds.left or
    mnt.bounds.bottom > wse.bounds.bottom or
        mnt.bounds.top < mnt.bounds.top):
    exit("MNT extent should encompass WSE extent")
if (wse.res[0] != 1 or wse.res[1] != -1):
    print("Encode_coverage: WSE file cells are not 1m x 1m.")
if (mnt.res[0] != 1 or mnt.res[1] != -1):
    print("Encode_coverage: Original MNT file cells are not 1m x 1m.")

# If MNT cell sizes do not match WSE cell sizes, then resample MNT
if (mnt.res[0] != wse.res[0] or mnt.res[1] != wse.res[1]):
    print(
        "encode_coverage: MNT cell sizes differ from WSE cell sizes, " +
        "the MNT will be resampled to match WSE.")
# TODO. When MNT cell size does not match WSE cell sizes, resample MNT.

# Extract the MNT data corresponding to the WSE rectangle.
wse_rect_window = rasterio.windows.from_bounds(
    *wse.bounds, transform=mnt.transform)
mnt_rect = mnt.read(1, window=wse_rect_window)

bands = [np.full(shape=wse.shape, fill_value=255, dtype=np.uint8)
         for i in range(len(classes))]

for sc_idx in range(1, args.scenarios + 1):
    data_path = args.wse.format(sc_idx=sc_idx)
    print(f'Processing {data_path}')
    data_file = rasterio.open(data_path)
    data = data_file.read(1)
    for class_idx in range(len(classes)):
        bands[class_idx] = np.where(
            np.greater(data, mnt_rect + classes[class_idx]),
            np.minimum(bands[class_idx], sc_idx),
            bands[class_idx])

for class_idx in range(len(classes)):
    output_file = rasterio.open(
        f'/processing/output/{args.model}_{suffixes[class_idx]}.tif',
        'w',
        driver='GTiff',
        width=wse.width,
        height=wse.height,
        count=1,
        dtype=np.uint8,
        crs=wse.crs,
        transform=wse.transform,
        nodata=int(255),
        compress='deflate'
    )
    output_file.write(bands[class_idx], 1)
    output_file.close
