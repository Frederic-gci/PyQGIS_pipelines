"""
From : 
  * A file of buildings (polygons) from the model
  * A folder with the processed WSE
I want a table with these information in each row:
  * building id
  * scenario id
  * Esurf (whether the building intersects with the raw coverage)
  * Eisol (whether the building intersects with the filled coverage, but NOT with the raw coverage)
  * Z-water (the max value of the extended WSE under the building footprint), or the z-value of the point closest to the building.

To do : 
loop over scenario index
  load the proper WSE
  create the scenario coverage
  create the scenario filled coverage
  create a point 
  calculate zonal statistics from the processed WSE
  generate the ids of building that intersect with the coverage for the scenario
  generate the ids of features that intersect with filled coverage for the scenario

  loop over buildings:
    id = get building id
    z-water = get max of extendedWSE
    Esurf = whether the building intersect with coverage
    Eisol = wheter the building intersect with filled AND NOT Esurf.

    write to the table.
"""
import sys
import argparse
import os
import warnings

import utilities as utils

# from qgis.core import *
# import qgis.utils
# from qgis.analysis import *
# from qgis.PyQt.QtCore import QVariant
# sys.path.append('/usr/share/qgis/python/plugins')  # system specific

parser = argparse.ArgumentParser()

parser.add_argument(
    "--wse",
    default='{sc_idx}',
    help="Pattern of path to wse files, where '%(default)s' " +
    "will be replaced by the scenario index.",
    required=True
)
parser.add_argument(
    "--buildings",
    help="Shapefile containing the model's buidling.",
    required=True
)
parser.add_argument(
    "--scenarios",
    help="Number of scenarios.",
    type=int,
    required=True
)
parser.add_argument(
    "--model",
    help="The model name",
    required=True
)
parser.add_argument(
    "--tmp_dir",
    help="Directory for intermediary files.",
    required=False,
    default="/processing/tmp/"
)
parser.add_argument(
    "--output_dir",
    help="Output directory",
    required=False,
    default="/processing/output/"
)
args = parser.parse_args()

# Hard-coded values:
building_elev_attr = 'alt_premie'
building_id_attr = 'batiment_i'

# Prepare output file:
# if not os.path.exists(args.output_dir):
#     os.makedirs(args.output_dir)
# fh = open(f'{args.output_dir}/{args.model}_water_data.txt', "w+")
# header = f'building_id,sc_idx,z_water,e_surf,e_iso,h_sub,model\n'
# fh.write(header)

if not os.path.exists(args.tmp_dir):
    os.makedirs(args.tmp_dir)

print(f'get_esurf_eiso_hsub: {utils.now()} Getting filled coverage from WSE files.')
file_glob = args.wse.replace("{sc_idx}", "\*")
get_filled_coverage_command = (
    f'runner.py --function get_filled_coverage '
    f'--arguments "{{output_dir: {args.tmp_dir} }}" --files {file_glob}'
)
print(get_filled_coverage_command)
# os.system(get_filled_coverage_command)


print(f'get_esurf_eiso_hsub: {utils.now()} Getting wse points from WSE files.')
get_wse_points_command = (
    f'runner.py --function get_filled_coverage '
    f'--arguments "{{output_dir: {args.tmp_dir} }}" --files {file_glob}'
)
print(get_wse_points_command)
# os.system(get_wse_points_command)

# QgsApplication.setPrefixPath("/usr/share/qgis/", True)
# qgs = QgsApplication([], False)
# QgsApplication.initQgis()
# with warnings.catch_warnings():
#     warnings.filterwarnings("ignore", category=DeprecationWarning)
#     import processing
#     from processing.core.Processing import Processing
# Processing.initialize()
# QgsApplication.processingRegistry().addProvider(QgsNativeAlgorithms())

# buildings = QgsVectorLayer(args.buildings, '', 'ogr')
for sc_idx in range(1, args.scenarios + 1):
    wse_file = args.wse.format(sc_idx=sc_idx)
    path, basename = os.path.split(wse_file)
    name, ext = os.path.splitext(basename)

    filled_coverage =f'{args.tmp_dir}filled_coverage_{name}.shp' 
    wse_points = f'{args.tmp_dir}points_{name}.shp'
    print(wse_file)
    print(filled_coverage)
    print(wse_points)
    print(f'{utils.now()} working on {wse_file}')

