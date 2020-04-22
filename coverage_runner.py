import glob
import concurrent.futures

# Local scripts
import infocrue as ic
import utilities as utils

def main():
    fileList = glob.glob(
        "D:/RawData/InfoCrue/0508_JacquesCartier_HECRAS_WSE/WSE*.tif")
    outputDir = 'C:/DATA/INFO-Crue_tmp2/'
    e = concurrent.futures.ProcessPoolExecutor()
    for file in fileList:
        e.submit(ic.coverage, file, outputDir)
    e.shutdown(wait=True)
    ic.finalMerge(
        fileTemplate=outputDir + 'C_poly*.shp',
        outputFile=outputDir + 'JC_raw_coverage.shp')
    ic.finalSimplification(
        inputFile=outputDir + 'JC_raw_coverage.shp',
        outputFile=outputDir + 'JC_simplified_coverage.shp'
    )
    utils.clean(outputDir)


if __name__ == '__main__':
    main()
