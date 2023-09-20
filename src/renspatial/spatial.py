import geopandas as gpd
import pandas as pd
import rasterio
from rasterio.warp import calculate_default_transform, reproject
import numpy as np
import concurrent.futures
import random
from shapely.geometry import Polygon, Point


def process_chunks_parallel(
    gpkg_filepath, chunk_size, processing_function, num_workers
):
    """
    Process chunks of data from a GeoPackage file in parallel using a thread pool.

    This function reads the GeoPackage file in chunks, and each chunk is processed
    in parallel using multiple worker threads. The processed chunks are then stitched
    together into a complete GeoDataFrame.

    Parameters:
        gpkg_filepath (str): Path to the GeoPackage file.
        chunk_size (int): Size of each chunk.
        processing_function (function): Function to process each chunk.
        num_workers (int): Number of worker threads in the thread pool.

    Returns:
        geopandas.GeoDataFrame: A complete GeoDataFrame containing the processed data.
    """
    chunks = gpd.read_file(gpkg_filepath, iterator=True, chunksize=chunk_size)

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
        processed_results = list(executor.map(processing_function, chunks))

    complete_gdf = gpd.GeoDataFrame(pd.concat(processed_results, ignore_index=True))
    return complete_gdf


def regular_points(polygon, spacing=100):
    """
    Generate a GeoDataFrame containing a regular grid of points within a specified polygon extent.

    Parameters:
        polygon (shapely.geometry.Polygon): The polygon representing the extent within which to create the grid.
        spacing (float): The spacing between grid points (default is 100).

    Returns:
        geopandas.GeoDataFrame: A GeoDataFrame containing the generated regular grid points.
    """
    extent_polygon = polygon

    # Create grid points within the extent
    x_coords = np.arange(extent_polygon.bounds[0], extent_polygon.bounds[2], spacing)
    y_coords = np.arange(extent_polygon.bounds[1], extent_polygon.bounds[3], spacing)

    grid_points = []
    for x in x_coords:
        for y in y_coords:
            point = Point(x, y)
            if point.within(extent_polygon):
                grid_points.append(point)

    # Create a GeoDataFrame from the grid points
    grid_gdf = gpd.GeoDataFrame(grid_points, columns=["geometry"])

    return grid_gdf


def random_points(polygon, num_points, spacing=100, crs="EPSG:3857"):
    """
    Generates random points within a polygon while enforcing a minimum spacing between points.

    Parameters:
    - polygon (shapely.geometry.Polygon): The polygon in which to generate random points.
    - num_points (int): The number of random points to generate.
    - spacing (float, optional): The minimum spacing between points (default is 100).

    Returns:
    - List[shapely.geometry.Point]: A list of random points within the polygon.

    The function generates random points within the specified polygon. It ensures that the
    generated points are at least 'spacing' units away from each other within the polygon.

    Example:
    ```python
    from shapely.geometry import Polygon
    polygon = Polygon([(0, 0), (0, 100), (100, 100), (100, 0)])
    random_points = generate_random_points_in_polygon(polygon, 10, 20)
    ```

    This example generates 10 random points within the polygon with a minimum spacing of 20 units between points.
    """
    points = []
    min_x, min_y, max_x, max_y = polygon.bounds
    while len(points) < num_points:
        x = random.uniform(min_x, max_x)
        y = random.uniform(min_y, max_y)
        point = Point(x, y)
        if polygon.contains(point):
            if all(
                point.distance(existing_point) >= spacing for existing_point in points
            ):
                points.append(point)
    return gpd.GeoDataFrame(points, columns=["geometry"], crs=crs)


def clip_points():
    parser = argparse.ArgumentParser(
        description="Clip points using a polygon and save as a shapefile."
    )
    parser.add_argument("points", help="Path to the points shapefile")
    parser.add_argument("polygon", help="Path to the polygon shapefile")
    parser.add_argument("output", help="Path to the output clipped points shapefile")
    args = parser.parse_args()

    points_gdf = gpd.read_file(args.points)
    polygon_gdf = gpd.read_file(args.polygon)

    # Assuming the polygon shapefile contains a single polygon
    polygon = polygon_gdf.geometry.iloc[0]

    clipped_points = points_gdf[points_gdf.geometry.within(polygon)]

    return clipped_points


