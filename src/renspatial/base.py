import pandas as pd


def gendates360(startyears=[2000], ylength=3, freq="1d"):
    """
    Generate date ranges using a 360-day calendar for specified years.

    This function generates date ranges for specified starting years, using a
    360-day calendar, and returns a dictionary containing the generated date
    ranges for each year.

    Parameters:
        startyears (list[int]): List of starting years for generating date ranges.
            Default is [2000].
        ylength (int): Number of years to include in each date range. Default is 3.
        freq (str): Frequency of date generation. Default is "1d" (daily).

    Returns:
        dict: A dictionary where keys are starting years and values are xarray.CFTimeIndex
            objects representing the generated date ranges using a 360-day calendar.

    Note:
        This function relies on the `cftime` and `xarray` libraries for handling
        dates using a 360-day calendar. Make sure to import the necessary libraries
        before using this function.

    Example:
        >>> gendates360(startyears=[2022, 2024], ylength=2, freq="7d")
        {
            2022: CFTimeIndex(['2022-01-01', '2022-01-08', ..., '2023-12-30'], dtype='object', length=107),
            2024: CFTimeIndex(['2024-01-01', '2024-01-08', ..., '2025-12-30'], dtype='object', length=107)
        }
    """
    dates = {}
    for y in startyears:
        startdt = cftime.Datetime360Day(y, 1, 1, 12, 0, 0, 0)
        enddt = cftime.Datetime360Day(y + ylength - 1, 12, 30, 12, 0, 0, 0)
        dates[y] = xarray.cftime_range(
            start=startdt, end=enddt, freq=freq, calendar="360_day"
        )
    return dates


def gendates365(startyears=[2000], ylength=3, freq="1d"):
    """
    Generate date ranges excluding February 29th for specified years.

    This function generates date ranges for specified starting years,
    excluding February 29th (leap day), if present, for each year. It returns
    a dictionary containing the generated date ranges for each year.

    Parameters:
        startyears (list[int]): List of starting years for generating date ranges.
            Default is [2000].
        ylength (int): Number of years to include in each date range. Default is 3.
        freq (str): Frequency of date generation. Default is "1d" (daily).

    Returns:
        dict: A dictionary where keys are starting years and values are pandas DatetimeIndex
            objects representing the generated date ranges excluding February 29th.

    Example:
        >>> gendates365(startyears=[2022, 2024], ylength=2, freq="7d")
        {
            2022: DatetimeIndex(['2022-01-01', '2022-01-08', ..., '2023-12-24'], dtype='datetime64[ns]', length=105, freq='7D'),
            2024: DatetimeIndex(['2024-01-01', '2024-01-08', ..., '2025-12-23'], dtype='datetime64[ns]', length=105, freq='7D')
        }
    """
    dates = {}
    for y in startyears:
        dr = pd.date_range(
            start=str(y) + "-01-01", end=str(y + ylength - 1) + "-12-31", freq=freq
        )
        dates[y] = dr[(dr.day != 29) | (dr.month != 2)]
    return dates
