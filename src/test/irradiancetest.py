import numpy as np
import math
import os, sys

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import renspatial as rs
import pandas as pd
import geopandas as gpd
import xarray as xr
import pvlib
import suntimes
import datetime


def sunset_time(location, date):
    """
    Calculate the time of sunset for a specific location and date.

    This function uses the `suntimes` library to compute the time of sunset at a given
    geographic location on a specific date.

    Parameters
    ----------
    location : Location
        An object representing the geographic location. It should have attributes:
        - `longitude` (float): The longitude of the location in decimal degrees.
        - `latitude` (float): The latitude of the location in decimal degrees.
        - `altitude` (float): The altitude of the location in meters (optional).

    date : str, datetime.date, datetime.datetime
        The date for which the sunset time is to be calculated. It can be specified as
        a string in "YYYY-MM-DD" format, a datetime.date, or a datetime.datetime object.

    Returns
    -------
    sunset : datetime.time
        The time of sunset for the specified location and date.

    Note
    ----
    This function utilizes the `suntimes` library to calculate the sunset time based on
    the provided location's latitude, longitude, and optional altitude. Make sure to
    have the `suntimes` library installed before using this function.

    Example
    -------
    >>> from datetime import date
    >>> class Location:
    ...     pass
    >>> location = Location()
    >>> location.longitude = -122.4194
    >>> location.latitude = 37.7749
    >>> location.altitude = 10  # Optional altitude in meters
    >>> target_date = date(2023, 8, 22)
    >>> sunset = sunset_time(location, target_date)
    >>> print(sunset)
    19:47:25  # Example output
    """
    place = suntimes.SunTimes(
        location.longitude, location.latitude, altitude=location.altitude
    )
    return place.setutc(date)


def ghi_daily_to_hourly(ddata, daterange, location, timezone, downscale_alg="liu"):
    """
    Convert daily Global Horizontal Irradiance (GHI) data to hourly using specified algorithms.

    This function converts daily Global Horizontal Irradiance (GHI) data into hourly data
    using the specified downscaling algorithm. The algorithm choices are "liu", "cpr", or "garg".

    Parameters
    ----------
    ddata : array-like
        Array of daily GHI values to be converted.

    daterange : array-like
        Array of datetime objects corresponding to the dates of the daily GHI values.

    location : Location
        An object representing the geographic location. It should have attributes:
        - `longitude` (float): The longitude of the location in decimal degrees.
        - `latitude` (float): The latitude of the location in decimal degrees.
        - `altitude` (float): The altitude of the location in meters.

    timezone : str
        Timezone of the location in "America/New_York" format.

    downscale_alg : {"liu", "cpr", "garg"}, optional
        The algorithm to use for downscaling. Defaults to "liu".

    Returns
    -------
    hourly_data : pandas.DataFrame
        A DataFrame containing the converted hourly GHI data with additional solar
        position and ratio information.

    Notes
    -----
    The specified downscale algorithm determines how the conversion from daily to hourly
    GHI values is performed. The algorithm choices are as follows:
    - "liu": Liu and Jordan algorithm.
    - "cpr": Collares-Pereira and Rabl algorithm.
    - "garg": Garg and Garg algorithm.

    Example
    -------
    >>> class Location:
    ...     pass
    >>> location = Location()
    >>> location.longitude = -75.1652
    >>> location.latitude = 39.9526
    >>> location.altitude = 10
    >>> ddata = [5.6, 6.8, 7.2]  # Example daily GHI values
    >>> daterange = [datetime.date(2023, 8, 20), datetime.date(2023, 8, 21), datetime.date(2023, 8, 22)]
    >>> timezone = "America/New_York"
    >>> hourly_data = ghi_daily_to_hourly(ddata, daterange, location, timezone, downscale_alg="cpr")
    >>> print(hourly_data)
    """
    hourly_data = pd.DataFrame()

    for i, daily_value in enumerate(ddata):
        date = daterange[i]

        # Calculate sunset azimuth
        sunset_azimuth = sunset_time(location, date).azimuth

        # Calculate hourly azimuth and zenith
        hourly_datetimes = pd.date_range(
            start=date + datetime.timedelta(hours=0.5),
            end=date + datetime.timedelta(hours=23.5),
            freq="H",
            tz=timezone,
        )
        solar_positions = location.get_solarposition(hourly_datetimes)
        hourly_azimuth = np.around(solar_positions["azimuth"].values, decimals=2)
        zenith_angle = np.around(solar_positions["zenith"].values, decimals=2)
        apparent_zenith_angle = np.around(
            solar_positions["apparent_zenith"].values, decimals=2
        )
        cos_zenith = np.cos(np.deg2rad(zenith_angle))

        # Calculate daily-to-hourly ratio using specified algorithm
        if downscale_alg == "liu":
            ratio = calc_liu_ratio(sunset_azimuth, hourly_azimuth)
        elif downscale_alg == "cpr":
            ratio = calc_cpr_ratio(sunset_azimuth, hourly_azimuth)
        elif downscale_alg == "garg":
            ratio = calc_garg_ratio(sunset_azimuth, hourly_azimuth)

        # Normalize ratio
        ratio /= np.sum(ratio)

        # Calculate hourly GHI values
        hourly_values = np.around(daily_value * ratio, decimals=2)

        # Create DataFrame for hourly data
        hourly_data = pd.concat(
            [
                hourly_data,
                pd.DataFrame(
                    {
                        "w_h": hourly_azimuth,
                        "z_h": zenith_angle,
                        "z_h_a": apparent_zenith_angle,
                        "cos_z_h": cos_zenith,
                        "ratio": ratio,
                        "ghi": hourly_values,
                    },
                    index=hourly_datetimes,
                ),
            ]
        )

    return hourly_data


# Example usage
geopoints_data = "data/randompointsAT.geojson"
rspoints = gpd.read_file(geopoints_data)
# for testing purposes only the first x points
rspoints = rspoints.head(3)
dates365 = rs.base.gendates365([2000], 1, "1d")
daterange365 = dates365[2000]

ghid = [1] * 365
altitude = 250
timezone = "UTC"

for index, point in rspoints.iterrows():
    location = pvlib.location.Location(
        latitude=point.geometry.y,
        longitude=point.geometry.x,
        altitude=altitude,
        tz=timezone,
    )
    print(location)

    print(daterange365[2])

    ghih = ghi_daily_to_hourly(ghid, daterange365, location, timezone, "xxx")
    pd.set_option("display.max_rows", None)
    print(ghih.head(96))
