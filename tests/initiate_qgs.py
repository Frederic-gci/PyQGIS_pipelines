# Helper script to initiate the qgs application in a python console.
# Use the next line from the console to initiate qgs
# exec(open("/processing/PyQGIS_pipelines/tests/initiate_qgs.py").read()) 

import sys
import argparse
import os
import warnings

import utilities as utils

from qgis.core import *
import qgis.utils
from qgis.analysis import *
from qgis.PyQt.QtCore import QVariant
sys.path.append('/usr/share/qgis/python/plugins')  # system specific

QgsApplication.setPrefixPath("/usr/share/qgis/", True)
qgs = QgsApplication([], False)
qgs.initQgis()
with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    import processing
    from processing.core.Processing import Processing

Processing.initialize()
qgs.processingRegistry().addProvider(QgsNativeAlgorithms())

