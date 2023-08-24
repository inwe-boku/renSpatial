import geopandas as gpd
import argparse
from shapely.geometry import Polygon


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

    clipped_points.to_file(args.output, driver="ESRI Shapefile")
    print("Clipped points saved to", args.output)


def regular_points(polygon, spacing=100):
    extent_polygon = Polygon([(xmin, ymin), (xmin, ymax), (xmax, ymax), (xmax, ymin)])

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

    # Save the grid points as a GeoPackage file
    output_gpkg = "grid_points.gpkg"
    grid_gdf.to_file(output_gpkg, driver="GPKG")

    print("Grid points saved to", output_gpkg)

if __name__ == "__main__":
    main()
