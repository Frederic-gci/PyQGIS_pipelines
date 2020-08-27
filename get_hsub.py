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

from qgis.core import *
import qgis.utils
from qgis.analysis import *
from qgis.PyQt.QtCore import QVariant
sys.path.append('/usr/share/qgis/python/plugins')  # system specific

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
if not os.path.exists(args.output_dir):
    os.makedirs(args.output_dir)
if not os.path.exists(args.tmp_dir):
    os.makedirs(args.tmp_dir)

fh = open(f'{args.output_dir}/{args.model}_water_data.txt', "w")
header = f'building_id,sc_idx,z_water,e_surf,e_isol,hsub,model\n'
fh.write(header)

file_glob = args.wse.replace("{sc_idx}", "\*")

print(
    f'get_hsub: {utils.now()} Creating filled coverage from WSE files.', flush=True)
get_filled_coverage_command = (
    f'python3 runner.py '
    f'--function get_filled_coverage '
    f'--arguments \'{{"output_dir": "{args.tmp_dir}" }}\' '
    f'--files {file_glob} '
    f'--threads 6'
)
os.system(get_filled_coverage_command)
print(
    f'get_hsub: {utils.now()} Finished the creation of filled_coverage files.', flush=True)

print(
    f'get_hsub: {utils.now()} Creating wse points from WSE files.', flush=True)
get_wse_points_command = (
    f'python3 runner.py --function get_wse_points '
    f'--arguments \'{{"output_dir": "{args.tmp_dir}" }}\' '
    f'--files {file_glob} '
    f'--threads 16'
)
os.system(get_wse_points_command)
print(
    f'get_hsub: {utils.now()} Finished the creation of  wse points files.', flush=True)

QgsApplication.setPrefixPath("/usr/share/qgis/", True)
qgs = QgsApplication([], False)
qgs.initQgis()
with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    import processing
    from processing.core.Processing import Processing

Processing.initialize()
qgs.processingRegistry().addProvider(QgsNativeAlgorithms())

def qgis_treatment():
    buildings = QgsVectorLayer(args.buildings, '', 'ogr')
    ## Adding an empty field if using the grass7:v-distance algorithm
    # buildings.dataProvider().addAttributes(
    #     [QgsField('nearest_Z', QVariant.Double)])
    # buildings.updateFields()
    # buildings.selectAll()

    for sc_idx in range(1, args.scenarios + 1):
        wse_file = args.wse.format(sc_idx=sc_idx)

        path, basename = os.path.split(wse_file)
        print(
            f'get_hsub: {utils.now()} Getting hsub data for scenario {sc_idx}.', flush=True)
        name, ext = os.path.splitext(basename)
        filled_coverage = f'{args.tmp_dir}filled_coverage_{name}.shp'
        wse_points = f'{args.tmp_dir}points_{name}.shp'

        wse = QgsRasterLayer(wse_file)

        # Join attribute by nearest point
        print(f'   {utils.now()} Starting "native:joinbynearest".', flush=True)
        buildings_with_nearest = f'{args.tmp_dir}/buildings_with_nearest_{sc_idx}.shp'
        parameters = {
            'INPUT': buildings,
            'INPUT_2': wse_points,
            'FIELDS_TO_COPY': ['Z'],
            'DISCARD_NONMATCHING': False,
            'PREFIX': f'{sc_idx}_',
            'NEIGHBORS': 1,
            'MAX_DISTANCE': None,
            'OUTPUT': buildings_with_nearest
        }
        processing.run("native:joinbynearest", parameters)

        # # Join attributes using grass7:v.distance instead of joinbynearest
        # print(f'   {utils.now()} Starting "grass7:v.distance".', flush=True)
        # buildings_with_nearest = f'{args.tmp_dir}/buildings_with_nearest_{sc_idx}.shp'
        # parameters = {
        #     'from': buildings,
        #     'from_type': [3],  # area
        #     'to': wse_points,
        #     'to_type': [0],  # point
        #     'dmax': -1,  # no maximum distance
        #     'dmin': -1,  # no minimum distance
        #     'upload': [6],  # attribute from the 'to' table
        #     'column': 'nearest_Z',  # column where the uploaded value will be stored
        #     'to_column': 'Z',  # attribute from the 'to' table to be copied
        #     'from_output': buildings_with_nearest
        # }
        # processing.run('grass7:v.distance', parameters)

        buildings_with_nearest = QgsVectorLayer(
            buildings_with_nearest, '', 'ogr')

        # Add zonal stats to building
        print(f'   {utils.now()} Starting "QgsZonalStatistics".', flush=True)
        zonalstats = QgsZonalStatistics(
            polygonLayer=buildings_with_nearest,
            rasterLayer=wse,
            rasterBand=1,
            attributePrefix=f'{sc_idx}_',
            stats=QgsZonalStatistics.Max
        )
        zonalstats.calculateStatistics(None)

        ## Get ids of buildings intersecting with filled coverage
        # I need to use buidings_with_nearest, since IDs might have been changed from the 'buildings' layer.
        print(f'   {utils.now()} Starting "native:selectbylocation".', flush=True)
        processing.run('native:selectbylocation', {
            'INPUT': buildings_with_nearest,
            'PREDICATE': [0],
            'INTERSECT': filled_coverage,
            'METHOD': 0, }
        )
        filled_ids = buildings_with_nearest.selectedFeatureIds()

        seen_buildings=[]
        print(f'   {utils.now()} Starting the getFeatures() loop.', flush=True)
        for building in buildings_with_nearest.getFeatures():
            building_id = int(building[building_id_attr])
            # Break out of loop if the building has been studied already
            # In which case, the zonal max will be used, so no new info will be collected anyway
            if( building_id in seen_buildings): continue
            seen_buildings = seen_buildings + [building_id]
            feature_id = building.id()
            scenario_id = sc_idx
            max = building[f'{sc_idx}_Max']
            distance = building['distance']
            Esurf = max != qgis.core.NULL
            Eisol = feature_id in filled_ids and not Esurf
            if(Esurf):
                zWater = building[f'{sc_idx}_Max']  # max from WSE file
            else:
                zWater = building[f'{sc_idx}_Z'] # zWater = building['nearest_Z']  # value from nearest point if using v-distance
            Hsub = zWater - building[building_elev_attr]
            data = (
                f'{str(building_id)},{str(scenario_id)},'
                f'{str(zWater)},{str(Esurf)},{str(Eisol)},{str(Hsub)},'
                f'"{str(args.model)}",{str(distance)}\n'
            )
            fh.write(data)
            del(feature_id, building_id, scenario_id, Esurf, Eisol, zWater, Hsub, data, distance)

qgis_treatment()
fh.close()
qgs.exitQgis()
