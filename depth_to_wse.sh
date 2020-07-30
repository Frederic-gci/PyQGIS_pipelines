#!/usr/bin/bash

model="toto"
mnt_original='/data/aurige/raw_data/infocrue/Scenarios_Jacques_Cartier_ULAVAL/Modele_J_C_HD/mnt_jc_oct19.tif'
mnt="/processing/tmp/preprocessing/${model}/mnt_jc_oct19.tif"
depth1='/processing/tmp/preprocessing/toto/depth/SLNO00347/SC1.tif'
wse_path='/processing/tmp/preprocessing/toto/wse/'

rasterio warp --like ${depth1} --resampling bilinear --overwrite ${mnt_original} -o ${mnt}

rasterio_command="rasterio calc '(+ (read 1 1)  (read 2 1))' {} ${mnt} -o ${wse_path}{/}"
parallel -j 16 "${rasterio_command}" ::: /processing/tmp/preprocessing/toto/depth/SLNO00347/*.tif
