#!/usr/bin/python

import numpy as np
import os
import sys
from osgeo import ogr
import math


def deg2num(lon_deg, lat_deg, zoom):
    lat_rad = math.radians(lat_deg)
    n = 2.0**zoom
    xtile = int((lon_deg + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    return (ytile, xtile)


def num2deg(xtile, ytile, zoom):
    n = 2.0**zoom
    lon_deg = xtile / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
    lat_deg = math.degrees(lat_rad)
    return (lat_deg, lon_deg)


def main():
    working_directory = ""
    zoomLevel = 16

    at1 = (9.47996951665, 46.4318173285)
    at2 = (16.9796667823, 49.0390742051)

    # at1 = (15.30, 48.75)
    # at2 = (15.35, 48.80)

    maxY, minX = deg2num(at1[0], at1[1], zoomLevel)
    minY, maxX = deg2num(at2[0], at2[1], zoomLevel)

    print("start")

    originalFile = "data/%d/%d/%d.pbf"
    outDir = "vector/"
    if not os.path.exists(outDir):
        os.makedirs(outDir)

    totalNumberOfTiles = (maxX - minX + 1) * (maxY - minY + 1)
    numberOfTilesProcessed = 0

    dest_srs = ogr.osr.SpatialReference()
    dest_srs.ImportFromEPSG(3857)
    geometryType = ogr.wkbPolygon
    drv = ogr.GetDriverByName("GPKG")
    outds = drv.CreateDataSource("vector/buildings.gpkg")
    # outlyr = outds.CreateLayer("buildings", dest_srs, geometryType)

    source_srs = ogr.osr.SpatialReference()
    source_srs.ImportFromEPSG(4326)

    print("loop")
    firstbuildings = 1
    # Loop through all tiles
    for x in range(minX, maxX + 1):
        for y in range(minY, maxY + 1):
            print("We're on %d / %d." % (x, y))
            filename = originalFile % (zoomLevel, x, y)
            if os.path.isfile(filename):
                if os.path.getsize(filename) > 0:
                    print("File exists and is not empty. Extracting buildings...")
                    print(filename)
                    osm = ogr.Open(filename)
                    nLayerCount = osm.GetLayerCount()
                    for ilayer in range(nLayerCount):
                        lyr = osm.GetLayer(ilayer)
                        if lyr.GetName() == "GEBAEUDE_F_GEBAEUDE":
                            if firstbuildings:
                                outlyr = outds.CopyLayer(lyr, "buildings")
                                outlyr.SyncToDisk()
                                firstbuildings = 0
                            # lyrnam = str(x) + '-' + str(y)
                            for feat in lyr:
                                out_feat = ogr.Feature(outlyr.GetLayerDefn())
                                out_feat.SetGeometry(feat.GetGeometryRef().Clone())
                                outlyr.CreateFeature(out_feat)
                                out_feat = None
                                outlyr.SyncToDisk()
                                # outlyr = outds.CopyLayer(lyr, lyrnam)
                else:
                    print("File exists but is empty, what to do?")
            else:
                print(
                    "Error: Tile %d / %d does not exist. Trying a lower zoomlevel"
                    % (x, y)
                )
                lat1, lon1 = num2deg(x, y, zoomLevel)
                lat2, lon2 = num2deg(x + 1, y + 1, zoomLevel)
                nY, nX = deg2num(lon1, lat1, zoomLevel - 1)
                # print("y-x: %d - %d" % (nY, nX))
                filename = originalFile % (zoomLevel - 1, nX, nY)
                if os.path.isfile(filename):
                    if os.path.getsize(filename) > 0:
                        print("File exists and is not empty. Extracting buildings...")
                        # print(filename)
                        osm = ogr.Open(filename)
                        nLayerCount = osm.GetLayerCount()
                        for ilayer in range(nLayerCount):
                            lyr = osm.GetLayer(ilayer)
                            wkt = (
                                "POLYGON (("
                                + str(lat1)
                                + " "
                                + str(lon1)
                                + ","
                                + str(lat1)
                                + " "
                                + str(lon2)
                                + ","
                                + str(lat2)
                                + " "
                                + str(lon2)
                                + ","
                                + str(lat2)
                                + " "
                                + str(lon1)
                                + ","
                                + str(lat1)
                                + " "
                                + str(lon1)
                                + "))"
                            )
                            geometry = ogr.CreateGeometryFromWkt(wkt)
                            transform = ogr.osr.CoordinateTransformation(
                                source_srs, dest_srs
                            )
                            geometry.Transform(transform)

                            if lyr.GetName() == "GEBAEUDE_F_GEBAEUDE":
                                lyr.SetSpatialFilter(geometry)
                                if firstbuildings:
                                    outlyr = outds.CopyLayer(lyr, "buildingsadd")
                                    outlyr.SyncToDisk()
                                    firstbuildings = 0
                                lyrnam = str(x) + "-" + str(y)
                                for feat in lyr:
                                    out_feat = ogr.Feature(outlyr.GetLayerDefn())
                                    out_feat.SetGeometry(feat.GetGeometryRef().Clone())
                                    outlyr.CreateFeature(out_feat)
                                    out_feat = None
                                    outlyr.SyncToDisk()

            numberOfTilesProcessed += 1
            percent = (
                float(numberOfTilesProcessed) / float(totalNumberOfTiles) * float(100)
            )
            print(
                " --- Processed %d / %d (%.3f percent)"
                % (numberOfTilesProcessed, totalNumberOfTiles, percent)
            )


if __name__ == "__main__":
    main()
