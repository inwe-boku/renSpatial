# handles netcdf files from CCCA: https://data.ccca.ac.at/
import numpy as np

# CONSTANTS

CRS = "EPSG:4326"

def getxy(nd, point):
    """
    Calculates x and y values from a netcdf file for given coordinates from a
    point with lat / lon values.
    The netcdf is expected to have a format as used by the CCCA.

    Parameters
    ----------
    nd : open netcdf file (netcdf data)

    Returns
    -------
    x, y : values (integer)
    """
    abslat = np.abs(nd.lat - point.geometry.y)
    abslon = np.abs(nd.lon - point.geometry.x)
    c = np.maximum(abslon, abslat)

    ([yloc], [xloc]) = np.where(c == np.min(c))
    # print(point)
    # print(nd['x'][xloc].values, nd['y'][yloc].values)
    return (nd["x"][xloc].values, nd["y"][yloc].values)


def getvalues(nd, nx, ny, date):
    """
    Calculates x and y values from a netcdf file for given coordinates from a
    point with lat / lon values.
    The netcdf is expected to have a format as used by the CCCA.

    Parameters
    ----------
    nd : open netcdf file (netcdf data)

    Returns
    -------
    x, y : values (integer)
    """
    return nd.sel(
        x=nx,
        y=ny,
        method="nearest",
        time=date,
    )


def getdata(nd, points, startyear, years):
    # dates360 = gendates360(
    #    config['ccca']['startyears'], config['ccca']['timeframe'])
    dates365 = gendates365(startyears, years)
    # for other files we do not need dates360
    nd = xr.open_dataset(config["files"]["cccanc"])
    # dates360 = dates365
    # cccadict = {}
    for year, daterange in dates365.items():
        daterange365 = dates365[year]
        points, cccadict = cccapoints(nd, points, daterange365)
        hrsds = {}
        for nx in cccadict.keys():
            hrsds[nx] = {}
            for ny in cccadict[nx].keys():
                hrsds[nx][ny] = {}
                geom = cccadict[nx][ny]["geometry"]
                altitude = cccadict[nx][ny]["altitude"]

                location = pvlib.location.Location(geom.y, geom.x, "UTC", altitude)

                for year, daterange in dates365.items():
                    res = get_ccca_values(nd, int(nx), int(ny), daterange)
                    ddata = pd.DataFrame(index=daterange, data=res.rsds.values)
                    cccadict[nx][ny]["drsds"][year] = ddata
                    # GHI daily to GHI hourly
                    df = pd.DataFrame(data=ddata)

                    # daily to hourly
                    hdata = ghid2ghih(ddata, location)
                    # hdata['geometry'] = geom
                    # DNI+DHI hourly
                    hdata = ghi2dni(hdata, config["pvmod"]["hmodel"])
                    hrsds[nx][ny][year] = hdata
    return (hrsds, points)


    