def reproject_vector_layer(input_gdf, target_crs):
    """
    Reproject a vector GeoDataFrame to a new coordinate reference system (CRS).

    Parameters:
        input_gdf (geopandas.GeoDataFrame): Input vector GeoDataFrame.
        target_crs (str): Target CRS in Proj4 or EPSG format (e.g., 'EPSG:4326').

    Returns:
        geopandas.GeoDataFrame: Reprojected GeoDataFrame.
    """
    reprojected_gdf = input_gdf.to_crs(target_crs)
    return reprojected_gdf


def reproject_raster_layer(input_raster, target_crs):
    """
    Reproject a raster layer to a new coordinate reference system (CRS).

    Parameters:
        input_raster (rasterio.DatasetReader): Input raster dataset.
        target_crs (dict): Target CRS in rasterio's CRS format (e.g., {'init': 'EPSG:4326'}).

    Returns:
        numpy.ndarray: Reprojected raster data.
    """
    transform, width, height = calculate_default_transform(
        input_raster.crs,
        target_crs,
        input_raster.width,
        input_raster.height,
        *input_raster.bounds,
    )

    kwargs = input_raster.meta.copy()
    kwargs.update(
        {"crs": target_crs, "transform": transform, "width": width, "height": height}
    )

    reprojected_data = np.zeros(
        (input_raster.count, height, width), dtype=input_raster.dtypes[0]
    )
    with rasterio.open("reprojected.tif", "w", **kwargs) as dst:
        for i in range(1, input_raster.count + 1):
            reproject(
                source=rasterio.band(input_raster, i),
                destination=reprojected_data[i - 1],
                src_transform=input_raster.transform,
                src_crs=input_raster.crs,
                dst_transform=transform,
                dst_crs=target_crs,
                resampling=rasterio.warp.Resampling.nearest,
            )

    return reprojected_data


def sample_raster_from_points(point_layer, raster_path):
    """
    Sample raster values at the locations of points in a GeoDataFrame.

    Parameters:
        point_layer (geopandas.GeoDataFrame): GeoDataFrame containing point locations.
        raster_path (str): Path to the raster file.

    Returns:
        numpy.ndarray: Array of sampled raster values at the points.
    """
    with rasterio.open(raster_path) as raster:
        values = []
        for _, point in point_layer.iterrows():
            geom = point.geometry
            if geom is not None:
                row, col = raster.index(geom.x, geom.y)
                if 0 <= row < raster.height and 0 <= col < raster.width:
                    value = raster.read(1, window=((row, row + 1), (col, col + 1)))
                    values.append(value[0][0])
                else:
                    values.append(np.nan)
            else:
                values.append(np.nan)
        return np.array(values)


def sample_average_raster_around_points(grid_gdf, raster_path, window_size):
    """
    Sample the average raster value around each point in a GeoDataFrame.

    Parameters:
        grid_gdf (geopandas.GeoDataFrame): GeoDataFrame containing grid points.
        raster_path (str): Path to the raster file.
        window_size (int): Size of the search window around each point.

    Returns:
        numpy.ndarray: Array of average raster values around the points.
    """
    with rasterio.open(raster_path) as raster:
        values = []
        for _, point in grid_gdf.iterrows():
            geom = point.geometry
            if geom is not None:
                x, y = geom.x, geom.y
                row, col = raster.index(x, y)

                # Define a window around the point
                window = (
                    (row - window_size, row + window_size + 1),
                    (col - window_size, col + window_size + 1),
                )

                # Read the values within the window
                data = raster.read(1, window=window)

                # Calculate the average value
                avg_value = np.nanmean(data)
                values.append(avg_value)
            else:
                values.append(np.nan)
        return np.array(values)


