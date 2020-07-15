# Copyright 2019 Luke Pinner
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from contextlib import contextmanager

import rasterio
from rasterio import Affine, MemoryFile
from rasterio.enums import Resampling


@contextmanager
def resample_raster(raster, out_path=None, scale=2):
    """ Resample a raster
        multiply the pixel size by the scale factor
        divide the dimensions by the scale factor
        i.e
        given a pixel size of 250m, dimensions of (1024, 1024) and a scale of 2,
        the resampled raster would have an output pixel size of 500m and dimensions of (512, 512)
        given a pixel size of 250m, dimensions of (1024, 1024) and a scale of 0.5,
        the resampled raster would have an output pixel size of 125m and dimensions of (2048, 2048)
        returns a DatasetReader instance from either a filesystem raster or MemoryFile (if out_path is None)
    """
    t = raster.transform

    # rescale the metadata
    transform = Affine(t.a * scale, t.b, t.c, t.d, t.e * scale, t.f)
    height = int(raster.height / scale)
    width = int(raster.width / scale)

    profile = raster.profile
    profile.update(transform=transform, driver='GTiff', height=height, width=width)

    data = raster.read(
            out_shape=(raster.count, height, width),
            resampling=Resampling.bilinear,
        )

    if out_path is None:
        with write_mem_raster(data, **profile) as dataset:
            del data
            yield dataset

    else:
        with write_raster(out_path, data, **profile) as dataset:
            del data
            yield dataset


@contextmanager
def resample_raster_xy(raster, out_path=None, x_scale=2,y_scale=2):
    """ Resample a raster
        multiply the pixel size by the scale factor
        divide the dimensions by the scale factor
        i.e
        given a pixel size of 250m, dimensions of (1024, 1024) and a scale of 2,
        the resampled raster would have an output pixel size of 500m and dimensions of (512, 512)
        given a pixel size of 250m, dimensions of (1024, 1024) and a scale of 0.5,
        the resampled raster would have an output pixel size of 125m and dimensions of (2048, 2048)
        returns a DatasetReader instance from either a filesystem raster or MemoryFile (if out_path is None)
    """
    t = raster.transform

    # rescale the metadata
    transform = Affine(t.a * x_scale, t.b, t.c, t.d, t.e * y_scale, t.f)
    height = int(raster.height / y_scale)
    width = int(raster.width / x_scale)

    profile = raster.profile
    profile.update(transform=transform, driver='GTiff', height=height, width=width)

    data = raster.read(
            out_shape=(raster.count, height, width),
            resampling=Resampling.bilinear,
        )

    if out_path is None:
        with write_mem_raster(data, **profile) as dataset:
            del data
            yield dataset

    else:
        with write_raster(out_path, data, **profile) as dataset:
            del data
            yield dataset


@contextmanager
def write_mem_raster(data, **profile):
    with MemoryFile() as memfile:
        with memfile.open(**profile) as dataset:  # Open as DatasetWriter
            dataset.write(data)

        with memfile.open() as dataset:  # Reopen as DatasetReader
            yield dataset  # Note yield not return


@contextmanager
def write_raster(path, data, **profile):

    with rasterio.open(path, 'w', **profile) as dataset:  # Open as DatasetWriter
        dataset.write(data)

    with rasterio.open(path) as dataset:  # Reopen as DatasetReader
        yield dataset
