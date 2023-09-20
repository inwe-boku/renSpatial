import os, sys
import renspatial as rs
import pandas as pd
import geopandas as gpd

input_shapefile = "data/LCarea.shp"
output_shapefile = "output_random_points.shp"
min_points = 1  # Minimum number of points per polygon
max_points = 20  # Maximum number of points per polygon
min_distance = 50  # Minimum distance between points (adjust as needed)

gdf = gpd.read_file(input_shapefile)
random_points_gdf = gpd.GeoDataFrame(columns=["geometry"])

for idx, row in gdf.iterrows():
    print(idx, row)
    polygon = row["geometry"]
    area = polygon.area
    num_points = min_points + int((max_points - min_points) * (area / 5000))
    print(area, num_points)
    random_points = rs.spatial.random_points(polygon, num_points, min_distance, gdf.crs)
    random_points_gdf = gpd.GeoDataFrame(
        pd.concat([random_points_gdf, random_points], ignore_index=True)
    )

# Save the random points to a new shapefile
random_points_gdf.to_file(output_shapefile)
