import os, sys
import renspatial as rs
import pandas as pd
import geopandas as gpd
import xarray as xr
import pvlib
import json


def pvsystem(pvsys, location):
    cecmodules = pvlib.pvsystem.retrieve_sam("CECMod")
    cecinverters = pvlib.pvsystem.retrieve_sam("CECInverter")
    module_parameters = cecmodules[pvsys["module"]]
    inverter_parameters = cecinverters[pvsys["inverter"]]
    temperature_model_parameters = pvlib.temperature.TEMPERATURE_MODEL_PARAMETERS[
        "sapm"
    ]["open_rack_glass_glass"]
    # temp_strings = 2
    # temp_modules_per_string = 5
    # mult = config['pvsystem'][pvsys]['modules_per_string'] * \
    #    config['pvsystem'][pvsys]['strings'] / \
    #    temp_strings/temp_modules_per_string
    parray = dict(
        module_parameters=module_parameters,
        temperature_model_parameters=temperature_model_parameters,
        modules_per_string=pvsys["modules_per_string"],
        strings=pvsys["strings"]
        # strings_per_inverter=config['pvsystem'][pvsys]['strings']
    )
    parrays = []
    for i in range(len(pvsys["azimuth"])):
        tilt = pvsys["tilt"][i]
        azim = pvsys["azimuth"][i]
        parrays.append(
            pvlib.pvsystem.Array(
                pvlib.pvsystem.FixedMount(tilt, azim), name="agripv", **parray
            )
        )
    system = pvlib.pvsystem.PVSystem(
        arrays=parrays, inverter_parameters=inverter_parameters
    )
    mc = pvlib.modelchain.ModelChain(
        system, location, aoi_model="physical", spectral_model="no_loss"
    )
    return mc


def main():
    ### test the coordinates translation from lat-lon to x,y netcdf
    # read points
    geopoints_data = "data/randompointsAT.geojson"
    points = gpd.read_file(geopoints_data)
    # for testing purposes only the first x points
    points = points.head(500)

    # ccca takes EPSG:4326 as input for lat/lon, fransform if needed

    if rs.ccca.CRS != points.crs:
        print("transform")
        rspoints = points.to_crs(target_crs)
    else:
        rspoints = points
    # open ccca netcdf

    nd = xr.open_dataset(
        "/data/projects/PA3C3/Input/rsds_SDM_ICHEC-EC-EARTH_rcp45_r1i1p1_KNMI-RACMO22E.nc"
    )

    startyears = [1981, 2031]
    years = 30
    dates365 = rs.base.gendates365(startyears, years)

    temperature = 25
    altitude = 250
    timezone = "UTC"
    downscale_alg = "liu"

    pvsys = {
        "name": "1kWp",
        "type": "single",
        "module": "Aleo_Solar_S79y280",
        "inverter": "PV_Powered__PVP2000EVR__240V_",
        "modules_per_string": 4,  # = 1120Wp; number of modules per row
        "strings": 1,  # number of rows
        "distance": 10,  # distance in meters between rows
        "height": 1,  # slant height (without clearance)
        "tilt": [30],  # tilt of modules [0-90]
        "azimuth": [180],
    }

    for index, point in rspoints.iterrows():
        [nx, ny] = rs.ccca.getxy(nd, point)
        print("point - {} : {} - xy: {},{}".format(index, point.geometry, nx, ny))
        location = pvlib.location.Location(
            latitude=point.geometry.y,
            longitude=point.geometry.x,
            altitude=altitude,
            tz=timezone,
        )
        # print(location)
        for year, daterange in dates365.items():
            endyear = year + years - 1
            daterange365 = dates365[year]
            rsdsvalues = rs.ccca.getvalues(nd, nx, ny, daterange365).rsds.values
            ghid = rsdsvalues * 24
            # print("year: {}-{} - rsds: {}".format(year, endyear, rsdsvalues))
            pd.set_option("display.max_rows", None)
            # Convert daily GHI to hourly DNI and DHI using typical DNI/DHI ratios
            ghih = rs.irradiance.ghi_daily_to_hourly(
                ghid, daterange365, location, timezone, downscale_alg
            )
            # print(ghih.head(365 * 24 * 2))

            hdata = rs.irradiance.ghi_to_dni(ghih, model="erbs")
            # print(hdata.head(96))

            # print(pvsys)
            #
            mcsys = pvsystem(pvsys, location)
            # print(mcsys)
            mcsim = mcsys.run_model(hdata)
            res = mcsim.results.ac
            # print(res.head(96))
            res[res < 0] = 0
            # print(res.head(96))
            yearly_sum = res.resample("Y").sum()
            # print((yearly_sum.values / 1000).round(decimals=0))
            mean_yearly_sum = yearly_sum.mean()
            # print("yearly mean: {}".format(y_mean))
            colname = "y_" + str(year)
            rspoints.at[index, colname] = (mean_yearly_sum / 1000).round(decimals=0)
            colname = "means_" + str(year)
            rspoints.at[index, colname] = json.dumps(
                (yearly_sum.values / 1000).round(decimals=0).tolist()
            )
    outfile = "rspoints.gpkg"
    # print(rspoints)
    rspoints.to_file(outfile, driver="GPKG")


if __name__ == "__main__":
    main()
