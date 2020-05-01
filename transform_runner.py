# This script iterates on all the files globbed by the filemask
# and calls infocrue.transform on them using the
# given source_crs and target_crs.

import glob
import concurrent.futures
import infocrue as ic

# Inputs:
file_mask = 'D:/Results/INFO-Crue/0508_JacquesCartier/ExtendedWSE/*.tif'
output_dir = 'D:/Results/INFO-Crue/0508_JacquesCartier/ExtendedWSE/32198'
source_crs = 'EPSG:2949'
target_crs = 'EPSG:32198'


def main():
    fileList = glob.glob(file_mask)
    e = concurrent.futures.ProcessPoolExecutor(max_workers=4)
    for file in fileList:
        e.submit(ic.transform, file, source_crs, target_crs, output_dir)
    e.shutdown(wait=True)


if __name__ == '__main__':
    main()
