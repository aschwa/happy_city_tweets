#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import argparse
from pathlib import Path
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
from geopandas.tools import sjoin
from pyproj import Proj, transform
import multiprocessing
from multiprocessing import Pool

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("tweet_json",
                        help='tweet file name, in data/raw/tweets',
                        type=Path)
    # parser.add_argument("geo_shp", help='path to shp file', type=Path)
    args = parser.parse_args()
    return args


def save_tweets(tweets, path):
    with open(path, 'w') as fout:
        json.dump(tweets, fout, sort_keys=True, default=str)


def reproj_coords(coords):
    tweet_crs = Proj({'proj': 'longlat', 'ellps': 'WGS84', 'datum': 'WGS84'})
    tpl_crs = Proj({'proj': 'aea',
                            'lat_1': 20,
                    'lat_2': 60,
                    'lat_0': 40,
                    'lon_0': -96,
                    'x_0': 0,
                    'y_0': 0,
                    'datum': 'NAD83',
                    'units': 'm',
                    'no_defs': True,
                    'wktext': True})
    lon = coords[0]
    lat = coords[1]
    pt = Point(transform(tweet_crs, tpl_crs, lon, lat))
    return pt


if __name__ == "__main__":
    args = parse_args()
    # Load paths to tweet data, with arguments from CLI
    tweet_dir = Path("../../data/raw/tweets").resolve()
    tweet_path = args.tweet_json
    tweet_file = tweet_dir / tweet_path
    # get city id for shape file
    city_id = tweet_path.stem[-7:]
    print("Working with {} CPUs".format(multiprocessing.cpu_count()))
    # Load geodatabase, and subselect city we are looking at
    print("Loading geodatabase for {}".format(tweet_path))
    gdf = gpd.read_file('../../data/raw/geo/ParkServe_shp_DataShare_05152019/ParkServe_shp_DataShare_05152019/ParkServe_Parks_05152019.shp')
    city_gdf = gdf[gdf.Park_Pla_1 == city_id].copy()
    city_gdf = city_gdf[['geometry', 'ParkID', 'Park_Name']].copy()
    print("Parks to check in {} geodb {}".format(city_id, len(city_gdf)))

    # Load tweets to dataframe
    tweet_df = pd.read_json(tweet_file)
    print("Read {} tweets from file".format(len(tweet_df)))
    try:
        tweet_df.drop("fastText_lang", axis=1, inplace=True)
    except KeyError:
        pass
    tweet_geometry = [x['coordinates'] for x in tweet_df.geo.values]

    with Pool(None) as p:
        tweet_reproj = p.map(reproj_coords, tweet_geometry)

    #tweet_reproj = [Point(reproj_coords(xy['coordinates']))
    #                  for xy in tweet_df.geo.values]
    tweet_df = tweet_df.drop('geo', axis=1)
    # convert to geodataframe, with reprojeted geometry
    tweet_gdf = gpd.GeoDataFrame(tweet_df, crs= gdf.crs, geometry= tweet_reproj)
    #print("Tweets reprojected { }\nStarting Spatial Join".format(gdf.crs))

    # Spatial Join tweets into the city park polygons
    pointInPolys = sjoin(tweet_gdf, city_gdf, how='left', op="within")

    new_df = pd.DataFrame(pointInPolys.drop(columns='geometry'))
    # new_df = new_df.dropna()
    # Construct output file string and save park_tweets there
    output_dir = Path("../../data/processed/tweets").resolve() / tweet_path
    # pointInPolys.to_file(output_dir, driver="GeoJSON")
    print("Saving tweets with park info")
    save_tweets(new_df.to_dict('records'), output_dir)
