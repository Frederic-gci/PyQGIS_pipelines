#!/usr/bin bash

get_hsub="/processing/PyQGIS_pipelines/get_hsub.py"
# wse="/processing/tmp/32198/SC{sc_idx}.32198.tif"
# buildings="/processing/tmp/test/0508_JacquesCartier_HECRAS_buildings.shp"
# To use QT without GUI, set the platform to offscreen
export QT_QPA_PLATFORM=offscreen

wse="/processing/tmp/0508_JacquesCartier/wse_32198/SC{sc_idx}.tif"
buildings="/processing/tmp/0508_JacquesCartier/tmp/0508_JacquesCartier_buildings.shp"

python3 ${get_hsub} \
  --wse ${wse} \
  --buildings ${buildings} \
  --scenarios 2 \
  --model "0508_JacquesCartier" \
  --output_dir "/processing/tmp/hsub_test/" \
  --tmp_dir "/processing/tmp/hsub_test/tmp/"

echo ""