#     wse = QgsRasterLayer(wse_file)

#     # Get filled_coverage:
#     filled_coverage = f'{args.tmp_dir}/filled_coverage_{sc_idx}.shp'
#     tmp_bin_wse = f'{args.tmp_dir}/bin_{sc_idx}.tif'
#     tmp_cov = f'{args.tmp_dir}/tmp_cov_{sc_idx}.shp'
#     tmp_filled = f'{args.tmp_dir}/tmp_filled_{sc_idx}.shp'

#     processing.run('native:reclassifybytable', {
#         'INPUT_RASTER': wse,
#         'RASTER_BAND': 1,
#         'TABLE': [0, 6000, 1],
#         'NO_DATA': 0,
#         'RANGE_BOUNDARIES': 0,  # 0: min < value <= max
#         'DATA_TYPE': 0,  # 0: Byte
#         'OUTPUT': tmp_bin_wse
#     })
#     processing.run('gdal:polygonize', {
#         'INPUT': tmp_bin_wse,
#         'BAND': 1,
#         'FIELD': 'DN',
#         'EIGHT_CONNECTEDNESS': False,
#         'OUTPUT': tmp_cov
#     })
#     processing.run('native:deleteholes', {
#         'INPUT': tmp_cov,
#         'OUTPUT': tmp_filled,
#         'MIN_AREA': 0,
#     })
#     processing.run('native:fixgeometries', {
#         'INPUT': tmp_filled,
#         'OUTPUT': filled_coverage
#     })

#     os.remove(tmp_bin_wse)
#     QgsVectorFileWriter.deleteShapeFile(tmp_filled)
#     QgsVectorFileWriter.deleteShapeFile(tmp_cov)

#     # Get WSE points
#     wse_points = f'{args.output_dir}/points_{sc_idx}.shp'
#     parameters = {
#         'INPUT_RASTER': wse,
#         'RASTER_BAND': 1,
#         'FIELD_NAME': "Z",
#         'OUTPUT': wse_points
#     }
#     processing.run('native:pixelstopoints', parameters)

#     # Get ids of buildings intersecting with filled coverage
#     processing.run('native:selectbylocation', {
#         'INPUT': buildings,
#         'PREDICATE': [0],
#         'INTERSECT': filled_coverage,
#         'METHOD': 0, }
#     )
#     filled_ids = buildings.selectedFeatureIds()

#     # Join attribute by nearest point
#     buildings_with_nearest = f'{args.tmp_dir}/buildings_with_nearest_{sc_idx}.shp'
#     parameters = {
#         'INPUT': buildings,
#         'INPUT_2': wse_points,
#         'FIELDS_TO_COPY': ['Z'],
#         'DISCARD_NONMATCHING': False,
#         'PREFIX': f'{sc_idx}_',
#         'NEIGHBORS': 1,
#         'MAX_DISTANCE': None,
#         'OUTPUT': buildings_with_nearest
#     }
#     processing.run("native:joinbynearest", parameters)

#     buildings_with_nearest = QgsVectorLayer(buildings_with_nearest, '', 'ogr')

#     # Add zonal stats to building
#     zonalstats = QgsZonalStatistics(
#         polygonLayer=buildings_with_nearest,
#         rasterLayer=wse,
#         rasterBand=1,
#         attributePrefix=f'{sc_idx}_',
#         stats=QgsZonalStatistics.Max
#     )
#     zonalstats.calculateStatistics(None)

#     for building in buildings_with_nearest.getFeatures():
#         feature_id = building.id()
#         building_id = int(building[building_id_attr])
#         scenario_id = sc_idx
#         max = building[f'{sc_idx}_Max']
#         Esurf = max != qgis.core.NULL
#         Eisol = feature_id in filled_ids and not Esurf
#         if(Esurf):
#             zWater = building[f'{sc_idx}_Max']  # max from WSE file
#         else:
#             zWater = building[f'{sc_idx}_Z']  # value from nearest point
#         Hsub = zWater - building[building_elev_attr]
#         to_write = (
#             f'{str(building_id)},{str(scenario_id)},'
#             f'{str(zWater)},{str(Esurf)},{str(Eisol)},{str(Hsub)},'
#             f'{str(args.model)}\n'
#         )
#         fh.write(to_write)

# fh.close()
