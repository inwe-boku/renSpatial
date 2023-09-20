#!/usr/bin/env python3
import sys
import os
import requests
import time
import random
import math
import renspatial as rs


datadir = "~/basemapAT/"

zoomlevel = 15
bbox = (9.47996951665, 46.4318173285, 16.9796667823, 49.0390742051)

server = "https://maps{}.wien.gv.at"

minX, maxY = rs.calculate_tile_indices(bbox[0], bbox[1], zoomlevel)
maxX, minY = rs.calculate_tile_indices(bbox[2], bbox[3], zoomlevel)

print(minX, maxX, minY, maxY)
# minX, maxX = 8624, 8972
# minY, maxY = 5624, 5804
numberOfRequests = 0
pauseAfterRequests = 1000
pauseInSeconds = 1
totalNumberOfTiles = (maxX - minX + 1) * (maxY - minY + 1)
numberOfTilesProcessed = 0
z = zoomlevel

print(f"That's {totalNumberOfTiles} tiles total.")


def get_tile_url(x, y):
    return f"/basemapv/bmapv/3857/tile/{z}/{y}/{x}.pbf"  # "basemapv/bmapv/3857/tile/{z}/{y}/{x}.pbf"


def download_tile(x, y):
    query = get_tile_url(x, y)
    random_server = server.format(random.randint(1, 4))

    print(f"Issuing request {random_server}{query}...")

    try:
        r = requests.get(random_server + query)
    except requests.exceptions.ConnectionError:
        print("ConnectionError thrown. Waiting one minute...")
        time.sleep(60)
        r = requests.get(random_server + query)

    return r


for x in range(minX, maxX + 1):
    for y in range(minY, maxY + 1):
        directory = f"data/{z}/{x}/"

        file = directory + f"{y}.pbf"

        if not os.path.isfile(file):
            numberOfRequests += 1
            response = download_tile(x, y)

            if response.status_code == requests.codes.ok:
                print(f"{x} {y} was found. Saving file.")

                if not os.path.exists(directory):
                    os.makedirs(directory)
                with open(file, "wb") as fd:
                    for chunk in response.iter_content(1024):
                        fd.write(chunk)
            elif response.status_code == requests.codes.not_found:
                print(f"{x} {y} could not be found (HTTP 404).")
            else:
                print(
                    f"HTTP error {response.status_code} occurred while downloading {x} {y}."
                )

            if numberOfRequests >= pauseAfterRequests:
                time.sleep(pauseInSeconds)
                numberOfRequests = 0
        else:
            print(f"Tile {x} {y} already exists.")

        numberOfTilesProcessed += 1
        percent = numberOfTilesProcessed / totalNumberOfTiles * 100
        print(
            f" --- Processed {numberOfTilesProcessed} / {totalNumberOfTiles} ({percent:.3f} percent)"
        )
