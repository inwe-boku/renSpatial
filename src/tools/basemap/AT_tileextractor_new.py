#!/usr/bin/python

import os
import math
import geopandas as gpd
import pandas as pd
import mapbox_vector_tile
import fiona
from shapely.geometry import Polygon, MultiPolygon


def calculate_tile_indices(lon, lat, zoom_level):
    """
    Extracts building features from a PBF vector tile and appends them to a GeoPackage.

    This function takes an input PBF vector tile file, extracts building features from a specified
    layer within the tile, and appends these features to a provided GeoPackage. The extracted
    building geometries are transformed into Shapely geometry objects and appended to the GeoPackage's
    geometry column.

    Args:
        input_file (str): Path to the PBF vector tile file.
        gpkg (geopandas.GeoDataFrame): GeoPackage to which the extracted features will be appended.
        tilecrs (str): CRS information for the tile, e.g., "EPSG:3857".

    Returns:
        geopandas.GeoDataFrame: Updated GeoPackage with the extracted building features appended.
    """
    n = 2**zoom_level
    x = int((lon + 180.0) / 360.0 * n)
    y = int(
        (
            1.0
            - (
                math.log(
                    math.tan(math.radians(lat)) + 1.0 / math.cos(math.radians(lat))
                )
                / math.pi
            )
        )
        / 2.0
        * n
    )
    return x, y


def extract_buildings(input_file, gpkg, tilecrs):
    """
    Extracts building features from a PBF vector tile and appends them to a GeoPackage.

    This function takes an input PBF vector tile file, extracts building features from a specified
    layer within the tile, and appends these features to a provided GeoPackage. The extracted
    building geometries are transformed into Shapely geometry objects and appended to the GeoPackage's
    geometry column.

    Args:
        input_file (str): Path to the PBF vector tile file.
        gpkg (geopandas.GeoDataFrame): GeoPackage to which the extracted features will be appended.
        tilecrs (str): CRS information for the tile, e.g., "EPSG:3857".

    Returns:
        geopandas.GeoDataFrame: Updated GeoPackage with the extracted building features appended.
    """
    pbf_path = input_file
    with open(pbf_path, "rb") as pbf_file:
        tile_data = pbf_file.read()

    layer_name = "GEBAEUDE_F_GEBAEUDE"
    decoded_tile = mapbox_vector_tile.decode(tile_data)
    layer_features = decoded_tile.get(layer_name, [])

    if len(layer_features) == 0:
        return gpkg

    shapely_geometries = []
    for feature in layer_features:
        geometry = feature["geometry"]
        if geometry["type"] == "Polygon":
            shapely_geometries.append(Polygon(geometry["coordinates"][0]))
        elif geometry["type"] == "MultiPolygon":
            polygons = [Polygon(coords[0]) for coords in geometry["coordinates"]]
            shapely_geometries.append(MultiPolygon(polygons))
    layer_gdf = gpd.GeoDataFrame(geometry=shapely_geometries)

    with fiona.Env():
        gpkg = gpd.GeoDataFrame(pd.concat([gpkg, layer_gdf], ignore_index=True))
    return gpkg


def main():
    """
    Main function to process tiles and extract building features.
    """
    zoomlevel = 16
    bbox = (9.47996951665, 46.4318173285, 16.9796667823, 49.0390742051)

    minX, maxY = calculate_tile_indices(bbox[0], bbox[1], zoomlevel)
    maxX, minY = calculate_tile_indices(bbox[2], bbox[3], zoomlevel)

    print("Start")
    original_file = "data/%d/%d/%d.pbf"
    out_dir = "vector/"

    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    total_number_of_tiles = (maxX - minX + 1) * (maxY - minY + 1)
    number_of_tiles_processed = 0

    gpkg_file = "vector/buildings.gpkg"
    if os.path.exists(gpkg_file):
        gpkg = gpd.read_file(gpkg_file)
    else:
        gpkg = gpd.GeoDataFrame()

    tilecrs = "EPSG:3857"

    for x in range(minX, maxX + 1):
        for y in range(minY, maxY + 1):
            print("Processing tile %d / %d." % (x, y))
            filename = original_file % (zoomlevel, x, y)

            if os.path.isfile(filename) and os.path.getsize(filename) > 0:
                gpkg = extract_buildings(filename, gpkg, tilecrs)
            else:
                print("Error: Tile %d / %d does not exist or is empty." % (x, y))

            number_of_tiles_processed += 1
            percent = (number_of_tiles_processed / total_number_of_tiles) * 100
            print(
                "Processed %d / %d tiles (%.3f%%)"
                % (number_of_tiles_processed, total_number_of_tiles, percent)
            )
    gpkg.to_file(gpkg_file, driver="GPKG")


if __name__ == "__main__":
    main()
