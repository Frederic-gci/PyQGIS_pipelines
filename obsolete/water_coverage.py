import utilities as utils
import gdal_merge

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

def coverage_classes_from_wse(wse_file, wse_crs, mnt_32198, scenario_idx, output_dir):
    # This function will use an extrapolated WSE file, a raw coverage mask, a MNT and a scenario number,
    # and an output directory.
    # It will produce a reclassified multipolygon for the scenario and model.
    #   * classes: 0-30, 30-60, 60-90, > 75

    # To Do: 
    # 1. Buffer WSE by 2 meters (To get a smooth zero line).
    # 2. pad the raster with -1 values using gdal_merge 
    # 3. run processing.run("gdal:contour", 
    # 4. run polygonize
    # 5. run dissolve (remove supserposed contours)
    # 6. move from multipart to singlepart (native:multiparttosingleparts)
    # 7. select by area then delete under a certain threshold (tried with 5m, maybe 9m would be good).
    # 8. native: deleteholes (under the same threshold)
    # 9. native:simplifygeometry: METHOD:0 TOLERANCE:0.4
    # 10. in case geometry was broken: native:deleteholes again (same threshold, )
    # 11. singlepart to multipart
    # 12. add scenario number 
    # 13. save as shapefile.

    print(f"{utils.now()} Initializing coverage pipeline for scenario {scenario_idx}.")

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

    # Load wse and reproject if needs be
    if( wse_crs.lower() != "EPSG:32198".lower()):
        print(f"{utils.now()} Begin reprojection.")
        outname = f'{output_dir}\\tmp_{scenario_idx}_32198.tif'
        parameters={
            'INPUT': wse_file,
            'SOURCE_CRS': wse_crs,
            'TARGET_CRS': "EPSG:32198",
            'RESAMPLING':0,
            'NODATA':-9999,
            'OPTIONS': "COMPRESS=DEFLATE|PREDICTOR=2",
            'OUTPUT': outname
        }
        processing.run("gdal:warpreproject", parameters)
        wse = QgsRasterLayer(outname)
    else:
        wse = QgsRasterLayer(wse_file)

    ## Load mnt
    mnt = QgsRasterLayer(mnt_32198)
    mnt.setCrs(QgsCoordinateReferenceSystem("EPSG:32198"))

    # Get water depth
    print(f"{utils.now()} Begin raster calculator (wse to depth).")
    outname=f'{output_dir}\\tmp_{scenario_idx}_depth.tif'
    wse_entry=QgsRasterCalculatorEntry()
    wse_entry.raster=wse
    wse_entry.ref='wse@1'
    wse_entry.bandNumber=1
    mnt_entry=QgsRasterCalculatorEntry()
    mnt_entry.raster=mnt
    mnt_entry.ref='mnt@1'
    mnt_entry.bandNumber=1
    entries=[wse_entry, mnt_entry]
    raster_calc = QgsRasterCalculator(
        formulaString='"wse@1"-"mnt@1"',
        outputFile=outname,
        outputFormat='GTiff',
        outputExtent=wse.extent(),
        nOutputColumns=wse.width(),
        nOutputRows=wse.height(),
        rasterEntries=entries,
        transformContext=wse.transformContext()
    )
    raster_calc.processCalculation()
    wse = QgsRasterLayer(outname)

    # Pad raster with gdal_merge.py
    print(f"{utils.now()} Begin gdal merge.")
    input = outname
    outname = f'{output_dir}\\tmp_{scenario_idx}_padded.tif'
    ext = wse.extent()
    ext.grow(2)
    # ext = f'{ext.xMinimum()} {ext.yMaximum()} {ext.xMaximum()} {ext.yMinimum()}'
    gdal_merge.main(['', 
        '-o', outname, '-ul_lr', 
        str(ext.xMinimum()), 
        str(ext.yMaximum()), 
        str(ext.xMaximum()), 
        str(ext.yMinimum()),
        '-co', 'COMPRESS=DEFLATE',
        '-init', '-1', input])

    # Get contours
    print(f"{utils.now()} Start contour.")
    input = outname
    outname = f'{output_dir}\\tmp_{scenario_idx}_contour.gpkg'
    parameters = {
        'INPUT': input,
        'BAND':1,
        'INTERVAL':1000,
        'CREATE_3D':True,
        'IGNORE_NODATA':False,
        'NODATA':None,'OFFSET':0,
        'EXTRA':'-fl 0 0.001 0.3 0.6 0.9',
        'OUTPUT':outname}
    processing.run("gdal:contour", parameters )

    # Polygonize
    print(f"{utils.now()} Start polygonize.")
    input = QgsVectorLayer(outname, '', 'ogr')
    input.setCrs(QgsCoordinateReferenceSystem('EPSG:32198'))
    outname = f'{output_dir}\\tmp_{scenario_idx}_poly1.gpkg'
    parameters = {
        'INPUT':input,
        'KEEP_FIELDS':False,
        'OUTPUT': f'ogr:dbname=\'{outname}\' table=\"polygons\" (geom)'
    }
    processing.run("qgis:polygonize", parameters)

    # Add feature to polygons
    print(f"{utils.now()} Start add attribute.")
    input = outname
    poly = QgsVectorLayer(f'{outname}|layername=polygons', 'polygons', 'ogr')
    pr = poly.dataProvider()
    pr.addAttributes([QgsField('Z', QVariant.Double), QgsField('sc_idx', QVariant.Int)])
    expression=QgsExpression('z(start_point(exterior_ring($geometry)))')
    context = QgsExpressionContext()
    toDelete=[]
    with edit(poly):
        for f in poly.getFeatures():
            context.setFeature(f)
            f['Z'] = expression.evaluate(context)
            f['sc_idx'] = scenario_idx
            if(f['Z']==0):
                toDelete.append(f.id())
            poly.updateFeature(f)
    pr.deleteFeatures(toDelete)

    # Dissolve:
    print(f"{utils.now()} Start dissolve on Z attribute.")
    outname=f'{output_dir}\\tmp_{scenario_idx}_dissolved.gpkg'
    parameters={
        'INPUT':poly,
        'FIELD':['Z'],
        'OUTPUT':outname
    }
    processing.run("native:dissolve", parameters)

    # Single part to multipart
    print(f"{utils.now()} Start multipart to singlepart.")
    input=outname
    outname=f'{output_dir}\\tmp_{scenario_idx}_poly2.gpkg'
    parameters={
        'INPUT':input,
        'OUTPUT':outname}
    processing.run("native:multiparttosingleparts", parameters )

    # Delete by area
    print(f"{utils.now()} Start delete small polygons.")
    poly = QgsVectorLayer(f'{outname}|layername=tmp_{scenario_idx}_poly2', '', 'ogr')
    pr = poly.dataProvider()
    expression=QgsExpression('$area')
    context = QgsExpressionContext()
    toDelete=[]
    for f in poly.getFeatures():
        context.setFeature(f)
        area = expression.evaluate(context)
        if( area < 9):
            # print(f'area={area}')
            toDelete.append(f.id())
    pr.deleteFeatures(toDelete)
    print(f"{utils.now()} Delete by area.")

    # Fill holes
    print(f"{utils.now()} Start delete holes.")
    outname=f'{output_dir}\\tmp_{scenario_idx}_poly3.gpkg'
    parameters={
        'INPUT': poly,
        'MIN_AREA':9,
        'OUTPUT': outname
    }
    processing.run("native:deleteholes", parameters)

    # Simplify geometry
    print(f"{utils.now()} Start simplify geometry.")
    outname=f'{output_dir}\\tmp_{scenario_idx}_simplified.gpkg'
    parameters={
        'INPUT':f'{output_dir}tmp_{scenario_idx}_poly3.gpkg|layername=tmp_{scenario_idx}_poly3',
        'METHOD':0,'TOLERANCE':0.3,
        'OUTPUT': outname
    }
    processing.run("native:simplifygeometries", parameters)

    # Delete holes again
    print(f"{utils.now()} Start delete holes.")
    outname=f'{output_dir}\\tmp_{scenario_idx}_poly3.gpkg'
    parameters={
        'INPUT': f'{output_dir}\\tmp_{scenario_idx}_simplified.gpkg',
        'MIN_AREA':9,
        'OUTPUT': f'{output_dir}\\tmp_{scenario_idx}_filled.gpkg'
    }
    processing.run("native:deleteholes", parameters)

    # promote to multipart
    print(f"{utils.now()} Start multipart collection.")
    outname=f'{output_dir}\\{scenario_idx}_water_covarage_classes.shp'
    parameters = {
        'INPUT':f'{output_dir}\\tmp_{scenario_idx}_filled.gpkg|layername=tmp_{scenario_idx}_filled',
        'FIELD':['Z'],
        'OUTPUT':outname
    }
    processing.run("native:collect", parameters)

    outname=f'{output_dir}\\{scenario_idx}_water_covarage_classes.gpkg'
    parameters = {
        'INPUT':f'{output_dir}/tmp_{scenario_idx}_filled.gpkg|layername=tmp_{scenario_idx}_filled',
        'FIELD':['Z'],
        'OUTPUT':outname
    }
    processing.run("native:collect", parameters)

    print(f"{utils.now()} Finished coverage pipeline for scenario {scenario_idx}.")