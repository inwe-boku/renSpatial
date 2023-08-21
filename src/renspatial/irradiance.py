import pandas as pd
import numpy as np
import suntimes
import datetime
import math
import pvlib


def sunset_time(location, date):
    """[summary]

    Parameters
    ----------
    location : [type]
        [description]
    date : [type]
        [description]
    """
    place = suntimes.SunTimes(
        location.longitude, location.latitude, altitude=location.altitude
    )
    return place.setutc(date)


def rad_d2h(w_s, w, downscale_alg="liu"):
    """
    Calculates the ratio of daily and hourly radiation values.

    Parameters
    ----------
    w_s : sunset azimuth (~ sunset hour angle, where 0 = north, 180 = south)
    w : vector of sun azimuth over 24 hours (=24 values) (~ sun hour angle)

    Returns
    -------
    r : vector of relation values for each of the 24 hoursu
    """
    if downscale_alg == "liu":
        """
        Using the method presented in:
        B. Y. H. Liu and R. C. Jordan, “The interrelationship and characteristic
        distribution of direct, diffuse and total solar radiation,” Solar Energy,
        vol. 4, no. 3, pp. 1–19, 1960.
        """
        w_s_adp = w_s - 180
        rad_w_s_adp = math.radians(w_s_adp)
        cos_w_s = math.cos(rad_w_s_adp)
        sin_w_s = math.sin(rad_w_s_adp)
        ratio = []
        for w_h in w:
            w_h_adp = w_h - 180
            cos_w_h = math.cos(math.radians(w_h_adp))
            # r = (math.pi/24 * (cos_w_h - cos_w_s)) / \
            #    (sin_w_s - (rad_w_s_adp * cos_w_s))
            r = (((math.pi) / 24) * (cos_w_h - cos_w_s)) / (
                sin_w_s - rad_w_s_adp * cos_w_s
            )
            ratio.append(r)
    elif downscale_alg == "cpr":
        """
        Using the method presented in:
        M. Collares-Pereira and A. Rabl, “The average distribution of solar
        radiation-correlations between diffuse and hemispherical and between
        daily and hourly insolation values,” Solar Energy, vol. 22, no. 2,
        pp. 155–164, 1979.
        """
        w_s_adp = w_s - 180
        rad_w_s_adp = math.radians(w_s_adp)
        cos_w_s = math.cos(rad_w_s_adp)
        sin_w_s = math.sin(rad_w_s_adp)
        w_s_cp = w_s_adp - 60
        sin_w_s_cp = math.sin(math.radians(w_s_cp))
        a = 0.409 + (0.5016 * sin_w_s_cp)
        b = 0.6609 - (0.4767 * sin_w_s_cp)

        ratio = []
        for w_h in w:
            w_h_adp = w_h - 180
            cos_w_h = math.cos(math.radians(w_h_adp))
            # r = (a + (b * cos_w_h)) * \
            #    (math.pi / 24 * (cos_w_h - cos_w_s)) / \
            #    (sin_w_s - ((math.pi * w_s_adp/180) * cos_w_s))
            r = (
                (math.pi / 24)
                * (a + b * cos_w_h)
                * (cos_w_h - cos_w_s)
                / (sin_w_s - rad_w_s_adp * cos_w_s)
            )
            ratio.append(r)
    elif downscale_alg == "garg":
        """
        Using the method presented in:
        H.P.Garg and S.N.Garg, “Improved correlation of daily and hourly diffuse
        radiation with global radiation for Indian stations,”
        Solar Energy, vol. 22, no. 2,
        pp. 155–164, 1979.
        """
        w_s_adp = w_s - 180
        rad_w_s_adp = math.radians(w_s_adp)
        cos_w_s = math.cos(rad_w_s_adp)
        sin_w_s = math.sin(rad_w_s_adp)
        w_s_cp = w_s_adp - 60
        sin_w_s_cp = math.sin(math.radians(w_s_cp))

        ratio = []
        for w_h in w:
            w_h_adp = w_h - 180
            rad_w_h = math.radians(w_h_adp)
            cos_w_h = math.cos(rad_w_h)
            r = (math.pi / 24) * (cos_w_h - cos_w_s) / (
                sin_w_s - rad_w_s_adp * cos_w_s
            ) - (0.008 * math.sin(3 * (rad_w_h - 0.65)))
            ratio.append(r)
    return np.clip(ratio, a_min=0, a_max=None)


def ghi_daily_to_hourly(ddata, daterange, location, timezone, downscale_alg="liu"):
    i = 0
    data = pd.DataFrame()
    while i < len(ddata):
        # raw data is in W/m2 -> this is meteorological mean data per hour and day, have to multiply by 24
        # dval = ddata[i] * 24
        # print(ddata[i], dval)
        date = daterange[i]
        # sunset azimuth
        settime = sunset_time(location, date)
        solar_position = location.get_solarposition(settime)
        w_s = solar_position["azimuth"].values[0]

        # hourly azimuth
        datetimes = pd.date_range(
            start=date + datetime.timedelta(hours=0.5),
            end=date + datetime.timedelta(hours=23.5),
            freq="H",
            tz=timezone,
        )
        solar_position = location.get_solarposition(datetimes)
        # azimuth of sun
        w_h = np.around(solar_position["azimuth"].values, decimals=2)
        # zenith of sun
        z_h = np.around(solar_position["zenith"].values, decimals=2)
        z_h_a = np.around(solar_position["apparent_zenith"].values, decimals=2)
        cos_z_h = np.cos(np.deg2rad(z_h))
        # cos_z_h = np.where(cos_z_h > 0.08, cos_z_h, 1)

        # daily to hourly values
        ratio = rad_d2h(w_s, w_h, downscale_alg)
        # normalize
        ratio = ratio * 1 / (sum(ratio))
        # ratio = np.roll(ratio, 1)
        hvalues = np.around(ddata[i] * ratio, decimals=2)
        tempdata = np.stack([w_h, z_h, z_h_a, cos_z_h, ratio, hvalues], axis=1)
        hdata = pd.DataFrame(
            data=tempdata,
            index=datetimes,
            columns=["w_h", "z_h", "z_h_a", "cos_z_h", "ratio", "ghi"],
        )
        # print(hdata)
        data = pd.concat([data, hdata])
        i += 1
    return data


def ghi_to_dni(data, model="disc"):
    if model == "disc":
        dnidata = pvlib.irradiance.disc(
            ghi=data["ghi"], solar_zenith=data["z_h"], datetime_or_doy=data.index
        )
        data = pd.concat([data, dnidata], axis=1)
        data.dni = data.dni.round(decimals=2)
        # print(data['ghi'])
        # print(data['dni'])
        # print(data['cos_z_h'])
        x = data["ghi"] - data["dni"] * data["cos_z_h"]
        print(x)
        data["dhi"] = data.ghi - (data.dni * data.cos_z_h)
        data.kt = data.kt.round(decimals=5)

    elif model == "erbs":
        dnidata = pvlib.irradiance.erbs(
            ghi=data["ghi"],
            zenith=data["z_h"],
            datetime_or_doy=data.index,
            min_cos_zenith=0.065,
            max_zenith=85,
        )
        data = pd.concat([data, dnidata], axis=1)
        data.dni = data.dni.round(decimals=2)
        data.dhi = data.dhi.round(decimals=2)
        data.kt = data.kt.round(decimals=5)
    return data
