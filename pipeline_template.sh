#!/usr/bin/bash

## Notes:
## Rasterio needs a X display, otherwise, there are plenty of irrelevant error messages.

## Get the model specific informations:
# model="model"
# file_mask="SC{sc_idx}.32198.tif"
# original_wse_files="/path_to_wse_files/*.tif"
# original_mnt="/path_to_mnt/mnt"

model="0508_JacquesCartier"
file_mask="SC{sc_idx}.tif"
original_wse_files="/data/aurige/infocrue/0508_JacquesCartier_HECRAS/wse_processed/*.tif"
original_mnt="/data/aurige/raw_data/infocrue/Scenarios_Jacques_Cartier_ULAVAL/Modele_J_C_HD/mnt_jc_oct19.tif"

{
## Set up working environment
export QT_QPA_PLATFORM=offscreen # (to use QT without GUI)
DISPLAY='IP:0.0'
source psql.env
# log_file="/processing/PyQGIS_pipelines/executions/$(date +%F)_${model}.log"
pipeline_path="/processing/PyQGIS_pipelines/"
mnt_path="/processing/tmp/${model}/mnt_32198/"
wse_path="/processing/tmp/${model}/wse_32198/"
tmp_path="/processing/tmp/${model}/tmp/"
buildings="${tmp_path}${model}_buildings.shp"
depth_coverage_output="/processing/tmp/${model}/depth_coverage_output/"
hsub_output="/processing/tmp/${model}/hsub_output/"
mkdir -p ${mnt_path} ${wse_path} ${tmp_path} ${depth_coverage_output} ${hsub_data_output}
mnt=${mnt_path}`basename ${original_mnt}`

echo "$(date +'%F %T') -- Starting pipeline for ${model}."
echo "MNT used is '${original_mnt}'"
echo "WSE files are '${original_wse_files}'"
echo "WSE files are described as '${file_mask}' where '{sc_idx}' can be replaced by the scenario index."
echo " "

# Test WSE files for CRS
echo "$(date +'%F %T') -- Preparing WSE files"
one_wse_file=$(ls -t ${original_wse_files} | head -n 1)
original_wse_crs=`rasterio info --crs ${one_wse_file}`
original_wse_res=`rasterio info --res ${one_wse_file}`
echo "Original WSE file CRS is ${original_wse_crs}"
echo "Original WSE resolution is ${original_wse_res} "

if [[ ${wse_crs} = "EPSG:32198" ]]
then
  echo "WSE files are copied directly to ${wse_path}"
  cp ${original_wse_files} ${wse_path}
else
  echo -e "WSE files from ${original_wse_files}\n  will be reprojected to EPSG:32198\n  into ${wse_path}"
  rasterio_command="rasterio warp {} ${wse_path}{/} --dst-crs EPSG:32198 --resampling bilinear --overwrite"
  parallel -j 16 "${rasterio_command}; printf \"Reprojected {/} -- \"; date +'%F %T'" ::: ${original_wse_files}
fi

# Preparing MNT
one_wse_32198_file=$(ls -t ${wse_path}*.tif | head -n 1)
wse_crs=`rasterio info --crs ${one_wse_file}`
wse_res=`rasterio info --res ${one_wse_file}`
mnt_crs=`rasterio info --crs ${original_mnt}`
mnt_res=`rasterio info --res ${original_mnt}`

echo "$(date +'%F %T') -- Preparing WSE files"
echo "Original MNT CRS is ${mnt_crs}."
echo "Original MNT resolution is ${mnt_res}."
echo " "

if [[ ${mnt_crs} = "EPSG:32198" ]]
then
  echo "MNT is copied directly to ${mnt_path}"
  cp ${original_mnt} ${mnt}
else
  echo "MNT will be reprojected 'like' a WSE data file."
  rasterio warp ${original_mnt} ${mnt} --like ${one_wse_32198_file} \
  --resampling bilinear --threads 6 --overwrite
  printf "Reprojected $(basename ${mnt})"
  date +'%F %T'
fi

# Encode detph coverage:
num_scenarios=$(ls ${wse_path}*.tif | wc -l)

echo "$(date +'%F %T') -- Launching 'encode_coverage.py'"
python3 -u ${pipeline_path}/encode_depth.py \
  --mnt ${mnt} \
  --wse "${wse_path}${file_mask}" \
  --scenarios ${num_scenarios} \
  --model ${model} \
  --output_dir ${depth_coverage_output}
echo "$(date +'%F %T') -- Finished 'encode_coverage.py'"
echo " "


# # TODO: Get building file from psql using SAPIENS, +infocrue_segmentation +s
echo "$(date +'%F %T') -- Getting model building from sapiens"
query << endOfQuery
SELECT
  distinct sapiens.geom, sapiens.batiment_i, sapiens.alt_premie
FROM
  sapiens, xref_sector_building, sectors
WHERE
  sapiens.batiment_i=xref_sector_building.building_id
  AND xref_sector_building.sector_id=sectors.sector_id
  AND sectors.model = '${model}';
endOfQuery
pgsql2shp -h $PSQL_DB_HOST -u $PSQL_DB_USER -p $PSQL_DB_PORT -P $PSQL_DB_PW \
  -f ${buildings} aurige "${query}"
echo " "

echo "$(date +'%F %T') -- Launching hsub_data.py"
python3 -u ${pipeline_path}/get_hsub.py \
  --wse "${wse_path}${file_mask}" \
  --buildings ${buildings} \
  --scenarios ${num_scenarios} \
  --model ${model} \
  --output_dir ${hsub_output} \
  --tmp_dir ${tmp_path}/hsub_tmp/
echo "$(date +'%F %T') -- Finished hsub_data.py"
echo " "

# TODO: load water data to psql
# TODO: Move the model folder to aurige/results/
# TODO: scp results to aurige.gci.ulaval.ca

# } 2>&1 | tee -a ${log_file}

} | tee /processing/PyQGIS_pipelines/executions/0508_JC_test.log


# TODO : Fix the log file.