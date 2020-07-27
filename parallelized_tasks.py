import sys
import os
import re
import glob
import importlib
import warnings

# QGIS imports
from qgis.core import *
from qgis.analysis import *
from qgis.PyQt.QtCore import QVariant
sys.path.append('/usr/share/qgis/python/plugins')
with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    import qgis.utils

# local imports
import utilities as utils

# Set up QT to work if no X server:
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

def get_filled_coverage(file, output_dir):
    """Take a WSE tif file and return a polygonized and hole-filled shapefile.

    The filled coverage file is used to detect buildings that might be surrounded
    by water in get_esurf_eisol_hsub.py.
    Keyword arguments:
    file -- a Water Surface Elevation (WSE) in tif format.
    output_dir -- the directory where the resulting file will be written
    """
    basename = os.path.basename(file)
    name, extension = os.path.splitext(basename)

    QgsApplication.setPrefixPath("/usr/share/qgis/", True)
    qgs = QgsApplication([], False)
    QgsApplication.initQgis()
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        import processing
        from processing.core.Processing import Processing
    Processing.initialize()
    QgsApplication.processingRegistry().addProvider(QgsNativeAlgorithms())

    wse = QgsRasterLayer(file)
    filled_coverage = f'{output_dir}/filled_coverage_{name}.shp'
    tmp_bin_wse = f'{output_dir}/bin_{name}.tif'
    tmp_cov = f'{output_dir}/tmp_cov_{name}.shp'
    tmp_filled = f'{output_dir}/tmp_filled_{name}.shp'

    processing.run('native:reclassifybytable', {
        'INPUT_RASTER': wse,
        'RASTER_BAND': 1,
        'TABLE': [0, 6000, 1],
        'NO_DATA': 0,
        'RANGE_BOUNDARIES': 0,  # 0: min < value <= max
        'DATA_TYPE': 0,  # 0: Byte
        'OUTPUT': tmp_bin_wse
    })
    processing.run('gdal:polygonize', {
        'INPUT': tmp_bin_wse,
        'BAND': 1,
        'FIELD': 'DN',
        'EIGHT_CONNECTEDNESS': False,
        'OUTPUT': tmp_cov
    })
    processing.run('native:deleteholes', {
        'INPUT': tmp_cov,
        'OUTPUT': tmp_filled,
        'MIN_AREA': 0,
    })
    processing.run('native:fixgeometries', {
        'INPUT': tmp_filled,
        'OUTPUT': filled_coverage
    })
    os.remove(tmp_bin_wse)
    QgsVectorFileWriter.deleteShapeFile(tmp_filled)
    QgsVectorFileWriter.deleteShapeFile(tmp_cov)

def get_wse_points(file, output_dir):
    """Take a WSE tif file and apply rastertopoints.

    The points_wse file is used to detect the nearest water point elevation.
    Keyword arguments:
    file -- a Water Surface Elevation (WSE) in tif format.
    output_dir -- the directory where the resulting file will be written
    """
    basename = os.path.basename(file)
    name, extension = os.path.splitext(basename)

    QgsApplication.setPrefixPath("/usr/share/qgis/", True)
    qgs = QgsApplication([], False)
    QgsApplication.initQgis()
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        import processing
        from processing.core.Processing import Processing
    Processing.initialize()
    QgsApplication.processingRegistry().addProvider(QgsNativeAlgorithms())

    wse = QgsRasterLayer(file)
    wse_points = f'{output_dir}/points_{name}.shp'
    parameters = {
        'INPUT_RASTER': wse,
        'RASTER_BAND': 1,
        'FIELD_NAME': "Z",
        'OUTPUT': wse_points
    }
    processing.run('native:pixelstopoints', parameters)
