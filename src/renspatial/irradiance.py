import pandas as pd
import numpy as np
import suntimes
import datetime
import math
import pvlib


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


def rad_d2h(w_s, w, downscale_alg="liu"):
    """
    Calculate the ratio of daily and hourly radiation values based on specified algorithms.

    This function calculates the ratio of daily and hourly radiation values using one
    of three possible algorithms: "liu" (Liu and Jordan), "cpr" (Collares-Pereira and Rabl),
    or "garg" (Garg and Garg). The calculated ratios can be useful for downscaling daily
    radiation data to hourly resolution.

    Parameters
    ----------
    w_s : float
        Sunset azimuth angle in degrees, where 0 represents north and 180 represents south.

    w : array-like
        An array of sun azimuth angles over 24 hours, representing the sun hour angle.

    downscale_alg : {"liu", "cpr", "garg"}, optional
        The algorithm to use for calculating the ratios. Defaults to "liu".

    Returns
    -------
    ratio : numpy.ndarray
        An array of ratio values calculated using the specified algorithm for each of the 24 hours.

    Notes
    -----
    - If using the "liu" algorithm:
        This method is based on the work of B. Y. H. Liu and R. C. Jordan [Solar Energy, 1960].
    - If using the "cpr" algorithm:
        This method is based on the work of M. Collares-Pereira and A. Rabl [Solar Energy, 1979].
    - If using the "garg" algorithm:
        This method is based on the work of H. P. Garg and S. N. Garg [Solar Energy, 1979].

    The calculated ratios are clipped to a minimum of 0.

    Example
    -------
    >>> sunset_azimuth = 220
    >>> sun_azimuths = [180, 170, 160, ..., 190]  # Array of sun azimuth angles over 24 hours
    >>> algorithm = "cpr"
    >>> ratios = rad_d2h(sunset_azimuth, sun_azimuths, downscale_alg=algorithm)
    >>> print(ratios)
    [0.09234732 0.08173612 0.07102486 ...]

    References
    ----------
    - Liu, B. Y. H., & Jordan, R. C. (1960). The interrelationship and characteristic distribution of direct, diffuse and total solar radiation. Solar Energy, 4(3), 1–19.
    - Collares-Pereira, M., & Rabl, A. (1979). The average distribution of solar radiation—correlations between diffuse and hemispherical and between daily and hourly insolation values. Solar Energy, 22(2), 155–164.
    - Garg, H. P., & Garg, S. N. (1979). Improved correlation of daily and hourly diffuse radiation with global radiation for Indian stations. Solar Energy, 22(2), 155–164.
    """
    if downscale_alg == "liu":
        w_s_adp = w_s - 180
        rad_w_s_adp = math.radians(w_s_adp)
        cos_w_s = math.cos(rad_w_s_adp)
        sin_w_s = math.sin(rad_w_s_adp)

        ratios = []
        for w_h in w:
            w_h_adp = w_h - 180
            cos_w_h = math.cos(math.radians(w_h_adp))
            r = (
                ((math.pi) / 24)
                * (cos_w_h - cos_w_s)
                / (sin_w_s - rad_w_s_adp * cos_w_s)
            )
            ratios.append(r)
    elif downscale_alg == "cpr":
        a = 0.409 + (0.5016 * np.sin(np.radians(w_s - 240)))
        b = 0.6609 - (0.4767 * np.sin(np.radians(w_s - 240)))
        w_s_adp = w_s - 180
        rad_w_s_adp = math.radians(w_s_adp)
        cos_w_s = math.cos(rad_w_s_adp)
        sin_w_s = math.sin(rad_w_s_adp)

        ratios = []
        for w_h in w:
            w_h_adp = w_h - 180
            cos_w_h = math.cos(math.radians(w_h_adp))
            r = (
                (a + b * cos_w_h)
                * (math.pi / 24)
                * (cos_w_h - cos_w_s)
                / (sin_w_s - rad_w_s_adp * cos_w_s)
            )
            ratios.append(r)

    elif downscale_alg == "garg":
        w_s_adp = w_s - 180
        rad_w_s_adp = math.radians(w_s_adp)
        cos_w_s = math.cos(rad_w_s_adp)
        sin_w_s = math.sin(rad_w_s_adp)

        ratios = []
        for w_h in w:
            w_h_adp = w_h - 180
            rad_w_h = math.radians(w_h_adp)
            cos_w_h = math.cos(rad_w_h)
            r = (math.pi / 24) * (cos_w_h - cos_w_s) / (
                sin_w_s - rad_w_s_adp * cos_w_s
            ) - (0.008 * math.sin(3 * (rad_w_h - 0.65)))
            ratios.append(r)
    return np.clip(ratios, a_min=0, a_max=None)


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
        settime = sunset_time(location, date)
        solar_position = location.get_solarposition(settime)
        sunset_azimuth = solar_position["azimuth"].values[0]

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

        ratios = rad_d2h(sunset_azimuth, hourly_azimuth, downscale_alg)

        # Normalize ratio
        ratios /= np.sum(ratios)

        # Calculate hourly GHI values
        hourly_values = np.around(daily_value * ratios, decimals=2)

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
                        "ratio": ratios,
                        "ghi": hourly_values,
                    },
                    index=hourly_datetimes,
                ),
            ]
        )
    return hourly_data


def ghi_to_dni(data, model="disc"):
    """
    Convert Global Horizontal Irradiance (GHI) to Direct Normal Irradiance (DNI) and
    calculate Diffuse Horizontal Irradiance (DHI) using specified models.

    This function converts Global Horizontal Irradiance (GHI) data to Direct Normal
    Irradiance (DNI) using the specified model. It also calculates Diffuse Horizontal
    Irradiance (DHI) based on the calculated DNI and GHI.

    Parameters
    ----------
    data : pandas.DataFrame
        DataFrame containing GHI, solar zenith angle, and other relevant data.

    model : {"disc", "erbs"}, optional
        The model to use for conversion. Defaults to "disc".

    Returns
    -------
    data : pandas.DataFrame
        A DataFrame containing GHI, DNI, DHI, and other calculated values.

    Notes
    -----
    The specified model determines how the conversion from GHI to DNI is performed.
    The model choices are as follows:
    - "disc": DISC model for DNI estimation.
    - "erbs": ERBS model for DNI estimation.

    Example
    -------
    >>> data = pd.DataFrame({
    ...     "ghi": [500, 600, 700],
    ...     "z_h": [30, 40, 50],
    ...     "cos_z_h": [0.866, 0.766, 0.643]
    ... }, index=pd.date_range(start="2023-08-20", periods=3, freq="D"))
    >>> dni_data = ghi_to_dni(data, model="disc")
    >>> print(dni_data)
    """
    if model == "disc":
        dnidata = pvlib.irradiance.disc(
            ghi=data["ghi"], solar_zenith=data["z_h"], datetime_or_doy=data.index
        )
        data = data.assign(dni=dnidata.dni.round(2))
        data["dhi"] = (data.ghi - data.dni * data.cos_z_h).round(2)
        data["kt"] = dnidata.kt.round(5)
        print(dnidata.head(99))
    elif model == "erbs":
        dnidata = pvlib.irradiance.erbs(
            ghi=data["ghi"],
            zenith=data["z_h"],
            datetime_or_doy=data.index,
            min_cos_zenith=0.065,
            max_zenith=85,
        )
        data = data.assign(
            dni=dnidata.dni.round(2), dhi=dnidata.dhi.round(2), kt=dnidata.kt.round(5)
        )
    return data
