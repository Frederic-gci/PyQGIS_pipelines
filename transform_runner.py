# This script iterates on all the files globbed by the filemask
# and calls infocrue.transform on them using the
# given source_crs and target_crs.

import glob
import concurrent.futures
import infocrue as ic

# Inputs:
file_mask = '/processing/input/*.tif'
output_dir = '/processing/tmp/32198/'
source_crs = 'EPSG:6622'
target_crs = 'EPSG:32198'


def main():
    fileList = glob.glob(file_mask)
    e = concurrent.futures.ProcessPoolExecutor(max_workers=16)
    for file in fileList:
        e.submit(ic.transform, file, source_crs, target_crs, output_dir)
    e.shutdown(wait=True)


if __name__ == '__main__':
    main()

# /usr/lib/python3/dist-packages/qgis/
# sys.path.append('/usr/share/qgis/python/plugins/processing')