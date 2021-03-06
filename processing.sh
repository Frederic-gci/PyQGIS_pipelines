#!/usr/bin/bash

## Notes:
## Rasterio needs a X display, otherwise, there are plenty of irrelevant error messages.
## Copy the script template and fill the parameters,
## or call it from a launching script using params in the launching command.
# model="model"
# file_mask="SC{sc_idx}.tif"
# original_wse_files="/path_to_wse_files/*.tif"
# original_mnt="/path_to_mnt/mnt"

model=$1
file_mask=$2
original_wse_files=$3
original_mnt=$4
num_var="${5:-1}"
v1_length="${6:-0}"
encode_depth_var_first_increased="${7:-0}"

## Choose the steps to execute
prepare_wse=1
prepare_mnt=1
encode_depth=1
transfer_coverage=1
retrieve_buildings=1
get_hsub_data=1
transfer_hsub_data=1
move_result=1

log_file="/processing/PyQGIS_pipelines/executions/logs/processing/${model}_$(date +%F).log"
{

## Set up working environment
export QT_QPA_PLATFORM=offscreen # (to use QT without GUI)
source psql.env  # Load the credentials for psql server
pipeline_path="/processing/PyQGIS_pipelines/"
mnt_path="/processing/tmp/${model}/mnt_32198/"
wse_path="/processing/tmp/${model}/wse_32198/"
tmp_path="/processing/tmp/${model}/tmp/"
buildings="${tmp_path}${model}_buildings.shp"
depth_coverage_output="/processing/tmp/${model}/depth_coverage_output/"
hsub_output="/processing/tmp/${model}/hsub_output/"
mkdir -p ${mnt_path} ${wse_path} ${tmp_path} ${depth_coverage_output} ${hsub_data_output}
mnt=${mnt_path}`basename ${original_mnt}`
final_folder=/data/aurige/results/${model}_$(date +%F)/

echo "$(date +'%F %T') -- Starting pipeline for ${model}."
echo "MNT used is '${original_mnt}'"
echo "WSE files are '${original_wse_files}'"
echo "WSE files are described as '${file_mask}' where '{sc_idx}' can be replaced by the scenario index."
echo " "

## Test WSE files for CRS and copy or reproject
if (( prepare_wse ))
then
  echo "$(date +'%F %T') -- Preparing WSE files using rasterio v. $(rasterio --version)"
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
else
  echo "Skipped preparation of WSE files"
fi


## Test MNT and reproject
if (( prepare_mnt ))
then
  one_wse_32198_file=$(ls -t ${wse_path}*.tif | head -n 1)
  wse_crs=`rasterio info --crs ${one_wse_file}`
  wse_res=`rasterio info --res ${one_wse_file}`
  mnt_crs=`rasterio info --crs ${original_mnt}`
  mnt_res=`rasterio info --res ${original_mnt}`

  echo "$(date +'%F %T') -- Preparing MNT file using rasterio v. $(rasterio --version)"
  echo "Original MNT CRS is ${mnt_crs}."
  echo "Original MNT resolution is ${mnt_res}."
  if [[ ${mnt_crs} = "EPSG:32198" ]]
  then
    echo "MNT is copied directly to ${mnt_path}"
    cp ${original_mnt} ${mnt}
  else
    echo "MNT will be reprojected 'like' a WSE data file."
    rasterio warp ${original_mnt} ${mnt} --like ${one_wse_32198_file} \
    --resampling bilinear --threads 6 --overwrite
    printf "Reprojected $(basename ${mnt}) -- "
    date +'%F %T'
  fi
else
  echo "Skipped preparation of MNT file"
fi
echo ""

## Verify the number of available wse_files:
num_scenarios=$(ls ${wse_path}*.tif | wc -l)
echo "Num scenarios = ${num_scenarios}"
echo ""

## Encode depth coverage:
if (( encode_depth ))
then
  echo "$(date +'%F %T') -- Launching 'encode_coverage.py'"
  if (( num_var == 2 ))
  then
    python3 -u ${pipeline_path}/encode_depth_2v.py \
      --mnt ${mnt} \
      --wse "${wse_path}${file_mask}" \
      --scenarios ${num_scenarios} \
      --model ${model} \
      --output_dir ${depth_coverage_output} \
      --v1_length ${v1_length} \
      --var_first_increased ${encode_depth_var_first_increased}
  else
    python3 -u ${pipeline_path}/encode_depth.py \
      --mnt ${mnt} \
      --wse "${wse_path}${file_mask}" \
      --scenarios ${num_scenarios} \
      --model ${model} \
      --output_dir ${depth_coverage_output}
    echo "$(date +'%F %T') -- Finished 'encode_coverage.py'"
  fi
else
  echo "Skipped encoding of depth coverage."
fi
echo ""

## Transfert depth coverage output to dev
if (( transfer_coverage ))
then
  echo "$(date +'%F %T') -- Transfering encoded coverage output to dev server."
  scp ${depth_coverage_output}/* ${CC_DEV_USER}@${CC_DEV_IP}:/opt/aurige/geodata/infocrue/coverage/
else
  echo "Skipped the transfert of encoded coverage to CC server."
fi
echo ""

## Get a building shapefile from psql using SAPIENS, sectors xref_building_sectors
if (( retrieve_buildings ))
then
  echo "$(date +'%F %T') -- Retrieve buildings from SAPIENS database"
  query="SELECT "
  query+="distinct sap_bati.geom, sap_bati.id_batimen as batiment_i, sap_bati.alt_premie "
  query+="FROM "
  query+="sap_bati, xref_sector_building, sectors "
  query+="WHERE "
  query+="sap_bati.id_batimen=xref_sector_building.building_id "
  query+="AND xref_sector_building.sector_id=sectors.sector_id "
  query+="AND sectors.model = '${model}';"
  pgsql2shp -h $PSQL_DB_HOST -u $PSQL_DB_USER -p $PSQL_DB_PORT -P $PSQL_DB_PW \
    -f ${buildings} aurige "${query}"
else
  echo "Skipped retrieval of buildings from SAPIENS database."
fi
echo ""

## Launch get_hsub
if (( get_hsub_data ))
then
  echo "$(date +'%F %T') -- Launching hsub_data.py, using libraries from: $(qgis --version)."
  python3 ${pipeline_path}/get_hsub.py \
    --wse "${wse_path}${file_mask}" \
    --buildings ${buildings} \
    --scenarios ${num_scenarios} \
    --model ${model} \
    --output_dir ${hsub_output} \
    --tmp_dir ${tmp_path}
  echo "$(date +'%F %T') -- Finished hsub_data.py"
else
  echo "Skipped production of hsub data."
fi
echo ""

## Remove previous model data from aurige.infocrue_hsub:
if (( transfer_hsub_data ))
then
  query="DELETE FROM infocrue_hsub "
  query+="WHERE model = '${model}';"
  echo "$(date +'%F %T') -- Removing previous hsub data for this model from the database."
  echo "Query = '${query}'"
  PGPASSWORD=$PSQL_DB_PW psql -U $PSQL_DB_USER -h $PSQL_DB_HOST \
    -p $PSQL_DB_PORT  -d aurige -c "${query}"
  echo ""
  ## load hsub data to aurige.infocrue_hsub
  echo "$(date +'%F %T') -- Adding hsub data for this model to the database."
  query="\COPY infocrue_hsub (building_id,sc_idx,z_water,e_surf,e_isol,hsub,model,distance) "
  query+="FROM '${hsub_output}/${model}_water_data.txt' "
  query+="WITH (FORMAT CSV, DELIMITER ',', HEADER TRUE);"
  echo "Query = '${query}'"
  PGPASSWORD=$PSQL_DB_PW psql -U $PSQL_DB_USER -h $PSQL_DB_HOST \
    -p $PSQL_DB_PORT -d aurige -c "${query}"
else
  echo "Skipped transfer of hsub data to CC server database."
fi
echo ""

## Transfert analysis to /data/aurige/results/${model}_$(date +%F)/
if (( move_result ))
then
  echo "$(date +'%F %T') -- Moving analysis folder to ${final_folder}"
  mv /processing/tmp/${model}/ ${final_folder}
else
  echo "Skipped moving the results to the /data partition."
fi
echo ""

echo "$(date +'%F %T') -- Analysis pipeline for ${model} finished."
} 2>&1 | tee ${log_file}
