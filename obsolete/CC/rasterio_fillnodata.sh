#!/bin/bash

## Date: 2020-04-27
## Author: Frederic Fournier
## Goal: Run rasterio fillnodata on 157 raster from INFO-Crue, Jacques-Cartier river.

## For each file in the input directory, this script creates a python
## script with the rasterio command, and a sbatch script that creates the
## python environment and then launch the python script. 
## Then it submits the task to the scheduler.

workdir="/home/frederic/projects/def-franc/frederic/rasterio"

for file in `find ${workdir}/input/ -iname "*.tif"`
do

scenario=$(basename ${file} '.tif')
num=$(echo ${scenario} | tr -dc '0-9')
distance=750.0
if ((${num} > 149))
then
distance=550.0
elif ((${num} > 99))
then distance=600.0
elif ((${num} > 49))
then
distance=700.0
fi

py_script="${workdir}/scripts/${scenario}.py"
slurm_script="${workdir}/scripts/${scenario}.slurm.sh"
output="${workdir}/output/${scenario}.out.tif"

echo "
import rasterio
import rasterio.mask
import rasterio.fill
from datetime import datetime
import time

tic = time.perf_counter()
print('Starting to process${scenario}:', datetime.now())
dataset=rasterio.open('${file}')
profile=dataset.profile
mask=dataset.read_masks(1)
data=dataset.read(1)
filled=rasterio.fill.fillnodata(image=data,mask=mask,max_search_distance=${distance})
del mask, data, dataset
with rasterio.open('${output}', 'w', **profile) as dst:
  dst.write(filled,1)
print('Finished to process${scenario}:', datetime.now())
toc = time.perf_counter()
print(f'Filled ${distance}m in {toc-tic:0.4f} seconds.')

" > ${py_script}

echo "#!/bin/bash
#SBATCH --account=def-franc
#SBATCH --time=2:30:00
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem-per-cpu=36000M
#SBATCH --output=${workdir}/slurm_output/${scenario}.out
#SBATCH --error=${workdir}/slurm_output/${scenario}.err

module load python/3.8.2
virtualenv --no-download \$SLURM_TMPDIR/env
source \$SLURM_TMPDIR/env/bin/activate
pip install --no-index --upgrade pip
pip install --no-index rasterio

python ${py_script}

" > ${slurm_script}

#sbatch ${slurm_script}

done

