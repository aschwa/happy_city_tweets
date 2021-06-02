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
    #print(lon, lat)
    lon,lat = transform(tweet_crs,tpl_crs,lon,lat)
    return lon, lat

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



## Old way - andys
name_col = "Park_Name"
city_key = "Park_Pla_1"
city_id = "1150000"
pList, nList = geo_utils.loadGeneric('../data/raw/geo/ParkServe_shp_DataShare_05152019/ParkServe_shp_DataShare_05152019/ParkServe_Parks_05152019.shp',
                                     name_col, city_key,city_id)

print("Total park tweets in LA: {}".format(len(park_tweets)))
print("Total control tweets in LA: {}".format(len(control_tweets)))

#shape(la_parks.iloc[1].geometry)[0].centroid.coords.xy
#p1 = Point(la_parks.iloc[50].geometry.centroid.coords.xy[0][0], la_parks.iloc[50].geometry.centroid.coords.xy[1][0])

# Loop way 
la_parks.sort_values(by="Shape_Area", inplace=True)

tweet_sample = tweets[2000000:2000100]
# reproject tweets properly
# multipolyogne issues
# sort tweets
for tweet in tweet_sample:
    point = Point(reproj_tweet(tweet))
    for park in la_parks.iterrows():
        if shape(park[1].geometry).contains(point):
            print(park[1].Park_Name)
            break
