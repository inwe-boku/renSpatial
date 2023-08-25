import numpy as np
from shapely.geometry import Polygon


def detect_roof_ridges(dhm_data, roof_polygon):
    # Convert DHM data to a numpy array (assuming it's a 2D array of elevations)
    elevation_array = np.array(dhm_data)

    # Create a mask for the roof area within the polygon
    roof_mask = np.zeros_like(elevation_array, dtype=bool)
    min_x, min_y, max_x, max_y = roof_polygon.bounds
    min_x, min_y, max_x, max_y = int(min_x), int(min_y), int(max_x), int(max_y)
    roof_mask[min_y:max_y, min_x:max_x] = True

    # Apply the mask to the elevation data
    roof_elevations = elevation_array[roof_mask]

    # Calculate ridge points (for simplicity, let's consider points with higher elevation than their neighbors)
    ridge_points = []
    for y in range(1, roof_elevations.shape[0] - 1):
        for x in range(1, roof_elevations.shape[1] - 1):
            neighbors = [
                roof_elevations[y - 1, x - 1],
                roof_elevations[y - 1, x],
                roof_elevations[y - 1, x + 1],
                roof_elevations[y, x - 1],
                roof_elevations[y, x],
                roof_elevations[y, x + 1],
                roof_elevations[y + 1, x - 1],
                roof_elevations[y + 1, x],
                roof_elevations[y + 1, x + 1],
            ]
            if roof_elevations[y, x] > max(neighbors):
                ridge_points.append((x + min_x, y + min_y))

    return ridge_points


# Example usage
dhm_data = ...  # Replace with your DHM data (2D array of elevations)
roof_coords = [
    (x1, y1),
    (x2, y2),
    (x3, y3),
    ...,
]  # Replace with your polygon's coordinates
roof_polygon = Polygon(roof_coords)

ridge_points = detect_roof_ridges(dhm_data, roof_polygon)
print("Detected Ridge Points:", ridge_points)