def sample_values_around_points(grid_gdf, raster_path, window_size):
    """
    Sample raster values around each point in a GeoDataFrame.

    Parameters:
        grid_gdf (geopandas.GeoDataFrame): GeoDataFrame containing grid points.
        raster_path (str): Path to the raster file.
        window_size (int): Size of the search window around each point.

    Returns:
        list of dict: List of dictionaries containing sampled values and statistics.
    """
    with rasterio.open(raster_path) as raster:
        values = []
        for _, point in grid_gdf.iterrows():
            geom = point.geometry
            if geom is not None:
                x, y = geom.x, geom.y
                row, col = raster.index(x, y)

                # Define a window around the point
                window = (
                    (row - window_size, row + window_size + 1),
                    (col - window_size, col + window_size + 1),
                )

                # Read the values within the window
                data = raster.read(1, window=window)

                # Filter out NaN values
                valid_data = data[~np.isnan(data)]

                # Calculate statistics
                value_stats = {
                    "values": valid_data.tolist(),
                    "count": len(valid_data),
                    "percentage": (len(valid_data) / (2 * window_size + 1) ** 2) * 100,
                }
                values.append(value_stats)
            else:
                values.append(None)
        return values


def generate_random_points_within_polygons(polygon_layer, points_per_area=0.0001):
    """
    Generate random points within polygons in a GeoDataFrame.

    Parameters:
        polygon_layer (geopandas.GeoDataFrame): GeoDataFrame containing polygons.
        points_per_area (float): Number of points per unit area (default is 0.0001).

    Returns:
        geopandas.GeoDataFrame: GeoDataFrame containing generated random points.
    """
    random_points = []

    for _, polygon in polygon_layer.iterrows():
        area = polygon.geometry.area
        num_points = int(np.ceil(area * points_per_area))
        points = []

        while len(points) < num_points:
            point = Point(
                random.uniform(polygon.geometry.bounds[0], polygon.geometry.bounds[2]),
                random.uniform(polygon.geometry.bounds[1], polygon.geometry.bounds[3]),
            )

            if point.within(polygon.geometry):
                points.append(point)

        random_points.extend(points)

    random_points_gdf = gpd.GeoDataFrame(random_points, columns=["geometry"])
    return random_points_gdf


def calculate_average_roof_pitch(dhm_path, roof_mask_path):
    """
    Calculate the average roof pitch within the masked DHM.

    Parameters:
        dhm_path (str): Path to the Digital Height Model (DHM) raster file.
        roof_mask_path (str): Path to the roof mask raster file (1 for roofs, 0 for non-roofs).

    Returns:
        float: Average roof pitch in degrees.
    """
    with rasterio.open(dhm_path) as dhm:
        dhm_data = dhm.read(1)

    with rasterio.open(roof_mask_path) as mask:
        roof_mask = mask.read(1)

    roof_heights = dhm_data[roof_mask == 1]
    roof_slopes = np.arctan(roof_heights / dhm.res[0]) * (
        180 / np.pi
    )  # Convert to degrees

    average_roof_pitch = np.nanmean(roof_slopes)
    return average_roof_pitch


def segment_dhm_by_slope_and_azimuth(dhm_path, slope_thresholds, azimuth_thresholds):
    """
    Segment DHM data into slope and azimuth categories based on provided thresholds.

    Parameters:
        dhm_path (str): Path to the Digital Height Model (DHM) raster file.
        slope_thresholds (list): List of slope thresholds defining slope categories.
        azimuth_thresholds (list): List of azimuth thresholds defining azimuth categories.

    Returns:
        numpy.ndarray: Array with segmented slope and azimuth categories.
    """
    with rasterio.open(dhm_path) as dhm:
        dhm_data = dhm.read(1)
        dhm_transform = dhm.transform

    slope_data = np.arctan(np.gradient(dhm_data, *dhm_transform[0:2]) * (180 / np.pi))
    azimuth_data = np.arctan2(
        np.gradient(dhm_data, *dhm_transform[0:2])[1],
        np.gradient(dhm_data, *dhm_transform[0:2])[0],
    ) * (180 / np.pi)

    segmented_data = np.zeros_like(slope_data, dtype=np.uint8)

    for i, slope_threshold in enumerate(slope_thresholds):
        for j, azimuth_threshold in enumerate(azimuth_thresholds):
            mask = (slope_data <= slope_threshold) & (azimuth_data <= azimuth_threshold)
            segment_id = i * len(azimuth_thresholds) + j + 1
            segmented_data[mask] = segment_id

    return segmented_data
