import rasterio
import numpy as np

## Parameters: 
scenario_name = "0508_JacquesCartier_HECRAS"
file_mask = '/processing/tmp/32198/*.tif'
mnt_path = '/processing/mnt/mnt_jc_oct19.32198_2020-07-13.tif'
max_idx_scenario = 5

classes = [0,0.3,0.6,0.9,1.2,1.5]
suffixes = ["0to30cm", "30to60cm","60to90cm", "90to120cm", "120to150cm", "over150cm"]

### Load the MNT
mnt = rasterio.open(mnt_path)
mnt_dat = mnt.read(1)

### Load the first data file to get shape
wse = rasterio.open('/processing/tmp/32198/SC1.32198.tif')
shape = wse.shape

## TODO. Verify that the cell sizes match. If not, then resample MNT to get the match
## TODO. Verify that the WSE is totally contained in the MNT or raise error.

## Extract the MNT data corresponding to the WSE rectangle.
wse_rect_window = rasterio.windows.from_bounds(*wse.bounds, transform=mnt.transform)
mnt_rect = mnt.read(1, window=wse_rect_window)

### 
bands = [ np.full(shape=shape, fill_value=255, dtype=np.uint8) for i in range(len(classes))]

for sc_idx in range (1, 6):
  print(f'Processing wse number {sc_idx}')
  data_path = f'/processing/tmp/32198/SC{sc_idx}.32198.tif'
  data_file = rasterio.open(data_path)
  data = data_file.read(1)
  for class_idx in range(len(classes)):
    bands[class_idx] = np.where(
      np.greater(data, mnt_rect + classes[class_idx]),
      np.minimum(bands[class_idx], sc_idx),
      bands[class_idx])

for class_idx in range(len(classes)):
  output_file = rasterio.open(
    f'/processing/output/{scenario_name}_{suffixes[class_idx]}.tif',
    'w',
    driver='GTiff',
    width=wse.width,
    height=wse.height,
    count=1,
    dtype=np.uint8,
    crs=wse.crs,
    transform=wse.transform,
    nodata=int(255),
    compress='deflate'
  )
  output_file.write(bands[class_idx],1)
  output_file.close
