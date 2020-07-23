import glob
import concurrent.futures

# Local scripts
import water_coverage as wc
import infocrue as ic
import utilities as utils

# Inputs
file_template = 'D:/raw_data/info_crue/0508_JacquesCartier_HECRAS_WSE/WSE (PF {0}).Terrain.MNT_J_C.tif'
wse_crs="EPSG:2949"
# mnt_32198='D:/Results/info_crue/mnt/32198/mnt_jc_oct19.32198.tif'
mnt_32198='C:/A_DATA/INFOCRUE_data/mnt_jc_oct19.32198.tif'
output_dir='C:/A_DATA/INFOCRUE_data/mnt_jc_oct19.32198.tif'
output_dir="C:/A_DATA/jc_coverage/"

def main():
  e = concurrent.futures.ProcessPoolExecutor(8)
  for scenario_idx in range(107,158):
    wse_file = file_template.format(scenario_idx)
    # wc.coverage_classes_from_wse(
    #   wse_file=wse_file, 
    #   wse_crs=wse_crs,
    #   mnt_32198='C:/A_DATA/INFOCRUE_data/mnt_jc_oct19.32198.tif',
    #   scenario_idx=scenario_idx,
    #   output_dir=output_dir
    # )
    e.submit(wc.coverage_classes_from_wse, 
      wse_file=wse_file, 
      wse_crs=wse_crs,
      mnt_32198=mnt_32198,
      scenario_idx=scenario_idx,
      output_dir=output_dir
    )
  e.shutdown(wait=True)

  ic.finalMerge(
    fileTemplate=output_dir + '*_water_classes.shp',
    outputFile=output_dir + '0508_jc_water_classes_final.shp'
  )
  utils.clean(output_dir)

if __name__ == '__main__':
    main()


