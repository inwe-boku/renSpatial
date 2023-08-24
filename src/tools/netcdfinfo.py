import xarray as xr


def print_dataset_info(ds):
    """
    Print information about the opened dataset.

    Parameters:
        ds (xarray.Dataset): The opened dataset.
    """
    print("Dataset Information:")
    print(ds)


def print_variable_info(ds):
    """
    Print information about each variable in the dataset.

    Parameters:
        ds (xarray.Dataset): The opened dataset.
    """
    print("Variable Information:")
    for var_name in ds.variables:
        var = ds[var_name]
        print(var)


def main():
    """
    Main function to open a NetCDF file, print dataset information, and variable information.
    """
    ncfilename = "/data/projects/PA3C3/Input/rsds_SDM_ICHEC-EC-EARTH_rcp45_r1i1p1_KNMI-RACMO22E.nc"
    ds = xr.open_dataset(ncfilename)

    print_dataset_info(ds)
    print_variable_info(ds)


if __name__ == "__main__":
    main()
