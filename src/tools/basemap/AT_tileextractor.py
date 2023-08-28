#!/usr/bin/python

import os
import math
import ogr
import gdal


class TileProcessing:
    def __init__(self, zoom_level, bbox):
        self.zoom_level = zoom_level
        self.bbox = bbox
        self.dest_srs = ogr.osr.SpatialReference()
        self.dest_srs.ImportFromEPSG(3857)
        self.source_srs = ogr.osr.SpatialReference()
        self.source_srs.ImportFromEPSG(4326)
        self.geometry_type = ogr.wkbPolygon

    def deg2num(self, lon_deg, lat_deg):
        lat_rad = math.radians(lat_deg)
        n = 2.0**self.zoom_level
        xtile = int((lon_deg + 180.0) / 360.0 * n)
        ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
        return ytile, xtile

    def num2deg(self, xtile, ytile):
        n = 2.0**self.zoom_level
        lon_deg = xtile / n * 360.0 - 180.0
        lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
        lat_deg = math.degrees(lat_rad)
        return lat_deg, lon_deg

    def process_tile(self, x, y, filename):
        if os.path.isfile(filename) and os.path.getsize(filename) > 0:
            osm = ogr.Open(filename)
            n_layer_count = osm.GetLayerCount()
            for ilayer in range(n_layer_count):
                lyr = osm.GetLayer(ilayer)
                if lyr.GetName() == "GEBAEUDE_F_GEBAEUDE":
                    return lyr
        return None

    def extract_buildings(self, input_file, output_layer):
        for feat in input_file:
            out_feat = ogr.Feature(output_layer.GetLayerDefn())
            out_feat.SetGeometry(feat.GetGeometryRef().Clone())
            output_layer.CreateFeature(out_feat)
            out_feat = None
            output_layer.SyncToDisk()

    def main(self):
        minX, maxY = self.deg2num(bbox[0], bbox[1], zoomlevel)
        maxX, minY = self.deg2num(bbox[2], bbox[3], zoomlevel)

        print("Start")
        original_file = "data/%d/%d/%d.pbf"
        out_dir = "vector/"

        if not os.path.exists(out_dir):
            os.makedirs(out_dir)

        total_number_of_tiles = (maxX - minX + 1) * (maxY - minY + 1)
        number_of_tiles_processed = 0

        drv = ogr.GetDriverByName("GPKG")
        out_ds = drv.CreateDataSource("vector/buildings.gpkg")
        out_lyr = out_ds.CreateLayer("buildings", self.dest_srs, self.geometry_type)

        first_buildings = True

        for x in range(minX, maxX + 1):
            for y in range(minY, maxY + 1):
                print("Processing tile %d / %d." % (x, y))
                filename = original_file % (self.zoom_level, x, y)
                extracted_layer = self.process_tile(x, y, filename)

                if extracted_layer:
                    if first_buildings:
                        out_lyr = out_ds.CopyLayer(extracted_layer, "buildings")
                        out_lyr.SyncToDisk()
                        first_buildings = False
                    self.extract_buildings(extracted_layer, out_lyr)
                else:
                    print("Error: Tile %d / %d does not exist or is empty." % (x, y))

                number_of_tiles_processed += 1
                percent = (number_of_tiles_processed / total_number_of_tiles) * 100
                print(
                    "Processed %d / %d tiles (%.3f%%)"
                    % (number_of_tiles_processed, total_number_of_tiles, percent)
                )


if __name__ == "__main__":
    zoomlevel = 16
    bbox = (9.47996951665, 46.4318173285, 16.9796667823, 49.0390742051)

    processor = TileProcessing(zoomlevel, bbox)
    processor.main()
