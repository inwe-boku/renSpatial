import os, sys
import renspatial as rs
import pandas as pd
import geopandas as gpd
from tqdm import tqdm

input_gpkg = "~/my-data/VGD/VGD.gpkg"


sample_raster(chunk, rasterfile, colname="elevation")

process_chunks_parallel(
    input_gpkg, 1000, processing_function, 12

dissolve_column = "BKZ"

# Use the dissolve function to dissolve by the specified column
vgdBKZ = vgdAT.dissolve(by=dissolve_column, as_index=False)

for idx, row in tqdm(vgdBKZ.iterrows(), total=len(vgdBKZ), desc="Processing"):
    polygon = row["geometry"]
    area = polygon.area
    rgp = rs.spatial.regular_points(polygon, spacing=50)
    rgp["BKZ"] = row["BKZ"]
    rgp["PB"] = row["PB"]
    rgp["BL"] = row["BL"]
    rgp.to_file("~/my-data/VGD/VGD.gpkg", layer=row["BKZ"], driver="GPKG")
