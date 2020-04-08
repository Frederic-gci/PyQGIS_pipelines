from qgis.core import *
import qgis.utils
from qgis.analysis import *
from qgis.PyQt.QtCore import QVariant
import os
import re
import sys
import glob

import utilities as utils

def coverage(file, outputDir):
    #
    # Start
    basename = os.path.basename(file)
    scenario = re.findall(r'\(PF\s*\d+\)', basename)
    scenario = re.findall(r'\d+', scenario[0])[0]
    print( utils.now() + "Initializing coverage pipeline for scenario " + scenario + ".")
    #
    ## Initialise QgsApplication and processing modules
    QgsApplication.setPrefixPath("C:\\OSGeo4W64\\apps\\qgis", True)
    qgs = QgsApplication([], False)
    QgsApplication.initQgis()
    ## Retrieve algorithm and add them with Processing.initialize()
    sys.path.append('C:\\OSGeo4W64\\apps\\qgis\\python\\plugins')
    import processing
    from processing.core.Processing import Processing
    Processing.initialize()
    QgsApplication.processingRegistry().addProvider(QgsNativeAlgorithms())
    #
    ## Load as layer and set CRS
    raster = QgsRasterLayer(file)
    raster.setCrs(QgsCoordinateReferenceSystem("EPSG:2949"))
    #
    ## Binarize the raster (1 if value, 0 otherwise) (native:reclassifybytable)
    output = outputDir + 'tmp_' + scenario + '.tif'
    parameters = {
        'INPUT_RASTER': raster,
        'RASTER_BAND':1,
        'TABLE': [5,254,1],
        'NO_DATA':0,
        'RANGE_BOUNDARIES':2,
        'DATA_TYPE':0,
        'OUTPUT': output
    }
    processing.run('native:reclassifybytable', parameters)
    del(raster)
    #
    ## Compress the raster (gdal:translate)
    input = output 
    output = outputDir + 'A_BIN_' + scenario + '.tif'
    parameters = {
        'INPUT': input,
        'TARGET_CRS':QgsCoordinateReferenceSystem('EPSG:2949'),
        'OPTIONS':'COMPRESS=DEFLATE|PREDICTOR=2|ZLEVEL=9',
        'DATA_TYPE':1,
        'OUTPUT': output
    }
    processing.run('gdal:translate', parameters)
    try:
        os.rm(input)
    except:
        pass
    #
    ## Remove small puddles (less than 224m2, so less than 15m * 15m) (gdal:sieve)
    input = output
    output = outputDir + 'tmp2_'+ scenario + '.tif'
    parameters = {
        'INPUT': input,
        'THRESHOLD':224,
        'EIGHT_CONNECTEDNESS':False,
        'NO_MASK':True,
        'OUTPUT': output
    }
    processing.run('gdal:sieve', parameters)
    #
    ## Compress the raster (gdal:translate)
    input = output
    output = outputDir + 'B_SIEVED_' + scenario + '.tif'
    parameters = {
        'INPUT': input,
        'TARGET_CRS':QgsCoordinateReferenceSystem('EPSG:2949'),
        'OPTIONS':'COMPRESS=DEFLATE|PREDICTOR=2|ZLEVEL=9',
        'DATA_TYPE':1,
        'OUTPUT': output
    }
    processing.run('gdal:translate', parameters)
    try:
        os.remove(input)
    except:
        pass
    #
    ## Polygonize the coverage (gdal:polygonize)
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
    #
    # Delete non-covered regions (DN=0)
    layer = QgsVectorLayer(output, '', 'ogr')
    feats = layer.getFeatures()
    toDelete = []
    for feat in feats:
        if feat['DN'] == 0:
            toDelete.append(feat.id())
    layer.dataProvider().deleteFeatures(toDelete)
    del toDelete, feats, layer
    #
    # Fix geometries, since polygonize can create 'ring self-intersections' 
    # (native:fixgeometries)
    input = output
    output = outputDir + 'tmp_fixGeometry_' + scenario + '.shp'
    parameters = {
        'INPUT': input,
        'OUTPUT': output
    }
    processing.run('native:fixgeometries', parameters)
    #
    # Merge polygons into multipart (native:collect)
    input = output
    output = outputDir + "C_poly_" + scenario + '.shp'
    parameters = {
        'INPUT': input,
        'FIELD':['DN'],
        'OUTPUT': output
    }
    processing.run('native:collect', parameters)
    #
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