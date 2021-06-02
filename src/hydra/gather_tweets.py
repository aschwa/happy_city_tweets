#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import json
import argparse
import pandas as pd
from pathlib import Path
from datetime import datetime
from datetime import date
from datetime import timedelta
from dotenv import load_dotenv, find_dotenv

from pymongo import MongoClient
from src.hydra import mongo_utils


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("geo",
                        help='name of json file, in data/processed/city_geo',
                        type=Path)
    parser.add_argument("start_date",
                        default=date.today() - timedelta(days=1),
                        type=lambda d: datetime.strptime(d, '%Y%m%d'),
                        help="Date in the format yyyymmdd")
    parser.add_argument("end_date",
                        default=date.today(),
                        type=lambda d: datetime.strptime(d, '%Y%m%d'),
                        help="Date in the format yyyymmdd")
    parser.add_argument("-l", "--language", dest="lang", type=str,
                        default="en",
                        help="Twitter 2char language")
    parser.add_argument('-t', '--timezone', dest="timezone",
                        help='tz timezone database name',
                        default="America/New_York", type=str),
    args = parser.parse_args()
    return args

# load a polygon from geojson
def get_polygon(geoJsonFile):
    with open(geoJsonFile, 'r') as json_file:
        polygon = json.load(json_file)
    shape_type = polygon['features'][0]['geometry']['type']
    shape_coordinates = polygon['features'][0]['geometry']['coordinates']
    return shape_type, shape_coordinates


class Tweetdb:
    """Class to work with geotweets """

    def __init__(self, dbname=None, collection=None):
        """
        Parameters
        ----------
        dbname : mongo collection name [geotweets, 1-grams]
        datapath : directory to expand
        """
        try:
            dotenv_path = find_dotenv()
            load_dotenv(dotenv_path)
            hydra_user = os.environ.get("MONGO_USER")
            hydra_password = os.environ.get("MONGO_PASSWORD")
            client = MongoClient('mongodb://%s:%s@hydra.uvm.edu:27016'
                                 % (hydra_user, hydra_password))
            db = client[dbname]
            documents = db[collection]
        except IOError:
            raise IOError("Could not connect to MongoDB")
        self.dbname = dbname
        self.documents = documents
        self.client = client
        self.db = db
        self.collection = collection


# Dump geotweets to a directory from a mongodb cursor
def save_geo_tweets(tweet_cursor, tweet_path):
    tweets = []
    for tweet in tweet_cursor:
        tweets.append(tweet)
    print(len(tweets))
    # create directory to save into
    Path(city_path).mkdir(exist_ok=True)
    with open("{}".format(tweet_path), 'w') as fout:
        json.dump(tweets, fout, sort_keys=True, default=str)


# gather tweets  for a given polygon
if __name__ == "__main__":
    args = parse_args()
    geo_dir = Path("../../data/processed/city_geo_union").resolve()
    city_name = str(args.geo)[:-8]
    city_path = '../../data/raw/tweets/{}'.format(city_name.replace('.', ''))
    shape_type, shape_coords = get_polygon(str(geo_dir / args.geo))
    geotweets = Tweetdb('tweets', 'geotweets').documents
    daterange = pd.date_range(args.start_date, args.end_date)
    for single_date in daterange:
        date_str = single_date.strftime("%Y-%m-%d")
        tweet_path = "{}/{}.json".format(city_path, date_str)
        if Path(tweet_path).is_file():
            print("{} already exists".format(tweet_path))
        else:
            cursor = mongo_utils.tweet_aggregator(geotweets, shape_coords,
                                              single_date, shape_type)
            save_geo_tweets(cursor, tweet_path)
            print("{} gathered".format(tweet_path))
    # main()
