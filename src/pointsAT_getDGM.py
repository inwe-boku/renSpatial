import os, sys
import renspatial as rs
import pandas as pd
import geopandas as gpd
from tqdm import tqdm

gpkgfile = "~/my-data/VGD/VGD.gpkg"

rgpAT = gpd.read_file(input_shapefile)

complete_gdf = process_chunks_parallel(
    gpkgfile, chunk_size, sample_elevation, num_workers
)
