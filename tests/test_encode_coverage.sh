#!/usr/bin/bash

encode_cov="/processing/PyQGIS_pipelines/encode_coverage.py"
mnt_2949="/data/aurige/raw_data/infocrue/Scenarios_Jacques_Cartier_ULAVAL/Modele_J_C_HD/mnt_jc_oct19.tif"
mnt_32198="/processing/mnt/mnt_jc_oct19.32198_2020-07-13.tif"

## Test help:
echo "Should print the help for encode_coverage.py:"
python3 ${encode_cov} -h
echo ""

## Test exit if mnt is not in 32198:
echo "Should exit because MNT is not in epsg:32198: "
python3 ${encode_cov} \
  --mnt ${mnt_2949} \
  --wse "/processing/tmp/32198/SC{sc_idx}.32198.tif" \
  --scenarios 1 \
  --model "model name"
echo ""

echo "Should exit because WSE is not in epsg:32198: "
python3 ${encode_cov} \
  --mnt ${mnt_32198} \
  --wse "/data/aurige/infocrue/0508_JacquesCartier_HECRAS/wse_processed/SC{sc_idx}.tif" \
  --scenarios 1 \
  --model "model name"
echo ""

echo "Should exit because MNT does not contain the extent of wse file: "
python3 ${encode_cov} \
  --mnt "/processing/tmp/SLNO000347_SC1.32198.tif" \
  --wse "/processing/tmp/32198/SC{sc_idx}.32198.tif" \
  --scenarios 1 \
  --model "test_no_resampling"
echo ""

echo "Should warn that MNT is not 1x1"
python3 ${encode_cov} \
  --mnt "/processing/mnt/mnt_jc_oct19.32198.tif" \
  --wse "/processing/tmp/32198/SC{sc_idx}.32198.tif" \
  --scenarios 1 \
  --model "model name"
echo ""

echo "Should warn that WSE pattern does not contain the '{sc_idx}' placeholder: "
python3 ${encode_cov} \
  --mnt ${mnt_32198} \
  --wse "/processing/tmp/32198/SC.32198.tif" \
  --scenarios 1 \
  --model "model name"
echo ""

echo "What happens if there is no file?"
python3 ${encode_cov} \
  --mnt "/processing" \
  --wse "/processing/{sc_idx}" \
  --scenarios 1 \
  --model "test_no_resampling"
echo ""
# # OpenFailedError:  '/processin' not recognized a supported file format.""
