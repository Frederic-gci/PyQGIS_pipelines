# System imports
import sys
import os
import re
import glob
import warnings

# QGIS imports
from qgis.core import *
import qgis.utils
from qgis.analysis import *
from qgis.PyQt.QtCore import QVariant
sys.path.append('C:\\OSGeo4W64\\apps\\qgis\\python\\plugins')

# local imports
import utilities as utils

def coverage(inputFile, outputDir):
    ## This function, called on a WSE file, will
    ## do some post-treatment (remove small 'puds' or 'islands')
    ## and produce water coverage documents.
    ## It will produce three files: a compressed binary of
    ## the raw coverage; a compressed binary of the post-treated
    ## coverage; and a multi-polygon of the coverage.

    # Extract scenario number
    basename = os.path.basename(inputFile)
    scenario = re.findall(r'\(PF\s*\d+\)', basename)
    scenario = re.findall(r'\d+', scenario[0])[0]
    print( utils.now() + "Initializing coverage pipeline for scenario " + scenario + ".")

    # Initialise QgsApplication and processing modules
    QgsApplication.setPrefixPath("C:\\OSGeo4W64\\apps\\qgis", True)
    qgs = QgsApplication([], False)
    QgsApplication.initQgis()
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        import processing
        from processing.core.Processing import Processing
    Processing.initialize()
    QgsApplication.processingRegistry().addProvider(QgsNativeAlgorithms())

    # Load as layer and set CRS
    raster = QgsRasterLayer(inputFile)
    raster.setCrs(QgsCoordinateReferenceSystem("EPSG:2949"))

    # Binarize the raster (1 if value, 0 otherwise)
    outputBin = outputDir + 'tmp_' + scenario + '.tif'
    parameters = {
        'INPUT_RASTER': raster,
        'RASTER_BAND':1,
        'TABLE': [5,254,1],
        'NO_DATA':0,
        'RANGE_BOUNDARIES':2,
        'DATA_TYPE':0,
        'OUTPUT': outputBin
    }
    processing.run('native:reclassifybytable', parameters)
    del raster

    # Compress the binary raster
    input = outputBin
    output = outputDir + 'A_BIN_' + scenario + '.tif'
    parameters = {
        'INPUT': input,
        'TARGET_CRS':QgsCoordinateReferenceSystem('EPSG:2949'),
        'OPTIONS':'COMPRESS=DEFLATE|PREDICTOR=2|ZLEVEL=9',
        'DATA_TYPE':1,
        'OUTPUT': output
    }
    processing.run('gdal:translate', parameters)

    # Remove small puddles (less than 500m2) and small islands (less than 25m)
    input = output
    output25 = outputDir + 'tmp_sieved25_'+ scenario + '.tif'
    output500 = outputDir + 'tmp_sieved500_' + scenario + '.tif'
    parameters = {
        'INPUT': input,
        'THRESHOLD':25,
        'EIGHT_CONNECTEDNESS':False,
        'NO_MASK':True,
        'OUTPUT': output25
    }
    processing.run('gdal:sieve', parameters)
    parameters = {
        'INPUT': input,
        'THRESHOLD':500,
        'EIGHT_CONNECTEDNESS':False,
        'NO_MASK':True,
        'OUTPUT': output500
    }
    processing.run('gdal:sieve', parameters)
    outputSum = outputDir + 'tmp_summed_' + scenario + '.tif'
    parameters = {
        'INPUT': [ output25, output500 ],
        'REF_LAYER': input,
        'NODATA_AS_FALSE':False,
        'NO_DATA':0,
        'DATA_TYPE':0,
        'OUTPUT': outputSum
    }
    processing.run("native:rasterbooleanand", parameters)

    # Compress the sieved raster
    input = outputSum
    output = outputDir + 'B_SIEVED_' + scenario + '.tif'
    parameters = {
        'INPUT': input,
        'TARGET_CRS':QgsCoordinateReferenceSystem('EPSG:2949'),
        'OPTIONS':'COMPRESS=DEFLATE|PREDICTOR=2|ZLEVEL=9',
        'DATA_TYPE':1,
        'OUTPUT': output
    }
    processing.run('gdal:translate', parameters)
    for file in (outputBin, output25, output500, outputSum):
        try:
            os.remove(file)
        except Exception as e:
            print("Cannot delete " + file + ": " + e)
    del outputBin, output25, output500, outputSum

    # Polygonize the coverage (gdal:polygonize)
    input = output
    output = outputDir + 'tmp_polygonize_' + scenario + '.shp'
    parameters = {
        'INPUT': input, 
        'BAND':1,
        'FIELD':'DN',
        'EIGHT_CONNECTEDNESS':False,
        'OUTPUT':output
    }
    processing.run('gdal:polygonize', parameters)

    # Delete non-covered regions (DN=0)
    layer = QgsVectorLayer(output, '', 'ogr')
    feats = layer.getFeatures()
    toDelete = []
    for feat in feats:
        if feat['DN'] == 0:
            toDelete.append(feat.id())
    layer.dataProvider().deleteFeatures(toDelete)
    del toDelete, feats, layer

    # Fix geometries, since polygonize can create 'ring self-intersections' 
    input = output
    output = outputDir + 'tmp_fixGeometry_' + scenario + '.shp'
    parameters = {
        'INPUT': input,
        'OUTPUT': output
    }
    processing.run('native:fixgeometries', parameters)

    # Merge polygons into multipart (native:collect)
    input = output
    output = outputDir + "C_poly_" + scenario + '.shp'
    parameters = {
        'INPUT': input,
        'FIELD':['DN'],
        'OUTPUT': output
    }
    processing.run('native:collect', parameters)

    # Add attribute for scenario number
    layer = QgsVectorLayer(output, '', 'ogr')
    layer.setCrs(QgsCoordinateReferenceSystem("EPSG:2949"))
    layer.dataProvider().addAttributes( [QgsField('scIdx', QVariant.Int)])
    layer.updateFields()
    attributeIndex = layer.fields().indexFromName("scIdx")
    feats = layer.dataProvider().getFeatures()
    for feat in feats:
        layer.dataProvider().changeAttributeValues({ feat.id() : {1: int(scenario)} })
    del attributeIndex, feats, layer


def finalMerge(fileTemplate, outputFile):
    ## Given a template to get all the multipolygon shapefile created by
    ## 'coverage', this function will merge them all in outputFile.

    QgsApplication.setPrefixPath("C:\\OSGeo4W64\\apps\\qgis", True)
    qgs = QgsApplication([], False)
    QgsApplication.initQgis()
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        import processing
        from processing.core.Processing import Processing
    QgsApplication.processingRegistry().addProvider(QgsNativeAlgorithms())
    fileList = glob.glob(fileTemplate)
    parameters = {
        'LAYERS': fileList,
        'CRS': 'EPSG:2949',
        'OUTPUT': outputFile
    }
    processing.run("native:mergevectorlayers", parameters)

def finalSimplification(inputFile, outputFile):
    ## This function takes the inputFile (expected to be
    ## the lossless multipolygon file produced by finalMerge) and 
    ## apply geometry simplification to produce outputFile.

    QgsApplication.setPrefixPath("C:\\OSGeo4W64\\apps\\qgis", True)
    qgs = QgsApplication([], False)
    QgsApplication.initQgis()
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        import processing
        from processing.core.Processing import Processing
    QgsApplication.processingRegistry().addProvider(QgsNativeAlgorithms())
    parameters = {
        'INPUT': inputFile,
        'METHOD':0,
        'TOLERANCE':5,
        'OUTPUT': outputFile
    }
    processing.run("native:simplifygeometries", parameters)
