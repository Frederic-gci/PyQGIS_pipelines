#!/usr/bin bash

get_hsub="/processing/PyQGIS_pipelines/get_hsub.py"
wse="/processing/tmp/32198/SC{sc_idx}.32198.tif"
buildings="/processing/tmp/test/0508_JacquesCartier_HECRAS_buildings.shp"
# To use QT without GUI, set the platform to offscreen
export QT_QPA_PLATFORM=offscreen

# echo "Should print the help file"
# python3 ${water_data_script} --help
# echo ""

echo "Run 'water_data' on all scenario for 0508_JacquesCartier"
python3 ${get_hsub} \
  --wse ${wse} \
  --buildings ${buildings} \
  --scenarios 157 \
  --model "test_wd" \
  --output_dir "/processing/output/test_wd/" \
  --tmp_dir "/processing/tmp/test_wd/"
echo ""
