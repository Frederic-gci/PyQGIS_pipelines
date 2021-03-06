#!/usr/bin/env python3
import sys
import rasterio
import numpy as np
import argparse
import utilities as utils

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
parser.add_argument("--v1_length",
                    help="Number of values of the first variable",
                    required=True,
                    type=int)
parser.add_argument("--direction",
                    help="1: v1 increase first (sc1=(1,1), sc2=(2,1)); " +
                         "2: v2 increase first (sc1=(1,1), sc2=(1,2))",
                    required=False,
                    default=2,
                    type=int)
args = parser.parse_args()

# Parameter validation
pattern = '{sc_idx}'
if(pattern not in args.wse):
    exit(
        "The WSE argument must be a pattern that contains '{sc_idx}', " +
        "which will be replaced by the scenario index.")

# Hardcoded depth classes
classes = [0, 0.3, 0.6, 0.9, 1.2, 1.5]
suffixes = ["0_to_30cm", "30_to_60cm", "60_to_90cm",
            "90_to_120cm", "120_to_150cm", "over_150cm"]

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
    print(
        f'Encode_coverage: WSE file cells are not 1m x 1m, but {wse_res[0]} by {wse_res[1]}.')
if (mnt_res[0] != 1 or mnt_res[1] != 1):
    print(
        f'encode_depth: Original MNT file cells are not 1m x 1m, but {mnt_res[0]} by {mnt_res[1]}.')

with rasterio.open(args.mnt) as mnt:
    mnt_rect = mnt.read(1)

v1_length = args.v1_length
v2_length = args.scenarios // v1_length

# To Do: create a 2D list of np.arrays of data type np.uint8.
# Indexing is : v1_bands[v1_idx][class_idx]
v1_bands = [[np.full(shape=wse.shape, fill_value=255, dtype=np.uint8) for i in range(len(classes))]
            for j in range(v1_length)]

# Create bands of np.uint64
# indexing is : bands[class_idx]
bands = [np.full(shape=wse.shape, fill_value=0, dtype=np.uint32)
         for i in range(len(classes))]

for v1 in range(v1_length):
    for v2 in range(v2_length):
        # Find the sc_idx with regard to v1 and v2 value, direction, and v1_length and v2_length
        if (args.direction == 2):
            sc_idx = (v1 * v1_length) + (v2 + 1)
        else:
            sc_idx = (v1 + 1) + (v2 * v2_length)

        data_path = args.wse.format(sc_idx=sc_idx)
        print(f'encode_depth: {utils.now()} Processing scenario {sc_idx}.')
        data_file = rasterio.open(data_path)
        data = data_file.read(1)

        for class_idx in range(len(classes)):
            v1_bands[v1][class_idx] = np.where(
                np.greater(data, mnt_rect + classes[class_idx]),
                np.minimum(v1_bands[v1][class_idx], (v2 + 1)),
                v1_bands[v1][class_idx])


for class_idx in range(len(classes)):
#    for v1 in range(v1_length):
    for v1 in range(8):  ## to test if 32 bit can be served by mapserver.
        # encode bands
        v1_band = v1_bands[v1][class_idx]
        v1_band[v1_band == 255] = 0
        bands[class_idx] += v1_band * 16**v1

    output_file = rasterio.open(
        f'{args.output_dir}/{args.model}_{suffixes[class_idx]}.tif',
        'w',
        driver='GTiff',
        width=wse_profile['width'],
        height=wse_profile['height'],
        count=1,
        dtype=np.uint32,
        crs=wse_profile['crs'],
        transform=wse_profile['transform'],
        nodata=int(0),
        compress='deflate'
    )
    output_file.write(bands[class_idx], 1)
    output_file.close
