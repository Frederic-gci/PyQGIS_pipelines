#!/usr/bin/bash

## Input parameters
model="model"
mnt_original="/path/to/mnt"
depth1='/path/to/depth/file/SC1.tif'
depth_glob='/path/to/depth_files/SC*.tif'

## Example inputs for SLNO00381_LE:
## model="SLNO00381_LE"
## original_mnt='/data/aurige/raw_data/infocrue/Scenarios_Jacques_Cartier_ULAVAL/Modele_J_C_HD/mnt_jc_oct19.tif'
## depth1='/data/aurige/infocrue/SLNO00381/SC1.tif'
## depth_glob="/data/aurige/infocrue/SLNO00381/SC*.tif"

## Set up working environment
wse_path="/processing/tmp/preprocessing/${model}/wse/"
mnt_path="/processing/tmp/preprocessing/${model}/mnt/"
mnt=${mnt_path}`basename ${original_mnt}`
final_folder=/data/aurige/results/preprocessing/${model}_$(date +%F)/
mkdir -p ${mnt_path} ${wse_path}

log_file="/processing/PyQGIS_pipelines/executions/logs/${model}_depth2wse_$(date +%F).log"
{

echo "$(date +'%F %T') -- Starting preprocessing depth2wse ${model}."
echo ""
echo "$(date +'%F %T') -- Preparing MNT file"
rasterio warp --like ${depth1} --resampling bilinear --overwrite ${original_mnt} -o ${mnt}
echo ""

## Adding MNT and depth files
echo "$(date +'%F %T') -- Adding MNT and depth files"
rasterio_command="rasterio calc '(+ (read 1 1)  (read 2 1))' {} ${mnt} -o ${wse_path}{/} --overwrite"
parallel -j 16 "${rasterio_command}" ::: ${depth_glob}
echo ""

## Transfert analysis to /data/aurige/results/${model}_$(date +%F)/
echo "$(date +'%F %T') -- Moving analysis folder to ${final_folder}"
mv /processing/tmp/preprocessing/${model}/ ${final_folder}
echo " "

echo "$(date +'%F %T') -- Preprocessing depth2wse for ${model} finished."
} 2>&1 | tee ${log_file}