############################################
# this module takes one or more geopoints,
# a configuration for a pv system (angles, modules, ...),
# radiation and temperature data from a netcdf file
# and returns the calculated electrical output
############################################

import pandas as pd
import numpy as np
import geopandas as gpd
import pvlib


def process_geopoints(geopoints_data):
    # Usage examples

    # Option 1: Provide a file path
    process_geopoints("geopoints.geojson")

    # Option 2: Provide a GeoDataFrame directly
    geopoints_data = gpd.GeoDataFrame(
        {
            "latitude": [40.7128, 34.0522],
            "longitude": [-74.0060, -118.2437],
            "geometry": [gpd.points_from_xy([-74.0060, -118.2437], [40.7128, 34.0522])],
        }
    )
    process_geopoints(geopoints_data)


def get_geopoints(geopoints_data):
    if isinstance(geopoints_data, str):
        return gpd.read_file(geopoints_data)
    elif isinstance(geopoints_data, gpd.GeoDataFrame):
        return geopoints_data
    else:
        raise ValueError("Invalid input. Must be a file path or a GeoDataFrame.")


def calculate_pvoutput(geopoints_data, radiation_data, pv_system_config):
    # Load the geopoints GeoDataFrame
    geopoints = gpd.read_file(geopoints_data)

    # Load the radiation data (assuming it's a pandas DataFrame)
    radiation = pd.read_csv(radiation_data)

    # Initialize a PVSystem from pvlib with the given configuration
    pv_system = pvlib.pvsystem.PVSystem(
        surface_tilt=pv_system_config["tilt_angle"],
        surface_azimuth=pv_system_config["azimuth_angle"],
        module_parameters=pvlib.pvsystem.retrieve_sam(pv_system_config["module_name"]),
    )

    # Prepare arrays for results
    electrical_outputs = []

    # Loop through each geopoint and calculate electrical output
    for index, row in geopoints.iterrows():
        latitude = row["latitude"]
        longitude = row["longitude"]

        solar_position = pvlib.solarposition.get_solarposition(
            radiation.index, latitude, longitude
        )

        dni = radiation["dni"]
        dhi = radiation["dhi"]
        ghi = radiation["ghi"]

        effective_irradiance = pvlib.irradiance.get_total_irradiance(
            surface_tilt=pv_system.surface_tilt,
            surface_azimuth=pv_system.surface_azimuth,
            solar_zenith=solar_position["apparent_zenith"],
            solar_azimuth=solar_position["azimuth"],
            dni=dni,
            ghi=ghi,
            dhi=dhi,
        )

        dc_power = pv_system.dc_power(
            effective_irradiance["poa_global"],
            temperature=pv_system_config["temperature"],
        )

        electrical_output = np.sum(dc_power) * pv_system_config["module_efficiency"]
        electrical_outputs.append(electrical_output)

    return electrical_outputs


def main():
    # Example configuration
    pv_system_config = {
        "tilt_angle": 30,  # degrees
        "azimuth_angle": 180,  # degrees
        "module_name": "Aleo_Solar_S79y280",
        "module_efficiency": 0.18,
        "temperature": 25,  # Celsius
    }

    # for pvsys in config['pvsystem'].keys():
    #
    #        print(pvsys)
    #        [rDHI, rShade, rTransp] = relative_diffuse_ratio(config['pvsystem'][pvsys]['distance'],
    #                                                            config['pvsystem'][pvsys]['height'],
    #                                                            config['pvsystem'][pvsys]['tilt'])
    #        mcsys = pvsystem(pvsys, pvlib.location.Location(
    #            prow['geometry'].y, prow['geometry'].x, altitude=json.loads(prow['altitude'])[0]))
    #        mcsim = mcsys.run_model(hdata)
    #        # with pd.option_context('display.max_rows', None):
    #        res = mcsim.results.ac

    # Example usage
    geopoints_data = "data/randompointsAT.geojson"
    radiation_data = "radiation.csv"
    electrical_outputs = calculate_pvoutput(
        geopoints_data, radiation_data, pv_system_config
    )

    for index, output in enumerate(electrical_outputs):
        print(f"Geopoint {index}: Electrical Output = {output} kWh")


if __name__ == "__main__":
    main()
