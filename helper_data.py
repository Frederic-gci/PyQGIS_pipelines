"""
From : 
  * A vector of building from the scenario
  * A folder with the extended WSE
  * A file with the raw coverage for each scenario
  * A file with the 'filled' coverage for each scenario
I want a table with these information in each row:
  * building id
  * scenario id
  * Esurf (whether the building intersects with the raw coverage)
  * Eisol (whether the building intersects with the filled coverage, but NOT with the raw coverage)
  * Z-water (the max value of the extended WSE under the building footprint)

To do : 
loop over scenario
  load the proper extendedWSE
  calculate zonal statistics
  generate the ids of building that intersect with the coverage for the scenario
  generate the ids of features that intersect with filled coverage for the scenario

  loop over buildings:
    id = get building id
    z-water = get max of extendedWSE
    Esurf = whether the building intersect with coverage
    Eisol = wheter the building intersect with filled AND NOT Esurf.

    write to the table.
"""

# System imports
import sys
import os
import warnings

# QGIS imports
from qgis.core import *
import qgis.utils
from qgis.analysis import *
sys.path.append('C:\\OSGeo4W64\\apps\\qgis\\python\\plugins')

fh = open("output.txt", "w+")

QgsApplication.setPrefixPath("C:\\OSGeo4W64\\apps\\qgis", True)
qgs = QgsApplication([], False)
qgs.initQgis()
with warnings.catch_warnings():
  warnings.filterwarnings("ignore", category=DeprecationWarning)
  import processing
  from processing.core.Processing import Processing
Processing.initialize()
QgsApplication.processingRegistry().addProvider(QgsNativeAlgorithms())

coverages = QgsVectorLayer(
  "D:/Results/INFO-Crue/0508_JacquesCartier/Couverture/JC_raw_coverage_32198.shp",'', 'ogr')

buildings = QgsVectorLayer(
  "C:/A_DATA/tests/0508_batiment.shp", '', 'ogr')

filled_coverages = QgsVectorLayer(
  "D:/Results/INFO-Crue/0508_JacquesCartier/Couverture/JC_raw_coverage_filled_32198.shp",'', 'ogr')

for scenario_num in range(1,152):
  extended_WSE_path=(
    f'D:/Results/INFO-Crue/0508_JacquesCartier/ExtendedWSE/32198/PF{scenario_num}.32198.tif')
  extended_WSE = QgsRasterLayer(extended_WSE_path)

  # Add zonal stats
  zonalstats = QgsZonalStatistics(
    polygonLayer=buildings, 
    rasterLayer=extended_WSE, 
    rasterBand=1,
    attributePrefix=f'{scenario_num}_',
    stats=QgsZonalStatistics.Max
  )
  zonalstats.calculateStatistics(None)

  # Get Esurf ids.
  processing.run('native:selectbylocation', {
    'INPUT': buildings, 
    'PREDICATE': [0],
    'INTERSECT': (
      f"D:/Results/INFO-Crue/0508_JacquesCartier/Couverture/JC_raw_coverage_32198.shp"
      f"|layerid=0|subset=\"scIdx\"={scenario_num}"),
    'METHOD':0, })
  esurf_ids=buildings.selectedFeatureIds()

  # Get Eisol ids
  processing.run('native:selectbylocation', {
    'INPUT': buildings, 
    'PREDICATE': [0],
    'INTERSECT': (
      f"D:/Results/INFO-Crue/0508_JacquesCartier/Couverture/JC_raw_coverage_filled_32198.shp"
      f"|layerid=0|subset=\"scIdx\"={scenario_num}"),
    'METHOD':0, })
  eisol_ids=buildings.selectedFeatureIds()


  for building in buildings.getFeatures(): 
    feature_id = building.id()
    building_id = int(building['batiment_i'])
    scenario_id = scenario_num
    zWater = building[f'{scenario_num}_Max']
    Esurf= feature_id in esurf_ids
    Eisol= feature_id in eisol_ids and not Esurf
    Hsub = zWater - building['alt_premie']
    to_write = f'{str(building_id)},{str(scenario_id)},{str(zWater)},{str(Esurf)},{str(Eisol)},{str(Hsub)}\n'
    fh.write(to_write)

fh.close()
qgs.exitQgis()