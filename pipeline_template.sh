#!/usr/bin/bash

## Get the model specific informations:
model="model"
file_mask="SC{sc_idx}.32198.tif"
original_wse_files="/path_to_wse_files/*.tif"
original_mnt="/path_to_mnt/mnt"

## Set up worcing environment
export QT_QPA_PLATFORM=offscreen # (to use QT without GUI)
pipeline_path="/processing/PyQgis_pipelines/"
mnt_path="/processint/tmp/${model}/mnt_32198/"
wse_path="/processing/tmp/${model}/wse_32198/"
tmp_path="/processing/tmp/${model}/"
depth_output="/processing/tmp/${model}/depth_output/"
water_data_output="/processing/tmp/${model}/water_data_output/"
mkdir ${mnt_path} ${wse_path} ${tmp_path} ${depth_output} ${water_data_output}

mnt=${mnt_path}`basename ${original_mnt}`

# Test WSE files for CRS
one_wse_file=$(ls -t ${original_wse_files} | head -n 1)
wse_crs=`rasterio info --crs ${one_wse_file}`
if [ ${wse_crs} == "EPSG:32198" ]
then
  cp ${original_wse_files} ${wse_path}
else
  for file in ${original_wse_files}
  do
    output=${wse_path}`basename ${file}`
    rasterio ${file} ${output} --dst-crs "EPSG:32198" --res 1.0 \
    --resampling bilinear --threads 6 --overwrite
  done
fi
one_wse_32198_file=$(ls -t ${wse_path}*.tif | head -n 1)

# Test original mnt for CRS and resolution, reproject or copy.
mnt_crs=`rasterio info --crs ${original_mnt}`
mnt_res=`rasterio info --res ${original_mnt}`

if [ ${mnt_crs}=="EPSG:32198" ] && [ ${mnt_res}=="1.0 1.0" ]
then
  cp ${original_mnt} ${mnt}
else
  rasterio ${original_mnt} ${mnt} --like ${one_wse_32198_file} \
  --resampling bilinear --threads 6 --overwrite
fi

# Encode detph coverage:
num_scenarios=$(ls ${wse_path}*.tif | wc -l)
python3 ${pipeline_path}/encode_coverage.py \
  --mnt ${mnt} \
  --wse "${wse_path}${file_mask}" \
  --scenarios ${num_scenarios} \
  --model ${model} \
  --output_dir ${depth_output}

# TODO: Get building file from psql using SAPIENS, +infocrue_segmentation +s
# pgsql2shp -f <file path to save shape file> \
# -u <username> -h <hostname> -P <password> <database Name> \
# “query to be executed”


# TODO: launch water_data.py

# TODO: load water data to psql


# TODO: create a log file.

