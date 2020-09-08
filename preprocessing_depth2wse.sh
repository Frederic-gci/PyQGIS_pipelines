#!/usr/bin/bash

## Input parameters
## Copy the script template and fill the parameters,
## or call it from a launching script using params in the launching command.
# model="model"
# mnt_original="/path/to/mnt"
# depth1='/path/to/depth/file/SC1.tif'
# depth_glob='/path/to/depth_files/SC*.tif'

model=$1
original_mnt=$2
depth1=$3
depth_glob=$4

## Set up working environment
wse_path="/processing/tmp/preprocessing/${model}/wse/"
mnt_path="/processing/tmp/preprocessing/${model}/mnt/"
mnt=${mnt_path}`basename ${original_mnt}`
final_folder=/data/aurige/results/preprocessing/${model}/
mkdir -p ${mnt_path} ${wse_path} ${final_folder}

log_file="/processing/PyQGIS_pipelines/executions/logs/preprocessing/${model}_depth2wse_$(date +%F).log"
{

echo "$(date +'%F %T') -- Starting preprocessing depth2wse ${model}."
echo ""

## Resample MNT file
echo "$(date +'%F %T') -- Preparing MNT file"
rasterio warp --like ${depth1} --resampling bilinear --overwrite ${original_mnt} -o ${mnt}
echo "$(date +'%F %T') -- MNT file resampled 'like' ${depth1}"
echo ""

## Add MNT and depth files in parallel
echo "$(date +'%F %T') -- Adding MNT and depth files"
rasterio_command="rasterio calc '(+ (read 1 1)  (read 2 1))' {} ${mnt} -o ${wse_path}{/} --overwrite"
parallel -j 16 --joblog /dev/stdout "${rasterio_command}" ::: ${depth_glob}
echo "$(date +'%F %T') -- Finished adding MNT and depth files."
echo ""

## Transfert analysis to /data/aurige/results/${model}_$(date +%F)/
echo "$(date +'%F %T') -- Moving analysis folder to ${final_folder}"
mv /processing/tmp/preprocessing/${model}/* ${final_folder}
echo ""

echo "$(date +'%F %T') -- Preprocessing depth2wse for ${model} finished."
} 2>&1 | tee ${log_file}
