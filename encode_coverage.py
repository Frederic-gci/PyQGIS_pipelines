#!/usr/bin/env python3

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
# TODO. Validate that wse contains "{sc_idx}"

# Hardcoded depth classes
classes = [0, 0.3, 0.6, 0.9, 1.2, 1.5]
suffixes = ["0to30cm", "30to60cm", "60to90cm",
            "90to120cm", "120to150cm", "over150cm"]

# Load the MNT
mnt = rasterio.open(args.mnt)
mnt_dat = mnt.read(1)

# The first data file profile will be used for shape, bounds, etc.
wse = rasterio.open(args.wse.format(sc_idx=1))

# TODO. Verify that the cell sizes match. If not, then resample MNT to get the match
# TODO. Verify that the WSE is totally contained in the MNT or raise error.

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
