# handles netcdf files from CCCA: https://data.ccca.ac.at/
import numpy as np

# CONSTANTS

CRS = "EPSG:4326"


def getxy(nd, point):
    """
    Calculate x and y values from a netcdf file based on the closest coordinates
    to a given point's latitude and longitude. The netcdf file is expected to have
    a format compatible with the CCCA (Climate Change Centre Austria) standards.

    Parameters
    ----------
    nd : netCDF4.Dataset
        An open netCDF4 dataset containing relevant lat and lon variables.

    point : GeoPandas GeoSeries
        A GeoPandas GeoSeries with geometry information representing the point
        for which the closest x and y values are to be calculated.

    Returns
    -------
    x, y : float
        Calculated x and y values corresponding to the closest coordinates
        in the netCDF file.

    Note
    ----
    The function computes the absolute differences between the provided point's
    latitude and longitude and the latitudes and longitudes in the netCDF file.
    It then identifies the coordinates with the minimum absolute difference and
    returns the corresponding x and y values from the netCDF data.

    Example
    -------
    >>> import netCDF4
    >>> import geopandas as gpd
    >>> point = gpd.GeoSeries({"geometry": gpd.points_from_xy([15], [47])})
    >>> dataset = netCDF4.Dataset("climate_data.nc")
    >>> x_val, y_val = getxy(dataset, point)
    """
    abslat = np.abs(nd.lat - point.geometry.y)
    abslon = np.abs(nd.lon - point.geometry.x)
    c = np.maximum(abslon, abslat)

    yloc = np.where(c == np.min(c))[0][0]
    xloc = np.where(c == np.min(c))[1][0]
    return (nd["x"][xloc].values, nd["y"][yloc].values)


def getvalues(nd, nx, ny, date):
    """
    Retrieve data values from a netcdf file at the nearest coordinates to the specified
    x and y indices, for a given date. The netcdf file is expected to have a format
    compatible with the CCCA (Climate Change Centre Austria) standards.

    Parameters
    ----------
    nd : xarray.Dataset
        An xarray Dataset representing the netcdf data.

    nx : int or float
        The x-coordinate index or value for which to retrieve data.

    ny : int or float
        The y-coordinate index or value for which to retrieve data.

    date : str or datetime-like object
        The date or time for which data is to be retrieved. This should be compatible
        with the time dimension in the netcdf file.

    Returns
    -------
    values : xarray.DataArray
        A subset of the netcdf data containing values at the nearest coordinates to the
        specified x and y indices or values, for the given date.

    Note
    ----
    The function uses xarray's `.sel()` method with the "nearest" method to retrieve data
    from the netcdf file at the closest coordinates to the provided x and y values, for
    the specified date.

    Example
    -------
    >>> import xarray as xr
    >>> dataset = xr.open_dataset("climate_data.nc")
    >>> x_coord = 15
    >>> y_coord = 47
    >>> target_date = "2023-08-22"
    >>> values = getvalues(dataset, x_coord, y_coord, target_date)
    """
    return nd.sel(
        x=nx,
        y=ny,
        method="nearest",
        time=date,
    )
