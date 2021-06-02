import fiona
from shapely.geometry import Point, Polygon, MultiPolygon
import geopandas as geopd
import json
from pyproj import Proj, transform

def get_shape(geoJsonFileName):
    print(geoJsonFileName)
    # geopandas struggels with PosixPaths
    return geopd.read_file(str(geoJsonFileName))


def loadGeneric(shapefile, key="PUBLIC_NAM", city_key="", city_id=""):
    """Load any shapefile.
    Ex usage:
    park_polygon_list,park_name_list =
    loadGeneric("shapefiles/nps_boundary.shp",key="UNIT_NAME"):"""

    c = fiona.open(shapefile, 'r')
    polygonList = []
    nameList = []
    polygonCount = 0
    multiPolygonCount = 0
    print(city_key, city_id)
    for city in list(c):
        if city['properties'][city_key] == city_id:
            nameList.append(city['properties'][key])
            try:
                if city['geometry']['type'] == 'Polygon':
                    polygonCount += 1
                    coordinates = city['geometry']['coordinates']
                    polygonList.append(Polygon(coordinates[0]))
                elif city['geometry']['type'] == 'MultiPolygon':
                    multiPolygonCount += 1
                    coordinates = city['geometry']['coordinates']
                    coordinates_w_holes = [(tuple(c[0]), ()) if len(
                        c) == 1 else (tuple(c[0]), (c[1:])) for c in coordinates]
                    polygonList.append(MultiPolygon(coordinates_w_holes))
                else:
                    raise('unknown geometry ' % city['geometry']['type'])
            except TypeError:
                pass
    print('done loading')
    return polygonList, nameList


def cityID(polygonList, pt):
    for i, city in enumerate(polygonList):
        if city.contains(pt):
            return i
    return -1


def merge_tweets(path):
    """ Takes a directory (path object) and joins the files into single json
    """
    tweet_files = [e for e in path.iterdir() if e.is_file()]
    all_tweets = []
    for file_path in tweet_files:
        with open(str(file_path)) as f:
            day_of_tweets = json.load(f)
        all_tweets.extend(day_of_tweets)
    return(all_tweets)


def reproj_tweet(tweet):
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
    lon = tweet['geo']['coordinates'][0]
    lat = tweet['geo']['coordinates'][1]
    lon, lat = transform(tweet_crs, tpl_crs, lon, lat)
    return [lon, lat]


def get_park_tweets(tweets, pList, nList):
    """Takes a list of tweets as processed from the mongodb.
    Returns tweets with coordinates originating in the pList
    (e.g., park polygons loaded from a shapefile
    """
    park_tweets = []
    control_tweets = []
    current_tweet = {}
    for tweet in tweets:
        coords = reproj_tweet(tweet)
        # tweet['geo']['coordinates']
        # coords = [coords[1], coords[0]]
        park_id = cityID(pList, Point(Point(coords)))
        tweet['park_id'] = park_id
        if park_id >= 0:
            tweet['park_name'] = nList[park_id]
            print("found park tweet")
            park_tweets.append(tweet)
            control_tweets.append(current_tweet)
        else:
            current_tweet = tweet
    return park_tweets, control_tweets
