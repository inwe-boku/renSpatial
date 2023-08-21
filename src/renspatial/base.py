import pandas as pd

def gendates360(startyears, ylength):
    dates = {}
    for y in startyears:
        startdt = cftime.Datetime360Day(y, 1, 1, 12, 0, 0, 0)
        enddt = cftime.Datetime360Day(y+ylength-1, 12, 30, 12, 0, 0, 0)
        dates[y] = xarray.cftime_range(
            start=startdt, end=enddt, freq='D', calendar='360_day')
    return(dates)


def gendates365(startyears, ylength):
    dates = {}
    for y in startyears:
        dr = pd.date_range(start=str(y)+"-01-01",
                           end=str(y+ylength-1)+"-12-31", freq='1d')
        dates[y] = dr[(dr.day != 29) | (dr.month != 2)]
    return(dates)
