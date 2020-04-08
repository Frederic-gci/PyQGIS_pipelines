import glob
import concurrent.futures

## Local scripts
import infocrue as ic
import utilities as utils

## To avoid nasty deprecation warnings from the qgis code: 
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

def main():
    fileList = glob.glob("D:/RawData/InfoCrue/0508_JacquesCartier_HECRAS_WSE/WSE*.tif")
    print( utils.now() + "Starting execution")
    outputDir = 'C:/DATA/INFO-Crue_tmp/'
    e = concurrent.futures.ProcessPoolExecutor()
    for file in fileList:
        e.submit(ic.coverage, file, outputDir)
    e.shutdown(wait=True)
    print( pipeline.now() + "Ending loop: e.shutdown returned")

if __name__ == '__main__':
    main()
