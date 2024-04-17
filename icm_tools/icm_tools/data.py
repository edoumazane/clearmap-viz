#!/usr/bin/env python3

__author__ = "Etienne Doumazane"
__license__ = "MIT"
__version__ = "0.0.1"
__maintainer__ = "Etienne Doumazane"
__email__ = "etienne.doumazane@icm-institute.org"
__status__ = "Development"

"""
This module contains utils to interact with the data of the project.
"""


import json
import sys
from pathlib import Path
from natsort import natsorted

import dask.array as da
import numpy as np
import pandas as pd
import tifffile

from icm_tools.utils import timestamp_error, BOLD, RED, ORANGE, GREEN, ENDC, timestamp_info


def load_img(fpath, swapaxes=True, as_dask_array=True):
    """
    Load a 3D image from a TIF or a NPY file.
    Note: The array is reoriented to have the first dimension as the z-axis.
    input: (str or Path)
    returns: dask array
    """
    if isinstance(fpath, Path):
        fpath = str(fpath)
    if fpath.endswith('.tif') or fpath.endswith('.tiff'):
        if as_dask_array == False:
            return tifffile.imread(fpath)
        store = tifffile.imread(fpath, aszarr=True)
        return da.from_zarr(store)
    elif fpath.endswith('.npy'):
        arr = da.from_array(np.load(fpath, mmap_mode="r"))
        if not as_dask_array:
            arr = arr.compute()
        if swapaxes:
            arr = arr.swapaxes(0,2)
        return arr        
    else:
        timestamp_error(f"Unknown file format for {fpath}")

def save_json(path, data):
    """
    Saves an object as a JSON file.
    """
    with open(path, "w") as f:
        json.dump(data, f)

def save_img_npy(path, img):
    """
    Save a 3D image to a NPY file.
    Note: The array is reoriented to have the first dimension as the z-axis.
    input: (str or Path)
    """
    np.save(path, img.swapaxes(0,2))
