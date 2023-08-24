mport os, sys

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import renspatial as rs
import pandas as pd
import geopandas as gpd
import xarray as xr
import pvlib

dhm_path = "dhm.tif"
slope_thresholds = [5, 15, 30]  # Degrees
azimuth_thresholds = [30, 60, 90]  # Degrees
segmented_data = segment_dhm_by_slope_and_azimuth(dhm_path, slope_thresholds, azimuth_thresholds)

# Plot the segmented data
plt.imshow(segmented_data, cmap='viridis')
plt.colorbar(label='Segment ID')
plt.title('Segmented DHM by Slope and Azimuth')
plt.show()
