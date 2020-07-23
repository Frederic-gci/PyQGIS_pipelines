#!/usr/bin/env python3
import sys
import rasterio
import numpy as np
import argparse
import utilities as utils

# from https://gist.github.com/lpinner/13244b5c589cda4fbdfa89b30a44005b#file-resample_raster-py
from resample_raster import resample_raster_xy as resample

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
parser.add_argument("--output_dir",
                     help="Output directory",
                     required=False,
                     default="/processing/output/")
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

# Get some mnt and wse metadata
with rasterio.open(args.mnt) as mnt:
    mnt_profile = mnt.profile
    mnt_bounds = mnt.bounds
    mnt_res = mnt.res

with rasterio.open(args.wse.format(sc_idx=1)) as wse:
    wse_profile = wse.profile
    wse_bounds = wse.bounds
    wse_res = wse.res
    wse_shape = wse.shape

# Validate MNT and WSE files
if (wse_profile['crs'] != 32198 or mnt_profile['crs'] != 32198):
    exit("MNT and WSE files must in EPSG:32198 projection (NAD83 Quebec Lambert).")
if (mnt_bounds.left > wse_bounds.left or
    mnt_bounds.right < wse_bounds.left or
    mnt_bounds.bottom > wse_bounds.bottom or
        mnt_bounds.top < wse_bounds.top):
    exit("MNT extent should encompass WSE extent")
if (wse_res[0] != 1 or wse_res[1] != 1):
    print("Encode_coverage: WSE file cells are not 1m x 1m.")
if (mnt_res[0] != 1 or mnt_res[1] != 1):
    print("Encode_coverage: Original MNT file cells are not 1m x 1m.")

# Extract the MNT data corresponding to the WSE rectangle.
with rasterio.open(args.mnt) as mnt:
    if (mnt_res[0] != wse_res[0] or mnt_res[1] != wse_res[1]):
        print(
            "Encode_coverage: MNT cell sizes differ from WSE cell sizes, " +
            "the MNT will be resampled to match WSE.")
        x_scale = wse_res[0] / mnt_res[0]
        y_scale = wse_res[1] / mnt_res[1]
        with resample(mnt, x_scale=x_scale, y_scale=y_scale) as scaled_mnt:
            wse_rect_window = rasterio.windows.from_bounds(
                *wse_bounds, transform=scaled_mnt.profile['transform']
            )
            mnt_rect = scaled_mnt.read(1, window=wse_rect_window)
    else:
        wse_rect_window = rasterio.windows.from_bounds(
            *wse_bounds, transform=mnt.profile['transform'])
        mnt_rect = mnt.read(1, window=wse_rect_window)

bands = [np.full(shape=wse.shape, fill_value=255, dtype=np.uint8)
         for i in range(len(classes))]

for sc_idx in range(1, args.scenarios + 1):
    data_path = args.wse.format(sc_idx=sc_idx)
    print(f'Encode_coverage: {utils.now()} Processing {data_path}')
    data_file = rasterio.open(data_path)
    data = data_file.read(1)
    for class_idx in range(len(classes)):
        bands[class_idx] = np.where(
            np.greater(data, mnt_rect + classes[class_idx]),
            np.minimum(bands[class_idx], sc_idx),
            bands[class_idx])

for class_idx in range(len(classes)):
    output_file = rasterio.open(
        f'{args.output_dir}/{args.model}_{suffixes[class_idx]}.tif',
        'w',
        driver='GTiff',
        width=wse_profile['width'],
        height=wse_profile['height'],
        count=1,
        dtype=np.uint8,
        crs=wse_profile['crs'],
        transform=wse_profile['transform'],
        nodata=int(255),
        compress='deflate'
    )
    output_file.write(bands[class_idx], 1)
    output_file.close
