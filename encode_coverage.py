import rasterio
import numpy as np

## Parameters: 
file_mask = '/processing/tmp/32198/*.tif'
mnt_path = '/processing/mnt/mnt_jc_oct19_32198_1x1_clipped.tif'
max_idx_scenario = 157

thresholds = [0,0.3,0.6,0.9,1.2,1.5]
suffixes = ["0to30cm.tif", "30to60cm.tif","60to90cm.tif", "90to120cm.tif", "over120cm.tif"]

### Load the MNT
mnt = rasterio.open(mnt_path)
mnt_dat = mnt.read(1)

### Load the first data file to get shape
wse = rasterio.open('/processing/tmp/32198/SC1.32198.tif')
shape = wse.shape

### 
band1 = np.full(shape=shape, fill_value=255, dtype=np.uint8)
band2, band3, band4 = map(np.copy, [band1] * 3)

for i in range (1, 156):
  print(f'Processing wse number {i}')
  data_path = f'/processing/tmp/32198/SC{i}.32198.tif'
  data_file = rasterio.open(data_path)
  data = data_file.read(1)
  band1 = np.where( np.greater(data, mnt_dat + threshold[0]) , np.minimum(band1, i), band1 )
  band2 = np.where( np.greater(data, mnt_dat + threshold[1]) , np.minimum(band2, i), band2 )
  band3 = np.where( np.greater(data, mnt_dat + threshold[2]) , np.minimum(band3, i), band3 )
  band4 = np.where( np.greater(data, mnt_dat + threshold[3]) , np.minimum(band4, i), band4 )


output_file = rasterio.open(
  '/processing/output/test.tif',
  'w', 
  driver='GTiff',
  width=wse.width,
  height=wse.height,
  count=4,
  dtype=np.uint8,
  crs=wse.crs,
  transform=wse.transform,
  nodata=int(255),
  compress='deflate'
)
output_file.write(band1, 1)
output_file.write(band2, 2)
output_file.write(band3, 3)
output_file.write(band4, 4)


## Notes: 
## First, in QGIS, set the raster to the resolution of the scenario.
## Second, in QGIS, clip the raster according to the extent of the scenario.
