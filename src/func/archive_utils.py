def tweet_list_to_gdf(tweet_list):
    """ Convert list of tweet objects to a GeoDataFrame
     with list index and lat/long.

    """

    coords = []
    for tweet in tweet_list:
        if tweet['geo']['type'] == 'Point':
            temp_coords = tweet['geo']['coordinates']
            coords.append([temp_coords[1],temp_coords[0]])
        else:
            print('PARSE ERROR: No geo point attribute.')

    print(len(coords))
    df = pd.DataFrame(coords, columns = ['lat','long'])

    df['coords'] = list(zip(df.lat,df.long))

    df.reset_index(inplace=True) # df index is index of tweet_list

    df['coords'] = df['coords'].apply(Point)

    return geopandas.GeoDataFrame(df, geometry='coords')
    def merge(list1, list2):
    merged_list = [{"coordinates":list1[i], "text":list2[i]} for i in range(0, len(list1))]
    return merged_list

from shapely.geometry.polygon import Polygon
from shapely.geometry.multipolygon import MultiPolygon

def explode(gdf):
    """
    Explodes a geodataframe

    Will explode muti-part geometries into single geometries. Original index is
    stored in column level_0 and zero-based count of geometries per multi-
    geometry is stored in level_1

    Args:
        gdf (gpd.GeoDataFrame) : input geodataframe with multi-geometries

    Returns:
        gdf (gpd.GeoDataFrame) : exploded geodataframe with a new index
                                 and two new columns: level_0 and level_1

    """
    gs = gdf.explode()
    gdf2 = gs.reset_index().rename(columns={0: 'geometry'})
    gdf_out = gdf2.merge(gdf.drop('geometry', axis=1), left_on='level_0', right_index=True)
    gdf_out = gdf_out.set_index(['level_0', 'level_1']).set_geometry('geometry')
    gdf_out.crs = gdf.crs
    return gdf_out
