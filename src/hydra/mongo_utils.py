from datetime import timedelta

## Count geotweets within a polygon
def daily_tweet_counter(geotweets, polygon, start, end, timezone = "America/New_York"):
    tweet_cursor = geotweets.count_documents(
       {'tweet_created_at':{'$gte':start,
                '$lt':end},
         "geo.coordinates": {
           "$geoWithin": {
              "$geometry": {
                 "type" : "Polygon" ,
                 "coordinates": [polygon],
              }
           }
         },
       })
    return tweet_cursor

#GReturn tweets within a polygon with specific fields
def tweet_aggregator(geotweets, polygon, date, shape_type="Polygon"):
    tweet_cursor = geotweets.aggregate([
       {"$match": { "$and":
         [{"geo.coordinates": {
           "$geoWithin": {
              "$geometry": {
                 "type" : shape_type ,
                 "coordinates": polygon,
              }
           }
         }}, {'tweet_created_at':{'$gte':date,
                                  '$lt':date+timedelta(days=1)}},
          {"fastText_lang": 'en'},
      ]}},
        {"$project" : {"_id": 0,
                       'id':1,
                       'id_str':1,
                       'tweet_created_at':1,
                       'pure_text': 1,
                       'verb': 1,
                       'user.id': 1,
                       'user.id_str': 1,
                       'geo.coordinates': 1,
                       'user.location': 1
                      }
        }
    ])
    return tweet_cursor

#  Return tweets within a specific polygon, on a specific date
def daily_tweet_aggregator(geotweets,polygon, date, timezone = "America/New_York"):
    tweet_cursor = geotweets.aggregate([
       {"$match": { "$and":
         [{"geo.coordinates": {
           "$geoWithin": {
              "$geometry": {
                 "type" : "Polygon" ,
                 "coordinates": [polygon],
              }
           }
         }}, {'tweet_created_at':{'$gte':date,
                                  '$lt':date+timedelta(days=1)}},
           {'fastText_lang': 'en'}]}},
        {"$project" : {"_id": 0,'tweet_created_at':1,'text': 1,'geo.coordinates':1,
                       'long_body':1,'body':1, 'id':1,
                       'day':{'$dateToString': {'format': '%Y-%m-%d',
                                                'date': '$tweet_created_at',
                                                'timezone':timezone}}
                      }
        },
         {
             "$group": {"_id": "$day","count" :{"$sum":1},
                        "tweet_coordinates": {"$push": '$geo.coordinates'},
                        "tweet_text": {"$push": '$text'}, "message_id":{"$push": '$id'}}
         },
        {
            "$sort": { "_id": 1 }
        }
    ])
    return tweet_cursor
